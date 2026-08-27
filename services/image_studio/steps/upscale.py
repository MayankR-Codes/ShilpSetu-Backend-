"""
Super-Resolution Upscaling Step
Uses Real-ESRGAN to 4× upscale product images.

✅ CPU MODE: No GPU required. Works on any standard laptop/desktop CPU.
   Processing time on CPU: ~20–60 seconds per image (depending on size).
   Processing time on GPU: ~2–5 seconds per image.

Model weights: services/image_studio/models/RealESRGAN_x4plus.pth
Download:
  curl -L https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth \
       -o services/image_studio/models/RealESRGAN_x4plus.pth

If weights are not downloaded yet → falls back to Lanczos 4× upscaling automatically.
"""

import os
import numpy as np
from PIL import Image

ESRGAN_MODEL_PATH = os.getenv(
    "ESRGAN_MODEL_PATH",
    "services/image_studio/models/RealESRGAN_x4plus.pth",
)
# GPU is completely optional — set USE_GPU=true only if you have a CUDA GPU
USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"


def upscale_image(pil_image: Image.Image) -> Image.Image:
    """
    Upscale image 4× using Real-ESRGAN on CPU (or GPU if available).
    Falls back to Lanczos if model weights aren't downloaded yet.

    Args:
        pil_image: Input PIL image (RGBA).

    Returns:
        Upscaled PIL image (RGBA), 4× the original dimensions.
    """
    if os.path.exists(ESRGAN_MODEL_PATH):
        return _upscale_esrgan(pil_image)
    else:
        print("[upscale] Model weights not found — using Lanczos fallback.")
        print(f"[upscale] To enable AI upscaling, download weights to: {ESRGAN_MODEL_PATH}")
        return _upscale_lanczos(pil_image)


def _upscale_esrgan(pil_image: Image.Image) -> Image.Image:
    """
    Real-ESRGAN 4× upscaling.
    Runs on CPU by default — tile=512 prevents memory crash on large images.
    """
    try:
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        device = "cuda" if USE_GPU else "cpu"

        model = RRDBNet(
            num_in_ch=3, num_out_ch=3,
            num_feat=64, num_block=23, num_grow_ch=32, scale=4
        )
        upsampler = RealESRGANer(
            scale=4,
            model_path=ESRGAN_MODEL_PATH,
            model=model,
            tile=512,        # ← process in tiles so CPU doesn't run out of RAM
            tile_pad=10,
            pre_pad=0,
            half=False,      # half=True only for GPU (float16)
            device=device,
        )

        rgb = pil_image.convert("RGB")
        img_np = np.array(rgb)[:, :, ::-1]   # PIL RGB → OpenCV BGR
        output, _ = upsampler.enhance(img_np, outscale=4)
        result_rgb = output[:, :, ::-1]        # BGR → RGB
        return Image.fromarray(result_rgb).convert("RGBA")

    except Exception as e:
        print(f"[upscale] Real-ESRGAN failed ({e}), falling back to Lanczos.")
        return _upscale_lanczos(pil_image)


def _upscale_lanczos(pil_image: Image.Image) -> Image.Image:
    """High-quality Lanczos 4× fallback — no model needed, instant on CPU."""
    w, h = pil_image.size
    return pil_image.resize((w * 4, h * 4), Image.LANCZOS)

