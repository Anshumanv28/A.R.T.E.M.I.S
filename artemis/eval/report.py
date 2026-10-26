"""
Write/print eval suite reports: a timestamped JSON file under eval_reports/
(for diffing across runs) plus a human-readable console summary.
"""

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from artemis.eval.metrics import SuiteMetrics
from artemis.eval.runner import CaseResult

DEFAULT_REPORTS_DIR = Path("eval_reports")


def write_json_report(
    metrics: SuiteMetrics,
    results: List[CaseResult],
    reports_dir: Optional[Path] = None,
) -> Path:
    """Write a timestamped JSON report (metrics + full per-case results) and return its path."""
    reports_dir = reports_dir or DEFAULT_REPORTS_DIR
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = reports_dir / f"eval_report_{timestamp}.json"

    payload = {
        "generated_at": timestamp,
        "metrics": asdict(metrics),
        "results": [
            {**asdict(r), "usage": asdict(r.usage)} for r in results
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def print_human_summary(metrics: SuiteMetrics, results: List[CaseResult]) -> None:
    """Print a console summary: pass/fail per case, then suite-level metrics."""
    print(f"\n{'=' * 60}")
    print("A.R.T.E.M.I.S agent eval results")
    print(f"{'=' * 60}")
    for r in results:
        status = "PASS" if r.success else f"FAIL ({r.failure_reason})"
        print(f"  [{status}] {r.case_id}  (routed_to={r.actual_agent}, steps={len(r.actual_tool_names)})")

    print(f"\n{'-' * 60}")
    print(f"Total cases:              {metrics.total_cases}")
    print(f"Task success rate:        {metrics.task_success_rate:.0%}")
    print(f"Routing accuracy:         {metrics.routing_accuracy:.0%}")
    print(f"Tool-selection accuracy:  {metrics.tool_selection_accuracy:.0%}")
    print(f"Avg step count:           {metrics.avg_step_count:.1f}")
    print(f"Avg duration (s):         {metrics.avg_duration_s:.2f}")
    print(f"Total tokens:             {metrics.total_tokens} (prompt={metrics.total_prompt_tokens}, completion={metrics.total_completion_tokens})")
    if metrics.total_cost_usd is not None:
        print(f"Total cost (USD):         ${metrics.total_cost_usd:.6f}")
    if metrics.pricing_unavailable_count:
        print(f"  ({metrics.pricing_unavailable_count} case(s) ran on an unpriced model -- cost reported as pricing_unavailable)")
    if metrics.failure_breakdown:
        print("Failure breakdown:")
        for reason, count in sorted(metrics.failure_breakdown.items(), key=lambda kv: -kv[1]):
            print(f"  - {reason}: {count}")
    print(f"{'=' * 60}\n")


__all__ = ["write_json_report", "print_human_summary", "DEFAULT_REPORTS_DIR"]
