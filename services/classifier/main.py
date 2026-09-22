"""
ShilpSetu — Smart Product Classifier Service (Pillar 4).
FastAPI Router for zero-touch visual craft classification,
GI-tag recognition, and raw material composition breakdown.
"""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel

from api_gateway.logger import get_logger
from services.classifier.engine import CraftClassifier
from services.classifier.taxonomy import (
    get_all_categories,
    get_subcategories,
    get_gi_registry,
    find_gi_match,
)

logger = get_logger(__name__)
classifier_router = APIRouter()
classifier_engine = CraftClassifier()


# ── Schemas ────────────────────────────────────────────────────────

class MaterialBreakdownItem(BaseModel):
    material: str
    percentage: float


class AlternateCategoryItem(BaseModel):
    category: str
    confidence: float


class CraftClassificationResponse(BaseModel):
    primary_category: str
    sub_category: str
    craft_heritage: str
    region_of_origin: str
    gi_tagged: bool
    materials_breakdown: List[MaterialBreakdownItem]
    craft_technique: str
    confidence: float
    alternate_categories: List[AlternateCategoryItem] = []


class TaxonomyResponse(BaseModel):
    categories: List[str]
    sub_categories: Dict[str, List[str]]
    total_categories: int
    total_gi_crafts: int


class GIDetectionResponse(BaseModel):
    is_gi_tagged: bool
    craft_name: str
    gi_details: Optional[Dict[str, Any]] = None


# ── Endpoints ──────────────────────────────────────────────────────

@classifier_router.post("/classify", response_model=CraftClassificationResponse)
async def classify_craft_image(
    image: UploadFile = File(..., description="Craft photograph (JPEG/PNG/WebP)"),
    artisan_materials: Optional[str] = Form(
        None,
        description="Optional JSON array of artisan-declared materials with percentages, e.g. '[{\"material\":\"Clay\",\"percentage\":80}]'",
    ),
    artisan_hint: Optional[str] = Form(
        None,
        description="Optional artisan context or regional hint (e.g. 'terracotta vase from Bishnupur')",
    ),
):
    """
    Visual Craft Classifier:
    Inspects an uploaded craft photo directly and classifies:
    - Primary Category & Sub-Category
    - Regional Heritage Craft & State of Origin
    - Geographical Indication (GI Tag) Status
    - Materials Composition Breakdown (Artisan-declared or AI-inferred percentages)
    - Handcrafted Technique
    """
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image format. Please upload JPEG, PNG, or WebP.",
        )

    # Parse optional artisan materials JSON
    parsed_materials = None
    if artisan_materials:
        try:
            parsed_materials = json.loads(artisan_materials)
            if not isinstance(parsed_materials, list):
                parsed_materials = None
        except Exception:
            logger.warning(f"Could not parse artisan_materials JSON: {artisan_materials}")

    image_bytes = await image.read()

    result = classifier_engine.classify_craft(
        image_input=image_bytes,
        artisan_materials=parsed_materials,
        artisan_hint=artisan_hint,
    )

    return result


@classifier_router.get("/taxonomy", response_model=TaxonomyResponse)
async def get_taxonomy_hierarchy():
    """
    Returns the complete ShilpSetu Indian Handicraft Taxonomy
    for Flutter dropdown menus, search filters, and artisan forms.
    """
    cats = get_all_categories()
    sub_cats = {cat: get_subcategories(cat) for cat in cats}
    gi_reg = get_gi_registry()

    return TaxonomyResponse(
        categories=cats,
        sub_categories=sub_cats,
        total_categories=len(cats),
        total_gi_crafts=len(gi_reg),
    )


@classifier_router.post("/detect-gi", response_model=GIDetectionResponse)
async def detect_gi_heritage(
    craft_name: str = Form(..., description="Name of the craft (e.g. 'Bankura Terracotta', 'Banarasi Silk')"),
):
    """
    Checks if a given craft name is an officially recognized Indian
    Geographical Indication (GI Tag) craft.
    """
    gi_info = find_gi_match(craft_name)
    if gi_info:
        return GIDetectionResponse(
            is_gi_tagged=True,
            craft_name=gi_info["craft_name"],
            gi_details=gi_info,
        )
    return GIDetectionResponse(
        is_gi_tagged=False,
        craft_name=craft_name,
        gi_details=None,
    )
