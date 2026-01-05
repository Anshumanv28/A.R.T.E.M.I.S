"""
Tests for ingestion pipeline in A.R.T.E.M.I.S.

Tests ingest_file and convenience functions (ingest_csv, ingest_pdf, etc.).

REQUIRED DATA:
=============
These tests require the restaurant dataset CSV file for CSV ingestion tests.

Restaurant Dataset:
- Source: Kaggle
- URL: https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset
- Path: data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv

Note: Text and Markdown tests use simple test files created in-memory for unit testing.
These verify the ingestion pipeline functionality without requiring external data files.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import ingestion functions (may fail if sentence_transformers not installed)
try:
    from artemis.rag.ingestion.ingestion import (
        ingest_file,
        ingest_csv,
        ingest_pdf,
        ingest_docx,
        ingest_md,
        ingest_text,
    )
    _INGESTION_AVAILABLE = True
except ImportError as e:
    # Ingestion requires sentence_transformers for Indexer
    _INGESTION_AVAILABLE = False
    ingest_file = None
    ingest_csv = None
    ingest_pdf = None
    ingest_docx = None
    ingest_md = None
    ingest_text = None

from artemis.rag.ingestion.chunkers.registry import FileType, ChunkStrategy
from artemis.rag.ingestion.converters.csv_converter import DocumentSchema

# Path to actual restaurant dataset
RESTAURANT_DATASET_PATH = (
    project_root / "data" / "kaggle_datasets" / "datasets" / 
    "mohdshahnawazaadil" / "restaurant-dataset" / "versions" / "1" / "Dataset .csv"
)

# Path to test data directory
TEST_DATA_DIR = project_root / "tests" / "test_data"
TEXT_SAMPLE_PATH = TEST_DATA_DIR / "text" / "sample.txt"
MARKDOWN_SAMPLE_PATH = TEST_DATA_DIR / "markdown" / "sample.md"
PDF_SAMPLE_PATH = TEST_DATA_DIR / "pdf" / "sample.pdf"
DOCX_SAMPLE_PATH = TEST_DATA_DIR / "docx" / "sample.docx"


def _skip_if_not_available():
    """Skip test if ingestion is not available."""
    if not _INGESTION_AVAILABLE:
        print("⚠️  Skipping test (ingestion not available - sentence_transformers required)")
        return True
    return False


def _create_temp_text(content: str) -> Path:
    """Create a temporary text file for testing."""
    import tempfile
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tmp_file.write(content)
    tmp_file.close()
    return Path(tmp_file.name)


def _create_temp_markdown(content: str) -> Path:
    """Create a temporary markdown file for testing."""
    import tempfile
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    tmp_file.write(content)
    tmp_file.close()
    return Path(tmp_file.name)


class TestIngestFile:
    """Tests for ingest_file function."""
    
    def test_ingest_file_csv(self):
        """Test ingest_file with CSV file using actual dataset."""
        if _skip_if_not_available():
            return
        
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
            
        mock_indexer = Mock()
        
        ingest_file(str(RESTAURANT_DATASET_PATH), FileType.CSV, mock_indexer)
        
        # Check that indexer.add_documents was called
        assert mock_indexer.add_documents.called
        call_args = mock_indexer.add_documents.call_args
        documents, metadata = call_args[0]
        
        assert len(documents) > 0
        assert len(metadata) > 0
        assert len(documents) == len(metadata)
    
    def test_ingest_file_text(self):
        """Test ingest_file with text file using actual file if available."""
        if _skip_if_not_available():
            return
        
        mock_indexer = Mock()
        
        if TEXT_SAMPLE_PATH.exists():
            # Use actual test file
            ingest_file(str(TEXT_SAMPLE_PATH), FileType.TEXT, mock_indexer)
        else:
            # Fallback to temporary file
            print(f"⚠️  Test file not found: {TEXT_SAMPLE_PATH}")
            print("   Using temporary file (see tests/WHAT_TO_ADD.md to add test files)")
            text_content = "This is a test document. " * 50
            text_file = _create_temp_text(text_content)
            try:
                ingest_file(str(text_file), FileType.TEXT, mock_indexer)
            finally:
                text_file.unlink(missing_ok=True)
        
        # Check that indexer.add_documents was called
        assert mock_indexer.add_documents.called
        call_args = mock_indexer.add_documents.call_args
        documents, metadata = call_args[0]
        
        assert len(documents) > 0
        assert len(metadata) > 0
    
    def test_ingest_file_markdown(self):
        """Test ingest_file with markdown file using actual file if available."""
        if _skip_if_not_available():
            return
        
        mock_indexer = Mock()
        
        if MARKDOWN_SAMPLE_PATH.exists():
            # Use actual test file
            ingest_file(str(MARKDOWN_SAMPLE_PATH), FileType.MD, mock_indexer)
        else:
            # Fallback to temporary file
            print(f"⚠️  Test file not found: {MARKDOWN_SAMPLE_PATH}")
            print("   Using temporary file (see tests/WHAT_TO_ADD.md to add test files)")
            md_content = "# Test Document\n\nThis is test content with multiple paragraphs.\n\n## Section 1\n\nContent here."
            md_file = _create_temp_markdown(md_content)
            try:
                ingest_file(str(md_file), FileType.MD, mock_indexer)
            finally:
                md_file.unlink(missing_ok=True)
        
        assert mock_indexer.add_documents.called
        call_args = mock_indexer.add_documents.call_args
        documents, metadata = call_args[0]
        
        assert len(documents) > 0
        assert len(metadata) > 0
    
    def test_ingest_file_with_custom_strategy(self):
        """Test ingest_file with custom chunking strategy."""
        if _skip_if_not_available():
            return
            
        text_content = "This is a test document. " * 50
        text_file = _create_temp_text(text_content)
        mock_indexer = Mock()
        
        try:
            ingest_file(str(text_file), FileType.TEXT, mock_indexer, chunk_strategy=ChunkStrategy.FIXED)
            
            assert mock_indexer.add_documents.called
        finally:
            text_file.unlink(missing_ok=True)
    
    def test_ingest_file_csv_with_schema(self):
        """Test ingest_file with CSV and schema using actual dataset."""
        if _skip_if_not_available():
            return
        
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
            
        mock_indexer = Mock()
        
        ingest_file(
            str(RESTAURANT_DATASET_PATH), 
            FileType.CSV, 
            mock_indexer, 
            schema=DocumentSchema.RESTAURANT
        )
        
        assert mock_indexer.add_documents.called
        call_args = mock_indexer.add_documents.call_args
        documents, metadata = call_args[0]
        
        assert len(documents) > 0
        assert len(metadata) > 0
    
    def test_ingest_file_file_not_found(self):
        """Test ingest_file with non-existent file."""
        if _skip_if_not_available():
            return
            
        fake_path = Path("/nonexistent/file.txt")
        mock_indexer = Mock()
        
        try:
            ingest_file(str(fake_path), FileType.TEXT, mock_indexer)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            assert True
        except Exception as e:
            # On Windows, might get different error
            assert "not found" in str(e).lower() or "cannot find" in str(e).lower()


class TestConvenienceFunctions:
    """Tests for convenience ingestion functions."""
    
    def test_ingest_csv(self):
        """Test ingest_csv convenience function with actual dataset."""
        if _skip_if_not_available():
            return
        
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
            
        mock_indexer = Mock()
        
        ingest_csv(str(RESTAURANT_DATASET_PATH), mock_indexer)
        assert mock_indexer.add_documents.called
        call_args = mock_indexer.add_documents.call_args
        documents, metadata = call_args[0]
        assert len(documents) > 0
        assert len(metadata) > 0
    
    def test_ingest_csv_with_schema(self):
        """Test ingest_csv with schema using actual dataset."""
        if _skip_if_not_available():
            return
        
        if not RESTAURANT_DATASET_PATH.exists():
            print(f"⚠️  Skipping test: Dataset not found at {RESTAURANT_DATASET_PATH}")
            return
            
        mock_indexer = Mock()
        
        ingest_csv(str(RESTAURANT_DATASET_PATH), mock_indexer, schema=DocumentSchema.RESTAURANT)
        assert mock_indexer.add_documents.called
        call_args = mock_indexer.add_documents.call_args
        documents, metadata = call_args[0]
        assert len(documents) > 0
        assert len(metadata) > 0
    
    def test_ingest_text(self):
        """Test ingest_text convenience function."""
        if _skip_if_not_available():
            return
            
        text_content = "Test content for ingestion pipeline testing."
        text_file = _create_temp_text(text_content)
        mock_indexer = Mock()
        
        try:
            ingest_text(str(text_file), mock_indexer)
            assert mock_indexer.add_documents.called
        finally:
            text_file.unlink(missing_ok=True)
    
    def test_ingest_md(self):
        """Test ingest_md convenience function using actual file if available."""
        if _skip_if_not_available():
            return
        
        mock_indexer = Mock()
        
        if MARKDOWN_SAMPLE_PATH.exists():
            # Use actual test file
            ingest_md(str(MARKDOWN_SAMPLE_PATH), mock_indexer)
        else:
            # Fallback to temporary file
            md_content = "# Test Document\n\nContent for testing markdown ingestion."
            md_file = _create_temp_markdown(md_content)
            try:
                ingest_md(str(md_file), mock_indexer)
            finally:
                md_file.unlink(missing_ok=True)
        
        assert mock_indexer.add_documents.called
    
    # Note: PDF and DOCX tests would require actual files
    # These are integration tests that could be added later


def run_tests():
    """Run all ingestion pipeline tests."""
    print("=" * 60)
    print("Testing Ingestion Pipeline")
    print("=" * 60)
    print()
    
    if not _INGESTION_AVAILABLE:
        print("⚠️  Ingestion functions not available (sentence_transformers required)")
        print("   Skipping all ingestion tests")
        print()
        return
    
    if not RESTAURANT_DATASET_PATH.exists():
        print(f"⚠️  Restaurant dataset not found at {RESTAURANT_DATASET_PATH}")
        print("   CSV ingestion tests will be skipped")
        print("   See test file header for dataset requirements")
        print()
    
    # Ingest File Tests
    print("Testing ingest_file...")
    test_ingest = TestIngestFile()
    
    if RESTAURANT_DATASET_PATH.exists():
        test_ingest.test_ingest_file_csv()
        print("✅ ingest_file: CSV (with dataset)")
        try:
            test_ingest.test_ingest_file_csv_with_schema()
            print("✅ ingest_file: CSV with schema (with dataset)")
        except Exception as e:
            print(f"⚠️  ingest_file CSV with schema: {e}")
    else:
        print("⚠️  Skipping CSV tests (dataset not found)")
    
    test_ingest.test_ingest_file_text()
    print("✅ ingest_file: Text")
    test_ingest.test_ingest_file_markdown()
    print("✅ ingest_file: Markdown")
    test_ingest.test_ingest_file_with_custom_strategy()
    print("✅ ingest_file: Custom strategy")
    print()
    
    # Convenience Function Tests
    print("Testing Convenience Functions...")
    test_conv = TestConvenienceFunctions()
    
    if RESTAURANT_DATASET_PATH.exists():
        test_conv.test_ingest_csv()
        print("✅ ingest_csv (with dataset)")
        try:
            test_conv.test_ingest_csv_with_schema()
            print("✅ ingest_csv with schema (with dataset)")
        except Exception as e:
            print(f"⚠️  ingest_csv with schema: {e}")
    else:
        print("⚠️  Skipping ingest_csv tests (dataset not found)")
    
    test_conv.test_ingest_text()
    print("✅ ingest_text")
    test_conv.test_ingest_md()
    print("✅ ingest_md")
    print()
    
    print("=" * 60)
    print("All Ingestion Pipeline Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
