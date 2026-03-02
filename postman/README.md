# Postman – ARTEMIS API

Import these into Postman to call the ARTEMIS HTTP API.

## Import

1. **Collection:** In Postman, **Import** → choose `ARTEMIS_API.postman_collection.json`.
2. **Environments:** **Import** both:
   - `ARTEMIS.postman_environment.json` (**ARTEMIS Local**)
   - `ARTEMIS_DEMO.postman_environment.json` (**ARTEMIS Demo (EC2)**)
3. In the top-right environment dropdown, select **ARTEMIS Local** (local dev) or **ARTEMIS Demo (EC2)** (deployed).

## Recommended sharing method (repo-native)

For a dev-focused repo, the most reliable way to share Postman assets is to keep the exported JSON files in version control (this folder). It avoids workspace permission issues and keeps changes reviewable in PRs.

Optional hosted Postman docs (may change): [Postman workspace request docs](https://planetary-desert-315596.postman.co/workspace/My-Workspace~070a057c-0089-4b38-8434-707e445eb7b7/request/32894704-e64db534-5b65-4245-81f8-4624e7326966?action=share&creator=32894704&ctx=documentation&active-environment=32894704-b4ddc88a-8114-40eb-81f0-0ddee0104976)

## Contents

- **ARTEMIS Local** environment:
  - `base_url`: `http://localhost:8000` (change if you use a different host/port, e.g. `ARTEMIS_API_PORT=9000` → `http://localhost:9000`).
  - `query`: default query text used in the “Query (single turn)” request.

- **ARTEMIS Demo (EC2)** environment:
  - `base_url`: `http://54.87.62.83:8000` (your current deployed demo base URL).
  - `query`: default query text used in the “Query (single turn)” request.

- **ARTEMIS API** collection:
  - **Health** – `GET /health`
  - **Query (single turn)** – `POST /query` with `{{query}}` and `message_history: null`
  - **Query (multi-turn)** – `POST /query` with a sample `message_history`
  - **Query - What can you do?** – example single-turn request
  - **Query - Tell me about ARTEMIS** – example single-turn request

## Run the API first

```bash
python -m artemis.api
# or: uvicorn artemis.api:app --host 0.0.0.0 --port 8000
```

Then run **Health**; if it returns 200, run any **Query** request.
