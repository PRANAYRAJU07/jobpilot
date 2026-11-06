from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
import models
import auth
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter()


class PreferenceUpdate(BaseModel):
    job_match_enabled: Optional[bool] = None
    application_updates_enabled: Optional[bool] = None
    interview_enabled: Optional[bool] = None
    assessment_enabled: Optional[bool] = None
    action_required_enabled: Optional[bool] = None
    rejection_enabled: Optional[bool] = None
    offer_enabled: Optional[bool] = None
    system_enabled: Optional[bool] = None
    daily_summary_enabled: Optional[bool] = None
    web_push_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    alert_email: Optional[str] = None
    whatsapp_number: Optional[str] = None
    min_match_score_threshold: Optional[int] = None
    fresh_only_alerts: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: Optional[str] = None


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


@router.get("")
@router.get("/")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    limit: int = 50,
    offset: int = 0
):
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(models.Notification.created_at.desc()).offset(offset).limit(limit).all()

    result = []
    for n in notifications:
        d = {
            "id": str(n.id),
            "user_id": str(n.user_id),
            "title": n.title,
            "body": n.body,
            "type": n.type,
            "category": n.type,
            "priority": n.priority,
            "read": n.read_at is not None,
            "read_at": n.read_at,
            "status": n.status,
            "created_at": n.created_at,
            "payload": n.payload,
            "application_id": str(n.application_id) if n.application_id else None,
            "job_id": str(n.job_id) if n.job_id else None,
        }
        result.append(d)
    return result


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    count = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.read_at == None
    ).count()

    return {"unread_count": count}


@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read_at = datetime.utcnow()
    notification.status = "READ"
    db.commit()

    return {"status": "SUCCESS"}


@router.post("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.read_at == None
    ).update({"read_at": datetime.utcnow(), "status": "READ"})
    db.commit()

    return {"status": "SUCCESS"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return {"status": "SUCCESS"}


@router.get("/preferences")
def get_preferences(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    pref = db.query(models.NotificationPreference).filter_by(user_id=current_user.id).first()
    profile = db.query(models.CandidateProfile).filter_by(user_id=current_user.id).first()
    if not pref:
        pref = models.NotificationPreference(
            user_id=current_user.id,
            alert_email=profile.alert_email if profile and profile.alert_email else current_user.email,
            whatsapp_number=profile.whatsapp_number if profile and profile.whatsapp_number else (profile.phone if profile else None),
            email_enabled=True,
            whatsapp_enabled=True,
            min_match_score_threshold=profile.min_match_score if profile and profile.min_match_score else 60,
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("/preferences")
def update_preferences(
    update: PreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    pref = db.query(models.NotificationPreference).filter_by(user_id=current_user.id).first()
    if not pref:
        pref = models.NotificationPreference(user_id=current_user.id)
        db.add(pref)

    updates = update.dict(exclude_unset=True)
    for key, value in updates.items():
        setattr(pref, key, value)

    # Sync Email & WhatsApp alert channels back to CandidateProfile as well
    profile = db.query(models.CandidateProfile).filter_by(user_id=current_user.id).first()
    if profile:
        if "alert_email" in updates:
            profile.alert_email = updates["alert_email"]
        if "whatsapp_number" in updates:
            profile.whatsapp_number = updates["whatsapp_number"]
        if "email_enabled" in updates:
            profile.email_alerts_enabled = updates["email_enabled"]
        if "whatsapp_enabled" in updates:
            profile.whatsapp_alerts_enabled = updates["whatsapp_enabled"]
        if "min_match_score_threshold" in updates and updates["min_match_score_threshold"] is not None:
            profile.min_match_score = updates["min_match_score_threshold"]
        if "fresh_only_alerts" in updates and updates["fresh_only_alerts"] is not None:
            profile.fresh_jobs_only = updates["fresh_only_alerts"]

    db.commit()
    db.refresh(pref)
    return pref


@router.post("/test-alert")
def send_test_alert(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Sends a real test Email & WhatsApp job alert using the user's top matched job
    (or a sample verified AI/ML Intern role) so they can verify delivery and click the link.
    """
    profile = db.query(models.CandidateProfile).filter_by(user_id=current_user.id).first()
    if not profile:
        profile = models.CandidateProfile(
            user_id=current_user.id,
            full_name=current_user.email.split("@")[0].title(),
            alert_email=current_user.email,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    job = db.query(models.Job).filter(models.Job.status == "MATCHED").order_by(models.Job.posted_at.desc().nullslast()).first()
    if not job:
        job = models.Job(
            id=uuid.uuid4(),
            external_job_id="test_alert_job",
            source="GREENHOUSE",
            title="AI / Machine Learning Intern",
            company="Anthropic",
            location="Hyderabad / Remote",
            url="https://boards.greenhouse.io/anthropic",
            apply_url="https://boards.greenhouse.io/anthropic",
            description="Test alert for verified AI/ML internship matching your resume skills.",
            is_internship=True,
            is_fresh=True,
            is_genuine=True,
            domain_category="AI_ML",
        )

    match_data = (job.raw_jd or {}).get("match_analysis") or {
        "relevance_score": 92,
        "matched_skills": ["Python", "PyTorch", "FastAPI", "LLMs", "RAG"],
        "missing_skills": [],
        "matched_requirements": [
            {"skill": "Python", "evidence": ["Resume", "Project: ASFO"]},
            {"skill": "PyTorch", "evidence": ["Project: ASFO"]},
            {"skill": "FastAPI", "evidence": ["Project: AI-HMS"]},
        ],
        "domain_category": "AI_ML",
        "cross_validation_passed": True,
    }

    from services.alert_dispatcher import AlertDispatcherService
    dispatcher = AlertDispatcherService(db)
    result = dispatcher.dispatch_job_match_alert(job, profile, match_data, force=True)
    return {
        "status": "SUCCESS",
        "message": "Test job alert dispatched across configured Email, WhatsApp, and In-App channels",
        "result": result,
    }


@router.post("/push/subscribe")
def subscribe_push(
    sub: PushSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    existing = db.query(models.PushSubscription).filter_by(endpoint=sub.endpoint).first()
    if existing:
        if existing.user_id != current_user.id:
            existing.user_id = current_user.id
        existing.p256dh = sub.p256dh
        existing.auth = sub.auth
        existing.active = True
        existing.user_agent = sub.user_agent
    else:
        new_sub = models.PushSubscription(
            user_id=current_user.id,
            endpoint=sub.endpoint,
            p256dh=sub.p256dh,
            auth=sub.auth,
            user_agent=sub.user_agent
        )
        db.add(new_sub)

    db.commit()
    return {"status": "SUCCESS"}


@router.delete("/push/unsubscribe")
def unsubscribe_push(
    endpoint: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    sub = db.query(models.PushSubscription).filter_by(
        endpoint=endpoint,
        user_id=current_user.id
    ).first()

    if sub:
        db.delete(sub)
        db.commit()

    return {"status": "SUCCESS"}
