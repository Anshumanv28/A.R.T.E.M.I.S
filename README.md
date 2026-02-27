# A.R.T.E.M.I.S. 🏹

**Adaptive Retrieval & Tool-Enabled Multimodal Intelligence System**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **A multi-agent RAG system that routes natural language queries to specialist agents — search your knowledge base, ingest documents, and manage collections, all via a single interface.**

---

## What is A.R.T.E.M.I.S.?

A.R.T.E.M.I.S. is a **Supervisor-based multi-agent RAG framework** built on LangGraph. It takes a user query, classifies it with a lightweight LLM call, and dispatches it to the right specialist agent — each with its own focused toolset and system prompt.

**Three specialist agents, one Supervisor:**

```
User query
│
▼
Supervisor ──── single LLM classification call
│
├──► rag_search     → semantic search across knowledge base
├──► ingestion      → ingest documents, URLs, text
├──► collection_mgmt → create / delete / list Qdrant collections
└──► direct         → answer directly, no tools needed
```

Each sub-agent runs its own **ReAct loop** (plan → tool → plan → answer) with only the tools it needs — keeping reasoning tight and costs low.

**Extensible by design** — add a new agent (browser, web search, SQL) with one function call:

```python
supervisor.register_agent("web_search", build_web_search_agent(...), "Search the web")
```

---

## What's built

### RAG layer

- ✅ **File ingestion** — CSV, PDF, DOCX, Markdown, plain text
- ✅ **Chunking strategies** — fixed, fixed_overlap, csv_row, semantic, agentic (LLM-driven)
- ✅ **Retrieval** — semantic vector search via Qdrant (keyword/hybrid: planned)
- ✅ **Multi-collection** — agent routes between artemis_system_docs and artemis_user_docs by task
- ✅ **CSV schema converters** — RESTAURANT, TRAVEL schemas

### Agent layer (v2)

- ✅ **Supervisor** — lightweight LLM router, no tool loop, classifies and dispatches
- ✅ **SubAgentGraph** — reusable ReAct sub-agent base class, filtered registry per agent
- ✅ **SystemContext** — live Qdrant collection metadata injected into each agent's prompt
- ✅ **run_agent_v2()** — Supervisor entrypoint, backwards-compatible with v1
- ✅ **--v2 CLI flag** — opt-in to Supervisor architecture

### Also included

- ✅ **Legacy v1 agent** (AgentGraph, run_agent) — still works, not removed
- ✅ **Per-agent prompt classes** (RAGSearchPrompt, IngestionPrompt, CollectionManagementPrompt, SupervisorPrompt)

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/Anshumanv28/A.R.T.E.M.I.S.git
cd A.R.T.E.M.I.S
pip install -e .

# 2. Set environment variables
cp .env.example .env
# Edit .env with your keys (see Configuration below)

# 3. Run the agent (v2 — Supervisor architecture)
python -m artemis.agent.run --v2

# Or single query
python -m artemis.agent.run "What does the document say about X?" --v2
```

---

## Configuration

Create a `.env` file in the project root:

```env
# LLM — at least one required
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key   # alternative to Groq

# Qdrant — required
QDRANT_URL=your-qdrant-url
QDRANT_API_KEY=your-qdrant-api-key
```

**Getting Qdrant credentials:**

- **Cloud (recommended):** sign up at [cloud.qdrant.io](https://cloud.qdrant.io), create a free cluster, copy the URL + API key
- **Local:** `docker run -p 6333:6333 qdrant/qdrant` then use `QDRANT_URL=http://localhost:6333`

---

## Usage

### Run with Supervisor (v2 — recommended)

```python
from artemis.agent import run_agent_v2

result = run_agent_v2("What does the document say about onboarding?")
print(result["final_answer"])
print(f"Routed to: {result['routed_to']}")   # e.g. "rag_search"
```

### Run with legacy agent (v1)

```python
from artemis.agent import run_agent

result = run_agent("What does the document say about onboarding?")
print(result["final_answer"])
```

### Ingest documents

```python
from artemis.rag import Indexer, FileType, ingest_file, DocumentSchema

indexer = Indexer(collection_name="artemis_user_docs")
ingest_file("manual.pdf", FileType.PDF, indexer)
ingest_file("restaurants.csv", FileType.CSV, indexer, schema=DocumentSchema.RESTAURANT)
```

### Search directly

```python
from artemis.rag import Retriever, RetrievalMode, Indexer

indexer = Indexer(collection_name="artemis_user_docs")
retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
results = retriever.retrieve("Italian restaurants in Mumbai", k=5)
```

---

## Architecture

### Supervisor flow (v2)

```
run_agent_v2(query)
    │
    ├─ build ToolRegistry (all RAG tools)
    ├─ load SystemContext (live Qdrant metadata)
    │
    └─ Supervisor.invoke(query)
            │
            ├─ _route(): single LLM call → JSON {"agent": "rag_search"}
            │
            └─ agents[agent_name].invoke(query)
                    │
                    └─ SubAgentGraph (filtered registry + focused prompt)
                            │
                            planner ──► tool_node ──► planner ──► ...
                                                              └──► direct_answer
```

---

## Project structure

```
artemis/
├── agent/
│   ├── supervisor.py          # Supervisor: classify + dispatch
│   ├── context.py             # SystemContext + load_system_context()
│   ├── agents/
│   │   ├── base.py            # SubAgentGraph + _filter_registry()
│   │   ├── rag_agent.py       # build_rag_agent()
│   │   ├── ingestion_agent.py # build_ingestion_agent()
│   │   └── collection_agent.py# build_collection_agent()
│   ├── graph.py               # AgentGraph (v1, legacy)
│   ├── run.py                 # run_agent(), run_agent_v2(), CLI
│   └── prompts/               # Per-agent prompt classes
└── rag/
    ├── core/                  # Indexer, Retriever, Embedder
    └── ingestion/
        ├── chunkers/          # fixed, semantic, agentic, csv_row...
        ├── loaders/           # PDF, DOCX, MD, CSV loaders
        └── converters/        # CSV schema converters
```

---

## Roadmap

- Integration tests for Supervisor + sub-agents
- Structure-aware chunking strategy (see #4)
- Web search sub-agent
- Keyword + hybrid retrieval (BM25)
- REST API (FastAPI)
- Conversation memory / multi-turn support

---

## Contributing

Contributions are welcome. Check the open issues — there are several good first issue entries that don't require deep codebase knowledge.

```bash
git clone https://github.com/Anshumanv28/A.R.T.E.M.I.S.git
cd A.R.T.E.M.I.S
pip install -e .
pytest tests/
```

See CONTRIBUTING.md once it's added (tracked in #2).

---

## Tech stack

| Layer | Tool |
|-------|------|
| Agent orchestration | LangGraph |
| LLM providers | Groq · OpenAI |
| Vector database | Qdrant |
| Embeddings | Sentence Transformers |
| Code style | Black |

---

## License

MIT — see [LICENSE](LICENSE).

---

**Made with 🏹 by [Anshuman](https://github.com/Anshumanv28)**
