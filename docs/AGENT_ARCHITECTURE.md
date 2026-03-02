# Agent architecture: ReAct-style planner–executor

The A.R.T.E.M.I.S agent follows a **ReAct-style** (Reasoning + Acting) design: a planner chooses whether to use a tool or answer directly, and a single tool-execution loop runs any registered tool and feeds results back to the planner. This matches patterns used in LangGraph-style systems and Plan-and-Execute hybrids.

## Flow from user prompt to answer

### V2 (Supervisor + sub-agents, `--v2`)

1. **Entry**  
   User types a query.  
   - **Interactive:** `main()` already has a `Supervisor` and calls `supervisor.invoke(query, message_history)`.  
   - **Single-shot:** `run_agent_v2(query)` builds a `Supervisor` (with `system_context=None`), then `supervisor.invoke(query)`.

2. **Routing (Supervisor)**  
   `Supervisor.invoke()` calls `_route(query)`:
   - **First time only:** Accessing `self.system_context` triggers `_ensure_system_context()` → `load_system_context(registry)` (calls `list_collections`, `get_collection_info` per collection, `get_rag_options`). Result is cached.
   - Build routing prompt: agent names/descriptions + `system_context.collections`.
   - **LLM call** (lightweight): “Route this query to one of: direct, rag_search, ingestion, collection_management.” Response is parsed to get `agent_name`.

3. **Branch**
   - **If `agent_name == "direct"`:** Build minimal `AgentState`, call `direct_answer_node(state, config)` → one **LLM call** with direct-answer prompt (no tools) → `final_answer` → return to caller.
   - **Else:** `_get_agent(agent_name)` — if that sub-agent isn’t built yet, build and cache it (only the one that was routed to). Then `sub.invoke(query, message_history)`.

4. **Sub-agent run (e.g. rag_search, ingestion, collection_management)**  
   Sub-agent is a **ReAct graph** (same shape as V1): planner ↔ tool_node ↔ direct_answer.
   - **Initial state:** `query`, `message_history`, empty `tool_calls`, `step_count=0`.
   - **Planner node:** LLM sees that sub-agent’s system prompt (tools, collections, rules) + query + prior tool results. Returns JSON: `intent` ("tool" or "direct"), and if tool: `tool_name`, `tool_args`.
   - **If intent == "direct":** Go to **direct_answer** node → one LLM call to synthesize from query + `tool_calls_summary` and formatted tool results → set `final_answer` → **END**.
   - **If intent == "tool":** Go to **tool_node** → `registry.get(tool_name).callable(**tool_args)` (e.g. `search_documents`, `ingest_directory`). Append to `tool_calls`, increment `step_count`, build `tool_calls_summary`. Then:
     - If `step_count >= max_tool_steps` → go to **direct_answer** (cap).
     - Else → back to **planner** (loop with new tool results).
   - When the graph hits **direct_answer** and produces `final_answer`, the sub-agent returns that state to the Supervisor.

5. **Return**  
   Supervisor adds `routed_to: agent_name` to the state and returns.  
   `main()` (or `run_agent_v2`) gets `final_answer`, `tool_calls`, `routed_to`, etc., and prints the answer.

So per prompt in V2: **one routing LLM call**, then either **one direct-answer LLM call** (if routed to direct) or **one or more planner + tool_node + direct_answer steps** inside the chosen sub-agent (each step: planner LLM → optional tool run → eventually direct_answer LLM).

### V1 (single ReAct graph, no `--v2`)

1. **Entry**  
   `run_agent(query, ...)` builds or uses a registry, then builds one `AgentGraph` (planner + tool_node + direct_answer) and calls `agent.invoke(query)`.

2. **Single ReAct loop**  
   Same graph as a sub-agent, but with the **full** tool list and the **planner_system.md** prompt (all tools, RAG options, system/self-awareness rules).
   - **Planner** → intent + (optional) tool_name/tool_args.
   - **If direct** → direct_answer node → final_answer → END.
   - **If tool** → tool_node runs the tool, then back to planner (or to direct_answer if step limit).
   - Repeat until planner returns direct or step limit.

3. **Return**  
   State with `final_answer`, `tool_calls`, etc. is returned and printed.

So per prompt in V1: **one or more** planner LLM calls, interleaved with tool runs, then **one** direct_answer LLM call.

## High-level flow

1. **Planner** – Receives the user query and a list of available tools from the **tool registry**. It outputs:
   - `intent`: `"tool"` or `"direct"`
   - If `"tool"`: `tool_name` and `tool_args` (e.g. `search_documents` with `{"query": "..."}`)
   - If `"direct"`: the agent will answer without calling another tool (possibly using prior tool results)

2. **Tool node** – When the planner chose `"tool"`, the tool node runs `registry.get(tool_name).callable(**tool_args)`, appends the result (with an `ok` flag) to `tool_calls`, increments `step_count`, and returns state to the **planner** again.

3. **Direct-answer node** – When the planner chooses `"direct"`, the direct-answer node uses the query and a **pre-summarized** view of `tool_calls` (and any retrieved documents) to synthesize the final reply. It does not receive a raw dump of all tool output; the state field `tool_calls_summary` (and formatted tool results) keeps the prompt focused.

4. **Step limit** – To avoid infinite loops, the agent caps the number of tool steps (e.g. 10). Once the limit is reached, the graph routes to the direct-answer node so the run always terminates.

## Tool registry as source of truth

- **Central registry** – All tools (RAG search, ingest, collection management, or future tools) are registered in a single `ToolRegistry` with:
  - `name`, `description`, optional `parameters_schema` (for the LLM)
  - `callable(**kwargs)` for execution

- **Planner** – Only sees `registry.list_tools()` (names and descriptions). It never sees callables.

- **Tool node** – Dispatches by name: `registry.get(tool_name).callable(**tool_args)`.

- **RAG is “just a tool”** – There is no dedicated RAG path. When the planner decides the user needs to search the knowledge base, it selects the `search_documents` tool. The same loop runs for ingest, list collections, or any other registered tool. This keeps the agent extensible and avoids hard-coding retrieval.

## Alignment with common patterns

- **LangGraph** – The graph is a state machine with a planner node, a tool node, and a direct-answer node; conditional edges implement the planner → tool vs direct routing and the tool → planner loop. The registry mirrors LangGraph-style tool/skill registries.

- **Plan-and-Execute** – The planner effectively “plans” one step at a time (choose tool or answer); the tool node “executes” that step and returns to the planner. Multiple tool steps correspond to multiple plan–execute iterations.

- **ReAct** – The loop of “reason about what to do → act (call a tool) → observe result → reason again” is implemented by planner → tool_node → planner, with the LLM in the planner seeing prior tool results and choosing the next intent.

## Configuration and extensibility

- **Max tool steps** – Configurable (e.g. `AgentConfig.max_tool_steps`). The planner prompt is told the limit so it can move to direct when appropriate; the graph can also short-circuit from the tool node to direct-answer when the limit is reached.

- **Planner output contract** – The planner response is validated against a strict JSON schema. On parse failure, the agent falls back to `intent="direct"` so the graph always makes progress.

- **Tool result shape** – Each entry in `tool_calls` includes `ok: bool` so the planner can distinguish “no data” from “tool crashed” and decide to retry or answer with what it has.

- **DSPy** – The registry design (name + callable + optional schema) is compatible with using DSPy modules as callable implementations later (e.g. `dspy_rag(**tool_args)`), which fits DSPy’s recommended integration with larger agent systems.

- **RAG options from registries** – Search modes and chunk strategies offered to the agent are derived from the RAG registries (`RETRIEVAL_STRATEGIES`, `CHUNKERS`, `CSV_CONVERTERS`). Adding a new strategy in code and registering it (e.g. `@register_strategy`, `@register_chunker`) makes it visible to the agent after restart, with no change to the agent or tool-registry code. A manual override is possible to restrict or replace what the agent sees. See [RAG customization – Adding new strategies](RAG_CUSTOMIZATION.md#5-adding-new-strategies-automatic-vs-manual).

For how to use RAG with this agent (search, ingest, collections), see [RAG usage](RAG_USAGE.md).
