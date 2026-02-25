"""
Central tool registry for the agent.

Tools are registered by name with a callable and optional JSON schema.
The planner receives list_tools(); the tool node invokes via get(name).callable(**kwargs).
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDescriptor:
    """
    Descriptor for a single tool.

    Attributes:
        name: Tool name (used by planner and tool_node).
        description: Short description for the planner prompt.
        parameters_schema: Optional JSON Schema for the tool's arguments (for LLM tool definitions).
        callable: Function to invoke; must accept **kwargs matching tool_args from the planner.
    """
    name: str
    description: str
    parameters_schema: Optional[Dict[str, Any]] = None
    callable: Callable[..., Any] = None  # type: ignore[assignment]


class ToolRegistry:
    """
    Registry of tools available to the agent.

    - register(): add a tool by name (raises if name already registered).
    - list_tools(): return list of {name, description, parameters_schema} for planner (no callable).
    - get(name): return ToolDescriptor for invocation.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDescriptor] = {}

    def register(
        self,
        name: str,
        callable_fn: Callable[..., Any],
        description: str,
        parameters_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a tool by name.

        Args:
            name: Unique tool name.
            callable_fn: Function to call; will be invoked with **tool_args.
            description: Short description for the planner.
            parameters_schema: Optional JSON Schema for arguments.

        Raises:
            ValueError: If name is already registered.
        """
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = ToolDescriptor(
            name=name,
            description=description,
            parameters_schema=parameters_schema,
            callable=callable_fn,
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        Return tool metadata for the planner (no callables).

        Returns:
            List of dicts with keys: name, description, parameters_schema (optional).
        """
        return [
            {
                "name": d.name,
                "description": d.description,
                "parameters_schema": d.parameters_schema,
            }
            for d in self._tools.values()
        ]

    def get(self, name: str) -> ToolDescriptor:
        """
        Get the descriptor for a tool by name.

        Args:
            name: Tool name.

        Returns:
            ToolDescriptor with callable.

        Raises:
            KeyError: If tool is not registered.
        """
        if name not in self._tools:
            raise KeyError(f"Tool not registered: {name}")
        return self._tools[name]
