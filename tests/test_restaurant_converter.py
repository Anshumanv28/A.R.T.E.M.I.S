"""
Test script for restaurant document converter.

Tests the document conversion pipeline:
1. Convert CSV to documents (saved to artemis_data/docs/ folder)
2. Verify files are created
3. Test retriever ingestion (reads files and deletes them)
"""

import os
import sys
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file from project root
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import directly from document_converter to avoid retriever dependency
from artemis.rag.document_converter import csv_to_documents, DocumentSchema

# Try to import retriever (optional for testing)
try:
    from artemis.rag.retrieval import Retriever, RetrievalMode
    RETRIEVER_AVAILABLE = True
except ImportError:
    RETRIEVER_AVAILABLE = False
    print("⚠️  Retriever not available (qdrant_client not installed)")
    print("   Will test document conversion only")
    print()

# Path to restaurant CSV (relative to project root)
CSV_PATH = project_root / "data" / "kaggle_datasets" / "datasets" / "mohdshahnawazaadil" / "restaurant-dataset" / "versions" / "1" / "Dataset .csv"


def get_save_to_disk_default():
    """Get default save_to_disk value from environment variable."""
    env_value = os.getenv("ARTEMIS_SAVE_DOCS_TO_DISK", "false").lower()
    return env_value in ("true", "1", "yes")


def test_conversion():
    """Test CSV to documents conversion."""
    print("=" * 60)
    print("Testing Restaurant Document Converter")
    print("=" * 60)
    
    # Check if CSV exists
    if not CSV_PATH.exists():
        print(f"❌ CSV file not found: {CSV_PATH}")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Project root: {project_root}")
        return None, None
    
    print(f"✅ CSV file found: {CSV_PATH}")
    print()
    
    # Test 1: Convert with RESTAURANT schema (respects ARTEMIS_SAVE_DOCS_TO_DISK env var)
    save_to_disk = get_save_to_disk_default()
    mode_str = "file-based (saves to artemis_data/docs/ folder)" if save_to_disk else "in-memory"
    print(f"Test 1: Converting CSV to documents ({mode_str})")
    print(f"   Using ARTEMIS_SAVE_DOCS_TO_DISK={os.getenv('ARTEMIS_SAVE_DOCS_TO_DISK', 'false')}")
    print("-" * 60)
    try:
        result = csv_to_documents(
            str(CSV_PATH),
            schema=DocumentSchema.RESTAURANT,
            save_to_disk=save_to_disk
        )
        
        if save_to_disk:
            doc_paths, metadata_path = result
        else:
            docs, metadata = result
            # For in-memory mode, we'll return None, None to skip file-based tests
            print(f"✅ Conversion successful (in-memory mode)!")
            print(f"   Documents: {len(docs)}")
            print(f"   Metadata entries: {len(metadata)}")
            print()
            print("Sample document:")
            print("-" * 60)
            print(docs[0][:200] + "..." if len(docs[0]) > 200 else docs[0])
            print()
            return None, None  # Skip file-based tests in in-memory mode
        
        print(f"✅ Conversion successful!")
        print(f"   Documents created: {len(doc_paths)}")
        print(f"   Metadata file: {metadata_path}")
        print()
        
        # Verify files exist
        print("Verifying files exist:")
        for i, doc_path in enumerate(doc_paths[:3]):  # Check first 3
            if Path(doc_path).exists():
                size = Path(doc_path).stat().st_size
                print(f"   ✅ {Path(doc_path).name} ({size} bytes)")
            else:
                print(f"   ❌ {doc_path} not found")
        
        if len(doc_paths) > 3:
            print(f"   ... and {len(doc_paths) - 3} more files")
        
        if Path(metadata_path).exists():
            print(f"   ✅ {Path(metadata_path).name} exists")
        else:
            print(f"   ❌ {metadata_path} not found")
        
        print()
        
        # Show sample document
        if doc_paths:
            print("Sample document (first file):")
            print("-" * 60)
            with open(doc_paths[0], "r", encoding="utf-8") as f:
                sample_doc = f.read()
            print(sample_doc[:200] + "..." if len(sample_doc) > 200 else sample_doc)
            print()
        
        # Show sample metadata
        if Path(metadata_path).exists():
            import json
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_dict = json.load(f)
            print("Sample metadata (first entry):")
            print("-" * 60)
            first_key = list(metadata_dict.keys())[0]
            print(f"Document ID: {first_key}")
            print(f"Metadata: {metadata_dict[first_key]}")
            print()
        
        return doc_paths, metadata_path
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_retriever_ingestion(doc_paths, metadata_path):
    """Test retriever ingestion (reads files and deletes them)."""
    if not doc_paths or not metadata_path:
        print("Skipping retriever test (conversion failed)")
        return
    
    if not RETRIEVER_AVAILABLE:
        print("Skipping retriever test (retriever not available)")
        return
    
    print("=" * 60)
    print("Test 2: Retriever Ingestion (reads files, deletes after)")
    print("=" * 60)
    
    # Check if Qdrant is configured
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping retriever test")
        print("   Set QDRANT_URL and QDRANT_API_KEY environment variables to test ingestion")
        print()
        from artemis.utils.paths import get_docs_dir
        print(f"Files will remain in {get_docs_dir()} folder for manual inspection")
        return
    
    try:
        print(f"Connecting to Qdrant: {qdrant_url}")
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            collection_name="test_restaurants",
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_key
        )
        
        print(f"✅ Retriever initialized")
        print(f"   Collection: test_restaurants")
        print()
        
        # Count files before ingestion
        from artemis.utils.paths import get_docs_dir
        docs_dir = get_docs_dir()
        files_before = len([p for p in docs_dir.glob("*.txt") if p.exists()])
        print(f"Files in {docs_dir} before ingestion: {files_before}")
        
        # Ingest documents (will delete files after)
        print("Ingesting documents...")
        retriever.add_documents(doc_paths, metadata_path)
        
        print("✅ Documents ingested successfully!")
        print()
        
        # Check files after ingestion
        files_after = len([p for p in docs_dir.glob("*.txt") if p.exists()])
        metadata_after = len([p for p in docs_dir.glob("*_metadata.json") if p.exists()])
        
        print(f"Files in {docs_dir} after ingestion:")
        print(f"   Document files: {files_after} (should be 0)")
        print(f"   Metadata files: {metadata_after} (should be 0)")
        
        if files_after == 0 and metadata_after == 0:
            print("✅ All files deleted after successful ingestion!")
        else:
            print("⚠️  Some files remain (ingestion may have failed)")
        
        print()
        
        # Test retrieval
        print("Test 3: Testing retrieval")
        print("-" * 60)
        results = retriever.retrieve("Italian restaurants in Mumbai with rating above 4", k=3)
        print(f"✅ Retrieved {len(results)} results")
        print()
        print("Top result:")
        if results:
            print(f"   Score: {results[0].get('score', 'N/A'):.4f}")
            print(f"   Text: {results[0].get('payload', {}).get('text', '')[:150]}...")
        
    except Exception as e:
        print(f"❌ Retriever test failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        from artemis.utils.paths import get_docs_dir
        print(f"Files remain in {get_docs_dir()} folder for debugging")


def test_in_memory_mode():
    """Test in-memory mode explicitly (overrides env var)."""
    print("=" * 60)
    print("Test 4: In-Memory Mode (explicit override)")
    print("=" * 60)
    
    try:
        # Explicitly set save_to_disk=False to test in-memory mode
        docs, metadata = csv_to_documents(
            str(CSV_PATH),
            schema=DocumentSchema.RESTAURANT,
            save_to_disk=False  # Explicit override
        )
        
        print(f"✅ In-memory conversion successful!")
        print(f"   Documents: {len(docs)}")
        print(f"   Metadata entries: {len(metadata)}")
        print()
        print("Sample document:")
        print("-" * 60)
        print(docs[0][:200] + "..." if len(docs[0]) > 200 else docs[0])
        print()
        print("Sample metadata:")
        print("-" * 60)
        print(metadata[0])
        
    except Exception as e:
        print(f"❌ In-memory test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Show current environment configuration
    env_save_to_disk = os.getenv("ARTEMIS_SAVE_DOCS_TO_DISK", "false")
    print("=" * 60)
    print("Test Configuration")
    print("=" * 60)
    print(f"ARTEMIS_SAVE_DOCS_TO_DISK: {env_save_to_disk}")
    print(f"Default mode: {'file-based' if get_save_to_disk_default() else 'in-memory'}")
    print()
    
    # Run tests
    doc_paths, metadata_path = test_conversion()
    
    # Only run file-based tests if we're in file mode
    if doc_paths:
        test_retriever_ingestion(doc_paths, metadata_path)
    
    # Always test in-memory mode explicitly
    test_in_memory_mode()
    
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)

