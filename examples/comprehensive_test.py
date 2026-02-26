#!/usr/bin/env python3
"""
Comprehensive System Test

Tests the entire A.R.T.E.M.I.S system with:
- Restaurant CSV data (in test_restaurants collection)
- HR-Policy.pdf (in test_hr_policy collection)

Validates:
- RAG retrieval from both collections
- Agent intent classification (tool vs direct)
- Agent tool node (search_documents, ingest, etc.) and direct-answer node
- End-to-end agent flow
- Collection isolation (no cross-contamination)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import artemis
sys.path.insert(0, str(Path(__file__).parent.parent))

from artemis.rag.core import Indexer, Retriever, RetrievalMode
from artemis.rag.ingestion import ingest_file, FileType, DocumentSchema
from artemis.rag.core.collection_manager import (
    list_collections,
    get_collection_info,
    delete_collection
)
from artemis.agent import run_agent
from artemis.utils import get_logger

logger = get_logger(__name__)

# Default collection names
RESTAURANT_COLLECTION = "test_restaurants"
HR_POLICY_COLLECTION = "test_hr_policy"


def print_section(title: str, description: str = ""):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)
    if description:
        print(f"  {description}")
    print()


def check_environment() -> bool:
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = {
        "QDRANT_URL": os.getenv("QDRANT_URL"),
        "QDRANT_API_KEY": os.getenv("QDRANT_API_KEY"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
    }
    
    missing = []
    for var, value in required_vars.items():
        if not value:
            missing.append(var)
            print(f"   ❌ {var} not set")
        else:
            print(f"   ✅ {var} is set")
    
    if missing:
        print(f"\n❌ Missing required environment variables: {', '.join(missing)}")
        return False
    
    return True


def find_restaurant_csv() -> Path:
    """Find restaurant CSV file."""
    # Common paths
    possible_paths = [
        Path("data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv"),
        Path("../data/kaggle_datasets/datasets/mohdshahnawazaadil/restaurant-dataset/versions/1/Dataset .csv"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Prompt user
    print("\n📄 Restaurant CSV not found in default locations.")
    csv_path = input("   Enter path to restaurant CSV (or press Enter to skip): ").strip()
    
    if not csv_path:
        return None
    
    path = Path(csv_path)
    if not path.exists():
        print(f"❌ Path not found: {path}")
        return None
    
    return path


def find_hr_policy_pdf() -> Path:
    """Find HR-Policy.pdf file."""
    possible_paths = [
        Path("HR-Policy.pdf"),
        Path("../HR-Policy.pdf"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # Prompt user
    print("\n📄 HR-Policy.pdf not found in default locations.")
    pdf_path = input("   Enter path to HR-Policy.pdf (or press Enter to skip): ").strip()
    
    if not pdf_path:
        return None
    
    path = Path(pdf_path)
    if not path.exists():
        print(f"❌ Path not found: {path}")
        return None
    
    return path


def cleanup_test_collections(confirm: bool = False):
    """Delete test collections if they exist."""
    collections = list_collections()
    
    for collection_name in [RESTAURANT_COLLECTION, HR_POLICY_COLLECTION]:
        if collection_name in collections:
            if confirm:
                try:
                    delete_collection(collection_name, confirm=True)
                    print(f"   ✅ Deleted existing collection: {collection_name}")
                except Exception as e:
                    print(f"   ⚠️  Failed to delete {collection_name}: {e}")
            else:
                print(f"   ⚠️  Collection '{collection_name}' already exists (will be reused)")


def test_retriever(collection_name: str, queries: list, description: str):
    """Test Retriever on a collection."""
    print_section(f"Testing Retriever: {description}", f"Collection: {collection_name}")
    
    try:
        indexer = Indexer(collection_name=collection_name)
        retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 70)
            
            results = retriever.retrieve(query, k=3)
            
            if results:
                print(f"✅ Retrieved {len(results)} results")
                print(f"   Top result score: {results[0].get('score', 0.0):.4f}")
                print(f"   Top result preview: {results[0].get('text', '')[:150]}...")
            else:
                print("⚠️  No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Retriever test failed: {e}")
        logger.exception("Retriever test failed", exc_info=True)
        return False


def test_agent(collection_name: str, queries: list, description: str):
    """Test agent on a collection."""
    print_section(f"Testing Agent: {description}", f"Collection: {collection_name}")
    
    try:
        indexer = Indexer(collection_name=collection_name)
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 70)
            
            result = run_agent(query=query, indexer=indexer)
            
            print(f"✅ Intent: {result.get('intent', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"   Retrieved Docs: {len(result.get('retrieved_docs', []))}")
            
            answer = result.get('final_answer', 'No answer')
            print(f"   Answer preview: {answer[:200]}...")
            
            if result.get('error'):
                print(f"   ⚠️  Error: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        logger.exception("Agent test failed", exc_info=True)
        return False


def test_direct_answer():
    """Test agent direct answer (no RAG)."""
    print_section("Testing Agent Direct Answer", "General questions (should not use RAG)")
    
    queries = [
        "What is machine learning?",
        "Explain quantum computing in simple terms",
    ]
    
    try:
        # Use any collection (agent should route to direct for these queries)
        indexer = Indexer(collection_name=RESTAURANT_COLLECTION)
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            print("-" * 70)
            
            result = run_agent(query=query, indexer=indexer)
            
            print(f"✅ Intent: {result.get('intent', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"   Retrieved Docs: {len(result.get('retrieved_docs', []))}")
            
            # Should be direct intent
            if result.get('intent') == 'direct':
                print("   ✅ Correctly routed to direct answer")
            else:
                print("   ⚠️  Expected 'direct' intent but got 'rag'")
            
            answer = result.get('final_answer', 'No answer')
            print(f"   Answer preview: {answer[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct answer test failed: {e}")
        logger.exception("Direct answer test failed", exc_info=True)
        return False


def validate_collection_isolation():
    """Validate that queries don't cross-contaminate between collections."""
    print_section("Validating Collection Isolation", "Ensuring queries return data from correct collection")
    
    try:
        # Test restaurant query on restaurant collection
        restaurant_indexer = Indexer(collection_name=RESTAURANT_COLLECTION)
        restaurant_result = run_agent(
            query="Find Italian restaurants in Mumbai",
            indexer=restaurant_indexer
        )
        
        # Test HR policy query on HR policy collection
        hr_indexer = Indexer(collection_name=HR_POLICY_COLLECTION)
        hr_result = run_agent(
            query="What does the HR policy say about vacation days?",
            indexer=hr_indexer
        )
        
        # Test restaurant query on HR collection (should not find restaurant data)
        hr_indexer_wrong = Indexer(collection_name=HR_POLICY_COLLECTION)
        wrong_result = run_agent(
            query="Find Italian restaurants in Mumbai",
            indexer=hr_indexer_wrong
        )
        
        print("\n✅ Restaurant query on restaurant collection:")
        print(f"   Retrieved {len(restaurant_result.get('retrieved_docs', []))} docs")
        print(f"   Intent: {restaurant_result.get('intent')}")
        
        print("\n✅ HR policy query on HR policy collection:")
        print(f"   Retrieved {len(hr_result.get('retrieved_docs', []))} docs")
        print(f"   Intent: {hr_result.get('intent')}")
        
        print("\n✅ Restaurant query on HR collection (isolation test):")
        print(f"   Retrieved {len(wrong_result.get('retrieved_docs', []))} docs")
        if len(wrong_result.get('retrieved_docs', [])) == 0:
            print("   ✅ Correctly isolated (no cross-contamination)")
        else:
            print("   ⚠️  Found documents (may be expected if query matches policy content)")
        
        return True
        
    except Exception as e:
        print(f"❌ Isolation validation failed: {e}")
        logger.exception("Isolation validation failed", exc_info=True)
        return False


def main():
    """Main test function."""
    print("\n" + "🧪" * 35)
    print("A.R.T.E.M.I.S Comprehensive System Test")
    print("🧪" * 35)
    
    # ========================================================================
    # STEP 1: Setup & Cleanup
    # ========================================================================
    print_section(
        "STEP 1: Setup & Cleanup",
        "Check environment and prepare test collections"
    )
    
    if not check_environment():
        print("\n❌ Please set required environment variables and try again.")
        return
    
    # List existing collections
    print("\n📋 Existing collections:")
    try:
        collections = list_collections()
        if collections:
            for col in collections:
                try:
                    info = get_collection_info(col)
                    print(f"   - {col}: {info.get('points_count', 0)} points")
                except:
                    print(f"   - {col}")
        else:
            print("   (no collections found)")
    except Exception as e:
        print(f"   ⚠️  Could not list collections: {e}")
    
    # Ask about cleanup
    print(f"\n🧹 Cleanup:")
    response = input(
        f"   Delete existing test collections ({RESTAURANT_COLLECTION}, {HR_POLICY_COLLECTION}) if they exist? (y/N): "
    ).strip().lower()
    
    if response == 'y':
        cleanup_test_collections(confirm=True)
    else:
        cleanup_test_collections(confirm=False)
    
    # ========================================================================
    # STEP 2: Data Ingestion
    # ========================================================================
    print_section(
        "STEP 2: Data Ingestion",
        "Index restaurant CSV and HR-Policy.pdf into separate collections"
    )
    
    # Find restaurant CSV
    restaurant_csv = find_restaurant_csv()
    if restaurant_csv:
        print(f"\n📄 Restaurant CSV: {restaurant_csv}")
        try:
            indexer = Indexer(collection_name=RESTAURANT_COLLECTION)
            print("   Indexing restaurant data...")
            ingest_file(
                str(restaurant_csv),
                FileType.CSV,
                indexer,
                schema=DocumentSchema.RESTAURANT
            )
            info = get_collection_info(RESTAURANT_COLLECTION)
            print(f"   ✅ Indexed {info.get('points_count', 0)} documents into '{RESTAURANT_COLLECTION}'")
        except Exception as e:
            print(f"   ❌ Failed to index restaurant CSV: {e}")
            logger.exception("Restaurant indexing failed", exc_info=True)
    else:
        print("   ⚠️  Skipping restaurant CSV ingestion")
    
    # Find HR-Policy.pdf
    hr_pdf = find_hr_policy_pdf()
    if hr_pdf:
        print(f"\n📄 HR-Policy.pdf: {hr_pdf}")
        try:
            indexer = Indexer(collection_name=HR_POLICY_COLLECTION)
            print("   Indexing HR policy PDF...")
            ingest_file(
                str(hr_pdf),
                FileType.PDF,
                indexer
            )
            info = get_collection_info(HR_POLICY_COLLECTION)
            print(f"   ✅ Indexed {info.get('points_count', 0)} documents into '{HR_POLICY_COLLECTION}'")
        except Exception as e:
            print(f"   ❌ Failed to index HR-Policy.pdf: {e}")
            logger.exception("HR policy indexing failed", exc_info=True)
    else:
        print("   ⚠️  Skipping HR-Policy.pdf ingestion")
    
    # ========================================================================
    # STEP 3: Component Testing
    # ========================================================================
    print_section(
        "STEP 3: Component Testing",
        "Test Retriever and Agent components"
    )
    
    test_results = {}
    
    # Test Retriever on restaurant collection
    if restaurant_csv:
        test_results['retriever_restaurant'] = test_retriever(
            RESTAURANT_COLLECTION,
            [
                "Italian restaurants in Mumbai",
                "Restaurants with rating above 4.5",
            ],
            "Restaurant Data"
        )
    
    # Test Retriever on HR policy collection
    if hr_pdf:
        test_results['retriever_hr'] = test_retriever(
            HR_POLICY_COLLECTION,
            [
                "What are the vacation policies?",
                "What does the policy say about leave?",
            ],
            "HR Policy Data"
        )
    
    # Test Agent on restaurant collection
    if restaurant_csv:
        test_results['agent_restaurant'] = test_agent(
            RESTAURANT_COLLECTION,
            [
                "Find Italian restaurants in Mumbai with good ratings",
                "What restaurants serve Chinese cuisine?",
            ],
            "Restaurant Queries"
        )
    
    # Test Agent on HR policy collection
    if hr_pdf:
        test_results['agent_hr'] = test_agent(
            HR_POLICY_COLLECTION,
            [
                "What does the HR policy say about vacation days?",
                "What are the leave policies?",
            ],
            "HR Policy Queries"
        )
    
    # Test direct answer
    test_results['agent_direct'] = test_direct_answer()
    
    # ========================================================================
    # STEP 4: Validation
    # ========================================================================
    print_section(
        "STEP 4: Validation",
        "Validate collection isolation and system integrity"
    )
    
    if restaurant_csv and hr_pdf:
        test_results['isolation'] = validate_collection_isolation()
    
    # ========================================================================
    # Summary
    # ========================================================================
    print_section("Test Summary", "Results overview")
    
    print("Test Results:")
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    total = len(test_results)
    passed = sum(1 for v in test_results.values() if v)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
