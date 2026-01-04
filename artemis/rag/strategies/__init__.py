"""
Retrieval strategies for A.R.T.E.M.I.S.

This module contains retrieval strategy implementations for different search modes.
Strategies are automatically registered when this module is imported.
"""

# Import strategies to auto-register them
# Add new strategies here as they're implemented

# Semantic search strategy (MVP)
try:
    from artemis.rag.strategies.semantic import semantic_search_strategy
except ImportError:
    # Semantic strategy not available
    pass

# Keyword search strategy (Phase 2)
try:
    from artemis.rag.strategies.keyword import keyword_search_strategy
except ImportError:
    # Keyword strategy not yet implemented
    pass

# Hybrid search strategy (Phase 2)
try:
    from artemis.rag.strategies.hybrid import hybrid_search_strategy
except ImportError:
    # Hybrid strategy not yet implemented
    pass

__all__ = []  # Strategies are registered via decorators, not exported directly

