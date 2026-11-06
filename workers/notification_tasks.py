import os
import sys
import json
import logging
from datetime import datetime
import redis
from sqlalchemy.exc import IntegrityError

for candidate_path in ["/app", os.path.abspath(os.path.join(os.path.dirname(__file__), "../apps/backend"))]:
    if os.path.isdir(candidate_path) and candidate_path not in sys.path:
        sys.path.insert(0, candidate_path)

from workers.celery_app import celery_app
from database import SessionLocal
import models
from services.push_service import push_channel, MockPushProvider
from services.notification_policy import NotificationPolicy

logger = logging.getLogger("jobpilot.notification_tasks")

if os.getenv("TESTING") == "true":
    push_channel = MockPushProvider()


@celery_app.task(name="tasks.notifications.enqueue", bind=True, max_retries=4)
def enqueue_notification(self, notification_data: dict):
    db = SessionLocal()
    try:
        user_id = notification_data["user_id"]
        preference = db.query(models.NotificationPreference).filter_by(user_id=user_id).first()

        priority = NotificationPolicy.get_priority(notification_data["type"])
        if not NotificationPolicy.should_deliver(notification_data["type"], preference):
            logger.info(f"Notification {notification_data['type']} ignored per user preferences")
            return

        initial_status = NotificationPolicy.get_delivery_status(notification_data["type"], preference)

        notification = models.Notification(
            user_id=user_id,
            type=notification_data["type"],
            priority=priority,
            title=notification_data["title"],
            body=notification_data["body"],
            payload=notification_data.get("payload"),
            source_event_id=notification_data.get("source_event_id"),
            dedupe_key=notification_data["dedupe_key"],
            status=initial_status
        )

        db.add(notification)

        try:
            db.commit()
            db.refresh(notification)
        except IntegrityError:
            db.rollback()
            logger.info(f"Duplicate notification {notification_data['dedupe_key']} ignored.")
            return

        if initial_status == "PENDING":
            try:
                r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0)
                ws_payload = {
                    "event": "NOTIFICATION_CREATED",
                    "data": {
                        "id": str(notification.id),
                        "type": notification.type,
                        "priority": notification.priority,
                        "title": notification.title,
                        "body": notification.body,
                        "created_at": notification.created_at.isoformat()
                    }
                }
                r.publish(f"user_events:{user_id}", json.dumps(ws_payload))
            except Exception:
                pass

            if preference and preference.web_push_enabled:
                process_web_push.delay(str(notification.id))
            else:
                notification.status = "DELIVERED"
                notification.delivered_at = datetime.utcnow()
                db.commit()

    except Exception as e:
        logger.error(f"Error enqueueing notification: {str(e)}")
        raise self.retry(exc=e, countdown=30)
    finally:
        db.close()


@celery_app.task(name="tasks.notifications.process_web_push", bind=True, max_retries=4)
def process_web_push(self, notification_id: str):
    db = SessionLocal()
    try:
        notification = db.query(models.Notification).filter_by(id=notification_id).first()
        if not notification or notification.status in ["DELIVERED", "READ", "CANCELLED"]:
            return

        notification.status = "SENDING"
        db.commit()

        subs = db.query(models.PushSubscription).filter_by(user_id=notification.user_id, active=True).all()

        if not subs:
            notification.status = "DELIVERED"
            db.commit()
            return

        push_data = {
            "title": notification.title,
            "body": notification.body,
            "type": notification.type,
            "id": str(notification.id)
        }

        all_success = True

        for sub in subs:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth
                }
            }

            result = push_channel.send(push_data, sub_info)

            if result == "INVALID_SUBSCRIPTION":
                sub.active = False
                sub.last_failure_at = datetime.utcnow()
            elif result == "TRANSIENT_FAILURE":
                all_success = False
                sub.last_failure_at = datetime.utcnow()
            elif result == "SUCCESS":
                sub.last_success_at = datetime.utcnow()

        db.commit()

        if not all_success:
            backoff = [30, 120, 600, 1800]
            delay = backoff[self.request.retries] if self.request.retries < len(backoff) else 1800

            notification.status = "FAILED"
            notification.failed_at = datetime.utcnow()
            notification.failure_reason = "TRANSIENT_FAILURE"
            db.commit()

            raise self.retry(countdown=delay)

        notification.status = "DELIVERED"
        notification.delivered_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"Error in web push: {str(e)}")
        notification = db.query(models.Notification).filter_by(id=notification_id).first()
        if notification:
            notification.status = "FAILED"
            notification.failed_at = datetime.utcnow()
            notification.failure_reason = str(e)
            db.commit()
    finally:
        db.close()
