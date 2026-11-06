from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from typing import Optional

import models
import auth
from database import get_db

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/")
def list_jobs(
    status: Optional[str] = None,
    company: Optional[str] = None,
    source: Optional[str] = None,
    q: Optional[str] = None,
    min_score: Optional[int] = None,
    country: Optional[str] = None,
    location_city: Optional[str] = None,
    is_internship: Optional[bool] = None,
    role_level: Optional[str] = None,
    eligibility: Optional[str] = None,
    domain: Optional[str] = None,
    fresh_only: Optional[bool] = None,
    genuine_only: Optional[bool] = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = db.query(models.Job)

    if genuine_only:
        query = query.filter(or_(models.Job.is_genuine == True, models.Job.is_genuine.is_(None)))
    if fresh_only:
        query = query.filter(models.Job.is_fresh == True)
    if status:
        query = query.filter(models.Job.status == status)
    if domain:
        query = query.filter(models.Job.domain_category == domain)
    if company:
        query = query.filter(models.Job.company.ilike(f"%{company}%"))
    if source:
        query = query.filter(models.Job.source == source)
    if q:
        query = query.filter(
            (models.Job.title.ilike(f"%{q}%")) |
            (models.Job.company.ilike(f"%{q}%")) |
            (models.Job.description.ilike(f"%{q}%"))
        )
    if min_score is not None:
        query = query.filter(
            text("NULLIF(raw_jd->'match_analysis'->>'relevance_score', '')::int >= :min_score")
        ).params(min_score=min_score)
    if country:
        query = query.filter(models.Job.country == country)
    if location_city:
        query = query.filter(models.Job.location.ilike(f"%{location_city}%"))
    if is_internship is not None:
        query = query.filter(models.Job.is_internship == is_internship)
    if role_level:
        query = query.filter(models.Job.role_level == role_level)
    if eligibility:
        query = query.filter(models.Job.eligibility_status == eligibility)

    total = query.count()
    jobs = query.order_by(models.Job.posted_at.desc().nullslast(), models.Job.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "jobs": jobs, "skip": skip, "limit": limit}


@router.get("/stats")
def get_job_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    total = db.query(models.Job).filter(or_(models.Job.is_genuine == True, models.Job.is_genuine.is_(None))).count()
    matched = db.query(models.Job).filter(models.Job.status == "MATCHED").count()
    high_match = db.execute(
        text("SELECT COUNT(*) FROM jobs WHERE status = 'MATCHED' AND NULLIF(raw_jd->'match_analysis'->>'relevance_score', '')::int >= 70")
    ).scalar()
    fresh_jobs = db.query(models.Job).filter(models.Job.is_fresh == True).count()
    total_applications = db.query(models.Application).filter(models.Application.user_id == current_user.id).count()

    india_jobs = db.query(models.Job).filter(or_(
        models.Job.country == 'India',
        models.Job.location.ilike('%india%'),
        models.Job.location.ilike('%hyderabad%'),
        models.Job.location.ilike('%bengaluru%'),
        models.Job.location.ilike('%bangalore%'),
        models.Job.location.ilike('%pune%'),
        models.Job.location.ilike('%mumbai%'),
        models.Job.location.ilike('%delhi%'),
        models.Job.location.ilike('%chennai%'),
        models.Job.location.ilike('%noida%'),
        models.Job.location.ilike('%gurugram%'),
        models.Job.location.ilike('%gurgaon%'),
    )).count()

    hyderabad_jobs = db.query(models.Job).filter(
        models.Job.location.ilike('%hyderabad%')
    ).count()

    internship_jobs = db.query(models.Job).filter(or_(
        models.Job.is_internship == True,
        models.Job.title.ilike('%intern%'),
    )).count()

    return {
        "total_jobs": total,
        "matched_jobs": matched,
        "high_match_jobs": high_match or 0,
        "fresh_jobs": fresh_jobs,
        "total_applications": total_applications,
        "india_jobs": india_jobs,
        "hyderabad_jobs": hyderabad_jobs,
        "internship_jobs": internship_jobs,
    }


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/why")
def why_this_job(job_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    raw = job.raw_jd or {}
    ma = raw.get("match_analysis", {})
    return {
        "job_id": str(job.id),
        "title": job.title,
        "company": job.company,
        "apply_url": job.apply_url or job.url,
        "relevance_score": ma.get("relevance_score"),
        "domain_category": ma.get("domain_category") or job.domain_category,
        "domain_suitable": ma.get("domain_suitable", True),
        "is_genuine": ma.get("is_genuine", job.is_genuine),
        "genuineness_score": ma.get("genuineness_score", job.genuineness_score),
        "genuineness_reasons": ma.get("genuineness_reasons", []),
        "cross_validation_passed": ma.get("cross_validation_passed", False),
        "matched_requirements": ma.get("matched_requirements", []),
        "missing_requirements": ma.get("missing_requirements", []),
        "matched_skills": ma.get("matched_skills", []),
        "missing_skills": ma.get("missing_skills", []),
    }


@router.post("/{job_id}/notify")
def send_job_alert_now(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Cross-validates a specific job against the current user's profile and immediately
    dispatches the direct job application link via Email and WhatsApp.
    """
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Create a profile or upload your resume first")

    from services.job_engine import JobEngineService
    from services.alert_dispatcher import AlertDispatcherService

    engine = JobEngineService(db)
    reqs = engine.analyze_jd(job)
    match_data = engine.calculate_match(reqs, profile, job=job)

    dispatcher = AlertDispatcherService(db)
    dispatch_result = dispatcher.dispatch_job_match_alert(job, profile, match_data, force=True)

    return {
        "message": "Job link notification dispatched",
        "job_id": str(job.id),
        "apply_url": job.apply_url or job.url,
        "match_data": match_data,
        "dispatch_result": dispatch_result,
    }


@router.post("/search")
def trigger_manual_search(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    from workers.tasks.job_tasks import schedule_active_sources_task
    try:
        schedule_active_sources_task.delay()
        return {"message": "Fresh job discovery scan queued across all active sources", "status": "QUEUED"}
    except Exception as e:
        return {"message": f"Discovery trigger error: {e}", "status": "ERROR"}
