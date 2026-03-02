# Postman – ARTEMIS API

Import these into Postman to call the ARTEMIS HTTP API.

## Import

1. **Collection:** In Postman, **Import** → choose `ARTEMIS_API.postman_collection.json`.
2. **Environment:** **Import** → choose `ARTEMIS.postman_environment.json`.
3. In the top-right environment dropdown, select **ARTEMIS Local**.

## Contents

- **ARTEMIS Local** environment:
  - `base_url`: `http://localhost:8000` (change if you use a different host/port, e.g. `ARTEMIS_API_PORT=9000` → `http://localhost:9000`).
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
