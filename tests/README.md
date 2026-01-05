# A.R.T.E.M.I.S. Test Suite

Comprehensive test suite for all implemented components in the RAG pipeline.

## Running Tests

### Run All Tests

```bash
# From project root (recommended)
python -m pytest tests/ -v
# or
pytest tests/ -v

# From tests directory
cd tests
python -m pytest . -v
# or
pytest . -v
# or simply
pytest -v

# Or run individual test files (from project root)
python tests/test_loaders.py
python tests/test_chunkers.py
python tests/test_csv_converter.py
python tests/test_csv_schemas.py
python tests/test_ingestion_pipeline.py
python tests/test_restaurant_converter.py
python tests/test_embeddings_retrieval.py

# Or from tests directory
cd tests
python test_loaders.py
python test_chunkers.py
# etc.
```

### Run Specific Test Categories

```bash
# From project root - Unit tests only
pytest tests/test_loaders.py tests/test_chunkers.py tests/test_csv_converter.py -v

# From project root - Integration tests
pytest tests/test_ingestion_pipeline.py tests/test_embeddings_retrieval.py -v

# Or run as scripts (from project root)
python tests/test_loaders.py
python tests/test_chunkers.py
python tests/test_csv_converter.py
python tests/test_ingestion_pipeline.py
python tests/test_embeddings_retrieval.py
```

## Test Files Overview

### Component Tests (Unit Tests)

1. **`test_loaders.py`**

   - Tests all file loaders (CSV, PDF, DOCX, Markdown, Text)
   - Tests file not found errors
   - Tests encoding handling
   - Uses temporary files for testing

2. **`test_chunkers.py`**

   - Tests all chunking strategies (CSV_ROW, FIXED, FIXED_OVERLAP, SEMANTIC)
   - Tests chunker registry
   - Tests default strategy mapping
   - Tests edge cases (empty input, etc.)

3. **`test_csv_converter.py`**

   - Tests `format_doc()` utility
   - Tests `csv_to_documents()` function (in-memory and save-to-disk modes)
   - Tests `DocumentSchema` enum
   - Tests `register_csv_schema()` decorator
   - Tests CSV_CONVERTERS registry

4. **`test_csv_schemas.py`**
   - Tests RESTAURANT schema converter
   - Tests TRAVEL schema converter
   - Tests schema registration
   - Tests document formatting

### Integration Tests

5. **`test_ingestion_pipeline.py`**

   - Tests `ingest_file()` with different file types
   - Tests convenience functions (ingest_csv, ingest_pdf, etc.)
   - Tests default and custom chunking strategies
   - Tests CSV with schemas
   - Tests error handling
   - Uses mocked Indexer

6. **`test_restaurant_converter.py`**

   - Tests CSV conversion pipeline with restaurant data
   - Tests file-based and in-memory modes
   - Tests retriever integration (optional, requires Qdrant)

7. **`test_embeddings_retrieval.py`**
   - Tests embeddings generation
   - Tests indexer storage
   - Tests semantic retrieval
   - Tests end-to-end pipeline
   - Requires Qdrant configuration

### Utility Tests

8. **`test_colorama.py`**
   - Tests colorama utility (keep as-is)

## What Each Test Category Covers

### Loaders (`test_loaders.py`)

- ✅ CSV file loading (DataFrame creation)
- ✅ Text file loading (UTF-8 encoding)
- ✅ Markdown file loading
- ✅ File not found errors
- ⚠️ PDF/DOCX loading (basic tests, full tests require actual files)

### Chunkers (`test_chunkers.py`)

- ✅ CSV_ROW chunker (with/without schema)
- ✅ FIXED chunker (word boundary handling)
- ✅ FIXED_OVERLAP chunker (overlap verification)
- ✅ SEMANTIC chunker (paragraph/sentence awareness)
- ✅ Chunker registry verification
- ✅ Default strategy mapping
- ⚠️ Agentic chunker (skipped - placeholder)

### CSV Converter (`test_csv_converter.py`)

- ✅ `format_doc()` utility (field formatting, empty value filtering)
- ✅ `csv_to_documents()` in-memory mode
- ✅ `csv_to_documents()` save-to-disk mode
- ✅ `DocumentSchema` enum
- ✅ Schema registration decorator
- ✅ CSV_CONVERTERS registry

### CSV Schemas (`test_csv_schemas.py`)

- ✅ RESTAURANT schema converter (registration, conversion, formatting)
- ✅ TRAVEL schema converter (registration, conversion, formatting)
- ✅ Schema-specific document formatting

### Ingestion Pipeline (`test_ingestion_pipeline.py`)

- ✅ `ingest_file()` with CSV, Text, Markdown
- ✅ Convenience functions (ingest_csv, ingest_text, ingest_md)
- ✅ Custom chunking strategies
- ✅ CSV with schemas
- ✅ Error handling
- ⚠️ PDF/DOCX ingestion (requires actual files or mocking)

### Restaurant Converter (`test_restaurant_converter.py`)

- ✅ CSV to documents conversion
- ✅ File-based storage mode
- ✅ In-memory mode
- ✅ Retriever integration (optional, requires Qdrant)

### Embeddings & Retrieval (`test_embeddings_retrieval.py`)

- ✅ Embedding generation
- ✅ Indexer storage
- ✅ Semantic retrieval
- ✅ Strategy registry
- ✅ End-to-end pipeline
- ✅ Metadata preservation

## Test Dependencies

### Required

- Python 3.12+
- pandas (for CSV tests)
- pytest (recommended, but tests can run standalone)

### Optional (for full test coverage)

- pdfplumber or PyPDF2 (for PDF loader tests)
- python-docx (for DOCX loader tests)
- sentence_transformers (for semantic chunker tests)
- qdrant_client (for retrieval tests)

## Test Data

Tests use:

- Temporary files created in `conftest.py`
- Sample CSV data (restaurant, travel schemas)
- Sample text and markdown content
- Mocked Indexer for ingestion pipeline tests

## Environment Variables

Some tests may use environment variables:

- `ARTEMIS_SAVE_DOCS_TO_DISK` - Controls file-based mode in CSV converter tests
- `QDRANT_URL`, `QDRANT_API_KEY` - Required for retrieval tests (optional for other tests)

## Expected Output

Tests should output:

- ✅ for passed tests
- ⚠️ for skipped tests (missing dependencies)
- ❌ for failed tests (with error details)

## Notes

- Tests use temporary files that are automatically cleaned up
- Mock Indexer is used for ingestion pipeline tests (no actual Qdrant connection needed)
- Full PDF/DOCX tests would require actual files (can be added as integration tests)
- Placeholder components (agentic_chunker, keyword/hybrid strategies) are not tested
