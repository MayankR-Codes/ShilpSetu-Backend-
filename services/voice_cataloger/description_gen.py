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

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODELS = [m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.7-flash,gemini-3.6-flash").split(",") if m.strip()]


def _call_gemini_with_fallback(contents):
    """
    Attempts generation with the primary model, automatically cascading to
    secondary fallback models if a 429 Rate Limit or API error occurs.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set in the environment.",
        )

    model_chain = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_err = None

    for model_name in model_chain:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(contents)
            if response and response.text:
                parsed = _parse_json_response(response.text)
                parsed["generated_by_model"] = model_name
                logger.info(f"Successfully generated product listing using Gemini model: '{model_name}'")
                return parsed
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str or "Quota" in err_str or "ResourceExhausted" in err_str:
                logger.warning(f"Model '{model_name}' hit rate limit (429). Cascading to next model...")
                continue
            else:
                logger.warning(f"Model '{model_name}' failed with error: {e}. Cascading...")
                continue

    raise last_err or Exception("All Gemini candidate models failed.")


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
        return _call_gemini_with_fallback(prompt)
    except Exception as e:
        logger.warning(f"Gemini voice listing generation failed ({e}). Using intelligent fallback copywriter.")
        return _fallback_catalog_listing(text_context=english_transcript)



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
        return _call_gemini_with_fallback([prompt, pil_image])
    except Exception as e:
        logger.warning(f"Gemini vision description generation failed ({e}). Using intelligent fallback copywriter.")
        return _fallback_catalog_listing(text_context=craft_hint, craft_hint=craft_hint)


def generate_fused_catalog_listing(image_bytes: bytes, english_transcript: str) -> dict:
    """
    Multimodal Voice + Vision Fusion Generator:
    Fuses the artisan's spoken story and personal context with visual inspection
    of the actual craft photo via Gemini Vision.
    """
    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        logger.warning(f"Could not open image for multimodal fusion ({e}). Falling back to transcript.")
        return generate_catalog_listing(english_transcript)

    prompt = f"""
    You are an expert e-commerce copywriter and handicraft curator for ShilpSetu, an Indian artisan marketplace.
    You are given BOTH a photograph of an authentic Indian handcrafted product AND the artisan's personal spoken voice note.

    Artisan's Spoken Voice Note (Translated to English):
    "{english_transcript}"

    INSTRUCTIONS:
    1. Synergize both inputs: Combine what you visually observe in the photo (colors, textures, motifs, craftsmanship details) with the artisan's spoken story (materials used, days taken, traditional technique).
    2. "category": Primary category ("Textiles", "Pottery", "Woodcraft", "Metalcraft", "Jewelry", "Paintings", "Leather", or "Home Decor").
    3. "craft_type": Specific regional craft name (e.g. "Bankura Terracotta", "Banarasi Silk", "Channapatna Woodcraft", "Jaipur Blue Pottery", "Moradabad Brass", etc.).
    4. "description_en" & "description_hi": Exactly 3 to 4 captivating lines of storytelling description that honors the artisan's personal work while detailing the visual beauty of the piece.
    5. "why_buy": 3 to 4 persuasive bullet points explaining why a buyer will purchase this product upon seeing it.
    6. "features": 4 specific visible craftsmanship features.
    7. "seo_tags": 8-10 trending e-commerce tags.
    8. Return ONLY a valid JSON object without markdown fences or commentary.

    Required JSON Schema:
    {{
        "category": "Pottery",
        "craft_type": "Terracotta",
        "title_en": "Catchy Product Title (max 80 chars)",
        "title_hi": "उत्पाद का आकर्षक शीर्षक",
        "description_en": "Compelling 3-4 line e-commerce storytelling description...",
        "description_hi": "3-4 पंक्तियों का सुंदर विवरण...",
        "why_buy": [
            "Unique handmade detail reflecting the artisan's dedicated craft",
            "100% eco-friendly and authentic natural materials",
            "Statement heritage decor that enriches any living space"
        ],
        "features": [
            "Handmade using traditional techniques",
            "Authentic artisanal finish",
            "Premium durable construction"
        ],
        "seo_tags": ["handmade", "artisan", "authentic craft", "vocal for local"]
    }}
    """

    try:
        return _call_gemini_with_fallback([prompt, pil_image])
    except Exception as e:
        logger.warning(f"Multimodal Gemini vision generation failed ({e}). Using intelligent fallback copywriter.")
        return _fallback_catalog_listing(text_context=english_transcript, craft_hint=english_transcript)


def _fallback_catalog_listing(text_context: Optional[str] = None, craft_hint: Optional[str] = None) -> dict:
    """
    Intelligent offline heuristic copywriter fallback.
    Used when Gemini API quota (429) or network is unavailable, ensuring
    the artisan app NEVER crashes and ALWAYS returns complete, high-quality listings.
    """
    combined = f"{text_context or ''} {craft_hint or ''}".lower()

    if any(k in combined for k in ["clay", "terracotta", "pottery", "diya", "ghada", "pot", "vase", "mitti"]):
        category = "Pottery"
        craft_type = "Terracotta Craft"
        title_en = "Handcrafted Earthen Terracotta Decor"
        title_hi = "हस्तनिर्मित पारंपरिक टेराकोटा कला"
        desc_en = (
            "Meticulously hand-molded from pure natural riverbed clay, this authentic piece embodies centuries-old Indian pottery heritage. "
            "Kiln-fired to achieve its signature earthy rust tone, it showcases intricate hand-carved textures and traditional artisanal motifs. "
            "A timeless sustainable accent, it infuses living rooms and cultural spaces with organic warmth and rustic charm."
        )
        desc_hi = (
            "प्राकृतिक नदी की मिट्टी से हस्तनिर्मित, यह रचना सदियों पुरानी भारतीय कुम्हार विरासत को दर्शाती है। "
            "पारंपरिक भट्टी में पकी यह कलाकृति आपके घर को पर्यावरण के अनुकूल देहाती सुंदरता और सांस्कृतिक आकर्षण से भर देती है।"
        )
        features = [
            "Handcrafted from 100% natural baked clay",
            "Traditional kiln-fired matte terracotta finish",
            "Eco-friendly, chemical-free and sustainable",
            "Authentic artisanal design by Indian rural potters",
        ]
        why_buy = [
            "Pure handmade craftsmanship that factory molds cannot replicate",
            "Brings soothing organic warmth to modern minimalist interiors",
            "100% biodegradable and non-toxic natural material",
        ]
        seo_tags = ["terracotta", "handmade pottery", "clay art", "vocal for local", "eco friendly"]

    elif any(k in combined for k in ["silk", "saree", "handloom", "weave", "cotton", "textile", "zari"]):
        category = "Textiles"
        craft_type = "Handloom Weaving"
        title_en = "Authentic Handloom Woven Textile Craft"
        title_hi = "पारंपरिक हथकरघा रेशम वस्त्र"
        desc_en = (
            "Woven on traditional Indian pit looms by master artisans, this handloom creation celebrates generations of textile heritage. "
            "Featuring delicate artisanal weaves and natural organic fibers, every inch reflects the patient rhythm of the weaver's shuttle. "
            "An elegant tribute to sustainable slow fashion, it radiates regal dignity and timeless cultural grace."
        )
        desc_hi = (
            "पारंपरिक हथकरघे पर कुशल बुनकरों द्वारा तैयार, यह रचना समृद्ध भारतीय वस्त्र विरासत का प्रतीक है। "
            "प्राकृतिक धागों और जटिल बुनाई से सुसज्जित, यह परिधान पारंपरिक गरिमा और कालातीत सुंदरता बिखेरता है।"
        )
        features = [
            "Woven on traditional Indian handlooms",
            "Premium natural fibers with authentic texture",
            "Intricate border and pallu weave detailing",
            "Breathable, durable, and slow-fashion certified",
        ]
        why_buy = [
            "Authentic handloom authenticity preserving weaver livelihoods",
            "Luxurious natural drape and breathable comfort",
            "Heirloom-grade craftsmanship built to last generations",
        ]
        seo_tags = ["handloom", "pure silk", "traditional weave", "artisan textile", "sustainable fashion"]

    elif any(k in combined for k in ["wood", "carved", "teak", "sheesham", "wooden", "furniture"]):
        category = "Woodcraft"
        craft_type = "Hand-Carved Woodcraft"
        title_en = "Hand-Carved Solid Wood Artisan Decor"
        title_hi = "हस्तनिर्मित काष्ठ नक्काशी कला"
        desc_en = (
            "Carved from sustainably harvested solid timber, this wooden masterpiece displays the intricate chisel work of master woodcraft artisans. "
            "Each curve, groove, and relief pattern is shaped entirely by hand, accentuating the natural grain and deep luster of the wood. "
            "A sturdy, enduring statement artifact, it brings organic richness and architectural grandeur to any setting."
        )
        desc_hi = (
            "प्राकृतिक लकड़ी पर कुशल नक्काशी द्वारा तैयार, यह कलाकृति पारंपरिक भारतीय काष्ठ कला का उत्कृष्ट उदाहरण है। "
            "हाथ से तराशे गए सूक्ष्म पैटर्न और लकड़ी की प्राकृतिक बनावट आपके घर को एक शाही और देहाती रूप प्रदान करते हैं।"
        )
        features = [
            "Hand-carved from seasoned natural hardwood",
            "Smooth hand-rubbed organic wax/polish finish",
            "Intricate floral or geometric relief patterns",
            "Durable heirloom construction for lifelong longevity",
        ]
        why_buy = [
            "One-of-a-kind hand-chiseled texture with no machine stamping",
            "Sustainably harvested wood with natural grain warmth",
            "Adds classic regal heritage to study tables, consoles, or living rooms",
        ]
        seo_tags = ["woodcraft", "hand carved", "solid wood", "artisan decor", "handmade india"]

    elif any(k in combined for k in ["brass", "metal", "bronze", "copper", "bell", "diya"]):
        category = "Metalcraft"
        craft_type = "Traditional Metalcraft"
        title_en = "Artisanal Hand-Cast Brass & Metal Artifact"
        title_hi = "हस्तनिर्मित पीतल धातु कलाकृति"
        desc_en = (
            "Cast using ancient metal-smithing traditions, this authentic brass artifact exemplifies timeless Indian metallurgical skill. "
            "Hand-finished with fine engraving and a radiant warm metallic patina, it combines structural weight with ornate folk motifs. "
            "An auspicious centerpiece for ceremonies and interiors alike, it exudes enduring prosperity, grace, and cultural depth."
        )
        desc_hi = (
            "प्राचीन धातु ढलाई परंपरा से निर्मित, यह पीतल की कलाकृति पारंपरिक भारतीय शिल्प कौशल का अनुपम प्रमाण है। "
            "हाथ की बारीक नक्काशी और चमकदार धातु की चमक आपके पूजा स्थल या बैठक को शुभ और भव्य बनाती है।"
        )
        features = [
            "Hand-cast from solid virgin brass/metal alloy",
            "Hand-engraved traditional auspicious motifs",
            "Corrosion-resistant protective artisanal patina",
            "Substantial weight and authentic heritage feel",
        ]
        why_buy = [
            "Solid metal casting designed to endure for centuries",
            "Auspicious positive energy and cultural reverence",
            "Directly supports generational family brass clusters",
        ]
        seo_tags = ["brass craft", "metal art", "handmade brass", "traditional decor", "moradabad brass"]

    else:
        category = "Home Decor"
        craft_type = "Artisanal Heritage Craft"
        title_en = "Handcrafted Authentic Indian Artisan Creation"
        title_hi = "प्रामाणिक हस्तनिर्मित भारतीय पारंपरिक कला"
        desc_en = (
            "Meticulously hand-crafted by skilled rural Indian artisans, this authentic creation embodies generations of indigenous craft tradition. "
            "Formed using eco-friendly natural materials and time-honored artisanal techniques, each piece possesses a unique personal touch. "
            "An enchanting celebration of Indian folk heritage, it adds authentic rustic warmth and handmade pride to any living space."
        )
        desc_hi = (
            "कुशल ग्रामीण भारतीय कारीगरों द्वारा हस्तनिर्मित, यह प्रामाणिक रचना पीढ़ियों पुरानी पारंपरिक विरासत और शिल्प कौशल को दर्शाती है। "
            "पर्यावरण के अनुकूल प्राकृतिक सामग्रियों और सदियों पुरानी तकनीकों से तैयार, प्रत्येक उत्पाद अपने आप में अद्वितीय और खास है। "
            "इसकी देहाती बनावट और सांस्कृतिक आकर्षण आपके घर को एक प्रामाणिक पारंपरिक स्पर्श प्रदान करता है।"
        )
        features = [
            "100% handmade by rural Indian artisans",
            "Eco-friendly natural materials and traditional methods",
            "Distinctive artisanal finish with unique handcrafted nuances",
            "Ideal for aesthetic home decor and meaningful gifting",
        ]
        why_buy = [
            "Pure human craftsmanship with zero industrial factory mass-production",
            "Direct fair-trade empowerment for indigenous artisan communities",
            "Brings unique soul, rustic warmth, and storytelling to your home",
        ]
        seo_tags = ["handmade", "artisan", "vocal for local", "indian handicraft", "sustainable decor"]

    logger.info("Generated product listing using Offline Intelligent Heuristic Engine (Pillars 2 & 4 Fallback)")
    return {
        "category": category,
        "craft_type": craft_type,
        "title_en": title_en,
        "title_hi": title_hi,
        "description_en": desc_en,
        "description_hi": desc_hi,
        "why_buy": why_buy,
        "features": features,
        "seo_tags": seo_tags,
        "generated_by_model": "offline-heuristic-engine",
    }


