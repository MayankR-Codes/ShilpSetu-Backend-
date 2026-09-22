"""
Unit tests for ShilpSetu Smart Product Classifier Service (Pillar 4).
"""

import io
import json
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from api_gateway.main import app
from services.classifier.taxonomy import (
    CATEGORIES,
    SUB_CATEGORIES,
    GI_REGISTRY,
    get_all_categories,
    get_subcategories,
    find_gi_match,
    normalize_category,
)
from services.classifier.engine import CraftClassifier

client = TestClient(app)


def test_taxonomy_categories_completeness():
    """Verify all 10 core handicraft categories exist and have non-empty subcategories."""
    cats = get_all_categories()
    assert len(cats) == 10
    assert "Pottery" in cats
    assert "Textiles" in cats
    assert "Woodcraft" in cats
    assert "Metalcraft" in cats
    assert "Home Decor" in cats

    for cat in cats:
        subs = get_subcategories(cat)
        assert len(subs) > 0, f"Category {cat} should have subcategories"


def test_gi_registry_lookup():
    """Verify GI tag lookup matches regional crafts correctly."""
    bankura = find_gi_match("Bankura Terracotta Horse")
    assert bankura is not None
    assert bankura["gi_tagged"] is True
    assert bankura["state"] == "West Bengal"

    channapatna = find_gi_match("Channapatna Wooden Toy")
    assert channapatna is not None
    assert channapatna["state"] == "Karnataka"

    unknown = find_gi_match("Random Modern Plastic Box")
    assert unknown is None


def test_material_breakdown_normalization():
    """Verify material proportions are normalized to 100%."""
    classifier = CraftClassifier()

    # Case 1: Custom artisan materials provided
    artisan_input = [
        {"material": "River Stone", "percentage": 40.0},
        {"material": "Wood Slice", "percentage": 40.0},
    ]
    # Sums to 80 -> should re-normalize to 50% each (total 100)
    normalized = classifier._normalize_materials(None, artisan_input)
    assert len(normalized) == 2
    total = sum(item["percentage"] for item in normalized)
    assert round(total, 1) == 100.0

    # Case 2: No materials provided -> fallback default
    empty_norm = classifier._normalize_materials(None, None)
    assert len(empty_norm) >= 1
    assert empty_norm[0]["percentage"] == 100.0


def test_classifier_offline_heuristic():
    """Verify local heuristic classifier provides valid taxonomy and material breakdown."""
    classifier = CraftClassifier()
    dummy_img = Image.new("RGB", (100, 100), color=(180, 100, 60))  # Terracotta clay tone

    result = classifier._classify_with_heuristics(
        pil_image=dummy_img,
        artisan_materials=[
            {"material": "Clay", "percentage": 80.0},
            {"material": "Sand", "percentage": 20.0},
        ],
        artisan_hint="Handmade clay mitti pot",
    )

    assert result["primary_category"] == "Pottery"
    assert "Terracotta" in result["sub_category"]
    assert result["confidence"] > 0.70
    assert len(result["materials_breakdown"]) == 2
    assert result["materials_breakdown"][0]["material"] == "Clay"


# ── API Endpoint Tests ─────────────────────────────────────────────

def test_get_taxonomy_endpoint():
    """Test GET /api/v1/classifier/taxonomy."""
    response = client.get("/api/v1/classifier/taxonomy")
    assert response.status_code == 200
    data = response.json()
    assert data["total_categories"] == 10
    assert "Pottery" in data["categories"]
    assert "sub_categories" in data
    assert data["total_gi_crafts"] >= 10


def test_detect_gi_endpoint():
    """Test POST /api/v1/classifier/detect-gi."""
    # Test valid GI craft
    response = client.post(
        "/api/v1/classifier/detect-gi",
        data={"craft_name": "Moradabad Brass Pooja Thali"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_gi_tagged"] is True
    assert data["gi_details"]["state"] == "Uttar Pradesh"

    # Test non-GI craft
    response_non = client.post(
        "/api/v1/classifier/detect-gi",
        data={"craft_name": "Modern Synthetic Glass"},
    )
    assert response_non.status_code == 200
    data_non = response_non.json()
    assert data_non["is_gi_tagged"] is False


def test_classify_craft_endpoint_with_materials():
    """Test POST /api/v1/classifier/classify with uploaded image and artisan materials."""
    # Create simple in-memory test image
    img = Image.new("RGB", (120, 120), color="peru")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    materials_json = json.dumps([
        {"material": "Baked Clay", "percentage": 75.0},
        {"material": "Natural Red Slip", "percentage": 25.0},
    ])

    response = client.post(
        "/api/v1/classifier/classify",
        files={"image": ("craft.png", buf.getvalue(), "image/png")},
        data={
            "artisan_materials": materials_json,
            "artisan_hint": "Bishnupur Terracotta figurine",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "primary_category" in data
    assert "sub_category" in data
    assert "craft_heritage" in data
    assert "materials_breakdown" in data
    assert len(data["materials_breakdown"]) >= 1
    assert data["confidence"] > 0.0
