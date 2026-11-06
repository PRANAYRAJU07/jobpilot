from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
import models
import auth
from encryption import encrypt_token
import os
import uuid
import datetime
import redis as redis_lib
import requests as http_requests

router = APIRouter()

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:8001/api/gmail/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")


def get_redis():
    return redis_lib.Redis(
        host=os.getenv("REDIS_HOST", "redis"),
        port=6379,
        db=1,
        decode_responses=True
    )


def get_credentials():
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Gmail OAuth credentials not configured. Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET."
        )
    return client_id, client_secret


@router.get("/auth-url")
def get_auth_url(current_user: models.User = Depends(auth.get_current_user)):
    """Generate the Google OAuth authorization URL (no PKCE — standard flow)."""
    client_id, _ = get_credentials()
    state = f"{current_user.id}:{uuid.uuid4()}"

    try:
        r = get_redis()
        r.setex(f"gmail_oauth_state:{state}", 600, str(current_user.id))
    except Exception:
        pass

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    query = "&".join(f"{k}={http_requests.utils.quote(str(v))}" for k, v in params.items())
    auth_url = f"{base_url}?{query}"

    return {"url": auth_url}


@router.get("/callback")
def oauth_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth redirect. Exchange code for tokens and encrypt before storing."""
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error={error}")

    if not code or not state:
        return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error=missing_code_or_state")

    try:
        parts = state.split(":")
        if len(parts) < 2:
            return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error=invalid_state")
        user_id = parts[0]

        try:
            r = get_redis()
            stored_user = r.get(f"gmail_oauth_state:{state}")
            if stored_user and stored_user != str(user_id):
                return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error=state_mismatch")
            r.delete(f"gmail_oauth_state:{state}")
        except Exception:
            pass

        client_id, client_secret = get_credentials()

        token_response = http_requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10
        )

        if token_response.status_code != 200:
            err_detail = token_response.json().get("error_description", token_response.text)
            return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error={http_requests.utils.quote(err_detail[:100])}")

        tokens = token_response.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token", "")

        userinfo_response = http_requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        email_address = ""
        if userinfo_response.status_code == 200:
            email_address = userinfo_response.json().get("email", "")

        connection = db.query(models.GmailConnection).filter(
            models.GmailConnection.user_id == user_id
        ).first()

        now = datetime.datetime.utcnow()
        expires_in = tokens.get("expires_in", 3600)
        token_expires_at = now + datetime.timedelta(seconds=expires_in)

        enc_access = encrypt_token(access_token) if access_token else ""
        enc_refresh = encrypt_token(refresh_token) if refresh_token else ""

        if not connection:
            connection = models.GmailConnection(
                user_id=user_id,
                email_address=email_address or "unknown",
                encrypted_access_token=enc_access,
                encrypted_refresh_token=enc_refresh,
                token_expires_at=token_expires_at,
                status="CONNECTED",
            )
            db.add(connection)
        else:
            connection.email_address = email_address or connection.email_address or "unknown"
            connection.encrypted_access_token = enc_access
            if enc_refresh:
                connection.encrypted_refresh_token = enc_refresh
            connection.token_expires_at = token_expires_at
            connection.status = "CONNECTED"

        db.commit()
        return RedirectResponse(url=f"{FRONTEND_URL}/gmail?connected=true")

    except HTTPException:
        raise
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/gmail?error={http_requests.utils.quote(str(e)[:100])}")


@router.get("/connection")
def get_gmail_connection(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    connection = db.query(models.GmailConnection).filter(
        models.GmailConnection.user_id == current_user.id
    ).first()

    if not connection or connection.status != "CONNECTED":
        return None

    return {
        "id": str(connection.id),
        "user_id": str(connection.user_id),
        "connected": True,
        "email": connection.email_address,
        "status": connection.status,
        "last_sync_at": connection.last_sync_at,
        "history_id": connection.last_history_id,
        "created_at": connection.created_at,
    }


@router.get("/status")
def get_gmail_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    connection = db.query(models.GmailConnection).filter(
        models.GmailConnection.user_id == current_user.id
    ).first()

    if not connection:
        return {"status": "DISCONNECTED"}

    return {
        "status": connection.status,
        "email_address": connection.email_address,
        "last_sync_at": getattr(connection, 'last_sync_at', None),
    }


@router.delete("/disconnect")
@router.post("/disconnect")
def disconnect_gmail(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    connection = db.query(models.GmailConnection).filter(
        models.GmailConnection.user_id == current_user.id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="No Gmail connection found")

    connection.status = "DISCONNECTED"
    connection.encrypted_access_token = ""
    connection.encrypted_refresh_token = ""
    db.commit()
    return {"message": "Gmail disconnected successfully"}
