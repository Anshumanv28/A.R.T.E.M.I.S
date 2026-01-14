"""
CSV schema converters for A.R.T.E.M.I.S.

This module contains schema-specific converters for different CSV data types.
Converters are automatically registered when this module is imported.
"""

# Import CSV schema converters to auto-register them
# Add new schema converters here as they're implemented

# Restaurant schema converter (MVP)
try:
    from artemis.rag.ingestion.converters.schemas.restaurant import convert_restaurants  # noqa: F401
except ImportError:
    # Restaurant schema converter not available
    pass

# Travel schema converter (Phase 2)
try:
    from artemis.rag.ingestion.converters.schemas.travel import convert_travel  # noqa: F401
except ImportError:
    # Travel schema converter not yet implemented
    pass

# Support schema converter (Phase 2)
# from artemis.rag.ingestion.converters.schemas.support import convert_support  # noqa: F401

__all__ = []  # Schema converters are registered via decorators, not exported directly
