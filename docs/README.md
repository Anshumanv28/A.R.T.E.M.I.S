# A.R.T.E.M.I.S. Documentation

Documentation index for the A.R.T.E.M.I.S. project.

## Project documentation

- **[Architecture Flow](ARCHITECTURE_FLOW.md)** – System architecture and data flow
- **[Agent architecture](AGENT_ARCHITECTURE.md)** – ReAct-style planner–executor, tool registry, no dedicated RAG node (RAG via tools)
- **[Agent quick start](AGENT_QUICKSTART.md)** – Run the agent, multi-collection default, CLI, state shape
- **[Agent test prompts](AGENT_TEST_PROMPTS.md)** – Example prompts and queries to test retrieval after ingesting docs
- **[RAG usage](RAG_USAGE.md)** – RAG standalone and with the agent (search, ingest, suggest_ingest_options, multi-collection)
- **[RAG customization](RAG_CUSTOMIZATION.md)** – RAG parameters, chunk/retrieval options, and **adding new strategies** (automatic registry-driven vs manual override)
- **[Roadmap](ROADMAP.md)** – Project roadmap and milestones (if present)

## Examples

- **[PDF RAG Guide](examples/README_PDF_RAG.md)** – Integrate PDFs into the RAG system
- **[Travel converter guide](examples/README_travel_example.md)** – Document converters and CSV schemas
- **[Templates](examples/templates_README.md)** – Template files for custom components

## Testing

- **[Test suite](testing/README.md)** – Running tests and test overview
- **[What to add](testing/WHAT_TO_ADD.md)** – Test files to add
- **[Data requirements](testing/DATA_REQUIREMENTS.md)** – Required datasets for tests
- **[Test files requirements](testing/TEST_FILES_REQUIREMENTS.md)** – Sample file specifications
- **[Test data README](testing/test_data_README.md)** – Test data directory overview
- **[Test data setup](testing/TEST_DATA_SETUP.md)** – Test data setup guide

## Other docs (referenced from main README)

The main [README](../README.md) may reference additional guides (e.g. Quick Start, Setup Guide, Extending A.R.T.E.M.I.S.). Those can be added under `docs/` as they are created.
