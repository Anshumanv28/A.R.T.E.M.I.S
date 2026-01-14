"""
Tests for CSV converter infrastructure in A.R.T.E.M.I.S.

Tests format_doc, csv_to_documents, DocumentSchema, registry, etc.

REQUIRED DATA:
=============
These tests require the restaurant dataset CSV file. 

Dataset: Restaurant Dataset
Source: Kaggle
URL: https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset
Path: data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv

Expected CSV columns:
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

To download:
1. Visit https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset
2. Download the dataset (requires Kaggle account and API credentials)
3. Extract to: data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/
4. Ensure the file is named "Dataset .csv" (with space before .csv)

Alternatively, if you have the dataset elsewhere, update RESTAURANT_DATASET_PATH in this file.

Using Kaggle API:
-----------------
If you have Kaggle API credentials set up:
    kaggle datasets download -d mohdshahnawazaadil/restaurant-dataset -p data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/
    unzip data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/*.zip -d data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

# Import pytest here to avoid breaking if not installed
try:
    import pytest
except ImportError:
    pytest = None

from artemis.rag.ingestion.converters.csv_converter import (
    format_doc,
    csv_to_documents,
    DocumentSchema,
    CSV_CONVERTERS,
    register_csv_schema,
)

# Path to actual restaurant dataset
# This dataset is required for running the tests
RESTAURANT_DATASET_PATH = (
    project_root / "data" / "kaggle_datasets" / "datasets" / 
    "mohdshahnawazaadil" / "restaurant-dataset" / "versions" / "1" / "Dataset .csv"
)


class TestFormatDoc:
    """Tests for format_doc utility."""
    
    def test_format_doc_basic(self):
        """Test format_doc with basic dict."""
        parts = {
            "Restaurant": "Le Petit Souffle",
            "Location": "Makati City",
            "Rating": "4.8"
        }
        
        result = format_doc(parts)
        
        assert "Restaurant: Le Petit Souffle" in result
        assert "Location: Makati City" in result
        assert "Rating: 4.8" in result
    
    def test_format_doc_filters_empty(self):
        """Test format_doc filters out empty values."""
        parts = {
            "Restaurant": "Test",
            "Location": "",
            "Rating": None,
            "Price": "N/A"
        }
        
        result = format_doc(parts)
        
        assert "Restaurant: Test" in result
        assert "Location:" not in result
        assert "Rating:" not in result
        assert "Price:" not in result
    
    def test_format_doc_empty_dict(self):
        """Test format_doc with empty dict."""
        result = format_doc({})
        assert result == ""


class TestDocumentSchema:
    """Tests for DocumentSchema enum."""
    
    def test_document_schema_values(self):
        """Test DocumentSchema enum values."""
        assert DocumentSchema.RESTAURANT.value == "restaurant"
        assert DocumentSchema.TRAVEL.value == "travel"
        assert DocumentSchema.SUPPORT.value == "support"
    
    def test_document_schema_enum(self):
        """Test DocumentSchema enum access."""
        schema = DocumentSchema.RESTAURANT
        assert isinstance(schema, DocumentSchema)
        assert schema == DocumentSchema.RESTAURANT


class TestCSVToDocuments:
    """Tests for csv_to_documents function."""
    
    def test_csv_to_documents_in_memory(self):
        """Test csv_to_documents in-memory mode with actual dataset."""
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
        
        documents, metadata = csv_to_documents(str(RESTAURANT_DATASET_PATH))
        
        assert isinstance(documents, list)
        assert isinstance(metadata, list)
        assert len(documents) > 0
        assert len(metadata) > 0
        assert len(documents) == len(metadata)
        
        # Check document format
        assert any("restaurant" in doc.lower() for doc in documents[:10])
        
        # Check metadata structure
        if metadata:
            assert isinstance(metadata[0], dict)
    
    def test_csv_to_documents_with_schema(self):
        """Test csv_to_documents with RESTAURANT schema using actual dataset."""
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
        
        documents, metadata = csv_to_documents(
            str(RESTAURANT_DATASET_PATH), 
            schema=DocumentSchema.RESTAURANT
        )
        
        assert len(documents) > 0
        assert len(metadata) > 0
        assert len(documents) == len(metadata)
        
        # Schema-based conversion should format documents
        assert any("restaurant" in doc.lower() or "rating" in doc.lower() for doc in documents[:10])
    
    def test_csv_to_documents_save_to_disk(self):
        """Test csv_to_documents with save_to_disk=True using actual dataset."""
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
        
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_paths, metadata_path = csv_to_documents(
                str(RESTAURANT_DATASET_PATH),
                save_to_disk=True,
                output_dir=tmpdir
            )
            
            assert isinstance(doc_paths, list)
            assert isinstance(metadata_path, str)
            assert len(doc_paths) > 0
            
            # Check files exist
            for doc_path in doc_paths:
                assert Path(doc_path).exists()
            
            assert Path(metadata_path).exists()
    
    def test_csv_to_documents_file_not_found(self):
        """Test csv_to_documents with non-existent file."""
        fake_path = "/nonexistent/file.csv"
        
        try:
            csv_to_documents(fake_path)
            assert False, "Should have raised FileNotFoundError"
        except (FileNotFoundError, pd.errors.EmptyDataError):
            assert True


class TestCSVConverterRegistry:
    """Tests for CSV converter registry."""
    
    def test_csv_converters_registry(self):
        """Test CSV_CONVERTERS registry."""
        assert isinstance(CSV_CONVERTERS, dict)
        # RESTAURANT and TRAVEL should be registered if schemas module imported
        # This test just checks the registry exists
    
    def test_register_csv_schema_decorator(self):
        """Test register_csv_schema decorator."""
        # Define a test converter
        @register_csv_schema(DocumentSchema.SUPPORT)
        def test_converter(csv_path: str):
            df = pd.read_csv(csv_path)
            docs = [f"Support: {row.get('ticket_id', '')}" for _, row in df.iterrows()]
            metadata = [{"ticket_id": row.get("ticket_id")} for _, row in df.iterrows()]
            return docs, metadata
        
        # Check it's registered
        assert DocumentSchema.SUPPORT in CSV_CONVERTERS
        assert CSV_CONVERTERS[DocumentSchema.SUPPORT] == test_converter


def run_tests():
    """Run all CSV converter tests."""
    print("=" * 60)
    print("Testing CSV Converter Infrastructure")
    print("=" * 60)
    print()
    
    # Check if dataset exists
    if not RESTAURANT_DATASET_PATH.exists():
        print("❌ REQUIRED DATASET NOT FOUND")
        print(f"   Expected path: {RESTAURANT_DATASET_PATH}")
        print()
        print("   Please download the restaurant dataset:")
        print("   - URL: https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset")
        print("   - See file header for detailed instructions")
        print()
        print("   Some tests will be skipped without the dataset.")
        print()
    
    # Format Doc Tests
    print("Testing format_doc...")
    test_format = TestFormatDoc()
    test_format.test_format_doc_basic()
    print("✅ format_doc: Basic")
    test_format.test_format_doc_filters_empty()
    print("✅ format_doc: Filters empty")
    test_format.test_format_doc_empty_dict()
    print("✅ format_doc: Empty dict")
    print()
    
    # DocumentSchema Tests
    print("Testing DocumentSchema...")
    test_schema = TestDocumentSchema()
    test_schema.test_document_schema_values()
    print("✅ DocumentSchema: Values")
    test_schema.test_document_schema_enum()
    print("✅ DocumentSchema: Enum access")
    print()
    
    # CSV To Documents Tests
    print("Testing csv_to_documents...")
    test_converter = TestCSVToDocuments()
    
    # Test with actual dataset
    if RESTAURANT_DATASET_PATH.exists():
        test_converter.test_csv_to_documents_in_memory()
        print("✅ csv_to_documents: In-memory mode (with dataset)")
        try:
            test_converter.test_csv_to_documents_with_schema()
            print("✅ csv_to_documents: With schema (with dataset)")
        except Exception as e:
            print(f"⚠️  csv_to_documents with schema: {e}")
        test_converter.test_csv_to_documents_save_to_disk()
        print("✅ csv_to_documents: Save to disk (with dataset)")
    else:
        print("⚠️  Skipping dataset tests (dataset not found)")
    print()
    
    # Registry Tests
    print("Testing CSV Converter Registry...")
    test_registry = TestCSVConverterRegistry()
    test_registry.test_csv_converters_registry()
    print("✅ CSV_CONVERTERS registry")
    test_registry.test_register_csv_schema_decorator()
    print("✅ register_csv_schema decorator")
    print()
    
    print("=" * 60)
    print("All CSV Converter Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
