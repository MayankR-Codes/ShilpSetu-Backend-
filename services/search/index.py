"""
ShilpSetu — Pillar 5: FAISS Search Index
Maintains a persistent vector index for product similarity and semantic query search.
Uses Cosine Similarity via Inner Product on L2-normalized 384-dimensional vectors.
"""

import os
import pickle
from typing import List, Optional, Tuple
import numpy as np

from api_gateway.logger import get_logger
from services.search.embedder import EMBEDDING_DIM

logger = get_logger(__name__)

DEFAULT_INDEX_DIR = os.path.join(os.getcwd(), "data", "search")


class SearchIndex:
    """
    Manages FAISS index and product ID mapping with persistence to disk.
    """

    def __init__(self, index_dir: str = DEFAULT_INDEX_DIR, dim: int = EMBEDDING_DIM):
        self.index_dir = index_dir
        self.dim = dim
        self.product_ids: List[int] = []
        self._index = None
        self._vectors: List[np.ndarray] = []  # In-memory vector store for fast rebuild/upsert

    def _init_empty_index(self):
        try:
            import faiss
            return faiss.IndexFlatIP(self.dim)
        except ImportError:
            logger.warning("FAISS is not installed. Using fallback vector search.")
            return None

    @property
    def index(self):
        if self._index is None:
            self._index = self._init_empty_index()
        return self._index

    def count(self) -> int:
        return len(self.product_ids)

    def clear(self):
        """Clears the index completely."""
        self._index = self._init_empty_index()
        self.product_ids = []
        self._vectors = []

    def add(self, product_id: int, vector: np.ndarray, auto_save: bool = True):
        """
        Adds or updates a product embedding in the index.
        """
        vec = np.asarray(vector, dtype=np.float32).reshape(1, self.dim)
        # Ensure L2 normalized
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm

        # If product already exists, remove it first
        if product_id in self.product_ids:
            idx = self.product_ids.index(product_id)
            self.product_ids.pop(idx)
            self._vectors.pop(idx)
            self._rebuild_faiss()

        self.product_ids.append(product_id)
        self._vectors.append(vec.flatten())

        if self.index is not None:
            self.index.add(vec)

        if auto_save:
            self.save()

    def add_batch(self, items: List[Tuple[int, np.ndarray]], auto_save: bool = True):
        """
        Add multiple (product_id, vector) pairs at once.
        """
        for pid, vec in items:
            self.add(pid, vec, auto_save=False)
        if auto_save:
            self.save()

    def remove(self, product_id: int, auto_save: bool = True) -> bool:
        """
        Removes a product ID from the index.
        """
        if product_id not in self.product_ids:
            return False

        idx = self.product_ids.index(product_id)
        self.product_ids.pop(idx)
        self._vectors.pop(idx)
        self._rebuild_faiss()

        if auto_save:
            self.save()
        return True

    def _rebuild_faiss(self):
        """Reconstructs the FAISS index from in-memory vectors."""
        self._index = self._init_empty_index()
        if self._vectors and self._index is not None:
            matrix = np.vstack(self._vectors).astype(np.float32)
            self._index.add(matrix)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Searches the index with a query vector.
        Returns list of (product_id, score) sorted in descending order of similarity.
        """
        if not self.product_ids:
            return []

        vec = np.asarray(query_vector, dtype=np.float32).reshape(1, self.dim)
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec = vec / norm

        k = min(top_k, len(self.product_ids))

        # FAISS search
        if self.index is not None:
            distances, indices = self.index.search(vec, k)
            results = []
            for score, idx in zip(distances[0], indices[0]):
                if idx != -1 and idx < len(self.product_ids):
                    results.append((self.product_ids[idx], float(score)))
            return results

        # Fallback numpy dot product (if FAISS is absent)
        matrix = np.vstack(self._vectors)
        scores = np.dot(matrix, vec.flatten())
        ranked_indices = np.argsort(scores)[::-1][:k]
        return [(self.product_ids[i], float(scores[i])) for i in ranked_indices]

    def save(self, directory: Optional[str] = None):
        """Persists the FAISS index and ID metadata to disk."""
        target_dir = directory or self.index_dir
        os.makedirs(target_dir, exist_ok=True)

        faiss_file = os.path.join(target_dir, "index.faiss")
        meta_file = os.path.join(target_dir, "index_ids.pkl")

        try:
            if self.index is not None:
                import faiss
                faiss.write_index(self.index, faiss_file)

            with open(meta_file, "wb") as f:
                pickle.dump({"ids": self.product_ids, "vectors": self._vectors}, f)
            logger.info(f"Saved FAISS index ({len(self.product_ids)} items) to {target_dir}")
        except Exception as e:
            logger.error(f"Failed to persist search index: {e}")

    def load(self, directory: Optional[str] = None) -> bool:
        """Loads the FAISS index and product IDs from disk."""
        target_dir = directory or self.index_dir
        faiss_file = os.path.join(target_dir, "index.faiss")
        meta_file = os.path.join(target_dir, "index_ids.pkl")

        if not os.path.exists(meta_file):
            logger.info(f"No existing search index found at {target_dir}. Starting fresh.")
            return False

        try:
            with open(meta_file, "rb") as f:
                data = pickle.load(f)
                self.product_ids = data.get("ids", [])
                self._vectors = data.get("vectors", [])

            if os.path.exists(faiss_file):
                try:
                    import faiss
                    self._index = faiss.read_index(faiss_file)
                except Exception as fe:
                    logger.warning(f"Could not read faiss file directly ({fe}), rebuilding from vectors...")
                    self._rebuild_faiss()
            else:
                self._rebuild_faiss()

            logger.info(f"Loaded search index with {len(self.product_ids)} items from {target_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to load search index from {target_dir}: {e}")
            return False


# Global singleton search index
search_index = SearchIndex()
