# A.R.T.E.M.I.S. Examples

Runnable demos and scripts for RAG, agents, and ingestion.

## Scripts

- **agent_demo.py** – LangGraph agent demo
- **comprehensive_test.py** – Comprehensive pipeline test
- **pdf_rag_example.py** – Interactive PDF RAG walkthrough
- **pdf_rag_quick_test.py** – Quick PDF RAG check
- **query_demo.py** – Query demo for ingested restaurant data (run after ingestion)
- **techcorp_docs_demo.py** – Ingest and query TechCorp-style markdown docs (expects `RAG_demo/techcorp_docs/`)
- **travel_converter_example.py** – Travel CSV schema converter example

## Templates

See **templates/** for boilerplate code (chunkers, converters, retrieval strategies, metadata extractors).

## Documentation

Detailed guides live in the **docs** folder:

- [PDF RAG guide](../docs/examples/README_PDF_RAG.md)
- [Travel converter guide](../docs/examples/README_travel_example.md)
- [Templates guide](../docs/examples/templates_README.md)

Run examples from the **project root**, e.g.:

```bash
python examples/query_demo.py
python examples/techcorp_docs_demo.py
python examples/pdf_rag_example.py
```
