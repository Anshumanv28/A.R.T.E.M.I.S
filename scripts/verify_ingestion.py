#!/usr/bin/env python3
"""
Verify that RAG_demo/techcorp_docs content (e.g. general-faqs.md) is in the collection
and can be retrieved. Run from project root with artemis-env activated.

Usage: python scripts/verify_ingestion.py
"""
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def main():
    from artemis.rag.core import Indexer, Retriever, RetrievalMode
    from artemis.rag.core.collection_manager import get_collection_info

    collection = "artemis_documents"
    print(f"Collection: {collection}")
    print("Connecting...")
    indexer = Indexer(collection_name=collection)
    retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)

    # Collection stats
    try:
        info = get_collection_info(collection)
        print(f"Collection info: {info}")
        points = info.get("points_count", "?")
    except Exception as e:
        print(f"Could not get collection info: {e}")
        info = {}
        points = "?"

    print(f"Points in collection: {points}")
    print()

    # Queries that should hit general-faqs.md "What products does TechCorp offer?"
    queries = [
        "What products does TechCorp offer?",
        "CloudSync Pro DataVault TechCorp products",
    ]
    product_markers = ["CloudSync Pro", "DataVault", "TechCorp AI Assistant"]

    for q in queries:
        print(f"Query: {q!r}")
        print("-" * 60)
        try:
            results = retriever.retrieve(q, k=15)
            print(f"Retrieved {len(results)} chunks.")
            found_products = False
            for i, r in enumerate(results):
                text = r.get("text", "")
                score = r.get("score", 0)
                has_marker = any(m in text for m in product_markers)
                if has_marker:
                    found_products = True
                    print(f"  [{i+1}] score={score:.4f} *** CONTAINS PRODUCT LIST ***")
                    print(f"      Preview: {text[:200].replace(chr(10), ' ')}...")
                else:
                    print(f"  [{i+1}] score={score:.4f} (no product list in chunk)")
            if not results:
                print("  No results returned.")
            elif not found_products:
                print("  WARNING: No retrieved chunk contained CloudSync Pro / DataVault / TechCorp AI Assistant.")
                print("  So general-faqs.md product section may not be in top-k or not in collection.")
            else:
                print("  OK: At least one chunk from product list was retrieved.")
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
        print()

    print("Done.")

if __name__ == "__main__":
    main()
