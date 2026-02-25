"""
Entrypoint for running the agent interactively or programmatically.
"""

import sys
from typing import Optional
from artemis.agent.config import AgentConfig
from artemis.agent.graph import AgentGraph
from artemis.rag.core.retriever import Retriever, RetrievalMode
from artemis.rag.core.indexer import Indexer
from artemis.utils import get_logger

logger = get_logger(__name__)


def run_agent(
    query: str,
    retriever: Optional[Retriever] = None,
    indexer: Optional[Indexer] = None,
    config: Optional[AgentConfig] = None,
    collection_name: str = "artemis_documents"
) -> dict:
    """
    Run the agent with a query.
    
    Args:
        query: User query string
        retriever: Optional Retriever instance (will create one if not provided)
        indexer: Optional Indexer instance (used to create retriever if retriever not provided)
        config: Optional AgentConfig (uses defaults from env if not provided)
        collection_name: Collection name for retriever (if creating new retriever)
        
    Returns:
        Final agent state as dict
        
    Example:
        >>> from artemis.agent import run_agent
        >>> result = run_agent("What is the main topic?")
        >>> print(result["final_answer"])
    """
    # Create config if not provided
    if config is None:
        try:
            config = AgentConfig.from_env()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
    
    # Create retriever if not provided
    if retriever is None:
        if indexer is not None:
            logger.info("Creating retriever from indexer")
            retriever = Retriever(
                mode=RetrievalMode.SEMANTIC,
                indexer=indexer
            )
        else:
            logger.info("Creating indexer and retriever (requires env vars)")
            # Create indexer first (recommended approach - ensures embedder consistency)
            indexer = Indexer(collection_name=collection_name)
            retriever = Retriever(
                mode=RetrievalMode.SEMANTIC,
                indexer=indexer
            )
    
    # Create and run agent
    agent = AgentGraph(config=config, retriever=retriever)
    result = agent.invoke(query)
    
    return dict(result)


def main():
    """Interactive CLI entrypoint."""
    import argparse
    
    parser = argparse.ArgumentParser(description="A.R.T.E.M.I.S Agent CLI")
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to process (if not provided, runs in interactive mode)"
    )
    parser.add_argument(
        "--collection",
        default="artemis_documents",
        help="Qdrant collection name (default: artemis_documents)"
    )
    parser.add_argument(
        "--provider",
        choices=["groq", "openai"],
        help="LLM provider (default: from env or groq)"
    )
    parser.add_argument(
        "--model",
        help="Model name (default: from env or provider default)"
    )
    
    args = parser.parse_args()
    
    # Build config
    config_kwargs = {}
    if args.provider:
        config_kwargs["provider"] = args.provider
    if args.model:
        config_kwargs["model_name"] = args.model
    
    try:
        config = AgentConfig.from_env(**config_kwargs)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nMake sure to set GROQ_API_KEY or OPENAI_API_KEY in your .env file")
        sys.exit(1)
    
    # Create indexer and retriever
    try:
        # Create indexer first (recommended approach - ensures embedder consistency)
        indexer = Indexer(collection_name=args.collection)
        retriever = Retriever(
            mode=RetrievalMode.SEMANTIC,
            indexer=indexer
        )
    except Exception as e:
        print(f"❌ Failed to create retriever: {e}")
        print("\nMake sure QDRANT_URL and QDRANT_API_KEY are set in your .env file")
        sys.exit(1)
    
    # Interactive mode
    if not args.query:
        print("=" * 70)
        print("A.R.T.E.M.I.S Agent - Interactive Mode")
        print("=" * 70)
        print(f"Provider: {config.provider}")
        print(f"Model: {config.model_name}")
        print(f"Collection: {args.collection}")
        print("\nEnter queries (or 'quit' to exit):\n")
        
        while True:
            try:
                query = input("🔍 Query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                # Run agent
                result = run_agent(query, retriever=retriever, config=config)
                
                # Display results
                print("\n" + "-" * 70)
                print("Answer:")
                print("-" * 70)
                print(result.get("final_answer", "No answer generated"))
                
                # Show retrieved docs if RAG was used
                retrieved_docs = result.get("retrieved_docs", [])
                if retrieved_docs:
                    print(f"\n📚 Retrieved {len(retrieved_docs)} documents")
                    print(f"Intent: {result.get('intent', 'unknown')}")
                    print(f"Confidence: {result.get('confidence', 0.0):.2f}")
                
                if result.get("error"):
                    print(f"\n⚠️  Error: {result['error']}")
                
                print("\n" + "=" * 70 + "\n")
                
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logger.exception("Error in interactive mode", exc_info=True)
    
    else:
        # Single query mode
        try:
            result = run_agent(args.query, retriever=retriever, config=config)
            print(result.get("final_answer", "No answer generated"))
            
            if result.get("error"):
                print(f"\nError: {result['error']}", file=sys.stderr)
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            logger.exception("Error processing query", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
