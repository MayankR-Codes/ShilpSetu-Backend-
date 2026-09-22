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
    print(f"  SHILPSETU AI TESTER: Testing photo in VS Code")
    print(f"  Target Image: {image_path}")
    print(f"  Artisan Inputs: Raw Material = ₹{raw_material_cost:.2f}, Min Profit Needed = ₹{min_profit:.2f}")
    print("=" * 65)

    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # ── 1. Image Studio: Background Removal & Upscaling ──────
    print("\n[1/3] Running AI Image Studio...")
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

    # ── 2. Vision Copywriting: Description & Why Buy ─────────
    print("\n[2/3] Running Gemini Vision (Description & 'Why Buy')...")
    desc_result = generate_description_from_image(image_bytes)
    print(f"  - Category: {desc_result.get('category')}")
    print(f"  - Craft Type: {desc_result.get('craft_type')}")
    print(f"  - Title (EN): {desc_result.get('title_en')}")
    print(f"  - Title (HI): {desc_result.get('title_hi')}")
    print(f"\n  - 3-4 Line Storytelling Description:")
    print(f"    \"{desc_result.get('description_en')}\"")
    print(f"\n  - Why Buy This Product (Buyer Triggers):")
    for reason in desc_result.get("why_buy", []):
        print(f"    * {reason}")

    # ── 3. Dynamic Pricing Assistant: Cost-Plus & XGBoost ───
    print("\n[3/3] Running XGBoost Pricing Assistant (with Artisan Cost-Plus Inputs)...")
    pricing_model = PricingModel()
    pricing_result = pricing_model.predict_pricing(
        image_input=image_bytes,
        title=desc_result.get("title_en"),
        description=desc_result.get("description_en"),
        category=desc_result.get("category"),
        craft_type=desc_result.get("craft_type"),
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
    print("  ALL 3 AI PIPELINES COMPLETED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    target_img = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGE_PATH
    mat_cost = float(sys.argv[2]) if len(sys.argv) > 2 else 250.0
    profit = float(sys.argv[3]) if len(sys.argv) > 3 else 200.0
    asyncio.run(test_craft_photo(target_img, raw_material_cost=mat_cost, min_profit=profit))
