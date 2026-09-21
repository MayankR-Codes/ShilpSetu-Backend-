"""
Unit tests for AI Description & 'Why Buy This' Generator.
Run: pytest tests/unit/test_description_gen.py -v
"""

import io
import json
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from api_gateway.main import app
from services.voice_cataloger.description_gen import (
    generate_catalog_listing,
    generate_description_from_image,
    _parse_json_response,
)

client = TestClient(app)


def test_parse_json_response_with_markdown_fences():
    raw_llm_output = """```json
    {
        "title_en": "Terracotta Vase",
        "description_en": "Handcrafted clay vase.",
        "why_buy": ["Eco-friendly", "Traditional craftsmanship"]
    }
    ```"""
    parsed = _parse_json_response(raw_llm_output)
    assert parsed["title_en"] == "Terracotta Vase"
    assert len(parsed["why_buy"]) == 2


@patch("services.voice_cataloger.description_gen._get_model")
def test_generate_catalog_listing_includes_why_buy(mock_get_model):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title_en": "Handcrafted Clay Horse",
        "title_hi": "हस्तनिर्मित मिट्टी का घोड़ा",
        "description_en": "Meticulously hand-molded from natural riverbed clay with authentic folk detailing.",
        "description_hi": "प्राकृतिक मिट्टी से निर्मित पारंपरिक घोड़ा।",
        "why_buy": [
            "Authentic handmade relief detail that machine molding cannot replicate",
            "Brings an organic rustic warmth to modern interiors",
            "100% sustainable and chemical-free natural clay"
        ],
        "features": ["Handcrafted clay", "Kiln-baked finish"],
        "seo_tags": ["terracotta", "handmade", "pottery"]
    })
    mock_model.generate_content.return_value = mock_response
    mock_get_model.return_value = mock_model

    result = generate_catalog_listing("This is a handmade clay horse made by me.")
    assert "why_buy" in result
    assert len(result["why_buy"]) == 3
    assert "description_en" in result
    assert "title_en" in result


@patch("services.voice_cataloger.description_gen._get_model")
def test_describe_image_endpoint(mock_get_model):
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "category": "Pottery",
        "craft_type": "Bankura Terracotta",
        "title_en": "Handcrafted Bankura Terracotta Horse",
        "title_hi": "हस्तनिर्मित बांकुरा टेराकोटा घोड़ा",
        "description_en": "Meticulously hand-sculpted from pure riverbed clay, this iconic horse embodies folk artistry. Kiln-fired to a rich earthen amber, it infuses living spaces with rustic heritage warmth.",
        "description_hi": "प्राकृतिक मिट्टी से हस्तनिर्मित, यह बांकुरा टेराकोटा घोड़ा भारतीय लोक कला का प्रतीक है।",
        "why_buy": [
            "Centuries-old Bankura folk tradition handcrafted by rural artisans",
            "Organic earthen warm aesthetic suited for modern minimalist decor",
            "100% biodegradable and non-toxic natural clay"
        ],
        "features": ["Hand-sculpted riverbed clay", "Kiln-fired matte terracotta finish"],
        "seo_tags": ["terracotta", "bankura horse", "indian artisan"]
    })
    mock_model.generate_content.return_value = mock_response
    mock_get_model.return_value = mock_model

    # Create synthetic image bytes
    img = Image.new("RGB", (100, 100), color="orange")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    response = client.post(
        "/api/v1/catalog/voice/describe-image",
        files={"image": ("horse.jpg", img_bytes, "image/jpeg")},
        data={"craft_hint": "Bankura pottery"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "Pottery"
    assert data["craft_type"] == "Bankura Terracotta"
    assert len(data["why_buy"]) >= 3
    assert "description_en" in data
    assert "vocal for local" in data["seo_tags"] or "handmade" in data["seo_tags"]
