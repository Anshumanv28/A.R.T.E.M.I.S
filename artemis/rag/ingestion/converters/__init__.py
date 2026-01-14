"""
CSV converters for A.R.T.E.M.I.S.

Provides CSV schema-aware formatting and conversion utilities.
"""

from artemis.rag.ingestion.converters.csv_converter import (
    DocumentSchema,
    CSV_CONVERTERS,
    register_csv_schema,
    format_doc,
    csv_to_documents,
)

# Auto-register CSV schema converters (restaurant, travel, support, etc.)
# These are registered when the schemas module is imported
try:
    from artemis.rag.ingestion.converters import schemas  # noqa: F401
except ImportError:
    # CSV schemas module not available or not yet implemented
    pass

__all__ = [
    "DocumentSchema",
    "CSV_CONVERTERS",
    "register_csv_schema",
    "format_doc",
    "csv_to_documents",
]

