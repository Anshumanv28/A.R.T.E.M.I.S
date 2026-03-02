"""
System context for the agent: collections, RAG options, and metadata loaded from the tool registry.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from artemis.utils import get_logger

from artemis.agent.tools.registry import ToolRegistry

logger = get_logger(__name__)

__all__ = ["SystemContext", "load_system_context"]


@dataclass
class SystemContext:
    """Snapshot of system state (collections, RAG options, etc.) loaded at startup or refresh."""

    collections: List[str] = field(default_factory=list)
    collection_info: Dict[str, Any] = field(default_factory=dict)
    search_modes: List[str] = field(default_factory=lambda: ["semantic"])
    chunk_strategies: List[str] = field(default_factory=list)
    csv_schemas: List[str] = field(default_factory=list)
    agent_names: List[str] = field(default_factory=list)
    loaded_at: str = ""


def load_system_context(registry: ToolRegistry) -> SystemContext:
    """
    Populate system context by calling registry tools. Never raises; partial context on any failure.
    """
    collections: List[str] = []
    collection_info: Dict[str, Any] = {}
    search_modes: List[str] = ["semantic"]
    chunk_strategies: List[str] = []
    csv_schemas: List[str] = []

    try:
        raw = registry.get("list_collections").callable()
        if isinstance(raw, dict) and "collections" in raw:
            collections = raw["collections"] if isinstance(raw["collections"], list) else []
        elif isinstance(raw, list):
            collections = raw
        else:
            collections = []
            logger.warning("list_collections did not return a list or dict with 'collections'; using empty collections")
    except KeyError as e:
        logger.warning("list_collections not registered: %s", e)
    except Exception as e:
        logger.warning("Failed to load collections: %s", e, exc_info=False)

    for c in collections:
        try:
            info = registry.get("get_collection_info").callable(collection_name=c)
            collection_info[c] = info if isinstance(info, dict) else {}
        except KeyError as e:
            logger.warning("get_collection_info not registered: %s", e)
            collection_info[c] = {}
        except Exception as e:
            logger.warning("Failed to get collection info for %r: %s", c, e, exc_info=False)
            collection_info[c] = {}

    try:
        opts = registry.get("get_rag_options").callable()
        if isinstance(opts, dict):
            if "search_modes" in opts and isinstance(opts["search_modes"], list):
                search_modes = opts["search_modes"]
            if "chunk_strategies" in opts and isinstance(opts["chunk_strategies"], list):
                chunk_strategies = opts["chunk_strategies"]
            if "csv_schemas" in opts and isinstance(opts["csv_schemas"], list):
                csv_schemas = opts["csv_schemas"]
    except KeyError as e:
        logger.warning("get_rag_options not registered: %s", e)
    except Exception as e:
        logger.warning("Failed to load RAG options: %s", e, exc_info=False)

    loaded_at = datetime.utcnow().isoformat()

    return SystemContext(
        collections=collections,
        collection_info=collection_info,
        search_modes=search_modes,
        chunk_strategies=chunk_strategies,
        csv_schemas=csv_schemas,
        agent_names=[],
        loaded_at=loaded_at,
    )
