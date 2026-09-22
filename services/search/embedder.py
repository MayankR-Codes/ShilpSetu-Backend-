"""
ShilpSetu — Pillar 5: Product Embedder
Uses multilingual sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
to produce 384-dimensional normalized dense vectors for Hindi and English text.
"""

import os
from typing import Any, Dict, List, Optional, Union
import numpy as np
from api_gateway.logger import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL_NAME = os.getenv("SEARCH_EMBED_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384


def build_product_text(product: Union[Dict[str, Any], Any]) -> str:
    """
    Constructs a rich textual representation of a product for semantic indexing.
    Accepts either a dict or an ORM/Pydantic product object.
    """
    def _get(key: str, default: Any = "") -> Any:
        if isinstance(product, dict):
            return product.get(key, default)
        return getattr(product, key, default)

    title_en = _get("title_en") or ""
    title_hi = _get("title_hi") or ""
    desc_en = _get("description_en") or ""
    desc_hi = _get("description_hi") or ""
    category = _get("category") or ""
    sub_category = _get("sub_category") or ""
    craft_type = _get("craft_type") or ""
    craft_heritage = _get("craft_heritage") or ""
    
    tags_raw = _get("tags") or []
    if isinstance(tags_raw, list):
        tags = " ".join(str(t) for t in tags_raw)
    else:
        tags = str(tags_raw)

    materials_raw = _get("materials_breakdown") or []
    materials_list = []
    if isinstance(materials_raw, list):
        for m in materials_raw:
            if isinstance(m, dict) and "material" in m:
                materials_list.append(str(m["material"]))
            elif isinstance(m, str):
                materials_list.append(m)
    materials = " ".join(materials_list)

    parts = [
        f"Title: {title_en}",
        f"Hindi Title: {title_hi}" if title_hi else "",
        f"Craft: {craft_type}" if craft_type else "",
        f"Heritage: {craft_heritage}" if craft_heritage else "",
        f"Category: {category} {sub_category}".strip() if (category or sub_category) else "",
        f"Materials: {materials}" if materials else "",
        f"Description: {desc_en}",
        f"Hindi Description: {desc_hi}" if desc_hi else "",
        f"Keywords: {tags}" if tags else "",
    ]

    cleaned_parts = [p.strip() for p in parts if p.strip()]
    return "\n".join(cleaned_parts)


class ProductEmbedder:
    """
    Encapsulates SentenceTransformer model loading and embedding operations.
    Lazy-loads the model to preserve startup speed until search/indexing is invoked.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading embedding model '{self.model_name}'...")
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Embedding model '{self.model_name}' loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer: {e}")
                raise
        return self._model

    def embed(self, text: str) -> np.ndarray:
        """
        Embed a single text string into a 384-dim normalized float32 vector.
        """
        if not text or not text.strip():
            # Return zero vector if empty
            vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
            return vec

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embedding, dtype=np.float32).reshape(-1)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Batch embed multiple texts. Returns (N, 384) float32 normalized array.
        """
        if not texts:
            return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)


# Global singleton instance
embedder = ProductEmbedder()
