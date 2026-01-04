"""
Chunking strategies for A.R.T.E.M.I.S.

This module contains chunking strategy implementations. Chunkers are
automatically registered when this module is imported.
"""

# Import chunkers to auto-register them
# Add new chunkers here as they're implemented

# CSV chunker
try:
    from artemis.rag.core.chunkers.csv_chunker import csv_row_chunker  # noqa: F401
except ImportError:
    pass

# Fixed chunkers
try:
    from artemis.rag.core.chunkers.fixed_chunker import (  # noqa: F401
        fixed_chunker,
        fixed_overlap_chunker,
    )
except ImportError:
    pass

# Semantic chunker
try:
    from artemis.rag.core.chunkers.semantic_chunker import semantic_chunker  # noqa: F401
except ImportError:
    pass

# Agentic chunker
try:
    from artemis.rag.core.chunkers.agentic_chunker import agentic_chunker  # noqa: F401
except ImportError:
    pass

__all__ = []  # Chunkers are registered via decorators, not exported directly

