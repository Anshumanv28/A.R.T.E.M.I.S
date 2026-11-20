"""
Retrieval-quality metrics: Recall@K and Mean Reciprocal Rank (MRR).

Pure functions over ranked doc_ids vs a relevant-doc_id set, independent of
how the ranking was produced (semantic, keyword, hybrid, reranked, ...).
"""

from typing import Iterable, List, Sequence


def recall_at_k(ranked_doc_ids: Sequence[str], relevant_doc_ids: Iterable[str], k: int) -> float:
    """
    Fraction of relevant_doc_ids that appear in the top k of ranked_doc_ids.

    Returns 0.0 if relevant_doc_ids is empty (nothing to recall).
    """
    relevant = set(relevant_doc_ids)
    if not relevant:
        return 0.0
    top_k = set(ranked_doc_ids[:k])
    return len(relevant & top_k) / len(relevant)


def reciprocal_rank(ranked_doc_ids: Sequence[str], relevant_doc_ids: Iterable[str]) -> float:
    """1/rank of the first relevant doc_id in ranked_doc_ids, or 0.0 if none appear."""
    relevant = set(relevant_doc_ids)
    for i, doc_id in enumerate(ranked_doc_ids, start=1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0


def mean_reciprocal_rank(per_query_ranked: List[Sequence[str]], per_query_relevant: List[Iterable[str]]) -> float:
    """MRR across queries; per_query_ranked[i] is scored against per_query_relevant[i]."""
    if not per_query_ranked:
        return 0.0
    scores = [
        reciprocal_rank(ranked, relevant)
        for ranked, relevant in zip(per_query_ranked, per_query_relevant)
    ]
    return sum(scores) / len(scores)


__all__ = ["recall_at_k", "reciprocal_rank", "mean_reciprocal_rank"]
