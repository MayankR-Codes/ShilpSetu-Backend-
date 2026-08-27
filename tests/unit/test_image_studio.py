"""
Unit tests for the AI Image Studio pipeline.
Run: pytest tests/unit/test_image_studio.py -v
"""

import io
import pytest
from PIL import Image, ImageDraw

from services.image_studio.utils.quality_check import check_quality
from services.image_studio.steps.color_correct import color_correct


def _make_sharp_image(size=(400, 400)) -> Image.Image:
    """Create a sharp test image with clear edges (high Laplacian variance)."""
    img = Image.new("RGBA", size, "white")
    draw = ImageDraw.Draw(img)
    for i in range(0, size[0], 20):
        draw.line([(i, 0), (i, size[1])], fill="black", width=2)
    return img


def _make_blurry_image(size=(400, 400)) -> Image.Image:
    """Create a uniform image (very low Laplacian variance = blurry)."""
    return Image.new("RGBA", size, (128, 128, 128, 255))


# ── Quality Check Tests ────────────────────────────────────────────

def test_quality_sharp_image_passes_threshold():
    img = _make_sharp_image()
    score = check_quality(img)
    assert score >= 30, f"Sharp image should score ≥30, got {score}"


def test_quality_blurry_image_below_threshold():
    img = _make_blurry_image()
    score = check_quality(img)
    assert score < 30, f"Blurry image should score <30, got {score}"


def test_quality_score_range():
    img = _make_sharp_image()
    score = check_quality(img)
    assert 0 <= score <= 100, f"Score should be in [0, 100], got {score}"


# ── Color Correction Tests ─────────────────────────────────────────

def test_color_correct_preserves_alpha():
    img = _make_sharp_image()
    result = color_correct(img)
    assert result.mode == "RGBA", "Output should be RGBA"
    assert result.size == img.size, "Output size should match input"


def test_color_correct_output_is_image():
    img = _make_sharp_image()
    result = color_correct(img)
    assert isinstance(result, Image.Image)


def test_color_correct_does_not_crash_on_pure_white():
    img = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
    result = color_correct(img)
    assert result is not None
