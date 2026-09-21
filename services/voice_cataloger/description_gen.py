"""
Gemini AI Copywriting Engine for ShilpSetu.
Generates structured e-commerce product listings, evocative 3–4 line descriptions,
and 'Why Buy This Product' value propositions from Voice notes and Craft Images.
"""

import io
import json
import os
from typing import Optional
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
from fastapi import HTTPException
from api_gateway.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def _get_model():
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set in the environment.",
        )
    return genai.GenerativeModel(GEMINI_MODEL_NAME)


def _parse_json_response(text: str) -> dict:
    """Cleans up markdown code fences and parses JSON safely."""
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except Exception as e:
        logger.error(f"Failed to parse LLM JSON output: {e}\nRaw Text:\n{text}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse structured product listing from AI response.",
        )


def generate_catalog_listing(english_transcript: str) -> dict:
    """
    Converts transcribed voice note into a high-converting e-commerce listing with
    concise 3-4 line storytelling description and 'Why Buy' purchase triggers.
    """
    model = _get_model()

    prompt = f"""
    You are an expert e-commerce copywriter for an Indian artisan platform called ShilpSetu.
    Based on the following artisan's voice note, create a high-converting, authentic product listing.
    
    CRITICAL REQUIREMENTS:
    1. "description_en" and "description_hi" MUST be exactly 3 to 4 captivating lines of storytelling description that highlights the authentic materials, traditional hand-crafting technique, and emotional/aesthetic warmth of the item.
    2. "why_buy" MUST be an array of 3 to 4 persuasive bullet points explaining WHY a buyer will purchase this product upon seeing it (e.g. handmade human craftsmanship vs factory molds, eco-friendly/organic materials, auspicious or cultural symbolism, aesthetic home decor statement).
    3. Return ONLY a valid JSON object. Do not wrap it in markdown backticks or commentary.

    Required JSON Schema:
    {{
        "title_en": "Catchy Product Title (max 80 chars)",
        "title_hi": "उत्पाद का आकर्षक शीर्षक",
        "description_en": "Compelling 3-4 line e-commerce description...",
        "description_hi": "3-4 पंक्तियों का सुंदर विवरण...",
        "why_buy": [
            "Visually striking artisanal detail showing authentic hand-craftsmanship",
            "100% eco-friendly and non-toxic natural materials",
            "Auspicious cultural heritage decor that adds rustic warmth"
        ],
        "features": [
            "Handmade by rural Indian artisans",
            "Authentic traditional technique",
            "Durable kiln-baked finish"
        ],
        "seo_tags": ["handmade", "artisan", "vocal for local"]
    }}

    Artisan's description (translated to English):
    "{english_transcript}"
    """

    try:
        response = model.generate_content(prompt)
        return _parse_json_response(response.text)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini voice listing generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate product description from AI: {str(e)}",
        )


def generate_description_from_image(image_bytes: bytes, craft_hint: Optional[str] = None) -> dict:
    """
    Vision-to-Listing Generator:
    Inspects an uploaded craft photo directly using Gemini Vision and generates:
    - Craft Category & Craft Type
    - Title in English & Hindi
    - Evocative 3-4 line description
    - 'Why Buy This Product' bullet points
    - Key specifications and SEO tags
    """
    model = _get_model()

    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {e}")

    hint_text = f"Artisan hint / craft context: {craft_hint}" if craft_hint else ""

    prompt = f"""
    You are a master curator of Indian handicrafts for the ShilpSetu artisan marketplace.
    Inspect the attached photograph of this handcrafted Indian product.

    Analyze its materials (clay, brass, wood, silk, stone, leather, etc.), hand-molding or carving textures, folk motifs, and artistic style.
    {hint_text}

    Generate a complete, high-converting product listing adhering strictly to:
    1. "category": Must be one of: "Textiles", "Pottery", "Woodcraft", "Metalcraft", "Jewelry", "Paintings", "Leather", or "Home Decor".
    2. "craft_type": Specific regional craft name (e.g. "Terracotta", "Banarasi", "Moradabad Brass", "Dhokra", "Madhubani", "Saharanpur Wood", etc.).
    3. "description_en" & "description_hi": An evocative, premium 3–4 line storytelling description detailing the raw natural material, handcrafting technique, and rustic/heritage charm.
    4. "why_buy": 3 to 4 persuasive bullet points answering why a customer will instantly want to purchase this upon seeing it.
    5. "features": 4 specific visible craftsmanship features.
    6. "seo_tags": 8-10 trending tags.
    7. Return ONLY a valid JSON object.

    Required JSON Schema:
    {{
        "category": "Pottery",
        "craft_type": "Terracotta",
        "title_en": "Handcrafted Terracotta Horse Figurine",
        "title_hi": "हस्तनिर्मित टेराकोटा मिट्टी का घोड़ा",
        "description_en": "Meticulously hand-molded from pure natural riverbed clay, this authentic Terracotta Horse embodies centuries-old Indian folk craftsmanship. Adorned with intricately rolled clay braids, ceremonial neckbands, and traditional bell motifs, each piece is kiln-baked to achieve its signature earthy rust-amber tone. A timeless statement piece, it infuses living rooms and cultural spaces with rustic warmth and heritage charm.",
        "description_hi": "प्राकृतिक नदी की मिट्टी से हस्तनिर्मित, यह टेराकोटा घोड़ा भारतीय लोक कला का प्रतीक है। जटिल मिट्टी की चोटियों और पारंपरिक घंटियों से सजाया गया, यह घर को देहाती और सांस्कृतिक आकर्षण से भर देता है।",
        "why_buy": [
            "Unique handmade detail that factory molds cannot replicate",
            "Brings calming organic warmth to modern minimalist interiors",
            "Auspicious heritage symbol of vitality and guardian energy",
            "100% sustainable and chemical-free natural clay"
        ],
        "features": [
            "Handcrafted from pure natural baked clay",
            "Intricate neck braid and bell tassel relief work",
            "Kiln-fired matte terracotta finish",
            "Ideal for study tables, consoles, or prayer rooms"
        ],
        "seo_tags": ["terracotta", "bankura horse", "handmade pottery", "indian artisan", "vocal for local"]
    }}
    """

    try:
        response = model.generate_content([prompt, pil_image])
        return _parse_json_response(response.text)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Gemini vision description generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate craft description from image: {str(e)}",
        )
