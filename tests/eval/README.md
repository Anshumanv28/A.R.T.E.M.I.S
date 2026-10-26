# Agent eval golden dataset

`golden_dataset.json` reuses the example queries from `docs/AGENT_TEST_PROMPTS.md`
(the repo's own author-written expected-tool-behavior cases) rather than inventing
new ones. Run it with `scripts/eval_agent.py`.

## Disposable Qdrant only

Two cases are genuinely **mutating**: `smart_ingest_readme_file` and
`combined_flow_ingest_docs_dir` actually call `ingest_file`/`ingest_directory`
against the real collections (`artemis_system_docs`/`artemis_user_docs` --
`run.py`'s collection names are hardcoded constants, not parameterized per run).

- For a quick/safe check against any Qdrant instance (including one with real
  data you care about), pass `--skip-mutating`.
- Run the **full** suite (including the mutating cases) only against a
  disposable Qdrant instance -- e.g. the `docker-compose.yml` Qdrant profile,
  or a fresh `artemis-qdrant` container you're fine wiping. Never run the full
  suite against production data.

## Usage

```bash
python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json --skip-mutating
python scripts/eval_agent.py --dataset tests/eval/golden_dataset.json --provider openai --model gpt-4o-mini
```

Each run prints a console summary and writes a timestamped JSON report under
`eval_reports/`. Re-run after any planner/prompt change and diff the reports'
`task_success_rate` / `failure_breakdown` to catch regressions -- that's the
harness's ongoing value, not just a one-shot demo.
