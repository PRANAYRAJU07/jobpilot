#!/usr/bin/env python3
"""
JobPilot AI — Schema Verification Script
Checks that the actual PostgreSQL schema matches the SQLAlchemy models.

Usage:
  python scripts/check_db_schema.py

Exits with code 0 if all checks pass, 1 if there are issues.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
log = logging.getLogger('schema_check')

# Expected columns per table (minimum required — not exhaustive)
EXPECTED = {
    'gmail_connections': ['id','user_id','email_address','status','last_history_id','last_sync_at','encrypted_access_token','encrypted_refresh_token','token_expires_at'],
    'applications': ['id','job_id','user_id','status','created_at','error_message','retry_count'],
    'jobs': ['id','title','company','location','country','role_level','is_internship','eligibility_status','status','raw_jd','source'],
    'candidate_profiles': ['id','user_id','full_name','location','auto_apply_enabled','daily_application_limit'],
    'job_source_registry': ['id','company','source_type','country_focus','status','enabled'],
    'notifications': ['id','user_id','title','body','type','priority','dedupe_key','status','created_at','read_at'],
    'users': ['id','email','password_hash','created_at'],
    'application_events': ['id','application_id','previous_state','new_state','timestamp'],
}


def check():
    issues = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.connect() as conn:
        for table, expected_cols in EXPECTED.items():
            if table not in existing_tables:
                issues.append(f"MISSING TABLE: {table}")
                continue

            result = conn.execute(text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"
            )).fetchall()
            actual_cols = {row[0] for row in result}

            for col in expected_cols:
                if col not in actual_cols:
                    issues.append(f"MISSING COLUMN: {table}.{col}")
                else:
                    log.info(f"  ✓ {table}.{col}")

    if issues:
        log.error("\n=== SCHEMA ISSUES FOUND ===")
        for issue in issues:
            log.error(f"  ✗ {issue}")
        log.error(f"\nTotal issues: {len(issues)}")
        log.error("Run: python scripts/migrate_schema.py to fix")
        return False
    else:
        log.info("\n=== ALL SCHEMA CHECKS PASSED ===")
        return True


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
