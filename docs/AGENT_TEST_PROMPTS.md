# Agent test prompts: multi-collection and smart ingest

**Multi-collection is the default.** The agent uses `artemis_system_docs` (system/docs/RAG context) and `artemis_user_docs` (user data). If you never ingest into the system collection, behavior is the same as a single collection; when you do, the agent uses it as a context booster. Use `--single-collection` only when you want to pin everything to one collection (legacy).

## Run command

From the project root, with `.env` set (e.g. `GROQ_API_KEY` or `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`):

```bash
# Interactive (default: multi-collection)
python -m artemis.agent.run
```

Single-query (one shot):

```bash
python -m artemis.agent.run "Ingest all markdown files in the docs folder using the best options for the data."
```

To use a single collection for all ingest/search (legacy):

```bash
python -m artemis.agent.run --single-collection --collection artemis_documents
```

Use a real path that exists on your machine, e.g. `docs` or `examples` or an absolute path.

---

## Example prompts

### 1. Suggestions only (no ingest)

- **"What are the best options for ingesting the docs folder? Don't ingest, just suggest."**  
  Expect: `suggest_ingest_options(path="docs")`, then the agent answers with the recommended file_extension, chunk_strategy, chunk_size, overlap and reasoning—no ingest call.

- **"Suggest settings for ingesting README.md. I don't want to ingest yet."**  
  Expect: `suggest_ingest_options(path="README.md")`, then a summary of the recommended options.

### 2. Smart ingest (suggest options then ingest)

- **"Ingest the files in the docs directory. Use whatever chunking and options work best for that content."**  
  Expect: agent calls `suggest_ingest_options(path="docs")`, then `ingest_directory` with the returned `file_extension`, `chunk_strategy`, `chunk_size`, `overlap`.

- **"Add the markdown files in examples to the knowledge base with the best settings for that data."**  
  Expect: `suggest_ingest_options` for that path, then ingest with suggested options.

- **"Ingest README.md with the right strategy for markdown."**  
  Expect: `suggest_ingest_options(path="README.md")`, then `ingest_file` with suggested options.

### 3. Multi-collection (system vs user)

- **"What search modes and chunk strategies are available?"**  
  Expect: `get_rag_options` (and possibly search in `artemis_system_docs` if RAG docs are ingested there).

- **"Search the knowledge base for how RAG chunking works."**  
  Expect: `search_documents` with `collection_name: "artemis_system_docs"` if the agent treats it as system knowledge.

- After ingesting your own docs: **"Search my documents for project goals."**  
  Expect: `search_documents` with `collection_name: "artemis_user_docs"`.

### 4. Combined flow

1. **"Ingest the docs folder using the best options for the data."**  
   → `suggest_ingest_options("docs")` then `ingest_directory` with suggested options into `artemis_user_docs`.

2. **"What did you use for chunking and why?"**  
   → Answer from prior tool results (reasoning from suggest_ingest_options).

3. **"Search the docs you just ingested for 'architecture'."**  
   → `search_documents(query="architecture", collection_name="artemis_user_docs")`.

---

## Queries to test retrieval (after ingesting docs)

Use these **after** you’ve ingested the `docs` folder (e.g. into `artemis_system_docs`) to see if the agent uses the ingested content to answer. The agent should call `search_documents` with `collection_name: "artemis_system_docs"` and then answer from the retrieved chunks.

**Architecture & flow**
- *How does the A.R.T.E.M.I.S agent decide when to use a tool versus answer directly?*
- *What is the agent graph flow? Describe planner, tool execution, and direct answer.*
- *What nodes does the agent have and how do they connect?*

**RAG & chunking**
- *What chunking strategies are available in this system and when should I use each?*
- *How do I add a custom chunker or extend the RAG pipeline?*
- *What’s the difference between semantic, fixed_overlap, and agentic chunking according to the docs?*

**Search & retrieval**
- *What search modes (semantic, keyword, hybrid) does the retriever support and when to use which?*
- *How can I filter search results by metadata?*
- *How do I ingest PDFs for RAG in this project?*

**Testing & setup**
- *What do the testing docs say about adding test data or running agent tests?*
- *How do I set up the agent with Groq or OpenAI according to the quickstart?*

If answers cite specific doc content (e.g. file names, section names, or exact phrasing from the docs), retrieval is working. If answers are generic and don’t reference the ingested docs, try rephrasing or asking for “according to the documentation” / “based on the system docs”.

---

## Paths that usually exist in-repo

- `docs` – markdown docs
- `examples` – example files
- `README.md` – single file
- `tests/test_data/markdown/` – sample markdown

Adjust paths if your layout differs. Use absolute paths if the agent runs from a different cwd.
