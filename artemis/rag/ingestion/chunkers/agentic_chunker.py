"""
Agentic chunking strategy for A.R.T.E.M.I.S.

Uses an LLM to split text into semantic chunks when an llm_client is provided.
Falls back to fixed-overlap chunking when no client is given or when the text
is too long / the LLM call fails.
"""

import json
import re
from typing import List, Dict, Tuple, Any, Optional

from artemis.rag.ingestion.chunkers.registry import register_chunker, ChunkStrategy
from artemis.utils import get_logger

logger = get_logger(__name__)

# Max characters to send in one LLM call (leave room for prompt + response)
MAX_AGENTIC_TEXT_LEN = 6000

AGENTIC_SYSTEM_PROMPT = """You are a document chunking assistant. Split the following text into semantic chunks: each chunk should cover one topic, section, or idea and be self-contained for retrieval.

Rules:
- Preserve the original text; do not summarize or rewrite.
- Return ONLY a valid JSON array of strings. Each string is one chunk. Example: ["first chunk text...", "second chunk text..."]
- No markdown, no code fence, no explanation outside the JSON."""


def _parse_chunks_from_llm(response: str) -> Optional[List[str]]:
    """Extract a list of chunk strings from LLM response. Returns None on parse failure."""
    if not response or not response.strip():
        return None
    text = response.strip()
    # Remove optional markdown code block
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if not isinstance(data, list):
            return None
        chunks = [str(x).strip() for x in data if x]
        return chunks if chunks else None
    except (json.JSONDecodeError, TypeError):
        return None


@register_chunker(ChunkStrategy.AGENTIC)
def agentic_chunker(
    text: str,
    chunk_size: int = 1000,
    llm_client: Optional[Any] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Chunk text using LLM-driven semantic boundaries when llm_client is provided.

    When llm_client is None, or the text is too long, or the LLM call fails,
    falls back to fixed-overlap chunking so ingestion always succeeds.

    Args:
        text: Input text to chunk
        chunk_size: Target size for fallback chunking; also hints desired chunk scale for LLM
        llm_client: Optional client with generate(system_prompt, user_prompt, **) -> str

    Returns:
        Tuple of (documents, metadata). Metadata includes "agentic": True when LLM was used.
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to agentic_chunker")
        return [], []

    use_fallback = True
    documents: List[str] = []
    metadata_list: List[Dict[str, Any]] = []

    if llm_client is not None and len(text) <= MAX_AGENTIC_TEXT_LEN:
        try:
            user_prompt = f"Text to split into semantic chunks:\n\n{text}"
            response = llm_client.generate(
                system_prompt=AGENTIC_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=4096,
            )
            chunks = _parse_chunks_from_llm(response)
            if chunks:
                documents = chunks
                metadata_list = [
                    {
                        "chunk_index": i,
                        "chunk_size": len(c),
                        "strategy": ChunkStrategy.AGENTIC.value,
                        "agentic": True,
                    }
                    for i, c in enumerate(documents)
                ]
                use_fallback = False
                logger.info(f"Created {len(documents)} chunks using agentic (LLM) chunking")
        except Exception as e:
            logger.warning("Agentic LLM chunking failed, using fallback: %s", e)

    if use_fallback:
        from artemis.rag.ingestion.chunkers.fixed_chunker import fixed_overlap_chunker

        documents, metadata_list = fixed_overlap_chunker(
            text,
            chunk_size=chunk_size,
            overlap=chunk_size // 4,
        )
        for meta in metadata_list:
            meta["strategy"] = ChunkStrategy.AGENTIC.value
            meta["agentic"] = False
            meta["note"] = "Agentic fallback (no LLM client or LLM failed)"
        logger.info(f"Created {len(documents)} chunks using agentic fallback")

    return documents, metadata_list
