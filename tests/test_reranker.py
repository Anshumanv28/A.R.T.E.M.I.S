"""
Unit tests for cross-encoder reranking.

Does not require Qdrant - exercises the Reranker class directly against
hand-built candidate lists. Requires internet access on first run to
download the cross-encoder model from Hugging Face Hub (cached after that).
"""

import pytest

from artemis.rag.core.reranker import CROSS_ENCODER_AVAILABLE, get_reranker

pytestmark = pytest.mark.skipif(
    not CROSS_ENCODER_AVAILABLE, reason="sentence-transformers CrossEncoder not available"
)


def _candidates():
    return [
        {"text": "The error code ERR-4032 indicates a database timeout.", "score": 0.4, "metadata": {"doc": "a"}},
        {"text": "Our Q3 revenue grew by 12% year over year.", "score": 0.9, "metadata": {"doc": "b"}},
        {"text": "ERR-4032 occurs when the connection pool is exhausted.", "score": 0.5, "metadata": {"doc": "c"}},
    ]


def test_rerank_reorders_by_relevance():
    reranker = get_reranker()
    results = reranker.rerank("What causes error code ERR-4032?", _candidates())

    assert len(results) == 3
    # Both ERR-4032 docs should outrank the unrelated revenue doc, even though
    # the revenue doc had the highest original retrieval score.
    top_docs = {results[0]["metadata"]["doc"], results[1]["metadata"]["doc"]}
    assert top_docs == {"a", "c"}
    assert results[-1]["metadata"]["doc"] == "b"


def test_rerank_preserves_retrieval_score_in_metadata():
    reranker = get_reranker()
    results = reranker.rerank("database timeout", _candidates())

    for r in results:
        assert "retrieval_score" in r["metadata"]


def test_rerank_respects_top_k():
    reranker = get_reranker()
    results = reranker.rerank("error code", _candidates(), top_k=2)
    assert len(results) == 2


def test_rerank_empty_candidates_returns_empty():
    reranker = get_reranker()
    assert reranker.rerank("anything", []) == []
