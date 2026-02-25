#!/usr/bin/env python3
"""
Quick PDF RAG Test - Non-Interactive Version

A simple script to quickly test PDF ingestion and retrieval.
Modify the PDF_PATH variable to point to your PDF file.

Usage:
    python examples/pdf_rag_quick_test.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from artemis.rag.core import Indexer, Retriever, RetrievalMode
from artemis.rag.ingestion import ingest_pdf

# ============================================================================
# CONFIGURATION - Modify these values
# ============================================================================

# Qdrant configuration (uses environment variables if not set)
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")  # None for local Qdrant
COLLECTION_NAME = "pdf_test_collection"

# Path to your PDF file or folder (folder will ingest all PDFs inside)
PDF_PATH = Path("HR-Policy.pdf")  # Change this to your PDF file or folder path

# Test queries
TEST_QUERIES = [
    "What is the main topic?",
    "Summarize the key points",
    "What are the important details?",
]

# ============================================================================
# MAIN SCRIPT
# ============================================================================

def main():
    print("🚀 Quick PDF RAG Test")
    print("=" * 70)
    
    # Step 1: Resolve PDF files
    if not PDF_PATH.exists():
        print(f"❌ Path not found: {PDF_PATH}")
        print("   Please update PDF_PATH in the script to point to your PDF file or folder")
        return
    
    if PDF_PATH.is_dir():
        pdf_files = sorted(PDF_PATH.glob("*.pdf"))
    else:
        pdf_files = [PDF_PATH]
    
    if not pdf_files:
        print(f"❌ No PDF files found in: {PDF_PATH}")
        return
    
    print(f"✅ Found {len(pdf_files)} PDF file(s)")
    
    # Step 2: Create Indexer
    print(f"\n📦 Creating Indexer (collection: {COLLECTION_NAME})...")
    try:
        indexer = Indexer(
            qdrant_url=QDRANT_URL,
            qdrant_api_key=QDRANT_API_KEY,
            collection_name=COLLECTION_NAME
        )
        print("✅ Indexer created")
    except Exception as e:
        print(f"❌ Failed to create Indexer: {e}")
        return
    
    # Step 3: Ingest PDFs
    print(f"\n📥 Ingesting PDFs...")
    try:
        for pdf_file in pdf_files:
            print(f"   - {pdf_file}")
            ingest_pdf(pdf_file, indexer)
        collection_info = indexer.qdrant_client.get_collection(COLLECTION_NAME)
        print(f"✅ PDFs ingested! Total chunks: {collection_info.points_count}")
    except Exception as e:
        print(f"❌ Failed to ingest PDFs: {e}")
        return
    
    # Step 4: Create Retriever
    print(f"\n🔍 Creating Retriever...")
    try:
        retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
        print("✅ Retriever created")
    except Exception as e:
        print(f"❌ Failed to create Retriever: {e}")
        return
    
    # Step 5: Test queries
    print(f"\n🔎 Testing queries...")
    print("=" * 70)
    
    for query in TEST_QUERIES:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        try:
            results = retriever.retrieve(query, k=3)
            
            if not results:
                print("   No results found")
                continue
            
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                text = result.get('text', '')
                print(f"\n   Result {i} (Score: {score:.4f}):")
                print(f"   {text[:300]}{'...' if len(text) > 300 else ''}")
        
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
    
    print("\n" + "=" * 70)
    print("✅ Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
