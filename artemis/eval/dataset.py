"""
Golden dataset loading: plain JSON (the repo has zero YAML dependency).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union


@dataclass
class EvalCase:
    """
    One golden-dataset case, matching tests/eval/golden_dataset.json.

    expected_tool_sequence: tool names expected to appear, in order, as a
        (not necessarily contiguous) subsequence of the actual tool calls --
        a flexible check since planner wording and intermediate steps vary.
    forbidden_tools: none of these may appear anywhere in the actual tool calls.
    mutating: True for cases that call real ingest_file/ingest_directory
        (or other write tools) -- these must only run against a disposable Qdrant.
    """

    id: str
    query: str
    expected_agent: str
    expected_tool_sequence: List[str] = field(default_factory=list)
    forbidden_tools: List[str] = field(default_factory=list)
    assert_no_error: bool = True
    mutating: bool = False


def load_dataset(path: Union[str, Path]) -> List[EvalCase]:
    """Load and validate a golden dataset JSON file into a list of EvalCase."""
    with open(path, "r", encoding="utf-8") as f:
        raw: List[Dict[str, Any]] = json.load(f)
    cases = [
        EvalCase(
            id=entry["id"],
            query=entry["query"],
            expected_agent=entry["expected_agent"],
            expected_tool_sequence=entry.get("expected_tool_sequence", []),
            forbidden_tools=entry.get("forbidden_tools", []),
            assert_no_error=entry.get("assert_no_error", True),
            mutating=entry.get("mutating", False),
        )
        for entry in raw
    ]
    seen_ids = set()
    for case in cases:
        if case.id in seen_ids:
            raise ValueError(f"Duplicate eval case id in dataset: {case.id!r}")
        seen_ids.add(case.id)
    return cases


__all__ = ["EvalCase", "load_dataset"]
