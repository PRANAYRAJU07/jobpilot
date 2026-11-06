from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
import hashlib
import os
import re

import models
import auth
from database import get_db

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = os.getenv("RESUME_UPLOAD_DIR", "/tmp/jobpilot_uploads/resumes")


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Auto-create CandidateProfile if user doesn't have one yet
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

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    file_hash = hashlib.sha256(content).hexdigest()

    # Save file to disk so browser-worker or user can reference it
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = re.sub(r"[^A-Za-z0-9_.\-]", "_", file.filename or "resume.pdf")
    saved_path = os.path.join(UPLOAD_DIR, f"{profile.id}_{safe_name}")
    try:
        with open(saved_path, "wb") as f_out:
            f_out.write(content)
    except Exception:
        saved_path = None

    existing = db.query(models.Document).filter(
        models.Document.profile_id == profile.id,
        models.Document.hash == file_hash
    ).first()

    if existing:
        doc_record = existing
        doc_record.filename = file.filename or existing.filename
        doc_record.file_path = saved_path or existing.file_path
    else:
        doc_record = models.Document(
            profile_id=profile.id,
            filename=file.filename or "resume.pdf",
            hash=file_hash,
            source="upload",
            document_type=file.content_type or "application/pdf",
            verification_status="VERIFIED",
            file_path=saved_path,
        )
        db.add(doc_record)
        db.commit()
        db.refresh(doc_record)

    # Parse resume, learn skills, extract projects & metadata, and populate Evidence Graph
    from services.document_intelligence import DocumentIntelligenceService
    doc_service = DocumentIntelligenceService(db)
    parse_summary = doc_service.parse_and_populate(doc_record, raw_bytes=content)

    # Immediately cross-validate the freshest 50 jobs for fast UI feedback
    from services.job_engine import JobEngineService
    job_engine = JobEngineService(db)
    rematch_summary = job_engine.re_evaluate_all_jobs_for_profile(profile, send_alerts_for_top=0, limit=50)

    # Background task to evaluate remaining jobs & dispatch alerts without slowing down upload response
    def run_full_evaluation(profile_id: str):
        from database import SessionLocal
        bg_db = SessionLocal()
        try:
            bg_profile = bg_db.query(models.CandidateProfile).filter(models.CandidateProfile.id == profile_id).first()
            if bg_profile:
                bg_engine = JobEngineService(bg_db)
                bg_engine.re_evaluate_all_jobs_for_profile(bg_profile, send_alerts_for_top=5)
                bg_engine.re_evaluate_all_jobs_for_profile(bg_profile, send_alerts_for_top=10)
        except Exception as e:
            import logging
            logging.getLogger("jobpilot").error(f"Background evaluation error: {e}")
        finally:
            bg_db.close()

    background_tasks.add_task(run_full_evaluation, str(profile.id))

    return {
        "message": "Resume uploaded, skills learned, and jobs cross-validated successfully",
        "document_id": str(doc_record.id),
        "filename": doc_record.filename,
        "parse_summary": parse_summary,
        "rematch_summary": rematch_summary,
    }


@router.get("/")
def list_documents(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        return []
    docs = (
        db.query(models.Document)
        .filter(models.Document.profile_id == profile.id)
        .order_by(models.Document.upload_timestamp.desc())
        .all()
    )
    return docs


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(models.CandidateProfile).filter(models.CandidateProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.profile_id == profile.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Detach claims referencing this document before deletion
    db.query(models.CandidateClaim).filter(
        models.CandidateClaim.document_evidence_id == doc.id
    ).update({"document_evidence_id": None})

    db.delete(doc)
    db.commit()
    return {"status": "DELETED", "document_id": document_id}
