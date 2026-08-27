"""
Background Removal Step
Uses rembg (U²-Net) to cleanly remove the background from product photos.
"""

from PIL import Image
from rembg import remove as rembg_remove


def remove_background(pil_image: Image.Image) -> Image.Image:
    """
    Remove the background from a PIL image using rembg (U²-Net).

    Args:
        pil_image: Input PIL image (RGBA or RGB).

    Returns:
        PIL image with background removed (RGBA with transparent background).
    """
    # rembg works with bytes — convert PIL → bytes → PIL
    import io
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, format="PNG")
    buf.seek(0)

    output_bytes = rembg_remove(buf.read())
    result = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    return result
