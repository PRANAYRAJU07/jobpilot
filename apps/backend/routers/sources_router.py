from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import models
import auth
from database import get_db
from workers.tasks.job_tasks import run_discovery_for_source_task, schedule_active_sources_task

router = APIRouter(prefix="/api/sources", tags=["sources"])


class SourceCreate(BaseModel):
    company: str
    source_type: str  # GREENHOUSE, LEVER, ASHBY, DIRECT_CAREER, LINKEDIN, INTERNSHALA, NAUKRI
    external_company_id: str
    career_url: str
    country_focus: Optional[str] = "INDIA"
    scan_interval_minutes: Optional[int] = 30
    tags: Optional[List[str]] = []


@router.get("/")
def list_sources(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return db.query(models.JobSourceRegistry).order_by(models.JobSourceRegistry.company.asc()).all()


@router.post("/")
def create_source(
    source_in: SourceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    valid_types = {"GREENHOUSE", "LEVER", "ASHBY", "DIRECT_CAREER", "LINKEDIN", "INTERNSHALA", "NAUKRI"}
    stype = source_in.source_type.upper().strip()
    if stype not in valid_types:
        raise HTTPException(status_code=400, detail=f"source_type must be one of {sorted(valid_types)}")

    new_source = models.JobSourceRegistry(
        company=source_in.company.strip(),
        source_type=stype,
        external_company_id=source_in.external_company_id.strip(),
        career_url=source_in.career_url.strip(),
        country_focus=source_in.country_focus or "INDIA",
        scan_interval_minutes=source_in.scan_interval_minutes or 30,
        tags=source_in.tags or [],
        enabled=True,
        status="ACTIVE",
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return new_source


@router.post("/scan-all")
def trigger_scan_all(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    sources = db.query(models.JobSourceRegistry).filter_by(enabled=True).all()
    queued = 0
    for src in sources:
        try:
            run_discovery_for_source_task.delay(str(src.id))
            queued += 1
        except Exception:
            pass
    return {"message": f"Queued discovery scan for {queued} active sources", "queued_count": queued}


@router.post("/{source_id}/scan")
def trigger_scan(source_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    source = db.query(models.JobSourceRegistry).filter_by(id=source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    run_discovery_for_source_task.delay(str(source.id))
    return {"message": "Scan queued", "source_id": str(source.id)}


@router.post("/{source_id}/toggle")
def toggle_source(source_id: str, enabled: bool, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    source = db.query(models.JobSourceRegistry).filter_by(id=source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source.enabled = enabled
    if enabled and source.status in ("UNSUPPORTED", "PAUSED"):
        source.status = "ACTIVE"
    db.commit()
    return {"message": f"Source enabled set to {enabled}", "enabled": enabled}
