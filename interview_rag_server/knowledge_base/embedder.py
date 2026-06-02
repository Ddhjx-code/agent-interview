"""Embedding generation using sentence-transformers."""

import os
from typing import Optional

import numpy as np


_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts: list[str], batch_size: int = 64) -> np.ndarray:
    """Generate embeddings for a list of texts.

    Returns numpy array of shape (len(texts), embedding_dim).
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 100,
        normalize_embeddings=True,
    )
    return np.array(embeddings, dtype=np.float32)


def embed_query(query: str) -> np.ndarray:
    """Generate embedding for a single query string.

    Returns numpy array of shape (embedding_dim,).
    """
    model = _get_model()
    embedding = model.encode(
        [query],
        normalize_embeddings=True,
    )
    return np.array(embedding[0], dtype=np.float32)


def get_embedding_dim() -> int:
    """Return the dimensionality of the embedding model."""
    model = _get_model()
    return model.get_sentence_embedding_dimension()
