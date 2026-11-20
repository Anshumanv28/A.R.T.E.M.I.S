"""
CI regression guard for the retrieval layer: runs the same in-memory
benchmark as scripts/benchmark_retrieval.py and asserts loose floors,
so a change that quietly breaks keyword/hybrid search or the reranker
fails CI instead of only showing up in a manually-run report.
"""

from pathlib import Path

import pytest

from scripts.benchmark_retrieval import (
    build_in_memory_indexer,
    compute_config_metrics,
    load_retrieval_dataset,
    run_config,
)
from artemis.rag.core.retriever import RetrievalMode

DATASET_PATH = Path(__file__).parent / "eval" / "retrieval_dataset.json"


@pytest.fixture(scope="module")
def benchmark_metrics():
    data = load_retrieval_dataset(DATASET_PATH)
    indexer = build_in_memory_indexer(collection_name="retrieval_benchmark_ci")
    doc_texts = [d["text"] for d in data["corpus"]]
    doc_metadata = [{"doc_id": d["doc_id"]} for d in data["corpus"]]
    indexer.add_documents(doc_texts, doc_metadata)

    queries = data["queries"]
    metrics = {}
    for config_name, mode, rerank in [
        ("semantic", RetrievalMode.SEMANTIC, False),
        ("keyword", RetrievalMode.KEYWORD, False),
        ("hybrid", RetrievalMode.HYBRID, False),
        ("hybrid_rerank", RetrievalMode.HYBRID, True),
    ]:
        ranked, relevant, latencies_ms = run_config(indexer, mode, rerank, queries, max_k=10)
        metrics[config_name] = compute_config_metrics(config_name, ranked, relevant, latencies_ms)
    return metrics


def test_semantic_recall_meets_floor(benchmark_metrics):
    assert benchmark_metrics["semantic"].recall_at_10 >= 0.8


def test_keyword_recall_meets_floor(benchmark_metrics):
    assert benchmark_metrics["keyword"].recall_at_10 >= 0.7


def test_hybrid_recall_at_least_matches_best_single_strategy(benchmark_metrics):
    best_single = max(benchmark_metrics["semantic"].recall_at_10, benchmark_metrics["keyword"].recall_at_10)
    assert benchmark_metrics["hybrid"].recall_at_10 >= best_single - 0.05


def test_reranking_does_not_regress_mrr(benchmark_metrics):
    assert benchmark_metrics["hybrid_rerank"].mrr >= benchmark_metrics["hybrid"].mrr - 0.02
