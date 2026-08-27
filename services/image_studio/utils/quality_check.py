"""
Image Quality Checker using BRISQUE-like heuristics.
Rejects blurry or low-quality images before processing.

Score: 0–100. Higher = better quality.
Threshold: < 30 → reject.

Note: Full BRISQUE requires scikit-image. This implementation uses
Laplacian variance as a fast, dependency-light proxy.
Install scikit-image for production-grade BRISQUE scoring.
"""

import numpy as np
import cv2
from PIL import Image


def check_quality(pil_image: Image.Image) -> float:
    """
    Estimate image quality using Laplacian variance (sharpness proxy).

    Returns:
        float — quality score in range [0, 100].
                 Values below 30 indicate a blurry or unusable image.
    """
    # Convert to grayscale OpenCV image
    rgb = pil_image.convert("RGB")
    cv_image = cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2GRAY)

    # Laplacian variance — high value = sharp, low value = blurry
    laplacian_var = cv2.Laplacian(cv_image, cv2.CV_64F).var()

    # Normalize to 0–100 scale (empirically calibrated)
    # Typical sharp product photos: 200–2000 variance
    score = min(100.0, laplacian_var / 20.0)

    return round(score, 2)
