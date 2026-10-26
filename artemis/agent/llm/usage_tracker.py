"""
Thread-local token-usage accumulator.

Both LLM clients are reconstructed fresh per call (planner_node, direct_answer_node,
Supervisor._get_llm_client()), so a plain instance attribute on the client wouldn't
survive across a task's multiple calls. This module-level thread-local accumulator
does: call reset() once at the start of a task, record() after each LLM call, and
snapshot() at the end to read totals back out.
"""

import threading
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class UsageSnapshot:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    call_count: int = 0
    models: List[str] = field(default_factory=list)


_local = threading.local()


def _state() -> UsageSnapshot:
    if not hasattr(_local, "snapshot"):
        _local.snapshot = UsageSnapshot()
    return _local.snapshot


def reset() -> None:
    """Start tracking a new task on the current thread."""
    _local.snapshot = UsageSnapshot()


def record(usage: Any, model_name: str = "") -> None:
    """
    Accumulate one LLM call's usage onto the current thread's snapshot.

    `usage` is whatever the provider SDK returns on `response.usage` (Groq and
    OpenAI both expose `.prompt_tokens`/`.completion_tokens`/`.total_tokens`).
    Silently no-ops if usage is None or missing those attributes, since the
    caller shouldn't have to know whether a provider returned usage data.
    """
    if usage is None:
        return
    snapshot = _state()
    snapshot.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
    snapshot.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
    snapshot.total_tokens += getattr(usage, "total_tokens", 0) or 0
    snapshot.call_count += 1
    if model_name:
        snapshot.models.append(model_name)


def snapshot() -> UsageSnapshot:
    """Read back the current thread's accumulated usage without resetting it."""
    current = _state()
    return UsageSnapshot(
        prompt_tokens=current.prompt_tokens,
        completion_tokens=current.completion_tokens,
        total_tokens=current.total_tokens,
        call_count=current.call_count,
        models=list(current.models),
    )


__all__ = ["UsageSnapshot", "reset", "record", "snapshot"]
