#!/usr/bin/env python3
"""
Demo script to test queries on ingested restaurant data.

This script demonstrates how to query the A.R.T.E.M.I.S. RAG system
with custom queries and retrieve relevant restaurant information.

Run from project root: python examples/query_demo.py
"""

import os
from pathlib import Path
from artemis.rag.core import Indexer, Retriever, RetrievalMode

# Project root (so API key path works when run from examples/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
QDRANT_URL = os.getenv("QDRANT_URL") or input("Qdrant URL: ").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or (_PROJECT_ROOT / "ArtemisDB_api_key.txt").read_text().strip()

print("🔍 A.R.T.E.M.I.S. Query Demo")
print("=" * 60)
print()

# Create Indexer (reuse same config as ingestion)
print("1. Connecting to Qdrant...")
indexer = Indexer(
    qdrant_url=QDRANT_URL,
    qdrant_api_key=QDRANT_API_KEY,
    collection_name="artemis_documents"
)
print("   ✅ Connected to Qdrant")
print()

# Create Retriever (recommended: use same indexer for consistency)
print("2. Creating Retriever...")
retriever = Retriever(
    mode=RetrievalMode.SEMANTIC,
    indexer=indexer  # Uses same embedder and collection as ingestion
)
print("   ✅ Retriever ready")
print()

# Example queries for restaurant data
example_queries = [
    "Italian restaurants in Mumbai",
    "Cheap restaurants under 500 rupees",
    "Restaurants with excellent rating above 4.5",
    "Japanese restaurants with online delivery",
    "Best rated restaurants in Bangalore",
    "Restaurants with table booking available",
]

print("=" * 60)
print("📝 Example Queries")
print("=" * 60)
print()

# Test each example query
for i, query in enumerate(example_queries, 1):
    print(f"\n{i}. Query: \"{query}\"")
    print("-" * 60)
    
    try:
        results = retriever.retrieve(query, k=3)  # Top 3 results
        
        if results:
            for j, result in enumerate(results, 1):
                print(f"\n   Result {j} (Score: {result['score']:.4f}):")
                print(f"   {result['text']}")  # Full document text
                if 'metadata' in result and result['metadata']:
                    # Show key metadata fields
                    metadata = result['metadata']
                    if 'city' in metadata:
                        print(f"   City: {metadata['city']}")
                    if 'rating' in metadata and metadata['rating'] is not None:
                        print(f"   Rating: {metadata['rating']:.1f}")
                    if 'cost_for_two' in metadata and metadata['cost_for_two'] is not None:
                        print(f"   Cost for two: {metadata['cost_for_two']}")
                    if 'has_online_delivery' in metadata:
                        print(f"   Online delivery: {'Yes' if metadata['has_online_delivery'] else 'No'}")
                    if 'has_table_booking' in metadata:
                        print(f"   Table booking: {'Yes' if metadata['has_table_booking'] else 'No'}")
        else:
            print("   No results found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()

print("=" * 60)
print("🎉 Query Demo Complete!")
print()
print("You can also run custom queries interactively:")
print()
print("  from artemis.rag.core import Indexer, Retriever, RetrievalMode")
print("  indexer = Indexer(qdrant_url='...', qdrant_api_key='...')")
print("  retriever = Retriever(indexer=indexer)")
print("  results = retriever.retrieve('your query here', k=5)")
print()

# Interactive mode
print("=" * 60)
print("💬 Interactive Query Mode")
print("=" * 60)
print("Enter your queries (type 'exit' or 'quit' to stop)")
print()

while True:
    try:
        query = input("\nQuery: ").strip()
        
        if not query:
            continue
            
        if query.lower() in ['exit', 'quit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        print(f"\nSearching for: \"{query}\"")
        print("-" * 60)
        
        # Get number of results (optional)
        try:
            k = int(input("Number of results (default 5): ").strip() or "5")
        except ValueError:
            k = 5
        
        results = retriever.retrieve(query, k=k)
        
        if results:
            print(f"\nFound {len(results)} results:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. Score: {result['score']:.4f}")
                print(f"   {result['text']}")
                if 'metadata' in result and result['metadata']:
                    metadata = result['metadata']
                    print(f"   Metadata:")
                    if 'city' in metadata:
                        print(f"     - City: {metadata['city']}")
                    if 'rating' in metadata and metadata['rating'] is not None:
                        print(f"     - Rating: {metadata['rating']:.1f}")
                    if 'cost_for_two' in metadata and metadata['cost_for_two'] is not None:
                        print(f"     - Cost for two: {metadata['cost_for_two']}")
                    if 'has_online_delivery' in metadata:
                        print(f"     - Online delivery: {'Yes' if metadata['has_online_delivery'] else 'No'}")
                    if 'has_table_booking' in metadata:
                        print(f"     - Table booking: {'Yes' if metadata['has_table_booking'] else 'No'}")
                print()
        else:
            print("   No results found")
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
