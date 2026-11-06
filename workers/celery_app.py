from celery import Celery
import os
import logging

logger = logging.getLogger("jobpilot.worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "jobpilot_workers",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "workers.tasks.job_tasks",
        "workers.gmail_tasks",
        "workers.notification_tasks",
    ],
)

# Alias `app` so legacy `from workers.celery_app import app` also works seamlessly
app = celery_app

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "schedule_active_sources": {
            "task": "workers.tasks.job_tasks.schedule_active_sources_task",
            "schedule": 300.0,  # Every 5 minutes check for due sources
        },
        "sync_gmail_connections": {
            "task": "tasks.gmail.sync_all_connections",
            "schedule": 600.0,  # Every 10 minutes sync connected Gmail accounts
        },
    },
)
