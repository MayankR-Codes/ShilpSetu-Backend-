"""
AI Image Studio — FastAPI Router
Endpoint: POST /api/v1/image/enhance

NOTE: Auth is handled by the Flutter app / their backend.
      This endpoint is open — no JWT check on our side.
"""

import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

from services.image_studio.pipeline import ImagePipeline

image_router = APIRouter()
pipeline = ImagePipeline()


class EnhanceResponse(BaseModel):
    enhanced_url: str                      # Full absolute URL (e.g. https://.../uploads/...)
    enhanced_image_url: Optional[str] = None # Flutter alias
    image_url: Optional[str] = None        # Flutter alias
    image: Optional[str] = None            # Flutter alias
    url: Optional[str] = None              # Flutter alias
    quality_score: float                   # 0–100 sharpness score of original image
    processing_time_ms: int                # How long the pipeline took
    original_size_px: list[int]            # [width, height] of uploaded photo
    enhanced_size_px: list[int]            # [width, height] of enhanced output


def get_public_base_url(request: Request) -> str:
    """Constructs a clean HTTPS URL reachable from mobile apps behind ngrok or proxies."""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "http"
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or str(request.base_url.netloc)
    if "ngrok" in host.lower() or proto == "https":
        proto = "https"
    return f"{proto}://{host}".rstrip("/")


@image_router.post("/enhance", response_model=EnhanceResponse)
async def enhance_image(
    request: Request,
    file: UploadFile = File(..., description="Raw artisan product photo — JPEG/PNG/WebP"),
    output_format: str = Form(default="webp", description="Output format: 'webp' or 'png'"),
):
    """
    Takes a raw artisan product photo and returns a website-ready image:

    Step 1 → Quality check     : Reject blurry/unusable images (score < 30)
    Step 2 → Background removal: Remove background using rembg (U²-Net AI)
    Step 3 → Super-resolution  : Upscale 4× using Real-ESRGAN (CPU mode by default)
    Step 4 → Color correction  : Fix contrast (CLAHE) + white balance
    Step 5 → Save & return URL : Image saved, URL returned — ready to list on website
    """
    if file.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=415,
            detail="Unsupported format. Upload a JPEG, PNG, or WebP image."
        )

    raw_bytes = await file.read()
    start = time.monotonic()

    result = await pipeline.run(
        image_bytes=raw_bytes,
        original_filename=file.filename,
        output_format=output_format,
    )

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Convert relative path to full HTTPS absolute URL reachable by mobile devices
    base_url = get_public_base_url(request)
    rel_url = result["url"]
    full_url = f"{base_url}{rel_url}" if (rel_url and rel_url.startswith("/")) else rel_url

    return EnhanceResponse(
        enhanced_url=full_url,
        enhanced_image_url=full_url,
        image_url=full_url,
        image=full_url,
        url=full_url,
        quality_score=result["quality_score"],
        processing_time_ms=elapsed_ms,
        original_size_px=result["original_size"],
        enhanced_size_px=result["enhanced_size"],
    )

