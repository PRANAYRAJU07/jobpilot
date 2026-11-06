from workers.celery_app import celery_app
import logging
import sys
import os
from datetime import datetime, timedelta

# Ensure apps/backend is in the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../apps/backend')))

from database import SessionLocal
import models
from job_discovery.pipeline import JobDiscoveryPipeline

logger = logging.getLogger("jobpilot.tasks")

@celery_app.task(name="workers.tasks.job_tasks.schedule_active_sources_task")
def schedule_active_sources_task():
    logger.info("Checking for job sources that need scanning...")
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        sources = db.query(models.JobSourceRegistry).filter_by(enabled=True).all()
        for src in sources:
            should_scan = False
            if not src.last_scan_at:
                should_scan = True
            else:
                next_scan_time = src.last_scan_at + timedelta(minutes=src.scan_interval_minutes)
                if now >= next_scan_time:
                    should_scan = True
            
            if should_scan:
                logger.info(f"Queuing discovery for source {src.company} ({src.id})")
                run_discovery_for_source_task.delay(str(src.id))
    finally:
        db.close()

@celery_app.task(name="workers.tasks.job_tasks.run_discovery_for_source_task")
def run_discovery_for_source_task(source_id: str):
    logger.info(f"Running discovery pipeline for source_id: {source_id}")
    db = SessionLocal()
    try:
        pipeline = JobDiscoveryPipeline(db)
        pipeline.run_discovery(source_id)
    finally:
        db.close()

@celery_app.task(name="analyze_jd")
def analyze_jd_task(job_id: str):
    logger.info(f"Analyzing JD for job {job_id}")
    db = SessionLocal()
    try:
        from services.job_engine import JobEngineService
        job_engine = JobEngineService(db)
        # Assuming process_new_job triggers analysis
        job_engine.process_new_job(job_id)
        return {"status": "ELIGIBLE"}
    finally:
        db.close()
