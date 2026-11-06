from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

import models
import auth
from database import get_db

router = APIRouter(prefix="/api/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    education: Optional[str] = None
    cgpa: Optional[float] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    preferred_locations: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    preferred_job_types: Optional[List[str]] = None
    domain_focus: Optional[List[str]] = None
    min_match_score: Optional[int] = None
    daily_application_limit: Optional[int] = None
    auto_apply_enabled: Optional[bool] = None
    alert_email: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email_alerts_enabled: Optional[bool] = None
    whatsapp_alerts_enabled: Optional[bool] = None
    fresh_jobs_only: Optional[bool] = None
    max_job_age_hours: Optional[int] = None


class SkillCreate(BaseModel):
    name: str
    category: Optional[str] = "Custom"


@router.get("")
@router.get("/")
def get_profile(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        default_name = current_user.email.split("@")[0].replace(".", " ").title()
        profile = models.CandidateProfile(
            user_id=current_user.id,
            full_name=default_name,
            alert_email=current_user.email,
            email_alerts_enabled=True,
            whatsapp_alerts_enabled=True,
            min_match_score=60,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("")
@router.put("/")
def update_profile(
    profile_data: ProfileUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    payload = profile_data.dict(exclude_unset=True)

    if not profile:
        profile = models.CandidateProfile(user_id=current_user.id, **payload)
        db.add(profile)
    else:
        for key, value in payload.items():
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/skills")
def get_profile_skills(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        return []

    skills = db.query(models.CandidateSkill).filter(models.CandidateSkill.profile_id == profile.id).all()
    claims = db.query(models.CandidateClaim).filter(models.CandidateClaim.profile_id == profile.id).all()
    claim_map = {c.skill_id: c for c in claims if c.skill_id}

    result = []
    for s in skills:
        c = claim_map.get(s.id)
        evidence_sources = []
        if c:
            if c.document_evidence:
                evidence_sources.append(f"Resume: {c.document_evidence.filename}")
            if c.project_evidence:
                evidence_sources.append(f"Project: {c.project_evidence.title}")
            if not evidence_sources:
                evidence_sources.append("Verified Profile Skill")
        result.append({
            "id": str(s.id),
            "profile_id": str(s.profile_id),
            "name": s.name,
            "category": s.category or "General",
            "verification_status": c.verification_status if c else "SUPPORTED",
            "evidence": evidence_sources,
        })
    return result


@router.post("/skills")
def add_profile_skill(
    skill_in: SkillCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Create a profile or upload a resume first")

    clean_name = skill_in.name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Skill name cannot be empty")

    existing = db.query(models.CandidateSkill).filter(
        models.CandidateSkill.profile_id == profile.id,
        models.CandidateSkill.name.ilike(clean_name)
    ).first()
    if existing:
        return existing

    new_skill = models.CandidateSkill(
        profile_id=profile.id,
        name=clean_name,
        category=skill_in.category or "Custom"
    )
    db.add(new_skill)
    db.flush()

    claim = models.CandidateClaim(
        profile_id=profile.id,
        skill_id=new_skill.id,
        claim_text=f"Candidate added skill {clean_name}",
        verification_status="SUPPORTED",
    )
    db.add(claim)
    db.commit()
    db.refresh(new_skill)
    return new_skill


@router.delete("/skills/{skill_id}")
def delete_profile_skill(
    skill_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    skill = db.query(models.CandidateSkill).filter(
        models.CandidateSkill.id == skill_id,
        models.CandidateSkill.profile_id == profile.id
    ).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    db.query(models.CandidateClaim).filter(models.CandidateClaim.skill_id == skill.id).delete()
    db.delete(skill)
    db.commit()
    return {"status": "DELETED", "skill_id": skill_id}


@router.get("/projects")
@router.get("/projects/")
def get_profile_projects(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        return []
    projects = db.query(models.CandidateProject).filter(models.CandidateProject.profile_id == profile.id).all()
    return [
        {
            "id": str(p.id),
            "profile_id": str(p.profile_id),
            "title": p.title,
            "description": p.description,
        }
        for p in projects
    ]


@router.post("/re-match")
@router.post("/re-match/")
def trigger_profile_rematch(
    background_tasks: BackgroundTasks,
    send_alerts: bool = True,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    from services.job_engine import JobEngineService
    engine = JobEngineService(db)
    # Immediately evaluate the freshest 100 jobs for instant UI response
    summary = engine.re_evaluate_all_jobs_for_profile(
        profile,
        send_alerts_for_top=0,
        limit=100
    )

    # Background task to evaluate all jobs and dispatch alerts without blocking UI
    def bg_rematch(profile_id: str):
        from database import SessionLocal
        bg_db = SessionLocal()
        try:
            bg_profile = bg_db.query(models.CandidateProfile).filter(models.CandidateProfile.id == profile_id).first()
            if bg_profile:
                bg_engine = JobEngineService(bg_db)
                bg_engine.re_evaluate_all_jobs_for_profile(bg_profile, send_alerts_for_top=10 if send_alerts else 0)
        except Exception as e:
            import logging
            logging.getLogger("jobpilot").error(f"Background rematch error: {e}")
        finally:
            bg_db.close()

    background_tasks.add_task(bg_rematch, str(profile.id))

    return {
        "message": "Cross-validation completed across fresh jobs",
        "summary": summary,
    }
