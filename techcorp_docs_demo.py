#!/usr/bin/env python3
"""
TechCorp Documentation Demo - Ingest and Query

This script ingests all markdown files from techcorp_docs folder
and then allows you to query them interactively.
"""

import os
from pathlib import Path
from artemis.rag.core import Indexer, Retriever, RetrievalMode
from artemis.rag.ingestion import ingest_file, FileType

# Get Qdrant config
QDRANT_URL = os.getenv("QDRANT_URL") or input("Qdrant URL: ").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or Path("ArtemisDB_api_key.txt").read_text().strip()

print("📚 TechCorp Documentation Demo")
print("=" * 60)
print()

# Create Indexer
print("1. Connecting to Qdrant...")
indexer = Indexer(
    qdrant_url=QDRANT_URL,
    qdrant_api_key=QDRANT_API_KEY,
    collection_name="techcorp_docs"
)
print("   ✅ Connected to Qdrant")
print()

# Find all markdown files in techcorp_docs
techcorp_docs_path = Path("RAG_demo/techcorp_docs")
md_files = list(techcorp_docs_path.rglob("*.md"))

if not md_files:
    print(f"❌ No markdown files found in {techcorp_docs_path}")
    exit(1)

print(f"2. Found {len(md_files)} markdown files to ingest")
print()

# Ingest each file
for i, md_file in enumerate(md_files, 1):
    # Ensure md_file is a Path object
    md_path = Path(md_file) if not isinstance(md_file, Path) else md_file
    
    # Get relative path for display (try relative to cwd, fallback to relative to techcorp_docs_path)
    try:
        relative_path = md_path.relative_to(Path.cwd())
    except ValueError:
        try:
            relative_path = md_path.relative_to(techcorp_docs_path)
        except ValueError:
            relative_path = md_path
    
    print(f"   [{i}/{len(md_files)}] Ingesting: {relative_path}")
    try:
        ingest_file(md_path, FileType.MD, indexer)
        print(f"      ✅ Successfully ingested")
    except Exception as e:
        print(f"      ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    print()

print("=" * 60)
print("✅ Ingestion Complete!")
print(f"Successfully ingested {len(md_files)} documents into collection 'techcorp_docs'")
print()

# Create Retriever with Hybrid Search
print("3. Creating Retriever with Hybrid Search...")
retriever = Retriever(
    mode=RetrievalMode.HYBRID,  # Use hybrid search (semantic + keyword)
    indexer=indexer
)
print("   ✅ Retriever ready (Hybrid: Semantic 70% + Keyword 30%)")
print()

# Example queries
example_queries = [
    "What are the CloudSync Pro features?",
    "What is the remote work policy?",
    "What are the benefits offered to employees?",
    "What was discussed in the Q3 planning meeting?",
    "How do I contact customer support?",
    "What are the pricing tiers for CloudSync Pro?",
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
                # Show first 300 chars of text
                text_preview = result['text'][:300] + "..." if len(result['text']) > 300 else result['text']
                print(f"   {text_preview}")
                
                # Show metadata if available
                if 'metadata' in result and result['metadata']:
                    metadata = result['metadata']
                    if 'source_type' in metadata:
                        print(f"   Source: {metadata['source_type']}")
                    if 'headers' in metadata:
                        print(f"   Section: {', '.join(metadata['headers'][:3])}")
        else:
            print("   No results found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()

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
                # Show first 400 chars
                text_preview = result['text'][:400] + "..." if len(result['text']) > 400 else result['text']
                print(f"   {text_preview}")
                
                if 'metadata' in result and result['metadata']:
                    metadata = result['metadata']
                    print(f"   Metadata:")
                    for key, value in metadata.items():
                        if key != 'text':  # Skip text field
                            print(f"     - {key}: {value}")
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
