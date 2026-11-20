"""
API-key authentication and per-tenant collection-management scoping.

Auth: ARTEMIS_API_KEYS maps API keys to tenant ids. When unset (local dev,
the existing demo flow), auth is disabled and every request is treated as
the single "default" tenant -- no behavior change for anyone not opting in.

Tenant isolation covers collection *management* (list/get/create/clear/
delete), which talks to Qdrant directly by collection name regardless of
deployment mode (see artemis/rag/tools.py) -- a tenant can list, create,
inspect, clear, or delete only its own namespaced collections, because the
underlying Qdrant collection name differs.

It deliberately does NOT cover search_documents/ingest_file/ingest_directory:
those are bound to a fixed Retriever/Indexer (or a fixed multi_collection
dict keyed by literal names like "artemis_system_docs") wired once at app
startup, not a per-tenant collection chosen per request. Namespacing
collection_name for those tools would either be silently ignored (single-
collection mode) or break the multi_collection lookup (dict keys wouldn't
match the prefixed name). Real tenant isolation of the retrieval/ingestion
path needs per-tenant indexer/retriever provisioning, which is future work.
"""

import os
import time
from typing import Dict, Optional

from fastapi import HTTPException, Request

from artemis.agent.tools.registry import ToolRegistry
from artemis.utils import get_logger

logger = get_logger(__name__)

DEFAULT_TENANT_ID = "default"
TENANT_SEP = "__"

# Collection-management tools that talk to Qdrant directly by name (safe to
# namespace); search/ingest tools are intentionally excluded -- see module docstring.
_SCOPED_TOOL_NAMES = {
    "list_collections",
    "get_collection_info",
    "create_collection",
    "clear_collection",
    "delete_collection",
}


def parse_api_keys() -> Dict[str, str]:
    """
    Parse ARTEMIS_API_KEYS="key1:tenant1,key2:tenant2" into {key: tenant_id}.

    Empty/unset -> {} (auth disabled). Re-read on every call rather than
    cached at import time, so tests (and config reloads) can change it.
    """
    raw = os.environ.get("ARTEMIS_API_KEYS", "").strip()
    if not raw:
        return {}
    keys: Dict[str, str] = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            logger.warning("Ignoring malformed ARTEMIS_API_KEYS entry (expected key:tenant_id): %r", entry)
            continue
        key, tenant_id = entry.split(":", 1)
        key, tenant_id = key.strip(), tenant_id.strip()
        if key and tenant_id:
            keys[key] = tenant_id
    return keys


def _extract_api_key(request: Request) -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return request.headers.get("X-API-Key", "").strip() or None


async def require_api_key(request: Request) -> str:
    """
    FastAPI dependency: returns the caller's tenant_id.

    Raises 401 if ARTEMIS_API_KEYS is configured and the request's key is
    missing or unrecognized. If ARTEMIS_API_KEYS is unset, auth is disabled
    and every caller is the single DEFAULT_TENANT_ID.
    """
    configured_keys = parse_api_keys()
    if not configured_keys:
        return DEFAULT_TENANT_ID

    api_key = _extract_api_key(request)
    if not api_key or api_key not in configured_keys:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key. Pass it as 'Authorization: Bearer <key>' or 'X-API-Key: <key>'.",
        )
    return configured_keys[api_key]


def _scoped_name(tenant_id: str, collection_name: Optional[str]) -> str:
    logical_name = (collection_name or "default").strip() or "default"
    return f"{tenant_id}{TENANT_SEP}{logical_name}"


def _unscoped_name(tenant_id: str, scoped_name: str) -> Optional[str]:
    prefix = f"{tenant_id}{TENANT_SEP}"
    return scoped_name[len(prefix):] if scoped_name.startswith(prefix) else None


def scope_registry_to_tenant(registry: ToolRegistry, tenant_id: str) -> ToolRegistry:
    """
    Return a new ToolRegistry where collection-management tools operate only
    on `tenant_id`'s own namespaced collections (see module docstring for
    which tools and why). All other tools pass through unchanged.
    """
    scoped = ToolRegistry()
    for meta in registry.list_tools():
        name = meta["name"]
        descriptor = registry.get(name)
        if name == "list_collections":
            fn = _wrap_list_collections(descriptor.callable, tenant_id)
        elif name in _SCOPED_TOOL_NAMES:
            fn = _wrap_collection_name_arg(descriptor.callable, tenant_id)
        else:
            fn = descriptor.callable
        scoped.register(name, fn, descriptor.description, descriptor.parameters_schema)
    return scoped


def _wrap_collection_name_arg(fn, tenant_id: str):
    def wrapped(**kwargs):
        kwargs = dict(kwargs)
        kwargs["collection_name"] = _scoped_name(tenant_id, kwargs.get("collection_name"))
        return fn(**kwargs)

    return wrapped


def _wrap_list_collections(fn, tenant_id: str):
    def wrapped(**kwargs):
        result = fn(**kwargs)
        if not isinstance(result, dict):
            return result
        names = result.get("collections", []) or []
        purposes = result.get("purposes", {}) or {}
        own_names = []
        own_purposes = {}
        for scoped_name in names:
            logical_name = _unscoped_name(tenant_id, scoped_name)
            if logical_name is None:
                continue
            own_names.append(logical_name)
            if scoped_name in purposes:
                own_purposes[logical_name] = purposes[scoped_name]
        return {"collections": own_names, "purposes": own_purposes}

    return wrapped


class RateLimiter:
    """
    Fixed-window per-tenant rate limiter, in-process only (not shared across
    multiple API workers/instances -- fine for this project's single-process
    deployment; a real multi-instance deployment would need a shared store
    like Redis instead).
    """

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: Dict[str, list] = {}

    def check(self, tenant_id: str) -> None:
        """Record one hit for tenant_id; raise 429 if it exceeds the window's limit."""
        now = time.monotonic()
        hits = [t for t in self._hits.get(tenant_id, []) if now - t < self.window_seconds]
        if len(hits) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {self.max_requests} requests per {self.window_seconds:.0f}s.",
            )
        hits.append(now)
        self._hits[tenant_id] = hits


def build_rate_limiter() -> RateLimiter:
    max_requests = int(os.environ.get("ARTEMIS_RATE_LIMIT_PER_MINUTE", "30"))
    return RateLimiter(max_requests=max_requests, window_seconds=60.0)


__all__ = [
    "DEFAULT_TENANT_ID",
    "parse_api_keys",
    "require_api_key",
    "scope_registry_to_tenant",
    "RateLimiter",
    "build_rate_limiter",
]
