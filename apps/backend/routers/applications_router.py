from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import auth
from database import get_db

router = APIRouter(prefix="/api/applications", tags=["applications"])

@router.get("")
@router.get("/")
def list_applications(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.Application).filter(models.Application.user_id == current_user.id).all()

@router.get("/{application_id}")
def get_application(application_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    app = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.post("/{application_id}/approve")
def approve_application(application_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    User manually approves the application to proceed to submission.
    """
    app = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if app.status != "REVIEW_REQUIRED":
        raise HTTPException(status_code=400, detail=f"Cannot approve application in state: {app.status}")
        
    app.status = "READY_TO_SUBMIT"
    db.commit()
    return {"message": "Application approved", "status": app.status}

@router.post("/{application_id}/pause")
def pause_application(application_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    app = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    app.status = "PAUSED"
    db.commit()
    return {"message": "Application paused", "status": app.status}

@router.post("/{application_id}/start")
def start_application(application_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    app = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    app.status = "APPLICATION_STARTED"
    # Create Event
    event = models.ApplicationEvent(application_id=app.id, previous_state="READY", new_state="APPLICATION_STARTED", reason="User started manually")
    db.add(event)
    db.commit()
    
    # Enqueue task
    from workers.celery_app import celery_app
    celery_app.send_task("app.submission.process_application", args=[str(app.id)], queue="browser.application")
    
    return {"message": "Application started", "status": app.status}

@router.post("/{application_id}/resume")
def resume_application(application_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    app = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    app.status = "RESUMED"
    db.commit()
    return {"message": "Application resumed", "status": app.status}

@router.post("/{application_id}/cancel")
def cancel_application(application_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    app = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    app.status = "CANCELLED"
    db.commit()
    return {"message": "Application cancelled", "status": app.status}

@router.get("/{application_id}/events")
def get_application_events(application_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    app = db.query(models.Application).filter(models.Application.id == application_id, models.Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    events = db.query(models.ApplicationEvent).filter(models.ApplicationEvent.application_id == app.id).order_by(models.ApplicationEvent.timestamp.desc()).all()
    return events

