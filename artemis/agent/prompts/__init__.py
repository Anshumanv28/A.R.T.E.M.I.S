"""
Agent system prompts: load from files under this directory.

Keeps planner and direct-answer prompts separate from node code and makes them
easy to edit and version. Use load_planner_prompt() and load_direct_answer_prompt().

Prompt classes for supervisor and specialized agents: BasePrompt, SupervisorPrompt,
RAGSearchPrompt, IngestionPrompt, CollectionManagementPrompt.
"""

from pathlib import Path
from typing import Any, Dict

from artemis.agent.prompts.base import BasePrompt
from artemis.agent.prompts.supervisor import SupervisorPrompt
from artemis.agent.prompts.rag_agent import RAGSearchPrompt
from artemis.agent.prompts.ingestion_agent import IngestionPrompt
from artemis.agent.prompts.collection_agent import CollectionManagementPrompt

_PROMPTS_DIR = Path(__file__).parent


def _read_prompt(name: str) -> str:
    path = _PROMPTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def load_planner_prompt(
    tools_blob: str,
    rag_options: str,
    current_collection_line: str,
    max_tool_steps: int,
) -> str:
    """
    Load the planner system prompt and fill in dynamic placeholders.

    Placeholders: {{tools_blob}}, {{rag_options}}, {{current_collection_line}}, {{max_tool_steps}}.
    """
    template = _read_prompt("planner_system.md")
    return template.replace("{{tools_blob}}", tools_blob).replace(
        "{{rag_options}}", rag_options
    ).replace("{{current_collection_line}}", current_collection_line).replace(
        "{{max_tool_steps}}", str(max_tool_steps)
    )


def load_direct_answer_prompt(with_context: bool) -> str:
    """
    Load the direct-answer system prompt (with or without tool context).
    """
    name = "direct_answer_with_context.md" if with_context else "direct_answer_no_context.md"
    return _read_prompt(name)


__all__ = [
    "BasePrompt",
    "SupervisorPrompt",
    "RAGSearchPrompt",
    "IngestionPrompt",
    "CollectionManagementPrompt",
    "load_planner_prompt",
    "load_direct_answer_prompt",
]
