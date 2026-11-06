import os
import sys
import logging
from datetime import datetime

# Ensure backend directory is on sys.path both in container (/app) and host
for candidate_path in ["/app", os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/backend"))]:
    if os.path.isdir(candidate_path) and candidate_path not in sys.path:
        sys.path.insert(0, candidate_path)

from workers.celery_app import celery_app
from database import SessionLocal
import models
from services.gmail_service import GmailService
from services.email_intelligence import EmailIntelligenceService

logger = logging.getLogger("jobpilot.gmail_tasks")


@celery_app.task(name="tasks.gmail.sync_all_connections")
def sync_all_connections():
    db = SessionLocal()
    try:
        connections = db.query(models.GmailConnection).filter_by(status="CONNECTED").all()
        for conn in connections:
            sync_gmail_connection.delay(str(conn.id))
    finally:
        db.close()


@celery_app.task(name="tasks.gmail.sync_gmail_connection")
def sync_gmail_connection(connection_id: str):
    db = SessionLocal()
    try:
        connection = db.query(models.GmailConnection).filter_by(id=connection_id).first()
        if not connection or connection.status not in ["CONNECTED", "ACTIVE"]:
            return

        logger.info(f"Syncing Gmail for connection {connection_id}")
        gmail_service = GmailService(db, connection)
        new_messages, new_history_id = gmail_service.fetch_new_messages(limit=20)
        intelligence_service = EmailIntelligenceService(db)

        for msg_data in new_messages:
            email_record = intelligence_service.classify_and_match(msg_data, connection)
            logger.info(f"Classified email {email_record.id} as {email_record.classification}")

        if new_history_id:
            connection.last_history_id = str(new_history_id)

        connection.last_sync_at = datetime.utcnow()
        db.commit()
    except Exception as e:
        logger.error(f"Error in sync_gmail_connection: {e}")
        db.rollback()
    finally:
        db.close()
