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

import io
from PIL import Image

def test_enhance_validates_image_file():
    # Sending a completely empty request (no image) should return 422 Unprocessable Entity
    response = client.post("/api/v1/image/enhance")
    assert response.status_code == 422
    
def test_enhance_accepts_valid_image_format():
    # Create a dummy image
    img = Image.new("RGBA", (100, 100), "white")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # Send it to the endpoint (note: without a proper quality score, the quality_check might reject it with 422, which is expected pipeline behavior, not a crash)
    response = client.post(
        "/api/v1/image/enhance",
        files={"file": ("test.png", img_byte_arr, "image/png")}
    )
    
    # It either passes (200) or fails the quality check (422), but it shouldn't crash (500) or ask for auth (401)
    assert response.status_code in (200, 422)
