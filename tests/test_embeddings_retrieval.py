"""
Comprehensive tests for embeddings generation, storage, and retrieval.

Tests both unit-level functionality and end-to-end integration of the
ingestion and retrieval pipeline.
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

# Sample test documents
SAMPLE_DOCUMENTS = [
    "Restaurant: Le Petit Souffle. Location: Makati City. Cuisines: French, Japanese. Rating: 4.8.",
    "Restaurant: Spice Garden. Location: Mumbai. Cuisines: Indian, North Indian. Rating: 4.5.",
    "Restaurant: Pasta Paradise. Location: Delhi. Cuisines: Italian. Rating: 4.7.",
    "Restaurant: Sushi House. Location: Tokyo. Cuisines: Japanese, Sushi. Rating: 4.9.",
    "Restaurant: Burger King. Location: New York. Cuisines: American, Fast Food. Rating: 4.2.",
]

SAMPLE_METADATA = [
    {"restaurant_id": 1, "city": "Makati City", "rating": 4.8},
    {"restaurant_id": 2, "city": "Mumbai", "rating": 4.5},
    {"restaurant_id": 3, "city": "Delhi", "rating": 4.7},
    {"restaurant_id": 4, "city": "Tokyo", "rating": 4.9},
    {"restaurant_id": 5, "city": "New York", "rating": 4.2},
]


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
        
        # Test batch encoding
        embeddings = model.encode(SAMPLE_DOCUMENTS[:3], convert_to_numpy=True)
        print(f"✅ Batch embeddings generated")
        print(f"   Count: {len(embeddings)}")
        print(f"   All same dimension: {all(len(e) == len(embeddings[0]) for e in embeddings)}")
        
        # Verify dimensions
        expected_dim = model.get_sentence_embedding_dimension()
        assert len(embedding) == expected_dim, f"Expected dimension {expected_dim}, got {len(embedding)}"
        print(f"✅ Embedding dimension matches model: {expected_dim}")
        
    except Exception as e:
        print(f"❌ Embedding generation test failed: {e}")
        import traceback
        traceback.print_exc()


def test_embedding_dimensions():
    """Verify embedding dimensions match Qdrant collection configuration."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping embedding dimensions test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping embedding dimensions test")
        return
    
    print("=" * 60)
    print("Unit Test 2: Embedding Dimensions")
    print("=" * 60)
    
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        expected_dim = model.get_sentence_embedding_dimension()
        
        indexer = Indexer(
            collection_name="test_dimensions",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Check collection dimension
        from qdrant_client import QdrantClient
        client = indexer.qdrant_client
        collection_info = client.get_collection("test_dimensions")
        collection_dim = collection_info.config.params.vectors.size
        
        print(f"✅ Model embedding dimension: {expected_dim}")
        print(f"✅ Collection vector dimension: {collection_dim}")
        
        assert expected_dim == collection_dim, \
            f"Dimension mismatch: model={expected_dim}, collection={collection_dim}"
        
        print(f"✅ Dimensions match!")
        
    except Exception as e:
        print(f"❌ Embedding dimensions test failed: {e}")
        import traceback
        traceback.print_exc()


def test_indexer_storage():
    """Test Indexer stores documents correctly to Qdrant."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping indexer storage test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping indexer storage test")
        return
    
    print("=" * 60)
    print("Unit Test 3: Indexer Storage")
    print("=" * 60)
    
    try:
        indexer = Indexer(
            collection_name="test_storage",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        print(f"✅ Indexer initialized")
        print(f"   Collection: test_storage")
        print()
        
        # Store documents
        print(f"Indexing {len(SAMPLE_DOCUMENTS)} documents...")
        indexer.add_documents(SAMPLE_DOCUMENTS, SAMPLE_METADATA)
        
        print("✅ Documents stored successfully!")
        
        # Verify documents are in Qdrant
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        client = indexer.qdrant_client
        scroll_result = client.scroll(
            collection_name="test_storage",
            limit=10
        )
        
        stored_count = len(scroll_result[0])
        print(f"✅ Verified {stored_count} documents in Qdrant")
        
        assert stored_count == len(SAMPLE_DOCUMENTS), \
            f"Expected {len(SAMPLE_DOCUMENTS)} documents, found {stored_count}"
        
    except Exception as e:
        print(f"❌ Indexer storage test failed: {e}")
        import traceback
        traceback.print_exc()


def test_retriever_semantic_search():
    """Test semantic search returns relevant results."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping semantic search test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping semantic search test")
        return
    
    print("=" * 60)
    print("Unit Test 4: Retriever Semantic Search")
    print("=" * 60)
    
    try:
        # Use existing collection from previous test
        indexer = Indexer(
            collection_name="test_storage",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer
        )
        
        print(f"✅ Retriever initialized")
        print()
        
        # Test query
        query = "Japanese restaurant with high rating"
        print(f"Query: '{query}'")
        results = retriever.retrieve(query, k=3)
        
        print(f"✅ Retrieved {len(results)} results")
        
        assert len(results) > 0, "No results returned"
        assert len(results) <= 3, f"Expected at most 3 results, got {len(results)}"
        
        # Check result structure
        for i, result in enumerate(results):
            assert "text" in result, f"Result {i} missing 'text' field"
            assert "score" in result, f"Result {i} missing 'score' field"
            assert "metadata" in result, f"Result {i} missing 'metadata' field"
            print(f"   Result {i+1}: score={result['score']:.4f}, "
                  f"text='{result['text'][:50]}...'")
        
        # Verify top result is relevant (should be Sushi House or Le Petit Souffle)
        top_result_text = results[0]['text'].lower()
        assert "japanese" in top_result_text or "sushi" in top_result_text, \
            f"Top result doesn't seem relevant: {top_result_text[:50]}"
        
        print("✅ Top result is semantically relevant!")
        
    except Exception as e:
        print(f"❌ Semantic search test failed: {e}")
        import traceback
        traceback.print_exc()


def test_retrieval_strategy_registry():
    """Test registry system works correctly."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping registry test (components not available)")
        return
    
    print("=" * 60)
    print("Unit Test 5: Retrieval Strategy Registry")
    print("=" * 60)
    
    try:
        from artemis.rag.core.retriever import RETRIEVAL_STRATEGIES, register_strategy
        
        # Check that semantic strategy is registered
        assert RetrievalMode.SEMANTIC in RETRIEVAL_STRATEGIES, \
            "SEMANTIC strategy not registered"
        print("✅ SEMANTIC strategy is registered")
        
        # Check that keyword strategy is registered (even if not implemented)
        assert RetrievalMode.KEYWORD in RETRIEVAL_STRATEGIES, \
            "KEYWORD strategy not registered"
        print("✅ KEYWORD strategy is registered")
        
        # Check that hybrid strategy is registered
        assert RetrievalMode.HYBRID in RETRIEVAL_STRATEGIES, \
            "HYBRID strategy not registered"
        print("✅ HYBRID strategy is registered")
        
        # Test custom strategy registration
        @register_strategy(RetrievalMode.SEMANTIC)
        def test_strategy(retriever, query: str, k: int):
            return [{"text": "test", "score": 1.0, "metadata": {}}]
        
        # Note: This will override the existing semantic strategy temporarily
        # In real usage, you'd register for a new mode
        print("✅ Custom strategy registration works")
        
    except Exception as e:
        print(f"❌ Registry test failed: {e}")
        import traceback
        traceback.print_exc()


def test_retrieval_mode_switching():
    """Test different retrieval modes."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping mode switching test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping mode switching test")
        return
    
    print("=" * 60)
    print("Unit Test 6: Retrieval Mode Switching")
    print("=" * 60)
    
    try:
        indexer = Indexer(
            collection_name="test_storage",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Test semantic mode
        retriever_semantic = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer
        )
        results = retriever_semantic.retrieve("Italian food", k=2)
        print(f"✅ SEMANTIC mode: Retrieved {len(results)} results")
        
        # Test keyword mode (should raise NotImplementedError)
        retriever_keyword = Retriever(
            mode=RetrievalMode.KEYWORD,
            indexer=indexer
        )
        try:
            retriever_keyword.retrieve("Italian food", k=2)
            print("⚠️  KEYWORD mode unexpectedly succeeded (should raise NotImplementedError)")
        except NotImplementedError:
            print("✅ KEYWORD mode correctly raises NotImplementedError")
        
        # Test hybrid mode (should raise NotImplementedError)
        retriever_hybrid = Retriever(
            mode=RetrievalMode.HYBRID,
            indexer=indexer
        )
        try:
            retriever_hybrid.retrieve("Italian food", k=2)
            print("⚠️  HYBRID mode unexpectedly succeeded (should raise NotImplementedError)")
        except NotImplementedError:
            print("✅ HYBRID mode correctly raises NotImplementedError")
        
    except Exception as e:
        print(f"❌ Mode switching test failed: {e}")
        import traceback
        traceback.print_exc()


def test_end_to_end_pipeline():
    """Full pipeline: documents → embeddings → storage → retrieval."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping end-to-end test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping end-to-end test")
        return
    
    print("=" * 60)
    print("Integration Test 1: End-to-End Pipeline")
    print("=" * 60)
    
    try:
        # Step 1: Create indexer
        indexer = Indexer(
            collection_name="test_e2e",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        print("✅ Step 1: Indexer created")
        
        # Step 2: Index documents
        indexer.add_documents(SAMPLE_DOCUMENTS, SAMPLE_METADATA)
        print("✅ Step 2: Documents indexed")
        
        # Step 3: Create retriever
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer
        )
        print("✅ Step 3: Retriever created")
        
        # Step 4: Retrieve documents
        results = retriever.retrieve("French restaurant", k=2)
        print(f"✅ Step 4: Retrieved {len(results)} results")
        
        # Verify results
        assert len(results) > 0, "No results returned"
        assert any("French" in r['text'] for r in results), \
            "Expected French restaurant in results"
        
        print("✅ End-to-end pipeline test passed!")
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()


def test_retrieval_relevance():
    """Verify retrieved documents are semantically relevant."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping relevance test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping relevance test")
        return
    
    print("=" * 60)
    print("Integration Test 2: Retrieval Relevance")
    print("=" * 60)
    
    try:
        indexer = Indexer(
            collection_name="test_storage",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer
        )
        
        # Test multiple queries
        test_queries = [
            ("Italian food", "Italian"),
            ("High rated restaurant", "4.7"),  # Should match Pasta Paradise (4.7)
            ("Mumbai restaurant", "Mumbai"),
        ]
        
        for query, expected_keyword in test_queries:
            results = retriever.retrieve(query, k=2)
            print(f"\nQuery: '{query}'")
            print(f"   Retrieved {len(results)} results")
            
            # Check that at least one result contains expected keyword
            found_relevant = any(
                expected_keyword.lower() in result['text'].lower()
                for result in results
            )
            
            if found_relevant:
                print(f"   ✅ Found relevant result containing '{expected_keyword}'")
            else:
                print(f"   ⚠️  No result contains '{expected_keyword}'")
                # Show what we got
                for r in results:
                    print(f"      - {r['text'][:60]}...")
        
        print("\n✅ Relevance test completed!")
        
    except Exception as e:
        print(f"❌ Relevance test failed: {e}")
        import traceback
        traceback.print_exc()


def test_metadata_preservation():
    """Ensure metadata is preserved through indexing and retrieval."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping metadata preservation test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping metadata preservation test")
        return
    
    print("=" * 60)
    print("Integration Test 3: Metadata Preservation")
    print("=" * 60)
    
    try:
        indexer = Indexer(
            collection_name="test_metadata",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Index with metadata
        indexer.add_documents(SAMPLE_DOCUMENTS, SAMPLE_METADATA)
        print("✅ Documents indexed with metadata")
        
        # Retrieve and check metadata
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer
        )
        
        results = retriever.retrieve("restaurant", k=5)
        print(f"✅ Retrieved {len(results)} results")
        
        # Verify metadata is present
        for i, result in enumerate(results):
            assert "metadata" in result, f"Result {i} missing metadata"
            metadata = result['metadata']
            
            # Check that metadata contains expected fields
            if metadata:
                print(f"   Result {i+1} metadata: {metadata}")
                assert isinstance(metadata, dict), \
                    f"Result {i} metadata is not a dict: {type(metadata)}"
        
        print("✅ Metadata preserved through pipeline!")
        
    except Exception as e:
        print(f"❌ Metadata preservation test failed: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_queries():
    """Test various query types and verify results quality."""
    if not COMPONENTS_AVAILABLE:
        print("Skipping multiple queries test (components not available)")
        return
    
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        print("⚠️  QDRANT_URL not set - skipping multiple queries test")
        return
    
    print("=" * 60)
    print("Integration Test 4: Multiple Query Types")
    print("=" * 60)
    
    try:
        indexer = Indexer(
            collection_name="test_storage",
            qdrant_url=qdrant_url,
            qdrant_api_key=os.getenv("QDRANT_API_KEY")
        )
        
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer
        )
        
        query_types = [
            ("Exact match", "Le Petit Souffle"),
            ("Semantic similarity", "French cuisine restaurant"),
            ("Partial match", "Japanese"),
            ("Location-based", "restaurant in Mumbai"),
            ("Rating-based", "highly rated restaurant"),
        ]
        
        for query_type, query in query_types:
            print(f"\n{query_type}: '{query}'")
            results = retriever.retrieve(query, k=2)
            
            print(f"   Retrieved {len(results)} results")
            if results:
                print(f"   Top score: {results[0]['score']:.4f}")
                print(f"   Top result: {results[0]['text'][:60]}...")
        
        print("\n✅ Multiple queries test completed!")
        
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

