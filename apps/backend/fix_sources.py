import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'apps/backend')))

from database import SessionLocal
import models

def fix_sources():
    db = SessionLocal()
    try:
        # Fix Figma: was LEVER/figma, should be GREENHOUSE/figma
        figma = db.query(models.JobSourceRegistry).filter_by(company="Figma").first()
        if figma:
            figma.source_type = "GREENHOUSE"
            figma.external_company_id = "figma"
            figma.career_url = "https://boards.greenhouse.io/figma"
            figma.status = "PENDING"
            figma.last_error = None
            print("Updated Figma -> GREENHOUSE/figma")
        
        # Fix Notion: used their custom site, no public GH/Lever board found
        notion = db.query(models.JobSourceRegistry).filter_by(company="Notion").first()
        if notion:
            notion.enabled = False
            notion.status = "MANUAL_CONFIGURATION_REQUIRED"
            notion.last_error = "Notion manages careers via notion.com/careers (custom site). No public Greenhouse/Lever board confirmed."
            print("Updated Notion -> MANUAL_CONFIGURATION_REQUIRED")

        # Fix Netflix: uses Workday (not supported by current connectors)
        netflix = db.query(models.JobSourceRegistry).filter_by(company="Netflix").first()
        if netflix:
            netflix.enabled = False
            netflix.status = "UNSUPPORTED"
            netflix.last_error = "Netflix uses Workday (netflix.wd108.myworkdayjobs.com). Workday connector not implemented."
            print("Updated Netflix -> UNSUPPORTED/Workday")

        # Fix OpenAI: uses Ashby (not supported by current connectors)
        openai = db.query(models.JobSourceRegistry).filter_by(company="OpenAI").first()
        if openai:
            openai.enabled = False
            openai.status = "UNSUPPORTED"
            openai.last_error = "OpenAI uses Ashby ATS. Ashby connector not implemented in Phase 15."
            print("Updated OpenAI -> UNSUPPORTED/Ashby")

        db.commit()
        print("Source registry updated.")
    finally:
        db.close()

if __name__ == "__main__":
    fix_sources()
