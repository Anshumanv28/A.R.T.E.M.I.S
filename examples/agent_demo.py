#!/usr/bin/env python3
"""
LangGraph Agent Demo

This script demonstrates how to use the A.R.T.E.M.I.S agent layer
to intelligently route queries between RAG and direct answer paths.

Prerequisites:
- Qdrant running (local or cloud)
- Documents already indexed in Qdrant
- GROQ_API_KEY set in environment (or OPENAI_API_KEY)
- Required packages installed
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import artemis
sys.path.insert(0, str(Path(__file__).parent.parent))

from artemis.agent import run_agent
from artemis.rag.core.indexer import Indexer
from artemis.utils import get_logger

logger = get_logger(__name__)


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
    
    optional_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    }
    
    missing = []
    for var, value in required_vars.items():
        if not value:
            missing.append(var)
            print(f"   ❌ {var} not set")
        else:
            print(f"   ✅ {var} is set")
    
    for var, value in optional_vars.items():
        if value:
            print(f"   ✅ {var} is set (optional)")
        else:
            print(f"   ⚠️  {var} not set (optional, using Groq)")
    
    if missing:
        print(f"\n❌ Missing required environment variables: {', '.join(missing)}")
        print("\n💡 Set them in your .env file or export them:")
        print("   export QDRANT_URL='your-qdrant-url'")
        print("   export QDRANT_API_KEY='your-api-key'")
        print("   export GROQ_API_KEY='your-groq-api-key'")
        return False
    
    return True


def main():
    """Main function demonstrating agent usage."""
    
    print("\n" + "🤖" * 35)
    print("A.R.T.E.M.I.S Agent Demo")
    print("🤖" * 35)
    
    # ========================================================================
    # STEP 1: Environment Check
    # ========================================================================
    print_section(
        "STEP 1: Environment Check",
        "Verify required environment variables are set"
    )
    
    if not check_environment():
        print("\n❌ Please set required environment variables and try again.")
        return
    
    # ========================================================================
    # STEP 2: Setup Indexer
    # ========================================================================
    print_section(
        "STEP 2: Setup Indexer",
        "Create indexer pointing to your Qdrant collection"
    )
    
    # Get collection name
    collection_name = input(
        "   Enter collection name (or press Enter for 'artemis_documents'): "
    ).strip()
    if not collection_name:
        collection_name = "artemis_documents"
    
    print(f"\n📋 Configuration:")
    print(f"   Collection: {collection_name}")
    print(f"   Qdrant URL: {os.getenv('QDRANT_URL')}")
    
    try:
        indexer = Indexer(collection_name=collection_name)
        print("   ✅ Indexer created successfully!")
    except Exception as e:
        print(f"   ❌ Failed to create indexer: {e}")
        logger.exception("Indexer creation failed", exc_info=True)
        return
    
    # ========================================================================
    # STEP 3: Test Queries
    # ========================================================================
    print_section(
        "STEP 3: Test Queries",
        "Run example queries to demonstrate agent routing"
    )
    
    # Example queries that should trigger different paths
    test_queries = [
        {
            "query": "What is machine learning?",
            "expected_intent": "direct",
            "description": "General question (should use direct path)"
        },
        {
            "query": "What does the document say about vacation policies?",
            "expected_intent": "rag",
            "description": "Document-specific question (should use RAG path)"
        },
        {
            "query": "Summarize the main topics",
            "expected_intent": "rag",
            "description": "Document summary request (should use RAG path)"
        },
    ]
    
    print("📝 Running example queries...\n")
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        expected = test_case["expected_intent"]
        description = test_case["description"]
        
        print("-" * 70)
        print(f"Query {i}: {query}")
        print(f"Expected: {expected} path ({description})")
        print("-" * 70)
        
        try:
            result = run_agent(query=query, indexer=indexer)
            
            # Display results
            print(f"\n✅ Answer:")
            print(f"   {result.get('final_answer', 'No answer generated')[:200]}...")
            
            print(f"\n📊 Agent State:")
            print(f"   Intent: {result.get('intent', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"   Retrieved Docs: {len(result.get('retrieved_docs', []))}")
            
            if result.get('error'):
                print(f"\n⚠️  Error: {result['error']}")
            
            # Check if intent matches expectation
            actual_intent = result.get('intent', 'unknown')
            if actual_intent == expected:
                print(f"\n✅ Intent matches expectation ({expected})")
            else:
                print(f"\n⚠️  Intent is {actual_intent}, expected {expected}")
            
            print()
            
        except Exception as e:
            print(f"\n❌ Query failed: {e}")
            logger.exception("Query failed", exc_info=True)
            print()
    
    # ========================================================================
    # STEP 4: Interactive Mode
    # ========================================================================
    print_section(
        "STEP 4: Interactive Mode",
        "Enter your own queries (or 'quit' to exit)"
    )
    
    print("Enter queries to test the agent (or 'quit' to exit):\n")
    
    while True:
        try:
            query = input("🔍 Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Run agent
            result = run_agent(query=query, indexer=indexer)
            
            # Display results
            print("\n" + "-" * 70)
            print("Answer:")
            print("-" * 70)
            print(result.get("final_answer", "No answer generated"))
            
            print(f"\n📊 Agent Details:")
            print(f"   Intent: {result.get('intent', 'unknown')}")
            print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
            
            retrieved_docs = result.get("retrieved_docs", [])
            if retrieved_docs:
                print(f"   Retrieved {len(retrieved_docs)} documents")
                print(f"   Top document score: {retrieved_docs[0].get('score', 0.0):.4f}")
            
            if result.get("error"):
                print(f"\n⚠️  Error: {result['error']}")
            
            print("\n" + "=" * 70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.exception("Error in interactive mode", exc_info=True)
            print()
    
    # ========================================================================
    # Summary
    # ========================================================================
    print_section(
        "Summary",
        "What we accomplished"
    )
    
    print("✅ Successfully demonstrated the A.R.T.E.M.I.S agent layer!")
    print("\n📚 Key Features:")
    print("   - Intelligent routing between RAG and direct answer paths")
    print("   - Automatic intent classification with confidence scores")
    print("   - Document retrieval with citations")
    print("   - Error handling and graceful fallbacks")
    print("\n📖 Next Steps:")
    print("   - See docs/AGENT_QUICKSTART.md for detailed usage")
    print("   - Explore custom configuration options")
    print("   - Try different queries to see routing behavior")
    print()


if __name__ == "__main__":
    main()
