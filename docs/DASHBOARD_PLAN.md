# A.R.T.E.M.I.S: Operations Dashboard

## Context

`ROADMAP.md` has long listed a "React dashboard for config/memory view" as a Phase 2 item, and `docs/MVP_AND_CONTRIBUTOR_PLAN.md` explicitly deferred it ("not required for 'deploy + contributor-friendly'"). This plan is the first concrete design for that item — scoped down from the originally-imagined config/memory editing UI to something narrower and immediately useful: a **read-only** view of system status and Qdrant collection state, built on top of the chat frontend added in the previous session.

This also continues the same job-search-driven motivation behind `docs/MCP_AND_EVAL_PLAN.md`: a live operational view (is the backend up, what's in the vector store, what did the last eval run show) is itself a demonstrable "agent observability" skill, not just a nice-to-have UI.

**Decided up front (not open questions):**
- **Read-only.** No create/delete/clear-collection buttons here — those stay chat-only via the existing `collection_mgmt` sub-agent. This keeps the dashboard free of destructive-action confirmation dialogs and means no new CORS methods are needed (`GET` is already allowed).
- **Auto-poll every ~15s, plus a manual refresh button.**
- Two phases: **Phase 1** (system status + collections, buildable now) and **Phase 2** (eval metrics, blocked on `docs/MCP_AND_EVAL_PLAN.md` Feature 2, which doesn't exist yet).

Everything cited below was verified against the current code, not assumed: `artemis/api/__init__.py` has exactly two routes today (`/health`, `/query`); `artemis/rag/core/collection_manager.py`'s `get_collection_info()` currently returns only `{name, points_count, vectors_count, status}`; `artemis/agent/tools/__init__.py`'s `list_coll()` closure already returns `{"collections": [...], "purposes": {...}}`, not a bare list; `artemis/agent/config.py`'s `AgentConfig` uses `provider`/`model_name` as its literal field names; `requirements.lock` pins `qdrant-client==1.16.2`. One thing is **not** verified — `qdrant-client` isn't installed in the planning environment, so the exact `CollectionInfo.config.params.vectors` field path is unconfirmed; flagged below, same honesty pattern `docs/MCP_AND_EVAL_PLAN.md` used for its own unverified `mcp` SDK surface.

## Feature 1 — Dashboard Phase 1: system status + collections

### Backend: three new GET routes in `artemis/api/__init__.py`

Follow this file's existing conventions exactly: readiness guard first (`getattr(request.app.state, "ready", False)`), dependencies pulled from `request.app.state.X` (no `Depends()` anywhere in this codebase), plain dict / `JSONResponse` returns (not Pydantic response models), `logger.exception(...)` + 500 on unexpected failure, and — importantly — route business logic through `registry.get(tool_name).callable()` rather than importing Qdrant directly, matching how `/health` already pings Qdrant via the `list_collections` tool.

**`GET /status`**
```python
@app.get("/status")
async def status(request: Request):
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(status_code=503, content={
            "ready": False, "reason": reason,
            "provider": None, "model_name": None,
            "qdrant_reachable": False, "qdrant_error": None,
        })
    config = request.app.state.config
    qdrant_reachable, qdrant_error = True, None
    try:
        request.app.state.registry.get("list_collections").callable()
    except Exception as e:
        qdrant_reachable, qdrant_error = False, str(e)
    return {
        "ready": True, "reason": None,
        "provider": config.provider, "model_name": config.model_name,
        "qdrant_reachable": qdrant_reachable, "qdrant_error": qdrant_error,
    }
```
`provider`/`model_name` are read straight off `app.state.config` (already built at startup, zero extra cost). **Caveat the doc must carry into the UI copy**: this reports the LLM as *configured*, not *reachable* — `GroqClient`/`OpenAIClient` (`artemis/agent/llm/{groq_client,openai_client}.py`) have no ping method, and a real reachability check would mean a paid completion call. Don't imply full LLM health.

`/health` stays unchanged — it's the minimal uptime-check endpoint and should keep that shape. `/status` is a richer, dashboard-shaped superset that happens to duplicate one `list_collections()` call; that's an accepted tradeoff over coupling the two response shapes together.

**`GET /collections`**
```python
@app.get("/collections")
async def collections(request: Request):
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(status_code=503, content={"error": reason, "collections": []})
    try:
        result = request.app.state.registry.get("list_collections").callable()
        purposes = result.get("purposes", {})
        return {"collections": [
            {"name": n, "purpose": purposes.get(n)} for n in result.get("collections", [])
        ]}
    except Exception as e:
        logger.exception("Collections list failed: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e), "collections": []})
```
The `list_collections` tool's callable (`list_coll()` in `artemis/agent/tools/__init__.py`) already returns `{"collections": [...names...], "purposes": {...}}` — this route reshapes that into `{"collections": [{"name", "purpose"}]}` for a friendlier list. That's a deliberate reshape, not a passthrough.

**`GET /collections/{name}`**
```python
@app.get("/collections/{name}")
async def collection_detail(name: str, request: Request):
    if not getattr(request.app.state, "ready", False):
        reason = getattr(request.app.state, "ready_reason", "startup failed")
        return JSONResponse(status_code=503, content={"error": reason})
    try:
        return request.app.state.registry.get("get_collection_info").callable(collection_name=name)
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        logger.exception("Collection detail failed for %s: %s", name, e)
        return JSONResponse(status_code=500, content={"error": str(e)})
```
`get_collection_info()` (`collection_manager.py`) already raises `ValueError` with a "does not exist" message for an unknown collection — this is the one route that needs a distinct 404 branch, since `/health` never has to make that distinction.

### Backend data enrichment: extend `get_collection_info()` in place

`artemis/rag/core/collection_manager.py`'s `get_collection_info()` today returns only `{name, points_count, vectors_count, status}` (and `vectors_count` is currently just a duplicate of `points_count`). The dashboard's "details" requirement needs richer fields — vector dimension, distance metric, segment count, optimizer status — which live on the same `qdrant_client.CollectionInfo` object this function already fetches via `client.get_collection(name)`, just not read today.

**Recommendation: extend the existing function additively**, don't add a parallel `get_collection_detail()`:
- New dict keys are backwards-compatible for every existing caller (the `get_collection_info` agent tool used by `collection_agent.py`), so chat-based "tell me about collection X" answers get richer for free, at no risk.
- Avoids duplicating the `client.get_collection()` call and the `config.params.vectors` parsing logic in two places.

```python
collection_info = client.get_collection(collection_name)
vectors_cfg = collection_info.config.params.vectors
if isinstance(vectors_cfg, dict):  # named multi-vector config (defensive; not used by this app today)
    vector_size = {k: v.size for k, v in vectors_cfg.items()}
    distance = {k: str(v.distance) for k, v in vectors_cfg.items()}
else:  # single unnamed VectorParams — how this app's own create_collection() always creates collections
    vector_size = vectors_cfg.size
    distance = str(vectors_cfg.distance)
info = {
    "name": collection_name,
    "points_count": collection_info.points_count,
    "vectors_count": collection_info.vectors_count if hasattr(collection_info, "vectors_count") else collection_info.points_count,
    "status": str(collection_info.status) if hasattr(collection_info, "status") else "unknown",
    "vector_size": vector_size,
    "distance": distance,
    "segments_count": getattr(collection_info, "segments_count", None),
    "optimizer_status": str(collection_info.optimizer_status) if hasattr(collection_info, "optimizer_status") else None,
}
```

**⚠️ Not yet verified**: `qdrant-client` isn't installed in the planning environment, so `collection_info.config.params.vectors`'s exact attribute path on `qdrant-client==1.16.2` is unconfirmed. Before implementing: `pip install -e .` and inspect a real `client.get_collection(...)` response (or check the pinned version's source/docs) to confirm these field names.

No other files need to change for Phase 1 — `artemis/rag/tools.py`, `artemis/agent/tools/__init__.py`, and `collection_agent.py` all just pass through whatever `get_collection_info()` returns. No CORS or `pyproject.toml` changes (GET-only, no new dependencies).

### Frontend: new `frontend/src/components/dashboard/` + a polling hook

- **`App.tsx`** — add a local `useState<"chat" | "dashboard">("chat")` tab switch in the header, rendering `<ChatPanel/>` or `<DashboardPanel/>` in `<main>`. No router exists in the frontend today (confirmed — no react-router/wouter dependency), so a tab-state variable is the lowest-friction fit; introducing a router would be premature for one extra view.
- **`DashboardPanel.tsx`** — owns two independent `usePolling` instances, one for `/status` and one for `/collections` (kept independent so a slow collections fetch never blocks the status badge from updating), a single manual "Refresh" button driving both, and renders `StatusCard`, `CollectionsList`, and a static `EvalPlaceholder`.
- **`StatusCard.tsx`** — ready/not-ready and Qdrant-reachable badges, reusing the exact `--success`/`--danger`/`--neutral` CSS variables `HealthBadge.tsx` already uses; shows provider + model_name text; shows `qdrant_error` when unreachable.
- **`CollectionsList.tsx`** — renders `{name, purpose}` rows; an explicit empty state when there are zero collections (not a blank area).
- **`CollectionDetailCard.tsx`** — fetches `/collections/{name}` **on demand**, only when a row is expanded/selected — deliberately *not* part of the 15s poll cycle, to avoid N extra Qdrant round-trips per tick as the collection count grows. Owns its own independent loading/error state.
- **`EvalPlaceholder.tsx`** — a single static card, no props, no fetch: "Eval metrics — coming soon", linking to `docs/MCP_AND_EVAL_PLAN.md` Feature 2. Deliberately dumb so Phase 1 doesn't speculatively build data plumbing for a report format that doesn't exist yet.
- **`frontend/src/hooks/usePolling.ts`** — new generic hook (the frontend has zero existing polling code — confirmed no `setInterval`/`setTimeout` anywhere in `frontend/src`). Mirrors `HealthBadge.tsx`'s existing mount-fetch + `cancelled`-flag-guard pattern, adding `setInterval`/`clearInterval` cleanup on unmount and an exposed `refresh()` for the manual button:
  ```ts
  function usePolling<T>(fetchFn: () => Promise<T>, intervalMs = 15000) {
    const [data, setData] = useState<T | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const refresh = useCallback(() => { /* fetch, cancellation-guarded, sets data/error/loading */ }, [fetchFn]);
    useEffect(() => {
      let cancelled = false;
      const tick = () => { if (!cancelled) refresh(); };
      tick();
      const id = setInterval(tick, intervalMs);
      return () => { cancelled = true; clearInterval(id); };
    }, [intervalMs]);
    return { data, error, loading, refresh };
  }
  ```
- **`frontend/src/api/client.ts`** — `getStatus()`, `getCollections()`, `getCollectionDetail(name)`, following the exact `fetch` → `ApiError` pattern `postQuery`/`getHealth` already use.
- **`frontend/src/api/types.ts`** — new interfaces matching the backend shapes exactly:
  ```ts
  export interface StatusResponse {
    ready: boolean; reason: string | null;
    provider: "groq" | "openai" | null; model_name: string | null;
    qdrant_reachable: boolean; qdrant_error: string | null;
  }
  export interface CollectionSummary { name: string; purpose: string | null; }
  export interface CollectionsResponse { collections: CollectionSummary[]; error?: string; }
  export interface CollectionDetailResponse {
    name: string; points_count: number; vectors_count: number; status: string;
    vector_size: number | Record<string, number>;
    distance: string | Record<string, string>;
    segments_count: number | null; optimizer_status: string | null; error?: string;
  }
  ```
- **`frontend/src/index.css`** — additive rules only: `.dashboard-panel`, `.status-card`, `.collections-list`, `.collection-row`, `.collection-detail-card`, `.tab-switch`. Reuse existing CSS variables (`--surface`, `--border`, `--success`, `--danger`, `--neutral`) — no new variables needed, so the existing two-block dark-mode pattern (`@media (prefers-color-scheme: dark)` + `:root[data-theme="dark"]`) stays untouched. Scope a wider `max-width` to `.dashboard-panel` specifically rather than loosening the global `.app` rule, so the chat layout doesn't shift.

### Verification

With the backend running and Qdrant up:
```bash
curl -s http://localhost:8000/status | python -m json.tool
# {"ready": true, "reason": null, "provider": "groq"|"openai", "model_name": "...", "qdrant_reachable": true, "qdrant_error": null}

curl -s http://localhost:8000/collections | python -m json.tool
# zero collections: {"collections": []}
# several:          {"collections": [{"name": "artemis_system_docs", "purpose": "..."}, ...]}

curl -s http://localhost:8000/collections/artemis_system_docs | python -m json.tool
# {"name", "points_count", "vectors_count", "status", "vector_size", "distance", "segments_count", "optimizer_status"}

curl -s http://localhost:8000/collections/does_not_exist
# HTTP 404, {"error": "Collection 'does_not_exist' does not exist in Qdrant..."}
```

With Qdrant down (stop the container / point `QDRANT_URL` at an unreachable host):
```bash
curl -s http://localhost:8000/status      # ready: true, qdrant_reachable: false, qdrant_error populated
curl -s http://localhost:8000/collections # HTTP 500, {"error": ..., "collections": []}
```

With the app itself not ready (e.g. unset `GROQ_API_KEY`/`OPENAI_API_KEY` so startup fails):
```bash
curl -s http://localhost:8000/status      # HTTP 503, {"ready": false, "reason": "...", ...}
```

Manual UI walkthrough (`npm run dev` in `frontend/`, backend running):
1. Click the "Dashboard" tab → `StatusCard` shows its badges within ~1s of mount, without waiting for the first 15s poll tick.
2. With zero collections → `CollectionsList` shows its empty state, not a blank area.
3. Ingest something via the chat tab, switch back → the new collection appears after the next poll tick or a manual Refresh click, without a full page reload.
4. Expand a collection row → `CollectionDetailCard` fetches on demand with its own independent spinner (confirms the detail fetch isn't tied to the 15s poll).
5. Stop Qdrant mid-session, wait for the next tick (or click Refresh) → the status badge flips to unreachable in place; the panel doesn't crash or go blank.
6. Toggle dark/light theme while the dashboard is open → cards re-theme correctly using only existing CSS vars.
7. Leave the dashboard tab open across 2+ poll intervals, switch to chat and back, check dev tools for leaked intervals — confirms `clearInterval` cleanup actually fires. This is the one genuinely new piece of frontend plumbing (no prior polling code in this repo to pattern-match against), so it's worth checking deliberately rather than assuming `useEffect` cleanup "just works."

## Feature 2 — Dashboard Phase 2: eval metrics (blocked, intentionally lighter-spec'd)

Fully blocked on `docs/MCP_AND_EVAL_PLAN.md` Feature 2 — confirmed `artemis/eval/` and `artemis/agent/llm/usage_tracker.py` don't exist yet. Once that plan ships and produces timestamped JSON reports under `eval_reports/` (the `SuiteMetrics` shape — task success rate, failure breakdown, tokens/cost), the natural addition here is:
- Backend: `GET /eval/latest` — reads the most recent file in `eval_reports/` (by filename timestamp or mtime) and returns its JSON verbatim or a trimmed subset.
- Frontend: replace `EvalPlaceholder.tsx` with a real fetch + a small metrics table/badges (success rate, cost, failure breakdown).

Deliberately not spec'd further — `SuiteMetrics`'s exact shape isn't locked yet, and guessing field names now would just mean rewriting this section once Feature 2 actually ships.

---
*Drafted 2026-10-08 ahead of implementation, following the user's chat frontend work in the same session. Status: not yet built — Phase 1 is ready to execute against; Phase 2 waits on `docs/MCP_AND_EVAL_PLAN.md` Feature 2.*
