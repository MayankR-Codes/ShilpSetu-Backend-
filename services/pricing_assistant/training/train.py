"""
Training script for ShilpSetu XGBoost Pricing Regressor.
Fits an XGBoost model on Indian handicraft market data and saves model weights.
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.model_selection import train_test_split

from services.pricing_assistant.feature_extractor import FeatureExtractor, BENCHMARK_PATH, CATEGORIES


MODEL_OUTPUT_PATH = Path(__file__).parent.parent / "models" / "pricing_xgb.json"


def generate_training_data(n_samples: int = 1200):
    """Generates calibrated training samples matching Indian handicraft market price distributions."""
    with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
        benchmarks = json.load(f)

    extractor = FeatureExtractor()
    X = []
    y = []

    regions = ["Uttar Pradesh", "Rajasthan", "Odisha", "West Bengal", "Gujarat", "Tamil Nadu", "Assam", "Kashmir"]
    materials = ["pure silk", "natural clay", "carved teak", "solid brass", "sterling silver", "hand-spun khadi", "vegetable tanned leather"]

    categories = benchmarks.get("categories", {})
    np.random.seed(42)

    for i in range(n_samples):
        cat_name = np.random.choice(list(categories.keys()))
        cat_info = categories[cat_name]
        craft_types = list(cat_info.get("craft_types", {}).keys())
        craft_name = np.random.choice(craft_types) if craft_types else None

        base_sug = cat_info["base_suggested_price"]
        if craft_name and craft_name in cat_info.get("craft_types", {}):
            base_sug = cat_info["craft_types"][craft_name]["suggested"]

        # Random variations
        region = np.random.choice(regions)
        material = np.random.choice(materials)
        title = f"Authentic {craft_name or cat_name} {material}"
        description = f"Handcrafted by local artisans in {region} using {material}. Traditional heritage design."

        # Compute price with natural market variance
        noise = np.random.normal(1.0, 0.12)
        price = max(150.0, float(base_sug * noise))

        # Synthetic visual features (32 dim)
        fake_visual = np.random.uniform(0.1, 0.9, 32).astype(np.float32)

        # Feature vector
        t_feats = extractor.extract_text_features(title, description)
        c_feats = extractor.extract_categorical_features(cat_name, craft_name, region)
        vec = np.concatenate([fake_visual, t_feats, c_feats]).astype(np.float32)

        X.append(vec)
        y.append(price)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_pricing_model():
    print("[Pricing Training] Generating calibrated handicraft market samples...")
    X, y = generate_training_data()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"[Pricing Training] Fitting XGBoost Regressor on {len(X_train)} samples...")
    model = xgb.XGBRegressor(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mape = mean_absolute_percentage_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    print(f"[Pricing Training] Evaluation Results:")
    print(f"  - MAPE: {mape * 100:.2f}% (Target: < 18%)")
    print(f"  - R² Score: {r2:.4f}")

    MODEL_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_OUTPUT_PATH))
    print(f"[Pricing Training] Model weights saved to: {MODEL_OUTPUT_PATH}")
    return model


if __name__ == "__main__":
    train_pricing_model()
