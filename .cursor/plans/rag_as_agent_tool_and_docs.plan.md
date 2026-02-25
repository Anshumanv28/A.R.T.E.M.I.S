---
name: RAG as agent tool and docs
overview: Document the RAG system for standalone and agent use, and expose full RAG operations (retrieve, ingest, collection management) as callable tools so the agent can do everything a user can do. Add docs under docs/ for how to use the RAG system.
todos: []
isProject: false
---

# RAG system: agent tool readiness and documentation

## Current state

- **Standalone RAG**: Anyone can use [artemis.rag](artemis/rag/__init__.py) to ingest data (`Indexer` + `ingest_file`) and retrieve (`Retriever.retrieve()`). Works without the agent.
- **Agent**: [AgentGraph](artemis/agent/graph.py) takes a `Retriever`; the [planner](artemis/agent/nodes/planner.py) classifies intent (rag vs direct); [rag_node](artemis/agent/nodes/rag_node.py) uses that retriever to fetch docs and synthesize an answer. So RAG is already used by the agent, but as a **fixed path** (planner to rag_node), not as callable tools.
- **Collection management**: [artemis/rag/core/collection_manager.py](artemis/rag/core/collection_manager.py) provides list_collections, get_collection_info, create_collection, clear_collection, delete_collection. Users can do all of this; the agent currently cannot.

What's missing: (1) clear docs for standalone and agent use, (2) callable RAG tools so the agent can retrieve, ingest, and manage collections the same way a user can.

---

## 1. Add RAG usage documentation

Add **docs/RAG_USAGE.md** and link it from [docs/README.md](docs/README.md).

**Sections:**

- **Overview** – RAG = ingest any supported data (CSV, PDF, DOCX, MD, TEXT) into a vector store and retrieve by semantic (or keyword/hybrid) search. Same pipeline works standalone and inside the agent.
- **Prerequisites** – Qdrant (local or cloud), env vars QDRANT_URL / QDRANT_API_KEY. Python: artemis.rag and dependencies per requirements.txt.
- **Standalone use** – Create Indexer, ingest_file, create Retriever, retrieve(). Point to ARCHITECTURE_FLOW.md and examples.
- **Using RAG with the agent** – Same Indexer/Retriever for ingestion and for the agent; pass retriever into run_agent or AgentGraph; planner routes to RAG when needed.
- **RAG tools for the agent** – List all tools (search, ingest, list_collections, get_collection_info, create_collection, clear_collection, delete_collection). How to bind them in a tool-calling node. Safety: clear/delete require confirm; document that the app should set confirm only after user approval.

**Link from docs index:** In docs/README.md, add under Project documentation: **[RAG usage](RAG_USAGE.md)** – How to use the RAG system standalone and with the agent, including all RAG tools.

---

## 2. Expose full RAG as agent-callable tools

Users can do everything with RAG via [artemis/rag/core/collection_manager.py](artemis/rag/core/collection_manager.py) (list, create, get info, clear, delete collections) plus Indexer + ingest_file (ingest) and Retriever (retrieve). Expose the same operations as callable tools so the agent can do them too.

**Place:** Add **artemis/rag/tools.py** and export from [artemis/rag/__init__.py](artemis/rag/__init__.py). Each tool is a thin wrapper around existing APIs for use in a future tool-calling node.

**Tools to add:**

| Tool | Wraps | Signature |
|------|--------|-----------|
| **Search** | Retriever.retrieve | create_rag_search_tool(retriever, k=5) returns (query: str) -> list[dict] |
| **Ingest** | ingest_file + Indexer | create_rag_ingest_tool(indexer) returns (path: str, file_type: str) -> dict; map string to FileType |
| **List collections** | collection_manager.list_collections | callable () -> list[str] (uses env for Qdrant) |
| **Get collection info** | collection_manager.get_collection_info | callable (collection_name: str) -> dict |
| **Create collection** | collection_manager.create_collection | callable (collection_name: str, embedding_dim?: int) -> bool |
| **Clear collection** | collection_manager.clear_collection | callable (collection_name: str, confirm: bool) -> bool |
| **Delete collection** | collection_manager.delete_collection | callable (collection_name: str, confirm: bool) -> bool |

**Safety:** Clear and delete already require confirm=True in collection_manager. Tool wrappers pass through a confirm argument so the agent only succeeds when the app sets it after user approval. Document this in RAG_USAGE.md.

**Use in agent:** Current graph unchanged; rag_node keeps using the injected retriever. These tools are for when you add a tool-calling node: register them so the agent can search, ingest, and manage collections.

---

## 3. Summary

| Item | Action |
|------|--------|
| Docs | Add docs/RAG_USAGE.md (overview, prerequisites, standalone, agent, full RAG tools including ingest and collection management). Link from docs/README.md. |
| RAG tools | Add artemis/rag/tools.py with: search, ingest, list_collections, get_collection_info, create_collection, clear_collection, delete_collection. Each wraps collection_manager or Indexer/ingest_file/Retriever. Destructive ops require confirm. Export from artemis/rag/__init__.py. |
| Agent graph | No change; rag_node keeps using the injected retriever. Tools are ready for a future tool-calling node. |

Result: the agent can do everything a user can do with RAG (retrieve, ingest, list/create/get/clear/delete collections), via the same APIs, exposed as callable tools; plus documentation on how to use the RAG system and how to bind these tools safely.
