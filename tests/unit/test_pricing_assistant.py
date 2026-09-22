"""
Unit tests for ShilpSetu Dynamic Pricing Assistant (Pillar 3).
Run: pytest tests/unit/test_pricing_assistant.py -v
"""

from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import pytest
from PIL import Image
import numpy as np
from fastapi.testclient import TestClient

from api_gateway.main import app
from services.pricing_assistant.feature_extractor import FeatureExtractor
from services.pricing_assistant.model import PricingModel
from shared.db.session import get_db
from shared.db.models import Product

client = TestClient(app)


# ── Feature Extractor Tests ────────────────────────────────────────

def test_feature_vector_shapes():
    extractor = FeatureExtractor()

    # Synthetic 100x100 RGB image
    pil_img = Image.new("RGB", (100, 100), color="blue")

    v_feats = extractor.extract_visual_features(pil_img)
    assert v_feats.shape == (32,), f"Expected 32 visual features, got {v_feats.shape}"

    t_feats = extractor.extract_text_features("Pure Silk Saree", "Intricate gold zari border")
    assert t_feats.shape == (16,), f"Expected 16 text features, got {t_feats.shape}"

    c_feats = extractor.extract_categorical_features("Textiles", "Banarasi", "Uttar Pradesh")
    assert c_feats.shape == (16,), f"Expected 16 categorical features, got {c_feats.shape}"

    full_vector = extractor.extract_features(
        image_input=pil_img,
        title="Pure Silk Saree",
        description="Intricate gold zari border",
        category="Textiles",
        craft_type="Banarasi",
        region="Uttar Pradesh",
    )
    assert full_vector.shape == (64,), f"Expected 64 total features, got {full_vector.shape}"


def test_feature_extractor_handles_none():
    extractor = FeatureExtractor()
    full_vector = extractor.extract_features(
        image_input=None,
        title=None,
        description=None,
        category=None,
    )
    assert full_vector.shape == (64,)
    assert not np.isnan(full_vector).any()


# ── Model & Pricing Logic Tests ────────────────────────────────────

def test_pricing_model_prediction_structure():
    model = PricingModel()
    result = model.predict_pricing(
        title="Handcrafted Terracotta Clay Water Pot",
        description="Cool water naturally with this handmade earthen pot.",
        category="Pottery",
        craft_type="Terracotta",
    )

    assert "price_range" in result
    pr = result["price_range"]
    assert "min" in pr and "suggested" in pr and "max" in pr
    assert pr["min"] <= pr["suggested"] <= pr["max"]
    assert pr["min"] >= 50.0

    assert result["currency"] == "INR"
    assert 0.0 <= result["confidence"] <= 1.0
    assert "market_insights" in result
    assert result["market_insights"]["category"] == "Pottery"


def test_premium_craft_pricing_higher_than_basic():
    model = PricingModel()

    basic_terracotta = model.predict_pricing(
        title="Simple clay cup",
        description="Plain unpainted clay cup",
        category="Pottery",
        craft_type="Terracotta",
    )

    premium_silk = model.predict_pricing(
        title="Pure Katan Silk Banarasi Saree",
        description="Handwoven with pure gold zari and intricate royal floral motifs.",
        category="Textiles",
        craft_type="Banarasi",
    )

    assert premium_silk["price_range"]["suggested"] > basic_terracotta["price_range"]["suggested"]


# ── API Endpoint Tests ─────────────────────────────────────────────

def test_suggest_price_endpoint():
    payload = {
        "title": "Moradabad Brass Pooja Thali",
        "description": "Authentic engraved solid brass plate for religious rituals.",
        "category": "Metalcraft",
        "craft_type": "Moradabad Brass",
        "region": "Uttar Pradesh",
    }
    response = client.post("/api/v1/pricing/suggest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "price_range" in data
    assert data["price_range"]["suggested"] >= 500
    assert data["currency"] == "INR"
    assert "market_insights" in data


def test_apply_pricing_to_product_endpoint():
    # Mock DB session with a product
    fake_product = Product(
        id=42,
        artisan_id="artisan_77",
        title_en="Handmade Saharanpur Carved Wooden Box",
        description_en="Teak wood jewelry keepsake box with intricate floral carving.",
        category="Woodcraft",
        craft_type="Saharanpur",
    )

    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = fake_product
    session.execute.return_value = result_mock

    async def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post("/api/v1/pricing/apply/42")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["product_id"] == 42
        assert data["price_suggested"] > 0
        assert data["price_min"] <= data["price_suggested"] <= data["price_max"]
    finally:
        app.dependency_overrides.clear()


def test_artisan_cost_plus_floor_protection():
    """Artisan provides raw material cost and desired minimum profit; ensure minimum floor is never violated."""
    model = PricingModel()
    result = model.predict_pricing(
        title="Handcrafted Terracotta Planter",
        description="Earthy clay planter pot",
        category="Pottery",
        craft_type="Terracotta",
        raw_material_cost=300.0,
        min_profit=250.0,
    )
    cost_info = result.get("cost_analysis")
    assert cost_info is not None
    assert cost_info["raw_material_cost"] == 300.0
    assert cost_info["min_profit_desired"] == 250.0
    assert cost_info["cost_floor"] == 550.0
    assert result["price_range"]["min"] >= 550.0
    assert result["price_range"]["suggested"] >= 550.0
    assert cost_info["projected_profit"] >= 250.0


def test_artisan_cost_plus_market_surplus():
    """When market value exceeds cost floor, artisan enjoys extra surplus profit."""
    model = PricingModel()
    result = model.predict_pricing(
        title="Pure Katan Silk Banarasi Saree",
        description="Handwoven pure silk bridal saree with gold zari work.",
        category="Textiles",
        craft_type="Banarasi",
        raw_material_cost=2000.0,
        min_profit=1500.0,
    )
    cost_info = result.get("cost_analysis")
    assert cost_info is not None
    assert cost_info["cost_floor"] == 3500.0
    # Banarasi saree market valuation is typically >= ₹6000
    assert result["price_range"]["suggested"] >= 3500.0
    assert cost_info["surplus_above_min_profit"] >= 0
    assert cost_info["profit_margin_pct"] > 0
    assert "Market Value Premium" in result["market_insights"]["pricing_strategy"]


def test_suggest_endpoint_with_artisan_cost_inputs():
    """Test API endpoint /suggest with raw_material_cost and min_profit."""
    payload = {
        "title": "Channapatna Wooden Stacking Toy",
        "description": "Safe natural lacquer non-toxic wooden toy for kids.",
        "category": "Woodcraft",
        "craft_type": "Channapatna",
        "raw_material_cost": 180.0,
        "min_profit": 120.0,
    }
    response = client.post("/api/v1/pricing/suggest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "cost_analysis" in data
    cost_data = data["cost_analysis"]
    assert cost_data["raw_material_cost"] == 180.0
    assert cost_data["min_profit_desired"] == 120.0
    assert cost_data["cost_floor"] == 300.0
    assert data["price_range"]["min"] >= 300.0
    assert cost_data["projected_profit"] >= 120.0

