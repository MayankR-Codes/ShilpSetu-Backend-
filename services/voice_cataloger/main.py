import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List

from services.voice_cataloger.asr import transcribe_audio
from services.voice_cataloger.translate import translate_catalog_text
from services.voice_cataloger.description_gen import generate_catalog_listing
from services.voice_cataloger.seo_injector import inject_seo_tags

voice_router = APIRouter()

class VoiceCatalogResponse(BaseModel):
    detected_language: str
    raw_transcript: str
    title_en: str
    title_hi: str
    description_en: str
    description_hi: str
    features: List[str]
    seo_tags: List[str]
    processing_time_ms: int

@voice_router.post("", response_model=VoiceCatalogResponse)
async def process_voice_note(
    audio: UploadFile = File(..., description="Voice note from artisan (MP3/WAV/M4A)"),
    language_hint: str = Form(None, description="Optional ISO code (e.g., 'hi')"),
):
    """
    Sprint 2.1 & 2.2 - Complete Voice-to-Catalog Pipeline
    """
    if not audio.content_type.startswith("audio/") and audio.content_type not in ["application/octet-stream", "video/mp4"]:
        raise HTTPException(status_code=415, detail="Unsupported format. Upload an audio file.")

    raw_bytes = await audio.read()
    start = time.monotonic()

    # Step 1: Transcribe with Whisper
    asr_result = transcribe_audio(raw_bytes, language_hint)
    
    # Step 2: Translate to English (for LLM) and Hindi (fallback/standard)
    translations = translate_catalog_text(asr_result["text"])
    
    # Step 3: LLM Structured Generation
    catalog_listing = generate_catalog_listing(translations["english"])
    
    # Step 4: SEO Injection
    final_listing = inject_seo_tags(catalog_listing)

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return VoiceCatalogResponse(
        detected_language=asr_result["language"] or "unknown",
        raw_transcript=asr_result["text"],
        title_en=final_listing.get("title_en", ""),
        title_hi=final_listing.get("title_hi", ""),
        description_en=final_listing.get("description_en", ""),
        description_hi=final_listing.get("description_hi", ""),
        features=final_listing.get("features", []),
        seo_tags=final_listing.get("seo_tags", []),
        processing_time_ms=elapsed_ms,
    )

# ---------------------------------------------------------
# Backwards-compatibility aliases (Prefer /api/v1/products)
# ---------------------------------------------------------
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from shared.db.session import get_db
from services.catalog.main import ProductCreate, create_product, get_catalog_feed


@voice_router.post("/save", tags=["Voice Cataloger (Legacy)"])
async def save_product_to_db(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """[Legacy alias] Saves the finalized catalog item to the database. Use POST /api/v1/products instead."""
    created = await create_product(product, db)
    return {"status": "success", "product_id": created.id}


@voice_router.get("/feed", tags=["Voice Cataloger (Legacy)"])
async def legacy_get_catalog_feed(db: AsyncSession = Depends(get_db)):
    """[Legacy alias] Fetches products. Use GET /api/v1/products/feed instead."""
    return await get_catalog_feed(limit=50, offset=0, db=db)


