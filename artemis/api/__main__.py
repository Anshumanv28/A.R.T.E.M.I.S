"""Run the ARTEMIS API server. Usage: python -m artemis.api"""

import os

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("ARTEMIS_API_PORT", "8000"))
    uvicorn.run(
        "artemis.api:app",
        host="0.0.0.0",
        port=port,
    )
