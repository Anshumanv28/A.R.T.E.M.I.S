"""
Schema converters for A.R.T.E.M.I.S.

This module contains schema-specific converters for different data types.
Converters are automatically registered when this module is imported.
"""

# Import converters to auto-register them
# Add new converters here as they're implemented

# Restaurant converter (MVP)
try:
    from artemis.rag.converters.restaurant import convert_restaurants
except ImportError:
    # Restaurant converter not available
    pass

# Travel converter (Phase 2)
try:
    from artemis.rag.converters.travel import convert_travel
except ImportError:
    # Travel converter not yet implemented
    pass

# Support converter (Phase 2)
# from artemis.rag.converters.support import convert_support

__all__ = []  # Converters are registered via decorators, not exported directly

