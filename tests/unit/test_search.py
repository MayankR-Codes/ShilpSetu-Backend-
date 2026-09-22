"""
Unit tests for ShilpSetu Semantic Buyer Search & Recommendation Engine (Pillar 5).
"""

import os
import shutil
import tempfile
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from api_gateway.main import app
from services.search.embedder import build_product_text, EMBEDDING_DIM
from services.search.index import SearchIndex

client = TestClient(app)


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def temp_index_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ── Tests ──────────────────────────────────────────────────────────

def test_build_product_text_dict():
    """Verify rich text generation from a dictionary product representation."""
    product = {
        "title_en": "Handmade Terracotta Clay Vase",
        "title_hi": "हस्तनिर्मित मिट्टी का फूलदान",
        "description_en": "An authentic eco-friendly decorative vase crafted from alluvial clay.",
        "description_hi": "प्राकृतिक मिट्टी से बना एक सुंदर फूलदान।",
        "category": "Pottery",
        "sub_category": "Terracotta",
        "craft_type": "Terracotta Craft",
        "craft_heritage": "Bankura Terracotta (GI Tagged)",
        "tags": ["clay", "vase", "terracotta", "home decor"],
        "materials_breakdown": [
            {"material": "Natural Clay", "percentage": 85.0},
            {"material": "Mineral Pigment", "percentage": 15.0},
        ],
    }

    text = build_product_text(product)
    assert "Handmade Terracotta Clay Vase" in text
    assert "Bankura Terracotta" in text
    assert "Pottery" in text
    assert "Natural Clay" in text
    assert "Mineral Pigment" in text
    assert "eco-friendly" in text


def test_build_product_text_minimal():
    """Verify robust handling when fields are missing."""
    product = {"title_en": "Brass Diya"}
    text = build_product_text(product)
    assert "Brass Diya" in text


def test_search_index_add_search_remove(temp_index_dir):
    """Verify adding, searching, and removing vectors in SearchIndex."""
    index = SearchIndex(index_dir=temp_index_dir, dim=8)

    # Create 3 normalized vectors of dim 8
    v1 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    v2 = np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    v3 = np.array([0.7, 0.7, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
    v3 = v3 / np.linalg.norm(v3)

    index.add(101, v1, auto_save=False)
    index.add(102, v2, auto_save=False)
    index.add(103, v3, auto_save=False)

    assert index.count() == 3

    # Query matching v1
    results = index.search(v1, top_k=2)
    assert len(results) == 2
    top_pid, top_score = results[0]
    assert top_pid == 101
    assert top_score > 0.95

    # Remove product 101
    removed = index.remove(101, auto_save=False)
    assert removed is True
    assert index.count() == 2

    # Query again; 101 should no longer be present
    results_after = index.search(v1, top_k=2)
    pids = [pid for pid, _ in results_after]
    assert 101 not in pids


def test_search_index_persistence(temp_index_dir):
    """Verify saving and loading the FAISS index to/from disk."""
    index1 = SearchIndex(index_dir=temp_index_dir, dim=4)
    v1 = np.array([0.5, 0.5, 0.5, 0.5], dtype=np.float32)
    v2 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

    index1.add(1, v1, auto_save=True)
    index1.add(2, v2, auto_save=True)
    assert index1.count() == 2

    # Create a new instance pointing to same directory and load
    index2 = SearchIndex(index_dir=temp_index_dir, dim=4)
    loaded = index2.load()
    assert loaded is True
    assert index2.count() == 2
    assert index2.product_ids == [1, 2]

    # Search loaded index
    res = index2.search(v2, top_k=1)
    assert res[0][0] == 2


def test_search_status_endpoint():
    """Verify GET /api/v1/search/status responds correctly."""
    response = client.get("/api/v1/search/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "total_indexed" in data
    assert "dimension" in data
    assert data["dimension"] == EMBEDDING_DIM


def test_search_query_empty_index():
    """Verify POST /api/v1/search/query returns empty results gracefully when index is empty."""
    from services.search.index import search_index
    orig_ids = search_index.product_ids
    orig_vectors = search_index._vectors

    try:
        search_index.clear()
        payload = {"query": "terracotta elephant", "top_k": 5}
        response = client.post("/api/v1/search/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []
    finally:
        search_index.product_ids = orig_ids
        search_index._vectors = orig_vectors
        search_index._rebuild_faiss()


def test_similar_not_found():
    """Verify GET /api/v1/search/similar/{product_id} returns 404 for non-existent product."""
    from shared.db.session import get_db
    from unittest.mock import AsyncMock, MagicMock

    mock_session = AsyncMock()
    mock_exec = MagicMock()
    mock_exec.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_exec

    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        response = client.get("/api/v1/search/similar/99999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_search_query_with_results():
    """Verify POST /api/v1/search/query ranks and returns matching products with mock DB."""
    from services.search.index import search_index
    from shared.db.session import get_db
    from shared.db.models import Product
    from unittest.mock import AsyncMock, MagicMock

    mock_session = AsyncMock()
    p1 = Product(
        id=77,
        title_en="Handcrafted Clay Elephant",
        category="Pottery",
        sub_category="Terracotta",
        craft_type="Terracotta",
        price_suggested=650.0,
    )
    mock_exec = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [p1]
    mock_exec.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_exec

    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        search_index.add(77, np.ones(EMBEDDING_DIM, dtype=np.float32), auto_save=False)
        response = client.post("/api/v1/search/query", json={"query": "clay elephant", "top_k": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["product_id"] == 77
        assert data["results"][0]["title_en"] == "Handcrafted Clay Elephant"
    finally:
        search_index.remove(77, auto_save=False)
        app.dependency_overrides.pop(get_db, None)

