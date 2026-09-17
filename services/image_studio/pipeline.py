"""
Image Studio Pipeline Orchestrator
Chains: quality_check → remove_bg → upscale → color_correct → save
"""

import io
from PIL import Image
from fastapi import HTTPException

from services.image_studio.utils.quality_check import check_quality
from services.image_studio.steps.remove_bg import remove_background
from services.image_studio.steps.upscale import upscale_image
from services.image_studio.steps.color_correct import color_correct
from shared.storage.client import save_file


class ImagePipeline:
    async def run(
        self,
        image_bytes: bytes,
        original_filename: str,
        output_format: str = "webp",
    ) -> dict:
        """
        Execute the full 5-step image enhancement pipeline.

        Returns:
            dict with keys: url, quality_score, original_size, enhanced_size
        """
        # ── Step 1: Quality check ─────────────────────────────────
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        original_size = list(pil_image.size)  # [width, height]

        quality_score = check_quality(pil_image)
        if quality_score < 0.0:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "image_quality_too_low",
                    "quality_score": round(quality_score, 2),
                    "message": "Please upload a clearer image",
                },
            )

        # ── Step 2: Background removal ────────────────────────────
        no_bg_image = remove_background(pil_image)

        # ── Step 3: Super-resolution upscaling ───────────────────
        upscaled_image = upscale_image(no_bg_image)

        # ── Step 4: Color correction ──────────────────────────────
        final_image = color_correct(upscaled_image)
        enhanced_size = list(final_image.size)

        # ── Step 5: Save to storage ───────────────────────────────
        output_bytes = io.BytesIO()
        fmt = "PNG" if output_format == "png" else "WEBP"
        final_image.save(output_bytes, format=fmt, quality=90)
        output_bytes.seek(0)

        ext = ".png" if output_format == "png" else ".webp"
        url = await save_file(
            file_bytes=output_bytes.read(),
            filename=f"enhanced{ext}",
            folder="products",
        )

        return {
            "url": url,
            "quality_score": round(quality_score, 2),
            "original_size": original_size,
            "enhanced_size": enhanced_size,
        }
