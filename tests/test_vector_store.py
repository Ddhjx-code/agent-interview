import json
import tempfile
from pathlib import Path

import numpy as np

from interview_rag_server.vector_store import VectorStore


def _make_store(n_vectors: int = 10, dim: int = 768):
    vectors = np.random.randn(n_vectors, dim).astype(np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / norms

    metadata = [
        {
            "id": i,
            "text": f"chunk number {i} about topic {i % 3}",
            "topic": ["llm", "agent", "rag"][i % 3],
            "source": f"file_{i}.md",
            "content_type": "theory",
        }
        for i in range(n_vectors)
    ]

    store = VectorStore(dim=dim)
    store.add(vectors, metadata)
    return store


def test_vector_store_search_returns_results():
    store = _make_store()
    query_vec = np.random.randn(768).astype(np.float32)
    query_vec = query_vec / np.linalg.norm(query_vec)
    results = store.search(query_vec, top_k=3)
    assert len(results) == 3
    assert all("text" in r for r in results)
    assert all("score" in r for r in results)


def test_vector_store_topic_filter():
    store = _make_store(n_vectors=30)
    query_vec = np.random.randn(768).astype(np.float32)
    query_vec = query_vec / np.linalg.norm(query_vec)
    results = store.search(query_vec, top_k=5, topic_filter="agent")
    assert len(results) <= 5
    assert all(r["topic"] == "agent" for r in results)


def test_vector_store_save_and_load(tmp_path):
    store = _make_store()
    store.save(tmp_path)

    loaded = VectorStore.load(tmp_path)
    query_vec = np.random.randn(768).astype(np.float32)
    query_vec = query_vec / np.linalg.norm(query_vec)

    results_original = store.search(query_vec, top_k=3)
    results_loaded = loaded.search(query_vec, top_k=3)

    assert len(results_original) == len(results_loaded)
    for orig, load in zip(results_original, results_loaded):
        assert orig["id"] == load["id"]
