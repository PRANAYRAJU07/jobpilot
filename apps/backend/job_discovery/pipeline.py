import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
import redis

import models
from job_discovery.connectors import (
    GreenhouseConnector,
    LeverConnector,
    AshbyConnector,
    DirectCareerPageConnector,
    LinkedInConnector,
    InternshalaConnector,
    NaukriConnector,
)

logger = logging.getLogger(__name__)

class JobDiscoveryPipeline:
    def __init__(self, db: Session):
        self.db = db

    def get_connector(self, source: models.JobSourceRegistry):
        stype = (source.source_type or "").upper()
        if stype == "GREENHOUSE":
            return GreenhouseConnector(source.company, source.external_company_id, source.career_url)
        elif stype == "LEVER":
            return LeverConnector(source.company, source.external_company_id, source.career_url)
        elif stype == "ASHBY":
            return AshbyConnector(source.company, source.external_company_id, source.career_url)
        elif stype in ("DIRECT_CAREER", "WORKDAY", "SMARTRECRUITERS", "CAREER_PAGE"):
            return DirectCareerPageConnector(source.company, source.external_company_id, source.career_url)
        elif stype == "LINKEDIN":
            return LinkedInConnector(source.company, source.external_company_id, source.career_url)
        elif stype == "INTERNSHALA":
            return InternshalaConnector(source.company, source.external_company_id, source.career_url)
        elif stype == "NAUKRI":
            return NaukriConnector(source.company, source.external_company_id, source.career_url)
        raise ValueError(f"Unsupported source type: {source.source_type}")

    def run_discovery(self, source_id: str, fresh_only: bool = False):
        source = self.db.query(models.JobSourceRegistry).filter_by(id=source_id, enabled=True).first()
        if not source:
            logger.info(f"Source {source_id} not found or disabled.")
            return {"status": "SKIPPED", "new_jobs": 0}

        try:
            connector = self.get_connector(source)
            jobs = connector.discover_jobs()
            if fresh_only:
                jobs = [j for j in jobs if j.get("is_fresh", True)]

            source.jobs_found = len(jobs)
            new_jobs = self.deduplicate_and_save(jobs, source)

            source.last_success_at = datetime.utcnow()
            source.status = "ACTIVE"
            source.last_error = None
            logger.info(f"Found {len(jobs)} jobs for {source.company} ({source.source_type}), {len(new_jobs)} are new.")

            import sys
            if "/app" not in sys.path:
                sys.path.append("/app")
            from services.job_engine import JobEngineService
            job_engine = JobEngineService(self.db)
            matched_and_alerted = 0
            for db_job in new_jobs:
                try:
                    res = job_engine.process_new_job(db_job.id, send_alerts=True)
                    if res and res.get("alert_dispatched"):
                        matched_and_alerted += 1
                except Exception as e:
                    logger.error(f"Error processing new job {db_job.id}: {e}")

            source.last_scan_at = datetime.utcnow()
            self.db.commit()
            return {
                "status": "SUCCESS",
                "total_discovered": len(jobs),
                "new_jobs": len(new_jobs),
                "alerts_sent": matched_and_alerted,
            }

        except Exception as e:
            source.last_error_at = datetime.utcnow()
            source.status = "ERROR"
            source.last_error = str(e)[:500]
            source.last_scan_at = datetime.utcnow()
            self.db.commit()
            logger.exception(f"Error scanning source {source.company}")
            return {"status": "ERROR", "error": str(e)}

    def deduplicate_and_save(self, raw_jobs: List[Dict[str, Any]], source: models.JobSourceRegistry) -> List[models.Job]:
        new_jobs = []
        for rj in raw_jobs:
            ext_id = rj.get("external_job_id")
            source_name = rj.get("source") or source.source_type
            title = (rj.get("title") or "").strip()
            company = (rj.get("company") or source.company or "").strip()
            if not title or not ext_id:
                continue

            existing = self.db.query(models.Job).filter_by(
                external_job_id=ext_id,
                source=source_name
            ).first()

            if not existing:
                db_job = models.Job(
                    external_job_id=ext_id,
                    source=source_name,
                    title=title,
                    company=company,
                    location=rj.get("location"),
                    url=rj.get("url"),
                    apply_url=rj.get("apply_url") or rj.get("url"),
                    description=rj.get("description"),
                    employment_type=rj.get("employment_type"),
                    posted_at=rj.get("posted_at") or datetime.utcnow(),
                    is_fresh=rj.get("is_fresh", True),
                    raw_jd=rj.get("raw_jd") or {},
                )
                self.db.add(db_job)
                new_jobs.append(db_job)

        self.db.flush()
        for db_job in new_jobs:
            self.emit_discovery_event(db_job)
        return new_jobs

    def emit_discovery_event(self, job: models.Job):
        try:
            r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, socket_timeout=1)
            payload = {
                "event": "JOB_DISCOVERED",
                "data": {
                    "id": str(job.id),
                    "title": job.title,
                    "company": job.company,
                    "source": job.source,
                    "location": job.location,
                    "url": job.apply_url or job.url,
                },
            }
            r.publish("global_events", json.dumps(payload))
        except Exception:
            pass
