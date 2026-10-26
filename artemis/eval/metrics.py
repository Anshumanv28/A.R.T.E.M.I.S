"""
Aggregate per-case CaseResults into suite-level metrics.
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from artemis.eval.runner import CaseResult


@dataclass
class SuiteMetrics:
    total_cases: int
    task_success_rate: float
    routing_accuracy: float
    tool_selection_accuracy: float
    avg_step_count: float
    avg_duration_s: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: Optional[float]
    pricing_unavailable_count: int
    failure_breakdown: Dict[str, int] = field(default_factory=dict)


def compute_metrics(results: List[CaseResult]) -> SuiteMetrics:
    """Compute suite-level metrics from a list of CaseResult. Empty input -> all-zero metrics."""
    n = len(results)
    if n == 0:
        return SuiteMetrics(
            total_cases=0,
            task_success_rate=0.0,
            routing_accuracy=0.0,
            tool_selection_accuracy=0.0,
            avg_step_count=0.0,
            avg_duration_s=0.0,
            total_prompt_tokens=0,
            total_completion_tokens=0,
            total_tokens=0,
            total_cost_usd=None,
            pricing_unavailable_count=0,
            failure_breakdown={},
        )

    success_count = sum(1 for r in results if r.success)
    routing_correct_count = sum(1 for r in results if r.routing_correct)
    tool_selection_correct_count = sum(
        1 for r in results if r.tool_sequence_correct and r.forbidden_tool_used is None
    )
    total_steps = sum(len(r.actual_tool_names) for r in results)
    total_duration = sum(r.duration_s for r in results)
    total_prompt_tokens = sum(r.usage.prompt_tokens for r in results)
    total_completion_tokens = sum(r.usage.completion_tokens for r in results)
    total_tokens = sum(r.usage.total_tokens for r in results)

    priced_costs = [r.cost_usd for r in results if r.cost_usd is not None]
    pricing_unavailable_count = sum(1 for r in results if r.model_name and r.cost_usd is None)
    total_cost_usd = sum(priced_costs) if priced_costs else None

    failure_breakdown = dict(Counter(r.failure_reason for r in results if r.failure_reason))

    return SuiteMetrics(
        total_cases=n,
        task_success_rate=success_count / n,
        routing_accuracy=routing_correct_count / n,
        tool_selection_accuracy=tool_selection_correct_count / n,
        avg_step_count=total_steps / n,
        avg_duration_s=total_duration / n,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        total_tokens=total_tokens,
        total_cost_usd=total_cost_usd,
        pricing_unavailable_count=pricing_unavailable_count,
        failure_breakdown=failure_breakdown,
    )


__all__ = ["SuiteMetrics", "compute_metrics"]
