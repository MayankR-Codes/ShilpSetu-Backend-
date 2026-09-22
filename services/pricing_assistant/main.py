"""
ShilpSetu — Dynamic Pricing Assistant Service
FastAPI Router for AI-driven handicraft price estimation.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api_gateway.logger import get_logger
from shared.db.session import get_db
from shared.db.models import Product
from services.pricing_assistant.model import PricingModel

logger = get_logger(__name__)
pricing_router = APIRouter()
pricing_engine = PricingModel()


# ── Schemas ────────────────────────────────────────────────────────

class PriceRange(BaseModel):
    min: float
    suggested: float
    max: float


class CostAnalysis(BaseModel):
    raw_material_cost: float
    min_profit_desired: float
    cost_floor: float
    suggested_price: float
    projected_profit: float
    profit_margin_pct: float
    surplus_above_min_profit: float
    artisan_note: str


class PricingSuggestRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    craft_type: Optional[str] = None
    region: Optional[str] = None
    image_url: Optional[str] = None
    product_id: Optional[int] = None
    raw_material_cost: Optional[float] = None
    min_profit: Optional[float] = None


class PricingResponse(BaseModel):
    price_range: PriceRange
    currency: str = "INR"
    confidence: float
    market_insights: Dict[str, Any]
    cost_analysis: Optional[CostAnalysis] = None


class ApplyPricingRequest(BaseModel):
    raw_material_cost: Optional[float] = None
    min_profit: Optional[float] = None


class ApplyPricingResponse(BaseModel):
    status: str
    product_id: int
    price_suggested: float
    price_min: float
    price_max: float
    confidence: float
    cost_analysis: Optional[CostAnalysis] = None


# ── Endpoints ──────────────────────────────────────────────────────

@pricing_router.post("/suggest", response_model=PricingResponse)
async def suggest_price(request: PricingSuggestRequest, db: AsyncSession = Depends(get_db)):
    """
    Predict optimal competitive pricing for an artisan craft based on
    visual features, materials, craftsmanship complexity, regional market indices,
    and optional artisan cost-plus inputs (raw material cost + desired minimum profit).
    """
    # If product_id is provided and fields are missing, populate from DB
    title = request.title
    description = request.description
    category = request.category
    craft_type = request.craft_type
    raw_material_cost = request.raw_material_cost
    min_profit = request.min_profit

    if request.product_id:
        result = await db.execute(select(Product).where(Product.id == request.product_id))
        product = result.scalar_one_or_none()
        if product:
            title = title or product.title_en or product.title_hi
            description = description or product.description_en or product.description_hi
            category = category or product.category
            craft_type = craft_type or product.craft_type
            raw_material_cost = raw_material_cost if raw_material_cost is not None else product.raw_material_cost
            min_profit = min_profit if min_profit is not None else product.min_profit

    prediction = pricing_engine.predict_pricing(
        image_input=None,
        title=title,
        description=description,
        category=category,
        craft_type=craft_type,
        region=request.region,
        raw_material_cost=raw_material_cost,
        min_profit=min_profit,
    )

    return prediction


@pricing_router.post("/apply/{product_id}", response_model=ApplyPricingResponse)
async def apply_price_to_product(
    product_id: int,
    request: Optional[ApplyPricingRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates dynamic pricing for an existing product in the catalog and
    automatically saves price_suggested, price_min, and price_max into the database.
    Optionally accepts raw_material_cost and min_profit to enforce cost-plus floor.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found in catalog",
        )

    title = product.title_en or product.title_hi
    description = product.description_en or product.description_hi
    category = product.category
    craft_type = product.craft_type

    raw_material_cost = None
    min_profit = None
    if request:
        raw_material_cost = request.raw_material_cost if request.raw_material_cost is not None else product.raw_material_cost
        min_profit = request.min_profit if request.min_profit is not None else product.min_profit
    else:
        raw_material_cost = product.raw_material_cost
        min_profit = product.min_profit

    prediction = pricing_engine.predict_pricing(
        image_input=None,
        title=title,
        description=description,
        category=category,
        craft_type=craft_type,
        raw_material_cost=raw_material_cost,
        min_profit=min_profit,
    )

    price_range = prediction["price_range"]
    product.price_suggested = price_range["suggested"]
    product.price_min = price_range["min"]
    product.price_max = price_range["max"]
    if raw_material_cost is not None:
        product.raw_material_cost = raw_material_cost
    if min_profit is not None:
        product.min_profit = min_profit

    await db.commit()
    await db.refresh(product)

    logger.info(
        f"Applied dynamic pricing to product {product_id}: ₹{product.price_suggested} (range: ₹{product.price_min} - ₹{product.price_max})"
    )

    return ApplyPricingResponse(
        status="success",
        product_id=product.id,
        price_suggested=product.price_suggested,
        price_min=product.price_min,
        price_max=product.price_max,
        confidence=prediction["confidence"],
        cost_analysis=prediction.get("cost_analysis"),
    )
