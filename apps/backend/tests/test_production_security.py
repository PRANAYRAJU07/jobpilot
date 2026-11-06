import pytest
from fastapi.testclient import TestClient
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

client = TestClient(app)

def test_cors_policy():
    """Verify that wildcard origin is blocked for production."""
    response = client.options("/api/config", headers={"Origin": "http://evil-domain.com"})
    assert "access-control-allow-origin" not in response.headers or response.headers["access-control-allow-origin"] != "*"

def test_health_endpoint_no_secrets_leaked():
    """Ensure readiness/health endpoints don't leak passwords in tracebacks."""
    response = client.get("/ready")
    assert response.status_code in [200, 503]
    text = response.text.lower()
    assert "password" not in text
    assert "secret" not in text
    assert "traceback" not in text

def test_public_config_no_secrets():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "vapid_private_key" not in data
    assert "ENCRYPTION_KEY" not in data
    assert "DATABASE_URL" not in data

def test_rate_limiting_active():
    """Ensure slowapi limit is enforced."""
    for _ in range(6):
        response = client.get("/api/config")
    # 6th request should hit 429 Too Many Requests
    assert response.status_code == 429
