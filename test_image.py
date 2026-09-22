"""
ShilpSetu — Quick Photo Tester for VS Code
Run this script to test any craft image through all 3 AI models:
1. AI Image Studio (Background Removal & 4x Upscaling)
2. Vision Copywriter (3-4 line description & Why Buy points)
3. Dynamic Pricing Assistant (XGBoost Price Prediction)

Usage in VS Code Terminal:
    python test_image.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure environment & paths are loaded
load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.image_studio.pipeline import ImagePipeline
from services.pricing_assistant.model import PricingModel
from services.voice_cataloger.description_gen import generate_description_from_image
from services.classifier.engine import CraftClassifier

# -------------------------------------------------------------
# DEFAULT IMAGE PATH (can also be passed as: python test_image.py <image_path>)
# -------------------------------------------------------------
DEFAULT_IMAGE_PATH = r"C:\Users\KIIT\.gemini\antigravity\brain\427f0d68-e958-482c-83de-b890832a2c1e\.user_uploaded\media_1789996819687.jpg"


async def test_craft_photo(image_path: str, raw_material_cost: float = 250.0, min_profit: float = 200.0):
    if not os.path.exists(image_path):
        print(f"[Error] Image not found at: {image_path}")
        print("Please provide a valid image path. Example: python test_image.py path/to/craft.jpg")
        return

    print("=" * 65)
    print(f"  SHILPSETU AI TESTER: Testing photo in VS Code (Pillars 1 to 4)")
    print(f"  Target Image: {image_path}")
    print(f"  Artisan Inputs: Raw Material = Rs. {raw_material_cost:.2f}, Min Profit = Rs. {min_profit:.2f}")
    print("=" * 65)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # ── 1. Image Studio: Background Removal & Upscaling ──────
    print("\n[1/4] Running AI Image Studio (Pillar 1)...")
    pipeline = ImagePipeline()
    img_result = await pipeline.run(
        image_bytes=image_bytes,
        original_filename=os.path.basename(image_path),
        output_format="png",
    )
    print(f"  - Enhanced Image URL: {img_result['url']}")
    print(f"  - Original Size: {img_result['original_size']} px")
    print(f"  - Enhanced 4x Size: {img_result['enhanced_size']} px")
    print(f"  - Sharpness Quality Score: {img_result['quality_score']}/100")

    # ── 2. Smart Product Classifier (Pillar 4) ───────────────
    print("\n[2/4] Running Smart Product Classifier (Pillar 4)...")
    classifier = CraftClassifier()
    classification = classifier.classify_craft(
        image_input=image_bytes,
        artisan_materials=[
            {"material": "Natural River Pebble", "percentage": 55.0},
            {"material": "Wood Slice Backdrop", "percentage": 35.0},
            {"material": "Clay Applique & Colors", "percentage": 10.0},
        ],
        artisan_hint="Hand-painted pebble cat tabletop artifact",
    )
    print(f"  - Primary Category: {classification.get('primary_category')}")
    print(f"  - Sub-Category: {classification.get('sub_category')}")
    print(f"  - Regional Craft Heritage: {classification.get('craft_heritage')}")
    print(f"  - Origin / State: {classification.get('region_of_origin')}")
    print(f"  - GI Tag Recognized: {'Yes (Official Indian GI)' if classification.get('gi_tagged') else 'No (Folk/Artisan Craft)'}")
    print(f"  - Craft Technique: {classification.get('craft_technique')}")
    print(f"  - Raw Materials Composition (Percentages):")
    for mat in classification.get("materials_breakdown", []):
        print(f"    * {mat['material']}: {mat['percentage']}%")
    print(f"  - Classifier Confidence: {int(classification.get('confidence', 0.9) * 100)}%")

    # ── 3. Vision Copywriting: Description & Why Buy ─────────
    print("\n[3/4] Running Gemini Vision Copywriter (Pillar 2)...")
    desc_result = generate_description_from_image(image_bytes)
    print(f"  - Title (EN): {desc_result.get('title_en')}")
    print(f"  - Title (HI): {desc_result.get('title_hi')}")
    print(f"\n  - 3-4 Line Storytelling Description:")
    print(f"    \"{desc_result.get('description_en')}\"")
    print(f"\n  - Why Buy This Product (Buyer Triggers):")
    for reason in desc_result.get("why_buy", []):
        print(f"    * {reason}")

    # ── 4. Dynamic Pricing Assistant: Cost-Plus & XGBoost ───
    print("\n[4/4] Running XGBoost Pricing Assistant (Pillar 3)...")
    pricing_model = PricingModel()
    pricing_result = pricing_model.predict_pricing(
        image_input=image_bytes,
        title=desc_result.get("title_en"),
        description=desc_result.get("description_en"),
        category=classification.get("primary_category"),
        craft_type=classification.get("craft_heritage"),
        raw_material_cost=raw_material_cost,
        min_profit=min_profit,
    )
    pr = pricing_result["price_range"]
    cost_info = pricing_result.get("cost_analysis", {})

    print(f"  - Artisan Raw Materials Cost: Rs. {cost_info.get('raw_material_cost', raw_material_cost):.2f}")
    print(f"  - Artisan Min Profit Desired: Rs. {cost_info.get('min_profit_desired', min_profit):.2f}")
    print(f"  - Cost Floor (Cost + Profit): Rs. {cost_info.get('cost_floor', raw_material_cost + min_profit):.2f}")
    print(f"  -------------------------------------------------------------")
    print(f"  - Suggested Selling Price: Rs. {pr['suggested']:.2f}")
    print(f"  - Recommended Range: Rs. {pr['min']:.2f} - Rs. {pr['max']:.2f} (Floor Protected >= Rs. {cost_info.get('cost_floor'):.2f})")
    print(f"  - Projected Profit: Rs. {cost_info.get('projected_profit', 0):.2f} ({cost_info.get('profit_margin_pct', 0):.1f}% margin)")
    if cost_info.get("surplus_above_min_profit", 0) > 0:
        print(f"  - Extra Profit Surplus: +Rs. {cost_info.get('surplus_above_min_profit'):.2f} ABOVE artisan target!")
    print(f"  - Pricing Strategy: {pricing_result['market_insights']['pricing_strategy']}")
    print(f"  - Confidence: {int(pricing_result['confidence'] * 100)}%")
    print(f"  - Craft Tier: {pricing_result['market_insights']['craft_tier']}")
    print(f"  - Artisan Guidance Note: \"{cost_info.get('artisan_note')}\"")

    print("\n" + "=" * 65)
    print("  ALL 4 AI PILLARS COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    target_img = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE_PATH
    mat_cost = float(sys.argv[2]) if len(sys.argv) > 2 else 250.0
    profit = float(sys.argv[3]) if len(sys.argv) > 3 else 200.0
    asyncio.run(test_craft_photo(target_img, raw_material_cost=mat_cost, min_profit=profit))
