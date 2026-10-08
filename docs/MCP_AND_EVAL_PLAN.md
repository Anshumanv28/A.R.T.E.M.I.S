# A.R.T.E.M.I.S: MCP Server + Agent Evaluation Harness

## Context

The user is pivoting their job search toward "AI Engineer (Agentic AI/RAG)" roles. Market research (three real JDs: Kitron India, Flatworld Solutions, Volga Partners) showed the two most consistently-demanded skills their existing portfolio doesn't yet prove are **MCP server development** ("expose client systems to agents in a secure, reusable way", "least-privilege tool access") and **agent evaluation & tracing** ("task success rate, tool-selection accuracy, step count, cost per task, failure analysis on real traces"). A.R.T.E.M.I.S (their own multi-agent RAG project, already on their resume/GitHub) is the natural place to build real, working proof-of-work for both — not toy scripts.

Both features are genuinely new (verified: zero existing MCP code, zero existing eval harness anywhere in the repo) and are designed to reuse the existing `ToolRegistry`/`Supervisor`/sub-agent architecture rather than bolt on a separate system.

## Feature 1 — MCP Server

**Expose the existing `ToolRegistry` dynamically**, not as 11 hand-duplicated tools. `ToolDescriptor{name, description, parameters_schema, callable}` (`artemis/agent/tools/registry.py`) already maps 1:1 onto MCP's `Tool{name, description, inputSchema}` + call-handler model.

**Least-privilege scopes reuse the existing allow-lists verbatim** — `RAG_AGENT_TOOLS` (`artemis/agent/agents/rag_agent.py`), `INGESTION_AGENT_TOOLS` (`.../ingestion_agent.py`), `COLLECTION_AGENT_TOOLS` (`.../collection_agent.py`) — filtered via `_filter_registry()` (`artemis/agent/agents/base.py`), imported directly: the codebase already imports this cross-module (`rag_agent.py` does `from artemis.agent.agents.base import SubAgentGraph, _filter_registry`), so this isn't introducing a new pattern. Default scope is `rag_search` (the only one with zero mutating tools); `collection_management` (has `delete_collection`/`clear_collection`) must be explicitly requested.

**Transport: stdio first.** It's self-contained, needs zero changes to `artemis/api/__init__.py`, and is what real MCP clients (Claude Desktop, Cursor, MCP Inspector) actually connect to for a demo. Streamable HTTP mounted on the existing FastAPI app is a nice-to-have follow-up, not part of this build — it has a real wrinkle (the MCP ASGI app would need to read `request.app.state.registry` at request time since the registry is only built inside FastAPI's `_lifespan`) and depends on confirming the exact `mcp` 1.25.0 SDK API, which isn't installed/importable in the current environment and needs `pip install -e .` first.

### New files
- `artemis/mcp/__init__.py` — exports `build_server`, `MCP_SCOPES`.
- `artemis/mcp/scopes.py` — imports the three allow-lists above into `MCP_SCOPES = {"rag_search": RAG_AGENT_TOOLS, "ingestion": INGESTION_AGENT_TOOLS, "collection_management": COLLECTION_AGENT_TOOLS, "full": None}`, `DEFAULT_SCOPE = "rag_search"`.
- `artemis/mcp/adapter.py` — `descriptor_to_mcp_tool(descriptor) -> mcp.types.Tool` (translates `parameters_schema` → `inputSchema`); `call_tool_safely(registry, name, arguments) -> list[mcp.types.TextContent]` (catches `KeyError`/`Exception`, serializes non-str results via `json.dumps(result, default=str, indent=2)`).
- `artemis/mcp/server.py` — `build_server(registry, name="artemis") -> mcp.server.Server` using the low-level `Server` class with `@server.list_tools()`/`@server.call_tool()` handlers (data-driven over the registry, matching the repo's plain-function style rather than FastMCP's per-function decorators); `async def run_stdio(registry)` wrapping `mcp.server.stdio.stdio_server()`.
- `artemis/mcp/__main__.py` — `python -m artemis.mcp --scope rag_search`, reuses `artemis.agent.run.get_v2_runtime()` to build the registry (no duplicated construction logic), filters by scope, runs stdio.

### Minimal touch point
- `pyproject.toml` — add `"mcp>=1.25.0"` to `dependencies` (already resolves under this exact name as a transitive entry in `requirements.lock`; just needs to be a direct dependency).
- No other existing file changes for the stdio path.

### Verification
1. `pip install -e .` to pull in `mcp`; then confirm the real 1.25.0 API surface (`python -c "import mcp.server; help(mcp.server)"`) before finalizing `server.py`'s exact calls — this wasn't importable/verifiable in this planning session.
2. `npx @modelcontextprotocol/inspector python -m artemis.mcp --scope rag_search` (needs real `QDRANT_URL`/`QDRANT_API_KEY`/`GROQ_API_KEY`) → "List Tools" should show exactly `search_documents`, `list_collections`, `get_collection_info`, `get_rag_options`. "Call Tool" → `search_documents({"query": "test"})` → returns content, no error.
3. Negative test: attempt `delete_collection` while scoped to `rag_search` → expect `"Unknown tool: delete_collection"`, proving scope filtering actually removes it rather than just hiding it from the list.
4. Claude Desktop config for a real demo screenshot:
   ```json
   { "mcpServers": { "artemis-rag": {
       "command": "python", "args": ["-m", "artemis.mcp", "--scope", "rag_search"],
       "env": { "QDRANT_URL": "...", "QDRANT_API_KEY": "...", "GROQ_API_KEY": "..." }
   } } }
   ```

## Feature 2 — Agent Evaluation Harness

Computes real metrics against **live** Supervisor runs (not mocks) — deliberately filling the gap `tests/README.md` states explicitly ("no live end-to-end integration tests yet").

**Cost-per-task requires a small additive fix first.** Verified: neither `GroqClient.generate()` nor `OpenAIClient.generate()` (`artemis/agent/llm/{groq_client,openai_client}.py`) captures `response.usage` — both discard it. Both are also reconstructed fresh per LLM call (in `planner_node`, `direct_answer_node`, `Supervisor._get_llm_client()`), so a plain instance attribute wouldn't survive across a task's multiple calls. Fix: a tiny thread-local accumulator (`artemis/agent/llm/usage_tracker.py`: `reset()`, `record(usage)`, `snapshot()`), with one additive line in each client right after the `.create()` call: `usage_tracker.record(response.usage)`. No signature or behavior change to `generate()`.

**Pricing is explicit and honest, not guessed.** `artemis/eval/pricing.py` holds a documented `MODEL_PRICING_USD_PER_1K` dict. Verified today: Groq's `llama-3.3-70b-versatile` (this repo's own default model) moved to enterprise-only "Contact Sales" pricing on 2026-08-26 — no public self-serve rate anymore. `estimate_cost()` returns `None` (reported as `"pricing_unavailable"`) for unpriced models rather than fabricating a number. The demo/README should run against `gpt-4o-mini` ($0.15/$0.60 per 1M tokens) to get real dollar figures.

**Golden dataset reuses `docs/AGENT_TEST_PROMPTS.md`** (the repo's own author already wrote ~15 example queries with documented expected tool behavior) rather than inventing cases from scratch. Plain JSON (repo has zero YAML dependency), at `tests/eval/golden_dataset.json`:
```json
{"id": "suggest_ingest_docs_no_ingest", "query": "What are the best options for ingesting the docs folder? Don't ingest, just suggest.",
 "expected_agent": "ingestion", "expected_tool_sequence": ["suggest_ingest_options"],
 "forbidden_tools": ["ingest_file", "ingest_directory"], "assert_no_error": true}
```
At least 6 entries total, 2 of which (`smart_ingest_readme_file`, `combined_flow_ingest_docs_dir`) are genuinely **mutating** (call real `ingest_file`/`ingest_directory`). `run.py`'s collection names (`SYSTEM_DOCS_COLLECTION`/`USER_COLLECTION`) are hardcoded constants, not parameterized — so the harness supports `--skip-mutating` to exclude these, and the README instructs running the full suite only against a disposable Qdrant, never production data.

**Failure taxonomy accounts for a real, verified subtlety in `Supervisor.invoke()`:** if a sub-agent's `.invoke()` raises, the exception is swallowed and replaced with a direct answer (`artemis/agent/supervisor.py:227-236`) — but `routed_to` still reports the *original intended* agent, with `reasoning` hardcoded to the literal string `"Direct answer — no tools needed."`. A naive harness would misread this as "the planner chose not to use tools" rather than "the sub-agent crashed." `classify_failure()` checks for this exact signature (`routed_to` in expected set + empty `tool_calls` + that literal `reasoning` string) as `"likely_silent_subagent_fallback"`, distinct from a legitimate no-tool-needed case.

### New files
- `artemis/agent/llm/usage_tracker.py` — thread-local token accumulator (see above).
- `artemis/eval/__init__.py`, `artemis/eval/dataset.py` (`EvalCase` dataclass + `load_dataset()`), `artemis/eval/pricing.py`, `artemis/eval/runner.py` (`CaseResult` dataclass, `run_case()`, `classify_failure()`, `run_suite()`), `artemis/eval/metrics.py` (`SuiteMetrics` dataclass, `compute_metrics()`), `artemis/eval/report.py` (`write_json_report()`, `print_human_summary()`).
- `scripts/eval_agent.py` — CLI entrypoint matching the existing `scripts/manage_collections.py` style: `python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json [--skip-mutating] [--provider groq|openai] [--model NAME]`.
- `tests/eval/__init__.py`, `tests/eval/golden_dataset.json`, `tests/eval/README.md` (documents the disposable-Qdrant requirement for mutating cases).

### Minimal touch points
- `artemis/agent/llm/groq_client.py`, `artemis/agent/llm/openai_client.py` — one additive line each (`usage_tracker.record(response.usage)`).

### Verification
1. `python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json --skip-mutating` against a disposable Qdrant → console summary (success rate, routing accuracy, tool-selection accuracy, avg step count, total tokens/cost, failure breakdown) + a timestamped JSON report under `eval_reports/`.
2. Re-run after any planner/prompt change; diff the JSON reports' `task_success_rate`/`failure_breakdown` to catch regressions — this is the harness's actual ongoing value, not just a one-shot demo.
3. Full run including mutating cases only against the disposable Qdrant profile in `docker-compose.yml`.

**See also:** `docs/DASHBOARD_PLAN.md` Phase 2 plans to surface this feature's JSON reports (`eval_reports/`) in the dashboard UI via a `GET /eval/latest` endpoint — that work is blocked on this feature shipping first.

## Why this reads as real engineering, not a demo script
The MCP least-privilege scoping and the swallowed-exception failure category both come directly from reading and understanding the actual Supervisor/registry code — not generic eval boilerplate. That's the differentiator for a job application built around "I can read a real agent system and reason about its failure modes," which is exactly what the researched JDs ask for.

---
*Drafted 2026-10-07 in a planning session ahead of implementation. Status: not yet built — this is the design to execute against when ready.*
