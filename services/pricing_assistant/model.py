"""
ShilpSetu Dynamic Pricing Engine.
Runs inference using XGBoost / Gradient Boosting Regressor with fallback to
Indian handicraft market benchmarking rules.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np
from PIL import Image

from services.pricing_assistant.feature_extractor import FeatureExtractor, BENCHMARK_PATH

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "pricing_xgb.json"


class PricingModel:
    """Pricing Engine for Indian Artisan Handicrafts."""

    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.benchmarks = self._load_benchmarks()
        self.xgb_model = self._load_model()

    def _load_benchmarks(self) -> dict:
        if BENCHMARK_PATH.exists():
            with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"categories": {}, "keyword_multipliers": {}}

    def _load_model(self):
        """Loads trained XGBoost model if available."""
        if MODEL_PATH.exists():
            try:
                import xgboost as xgb
                model = xgb.XGBRegressor()
                model.load_model(str(MODEL_PATH))
                return model
            except Exception:
                return None
        return None

    def predict_pricing(
        self,
        image_input: Optional[Union[bytes, Image.Image]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        craft_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Predicts optimal price range and provides market intelligence.

        Returns:
            Dict with price_range (min, suggested, max), confidence, currency, and market_insights.
        """
        # 1. Extract 64-dim feature vector
        features = self.feature_extractor.extract_features(
            image_input=image_input,
            title=title,
            description=description,
            category=category,
            craft_type=craft_type,
            region=region,
        )

        # 2. Benchmark baseline estimation
        bench_res = self._compute_benchmark_price(title, description, category, craft_type)

        # 3. Model inference (if trained model available)
        if self.xgb_model is not None:
            try:
                raw_pred = float(self.xgb_model.predict(features.reshape(1, -1))[0])
                # Blend with benchmark (70% model, 30% empirical benchmark)
                suggested = 0.7 * raw_pred + 0.3 * bench_res["suggested"]
                confidence = 0.88
            except Exception:
                suggested = bench_res["suggested"]
                confidence = 0.78
        else:
            suggested = bench_res["suggested"]
            confidence = 0.82 if bench_res.get("category_matched") else 0.65

        # 4. Enforce realistic price boundaries
        min_bound = bench_res["min"]
        max_bound = bench_res["max"]

        # Ensure suggested is within bounds
        suggested = max(min_bound, min(suggested, max_bound))
        price_min = round(max(50.0, suggested * 0.75), 2)
        price_suggested = round(suggested, 2)
        price_max = round(suggested * 1.35, 2)

        # 5. Market Insights
        category_name = (category or "Handicraft").strip().title()
        cat_info = self.benchmarks.get("categories", {}).get(category_name, {})
        avg_market_price = cat_info.get("avg_market_price", price_suggested)
        competitors = cat_info.get("competitor_count", 120)

        # Identify craft tier
        craft_tier = "Standard Craft"
        if suggested > avg_market_price * 1.5:
            craft_tier = "Master / Heritage Craft"
        elif suggested > avg_market_price * 1.1:
            craft_tier = "Premium Artisan"

        return {
            "price_range": {
                "min": price_min,
                "suggested": price_suggested,
                "max": price_max,
            },
            "currency": "INR",
            "confidence": confidence,
            "market_insights": {
                "category": category_name,
                "craft_tier": craft_tier,
                "avg_category_price": avg_market_price,
                "competitor_count": competitors,
                "pricing_strategy": "Fair Trade Artisan Benchmark",
                "price_trend": "High Demand (Vocal for Local)",
            },
        }

    def _compute_benchmark_price(
        self,
        title: Optional[str],
        description: Optional[str],
        category: Optional[str],
        craft_type: Optional[str],
    ) -> Dict[str, float]:
        """Calculates benchmark price using empirical Indian handicraft index."""
        norm_cat = (category or "").strip().title()
        cat_data = self.benchmarks.get("categories", {}).get(norm_cat)

        category_matched = True
        if not cat_data:
            # Fallback to general handicraft median
            category_matched = False
            base_min = 400.0
            base_sug = 1200.0
            base_max = 3500.0
        else:
            base_min = float(cat_data.get("base_min_price", 400))
            base_sug = float(cat_data.get("base_suggested_price", 1200))
            base_max = float(cat_data.get("base_max_price", 3500))

            # Specific craft type adjustment
            craft_types = cat_data.get("craft_types", {})
            if craft_type:
                for ct_name, ct_info in craft_types.items():
                    if ct_name.lower() in craft_type.lower() or craft_type.lower() in ct_name.lower():
                        base_min = float(ct_info.get("min", base_min))
                        base_sug = float(ct_info.get("suggested", base_sug))
                        base_max = float(ct_info.get("max", base_max))
                        break

        # Check for premium keyword multipliers in text
        full_text = f"{title or ''} {description or ''}".lower()
        multiplier = 1.0
        for kw, mult in self.benchmarks.get("keyword_multipliers", {}).items():
            if kw in full_text:
                multiplier = max(multiplier, mult)

        return {
            "min": round(base_min * multiplier * 0.9, 2),
            "suggested": round(base_sug * multiplier, 2),
            "max": round(base_max * multiplier * 1.15, 2),
            "category_matched": category_matched,
        }
