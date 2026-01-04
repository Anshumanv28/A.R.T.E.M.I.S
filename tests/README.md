# A.R.T.E.M.I.S. Test Suite

## Running Tests

### Restaurant Document Converter Test

Test the document conversion pipeline with restaurant data:

```bash
# From project root
python tests/test_restaurant_converter.py
```

### Embeddings and Retrieval Test

Test embeddings generation, storage, and retrieval:

```bash
# From project root
python tests/test_embeddings_retrieval.py
```

Or from the tests directory:

```bash
cd tests
python test_restaurant_converter.py
python test_embeddings_retrieval.py
```

## What the Tests Cover

### Test 1: Document Conversion (File Mode)

- Converts restaurant CSV to documents
- Saves documents to `artemis_data/docs/` folder as individual `.txt` files
- Saves metadata to JSON file
- Verifies files are created correctly

### Test 2: Ingestion and Retrieval (Optional)

- Uses `Indexer` to read documents from files
- Ingests into Qdrant vector database
- Deletes files after successful ingestion
- Tests retrieval functionality using `Retriever`

**Note:** Requires `QDRANT_URL` and `QDRANT_API_KEY` environment variables.

### Test 3: In-Memory Mode

- Tests backward compatibility mode
- Returns documents as in-memory lists
- No files created

## Test Data

The test uses the restaurant dataset located at:

```
data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv
```

## Expected Output

The test will:

1. ✅ Convert CSV to documents (saves to `docs/` folder)
2. ✅ Verify files exist and show sample content
3. ⚠️ Skip retriever test if Qdrant not configured
4. ✅ Test in-memory mode

## Files Created During Tests

- `artemis_data/docs/{batch_id}_000000.txt` - Individual document files
- `artemis_data/docs/{batch_id}_metadata.json` - Metadata mapping file

These files are automatically deleted after successful ingestion, or remain for manual inspection if ingestion is skipped.

## Data Directory Structure

All generated files and logs are stored in the centralized `artemis_data/` folder:

```
artemis_data/
├── logs/          # Application logs
│   └── artemis.log
└── docs/          # Generated documents (temporary)
    ├── {batch_id}_000000.txt
    └── {batch_id}_metadata.json
```
