# Deploy ARTEMIS on AWS (free tier)

Plan for running ARTEMIS on AWS at **no cost** (or minimal cost after free tier), using **Qdrant Cloud** for the vector DB so you only host the app.

---

## What you need outside AWS (free)

| Dependency | Where | Cost |
|------------|--------|------|
| **LLM** | Groq or OpenAI | Groq free tier / OpenAI pay‑per‑use |
| **Vector DB** | Qdrant Cloud | Free tier (1 cluster) |
| **App (ARTEMIS)** | AWS | Free tier options below |

Keep **Qdrant Cloud** and **Groq/OpenAI** as-is; deploy only the ARTEMIS API (and agent) on AWS. Build and run with Docker locally first (see [README](../README.md) “Run with Docker”); then deploy that image to EC2 or Lambda.

---

## AWS free tier (quick reference)

- **New accounts (2025):** Up to **$200 credits** for 6 months (or until used). Use for any eligible service (EC2, Lambda, etc.).
- **EC2:** **750 hours/month** of t2.micro or t3.micro (Linux) for **12 months**. One instance 24/7 fits. After 12 months you pay (~\$8–10/mo for t3.micro) or move elsewhere.
- **Lambda:** **Always free:** 1M requests/month + 400,000 GB‑seconds compute. No expiry. Cold starts and deployment size are the main constraints for this app.
- **API Gateway:** 1M REST API calls/month free for 12 months.
- **Secrets / config:** **Systems Manager Parameter Store** — 10,000 *standard* parameters free (enough for a few env vars). Or store in Lambda/EC2 user data and avoid Secrets Manager.

---

## Recommended: EC2 free tier (12 months)

**Best fit:** One small instance 24/7, run the API in Docker. Simple, no cold starts, easy to debug.

### Architecture

```
Internet → (optional: Route53 + ACM cert)
    → EC2 (t2.micro / t3.micro)
        → Docker container: ARTEMIS API (FastAPI/uvicorn)
            → Qdrant Cloud (env: QDRANT_URL, QDRANT_API_KEY)
            → Groq/OpenAI (env: GROQ_API_KEY or OPENAI_API_KEY)
```

### Steps (high level)

1. **AWS account** — Sign up; use Free Plan or Paid Plan (credits still apply).
2. **Region** — Pick one (e.g. `us-east-1`) and stick to it for all resources.
3. **EC2 instance**
   - AMI: Amazon Linux 2023 or Ubuntu 22.04.
   - Type: **t2.micro** or **t3.micro** (free tier eligible).
   - Storage: 8–30 GB (default is fine).
   - Security group: allow **22** (SSH) from your IP; **80** (and **443** if you add HTTPS) from `0.0.0.0/0` for the API.
4. **Install Docker** on the instance (e.g. Amazon Linux: `sudo yum install -y docker`; start and enable Docker).
5. **Env vars** — Use **Parameter Store** (free) or a `.env` file on the instance (never commit it). Required: `GROQ_API_KEY` or `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`; optional: `ARTEMIS_LLM_PROVIDER`, `ARTEMIS_LLM_MODEL`, etc.
6. **Run the app** — Build the ARTEMIS Docker image (or pull from a registry). Run the container with env injected; map port 8000 (or 80) to host. Use a process manager (e.g. systemd) or a simple `docker run` with `--restart unless-stopped`.
7. **Health check** — `GET http://<instance-public-ip>:8000/health` (or the port you use). Returns 200 when app and dependencies are OK.
8. **Optional:** Put a domain in **Route53** (free hosted zone for first one) and add **ACM** certificate + **Application Load Balancer** for HTTPS; that uses more of your free-tier/credits.

### After 12 months

- Keep paying for the small instance (~\$8–10/mo), or
- Move to **AWS Lightsail** ($3.5/mo for smallest), or
- Move to another free-tier host (e.g. Render, Fly.io) and keep Qdrant Cloud.

---

## Alternative: Lambda + API Gateway (always free, with caveats)

**Pros:** Always-free tier (1M requests/month); no server to manage.  
**Cons:** Cold starts (can be 10–30+ seconds with `sentence-transformers`); deployment package or image can be large; timeout (max 15 min); need to design for stateless, single-request handling.

### Fit for ARTEMIS

- The agent uses **sentence-transformers** and other heavy deps → Lambda **container image** (up to 10 GB) is more realistic than a zip.
- First request after idle will be slow (cold start). Subsequent requests in the same concurrency slot are faster.
- Good for **low, bursty traffic** (e.g. a few dozen queries per day). For “always responsive” demos, EC2 is better.

### High-level setup

1. **Package:** Build a Docker image that runs a small HTTP server (e.g. FastAPI + Mangum) exposing `POST /query` and `GET /health`, calling `run_agent_v2()`.
2. **Push image** to **Amazon ECR** (free tier: 500 MB/month).
3. **Lambda:** Create function from container image; set memory (e.g. 2–3 GB) and timeout (e.g. 60–120 s). Use **Lambda URL** or **API Gateway HTTP API** to expose it.
4. **Env vars:** Set in Lambda configuration (Qdrant, Groq/OpenAI keys). Or use Parameter Store and load in the handler.
5. **API Gateway:** Create HTTP API, attach Lambda; use free tier (1M calls/month for 12 months). After that, cost is still low for moderate traffic.

---

## Where to store secrets (free)

| Method | Use case |
|--------|----------|
| **Lambda / EC2 env** | Store non-secret config and, if you’re careful, API keys (not ideal for teams). |
| **Systems Manager Parameter Store** | **Standard** parameters: 10,000 free. Store `GROQ_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`. App pulls at startup. |
| **Secrets Manager** | Free for a small number of secrets; use if you want rotation or stricter access control later. |

For minimal cost and simplicity: **Parameter Store (Standard)** or env vars in the task/function.

---

## Checklist before you deploy

- [ ] ARTEMIS has an **HTTP API** (e.g. `POST /query`, `GET /health`) — see MVP plan.
- [ ] **Dockerfile** builds and runs the API (and optionally runs tests in CI).
- [ ] **Qdrant Cloud** free cluster created; `QDRANT_URL` and `QDRANT_API_KEY` in hand.
- [ ] **Groq** (or OpenAI) API key ready; set in Parameter Store or env.
- [ ] **Security group** allows only needed ports (22 from your IP; 80/443 from internet if API is public).
- [ ] **Health** endpoint returns 503 if Qdrant or LLM config is missing so you don’t mark the app healthy when it can’t work.

---

## Summary

| Option | Free for | Best for |
|--------|----------|----------|
| **EC2 t2/t3.micro** | 12 months (750 hrs/mo) | Always-on API, no cold starts, simple ops. |
| **Lambda + API Gateway** | 1M req/mo always (Lambda); 1M calls/mo 12 mo (API Gw) | Low traffic, bursty; accept cold starts. |
| **Qdrant + Groq/OpenAI** | External free tiers | Use from both EC2 and Lambda. |

**Recommendation:** Start with **EC2 free tier** + Docker + Qdrant Cloud + Parameter Store (or .env). Add **Lambda** later if you want an always-free, low-traffic option and can tolerate cold starts. Keep deployment docs (this file + `DEPLOYMENT.md`) in the repo so contributors can run the same stack locally with Docker and deploy to AWS when needed.
