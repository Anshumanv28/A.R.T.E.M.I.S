# Agent architecture: ReAct-style planner–executor

The A.R.T.E.M.I.S agent follows a **ReAct-style** (Reasoning + Acting) design: a planner chooses whether to use a tool or answer directly, and a single tool-execution loop runs any registered tool and feeds results back to the planner. This matches patterns used in LangGraph-style systems and Plan-and-Execute hybrids.

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

For how to use RAG with this agent (search, ingest, collections), see [RAG usage](RAG_USAGE.md).
