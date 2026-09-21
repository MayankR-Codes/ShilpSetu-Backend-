"""
Feature Extractor for ShilpSetu Dynamic Pricing Assistant.
Extracts multimodal features (visual, textual, and categorical) into a dense vector
for XGBoost / Gradient Boosting regression.
"""

import io
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
from PIL import Image

BENCHMARK_PATH = Path(__file__).parent / "data" / "market_benchmarks.json"

CATEGORIES = [
    "Textiles",
    "Pottery",
    "Woodcraft",
    "Metalcraft",
    "Jewelry",
    "Paintings",
    "Leather",
]

PREMIUM_KEYWORDS = [
    "silk",
    "zari",
    "pure",
    "handwoven",
    "hand-carved",
    "brass",
    "bronze",
    "silver",
    "gold",
    "antique",
    "intricate",
    "natural dye",
    "organic",
    "teak",
    "sandalwood",
    "filigree",
    "vintage",
]


class FeatureExtractor:
    """Extracts a 64-dimensional feature vector from craft photo, text description, and metadata."""

    def __init__(self):
        self.benchmarks = self._load_benchmarks()

    def _load_benchmarks(self) -> dict:
        if BENCHMARK_PATH.exists():
            with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"categories": {}, "keyword_multipliers": {}}

    def extract_visual_features(self, image_input: Optional[Union[bytes, Image.Image]]) -> np.ndarray:
        """
        Extracts 32 visual feature descriptors:
        - 24 color distribution bins (8 per channel: R, G, B)
        - 4 texture & sharpness metrics (Laplacian variance, edge energy, contrast, saturation)
        - 4 geometry / scale indicators (aspect ratio, normalized area, mean brightness, std brightness)
        """
        if image_input is None:
            return np.zeros(32, dtype=np.float32)

        try:
            if isinstance(image_input, bytes):
                pil_img = Image.open(io.BytesIO(image_input)).convert("RGB")
            elif isinstance(image_input, Image.Image):
                pil_img = image_input.convert("RGB")
            else:
                return np.zeros(32, dtype=np.float32)

            img_np = np.array(pil_img, dtype=np.float32)
            w, h = pil_img.size

            # 1. Color histograms (8 bins per channel = 24 features)
            hist_r, _ = np.histogram(img_np[:, :, 0], bins=8, range=(0, 256), density=True)
            hist_g, _ = np.histogram(img_np[:, :, 1], bins=8, range=(0, 256), density=True)
            hist_b, _ = np.histogram(img_np[:, :, 2], bins=8, range=(0, 256), density=True)
            color_feats = np.concatenate([hist_r, hist_g, hist_b])

            # 2. Texture & sharpness (4 features)
            gray = np.mean(img_np, axis=2)
            gy, gx = np.gradient(gray)
            edge_energy = float(np.mean(gx**2 + gy**2)) / 1000.0
            contrast = float(np.std(gray)) / 128.0

            # Saturation
            max_c = np.max(img_np, axis=2)
            min_c = np.min(img_np, axis=2)
            diff = max_c - min_c
            sat = np.where(max_c > 0, diff / (max_c + 1e-5), 0)
            mean_sat = float(np.mean(sat))
            std_sat = float(np.std(sat))
            texture_feats = np.array([edge_energy, contrast, mean_sat, std_sat], dtype=np.float32)

            # 3. Geometry & lighting (4 features)
            aspect_ratio = float(w) / max(float(h), 1.0)
            norm_area = min(float(w * h) / (1920.0 * 1080.0), 2.0)
            mean_brightness = float(np.mean(gray)) / 255.0
            std_brightness = float(np.std(gray)) / 128.0
            geom_feats = np.array(
                [aspect_ratio, norm_area, mean_brightness, std_brightness],
                dtype=np.float32,
            )

            visual_vec = np.concatenate([color_feats, texture_feats, geom_feats])
            return visual_vec.astype(np.float32)
        except Exception:
            return np.zeros(32, dtype=np.float32)

    def extract_text_features(self, title: Optional[str], description: Optional[str]) -> np.ndarray:
        """
        Extracts 16 textual feature descriptors:
        - Word counts, character counts, average word length
        - Keyword hits for premium materials and craftsmanship techniques
        - Artisan narrative signals (handcrafted, authentic, traditional)
        """
        full_text = f"{title or ''} {description or ''}".lower()
        words = full_text.split()
        num_words = len(words)
        num_chars = len(full_text)
        avg_word_len = num_chars / max(num_words, 1)

        # Keyword density
        kw_hits = [1.0 if kw in full_text else 0.0 for kw in PREMIUM_KEYWORDS[:10]]
        total_kw_hits = sum(kw_hits)

        # Complexity signals
        has_handmade = 1.0 if any(k in full_text for k in ["handmade", "handcrafted", "handloom"]) else 0.0
        has_heritage = 1.0 if any(k in full_text for k in ["traditional", "heritage", "authentic", "antique"]) else 0.0
        has_material = 1.0 if any(k in full_text for k in ["silk", "brass", "copper", "silver", "clay", "wood", "leather"]) else 0.0

        text_feats = np.array(
            [
                min(float(num_words) / 100.0, 3.0),
                min(float(num_chars) / 500.0, 3.0),
                min(float(avg_word_len) / 10.0, 2.0),
                min(float(total_kw_hits) / 5.0, 2.0),
                has_handmade,
                has_heritage,
                has_material,
            ]
            + kw_hits[:9],
            dtype=np.float32,
        )
        return text_feats[:16]

    def extract_categorical_features(
        self,
        category: Optional[str],
        craft_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> np.ndarray:
        """
        Extracts 16 categorical descriptors:
        - 7 One-hot flags for primary craft categories
        - Labor factor & baseline market multiplier
        - Subcategory / region complexity indicators
        """
        feats = np.zeros(16, dtype=np.float32)
        norm_cat = (category or "").strip().title()

        # One-hot category (first 7 slots)
        for i, cat in enumerate(CATEGORIES):
            if norm_cat == cat or norm_cat in cat:
                feats[i] = 1.0
                break

        # Labor factor from benchmark
        cat_data = self.benchmarks.get("categories", {}).get(norm_cat, {})
        craft_types = cat_data.get("craft_types", {})

        labor_factor = 1.0
        if craft_type:
            norm_craft = craft_type.strip().title()
            for ct_name, ct_info in craft_types.items():
                if norm_craft in ct_name or ct_name in norm_craft:
                    labor_factor = ct_info.get("labor_factor", 1.2)
                    feats[7] = 1.0  # recognized craft type match
                    break

        feats[8] = float(labor_factor)
        feats[9] = float(cat_data.get("avg_market_price", 1500)) / 5000.0
        feats[10] = float(cat_data.get("competitor_count", 100)) / 200.0

        # Region indicator
        if region:
            feats[11] = 1.0

        return feats

    def extract_features(
        self,
        image_input: Optional[Union[bytes, Image.Image]] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        craft_type: Optional[str] = None,
        region: Optional[str] = None,
    ) -> np.ndarray:
        """Concatenates visual (32) + text (16) + categorical (16) into a 64-dim vector."""
        v_feats = self.extract_visual_features(image_input)
        t_feats = self.extract_text_features(title, description)
        c_feats = self.extract_categorical_features(category, craft_type, region)

        vector = np.concatenate([v_feats, t_feats, c_feats])
        return vector.astype(np.float32)
