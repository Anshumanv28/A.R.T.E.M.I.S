# Metadata Filtering in A.R.T.E.M.I.S.

## Overview

Metadata filtering enables precise querying by extracting filter conditions from natural language queries and applying them to semantic search. This allows queries like "Italian restaurants in Mumbai under 500 rupees" to return only restaurants that match all constraints.

## Architecture

The metadata filtering system consists of three main components:

1. **Query Parser** (`artemis/rag/core/query_parser.py`): Extracts filter conditions from natural language queries
2. **Filter Builder** (`artemis/rag/core/filter_builder.py`): Converts filter conditions to Qdrant Filter objects
3. **Metadata Discovery** (`artemis/rag/core/metadata_discovery.py`): Auto-discovers metadata fields from Qdrant collections

## Implementation History

### Initial Implementation (Hardcoded)

**Problem:** The initial implementation had hardcoded field names and patterns specific to restaurant data:
- Field aliases hardcoded in `query_parser.py`
- Field detection assumed `cost_for_two` for price fields
- Boolean patterns only recognized "delivery" and "table booking"
- Index creation in `indexer.py` used hardcoded field list

**Issues Faced:**

1. **Qdrant Index Requirements**: Qdrant requires indexes on metadata fields before they can be used in filters. Error: `Index required but not found for "city" of one of the following types: [keyword]`

   **Solution:** Added automatic index creation in `Indexer._create_metadata_indexes()` that creates indexes for discovered or configured fields.

2. **Dataset Switching**: Switching from restaurant to travel data required modifying code in multiple places (query parser, indexer).

   **Solution:** Implemented auto-discovery of metadata fields from Qdrant collections, eliminating the need for hardcoded field lists.

### Current Implementation (Adaptable)

The system now automatically:
- Discovers metadata fields from existing documents in Qdrant
- Creates indexes for discovered fields
- Uses discovered fields for query parsing
- Falls back to generic patterns if discovery fails (backward compatible)

## How It Works

### 1. Field Discovery

When documents are indexed or queries are made, the system:
1. Samples documents from the Qdrant collection
2. Analyzes payload to detect field names and types (string, number, boolean)
3. Caches results per collection

### 2. Query Parsing

The query parser:
1. Extracts location constraints ("in Mumbai" → `city == "Mumbai"`)
2. Extracts numeric comparisons ("under 500" → `cost_for_two < 500`)
3. Extracts boolean features ("with delivery" → `has_online_delivery == true`)
4. Uses discovered fields to validate and map extracted field names

### 3. Filter Application

Filters are applied to Qdrant queries:
- If indexes exist: Filters are applied directly
- If indexes missing: Falls back to search without filter (with warning)

## Usage

### Basic Usage (Auto-Discovery)

```python
from artemis.rag.core import Indexer, Retriever, RetrievalMode

# Create indexer - indexes will be auto-created for discovered fields
indexer = Indexer(collection_name="restaurant_data")

# Create retriever - uses auto-discovered fields
retriever = Retriever(indexer=indexer)

# Query with filters - works automatically
results = retriever.retrieve("Italian restaurants in Mumbai under 500 rupees", k=5)
```

### Advanced Usage (Custom Configuration)

```python
from artemis.rag.core import Indexer, Retriever, RetrievalMode, MetadataConfig

# Create custom metadata config
config = MetadataConfig(
    field_aliases={
        "price_per_night": ["price", "rate", "cost"],
        "country": ["nation", "location"]
    },
    field_types={
        "price_per_night": "number",
        "country": "string"
    },
    boolean_patterns=[
        ("has_spa", "spa"),
        ("has_pool", "pool"),
        ("free_cancellation", "free cancellation")
    ]
)

# Use config with indexer and retriever
indexer = Indexer(collection_name="travel_data", metadata_config=config)
retriever = Retriever(indexer=indexer, metadata_config=config)

# Query with custom field mappings
results = retriever.retrieve("hotels in Paris under $200 with spa", k=5)
```

## Supported Query Patterns

### Location Constraints
- "restaurants in Mumbai"
- "hotels from Paris"
- "located in Bangalore"

### Numeric Comparisons
- "under 500 rupees" → `cost_for_two < 500`
- "above 4.5 rating" → `rating > 4.5`
- "at least 3 stars" → `rating >= 3`
- "at most $200" → `price_per_night <= 200`

### Boolean Features
- "with online delivery" → `has_online_delivery == true`
- "has table booking" → `has_table_booking == true`
- "with spa" → `has_spa == true` (if configured)

### Combined Queries
- "Italian restaurants in Mumbai under 500 rupees with delivery"
- "Hotels in Paris above 4 stars with pool"

## Switching Datasets

### From Restaurant to Travel Data

**No code changes needed!** The system auto-discovers fields:

1. Ingest travel data with travel schema:
   ```python
   from artemis.rag.ingestion import ingest_file, FileType, DocumentSchema
   indexer = Indexer(collection_name="travel_data")
   ingest_file("hotels.csv", FileType.CSV, indexer, schema=DocumentSchema.TRAVEL)
   ```

2. Query automatically works:
   ```python
   retriever = Retriever(indexer=indexer)
   results = retriever.retrieve("hotels in Paris under $200")
   ```

The system will:
- Discover fields: `city`, `country`, `price_per_night`, `rating`, etc.
- Create indexes automatically
- Parse queries using discovered fields

## Troubleshooting

### "Index required but not found" Error

**Cause:** Qdrant requires indexes on metadata fields before filtering.

**Solution:**
1. Reinitialize Indexer - it will auto-create indexes:
   ```python
   indexer = Indexer(collection_name="your_collection")
   # Indexes created automatically
   ```

2. Or manually create indexes using Qdrant client

### Filters Not Working

**Possible Causes:**
1. Field names don't match between query and metadata
2. Indexes not created for fields
3. Field types don't match (e.g., filtering number field with string)

**Solution:**
- Check discovered fields: `discovery.discover_fields()`
- Verify indexes exist in Qdrant collection
- Use `MetadataConfig` to provide custom field mappings

## Future Enhancements

- Support for OR conditions ("restaurants in Mumbai OR Delhi")
- Support for date/time filtering
- Support for array/list field filtering
- More sophisticated query parsing with LLM assistance
