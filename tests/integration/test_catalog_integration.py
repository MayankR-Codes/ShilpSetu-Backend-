"""
Integration tests for the Product Catalog Service and Unified Multi-Modal AI pipeline.
Run: pytest tests/integration/test_catalog_integration.py -v
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from api_gateway.main import app
from shared.db.session import get_db
from shared.db.models import Product

client = TestClient(app)


@pytest.fixture
def mock_db():
    session = AsyncMock()
    products = []

    def sync_add(item):
        if not getattr(item, "id", None):
            item.id = len(products) + 1
        if not getattr(item, "created_at", None):
            item.created_at = datetime.utcnow()
        if not getattr(item, "updated_at", None):
            item.updated_at = datetime.utcnow()
        products.append(item)

    session.add = MagicMock(side_effect=sync_add)

    async def fake_refresh(item):
        if not getattr(item, "id", None):
            item.id = len(products)
        if not getattr(item, "created_at", None):
            item.created_at = datetime.utcnow()
        if not getattr(item, "updated_at", None):
            item.updated_at = datetime.utcnow()

    async def fake_commit():
        pass

    async def fake_execute(query):
        result_mock = MagicMock()
        # Return a copy of products reversed
        result_mock.scalars.return_value.all.return_value = list(reversed(products))
        result_mock.scalar_one_or_none.return_value = products[-1] if products else None
        return result_mock

    session.refresh.side_effect = fake_refresh
    session.commit.side_effect = fake_commit
    session.execute.side_effect = fake_execute

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield session
    app.dependency_overrides.clear()


def test_create_product(mock_db):
    payload = {
        "artisan_id": "artisan_123",
        "title_en": "Handcrafted Terracotta Vase",
        "title_hi": "हस्तनिर्मित टेराकोटा फूलदान",
        "description_en": "Authentic clay vase handmade by rural artisans.",
        "description_hi": "ग्रामीण कारीगरों द्वारा हस्तनिर्मित मिट्टी का फूलदान।",
        "category": "Pottery",
        "enhanced_image_url": "/uploads/products/vase_enhanced.webp",
        "features": ["100% natural clay", "Eco-friendly", "Hand-painted"],
        "tags": ["handmade", "pottery", "terracotta", "shilpsetu"]
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["artisan_id"] == "artisan_123"
    assert data["id"] == 1
    assert data["features"] == ["100% natural clay", "Eco-friendly", "Hand-painted"]
    assert "handmade" in data["tags"]


def test_get_catalog_feed(mock_db):
    # First create a product
    client.post("/api/v1/products", json={
        "artisan_id": "artisan_999",
        "title_en": "Pochampally Silk Saree",
        "enhanced_image_url": "/uploads/products/saree.webp"
    })

    # Fetch feed
    response = client.get("/api/v1/products/feed?limit=10&offset=0")
    assert response.status_code == 200
    feed = response.json()
    assert len(feed) >= 1
    assert feed[0]["title_en"] == "Pochampally Silk Saree"


def test_legacy_voice_save_and_feed(mock_db):
    # Test backwards compatibility of /api/v1/catalog/voice/save
    legacy_payload = {
        "artisan_id": "artisan_legacy_1",
        "title_en": "Brass Diya",
        "title_hi": "पीतल का दीया",
        "description_en": "Traditional brass diya for pooja",
        "description_hi": "पूजा के लिए पीतल का दीया",
        "enhanced_image_url": "/uploads/products/diya.webp"
    }
    save_resp = client.post("/api/v1/catalog/voice/save", json=legacy_payload)
    assert save_resp.status_code in (200, 201)
    assert save_resp.json()["status"] == "success"

    # Test backwards compatibility of /api/v1/catalog/voice/feed
    feed_resp = client.get("/api/v1/catalog/voice/feed")
    assert feed_resp.status_code == 200
    assert len(feed_resp.json()) >= 1


@patch("services.catalog.main.image_pipeline.run")
@patch("services.catalog.main.transcribe_audio")
@patch("services.catalog.main.translate_catalog_text")
@patch("services.catalog.main.generate_catalog_listing")
def test_unified_ai_product_creation(
    mock_llm, mock_trans, mock_asr, mock_img_pipeline, mock_db
):
    # 1. Mock image enhancement pipeline
    mock_img_pipeline.return_value = {
        "url": "/uploads/products/mock_enhanced.webp",
        "quality_score": 85.5,
        "original_size": [800, 600],
        "enhanced_size": [1600, 1200],
    }

    # 2. Mock speech-to-text
    mock_asr.return_value = {
        "text": "yeh ek mitti ka ghada hai jo maine banaya hai",
        "language": "hi",
    }

    # 3. Mock translation
    mock_trans.return_value = {
        "english": "This is a clay pot made by me.",
        "hindi": "यह एक मिट्टी का घड़ा है जो मैंने बनाया है।",
    }

    # 4. Mock LLM generator
    mock_llm.return_value = {
        "title_en": "Artisanal Handmade Clay Water Pot",
        "title_hi": "पारंपरिक हस्तनिर्मित मिट्टी का घड़ा",
        "description_en": "Keep your water naturally cool with this artisanal clay pot.",
        "description_hi": "इस मिट्टी के घड़े से पानी को प्राकृतिक रूप से ठंडा रखें।",
        "features": ["Keeps water cool", "Chemical free", "Handmade by Indian potters"],
        "seo_tags": ["terracotta", "clay pot", "handmade"],
    }

    # Generate dummy image bytes
    img = Image.new("RGB", (100, 100), color="red")
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG")
    img_bytes = img_buf.getvalue()

    # Generate dummy audio bytes
    audio_bytes = b"ID3" + b"\x00" * 2000

    response = client.post(
        "/api/v1/products/create-ai",
        files={
            "image": ("test_pot.jpg", img_bytes, "image/jpeg"),
            "audio": ("test_voice.mp3", audio_bytes, "audio/mpeg"),
        },
        data={
            "artisan_id": "artisan_rajesh",
            "language_hint": "hi",
            "auto_save": "true",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["artisan_id"] == "artisan_rajesh"
    assert data["title_en"] == "Artisanal Handmade Clay Water Pot"
    assert data["enhanced_image_url"] == "/uploads/products/mock_enhanced.webp"
    assert data["quality_score"] == 85.5
    assert data["detected_language"] == "hi"
    assert data["is_saved"] is True
    assert data["product_id"] is not None
    assert "handmade" in data["tags"]
    assert len(data["features"]) == 3
