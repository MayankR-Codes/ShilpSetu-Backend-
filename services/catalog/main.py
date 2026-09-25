"""
ShilpSetu — Product Catalog Service
Integrates AI Image Studio, Voice Cataloger, and database persistence into a unified workflow.
"""

import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, status, Request
from pydantic import BaseModel, ConfigDict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api_gateway.logger import get_logger
from shared.db.session import get_db
from shared.db.models import Product
from services.image_studio.pipeline import ImagePipeline
from services.voice_cataloger.asr import transcribe_audio
from services.voice_cataloger.translate import translate_catalog_text
from services.voice_cataloger.description_gen import (
    generate_catalog_listing,
    generate_description_from_image,
    generate_fused_catalog_listing,
)
from services.voice_cataloger.seo_injector import inject_seo_tags
from services.pricing_assistant.model import PricingModel
from services.classifier.engine import CraftClassifier

logger = get_logger(__name__)
catalog_router = APIRouter()
image_pipeline = ImagePipeline()
pricing_engine = PricingModel()
classifier_engine = CraftClassifier()


# ── Schemas ────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    artisan_id: str
    title_en: Optional[str] = None
    title_hi: Optional[str] = None
    description_en: Optional[str] = None
    description_hi: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    craft_type: Optional[str] = None
    original_image_url: Optional[str] = None
    enhanced_image_url: Optional[str] = None
    price_suggested: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    raw_material_cost: Optional[float] = None
    min_profit: Optional[float] = None
    features: Optional[List[str]] = []
    why_buy: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    materials_breakdown: Optional[List[dict]] = []


class ProductResponse(BaseModel):
    id: int
    artisan_id: str
    title_en: Optional[str] = None
    title_hi: Optional[str] = None
    description_en: Optional[str] = None
    description_hi: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    craft_type: Optional[str] = None
    original_image_url: Optional[str] = None
    enhanced_image_url: Optional[str] = None
    price_suggested: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    raw_material_cost: Optional[float] = None
    min_profit: Optional[float] = None
    features: Optional[List[str]] = []
    why_buy: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    materials_breakdown: Optional[List[dict]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UnifiedAIProductResponse(BaseModel):
    product_id: Optional[int] = None
    artisan_id: str
    title_en: str
    title_hi: str
    description_en: str
    description_hi: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    craft_type: Optional[str] = None
    craft_heritage: Optional[str] = None
    gi_tagged: Optional[bool] = False
    features: List[str]
    why_buy: List[str] = []
    tags: List[str] = []
    materials_breakdown: Optional[List[dict]] = []
    enhanced_image_url: Optional[str] = None
    enhanced_url: Optional[str] = None
    image_url: Optional[str] = None
    image: Optional[str] = None
    url: Optional[str] = None
    quality_score: Optional[float] = 0.0
    detected_language: str
    raw_transcript: str
    processing_time_ms: int
    is_saved: bool
    price_suggested: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    raw_material_cost: Optional[float] = None
    min_profit: Optional[float] = None
    cost_analysis: Optional[dict] = None
    generated_by_model: Optional[str] = None


def get_public_base_url(request: Request) -> str:
    """Constructs a clean HTTPS URL reachable from mobile apps behind ngrok or proxies."""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "http"
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or str(request.base_url.netloc)
    if "ngrok" in host.lower() or proto == "https":
        proto = "https"
    return f"{proto}://{host}".rstrip("/")


# ── Catalog Endpoints ──────────────────────────────────────────────

@catalog_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@catalog_router.post("/save", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(request: Request, product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """
    Save a finalized product listing to the PostgreSQL catalog.
    Supports both POST /api/v1/products and POST /api/v1/products/save (backwards compatible).
    """
    enhanced_img = product.enhanced_image_url
    if enhanced_img and ("data/user/" in enhanced_img or "craft_" in enhanced_img or enhanced_img.startswith("/data") or enhanced_img.startswith("file://")):
        import glob
        files = sorted(glob.glob("uploads/products/*.webp"), key=os.path.getmtime, reverse=True)
        if files:
            latest_rel = "/" + files[0].replace("\\", "/")
            base_url = get_public_base_url(request)
            enhanced_img = f"{base_url}{latest_rel}"
            logger.info(f"Auto-healed local mobile path '{product.enhanced_image_url}' -> '{enhanced_img}'")

    new_product = Product(
        artisan_id=product.artisan_id,
        title_en=product.title_en,
        title_hi=product.title_hi,
        description_en=product.description_en,
        description_hi=product.description_hi,
        category=product.category,
        sub_category=product.sub_category,
        craft_type=product.craft_type,
        original_image_url=product.original_image_url,
        enhanced_image_url=enhanced_img,
        price_suggested=product.price_suggested,
        price_min=product.price_min,
        price_max=product.price_max,
        raw_material_cost=product.raw_material_cost,
        min_profit=product.min_profit,
        features=product.features or [],
        why_buy=product.why_buy or [],
        tags=product.tags or [],
        materials_breakdown=product.materials_breakdown or [],
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    logger.info(f"Created product with ID {new_product.id} for artisan {new_product.artisan_id}")
    return new_product


@catalog_router.get("", response_model=List[ProductResponse])
@catalog_router.get("/feed", response_model=List[ProductResponse])
async def get_catalog_feed(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Number of items to fetch"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch all products for the buyer/artisan feed, sorted with latest first.
    Supports pagination via `limit` and `offset`.
    """
    query = (
        select(Product)
        .order_by(Product.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    products = result.scalars().all()
    base_url = get_public_base_url(request)
    for p in products:
        if p.enhanced_image_url and ("data/user/" in p.enhanced_image_url or "craft_" in p.enhanced_image_url):
            import glob
            files = sorted(glob.glob("uploads/products/*.webp"), key=os.path.getmtime, reverse=True)
            if files:
                rel = "/" + files[0].replace("\\", "/")
                p.enhanced_image_url = f"{base_url}{rel}"
        elif p.enhanced_image_url and p.enhanced_image_url.startswith("/"):
            p.enhanced_image_url = f"{base_url}{p.enhanced_image_url}"
    return products


@catalog_router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch single product details by product ID.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
    base_url = get_public_base_url(request)
    if product.enhanced_image_url and ("data/user/" in product.enhanced_image_url or "craft_" in product.enhanced_image_url):
        import glob
        files = sorted(glob.glob("uploads/products/*.webp"), key=os.path.getmtime, reverse=True)
        if files:
            rel = "/" + files[0].replace("\\", "/")
            product.enhanced_image_url = f"{base_url}{rel}"
    elif product.enhanced_image_url and product.enhanced_image_url.startswith("/"):
        product.enhanced_image_url = f"{base_url}{product.enhanced_image_url}"
    return product


# ── Unified Multi-Modal AI Creation ────────────────────────────────

@catalog_router.post("/create-ai", response_model=UnifiedAIProductResponse)
async def create_product_with_ai(
    request: Request,
    image: Optional[UploadFile] = File(None, description="Raw photo of artisan craft (JPEG/PNG/WebP)"),
    audio: Optional[UploadFile] = File(None, description="Voice description of craft (MP3/WAV/M4A)"),
    artisan_id: str = Form("artisan_001", description="Unique ID of the artisan"),
    category: Optional[str] = Form(None, description="Optional craft category (e.g. 'Textiles', 'Pottery')"),
    language_hint: Optional[str] = Form(None, description="Optional ISO code (e.g. 'hi')"),
    raw_material_cost: Optional[float] = Form(None, description="Cost of raw materials invested by artisan in INR"),
    min_profit: Optional[float] = Form(None, description="Minimum desired profit needed by artisan in INR"),
    materials_breakdown: Optional[str] = Form(
        None, description="Optional JSON array of materials and percentages, e.g. '[{\"material\":\"Clay\",\"percentage\":85}]'"
    ),
    auto_save: bool = Form(True, description="Whether to automatically commit the listing to the database"),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified Multi-Modal Pipeline (Flexible Tri-Mode):
    Artisans can provide Photo Only, Voice Only, or Both.

    - Mode 1: Multimodal Fusion (Photo + Voice) - Fuses visual craftsmanship with the artisan's personal spoken story.
    - Mode 2: Photo-Only - Autonomous vision cataloging for quiet artisans.
    - Mode 3: Voice-Only - Fast vocal catalog draft when photo is not yet available.
    """
    start_time = time.monotonic()

    # Pre-flight validation: must provide at least one input
    has_image = image is not None and bool(image.filename)
    has_audio = audio is not None and bool(audio.filename)

    if not has_image and not has_audio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least a product photo ('image'), a voice note ('audio'), or both.",
        )

    if has_image:
        if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
            raise HTTPException(status_code=415, detail="Unsupported image format. Upload JPEG, PNG, or WebP.")

    if has_audio:
        if not audio.content_type.startswith("audio/") and audio.content_type not in [
            "application/octet-stream",
            "video/mp4",
        ]:
            raise HTTPException(status_code=415, detail="Unsupported audio format. Upload an audio file.")

    # Parse optional artisan materials JSON
    parsed_materials = None
    if materials_breakdown:
        try:
            parsed_materials = json.loads(materials_breakdown)
            if not isinstance(parsed_materials, list):
                parsed_materials = None
        except Exception:
            logger.warning(f"Could not parse materials_breakdown JSON in create-ai: {materials_breakdown}")

    # 1. Image Studio Enhancement (if photo provided)
    image_bytes = None
    image_url = None
    quality_score = 0.0
    if has_image:
        image_bytes = await image.read()
        image_result = await image_pipeline.run(
            image_bytes=image_bytes,
            original_filename=image.filename,
            output_format="webp",
        )
        base_url = get_public_base_url(request)
        rel_url = image_result["url"]
        image_url = f"{base_url}{rel_url}" if (rel_url and rel_url.startswith("/")) else rel_url
        quality_score = image_result["quality_score"]


    # 2. Voice Cataloger Processing (if voice note provided)
    detected_lang = "none"
    raw_transcript = ""
    english_transcript = ""
    if has_audio:
        audio_bytes = await audio.read()
        asr_result = transcribe_audio(audio_bytes, language_hint)
        detected_lang = asr_result.get("language") or "unknown"
        raw_transcript = asr_result.get("text", "")
        translations = translate_catalog_text(raw_transcript)
        english_transcript = translations.get("english", "")

    # 3. AI Copywriting Generation (Flexible Tri-Mode)
    if has_image and has_audio:
        logger.info("Executing Mode 1: Multimodal Voice + Vision Fusion")
        catalog_listing = generate_fused_catalog_listing(image_bytes, english_transcript)
    elif has_image:
        logger.info("Executing Mode 2: Photo-Only Visual Cataloging")
        detected_lang = "visual"
        raw_transcript = "Visual AI cataloging (no voice note provided)"
        catalog_listing = generate_description_from_image(image_bytes)
    else:
        logger.info("Executing Mode 3: Voice-Only Cataloging")
        catalog_listing = generate_catalog_listing(english_transcript)

    final_listing = inject_seo_tags(catalog_listing)

    # 4. Extract fields
    title_en = final_listing.get("title_en", "")
    title_hi = final_listing.get("title_hi", "")
    description_en = final_listing.get("description_en", "")
    description_hi = final_listing.get("description_hi", "")
    features = final_listing.get("features", [])
    why_buy = final_listing.get("why_buy", [])
    seo_tags = final_listing.get("seo_tags", [])

    # 5. Smart Product Classifier (Pillar 4)
    classification = classifier_engine.classify_craft(
        image_input=image_bytes,
        artisan_materials=parsed_materials,
        artisan_hint=f"{title_en} {description_en}",
    )
    final_category = category or classification.get("primary_category")
    sub_category = classification.get("sub_category")
    craft_type = classification.get("craft_heritage")
    craft_heritage = classification.get("craft_heritage")
    gi_tagged = classification.get("gi_tagged", False)
    final_materials = classification.get("materials_breakdown", [])

    # 6. Dynamic Pricing Assistant (Pillar 3)
    pricing_pred = pricing_engine.predict_pricing(
        image_input=image_bytes,
        title=title_en,
        description=description_en,
        category=final_category,
        craft_type=craft_type,
        raw_material_cost=raw_material_cost,
        min_profit=min_profit,
    )
    price_range = pricing_pred["price_range"]
    price_min = price_range["min"]
    price_suggested = price_range["suggested"]
    price_max = price_range["max"]
    cost_analysis = pricing_pred.get("cost_analysis")

    # 7. Database Persistence & FAISS Vector Indexing
    product_id = None
    if auto_save:
        new_product = Product(
            artisan_id=artisan_id,
            title_en=title_en,
            title_hi=title_hi,
            description_en=description_en,
            description_hi=description_hi,
            category=final_category,
            sub_category=sub_category,
            craft_type=craft_type,
            enhanced_image_url=image_url,
            price_suggested=price_suggested,
            price_min=price_min,
            price_max=price_max,
            raw_material_cost=raw_material_cost,
            min_profit=min_profit,
            features=features,
            why_buy=why_buy,
            tags=seo_tags,
            materials_breakdown=final_materials,
        )
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        product_id = new_product.id
        logger.info(f"AI unified creation auto-saved product ID {product_id} with suggested price Rs. {price_suggested}")

        # Semantic Vector Search Indexing (Pillar 5)
        try:
            from services.search.embedder import embedder, build_product_text
            from services.search.index import search_index
            product_text = build_product_text(new_product)
            product_vec = embedder.embed(product_text)
            search_index.add(new_product.id, product_vec, auto_save=True)
            logger.info(f"Pillar 5: Auto-indexed product ID {product_id} into FAISS")
        except Exception as se:
            logger.warning(f"Pillar 5 auto-index warning for product {product_id}: {se}")

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    return UnifiedAIProductResponse(
        product_id=product_id,
        artisan_id=artisan_id,
        title_en=title_en,
        title_hi=title_hi,
        description_en=description_en,
        description_hi=description_hi,
        category=final_category,
        sub_category=sub_category,
        craft_type=craft_type,
        craft_heritage=craft_heritage,
        gi_tagged=gi_tagged,
        features=features,
        why_buy=why_buy,
        tags=seo_tags,
        materials_breakdown=final_materials,
        enhanced_image_url=image_url,
        enhanced_url=image_url,
        image_url=image_url,
        image=image_url,
        url=image_url,
        quality_score=quality_score,
        detected_language=detected_lang,
        raw_transcript=raw_transcript,
        processing_time_ms=elapsed_ms,
        is_saved=auto_save,
        price_suggested=price_suggested,
        price_min=price_min,
        price_max=price_max,
        raw_material_cost=raw_material_cost,
        min_profit=min_profit,
        cost_analysis=cost_analysis,
        generated_by_model=final_listing.get("generated_by_model"),
    )
