"""
Integration tests for the API Gateway.
Run: pytest tests/integration/test_gateway.py -v
Requires: uvicorn running OR use TestClient (no server needed).
"""

import pytest
from fastapi.testclient import TestClient
from api_gateway.main import app

client = TestClient(app)


# ── Health Check ───────────────────────────────────────────────────

def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_docs_accessible():
    response = client.get("/docs")
    assert response.status_code == 200


# ── Auth Tests ─────────────────────────────────────────────────────

def test_login_returns_token():
    response = client.post("/api/v1/auth/login", json={
        "username": "test_artisan",
        "password": "shilpsetu123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401():
    response = client.post("/api/v1/auth/login", json={
        "username": "test_artisan",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


def test_enhance_without_token_returns_403():
    import io
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(buf, format="JPEG")
    buf.seek(0)

    response = client.post(
        "/api/v1/image/enhance",
        files={"file": ("test.jpg", buf, "image/jpeg")},
    )
    assert response.status_code in (401, 403)
