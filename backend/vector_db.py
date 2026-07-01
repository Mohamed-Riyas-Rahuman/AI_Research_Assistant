"""
vector_db.py
------------
Wraps a FAISS index + the sentence-transformers embedding model.

Responsibilities:
  - turn text into embeddings
  - store embeddings + metadata (source file, page number, raw text)
  - run similarity search for a query
  - persist / load the index to disk so re-uploading isn't required
    every time the server restarts
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


class VectorStore:
    def __init__(self, store_dir: str = "vector_store"):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.store_dir / "index.faiss"
        self.meta_path = self.store_dir / "metadata.pkl"

        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.dimension = self.model.get_sentence_embedding_dimension()

        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict] = []  # parallel list to FAISS vectors

        self._load_if_exists()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load_if_exists(self):
        if self.index_path.exists() and self.meta_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            # Inner product on L2-normalized vectors == cosine similarity
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = []

    def save(self):
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.metadata, f)

    # ------------------------------------------------------------------ #
    # Embedding
    # ------------------------------------------------------------------ #
    def embed(self, texts: List[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # required for cosine via inner product
        )
        return vectors.astype("float32")

    # ------------------------------------------------------------------ #
    # Insert
    # ------------------------------------------------------------------ #
    def add_records(self, records: List[Dict]):
        """
        records: list of {"text": ..., "source": ..., "page": ...}
        """
        if not records:
            return

        texts = [r["text"] for r in records]
        vectors = self.embed(texts)

        self.index.add(vectors)
        self.metadata.extend(records)
        self.save()

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query_vec = self.embed([query])
        scores, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            record = dict(self.metadata[idx])
            record["score"] = float(score)
            results.append(record)
        return results

    # ------------------------------------------------------------------ #
    # Utilities
    # ------------------------------------------------------------------ #
    def list_sources(self) -> List[str]:
        return sorted({r["source"] for r in self.metadata})

    def clear(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self.save()

    def stats(self) -> Dict:
        return {
            "total_chunks": len(self.metadata),
            "sources": self.list_sources(),
        }
