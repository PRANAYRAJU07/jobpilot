from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from routers import auth_router, profile_router, document_router, jobs_router, applications_router, ws_router, gmail_router, notifications_router, sources_router
from config import settings
import logging
import time
import os
from sqlalchemy import text
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("jobpilot")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create database tables
@app.on_event("startup")
def startup_event():
    """Create database tables on startup with retry loop so container doesn't crash."""
    for attempt in range(1, 16):
        try:
            logger.info(f"Connecting to database (attempt {attempt}/15)...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables verified/created successfully.")
            break
        except Exception as e:
            if attempt == 15:
                logger.error(f"Could not connect to database after 15 attempts: {e}")
                raise e
            logger.warning(f"Database connection attempt {attempt}/15 failed: {e}. Retrying in 2s...")
            time.sleep(2)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
        headers=headers,
    )

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Error in request {request.method} {request.url.path}: {e}", exc_info=True)
        origin = request.headers.get("origin")
        headers = {}
        if origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)},
            headers=headers,
        )
    process_time = time.time() - start_time
    logger.info(f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Time: {process_time:.4f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response

frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_URL", "http://localhost:3001,http://127.0.0.1:3001,http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(profile_router.router)
app.include_router(document_router.router)
app.include_router(jobs_router.router)
app.include_router(applications_router.router)
app.include_router(gmail_router.router, prefix="/api/gmail", tags=["Gmail"])
app.include_router(notifications_router.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(sources_router.router)
app.include_router(ws_router.router)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "backend"}

@app.get("/api/ready")
def ready_check():
    """Verify DB and Redis dependencies."""
    db_ok = False
    redis_ok = False
    
    # 1. Check PostgreSQL
    try:
        from database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"DB Readiness check failed: {e}")
    finally:
        db.close()
        
    # 2. Check Redis
    try:
        r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, db=0, socket_timeout=1)
        r.ping()
        redis_ok = True
    except Exception as e:
        logger.error(f"Redis Readiness check failed: {e}")
        
    if db_ok and redis_ok:
        return {"status": "ready"}
    else:
        from fastapi import Response
        return Response(content="Dependencies unavailable", status_code=503)

@app.get("/api/config")
@limiter.limit("5/minute")
def get_public_config(request: Request):
    """Retrieve non-sensitive public configuration."""
    return {
        "vapid_public_key": os.getenv("VAPID_PUBLIC_KEY"),
        "features": {
            "application_automation": os.getenv("APPLICATION_AUTOMATION_ENABLED", "true") == "true",
            "gmail_sync": os.getenv("GMAIL_SYNC_ENABLED", "true") == "true",
            "notifications": os.getenv("NOTIFICATIONS_ENABLED", "true") == "true"
        }
    }
