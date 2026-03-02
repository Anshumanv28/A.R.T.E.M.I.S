# MVP + contributor plan (dev-focused)

**Goal:** Close deployment gaps and make the repo **obviously contributor-friendly** so more devs get involved on GitHub.

**Primary audience:** Developers who discover the repo, want to run it locally or deploy it, and potentially contribute (issues, PRs, docs).

---

## Principles

1. **Dev experience first** — Clone, install, run in under 5 minutes; docs and tooling support both “run locally” and “deploy.”
2. **Low-friction contribution** — CONTRIBUTING.md, good-first-issue labels, CI that runs on PRs, clear code layout.
3. **Deployment as an option** — HTTP API + health + Docker so the same codebase can be used as a service without blocking CLI-first usage.
4. **Transparency** — README and docs state what’s stable, what’s optional, and how to get help (e.g. Discussions, issues).

---

## Phase 1: Contributor-friendly base (do first)

*Makes the repo feel “open for contribution” and easy to try.*

| Item | Why it matters for devs |
|------|-------------------------|
| **CONTRIBUTING.md** | How to set up, run tests, open PRs, code style. Single place to point new contributors. |
| **.github/workflows** | `ci.yml`: run tests + lint on push/PR. Build confidence that PRs don’t break the suite. |
| **.github/ISSUE_TEMPLATE** | Bug report + feature request templates. Optional: “good first issue” template so you can label easy tasks. |
| **README badges** | e.g. “tests passing”, “Python 3.12”, “license”. Quick signal of health and stack. |
| **One-command run** | README already has `pip install -e .` + `.env` + `python -m artemis.agent.run --v2`. Add a “Run with Docker (Qdrant included)” option once Docker exists (Phase 2). |
| **.env.example completeness** | Ensure every required and optional env var is documented (already mostly there). Reduces “it doesn’t run” issues. |

**Outcome:** New visitors see tests, contribution path, and a clear “run locally” story.

---

## Phase 2: Deployment-ready surface

*Same codebase; add the minimal surface needed to run as a service.*

| Item | Why |
|------|-----|
| **Minimal HTTP API** | Single service entrypoint: e.g. `POST /query` (or `/chat`) calling `run_agent_v2`, returning `{ "final_answer", "routed_to", "error" }`. Optional: `message_history` for multi-turn. Keeps API small and easy to secure later. |
| **Health endpoint** | `GET /health`: process up, env present (LLM + Qdrant), optional Qdrant ping. Returns 200/503 so orchestrators can use it. |
| **Dockerfile** | Builds app image (install deps, no secrets in image). CMD runs API server (or CLI if you prefer script-only first). |
| **docker-compose (optional)** | App + Qdrant service so `docker-compose up` gives a working stack. Huge win for “try it in 5 minutes” and for contributors who don’t want to sign up for Qdrant Cloud. |

**Outcome:** Deployable as a container; contributors can also use Docker for local dev.

---

## Phase 3: Polish and “good first issues”

*Turn remaining work into discoverable, scoped tasks so contributors can pick them up.*

| Item | Why |
|------|-----|
| **Label “good first issue”** | Tag 5–10 small tasks (e.g. “Add request_id to API response”, “Document RAG env vars in README”, “Add a pytest for the health endpoint”). New contributors can filter by label. |
| **Short deployment doc** | `docs/DEPLOYMENT.md`: env vars, how to run with Docker, health check URL, optional cloud hints (e.g. Render, Fly, Cloud Run). Keeps README focused; deployment is one link away. |
| **Structured errors from API** | API returns consistent JSON errors (e.g. `{ "error": "message", "code": "config_error" }`) and appropriate status codes. Document in API section of README or DEPLOYMENT.md. |
| **No secrets in logs** | Quick audit: no API keys or tokens in log messages. Easy good-first-issue: “Add a log filter that redacts env vars.” |

**Outcome:** Clear list of ways to contribute; deployment is documented and consistent.

---

## Suggested order of work

1. **CONTRIBUTING.md** + **.github/workflows/ci.yml** (lint + pytest).  
2. **.env.example** pass + README badge line (tests, Python).  
3. **Minimal API** (FastAPI or Starlette): `POST /query`, `GET /health`.  
4. **Dockerfile** that runs the API (or CLI); then **docker-compose** with Qdrant.  
5. **docs/DEPLOYMENT.md** and optional **ISSUE_TEMPLATE** + “good first issue” labels.  
6. **Structured API errors** + “no secrets in logs” as issues or small PRs.

---

## What to avoid (for now)

- **Heavy auth** — API can be “dev-only” or behind a single API key; full OAuth/JWT can wait.  
- **React dashboard** — ROADMAP Phase 2; not required for “deploy + contributor-friendly.”  
- **Big refactors** — Prefer small, additive changes (API module, Docker, docs) so existing CLI and `run_agent_v2()` stay the default for devs.

---

## Summary

- **Phase 1** = contributor trust and clarity (CONTRIBUTING, CI, badges, env docs).  
- **Phase 2** = deployment surface (API, health, Docker).  
- **Phase 3** = deployment docs + good-first-issues + error/log polish.

Primary goal (more devs on GitHub) is served by Phase 1 and by turning Phase 2/3 items into labeled, scoped issues so contributors can self-serve. Deployment becomes a natural outcome of the same work.
