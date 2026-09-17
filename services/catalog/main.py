"""
ShilpSetu — Product Catalog Service
Integrates AI Image Studio, Voice Cataloger, and database persistence into a unified workflow.
"""

import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api_gateway.logger import get_logger
from shared.db.session import get_db
from shared.db.models import Product
from services.image_studio.pipeline import ImagePipeline
from services.voice_cataloger.asr import transcribe_audio
from services.voice_cataloger.translate import translate_catalog_text
from services.voice_cataloger.description_gen import generate_catalog_listing
from services.voice_cataloger.seo_injector import inject_seo_tags

logger = get_logger(__name__)
catalog_router = APIRouter()
image_pipeline = ImagePipeline()


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
    features: Optional[List[str]] = []
    tags: Optional[List[str]] = []


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
    features: Optional[List[str]] = []
    tags: Optional[List[str]] = []
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
    features: List[str]
    tags: List[str]
    enhanced_image_url: str
    quality_score: float
    detected_language: str
    raw_transcript: str
    processing_time_ms: int
    is_saved: bool


# ── Catalog Endpoints ──────────────────────────────────────────────

@catalog_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
@catalog_router.post("/save", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """
    Save a finalized product listing to the PostgreSQL catalog.
    Supports both POST /api/v1/products and POST /api/v1/products/save (backwards compatible).
    """
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
        enhanced_image_url=product.enhanced_image_url,
        price_suggested=product.price_suggested,
        price_min=product.price_min,
        price_max=product.price_max,
        features=product.features or [],
        tags=product.tags or [],
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    logger.info(f"Created product with ID {new_product.id} for artisan {new_product.artisan_id}")
    return new_product


@catalog_router.get("", response_model=List[ProductResponse])
@catalog_router.get("/feed", response_model=List[ProductResponse])
async def get_catalog_feed(
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
    return products


@catalog_router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(product_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetch single product details by product ID.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
    return product


# ── Unified Multi-Modal AI Creation ────────────────────────────────

@catalog_router.post("/create-ai", response_model=UnifiedAIProductResponse)
async def create_product_with_ai(
    image: UploadFile = File(..., description="Raw photo of artisan craft (JPEG/PNG/WebP)"),
    audio: UploadFile = File(..., description="Voice description of craft (MP3/WAV/M4A)"),
    artisan_id: str = Form(..., description="Unique ID of the artisan"),
    language_hint: Optional[str] = Form(None, description="Optional ISO code (e.g. 'hi')"),
    auto_save: bool = Form(True, description="Whether to automatically commit the listing to the database"),
    db: AsyncSession = Depends(get_db),
):
    """
    Unified Multi-Modal Pipeline:
    Artisan uploads craft photo + audio note in ONE call.

    1. Enhances image (background removal, upscaling, color correction).
    2. Transcribes voice note (Whisper), translates to English/Hindi, and structures with Gemini AI.
    3. Injects SEO tags.
    4. Optionally saves the complete listing to the PostgreSQL catalog immediately.
    """
    # 1. Validation
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=415, detail="Unsupported image format. Upload JPEG, PNG, or WebP.")

    if not audio.content_type.startswith("audio/") and audio.content_type not in [
        "application/octet-stream",
        "video/mp4",
    ]:
        raise HTTPException(status_code=415, detail="Unsupported audio format. Upload an audio file.")

    start_time = time.monotonic()

    # 2. Image Studio Enhancement
    image_bytes = await image.read()
    image_result = await image_pipeline.run(
        image_bytes=image_bytes,
        original_filename=image.filename,
        output_format="webp",
    )

    # 3. Voice Cataloger Processing
    audio_bytes = await audio.read()
    asr_result = transcribe_audio(audio_bytes, language_hint)
    translations = translate_catalog_text(asr_result["text"])
    catalog_listing = generate_catalog_listing(translations["english"])
    final_listing = inject_seo_tags(catalog_listing)

    # 4. Extract fields
    title_en = final_listing.get("title_en", "")
    title_hi = final_listing.get("title_hi", "")
    description_en = final_listing.get("description_en", "")
    description_hi = final_listing.get("description_hi", "")
    features = final_listing.get("features", [])
    seo_tags = final_listing.get("seo_tags", [])

    product_id = None
    if auto_save:
        new_product = Product(
            artisan_id=artisan_id,
            title_en=title_en,
            title_hi=title_hi,
            description_en=description_en,
            description_hi=description_hi,
            enhanced_image_url=image_result["url"],
            features=features,
            tags=seo_tags,
        )
        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        product_id = new_product.id
        logger.info(f"AI unified creation auto-saved product ID {product_id}")

    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    return UnifiedAIProductResponse(
        product_id=product_id,
        artisan_id=artisan_id,
        title_en=title_en,
        title_hi=title_hi,
        description_en=description_en,
        description_hi=description_hi,
        features=features,
        tags=seo_tags,
        enhanced_image_url=image_result["url"],
        quality_score=image_result["quality_score"],
        detected_language=asr_result.get("language") or "unknown",
        raw_transcript=asr_result.get("text", ""),
        processing_time_ms=elapsed_ms,
        is_saved=auto_save,
    )
