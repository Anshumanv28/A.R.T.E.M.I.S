"""
HTTP API for ARTEMIS: same config and agent as the CLI, separate entrypoint.
"""

import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from artemis.auth import (
    DEFAULT_TENANT_ID,
    TenantRagRegistryCache,
    build_rate_limiter,
    parse_api_keys,
    require_api_key,
    scope_registry_to_tenant,
)
from artemis.utils import get_logger

logger = get_logger(__name__)


def _resolve_registry(request: Request, tenant_id: str):
    """
    The tenant's full RAG registry (own collections for search/ingest when
    tenant_id is a real tenant; the shared global registry unchanged for
    DEFAULT_TENANT_ID), with collection-management tools namespaced on top.
    """
    cache = getattr(request.app.state, "tenant_rag_cache", None)
    base_registry = (
        cache.get(tenant_id, request.app.state.registry)
        if cache is not None
        else request.app.state.registry
    )
    return scope_registry_to_tenant(base_registry, tenant_id)


class QueryBody(BaseModel):
    """Request body for POST /query."""

    query: str = Field(..., min_length=1, description="User query")
    message_history: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Optional multi-turn history: list of {role: 'user'|'assistant', content: '...'}",
    )


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Build v2 runtime at startup; store on app.state."""
    try:
        from artemis.agent.run import get_v2_runtime

        config, registry = get_v2_runtime()
        app.state.config = config
        app.state.registry = registry
        app.state.rate_limiter = build_rate_limiter()
        app.state.tenant_rag_cache = TenantRagRegistryCache(config)
        app.state.ready = True
        app.state.ready_reason = None
        if parse_api_keys():
            logger.info("API startup: config and registry ready (API key auth enabled)")
        else:
            logger.warning(
                "API startup: config and registry ready (ARTEMIS_API_KEYS not set -- "
                "auth is disabled, all requests run as the single default tenant)"
            )
    except Exception as e:
        logger.exception("API startup failed: %s", e)
        app.state.ready = False
        app.state.ready_reason = str(e)
    yield
    # shutdown: nothing to tear down


app = FastAPI(
    title="ARTEMIS API",
    description="Query the ARTEMIS agent (Supervisor v2). Same config as CLI (env vars).",
    lifespan=_lifespan,
)

# CORS: localhost dev (Vite default) always allowed; production frontend origins
# (e.g. a Vercel deployment) come from ARTEMIS_CORS_ORIGINS since that URL isn't
# known until the frontend is first deployed.
_default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_extra_origins = os.environ.get("ARTEMIS_CORS_ORIGINS", "")
_allow_origins = _default_origins + [o.strip() for o in _extra_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    allow_credentials=False,
)


@app.get("/health")
async def health(request: Request):
    """Return 200 if runtime is ready; optionally verify Qdrant. Else 503."""
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": reason},
        )
    # Optional: ping Qdrant via list_collections
    try:
        descriptor = request.app.state.registry.get("list_collections")
        descriptor.callable()
    except Exception as e:
        logger.warning("Health check: list_collections failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "reason": f"Qdrant unreachable: {e!s}"},
        )
    return {"status": "ok"}


@app.get("/status")
async def status(request: Request, tenant_id: str = Depends(require_api_key)):
    """Richer dashboard status: readiness, configured LLM provider/model, Qdrant reachability.

    provider/model_name reflect what's configured, not a verified-reachable LLM --
    GroqClient/OpenAIClient have no ping method, and a real check would cost a paid call.
    """
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "reason": reason,
                "provider": None,
                "model_name": None,
                "qdrant_reachable": False,
                "qdrant_error": None,
            },
        )
    config = request.app.state.config
    qdrant_reachable = True
    qdrant_error = None
    try:
        request.app.state.registry.get("list_collections").callable()
    except Exception as e:
        qdrant_reachable = False
        qdrant_error = str(e)
    return {
        "ready": True,
        "reason": None,
        "provider": config.provider,
        "model_name": config.model_name,
        "qdrant_reachable": qdrant_reachable,
        "qdrant_error": qdrant_error,
    }


@app.get("/collections")
async def collections(request: Request, tenant_id: str = Depends(require_api_key)):
    """List Qdrant collections with their recorded purpose, for the dashboard."""
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(status_code=503, content={"error": reason, "collections": []})
    try:
        registry = _resolve_registry(request, tenant_id)
        result = registry.get("list_collections").callable()
        purposes = result.get("purposes", {})
        return {
            "collections": [
                {"name": name, "purpose": purposes.get(name)}
                for name in result.get("collections", [])
            ]
        }
    except Exception as e:
        logger.exception("Collections list failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e), "collections": []})


@app.get("/collections/{name}")
async def collection_detail(name: str, request: Request, tenant_id: str = Depends(require_api_key)):
    """Per-collection detail (points, vector config, segments) for the dashboard."""
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(status_code=503, content={"error": reason})
    try:
        registry = _resolve_registry(request, tenant_id)
        return registry.get("get_collection_info").callable(collection_name=name)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        logger.exception("Collection detail failed for %s: %s", name, e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/eval/latest")
async def eval_latest(request: Request, tenant_id: str = Depends(require_api_key)):
    """Most recent eval report from eval_reports/ (written by scripts/eval_agent.py), trimmed for the dashboard.

    No reports yet is a normal first-run state, not a server error: 404 with
    metrics/cases null/empty rather than 500, so the dashboard can render an
    "nothing run yet" empty state instead of an error banner.
    """
    from artemis.eval.report import DEFAULT_REPORTS_DIR

    reports_dir = Path(DEFAULT_REPORTS_DIR)
    report_files = sorted(reports_dir.glob("eval_report_*.json")) if reports_dir.is_dir() else []
    if not report_files:
        return JSONResponse(
            status_code=404,
            content={
                "error": "No eval reports found. Run scripts/eval_agent.py first.",
                "report_file": None,
                "generated_at": None,
                "metrics": None,
                "cases": [],
            },
        )
    # Filenames are eval_report_<UTC timestamp>.json, so lexicographic sort is chronological.
    latest_path = report_files[-1]
    try:
        with open(latest_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        logger.exception("Failed to read eval report %s: %s", latest_path, e)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "report_file": latest_path.name, "generated_at": None, "metrics": None, "cases": []},
        )

    cases = [
        {
            "case_id": r.get("case_id"),
            "success": r.get("success"),
            "failure_reason": r.get("failure_reason"),
            "expected_agent": r.get("expected_agent"),
            "actual_agent": r.get("actual_agent"),
            "duration_s": r.get("duration_s"),
        }
        for r in report.get("results", [])
    ]
    return {
        "report_file": latest_path.name,
        "generated_at": report.get("generated_at"),
        "metrics": report.get("metrics"),
        "cases": cases,
    }


@app.post("/query")
async def query(request: Request, body: QueryBody, tenant_id: str = Depends(require_api_key)):
    """Run the agent on the given query; optional message_history for multi-turn."""
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(
            status_code=503,
            content={"error": reason, "final_answer": None, "routed_to": None},
        )
    rate_limiter = getattr(request.app.state, "rate_limiter", None)
    if rate_limiter is not None:
        rate_limiter.check(tenant_id)
    try:
        from artemis.agent.llm import usage_tracker
        from artemis.agent.run import run_agent_v2
        from artemis.eval.pricing import estimate_cost

        config = request.app.state.config
        registry = _resolve_registry(request, tenant_id)
        usage_tracker.reset()
        start = time.perf_counter()
        result = run_agent_v2(
            body.query,
            config=config,
            registry=registry,
            message_history=body.message_history,
        )
        total_latency_ms = (time.perf_counter() - start) * 1000
        usage = usage_tracker.snapshot()
        cost_usd = estimate_cost(config.model_name, usage.prompt_tokens, usage.completion_tokens)

        return {
            "final_answer": result.get("final_answer"),
            "routed_to": result.get("routed_to"),
            "error": result.get("error"),
            "tool_calls": result.get("tool_calls"),
            "metrics": {
                "total_latency_ms": round(total_latency_ms, 2),
                "routing_latency_ms": result.get("routing_latency_ms"),
                "agent_latency_ms": result.get("agent_latency_ms"),
                "provider": config.provider,
                "model_name": config.model_name,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "llm_call_count": usage.call_count,
                "cost_usd": cost_usd,
            },
        }
    except Exception as e:
        logger.exception("Query failed: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "final_answer": None,
                "routed_to": None,
            },
        )
