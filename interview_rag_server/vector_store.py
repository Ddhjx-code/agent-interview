"""FAISS-backed vector store with metadata and topic filtering."""

import json
from pathlib import Path
from typing import Optional

import faiss
import numpy as np


class VectorStore:
    """In-memory FAISS index with associated metadata."""

    def __init__(self, dim: int = 768):
        self._dim = dim
        self._index = faiss.IndexFlatIP(dim)
        self._metadata: list[dict] = []

    @property
    def size(self) -> int:
        return self._index.ntotal

    def add(self, vectors: np.ndarray, metadata: list[dict]) -> None:
        assert vectors.shape[0] == len(metadata)
        assert vectors.shape[1] == self._dim
        self._index.add(vectors)
        self._metadata.extend(metadata)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        topic_filter: Optional[str] = None,
    ) -> list[dict]:
        search_k = top_k * 5 if topic_filter else top_k
        query_2d = query_vector.reshape(1, -1)
        scores, indices = self._index.search(query_2d, min(search_k, self.size))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self._metadata[idx]
            if topic_filter and meta.get("topic") != topic_filter:
                continue
            results.append({**meta, "score": float(score)})
            if len(results) >= top_k:
                break

        return results

    def save(self, directory: Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(directory / "faiss_index.bin"))
        with open(directory / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, directory: Path) -> "VectorStore":
        directory = Path(directory)
        index = faiss.read_index(str(directory / "faiss_index.bin"))
        with open(directory / "metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)
        store = cls(dim=index.d)
        store._index = index
        store._metadata = metadata
        return store
