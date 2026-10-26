"""
Runs golden-dataset cases against a live Supervisor and classifies the result.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from artemis.agent.llm import usage_tracker
from artemis.agent.llm.usage_tracker import UsageSnapshot
from artemis.agent.supervisor import Supervisor
from artemis.eval.dataset import EvalCase
from artemis.eval.pricing import estimate_cost
from artemis.utils import get_logger

logger = get_logger(__name__)

NON_DIRECT_AGENTS = {"rag_search", "ingestion", "collection_management"}

# Hardcoded literal from Supervisor._direct_answer -- the "silent sub-agent fallback"
# signature only exists because this exact string is set there, never anywhere else.
_DIRECT_FALLBACK_REASONING = "Direct answer — no tools needed."


def _is_subsequence(expected: List[str], actual: List[str]) -> bool:
    """True if every item in `expected` appears in `actual`, in order (not necessarily contiguous)."""
    it = iter(actual)
    return all(item in it for item in expected)


@dataclass
class CaseResult:
    case_id: str
    query: str
    expected_agent: str
    actual_agent: Optional[str]
    actual_tool_names: List[str]
    routing_correct: bool
    tool_sequence_correct: bool
    forbidden_tool_used: Optional[str]
    error: Optional[str]
    failure_reason: Optional[str]
    success: bool
    duration_s: float
    usage: UsageSnapshot
    cost_usd: Optional[float]
    model_name: str = ""


def classify_failure(
    state: Dict[str, Any], case: EvalCase, actual_tool_names: List[str]
) -> Optional[str]:
    """
    Return a short failure-category string, or None if the case passed.

    Checks the Supervisor.invoke() swallowed-exception signature first: when a
    sub-agent raises, Supervisor falls back to a direct answer but `routed_to`
    still reports the *original intended* agent -- a naive check would read this
    as "planner chose not to use tools" rather than "the sub-agent crashed".
    """
    routed_to = state.get("routed_to")
    if (
        routed_to in NON_DIRECT_AGENTS
        and not actual_tool_names
        and state.get("reasoning") == _DIRECT_FALLBACK_REASONING
    ):
        return "likely_silent_subagent_fallback"

    if case.assert_no_error and state.get("error"):
        return "unexpected_error"

    if routed_to != case.expected_agent:
        return "wrong_routing"

    forbidden = next((t for t in case.forbidden_tools if t in actual_tool_names), None)
    if forbidden is not None:
        return "forbidden_tool_used"

    if not _is_subsequence(case.expected_tool_sequence, actual_tool_names):
        return "tool_sequence_mismatch"

    return None


def run_case(supervisor: Supervisor, case: EvalCase, model_name: str = "") -> CaseResult:
    """Run one case against a live Supervisor and classify the outcome."""
    usage_tracker.reset()
    start = time.monotonic()
    try:
        state = supervisor.invoke(case.query)
    except Exception as e:
        logger.exception("Eval case %s: Supervisor.invoke raised", case.id)
        state = {"error": str(e), "routed_to": None, "tool_calls": []}
    duration_s = time.monotonic() - start

    actual_tool_names = [tc.get("tool_name") for tc in (state.get("tool_calls") or [])]
    error = state.get("error")
    actual_agent = state.get("routed_to")

    failure_reason = classify_failure(state, case, actual_tool_names)

    usage = usage_tracker.snapshot()
    cost_usd = estimate_cost(model_name, usage.prompt_tokens, usage.completion_tokens) if model_name else None

    return CaseResult(
        case_id=case.id,
        query=case.query,
        expected_agent=case.expected_agent,
        actual_agent=actual_agent,
        actual_tool_names=actual_tool_names,
        routing_correct=(actual_agent == case.expected_agent),
        tool_sequence_correct=_is_subsequence(case.expected_tool_sequence, actual_tool_names),
        forbidden_tool_used=next((t for t in case.forbidden_tools if t in actual_tool_names), None),
        error=error,
        failure_reason=failure_reason,
        success=failure_reason is None,
        duration_s=duration_s,
        usage=usage,
        cost_usd=cost_usd,
        model_name=model_name,
    )


def run_suite(
    cases: List[EvalCase],
    supervisor: Supervisor,
    model_name: str = "",
    skip_mutating: bool = False,
) -> List[CaseResult]:
    """Run every case in order, optionally skipping mutating ones."""
    results: List[CaseResult] = []
    for case in cases:
        if skip_mutating and case.mutating:
            logger.info("Skipping mutating case %s (--skip-mutating)", case.id)
            continue
        logger.info("Running eval case: %s", case.id)
        results.append(run_case(supervisor, case, model_name=model_name))
    return results


__all__ = ["CaseResult", "classify_failure", "run_case", "run_suite"]
