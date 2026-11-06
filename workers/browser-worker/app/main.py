from celery import Celery
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("jobpilot.browser_worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "jobpilot_browser_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.submission"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_routes={
        "app.submission.*": {"queue": "browser.application"}
    }
)
