# Test Data Requirements

This document outlines the actual data files required for running the A.R.T.E.M.I.S test suite.

## Overview

All tests have been updated to use **actual data files** instead of sample/mock data. Tests will skip gracefully if required data is not found.

## Required Datasets

### 1. Restaurant Dataset (Required for CSV tests)

**Source:** Kaggle  
**URL:** https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset

**Path:**

```
data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv
```

**Expected Columns:**

- Restaurant ID
- Restaurant Name
- Country Code
- City
- Address
- Locality
- Locality Verbose
- Longitude
- Latitude
- Cuisines
- Average Cost for two
- Currency
- Has Table booking
- Has Online delivery
- Is delivering now
- Switch to order menu
- Price range
- Aggregate rating
- Rating color
- Rating text
- Votes

**Used by Tests:**

- `test_csv_converter.py` - All CSV converter tests
- `test_csv_schemas.py` - RESTAURANT schema tests
- `test_chunkers.py` - CSV chunker with schema tests
- `test_ingestion_pipeline.py` - CSV ingestion tests
- `test_restaurant_converter.py` - Restaurant converter tests

**How to Download:**

1. Visit: https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset
2. Sign in to Kaggle (account required)
3. Click "Download" button
4. Extract the ZIP file
5. Place `Dataset .csv` in the path above

**Using Kaggle API:**

```bash
kaggle datasets download -d mohdshahnawazaadil/restaurant-dataset -p data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/
unzip data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/*.zip -d data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/
```

### 2. Travel Dataset (Optional for TRAVEL schema tests)

**Status:** Not currently available

**Required Format:** CSV file with hotel/booking data

**Expected Columns:**

- hotel_name (or name, property_name)
- city
- country
- price_per_night (or price, rate)
- rating
- amenities
- room_type (optional)
- cancellation_policy (optional)
- check_in (optional)
- check_out (optional)

**Used by Tests:**

- `test_csv_schemas.py` - TRAVEL schema tests (optional)

**Note:** If you have a travel dataset, update `TRAVEL_DATASET_PATH` in `test_csv_schemas.py`

## Test-Specific Requirements

### test_loaders.py

**Status:** Uses actual test files from `tests/test_data/` if available, otherwise temporary files

**Required Test Files:**

- `tests/test_data/text/sample.txt` - Text file (500+ words)
- `tests/test_data/markdown/sample.md` - Markdown file
- `tests/test_data/pdf/sample.pdf` - PDF file with extractable text (optional)
- `tests/test_data/docx/sample.docx` - DOCX file (optional)

**Behavior:**

- Tests use actual files from `tests/test_data/` if they exist
- Falls back to temporary files if test files are not found (with warnings)
- Tests verify file loading functionality, error handling, and format parsing
- See [WHAT_TO_ADD.md](WHAT_TO_ADD.md) for details on what files to add

### test_embeddings_retrieval.py

**Status:** Uses documents from restaurant dataset conversion

**Current Implementation:** Uses inline sample documents (needs update)

**Recommended:** Should use documents converted from the restaurant dataset using `csv_to_documents()`.

**Required:**

- Restaurant dataset (see above)
- Qdrant instance (for full integration tests)
- sentence_transformers (for embedding tests)

### test_ingestion_pipeline.py

**CSV Tests:**

- Uses restaurant dataset (see above)

**Text/Markdown Tests:**

- Uses actual test files from `tests/test_data/` if available
- Falls back to temporary files if test files are not found (with warnings)
- See [WHAT_TO_ADD.md](WHAT_TO_ADD.md) for details on what files to add

**PDF/DOCX Tests:**

- Uses actual test files from `tests/test_data/` if available
- Tests skip gracefully if files are not found
- See [WHAT_TO_ADD.md](WHAT_TO_ADD.md) for details on what files to add

## Summary

| Test File                      | Required Data                         | Optional Data                   |
| ------------------------------ | ------------------------------------- | ------------------------------- |
| `test_csv_converter.py`        | Restaurant dataset                    | -                               |
| `test_csv_schemas.py`          | Restaurant dataset                    | Travel dataset                  |
| `test_chunkers.py`             | Restaurant dataset (for schema tests) | -                               |
| `test_ingestion_pipeline.py`   | Restaurant dataset (for CSV tests)    | Test files (see WHAT_TO_ADD.md) |
| `test_loaders.py`              | Test files (see WHAT_TO_ADD.md)       | -                               |
| `test_embeddings_retrieval.py`  | Restaurant dataset                    | Qdrant instance                 |
| `test_restaurant_converter.py` | Restaurant dataset                    | Qdrant instance                 |

## Quick Setup

To run all tests, you need at minimum:

1. **Restaurant Dataset** (most tests require this)

   - Download from Kaggle: https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset
   - Extract to: `data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv`

2. **Optional: Travel Dataset** (for TRAVEL schema tests)

   - Provide your own travel/hotel booking CSV
   - Update `TRAVEL_DATASET_PATH` in `test_csv_schemas.py`

3. **Optional: Test Files** (for loader and ingestion tests)

   - Add files to `tests/test_data/` (see [WHAT_TO_ADD.md](WHAT_TO_ADD.md))
   - Text: `tests/test_data/text/sample.txt`
   - Markdown: `tests/test_data/markdown/sample.md`
   - PDF: `tests/test_data/pdf/sample.pdf` (optional)
   - DOCX: `tests/test_data/docx/sample.docx` (optional)

4. **Optional: Qdrant Instance** (for retrieval tests)
   - Set `QDRANT_URL` and `QDRANT_API_KEY` environment variables
   - Or run local Qdrant instance

## Notes

- All tests skip gracefully if required data is not found
- Test files include documentation about data requirements in their headers
- Temporary files created by tests are automatically cleaned up
- Mock Indexer is used for ingestion pipeline tests (no Qdrant required)
