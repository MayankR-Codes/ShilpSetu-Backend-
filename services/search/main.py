"""
ShilpSetu — Pillar 5: Search API Endpoints
Provides buyer semantic search, similar item recommendations, and index management.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api_gateway.logger import get_logger
from shared.db.session import get_db
from shared.db.models import Product
from services.search.embedder import embedder, build_product_text
from services.search.index import search_index

logger = get_logger(__name__)
search_router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────

class SearchQueryRequest(BaseModel):
    query: str = Field(..., description="Buyer query in English or Hindi, e.g. 'rustic clay vase'")
    top_k: int = Field(10, ge=1, le=50, description="Max number of results to return")
    category: Optional[str] = Field(None, description="Optional category filter")
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")


class SearchResultItem(BaseModel):
    product_id: int
    title_en: Optional[str] = None
    title_hi: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    craft_type: Optional[str] = None
    price_suggested: Optional[float] = None
    original_image_url: Optional[str] = None
    enhanced_image_url: Optional[str] = None
    score: float = Field(..., description="Cosine similarity score between 0.0 and 1.0")


class SearchQueryResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]


class IndexProductResponse(BaseModel):
    success: bool
    product_id: int
    indexed_count: int
    message: str


class RebuildIndexResponse(BaseModel):
    status: str
    total_indexed: int
    message: str


# ── Endpoints ──────────────────────────────────────────────────────

@search_router.post("/query", response_model=SearchQueryResponse, summary="Buyer Semantic Vector Search")
async def semantic_search(
    req: SearchQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Performs semantic vector search across artisan products using cosine similarity.
    Supports natural language buyer queries in Hindi, English, or mixed ("Hinglish").
    """
    logger.info(f"Semantic search query: '{req.query}' (top_k={req.top_k})")

    if search_index.count() == 0:
        return SearchQueryResponse(query=req.query, total=0, results=[])

    # 1. Embed query
    query_vector = embedder.embed(req.query)

    # 2. Search FAISS index (fetch more if filters apply)
    search_k = req.top_k * 3 if (req.category or req.min_price or req.max_price) else req.top_k
    hits = search_index.search(query_vector, top_k=search_k)

    if not hits:
        return SearchQueryResponse(query=req.query, total=0, results=[])

    hit_ids = [pid for pid, _ in hits]
    score_map = {pid: score for pid, score in hits}

    # 3. Fetch products from DB
    result = await db.execute(select(Product).where(Product.id.in_(hit_ids)))
    products = {p.id: p for p in result.scalars().all()}

    # 4. Filter and rank results
    ranked_items: List[SearchResultItem] = []
    for pid in hit_ids:
        p = products.get(pid)
        if not p:
            continue

        # Optional filters
        if req.category and p.category and req.category.lower() not in p.category.lower():
            continue
        if req.min_price is not None and (p.price_suggested or 0.0) < req.min_price:
            continue
        if req.max_price is not None and (p.price_suggested or 0.0) > req.max_price:
            continue

        raw_score = score_map.get(pid, 0.0)
        # Normalize score to 0..1 for buyer presentation
        norm_score = max(0.0, min(1.0, (raw_score + 1.0) / 2.0)) if raw_score < 0 else min(1.0, raw_score)

        ranked_items.append(
            SearchResultItem(
                product_id=p.id,
                title_en=p.title_en,
                title_hi=p.title_hi,
                category=p.category,
                sub_category=p.sub_category,
                craft_type=p.craft_type,
                price_suggested=p.price_suggested,
                original_image_url=p.original_image_url,
                enhanced_image_url=p.enhanced_image_url,
                score=round(float(norm_score), 4),
            )
        )

        if len(ranked_items) >= req.top_k:
            break

    return SearchQueryResponse(
        query=req.query,
        total=len(ranked_items),
        results=ranked_items,
    )


@search_router.get("/similar/{product_id}", response_model=SearchQueryResponse, summary="Find Similar Products")
async def get_similar_products(
    product_id: int,
    top_k: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Finds products similar to a given product ID based on multimodal vector similarity.
    Excludes the target product itself from the recommendation list.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    # Generate embedding from target product
    prod_text = build_product_text(product)
    vec = embedder.embed(prod_text)

    # Search for top_k + 1 to account for self-match
    hits = search_index.search(vec, top_k=top_k + 1)
    filtered_hits = [(pid, score) for pid, score in hits if pid != product_id][:top_k]

    if not filtered_hits:
        return SearchQueryResponse(query=f"Product {product_id}", total=0, results=[])

    hit_ids = [pid for pid, _ in filtered_hits]
    score_map = {pid: score for pid, score in filtered_hits}

    res = await db.execute(select(Product).where(Product.id.in_(hit_ids)))
    products = {p.id: p for p in res.scalars().all()}

    results = []
    for pid in hit_ids:
        p = products.get(pid)
        if not p:
            continue
        raw_score = score_map.get(pid, 0.0)
        norm_score = max(0.0, min(1.0, (raw_score + 1.0) / 2.0)) if raw_score < 0 else min(1.0, raw_score)

        results.append(
            SearchResultItem(
                product_id=p.id,
                title_en=p.title_en,
                title_hi=p.title_hi,
                category=p.category,
                sub_category=p.sub_category,
                craft_type=p.craft_type,
                price_suggested=p.price_suggested,
                original_image_url=p.original_image_url,
                enhanced_image_url=p.enhanced_image_url,
                score=round(float(norm_score), 4),
            )
        )

    return SearchQueryResponse(
        query=f"Similar to product #{product_id} ({product.title_en or product.category or 'Craft'})",
        total=len(results),
        results=results,
    )


@search_router.post("/index/{product_id}", response_model=IndexProductResponse, summary="Index or Re-Index a Product")
async def index_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Generates and stores the semantic vector embedding for a single product.
    """
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    text = build_product_text(product)
    vector = embedder.embed(text)
    search_index.add(product_id, vector, auto_save=True)

    return IndexProductResponse(
        success=True,
        product_id=product_id,
        indexed_count=search_index.count(),
        message=f"Product #{product_id} indexed successfully in FAISS",
    )


@search_router.post("/rebuild", response_model=RebuildIndexResponse, summary="Rebuild Full FAISS Index from DB")
async def rebuild_index(
    db: AsyncSession = Depends(get_db),
):
    """
    Rebuilds the entire FAISS vector index from all products stored in the database.
    Useful on cold start or after bulk product uploads.
    """
    result = await db.execute(select(Product))
    products = result.scalars().all()

    if not products:
        search_index.clear()
        search_index.save()
        return RebuildIndexResponse(
            status="empty",
            total_indexed=0,
            message="No products found in DB. Index cleared.",
        )

    logger.info(f"Rebuilding FAISS index for {len(products)} products...")
    texts = [build_product_text(p) for p in products]
    vectors = embedder.embed_batch(texts)

    items = [(p.id, vectors[i]) for i, p in enumerate(products)]
    search_index.clear()
    search_index.add_batch(items, auto_save=True)

    return RebuildIndexResponse(
        status="success",
        total_indexed=len(products),
        message=f"Successfully indexed {len(products)} products into FAISS",
    )


@search_router.get("/status", summary="Search Index Status")
async def index_status():
    """
    Returns current status and item count of the vector search engine.
    """
    return {
        "status": "ready",
        "total_indexed": search_index.count(),
        "dimension": search_index.dim,
        "index_dir": search_index.index_dir,
    }
