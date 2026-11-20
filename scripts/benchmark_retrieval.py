#!/usr/bin/env python3
"""
Retrieval benchmark: compares semantic, keyword, hybrid, and hybrid+rerank
on Recall@5, Recall@10, MRR, and latency, over a small labeled dataset
(tests/eval/retrieval_dataset.json).

Runs entirely in-memory (an embedded Qdrant instance, no server/Docker
required) so it's cheap to re-run after any retrieval-layer change --
see tests/eval/README.md for why the *agent* eval harness needs a real
Qdrant but this one doesn't: it talks to Retriever/Indexer directly and
never goes through ingestion file I/O or the agent loop.

Usage:
    python scripts/benchmark_retrieval.py
    python scripts/benchmark_retrieval.py --dataset tests/eval/retrieval_dataset.json
"""

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient

from artemis.eval.retrieval_metrics import mean_reciprocal_rank, recall_at_k
from artemis.rag.core.embedder import Embedder
from artemis.rag.core.indexer import Indexer
from artemis.rag.core.reranker import get_reranker
from artemis.rag.core.retriever import Retriever, RetrievalMode
from artemis.utils import get_logger

logger = get_logger(__name__)

DEFAULT_DATASET = Path("tests/eval/retrieval_dataset.json")
DEFAULT_REPORTS_DIR = Path("eval_reports")
CONFIGS = ["semantic", "keyword", "hybrid", "hybrid_rerank"]
RECALL_KS = (5, 10)


@dataclass
class ConfigMetrics:
    config: str
    recall_at_5: float
    recall_at_10: float
    mrr: float
    avg_latency_ms: float


def load_retrieval_dataset(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_in_memory_indexer(collection_name: str = "retrieval_benchmark") -> Indexer:
    """
    An Indexer wired to an embedded (":memory:") Qdrant instance.

    Indexer.__init__ always requires a qdrant_url string (there's no server
    to point it at here), so we bypass it with __new__ and set the same
    attributes __init__ would have -- every method on Indexer/Retriever
    only ever touches these three instance attributes.
    """
    indexer = Indexer.__new__(Indexer)
    indexer.collection_name = collection_name
    indexer.embedder = Embedder()
    indexer.metadata_config = None
    indexer.qdrant_client = QdrantClient(location=":memory:")
    return indexer


def retrieve_doc_ids(retriever: Retriever, query: str, k: int, rerank: bool) -> tuple:
    """Returns (ranked_doc_ids, latency_ms) for one query against one retriever config."""
    fetch_k = max(k * 4, 20) if rerank else k
    start = time.perf_counter()
    results = retriever.retrieve(query, k=fetch_k)
    if rerank:
        results = get_reranker().rerank(query, results, top_k=k)
    latency_ms = (time.perf_counter() - start) * 1000
    doc_ids = [r.get("metadata", {}).get("doc_id") for r in results[:k]]
    return doc_ids, latency_ms


def run_config(indexer: Indexer, mode: RetrievalMode, rerank: bool, queries: List[Dict[str, Any]], max_k: int):
    retriever = Retriever(mode=mode, indexer=indexer)
    per_query_ranked = []
    per_query_relevant = []
    latencies_ms = []
    for q in queries:
        ranked, latency_ms = retrieve_doc_ids(retriever, q["query"], k=max_k, rerank=rerank)
        per_query_ranked.append(ranked)
        per_query_relevant.append(q["relevant_doc_ids"])
        latencies_ms.append(latency_ms)
    return per_query_ranked, per_query_relevant, latencies_ms


def compute_config_metrics(config_name: str, per_query_ranked, per_query_relevant, latencies_ms) -> ConfigMetrics:
    recall_5 = sum(
        recall_at_k(ranked, relevant, k=5) for ranked, relevant in zip(per_query_ranked, per_query_relevant)
    ) / len(per_query_ranked)
    recall_10 = sum(
        recall_at_k(ranked, relevant, k=10) for ranked, relevant in zip(per_query_ranked, per_query_relevant)
    ) / len(per_query_ranked)
    mrr = mean_reciprocal_rank(per_query_ranked, per_query_relevant)
    avg_latency_ms = sum(latencies_ms) / len(latencies_ms)
    return ConfigMetrics(
        config=config_name,
        recall_at_5=recall_5,
        recall_at_10=recall_10,
        mrr=mrr,
        avg_latency_ms=avg_latency_ms,
    )


def print_summary(all_metrics: List[ConfigMetrics]) -> None:
    print(f"\n{'=' * 72}")
    print("A.R.T.E.M.I.S retrieval benchmark")
    print(f"{'=' * 72}")
    print(f"{'Config':<16}{'Recall@5':>12}{'Recall@10':>12}{'MRR':>10}{'Avg latency (ms)':>20}")
    for m in all_metrics:
        print(f"{m.config:<16}{m.recall_at_5:>12.2%}{m.recall_at_10:>12.2%}{m.mrr:>10.3f}{m.avg_latency_ms:>20.1f}")
    print(f"{'=' * 72}\n")


def write_json_report(all_metrics: List[ConfigMetrics], reports_dir: Path = DEFAULT_REPORTS_DIR) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = reports_dir / f"retrieval_benchmark_{timestamp}.json"
    payload = {
        "generated_at": timestamp,
        "configs": [asdict(m) for m in all_metrics],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    args = parser.parse_args()

    data = load_retrieval_dataset(args.dataset)
    corpus = data["corpus"]
    queries = data["queries"]

    indexer = build_in_memory_indexer()
    doc_texts = [d["text"] for d in corpus]
    doc_metadata = [{"doc_id": d["doc_id"]} for d in corpus]
    indexer.add_documents(doc_texts, doc_metadata)

    max_k = max(RECALL_KS)
    all_metrics = []
    for config_name in CONFIGS:
        if config_name == "hybrid_rerank":
            mode, rerank = RetrievalMode.HYBRID, True
        else:
            mode, rerank = RetrievalMode(config_name), False
        ranked, relevant, latencies_ms = run_config(indexer, mode, rerank, queries, max_k)
        all_metrics.append(compute_config_metrics(config_name, ranked, relevant, latencies_ms))

    print_summary(all_metrics)
    report_path = write_json_report(all_metrics)
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
