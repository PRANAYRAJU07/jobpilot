#!/usr/bin/env python3
"""
JobPilot AI — Database Schema Migration Script
Run this script against any JobPilot database to bring it to the current schema.

Usage:
  python scripts/migrate_schema.py

This is idempotent — safe to run multiple times.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('migrate')


MIGRATIONS = [
    # ── Version 2: Gmail history ID (drift fix) ──
    ("gmail_connections: add last_history_id",
     "ALTER TABLE gmail_connections ADD COLUMN IF NOT EXISTS last_history_id VARCHAR"),

    # ── Version 3: Applications extra fields ──
    ("applications: add created_at",
     "ALTER TABLE applications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()"),
    ("applications: add updated_at",
     "ALTER TABLE applications ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()"),
    ("applications: add error_message",
     "ALTER TABLE applications ADD COLUMN IF NOT EXISTS error_message VARCHAR"),
    ("applications: add error_type",
     "ALTER TABLE applications ADD COLUMN IF NOT EXISTS error_type VARCHAR"),
    ("applications: add retry_count",
     "ALTER TABLE applications ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0"),

    # ── Version 4: Jobs India/internship/freshness/genuineness/domain classification ──
    ("jobs: add country",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS country VARCHAR"),
    ("jobs: add region",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS region VARCHAR"),
    ("jobs: add role_level",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS role_level VARCHAR"),
    ("jobs: add is_internship",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_internship BOOLEAN DEFAULT FALSE"),
    ("jobs: add eligibility_status",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS eligibility_status VARCHAR"),
    ("jobs: add graduation_year_min",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS graduation_year_min INTEGER"),
    ("jobs: add graduation_year_max",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS graduation_year_max INTEGER"),
    ("jobs: add apply_url",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS apply_url VARCHAR"),
    ("jobs: add domain_category",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS domain_category VARCHAR"),
    ("jobs: add is_genuine",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_genuine BOOLEAN DEFAULT TRUE"),
    ("jobs: add genuineness_score",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS genuineness_score INTEGER DEFAULT 100"),
    ("jobs: add is_fresh",
     "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS is_fresh BOOLEAN DEFAULT TRUE"),

    # ── Version 5: Candidate profile preferences & alert channels ──
    ("candidate_profiles: add location",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS location VARCHAR"),
    ("candidate_profiles: add preferred_locations",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS preferred_locations JSONB"),
    ("candidate_profiles: add preferred_roles",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS preferred_roles JSONB"),
    ("candidate_profiles: add preferred_job_types",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS preferred_job_types JSONB"),
    ("candidate_profiles: add domain_focus",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS domain_focus JSONB"),
    ("candidate_profiles: add min_match_score",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS min_match_score INTEGER DEFAULT 60"),
    ("candidate_profiles: add daily_application_limit",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS daily_application_limit INTEGER DEFAULT 10"),
    ("candidate_profiles: add auto_apply_enabled",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS auto_apply_enabled BOOLEAN DEFAULT FALSE"),
    ("candidate_profiles: add alert_email",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS alert_email VARCHAR"),
    ("candidate_profiles: add whatsapp_number",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR"),
    ("candidate_profiles: add email_alerts_enabled",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS email_alerts_enabled BOOLEAN DEFAULT TRUE"),
    ("candidate_profiles: add whatsapp_alerts_enabled",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS whatsapp_alerts_enabled BOOLEAN DEFAULT TRUE"),
    ("candidate_profiles: add fresh_jobs_only",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS fresh_jobs_only BOOLEAN DEFAULT TRUE"),
    ("candidate_profiles: add max_job_age_hours",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS max_job_age_hours INTEGER DEFAULT 72"),
    ("candidate_profiles: add created_at",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()"),
    ("candidate_profiles: add updated_at",
     "ALTER TABLE candidate_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()"),

    # ── Version 6: Document parsed metadata & text ──
    ("documents: add file_path",
     "ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_path VARCHAR"),
    ("documents: add extracted_text",
     "ALTER TABLE documents ADD COLUMN IF NOT EXISTS extracted_text TEXT"),
    ("documents: add parsed_metadata",
     "ALTER TABLE documents ADD COLUMN IF NOT EXISTS parsed_metadata JSONB"),

    # ── Version 7: Notification preferences for Email & WhatsApp job alerts ──
    ("notification_preferences: add whatsapp_enabled",
     "ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS whatsapp_enabled BOOLEAN DEFAULT TRUE"),
    ("notification_preferences: add alert_email",
     "ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS alert_email VARCHAR"),
    ("notification_preferences: add whatsapp_number",
     "ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR"),
    ("notification_preferences: add min_match_score_threshold",
     "ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS min_match_score_threshold INTEGER DEFAULT 60"),
    ("notification_preferences: add fresh_only_alerts",
     "ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS fresh_only_alerts BOOLEAN DEFAULT TRUE"),

    # ── Version 8: Job source India tagging ──
    ("job_source_registry: add country_focus",
     "ALTER TABLE job_source_registry ADD COLUMN IF NOT EXISTS country_focus VARCHAR DEFAULT 'GLOBAL'"),
    ("job_source_registry: add tags",
     "ALTER TABLE job_source_registry ADD COLUMN IF NOT EXISTS tags JSONB"),

    # ── Version 9: Indexes for performance ──
    ("index: jobs country",
     "CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs(country)"),
    ("index: jobs is_internship",
     "CREATE INDEX IF NOT EXISTS idx_jobs_is_internship ON jobs(is_internship)"),
    ("index: jobs role_level",
     "CREATE INDEX IF NOT EXISTS idx_jobs_role_level ON jobs(role_level)"),
    ("index: jobs domain_category",
     "CREATE INDEX IF NOT EXISTS idx_jobs_domain_category ON jobs(domain_category)"),
    ("index: jobs is_fresh",
     "CREATE INDEX IF NOT EXISTS idx_jobs_is_fresh ON jobs(is_fresh)"),
    ("index: jobs is_genuine",
     "CREATE INDEX IF NOT EXISTS idx_jobs_is_genuine ON jobs(is_genuine)"),
    ("index: jobs location trgm",
     "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm') THEN CREATE EXTENSION IF NOT EXISTS pg_trgm; END IF; END $$"),
    ("index: jobs eligibility_status",
     "CREATE INDEX IF NOT EXISTS idx_jobs_eligibility ON jobs(eligibility_status)"),
]


def run_migrations():
    log.info("Starting JobPilot schema migrations...")
    success = 0
    failed = 0

    with engine.connect() as conn:
        for name, sql in MIGRATIONS:
            try:
                conn.execute(text(sql))
                conn.commit()
                log.info(f"  ✓ {name}")
                success += 1
            except Exception as e:
                conn.rollback()
                log.warning(f"  ✗ {name}: {e}")
                failed += 1

    log.info(f"\nMigration complete: {success} succeeded, {failed} failed")
    if failed > 0:
        log.warning("Some migrations failed — check the warnings above")
    else:
        log.info("All migrations succeeded ✓")

    return failed == 0


if __name__ == "__main__":
    ok = run_migrations()
    sys.exit(0 if ok else 1)
