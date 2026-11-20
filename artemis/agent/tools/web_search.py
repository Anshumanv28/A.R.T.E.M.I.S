"""
Web search tool via Tavily (https://tavily.com) -- built for LLM agents,
returns clean {title, url, content, score} results instead of raw HTML/SERPs.
"""

from typing import Any, Dict, List

import requests

from artemis.agent.tools.registry import ToolRegistry
from artemis.utils import get_logger

logger = get_logger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
DEFAULT_MAX_RESULTS = 5


def web_search(
    query: str,
    api_key: str,
    max_results: int = DEFAULT_MAX_RESULTS,
    timeout: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Search the public web via Tavily.

    Returns a list of {title, url, content, score} on success, or a single
    {"error": "..."} entry on failure (network error, bad key, rate limit) --
    same error-shape convention as search_documents.
    """
    try:
        response = requests.post(
            TAVILY_SEARCH_URL,
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logger.warning(f"Tavily search failed for query='{query[:50]}...': {e}")
        return [{"error": f"Web search failed: {e}"}]

    results = data.get("results", []) or []
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score"),
        }
        for r in results[:max_results]
    ]


def register_web_search_tool(
    registry: ToolRegistry,
    api_key: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> None:
    """Register the web_search tool, bound to the given Tavily API key."""

    def web_search_kw(**kwargs):
        q = kwargs.get("query", "")
        k = int(kwargs.get("max_results", max_results))
        return web_search(q, api_key=api_key, max_results=k)

    registry.register(
        "web_search",
        web_search_kw,
        description="Search the public web for current events, recent news, or facts not already in the knowledge base. Returns a list of {title, url, content, score}.",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": max_results,
                },
            },
            "required": ["query"],
        },
    )


__all__ = ["web_search", "register_web_search_tool", "DEFAULT_MAX_RESULTS"]
