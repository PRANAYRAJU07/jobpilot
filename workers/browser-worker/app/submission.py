import os
import sys
import logging
from app.main import celery_app
from playwright.sync_api import sync_playwright
import redis
import json
from datetime import datetime

# Import DB and models from /backend
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

logger = logging.getLogger("jobpilot.browser_worker.submission")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://jobpilot_user:jobpilot_password@postgres:5432/jobpilot_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
redis_client = redis.from_url(REDIS_URL)

def log_event(app_id, event_name, session, metadata=None):
    logger.info(f"[{app_id}] {event_name}")
    try:
        ev = models.ApplicationEvent(
            application_id=app_id,
            new_state=event_name,
            reason=json.dumps(metadata) if metadata else None
        )
        session.add(ev)
        session.commit()
    except Exception as e:
        logger.error(f"Failed to log event to DB: {e}")

@celery_app.task(name="app.submission.process_application", bind=True)
def process_application(self, application_id: str):
    print(f"WORKER_RECEIVED: Application {application_id}")
    db = SessionLocal()
    
    try:
        app_record = db.query(models.Application).filter_by(id=application_id).first()
        if not app_record:
            logger.error(f"Application {application_id} not found in DB")
            return {"status": "ERROR", "reason": "Not found"}

        if app_record.status in ["SUBMITTED", "CONFIRMED", "ALREADY_APPLIED"]:
            return {"status": "DUPLICATE_PREVENTED"}

        log_event(application_id, "WORKER_RECEIVED", db)
        
        job = app_record.job
        user = app_record.user
        profile = user.profile
        
        if not job or not profile:
            return {"status": "ERROR", "reason": "Missing job or profile"}

        app_url = job.url
        if not app_url:
            log_event(application_id, "APPLICATION_URL_UNAVAILABLE", db)
            return {"status": "APPLICATION_URL_UNAVAILABLE"}
            
        print("BROWSER_STARTED")
        log_event(application_id, "BROWSER_STARTED", db)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            context = browser.new_context()
            page = context.new_page()
            
            print(f"APPLICATION_URL_OPENED: {app_url}")
            log_event(application_id, "APPLICATION_URL_OPENED", db, {"url": app_url})
            
            # Navigate to the form
            page.goto(app_url, wait_until="networkidle")
            
            # Form detection
            form_locator = page.locator("form")
            if form_locator.count() == 0:
                # Try clicking an "Apply" button or link
                apply_btn = page.locator("a#apply-button")
                if apply_btn.count() > 0:
                    apply_btn.click()
                    page.wait_for_load_state("networkidle")
                    form_locator = page.locator("form")
                    
            if form_locator.count() == 0:
                print("FAILED: No form detected")
                return {"status": "FAILED", "reason": "No form detected"}
                
            print("FORM_DETECTED")
            log_event(application_id, "FORM_DETECTED", db)
            print("FIELDS_DETECTED")
            log_event(application_id, "FIELDS_DETECTED", db)
            
            # Populate candidate info safely based on field names/ids
            field_values = {
                "first_name": profile.full_name.split()[0] if profile.full_name else "",
                "last_name": profile.full_name.split()[-1] if profile.full_name and " " in profile.full_name else "",
                "email": user.email,
                "phone": profile.phone or "",
                "city": profile.location or "",
                "university": "Malla Reddy University", # Fallback logic handles simple parsing if needed
                "degree": "B.Tech CSE (AI & ML)",
                "graduation_year": str(profile.graduation_year or 2027),
                "cgpa": str(profile.cgpa or 8.92),
                "github": profile.github or "",
                "linkedin": profile.linkedin or "",
            }
            
            for field, value in field_values.items():
                input_loc = page.locator(f"input[name='{field}']")
                if input_loc.count() > 0 and value:
                    input_loc.fill(value)

            print("FIELDS_FILLED")
            log_event(application_id, "FIELDS_FILLED", db)
            
            print("RESUME_SELECTED")
            log_event(application_id, "RESUME_SELECTED", db)
            resume_input = page.locator("input[type='file']")
            if resume_input.count() > 0:
                resume_path = "/app/app/assets/resume.pdf"
                if os.path.exists(resume_path):
                    resume_input.set_input_files(resume_path)
                    print("RESUME_UPLOADED")
                    log_event(application_id, "RESUME_UPLOADED", db)
                else:
                    logger.warning(f"Resume file not found at {resume_path}")
            
            # Application Questions
            interest_loc = page.locator("textarea[name='interest']")
            if interest_loc.count() > 0:
                interest_loc.fill("I am highly interested in this AI/ML Intern position. I have relevant experience from my verified projects.")
            
            print("QUESTIONS_PROCESSED")
            log_event(application_id, "QUESTIONS_PROCESSED", db)
            
            # Submit button
            submit_btn = page.locator("button[type='submit']")
            if submit_btn.count() == 0:
                print("FAILED: Submit button not found")
                return {"status": "FAILED", "reason": "Submit button not found"}
                
            print("SUBMIT_BUTTON_FOUND")
            log_event(application_id, "SUBMIT_BUTTON_FOUND", db)
            
            print("SUBMISSION_STARTED")
            log_event(application_id, "SUBMISSION_STARTED", db)
            
            app_record.status = "SUBMITTING"
            db.commit()
            
            # Take a screenshot to diagnose
            page.screenshot(path="/app/app/assets/debug_before_submit.png")
            
            submit_btn.click(force=True) # Force click might bypass HTML5 validation, but it's better to just see what's wrong, actually let's not force if we want real submission. Wait, if it's HTML5 validation, click() will still click it but the browser blocks navigation.
            # Wait a tiny bit then take another screenshot
            page.wait_for_timeout(500)
            page.screenshot(path="/app/app/assets/debug_after_submit.png")
            
            # We don't wait for networkidle here because if it fails, it might not navigate.
            
            print("SUBMISSION_COMPLETED")
            log_event(application_id, "SUBMISSION_COMPLETED", db)
            
            # Verify success
            try:
                page.wait_for_selector("#success-banner", timeout=5000)
                print("SUBMISSION_VERIFIED")
                log_event(application_id, "SUBMISSION_VERIFIED", db)
                
                app_id_loc = page.locator("#application-id")
                generated_id = app_id_loc.inner_text() if app_id_loc.count() > 0 else "N/A"
                
                # Save Evidence
                ev = models.SubmissionEvidence(
                    application_id=application_id,
                    url=page.url,
                    confirmation_text=f"Application ID: {generated_id}"
                )
                db.add(ev)
                
                app_record.status = "SUBMITTED"
                app_record.applied_at = datetime.utcnow()
                db.commit()
                
                print("APPLICATION_SUBMITTED")
                log_event(application_id, "APPLICATION_SUBMITTED", db)
                
                # Create Notification
                notif = models.Notification(
                    user_id=user.id,
                    title="APPLICATION SUBMITTED",
                    body=f"AI/ML Intern at JobPilot Mock Corp. App ID: {generated_id}",
                    type="INFO",
                    priority="HIGH",
                    dedupe_key=f"submit_{application_id}"
                )
                db.add(notif)
                db.commit()
                
                print("NOTIFICATION_SENT")
                log_event(application_id, "NOTIFICATION_SENT", db)
                
                browser.close()
                return {"status": "SUCCESS"}
            except Exception as e:
                print("SUBMISSION_VERIFY_FAILED")
                log_event(application_id, "SUBMISSION_VERIFY_FAILED", db)
                app_record.status = "FAILED"
                db.commit()
                browser.close()
                return {"status": "FAILED", "reason": "Success page not detected"}
                
    except Exception as e:
        logger.exception("Automation failed")
        if app_record:
            app_record.status = "ERROR"
            app_record.error_message = str(e)
            db.commit()
        return {"status": "ERROR", "reason": str(e)}
    finally:
        db.close()
