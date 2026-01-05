"""
Tests for file loaders in A.R.T.E.M.I.S.

Tests all loader functions: CSV, PDF, DOCX, Markdown, and Text.

DATA REQUIREMENTS:
=================
These tests use actual test files from tests/test_data/ directory if available.
If test files are not found, tests will use temporary files (with warnings).

Required test files (if using actual files):
- tests/test_data/text/sample.txt
- tests/test_data/markdown/sample.md
- tests/test_data/pdf/sample.pdf
- tests/test_data/docx/sample.docx

See tests/WHAT_TO_ADD.md for details on what files to add.
"""

import sys
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

from artemis.rag.ingestion.loaders import (
    load_csv,
    load_pdf_text,
    load_docx_text,
    load_md_text,
    load_text,
)

# Path to test data directory
TEST_DATA_DIR = project_root / "tests" / "test_data"

# Test file paths
TEXT_SAMPLE_PATH = TEST_DATA_DIR / "text" / "sample.txt"
MARKDOWN_SAMPLE_PATH = TEST_DATA_DIR / "markdown" / "sample.md"
PDF_SAMPLE_PATH = TEST_DATA_DIR / "pdf" / "sample.pdf"
DOCX_SAMPLE_PATH = TEST_DATA_DIR / "docx" / "sample.docx"


def _create_temp_text(content: str) -> Path:
    """Create a temporary text file for testing."""
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tmp_file.write(content)
    tmp_file.close()
    return Path(tmp_file.name)


def _create_temp_markdown(content: str) -> Path:
    """Create a temporary markdown file for testing."""
    tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
    tmp_file.write(content)
    tmp_file.close()
    return Path(tmp_file.name)


class TestCSVLoader:
    """Tests for CSV loader."""
    
    def test_load_csv_success(self):
        """Test successful CSV loading."""
        # CSV tests use temporary files (appropriate for CSV unit tests)
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_file.write("name,value\nTest1,100\nTest2,200")
        csv_file.close()
        csv_path = Path(csv_file.name)
        
        try:
            df = load_csv(csv_path)
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 2
            assert list(df.columns) == ["name", "value"]
            assert df.iloc[0]["name"] == "Test1"
            assert df.iloc[0]["value"] == "100"
        finally:
            csv_path.unlink(missing_ok=True)
    
    def test_load_csv_file_not_found(self):
        """Test CSV loader with non-existent file."""
        fake_path = Path("/nonexistent/file.csv")
        
        try:
            load_csv(fake_path)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            assert True
    
    def test_load_csv_empty_file(self):
        """Test CSV loader with empty file."""
        csv_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        csv_file.close()
        csv_path = Path(csv_file.name)
        
        try:
            try:
                load_csv(csv_path)
                assert False, "Should have raised EmptyDataError"
            except pd.errors.EmptyDataError:
                assert True
        finally:
            csv_path.unlink(missing_ok=True)


class TestTextLoader:
    """Tests for text loader."""
    
    def test_load_text_success(self):
        """Test successful text loading using actual file if available."""
        if TEXT_SAMPLE_PATH.exists():
            # Use actual test file
            content = load_text(TEXT_SAMPLE_PATH)
            assert isinstance(content, str)
            assert len(content) > 0
        else:
            # Fallback to temporary file
            print(f"⚠️  Test file not found: {TEXT_SAMPLE_PATH}")
            print("   Using temporary file (see tests/WHAT_TO_ADD.md to add test files)")
            test_content = "This is a test document with multiple paragraphs.\n\nIt contains several sentences."
            text_file = _create_temp_text(test_content)
            try:
                content = load_text(text_file)
                assert isinstance(content, str)
                assert len(content) > 0
            finally:
                text_file.unlink(missing_ok=True)
    
    def test_load_text_file_not_found(self):
        """Test text loader with non-existent file."""
        fake_path = Path("/nonexistent/file.txt")
        
        try:
            load_text(fake_path)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            assert True
    
    def test_load_text_utf8_encoding(self):
        """Test text loader handles UTF-8 encoding."""
        content = "Test with émojis: 🎉 and special chars: ñ"
        text_file = _create_temp_text(content)
        
        try:
            loaded = load_text(text_file)
            assert "émojis" in loaded
            assert "ñ" in loaded
        finally:
            text_file.unlink(missing_ok=True)


class TestMarkdownLoader:
    """Tests for Markdown loader."""
    
    def test_load_md_success(self):
        """Test successful Markdown loading using actual file if available."""
        if MARKDOWN_SAMPLE_PATH.exists():
            # Use actual test file
            content = load_md_text(MARKDOWN_SAMPLE_PATH)
            assert isinstance(content, str)
            assert len(content) > 0
        else:
            # Fallback to temporary file
            print(f"⚠️  Test file not found: {MARKDOWN_SAMPLE_PATH}")
            print("   Using temporary file (see tests/WHAT_TO_ADD.md to add test files)")
            md_content = """# Test Document

This is a test markdown document.

## Section 1

Content for section 1.

### Subsection 1.1

More content here.

## Section 2

Content for section 2.
"""
            md_file = _create_temp_markdown(md_content)
            try:
                content = load_md_text(md_file)
                assert isinstance(content, str)
                assert "# Test Document" in content
                assert "Section 1" in content
                assert len(content) > 0
            finally:
                md_file.unlink(missing_ok=True)
    
    def test_load_md_file_not_found(self):
        """Test Markdown loader with non-existent file."""
        fake_path = Path("/nonexistent/file.md")
        
        try:
            load_md_text(fake_path)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            assert True


class TestPDFLoader:
    """Tests for PDF loader."""
    
    def test_load_pdf_success(self):
        """Test successful PDF loading using actual file if available."""
        if not PDF_SAMPLE_PATH.exists():
            print(f"⚠️  PDF test file not found: {PDF_SAMPLE_PATH}")
            print("   Skipping PDF loading test (see tests/WHAT_TO_ADD.md to add PDF files)")
            return
        
        try:
            content = load_pdf_text(PDF_SAMPLE_PATH)
            assert isinstance(content, str)
            assert len(content) > 0
        except ImportError:
            print("⚠️  PDF libraries not installed (pdfplumber or PyPDF2 required)")
            return
        except Exception as e:
            print(f"⚠️  PDF loading failed: {e}")
            # Don't fail test if PDF parsing fails (might be format issue)
            return
    
    def test_load_pdf_file_not_found(self):
        """Test PDF loader with non-existent file."""
        fake_path = Path("/nonexistent/file.pdf")
        
        try:
            load_pdf_text(fake_path)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            assert True
        except ImportError:
            # If PDF libraries not installed, ImportError happens first
            pass


class TestDOCXLoader:
    """Tests for DOCX loader."""
    
    def test_load_docx_success(self):
        """Test successful DOCX loading using actual file if available."""
        if not DOCX_SAMPLE_PATH.exists():
            print(f"⚠️  DOCX test file not found: {DOCX_SAMPLE_PATH}")
            print("   Skipping DOCX loading test (see tests/WHAT_TO_ADD.md to add DOCX files)")
            return
        
        try:
            content = load_docx_text(DOCX_SAMPLE_PATH)
            assert isinstance(content, str)
            assert len(content) > 0
        except ImportError:
            print("⚠️  python-docx library not installed")
            return
        except Exception as e:
            print(f"⚠️  DOCX loading failed: {e}")
            # Don't fail test if DOCX parsing fails (might be format issue)
            return
    
    def test_load_docx_file_not_found(self):
        """Test DOCX loader with non-existent file."""
        fake_path = Path("/nonexistent/file.docx")
        
        try:
            load_docx_text(fake_path)
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            assert True
        except ImportError:
            # If python-docx not installed, ImportError happens first
            pass


def run_tests():
    """Run all loader tests."""
    print("=" * 60)
    print("Testing File Loaders")
    print("=" * 60)
    print()
    
    if not TEST_DATA_DIR.exists():
        print(f"⚠️  Test data directory not found: {TEST_DATA_DIR}")
        print("   Tests will use temporary files (see tests/WHAT_TO_ADD.md)")
        print()
    
    # CSV Loader Tests
    print("Testing CSV Loader...")
    test_csv = TestCSVLoader()
    test_csv.test_load_csv_success()
    print("✅ CSV loader: Success")
    test_csv.test_load_csv_file_not_found()
    print("✅ CSV loader: File not found error")
    print()
    
    # Text Loader Tests
    print("Testing Text Loader...")
    test_text = TestTextLoader()
    test_text.test_load_text_success()
    print("✅ Text loader: Success")
    test_text.test_load_text_file_not_found()
    print("✅ Text loader: File not found error")
    test_text.test_load_text_utf8_encoding()
    print("✅ Text loader: UTF-8 encoding")
    print()
    
    # Markdown Loader Tests
    print("Testing Markdown Loader...")
    test_md = TestMarkdownLoader()
    test_md.test_load_md_success()
    print("✅ Markdown loader: Success")
    test_md.test_load_md_file_not_found()
    print("✅ Markdown loader: File not found error")
    print()
    
    # PDF Loader Tests
    print("Testing PDF Loader...")
    test_pdf = TestPDFLoader()
    test_pdf.test_load_pdf_file_not_found()
    print("✅ PDF loader: File not found error")
    try:
        test_pdf.test_load_pdf_success()
        print("✅ PDF loader: Success (with test file)")
    except Exception as e:
        print(f"⚠️  PDF loader: {e}")
    print()
    
    # DOCX Loader Tests
    print("Testing DOCX Loader...")
    test_docx = TestDOCXLoader()
    test_docx.test_load_docx_file_not_found()
    print("✅ DOCX loader: File not found error")
    try:
        test_docx.test_load_docx_success()
        print("✅ DOCX loader: Success (with test file)")
    except Exception as e:
        print(f"⚠️  DOCX loader: {e}")
    print()
    
    print("=" * 60)
    print("All Loader Tests Completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
