#!/usr/bin/env python3
"""
Step-by-Step PDF RAG Integration Example

This script demonstrates how to:
1. Set up Qdrant connection
2. Create an Indexer
3. Ingest a PDF file
4. Create a Retriever
5. Query the RAG system

Prerequisites:
- Qdrant running (local or cloud)
- PDF file to test with
- Required packages: pdfplumber or PyPDF2 (for PDF loading)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import artemis
sys.path.insert(0, str(Path(__file__).parent.parent))

from artemis.rag.core import Indexer, Retriever, RetrievalMode
from artemis.rag.ingestion import ingest_pdf, FileType
from artemis.utils import get_logger

logger = get_logger(__name__)


def print_step(step_num: int, title: str, description: str = ""):
    """Print a formatted step header."""
    print("\n" + "=" * 70)
    print(f"STEP {step_num}: {title}")
    print("=" * 70)
    if description:
        print(f"  {description}")
    print()


def check_qdrant_connection(qdrant_url: str, qdrant_api_key: str = None) -> bool:
    """Check if Qdrant is accessible."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        # Try to list collections to verify connection
        client.get_collections()
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print("\n💡 Tips:")
        print("   - Make sure Qdrant is running")
        print("   - Check your QDRANT_URL environment variable")
        print("   - For local Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        print("   - For Qdrant Cloud: Get URL and API key from cloud.qdrant.io")
        return False


def check_pdf_libraries() -> bool:
    """Check if PDF libraries are installed."""
    try:
        import pdfplumber
        print("   ✅ pdfplumber is installed")
        return True
    except ImportError:
        try:
            import PyPDF2
            print("   ✅ PyPDF2 is installed")
            return True
        except ImportError:
            print("   ❌ No PDF libraries found")
            print("\n💡 Install a PDF library:")
            print("   pip install pdfplumber  # Recommended (better text extraction)")
            print("   # OR")
            print("   pip install PyPDF2")
            return False


def main():
    """Main function demonstrating PDF RAG integration."""
    
    print("\n" + "🚀" * 35)
    print("PDF RAG Integration - Step-by-Step Guide")
    print("🚀" * 35)
    
    # ========================================================================
    # STEP 1: Configuration
    # ========================================================================
    print_step(
        1,
        "Configuration Setup",
        "Set up Qdrant connection and PDF file path"
    )
    
    # Get Qdrant configuration from environment or use defaults
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = "pdf_documents"  # Collection name for this example
    
    print(f"📋 Configuration:")
    print(f"   Qdrant URL: {qdrant_url}")
    print(f"   Collection: {collection_name}")
    print(f"   API Key: {'***' if qdrant_api_key else 'None (local Qdrant)'}")
    
    # Check Qdrant connection
    print("\n🔍 Checking Qdrant connection...")
    if not check_qdrant_connection(qdrant_url, qdrant_api_key):
        fallback_url = "http://localhost:6333"
        if qdrant_url != fallback_url:
            print("\n⚠️  Primary Qdrant URL failed. Trying local Qdrant fallback...")
            if check_qdrant_connection(fallback_url, None):
                qdrant_url = fallback_url
                qdrant_api_key = None
                print("   ✅ Connected to local Qdrant!")
            else:
                print("\n❌ Please fix Qdrant connection and try again.")
                return
        else:
            print("\n❌ Please fix Qdrant connection and try again.")
            return
    
    print("   ✅ Qdrant connection successful!")
    
    # Get PDF file or folder path
    print("\n📄 PDF File Setup:")
    pdf_path = input("   Enter path to PDF file/folder (or press Enter to use 'HR-Policy.pdf'): ").strip()
    if not pdf_path:
        pdf_path = "./../HR-Policy.pdf"
    
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"\n❌ Path not found: {pdf_path}")
        print("\n💡 Tips:")
        print("   - Place your PDF files in the project directory")
        print("   - Or provide the full path to your PDF file/folder")
        return
    
    if pdf_path.is_dir():
        pdf_files = sorted(pdf_path.glob("*.pdf"))
    else:
        pdf_files = [pdf_path]
    
    if not pdf_files:
        print(f"\n❌ No PDF files found in: {pdf_path}")
        return
    
    print(f"   ✅ Found {len(pdf_files)} PDF file(s)")
    
    # Check PDF libraries
    print("\n🔍 Checking PDF libraries...")
    if not check_pdf_libraries():
        print("\n❌ Please install a PDF library and try again.")
        return
    
    # ========================================================================
    # STEP 2: Create Indexer
    # ========================================================================
    print_step(
        2,
        "Create Indexer",
        "The Indexer manages the embedding model and Qdrant connection"
    )
    
    print("📦 Creating Indexer...")
    print("   This will:")
    print("   - Load the embedding model (all-MiniLM-L6-v2)")
    print("   - Connect to Qdrant")
    print("   - Create/verify the collection exists")
    
    try:
        indexer = Indexer(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            collection_name=collection_name
        )
        print("   ✅ Indexer created successfully!")
        print(f"   📊 Collection: {collection_name}")
        print(f"   📊 Embedding model: {indexer.embedder.model_name}")
        print(f"   📊 Embedding dimensions: {indexer.embedder.get_dimension()}")
    except Exception as e:
        print(f"   ❌ Failed to create Indexer: {e}")
        logger.exception("Indexer creation failed", exc_info=True)
        return
    
    # ========================================================================
    # STEP 3: Ingest PDF File
    # ========================================================================
    print_step(
        3,
        "Ingest PDF File",
        "Load, chunk, and index the PDF into the vector database"
    )
    
    print("📥 Ingesting PDFs:")
    print("   This will:")
    print("   1. Load PDF text content")
    print("   2. Split into chunks (default: fixed-size chunks)")
    print("   3. Generate embeddings for each chunk")
    print("   4. Store in Qdrant vector database")
    
    try:
        # Ingest the PDF
        # You can customize chunking:
        # - chunk_strategy: ChunkStrategy.FIXED, ChunkStrategy.SEMANTIC, etc.
        # - chunk_size: Size of chunks (default: 1000)
        # - overlap: Overlap between chunks (default: 200)
        for pdf_file in pdf_files:
            print(f"   - {pdf_file}")
            ingest_pdf(
                path=pdf_file,
                indexer=indexer,
                # Optional: customize chunking
                # chunk_strategy=ChunkStrategy.SEMANTIC,
                # chunk_size=1500,
                # overlap=300
            )
        print("   ✅ PDF ingested successfully!")
        
        # Get collection info
        collection_info = indexer.qdrant_client.get_collection(collection_name)
        print(f"   📊 Total points in collection: {collection_info.points_count}")
        
    except Exception as e:
        print(f"   ❌ Failed to ingest PDF: {e}")
        logger.exception("PDF ingestion failed", exc_info=True)
        return
    
    # ========================================================================
    # STEP 4: Create Retriever
    # ========================================================================
    print_step(
        4,
        "Create Retriever",
        "The Retriever uses the same Indexer to ensure consistency"
    )
    
    print("🔍 Creating Retriever...")
    print("   Using the same Indexer ensures:")
    print("   - Same embedding model (critical for search to work)")
    print("   - Same Qdrant connection")
    print("   - Same collection")
    
    try:
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer  # Recommended: pass indexer for consistency
        )
        print("   ✅ Retriever created successfully!")
        print(f"   📊 Retrieval mode: {retriever.mode.value}")
    except Exception as e:
        print(f"   ❌ Failed to create Retriever: {e}")
        logger.exception("Retriever creation failed", exc_info=True)
        return
    
    # ========================================================================
    # STEP 5: Query the RAG System
    # ========================================================================
    print_step(
        5,
        "Query the RAG System",
        "Search for relevant information from the PDF"
    )
    
    print("🔎 Testing RAG queries...")
    print("   The retriever will:")
    print("   1. Embed your query using the same model")
    print("   2. Search for similar chunks in Qdrant")
    print("   3. Return top-k most relevant results")
    
    # Example queries
    test_queries = [
        "What is the main topic of this document?",
        "Summarize the key points",
    ]
    
    print("\n💬 Example queries (you can modify these):")
    for i, query in enumerate(test_queries, 1):
        print(f"   {i}. {query}")
    
    print("\n" + "-" * 70)
    print("Interactive Query Mode")
    print("-" * 70)
    print("Enter queries to search the PDF (or 'quit' to exit):\n")
    
    while True:
        query = input("🔍 Query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
        
        try:
            # Retrieve top-k results (default k=5)
            results = retriever.retrieve(query, k=5)
            
            if not results:
                print("   ❌ No results found")
                continue
            
            print(f"\n   ✅ Found {len(results)} results:\n")
            
            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                text = result.get('text', '')
                metadata = result.get('metadata', {})
                
                print(f"   📄 Result {i} (Score: {score:.4f}):")
                print(f"      {text[:200]}{'...' if len(text) > 200 else ''}")
                if metadata:
                    print(f"      Metadata: {metadata}")
                print()
            
        except Exception as e:
            print(f"   ❌ Query failed: {e}")
            logger.exception("Query failed", exc_info=True)
    
    # ========================================================================
    # Summary
    # ========================================================================
    print_step(
        6,
        "Summary",
        "What we accomplished"
    )
    
    print("✅ Successfully completed PDF RAG integration!")
    print("\n📋 What we did:")
    print("   1. ✅ Connected to Qdrant")
    print("   2. ✅ Created Indexer (manages embeddings and Qdrant)")
    print("   3. ✅ Ingested PDF file (loaded, chunked, indexed)")
    print("   4. ✅ Created Retriever (for semantic search)")
    print("   5. ✅ Queried the RAG system (retrieved relevant chunks)")
    
    print("\n📚 Key Takeaways:")
    print("   - Indexer: Manages persistent resources (embedder, Qdrant)")
    print("   - ingest_pdf(): Handles PDF loading, chunking, and indexing")
    print("   - Retriever: Uses same Indexer to ensure consistency")
    print("   - retrieve(): Performs semantic search and returns results")
    
    print("\n🔧 Next Steps:")
    print("   - Try different chunking strategies (SEMANTIC, FIXED, etc.)")
    print("   - Experiment with chunk_size and overlap parameters")
    print("   - Add more PDFs to the same collection")
    print("   - Try different retrieval modes (HYBRID, KEYWORD)")
    
    print("\n" + "🎉" * 35)
    print("PDF RAG Integration Complete!")
    print("🎉" * 35 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        logger.exception("Unexpected error", exc_info=True)
        sys.exit(1)
