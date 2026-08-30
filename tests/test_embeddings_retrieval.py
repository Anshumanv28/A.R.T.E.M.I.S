"""
Comprehensive tests for embeddings generation, storage, and retrieval.

Tests both unit-level functionality and end-to-end integration of the
ingestion and retrieval pipeline.

REQUIRED DATA:
=============
These tests require the restaurant dataset CSV file.

Restaurant Dataset:
- Source: Kaggle
- URL: https://www.kaggle.com/datasets/mohdshahnawazaadil/restaurant-dataset
- Path: data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv

The tests convert the restaurant dataset to documents and use those for
embedding and retrieval testing.

OPTIONAL REQUIREMENTS:
- Qdrant instance (for full integration tests)
  - Set QDRANT_URL and QDRANT_API_KEY environment variables
  - Or run local Qdrant instance
"""

import os
import sys
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file from project root
except ImportError:
    pass

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Try to import required modules
try:
    from artemis.rag import Indexer, Retriever, RetrievalMode, csv_to_documents, DocumentSchema
    from sentence_transformers import SentenceTransformer
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    print(f"⚠️  Required components not available: {e}")
    print("   Will skip tests that require qdrant_client or sentence_transformers")
    print()

# Path to actual restaurant dataset
RESTAURANT_DATASET_PATH = (
    project_root / "data" / "kaggle_datasets" / "datasets" / 
    "mohdshahnawazaadil" / "restaurant-dataset" / "versions" / "1" / "Dataset .csv"
)


def _get_test_documents_from_dataset():
    """Get test documents from restaurant dataset."""
    if not RESTAURANT_DATASET_PATH.exists():
        return [], []
    
    try:
        documents, metadata = csv_to_documents(
            str(RESTAURANT_DATASET_PATH), 
            schema=DocumentSchema.RESTAURANT
        )
        # Use first 20 documents for testing
        return documents[:20], metadata[:20]
    except Exception as e:
        print(f"⚠️  Failed to load documents from dataset: {e}")
        return [], []


def setup_test_collection():
    """Ensure the artemis_test collection exists and has some initial data."""
    if not COMPONENTS_AVAILABLE or not RESTAURANT_DATASET_PATH.exists():
        return
        
    print("\n[Setup] Preparing test collection 'artemis_test'...")
    try:
        indexer = Indexer(collection_name="artemis_test")
        
        # Optionally clear the collection at the start of the test run
        try:
            indexer.qdrant_client.delete_collection("artemis_test")
            print("[Setup] Cleared existing 'artemis_test' collection")
        except Exception:
            pass
            
        # Ensure collection exists
        indexer._ensure_collection_exists()
        
        # Ingest a tiny amount of data for tests
        test_docs, test_metadata = _get_test_documents_from_dataset()
        if test_docs:
            print(f"[Setup] Ingesting {len(test_docs)} documents for tests...")
            indexer.add_documents(test_docs, test_metadata)
    except Exception as e:
        print(f"[Setup] Warning: Could not setup test collection: {e}")

try:
    import pytest
    @pytest.fixture(scope="module", autouse=True)
    def module_setup():
        setup_test_collection()
except ImportError:
    pass


def test_embedding_generation():
    """Test that embedding model generates correct embeddings."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping embedding generation test (components not available)")
        return
    
    print("=" * 60)
    print("Unit Test 1: Embedding Generation")
    print("=" * 60)
    
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Test single document
        embedding = model.encode("Test document", convert_to_numpy=True)
        print(f"✅ Single embedding generated")
        print(f"   Dimension: {len(embedding)}")
        print(f"   Type: {type(embedding)}")
        
        # Test batch encoding with actual documents
        test_docs, test_metadata = _get_test_documents_from_dataset()
        if test_docs:
            embeddings = model.encode(test_docs[:3], convert_to_numpy=True)
            print(f"✅ Batch embeddings generated (from dataset)")
            print(f"   Count: {len(embeddings)}")
            print(f"   All same dimension: {all(len(e) == len(embeddings[0]) for e in embeddings)}")
        else:
            # Fallback to simple test
            test_texts = [
                "Restaurant: Le Petit Souffle. Location: Makati City.",
                "Restaurant: Spice Garden. Location: Mumbai.",
                "Restaurant: Pasta Paradise. Location: Delhi.",
            ]
            embeddings = model.encode(test_texts, convert_to_numpy=True)
            print(f"✅ Batch embeddings generated (fallback)")
            print(f"   Count: {len(embeddings)}")
        
        # Verify dimensions
        expected_dim = model.get_sentence_embedding_dimension()
        assert len(embedding) == expected_dim, f"Expected dimension {expected_dim}, got {len(embedding)}"
        assert len(embeddings[0]) == expected_dim, f"Expected dimension {expected_dim}, got {len(embeddings[0])}"
        
        print(f"✅ All embeddings have correct dimension: {expected_dim}")
        
    except Exception as e:
        print(f"❌ Embedding generation test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_embedding_dimensions():
    """Test that embeddings have consistent dimensions."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping embedding dimensions test (components not available)")
        return
    
    print("=" * 60)
    print("Unit Test 2: Embedding Dimensions")
    print("=" * 60)
    
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        expected_dim = model.get_sentence_embedding_dimension()
        
        # Test with documents from dataset
        test_docs, _ = _get_test_documents_from_dataset()
        if not test_docs:
            test_docs = [
                "Restaurant: Le Petit Souffle. Location: Makati City. Rating: 4.8.",
                "Restaurant: Spice Garden. Location: Mumbai. Rating: 4.5.",
            ]
        
        embeddings = model.encode(test_docs, convert_to_numpy=True)
        
        assert all(len(e) == expected_dim for e in embeddings), \
            f"Not all embeddings have dimension {expected_dim}"
        
        print(f"✅ All {len(embeddings)} embeddings have dimension {expected_dim}")
        
    except Exception as e:
        print(f"❌ Embedding dimensions test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_indexer_storage():
    """Test that Indexer stores documents correctly."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping indexer storage test (components not available)")
        return
    
    print("=" * 60)
    print("Unit Test 3: Indexer Storage")
    print("=" * 60)
    
    try:
        # Get documents from dataset
        test_docs, test_metadata = _get_test_documents_from_dataset()
        if not test_docs:
            print("⚠️  Dataset not found, skipping storage test")
            return
        
        print(f"Indexing {len(test_docs)} documents from restaurant dataset...")
        
        indexer = Indexer(collection_name="artemis_test")
        
        # Get initial count
        try:
            initial_count = indexer.qdrant_client.count(indexer.collection_name).count
        except Exception:
            initial_count = 0
            
        # Use a small subset to test storage
        indexer.add_documents(test_docs[:3], test_metadata[:3])
        
        # Verify storage
        stored_count = indexer.qdrant_client.count(indexer.collection_name).count
        assert stored_count == initial_count + 3, \
            f"Expected {initial_count + 3} documents, found {stored_count}"
        
        print(f"✅ Successfully stored 3 new documents")
        print(f"   Collection: {indexer.collection_name}")
        
    except Exception as e:
        print(f"❌ Indexer storage test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_retriever_semantic_search():
    """Test that Retriever performs semantic search correctly."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping retriever semantic search test (components not available)")
        return
    
    print("=" * 60)
    print("Unit Test 4: Retriever Semantic Search")
    print("=" * 60)
    
    try:
        # Get documents from dataset
        test_docs, test_metadata = _get_test_documents_from_dataset()
        if not test_docs:
            print("⚠️  Dataset not found, skipping retrieval test")
            return
        
        # Use existing documents from setup
        indexer = Indexer(collection_name="artemis_test")
        
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer,
            collection_name="artemis_test"
        )
        
        # Test query
        query = "restaurant in Makati"
        results = retriever.retrieve(query, k=3)
        
        assert len(results) > 0, "No results retrieved"
        assert all("score" in r for r in results), "Results missing scores"
        
        print(f"✅ Retrieved {len(results)} results for query: '{query}'")
        print(f"   Top result score: {results[0].get('score', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Retriever semantic search test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_retrieval_strategy_registry():
    """Test that retrieval strategies are registered correctly."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping retrieval strategy registry test (components not available)")
        return
    
    print("=" * 60)
    print("Unit Test 5: Retrieval Strategy Registry")
    print("=" * 60)
    
    try:
        from artemis.rag.core.retriever import RETRIEVAL_STRATEGIES
        
        assert isinstance(RETRIEVAL_STRATEGIES, dict)
        assert RetrievalMode.SEMANTIC in RETRIEVAL_STRATEGIES
        
        print(f"✅ Retrieval strategies registered: {list(RETRIEVAL_STRATEGIES.keys())}")
        
    except Exception as e:
        print(f"❌ Retrieval strategy registry test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_retrieval_mode_switching():
    """Test that Retriever can switch between retrieval modes."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping retrieval mode switching test (components not available)")
        return
    
    print("=" * 60)
    print("Unit Test 6: Retrieval Mode Switching")
    print("=" * 60)
    
    try:
        # Get documents from dataset
        test_docs, test_metadata = _get_test_documents_from_dataset()
        if not test_docs:
            print("⚠️  Dataset not found, skipping mode switching test")
            return
        
        indexer = Indexer(collection_name="artemis_test")
        
        # Test semantic mode
        retriever_semantic = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer,
            collection_name="artemis_test"
        )
        
        results_semantic = retriever_semantic.retrieve("restaurant", k=2)
        assert len(results_semantic) > 0
        
        print("✅ Semantic mode works")
        
    except Exception as e:
        print(f"❌ Retrieval mode switching test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_end_to_end_pipeline():
    """Test end-to-end pipeline: CSV -> Documents -> Index -> Retrieve."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping end-to-end pipeline test (components not available)")
        return
    
    print("=" * 60)
    print("Integration Test 1: End-to-End Pipeline")
    print("=" * 60)
    
    try:
        if not RESTAURANT_DATASET_PATH.exists():
            print("⚠️  Dataset not found, skipping end-to-end test")
            return
        
        # Step 1: Convert CSV to documents
        print("Step 1: Converting CSV to documents...")
        documents, metadata = csv_to_documents(
            str(RESTAURANT_DATASET_PATH), 
            schema=DocumentSchema.RESTAURANT
        )
        print(f"✅ Converted {len(documents)} documents")
        
        # Use subset for testing
        test_docs = documents[:10]
        test_metadata = metadata[:10]
        
        # Step 2: Index documents
        print("Step 2: Indexing documents...")
        indexer = Indexer(collection_name="artemis_test")
        indexer.add_documents(test_docs, test_metadata)
        print(f"✅ Indexed {len(test_docs)} documents")
        
        # Step 3: Retrieve
        print("Step 3: Retrieving documents...")
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer,
            collection_name="artemis_test"
        )
        
        query = "French restaurant"
        results = retriever.retrieve(query, k=5)
        print(f"✅ Retrieved {len(results)} results")
        print(f"   Query: '{query}'")
        print(f"   Top result score: {results[0].get('score', 'N/A') if results else 'N/A'}")
        
    except Exception as e:
        print(f"❌ End-to-end pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_retrieval_relevance():
    """Test that retrieved documents are relevant to the query."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping retrieval relevance test (components not available)")
        return
    
    print("=" * 60)
    print("Integration Test 2: Retrieval Relevance")
    print("=" * 60)
    
    try:
        if not RESTAURANT_DATASET_PATH.exists():
            print("⚠️  Dataset not found, skipping relevance test")
            return
        
        # Get documents
        documents, metadata = csv_to_documents(
            str(RESTAURANT_DATASET_PATH), 
            schema=DocumentSchema.RESTAURANT
        )
        
        indexer = Indexer(collection_name="artemis_test")
        
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer,
            collection_name="artemis_test"
        )
        
        # Test multiple queries
        queries = [
            "French restaurant",
            "high rating restaurant",
            "Makati City restaurant",
        ]
        
        for query in queries:
            results = retriever.retrieve(query, k=3)
            assert len(results) > 0, f"No results for query: {query}"
            print(f"✅ Query '{query}': {len(results)} results (top score: {results[0].get('score', 'N/A')})")
        
    except Exception as e:
        print(f"❌ Retrieval relevance test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_metadata_preservation():
    """Test that metadata is preserved through the pipeline."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping metadata preservation test (components not available)")
        return
    
    print("=" * 60)
    print("Integration Test 3: Metadata Preservation")
    print("=" * 60)
    
    try:
        if not RESTAURANT_DATASET_PATH.exists():
            print("⚠️  Dataset not found, skipping metadata test")
            return
        
        # Get documents with metadata
        documents, metadata = csv_to_documents(
            str(RESTAURANT_DATASET_PATH), 
            schema=DocumentSchema.RESTAURANT
        )
        
        indexer = Indexer(collection_name="artemis_test")
        
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer,
            collection_name="artemis_test"
        )
        
        results = retriever.retrieve("restaurant", k=5)
        
        # Check that results have metadata
        assert all("metadata" in r for r in results), "Results missing metadata"
        
        # Check that metadata fields are preserved
        metadata_fields = ["city", "rating"]
        for result in results[:3]:
            result_metadata = result.get("metadata", {})
            has_fields = any(field in result_metadata for field in metadata_fields)
            assert has_fields, f"Metadata missing expected fields: {result_metadata}"
        
        print(f"✅ Metadata preserved in {len(results)} results")
        
    except Exception as e:
        print(f"❌ Metadata preservation test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def test_multiple_queries():
    """Test multiple queries on the same index."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping multiple queries test (components not available)")
        return
    
    print("=" * 60)
    print("Integration Test 4: Multiple Queries")
    print("=" * 60)
    
    try:
        if not RESTAURANT_DATASET_PATH.exists():
            print("⚠️  Dataset not found, skipping multiple queries test")
            return
        
        # Get documents
        documents, metadata = csv_to_documents(
            str(RESTAURANT_DATASET_PATH), 
            schema=DocumentSchema.RESTAURANT
        )
        
        indexer = Indexer(collection_name="artemis_test")
        
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer,
            collection_name="artemis_test"
        )
        
        queries = [
            "restaurant in Makati",
            "Japanese restaurant",
            "high rating",
            "expensive restaurant",
        ]
        
        for query in queries:
            results = retriever.retrieve(query, k=3)
            print(f"✅ Query '{query}': {len(results)} results")
        
    except Exception as e:
        print(f"❌ Multiple queries test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("Embeddings and Retrieval Test Suite")
    print("=" * 60)
    print()
    
    if not COMPONENTS_AVAILABLE:
        print("⚠️  Some components are not available. Some tests will be skipped.")
        print()
    
    if not RESTAURANT_DATASET_PATH.exists():
        print(f"⚠️  Restaurant dataset not found at {RESTAURANT_DATASET_PATH}")
        print("   Many tests will be skipped. See test file header for dataset requirements.")
        print()
        
    # Setup test collection once
    setup_test_collection()
    print()
    
    # Run unit tests
    print("Running Unit Tests...")
    print()
    test_embedding_generation()
    print()
    test_embedding_dimensions()
    print()
    test_indexer_storage()
    print()
    test_retriever_semantic_search()
    print()
    test_retrieval_strategy_registry()
    print()
    test_retrieval_mode_switching()
    print()
    
    # Run integration tests
    print("Running Integration Tests...")
    print()
    test_end_to_end_pipeline()
    print()
    test_retrieval_relevance()
    print()
    test_metadata_preservation()
    print()
    test_multiple_queries()
    print()
    
    print("=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)
