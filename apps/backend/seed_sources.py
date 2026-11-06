import sys
import os
import uuid
from datetime import datetime

# Ensure apps/backend is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'apps/backend')))

from database import SessionLocal
import models

def seed_sources():
    db = SessionLocal()
    try:
        companies = [
            {"company": "Anthropic", "external_company_id": "anthropic", "source_type": "GREENHOUSE", "career_url": "https://boards.greenhouse.io/anthropic"},
            {"company": "OpenAI", "external_company_id": "openai", "source_type": "GREENHOUSE", "career_url": "https://boards.greenhouse.io/openai"},
            {"company": "Figma", "external_company_id": "figma", "source_type": "LEVER", "career_url": "https://jobs.lever.co/figma"},
            {"company": "Notion", "external_company_id": "notion", "source_type": "LEVER", "career_url": "https://jobs.lever.co/notion"},
            {"company": "Stripe", "external_company_id": "stripe", "source_type": "GREENHOUSE", "career_url": "https://boards.greenhouse.io/stripe"},
            {"company": "Netflix", "external_company_id": "netflix", "source_type": "LEVER", "career_url": "https://jobs.lever.co/netflix"},
            {"company": "Robinhood", "external_company_id": "robinhood", "source_type": "GREENHOUSE", "career_url": "https://boards.greenhouse.io/robinhood"},
            {"company": "Databricks", "external_company_id": "databricks", "source_type": "GREENHOUSE", "career_url": "https://boards.greenhouse.io/databricks"}
        ]
        
        for c in companies:
            existing = db.query(models.JobSourceRegistry).filter_by(company=c["company"]).first()
            if not existing:
                src = models.JobSourceRegistry(
                    company=c["company"],
                    career_url=c["career_url"],
                    source_type=c["source_type"],
                    external_company_id=c["external_company_id"],
                    enabled=True,
                    scan_interval_minutes=60
                )
                db.add(src)
        db.commit()
        print("Seeded database with real job sources.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_sources()
