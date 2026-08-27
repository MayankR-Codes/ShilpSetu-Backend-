"""
Color Correction Step
Applies CLAHE contrast enhancement + automatic white balance
to improve product photo color accuracy and brightness.
"""

import numpy as np
import cv2
from PIL import Image


def color_correct(pil_image: Image.Image) -> Image.Image:
    """
    Apply CLAHE contrast enhancement and white balance to the image.

    Args:
        pil_image: Input PIL image (RGBA).

    Returns:
        Color-corrected PIL image (RGBA).
    """
    # Preserve alpha channel
    rgba = pil_image.convert("RGBA")
    r, g, b, alpha = rgba.split()
    rgb = Image.merge("RGB", (r, g, b))

    # Convert to LAB color space for CLAHE on L channel
    cv_image = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(cv_image)

    # CLAHE on L channel (contrast-limited adaptive histogram equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_ch = clahe.apply(l_ch)

    # Merge back and convert to RGB
    enhanced_lab = cv2.merge([l_ch, a_ch, b_ch])
    enhanced_rgb = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)

    # Simple gray-world white balance
    enhanced_rgb = _white_balance(enhanced_rgb)

    # Reattach original alpha channel
    result = Image.fromarray(enhanced_rgb).convert("RGBA")
    result.putalpha(alpha)
    return result


def _white_balance(img_np: np.ndarray) -> np.ndarray:
    """
    Gray-world white balance assumption:
    scale each channel so its mean equals the overall mean.
    """
    result = img_np.astype(np.float32)
    mean = result.mean()
    for i in range(3):
        ch_mean = result[:, :, i].mean()
        if ch_mean > 0:
            result[:, :, i] *= mean / ch_mean
    return np.clip(result, 0, 255).astype(np.uint8)
