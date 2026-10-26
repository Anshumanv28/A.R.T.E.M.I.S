"""
Explicit, honest per-model pricing for cost-per-task estimation.

Unpriced models return None rather than a fabricated number. Verified 2026-10-07:
Groq's llama-3.3-70b-versatile moved to enterprise-only "Contact Sales" pricing
on 2026-08-26. Verified again 2026-10-26: that model has since been removed from
Groq's catalog entirely (404, not just unpriced) -- the repo's default Groq model
was updated to openai/gpt-oss-120b. Verified 2026-10-26 against
console.groq.com/docs/models: $0.15/1M input, $0.60/1M output.
"""

from typing import Dict, Optional, TypedDict


class ModelRate(TypedDict):
    prompt_usd_per_1k: float
    completion_usd_per_1k: float


# USD per 1,000 tokens. None = no public self-serve rate; estimate_cost() returns None.
MODEL_PRICING_USD_PER_1K: Dict[str, Optional[ModelRate]] = {
    "gpt-4o-mini": {"prompt_usd_per_1k": 0.00015, "completion_usd_per_1k": 0.0006},
    "gpt-4o": {"prompt_usd_per_1k": 0.0025, "completion_usd_per_1k": 0.01},
    # console.groq.com/docs/models, verified 2026-10-26: $0.15/1M input, $0.60/1M output.
    "openai/gpt-oss-120b": {"prompt_usd_per_1k": 0.00015, "completion_usd_per_1k": 0.0006},
    # No public pricing since 2026-08-26 (enterprise/Contact Sales only).
    "llama-3.3-70b-versatile": None,
}


def estimate_cost(
    model_name: str, prompt_tokens: int, completion_tokens: int
) -> Optional[float]:
    """
    Estimate USD cost for a model/token count. Returns None (report as
    "pricing_unavailable") when the model has no entry or no public rate,
    rather than guessing.
    """
    rate = MODEL_PRICING_USD_PER_1K.get(model_name)
    if rate is None:
        return None
    return (
        prompt_tokens / 1000.0 * rate["prompt_usd_per_1k"]
        + completion_tokens / 1000.0 * rate["completion_usd_per_1k"]
    )


__all__ = ["MODEL_PRICING_USD_PER_1K", "estimate_cost"]
