"""
Agent evaluation harness: runs the golden dataset against a live Supervisor
and computes real metrics (success rate, routing/tool-selection accuracy,
step count, token usage, cost-per-task, failure breakdown).
"""

from artemis.eval.dataset import EvalCase, load_dataset
from artemis.eval.metrics import SuiteMetrics, compute_metrics
from artemis.eval.runner import CaseResult, classify_failure, run_case, run_suite

__all__ = [
    "EvalCase",
    "load_dataset",
    "SuiteMetrics",
    "compute_metrics",
    "CaseResult",
    "classify_failure",
    "run_case",
    "run_suite",
]
