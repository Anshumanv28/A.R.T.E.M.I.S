# A.R.T.E.M.I.S. Template Files

This directory contains template files to help you quickly create custom components for A.R.T.E.M.I.S.

## Available Templates

### 1. `template_csv_schema.py`

Template for creating custom CSV schema converters.

**Use when**: You want to convert structured CSV data into formatted text documents optimized for semantic search.

**What it does**: Transforms CSV rows into formatted documents with metadata for filtering.

**Example use case**: Converting restaurant data, travel bookings, product catalogs, etc.

### 2. `template_chunker.py`

Template for creating custom chunking strategies.

**Use when**: You need a different way to split content into chunks (beyond fixed-size, semantic, etc.).

**What it does**: Splits content (text or CSV) into smaller pieces suitable for embedding.

**Example use case**: Domain-specific chunking (e.g., code files, legal documents, medical records).

### 3. `template_retrieval_strategy.py`

Template for creating custom retrieval/search strategies.

**Use when**: You want to implement a different search method (beyond semantic vector search).

**What it does**: Implements how documents are retrieved from the vector database.

**Example use case**: Keyword search (BM25), hybrid search, domain-specific ranking.

### 4. `template_metadata_extractor.py`

Template for creating custom metadata extractors.

**Use when**: You need to extract structured metadata from content during chunking.

**What it does**: Extracts metadata (page numbers, sections, headers, etc.) for each chunk.

**Example use case**: Extracting page numbers from PDFs, headers from Markdown, row data from CSV.

## How to Use Templates

### Step 1: Copy the Template

Copy the template file to your project:

```bash
# For your own project
cp examples/templates/template_csv_schema.py my_project/my_schema.py

# Or if contributing to A.R.T.E.M.I.S.
cp examples/templates/template_csv_schema.py artemis/rag/ingestion/converters/schemas/my_schema.py
```

### Step 2: Customize

1. **Update the docstrings** with your component's description
2. **Replace TODO comments** with your actual implementation
3. **Customize the logic** for your specific use case
4. **Update imports** if needed

### Step 3: Register

The template includes the registration decorator. Just import your module to register it:

```python
# Import to register
from my_project.my_schema import convert_my_schema, SCHEMA

# Now use it
from artemis.rag import ingest_file, FileType, Indexer, DocumentSchema

indexer = Indexer()
ingest_file("data.csv", FileType.CSV, indexer, schema=SCHEMA)
```

## Quick Start Examples

### CSV Schema Converter

```python
# 1. Copy template_csv_schema.py to my_schema.py
# 2. Customize the conversion logic
# 3. Use it:

from my_project.my_schema import SCHEMA
from artemis.rag import ingest_file, FileType, Indexer

indexer = Indexer()
ingest_file("data.csv", FileType.CSV, indexer, schema=SCHEMA)
```

### Custom Chunker

```python
# 1. Copy template_chunker.py to my_chunker.py
# 2. Customize the chunking logic
# 3. Use it:

from my_project.my_chunker import STRATEGY
from artemis.rag import ingest_file, FileType, Indexer

indexer = Indexer()
ingest_file("file.pdf", FileType.PDF, indexer, chunk_strategy=STRATEGY)
```

### Custom Retrieval Strategy

```python
# 1. Copy template_retrieval_strategy.py to my_strategy.py
# 2. Customize the search logic
# 3. Use it:

from my_project.my_strategy import my_custom_search
from artemis.rag import Retriever, RetrievalMode

retriever = Retriever(mode=RetrievalMode.MY_MODE)
results = retriever.retrieve("query", k=5)
```

## Template Structure

Each template includes:

1. **Header documentation** - Explains what the template is for
2. **Import statements** - Required imports for the component type
3. **Registration decorator** - Automatically registers the component
4. **Function/class skeleton** - Basic structure with TODO comments
5. **Example usage** - Commented-out example code
6. **Type hints** - Proper type annotations
7. **Logging** - Logger setup for debugging

## Customization Checklist

When customizing a template:

- [ ] Update docstrings with your component's description
- [ ] Replace all TODO comments with actual implementation
- [ ] Update function/class names if needed
- [ ] Add your specific logic
- [ ] Test your component
- [ ] Update example usage code
- [ ] Verify imports work correctly

## Best Practices

1. **Follow the existing patterns** - Look at existing implementations in the codebase
2. **Use helper functions** - Leverage `format_doc()`, logger, etc.
3. **Handle errors gracefully** - Use try/except blocks
4. **Add logging** - Use logger for debugging
5. **Include type hints** - Maintain type annotations
6. **Document your code** - Update docstrings

## Getting Help

- See [EXTENDING_ARTEMIS.md](../../docs/EXTENDING_ARTEMIS.md) for comprehensive guide
- See [QUICK_REFERENCE.md](../../docs/QUICK_REFERENCE.md) for quick reference
- Check existing implementations:
  - CSV schemas: `artemis/rag/ingestion/converters/schemas/`
  - Chunkers: `artemis/rag/ingestion/chunkers/`
  - Strategies: `artemis/rag/strategies/`
  - Extractors: `artemis/rag/ingestion/metadata_extractors/`

## Contributing

If you create a useful component using a template, consider:

1. Adding it to A.R.T.E.M.I.S. if it's generally useful
2. Sharing it as an example in the `examples/` directory
3. Documenting it in the developer guide

## Next Steps

1. Choose the template that matches your need
2. Copy and customize it
3. Test your component
4. Integrate it into your project
5. Share it with the community (optional)

Happy coding!
