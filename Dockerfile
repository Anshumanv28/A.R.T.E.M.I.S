# ARTEMIS API image. Non-Docker run (pip install -e ., python -m artemis.api) is unchanged.
# To run the CLI instead of the API: docker run ... artemis python -m artemis.agent.run --v2 "Your query"

FROM python:3.12-slim

WORKDIR /app

# Copy dependency and package metadata first for better layer caching
COPY pyproject.toml .
COPY artemis/ artemis/

RUN pip install --no-cache-dir .

# Config (GROQ_API_KEY, QDRANT_URL, QDRANT_API_KEY, etc.) must be provided at runtime via -e or --env-file
EXPOSE 8000
ENV ARTEMIS_API_PORT=8000

CMD ["python", "-m", "artemis.api"]
