"""
Cross-encoder reranking for A.R.T.E.M.I.S.

Reranking scores each (query, candidate) pair jointly through a small
cross-encoder model, which is more accurate at judging relevance than
comparing independently-computed embeddings or BM25 scores. It's applied
as a second pass on top of whatever retrieval strategy (semantic, keyword,
hybrid) produced the initial candidate set.
"""

from typing import List, Dict, Any, Optional

from artemis.utils import get_logger

logger = get_logger(__name__)

DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False


class Reranker:
    """Reorders retrieved candidates by cross-encoder relevance to the query."""

    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL):
        if not CROSS_ENCODER_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for reranking (CrossEncoder not found)."
            )
        self.model_name = model_name
        logger.info(f"Loading reranker model: {model_name}")
        self._model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Score each candidate's text against the query and return them sorted
        by relevance, highest first. The original retrieval score is kept in
        metadata['retrieval_score']; 'score' is overwritten with the
        cross-encoder relevance score.

        Args:
            query: Search query string
            candidates: Results from a retrieval strategy ({text, score, metadata})
            top_k: If given, truncate to this many results after reranking

        Returns:
            Reranked list of result dicts (same shape as input)
        """
        if not candidates:
            return candidates

        pairs = [(query, c.get("text", "")) for c in candidates]
        logger.debug(f"Reranking {len(candidates)} candidate(s) for query='{query[:50]}...'")
        scores = self._model.predict(pairs)

        reranked = []
        for candidate, rerank_score in zip(candidates, scores):
            metadata = dict(candidate.get("metadata", {}))
            metadata["retrieval_score"] = candidate.get("score")
            reranked.append({
                "text": candidate.get("text", ""),
                "score": float(rerank_score),
                "metadata": metadata,
            })

        reranked.sort(key=lambda r: r["score"], reverse=True)
        if top_k is not None:
            reranked = reranked[:top_k]
        return reranked


_reranker_singleton: Optional[Reranker] = None


def get_reranker(model_name: str = DEFAULT_RERANKER_MODEL) -> Reranker:
    """Lazily create and cache a single Reranker instance (the model is ~17M params but no need to load it more than once)."""
    global _reranker_singleton
    if _reranker_singleton is None or _reranker_singleton.model_name != model_name:
        _reranker_singleton = Reranker(model_name=model_name)
    return _reranker_singleton
