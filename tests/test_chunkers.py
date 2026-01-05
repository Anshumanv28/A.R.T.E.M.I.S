"""
Tests for chunking strategies in A.R.T.E.M.I.S.

Tests all implemented chunkers: CSV_ROW, FIXED, FIXED_OVERLAP, SEMANTIC.

REQUIRED DATA:
=============
These tests require the restaurant dataset CSV file for schema-based chunking tests.

Restaurant Dataset:
- Source: Kaggle
- URL: https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset
- Path: data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv

Note: Some tests use simple DataFrames/text created in-memory for basic functionality testing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

# Import chunkers directly to avoid triggering ingestion module imports
# which would require sentence_transformers
from artemis.rag.ingestion.chunkers.csv_chunker import csv_row_chunker
from artemis.rag.ingestion.chunkers.fixed_chunker import fixed_chunker, fixed_overlap_chunker
from artemis.rag.ingestion.chunkers.semantic_chunker import semantic_chunker
from artemis.rag.ingestion.chunkers.registry import (
    CHUNKERS,
    ChunkStrategy,
    FileType,
    DEFAULT_CHUNK_FOR_FILETYPE,
)
from artemis.rag.ingestion.converters.csv_converter import DocumentSchema

# Path to actual restaurant dataset
RESTAURANT_DATASET_PATH = (
    project_root / "data" / "kaggle_datasets" / "datasets" / 
    "mohdshahnawazaadil" / "restaurant-dataset" / "versions" / "1" / "Dataset .csv"
)

# Import ingestion only if needed (for tests that use ingestion functions)
# This avoids the import chain that requires sentence_transformers
try:
    from artemis.rag.core.indexer import Indexer
    from artemis.rag.ingestion.ingestion import ingest_file
    _INGESTION_AVAILABLE = True
except ImportError:
    _INGESTION_AVAILABLE = False
    Indexer = None
    ingest_file = None


class TestCSVRowChunker:
    """Tests for CSV row chunker."""
    
    def test_csv_row_chunker_basic(self):
        """Test CSV row chunker with basic DataFrame."""
        df = pd.DataFrame({
            "name": ["Test1", "Test2"],
            "value": ["100", "200"]
        })
        
        documents, metadata = csv_row_chunker(df)
        
        assert len(documents) == 2
        assert len(metadata) == 2
        assert "name" in documents[0].lower() or "test1" in documents[0].lower()
        assert "name" in metadata[0]
        assert metadata[0]["name"] == "Test1"
    
    def test_csv_row_chunker_with_schema(self):
        """Test CSV row chunker with RESTAURANT schema using actual dataset."""
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
        
        df = pd.read_csv(RESTAURANT_DATASET_PATH)
        # Use a small subset for testing
        df_subset = df.head(10)
        
        documents, metadata = csv_row_chunker(
            df_subset, 
            schema=DocumentSchema.RESTAURANT, 
            csv_path=RESTAURANT_DATASET_PATH
        )
        
        assert len(documents) > 0
        assert len(metadata) > 0
        assert len(documents) == len(metadata)
        # Check that documents are formatted (should contain restaurant info)
        assert any("restaurant" in doc.lower() for doc in documents[:5])
    
    def test_csv_row_chunker_empty_dataframe(self):
        """Test CSV row chunker with empty DataFrame."""
        df = pd.DataFrame()
        
        documents, metadata = csv_row_chunker(df)
        
        assert len(documents) == 0
        assert len(metadata) == 0


class TestFixedChunker:
    """Tests for fixed-size chunker."""
    
    def test_fixed_chunker_basic(self):
        """Test fixed chunker with basic text."""
        text = "This is a test document. " * 50
        documents, metadata = fixed_chunker(text, chunk_size=100)
        
        assert len(documents) > 0
        assert len(metadata) > 0
        assert len(documents) == len(metadata)
        assert all(len(doc) <= 100 for doc in documents)
    
    def test_fixed_chunker_empty_text(self):
        """Test fixed chunker with empty text."""
        documents, metadata = fixed_chunker("")
        
        assert len(documents) == 0
        assert len(metadata) == 0


class TestFixedOverlapChunker:
    """Tests for fixed-size chunker with overlap."""
    
    def test_fixed_overlap_chunker_basic(self):
        """Test fixed overlap chunker with basic text."""
        text = "This is a test document. " * 50
        documents, metadata = fixed_overlap_chunker(text, chunk_size=100, overlap=20)
        
        assert len(documents) > 0
        assert len(metadata) > 0
        assert len(documents) == len(metadata)
        # Check overlap (first chunk end should appear in second chunk start)
        if len(documents) > 1:
            overlap_text = documents[0][-20:]
            assert overlap_text in documents[1][:40]
    
    def test_fixed_overlap_chunker_empty_text(self):
        """Test fixed overlap chunker with empty text."""
        documents, metadata = fixed_overlap_chunker("")
        
        assert len(documents) == 0
        assert len(metadata) == 0


class TestSemanticChunker:
    """Tests for semantic chunker."""
    
    def test_semantic_chunker_basic(self):
        """Test semantic chunker with basic text."""
        text = """
        This is the first paragraph. It contains multiple sentences.
        These sentences form a coherent paragraph about a topic.
        
        This is the second paragraph. It discusses a different topic.
        The sentences in this paragraph are related to each other.
        
        This is the third paragraph. It introduces yet another topic.
        The content flows naturally within this paragraph.
        """
        
        documents, metadata = semantic_chunker(text, chunk_size=500)
        
        assert len(documents) > 0
        assert len(metadata) > 0
        assert len(documents) == len(metadata)
    
    def test_semantic_chunker_empty_text(self):
        """Test semantic chunker with empty text."""
        documents, metadata = semantic_chunker("")
        
        assert len(documents) == 0
        assert len(metadata) == 0


class TestChunkerRegistry:
    """Tests for chunker registry."""
    
    def test_chunkers_registry(self):
        """Test CHUNKERS registry."""
        assert isinstance(CHUNKERS, dict)
        assert len(CHUNKERS) > 0
    
    def test_default_chunk_for_filetype(self):
        """Test DEFAULT_CHUNK_FOR_FILETYPE mapping."""
        assert FileType.CSV in DEFAULT_CHUNK_FOR_FILETYPE
        assert FileType.TEXT in DEFAULT_CHUNK_FOR_FILETYPE
        assert FileType.MD in DEFAULT_CHUNK_FOR_FILETYPE
        assert DEFAULT_CHUNK_FOR_FILETYPE[FileType.CSV] == ChunkStrategy.CSV_ROW
        assert DEFAULT_CHUNK_FOR_FILETYPE[FileType.TEXT] == ChunkStrategy.FIXED_OVERLAP


def run_tests():
    """Run all chunker tests."""
    print("=" * 60)
    print("Testing Chunking Strategies")
    print("=" * 60)
    print()
    
    # CSV Row Chunker Tests
    print("Testing CSV Row Chunker...")
    test_csv = TestCSVRowChunker()
    test_csv.test_csv_row_chunker_basic()
    print("✅ CSV row chunker: Basic")
    if RESTAURANT_DATASET_PATH.exists():
        test_csv.test_csv_row_chunker_with_schema()
        print("✅ CSV row chunker: With schema (with dataset)")
    else:
        print(f"⚠️  Skipping CSV schema test (dataset not found at {RESTAURANT_DATASET_PATH})")
    test_csv.test_csv_row_chunker_empty_dataframe()
    print("✅ CSV row chunker: Empty DataFrame")
    print()
    
    # Fixed Chunker Tests
    print("Testing Fixed Chunker...")
    test_fixed = TestFixedChunker()
    test_fixed.test_fixed_chunker_basic()
    print("✅ Fixed chunker: Basic")
    test_fixed.test_fixed_chunker_empty_text()
    print("✅ Fixed chunker: Empty text")
    print()
    
    # Fixed Overlap Chunker Tests
    print("Testing Fixed Overlap Chunker...")
    test_overlap = TestFixedOverlapChunker()
    test_overlap.test_fixed_overlap_chunker_basic()
    print("✅ Fixed overlap chunker: Basic")
    test_overlap.test_fixed_overlap_chunker_empty_text()
    print("✅ Fixed overlap chunker: Empty text")
    print()
    
    # Semantic Chunker Tests
    print("Testing Semantic Chunker...")
    test_semantic = TestSemanticChunker()
    test_semantic.test_semantic_chunker_basic()
    print("✅ Semantic chunker: Basic")
    test_semantic.test_semantic_chunker_empty_text()
    print("✅ Semantic chunker: Empty text")
    print()
    
    # Registry Tests
    print("Testing Chunker Registry...")
    test_registry = TestChunkerRegistry()
    test_registry.test_chunkers_registry()
    print("✅ Chunkers registry")
    test_registry.test_default_chunk_for_filetype()
    print("✅ Default chunk for file type")
    print()
    
    print("=" * 60)
    print("All Chunker Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
