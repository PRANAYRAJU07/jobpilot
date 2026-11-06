import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models
from workers.celery_app import celery_app

def main():
    db = SessionLocal()
    try:
        user = db.query(models.User).filter_by(email='mpranayraju2@gmail.com').first()
        if not user:
            print("User not found.")
            return

        job = db.query(models.Job).filter_by(external_job_id='MOCK-AI-ML-1').first()
        if not job:
            print("Mock job not found.")
            return

        # Check for existing application
        app = db.query(models.Application).filter_by(user_id=user.id, job_id=job.id).first()
        if not app:
            app = models.Application(
                user_id=user.id,
                job_id=job.id,
                status="DISCOVERED"
            )
            db.add(app)
            db.commit()
        else:
            # Reset it for the test
            app.status = "DISCOVERED"
            db.commit()
            # Also clear old events and evidence
            db.query(models.ApplicationEvent).filter_by(application_id=app.id).delete()
            db.query(models.SubmissionEvidence).filter_by(application_id=app.id).delete()
            db.query(models.Notification).filter(models.Notification.dedupe_key == f"submit_{app.id}").delete()
            db.commit()

        print("APPLICATION_CREATED")
        
        # Log initial event
        ev = models.ApplicationEvent(application_id=app.id, new_state="APPLICATION_CREATED")
        db.add(ev)
        db.commit()

        # Enqueue Task
        print("APPLICATION_QUEUED")
        ev_queue = models.ApplicationEvent(application_id=app.id, new_state="APPLICATION_QUEUED")
        db.add(ev_queue)
        db.commit()

        # The route in celery config maps 'app.submission.*' to 'browser.application' queue
        celery_app.send_task(
            "app.submission.process_application",
            args=[str(app.id)],
            queue="browser.application"
        )

        print("Task sent to celery queue. Please check docker logs jobpilot_browser_worker")
        
        # We can poll the DB to see events showing up
        print("Polling database for events...")
        seen_events = set()
        for i in range(30):
            events = db.query(models.ApplicationEvent).filter_by(application_id=app.id).order_by(models.ApplicationEvent.timestamp.asc()).all()
            for e in events:
                if e.new_state not in seen_events:
                    print(f"[{e.timestamp}] {e.new_state}")
                    seen_events.add(e.new_state)
            
            app.refresh_from_db = db.query(models.Application).filter_by(id=app.id).first()
            if app.refresh_from_db.status in ["SUBMITTED", "FAILED", "ERROR"]:
                print(f"Final Status Reached: {app.refresh_from_db.status}")
                break
                
            time.sleep(2)
            
    finally:
        db.close()

if __name__ == "__main__":
    main()
