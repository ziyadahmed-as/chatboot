"""
Tests for RAG engine and vector store.
Validates: Requirements 5.1, 5.4, 5.7
"""
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deterministic_embedding(text: str, dim: int = 64) -> list[float]:
    """Return a unique, deterministic unit vector derived from the text hash."""
    digest = hashlib.sha256(text.encode()).digest()
    # Build a float vector from the digest bytes, tiling if needed
    raw = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    # Tile to desired dimension
    tiled = np.tile(raw, (dim // len(raw)) + 1)[:dim]
    norm = np.linalg.norm(tiled)
    if norm == 0:
        tiled[0] = 1.0
        norm = 1.0
    return (tiled / norm).tolist()


def _mock_get_embeddings(texts: list[str]) -> list[list[float]]:
    return [_deterministic_embedding(t) for t in texts]


# ---------------------------------------------------------------------------
# Task 6.3 — Property test: RAG round-trip integrity
# Validates: Requirements 5.7
# ---------------------------------------------------------------------------

@given(
    st.lists(
        st.text(
            min_size=1,
            max_size=100,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        ),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=50, deadline=None)
def test_rag_roundtrip_integrity(texts: list[str]):
    """
    **Validates: Requirements 5.7**

    Property: For all ingested documents, retrieving with the original text as
    query returns content that contains the ingested content.
    """
    from app.services.vector_store import FAISSAdapter

    with patch("app.services.vector_store._get_embeddings", side_effect=_mock_get_embeddings):
        adapter = FAISSAdapter()
        adapter.add(texts, domain=None)

        for text in texts:
            results = adapter.query(query_text=text, top_k=len(texts), threshold=0.5)
            assert any(text in r for r in results), (
                f"Expected to find '{text}' in query results, got: {results}"
            )


# ---------------------------------------------------------------------------
# Task 6.4 — Unit tests for RAG engine
# Validates: Requirements 5.1, 5.4
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieve_returns_empty_when_no_results():
    """When the vector store returns an empty list, retrieve() returns []."""
    mock_store = MagicMock()
    mock_store.query.return_value = []

    with patch("app.services.rag_engine.get_vector_store", return_value=mock_store):
        from app.services.rag_engine import retrieve
        result = await retrieve(query="anything")

    assert result == []
    mock_store.query.assert_called_once_with(query_text="anything", top_k=5, threshold=0.7)


@pytest.mark.asyncio
async def test_retrieve_returns_results_above_threshold():
    """When the vector store returns results, retrieve() passes them through."""
    docs = ["doc one", "doc two"]
    mock_store = MagicMock()
    mock_store.query.return_value = docs

    with patch("app.services.rag_engine.get_vector_store", return_value=mock_store):
        from app.services.rag_engine import retrieve
        result = await retrieve(query="some query", top_k=5)

    assert result == docs
