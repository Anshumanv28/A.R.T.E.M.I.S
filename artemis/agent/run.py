"""
Entrypoint for running the agent interactively or programmatically.
"""

import sys
from typing import Optional

from artemis.agent.config import AgentConfig
from artemis.agent.context import load_system_context
from artemis.agent.graph import AgentGraph
from artemis.agent.supervisor import Supervisor
from artemis.agent.tools import ToolRegistry, build_rag_registry
from artemis.rag.core.retriever import Retriever, RetrievalMode, RETRIEVAL_STRATEGIES
from artemis.rag.core.indexer import Indexer
from artemis.utils import get_logger

logger = get_logger(__name__)

SYSTEM_DOCS_COLLECTION = "artemis_system_docs"
USER_COLLECTION = "artemis_user_docs"


def _build_registry_v2(
    config: AgentConfig,
    retriever=None,
    indexer=None,
    collection_name: str = "artemis_documents",
) -> ToolRegistry:
    """
    Build the RAG tool registry for v2 (Supervisor) once. Reuse the returned
    registry across multiple run_agent_v2 calls to avoid rebuilding Embedder/Indexers/Retrievers.
    """
    if retriever is None and indexer is None:
        logger.info("Building multi-collection setup (artemis_system_docs + artemis_user_docs)")
        from artemis.rag.core.embedder import Embedder
        embedder = Embedder()
        idx_system = Indexer(collection_name=SYSTEM_DOCS_COLLECTION, embedder=embedder)
        idx_user = Indexer(collection_name=USER_COLLECTION, embedder=embedder)
        indexers = {SYSTEM_DOCS_COLLECTION: idx_system, USER_COLLECTION: idx_user}
        bm25_available = False
        try:
            from artemis.rag.strategies.keyword import BM25_AVAILABLE
            bm25_available = BM25_AVAILABLE
        except (ImportError, Exception):
            pass
        retrievers_by_collection = {}
        for col_name, idx in indexers.items():
            retrievers_by_collection[col_name] = {}
            for mode in RETRIEVAL_STRATEGIES:
                if mode in (RetrievalMode.KEYWORD, RetrievalMode.HYBRID) and not bm25_available:
                    continue
                try:
                    r = Retriever(mode=mode, indexer=idx)
                    retrievers_by_collection[col_name][mode.value] = r
                except Exception as e:
                    logger.debug("Skipping %s %s: %s", col_name, mode.value, e)
            if "semantic" not in retrievers_by_collection[col_name]:
                retrievers_by_collection[col_name]["semantic"] = Retriever(mode=RetrievalMode.SEMANTIC, indexer=idx)
        llm_client_for_agentic = None
        try:
            if config.provider == "groq" and getattr(config, "groq_api_key", None):
                from artemis.agent.llm.groq_client import GroqClient
                llm_client_for_agentic = GroqClient(api_key=config.groq_api_key, model_name=config.model_name)
            elif config.provider == "openai" and getattr(config, "openai_api_key", None):
                from artemis.agent.llm.openai_client import OpenAIClient
                llm_client_for_agentic = OpenAIClient(api_key=config.openai_api_key, model_name=config.model_name)
        except Exception as e:
            logger.debug("Could not create LLM client for agentic chunking: %s", e)
        return build_rag_registry(
            retriever=None,
            indexer=None,
            default_k=config.retrieval_k,
            retrievers=None,
            llm_client_for_agentic=llm_client_for_agentic,
            indexers=indexers,
            retrievers_by_collection=retrievers_by_collection,
            default_collection=USER_COLLECTION,
        )
    # Single-collection path
    if retriever is None:
        if indexer is not None:
            logger.info("Creating retriever from indexer")
            retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
        else:
            logger.info("Creating indexer and retriever (requires env vars)")
            indexer = Indexer(collection_name=collection_name)
            retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
    elif indexer is None:
        indexer = getattr(retriever, "indexer", None)
    idx = indexer or getattr(retriever, "indexer", None)
    retrievers = {}
    bm25_available = False
    try:
        from artemis.rag.strategies.keyword import BM25_AVAILABLE
        bm25_available = BM25_AVAILABLE
    except (ImportError, Exception):
        pass
    for mode in RETRIEVAL_STRATEGIES:
        if mode in (RetrievalMode.KEYWORD, RetrievalMode.HYBRID) and (not bm25_available or idx is None):
            continue
        try:
            if mode == RetrievalMode.SEMANTIC and idx is None:
                r = retriever
            else:
                if idx is None:
                    continue
                r = Retriever(mode=mode, indexer=idx)
            retrievers[mode.value] = r
        except Exception as e:
            logger.debug("Skipping retrieval mode %s: %s", mode.value, e)
    if "semantic" not in retrievers:
        retrievers["semantic"] = retriever
    llm_client_for_agentic = None
    try:
        if config.provider == "groq" and getattr(config, "groq_api_key", None):
            from artemis.agent.llm.groq_client import GroqClient
            llm_client_for_agentic = GroqClient(api_key=config.groq_api_key, model_name=config.model_name)
        elif config.provider == "openai" and getattr(config, "openai_api_key", None):
            from artemis.agent.llm.openai_client import OpenAIClient
            llm_client_for_agentic = OpenAIClient(api_key=config.openai_api_key, model_name=config.model_name)
    except Exception as e:
        logger.debug("Could not create LLM client for agentic chunking: %s", e)
    return build_rag_registry(
        retriever,
        indexer=indexer,
        default_k=config.retrieval_k,
        retrievers=retrievers,
        llm_client_for_agentic=llm_client_for_agentic,
    )


def run_agent(
    query: str,
    retriever: Optional[Retriever] = None,
    indexer: Optional[Indexer] = None,
    config: Optional[AgentConfig] = None,
    collection_name: str = "artemis_documents",
    registry: Optional[ToolRegistry] = None,
) -> dict:
    """
    Run the agent with a query.

    Builds a tool registry with RAG tools (search, ingest, collection management)
    from the given retriever/indexer, or creates retriever and indexer when not provided.
    The planner chooses when to use tools (e.g. search_documents) vs answer directly.

    Args:
        query: User query string
        retriever: Optional Retriever (will create one if not provided)
        indexer: Optional Indexer (used to create retriever if retriever not provided)
        config: Optional AgentConfig (uses defaults from env if not provided)
        collection_name: Collection name for retriever when creating new retriever
        registry: Optional pre-built ToolRegistry; if provided, retriever/indexer are only used when registry is None to build a default one

    Returns:
        Final agent state as dict

    Example:
        >>> from artemis.agent import run_agent
        >>> result = run_agent("What is the main topic?")
        >>> print(result["final_answer"])
    """
    if config is None:
        try:
            config = AgentConfig.from_env()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise

    SYSTEM_DOCS_COLLECTION = "artemis_system_docs"
    USER_COLLECTION = "artemis_user_docs"

    if registry is None:
        if retriever is None and indexer is None:
            # Multi-collection: agent can switch between system docs and user data by task
            logger.info("Building multi-collection setup (artemis_system_docs + artemis_user_docs)")
            from artemis.rag.core.embedder import Embedder
            embedder = Embedder()
            idx_system = Indexer(collection_name=SYSTEM_DOCS_COLLECTION, embedder=embedder)
            idx_user = Indexer(collection_name=USER_COLLECTION, embedder=embedder)
            indexers = {SYSTEM_DOCS_COLLECTION: idx_system, USER_COLLECTION: idx_user}
            bm25_available = False
            try:
                from artemis.rag.strategies.keyword import BM25_AVAILABLE
                bm25_available = BM25_AVAILABLE
            except (ImportError, Exception):
                pass
            retrievers_by_collection = {}
            for col_name, idx in indexers.items():
                retrievers_by_collection[col_name] = {}
                for mode in RETRIEVAL_STRATEGIES:
                    if mode in (RetrievalMode.KEYWORD, RetrievalMode.HYBRID) and not bm25_available:
                        continue
                    try:
                        r = Retriever(mode=mode, indexer=idx)
                        retrievers_by_collection[col_name][mode.value] = r
                    except Exception as e:
                        logger.debug("Skipping %s %s: %s", col_name, mode.value, e)
                if "semantic" not in retrievers_by_collection[col_name]:
                    retrievers_by_collection[col_name]["semantic"] = Retriever(mode=RetrievalMode.SEMANTIC, indexer=idx)
            llm_client_for_agentic = None
            try:
                if config.provider == "groq" and getattr(config, "groq_api_key", None):
                    from artemis.agent.llm.groq_client import GroqClient
                    llm_client_for_agentic = GroqClient(api_key=config.groq_api_key, model_name=config.model_name)
                elif config.provider == "openai" and getattr(config, "openai_api_key", None):
                    from artemis.agent.llm.openai_client import OpenAIClient
                    llm_client_for_agentic = OpenAIClient(api_key=config.openai_api_key, model_name=config.model_name)
            except Exception as e:
                logger.debug("Could not create LLM client for agentic chunking: %s", e)
            registry = build_rag_registry(
                retriever=None,
                indexer=None,
                default_k=config.retrieval_k,
                retrievers=None,
                llm_client_for_agentic=llm_client_for_agentic,
                indexers=indexers,
                retrievers_by_collection=retrievers_by_collection,
                default_collection=USER_COLLECTION,
            )
            current_collection = None
        else:
            # Single-collection path
            if retriever is None:
                if indexer is not None:
                    logger.info("Creating retriever from indexer")
                    retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
                else:
                    logger.info("Creating indexer and retriever (requires env vars)")
                    indexer = Indexer(collection_name=collection_name)
                    retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
            elif indexer is None:
                indexer = getattr(retriever, "indexer", None)
            idx = indexer or getattr(retriever, "indexer", None)
            retrievers = {}
            bm25_available = False
            try:
                from artemis.rag.strategies.keyword import BM25_AVAILABLE
                bm25_available = BM25_AVAILABLE
            except (ImportError, Exception):
                pass
            for mode in RETRIEVAL_STRATEGIES:
                if mode in (RetrievalMode.KEYWORD, RetrievalMode.HYBRID) and (not bm25_available or idx is None):
                    continue
                try:
                    if mode == RetrievalMode.SEMANTIC and idx is None:
                        r = retriever
                    else:
                        if idx is None:
                            continue
                        r = Retriever(mode=mode, indexer=idx)
                    retrievers[mode.value] = r
                except Exception as e:
                    logger.debug("Skipping retrieval mode %s: %s", mode.value, e)
            if "semantic" not in retrievers:
                retrievers["semantic"] = retriever
            llm_client_for_agentic = None
            try:
                if config.provider == "groq" and getattr(config, "groq_api_key", None):
                    from artemis.agent.llm.groq_client import GroqClient
                    llm_client_for_agentic = GroqClient(api_key=config.groq_api_key, model_name=config.model_name)
                elif config.provider == "openai" and getattr(config, "openai_api_key", None):
                    from artemis.agent.llm.openai_client import OpenAIClient
                    llm_client_for_agentic = OpenAIClient(api_key=config.openai_api_key, model_name=config.model_name)
            except Exception as e:
                logger.debug("Could not create LLM client for agentic chunking: %s", e)
            registry = build_rag_registry(
                retriever,
                indexer=indexer,
                default_k=config.retrieval_k,
                retrievers=retrievers,
                llm_client_for_agentic=llm_client_for_agentic,
            )
            current_collection = None
            if indexer is not None and hasattr(indexer, "collection_name"):
                current_collection = indexer.collection_name
            elif retriever is not None and getattr(retriever, "collection_name", None):
                current_collection = retriever.collection_name
            else:
                current_collection = collection_name
    else:
        current_collection = None
    agent = AgentGraph(
        config=config,
        registry=registry,
        max_tool_steps=config.max_tool_steps,
        current_collection=current_collection,
    )
    result = agent.invoke(query)
    return dict(result)


def run_agent_v2(
    query: str,
    config: Optional[AgentConfig] = None,
    registry: Optional[ToolRegistry] = None,
    indexer=None,
    retriever=None,
    collection_name: str = "artemis_documents",
) -> dict:
    """
    Run the agent using the Supervisor + sub-agent architecture.
    Builds config and registry the same way as run_agent() when not provided.
    Pass a pre-built registry to reuse the RAG stack across multiple queries (e.g. interactive loop).
    Loads system context from the registry, creates a Supervisor, and dispatches the query.
    Returns the final agent state as a dict (same shape as run_agent).
    """
    if config is None:
        try:
            config = AgentConfig.from_env()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise

    if registry is None:
        registry = _build_registry_v2(config, retriever, indexer, collection_name)

    system_context = load_system_context(registry)
    supervisor = Supervisor(
        config=config,
        registry=registry,
        system_context=system_context,
    )
    result = supervisor.invoke(query)
    return dict(result)


def main():
    """Interactive CLI entrypoint."""
    import argparse

    parser = argparse.ArgumentParser(description="A.R.T.E.M.I.S Agent CLI")
    parser.add_argument(
        "query",
        nargs="?",
        help="Query to process (if not provided, runs in interactive mode)",
    )
    parser.add_argument(
        "--collection",
        default="artemis_documents",
        help="Qdrant collection name when using --single-collection (default: artemis_documents)",
    )
    parser.add_argument(
        "--single-collection",
        action="store_true",
        help="Use a single collection for all ingest and search (legacy). Default is multi-collection (artemis_system_docs + artemis_user_docs); agent chooses by task.",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Use Supervisor architecture (v2) instead of legacy AgentGraph (v1).",
    )
    parser.add_argument(
        "--provider",
        choices=["groq", "openai"],
        help="LLM provider (default: from env or groq)",
    )
    parser.add_argument(
        "--model",
        help="Model name (default: from env or provider default)",
    )

    args = parser.parse_args()

    config_kwargs = {}
    if args.provider:
        config_kwargs["provider"] = args.provider
    if args.model:
        config_kwargs["model_name"] = args.model

    try:
        config = AgentConfig.from_env(**config_kwargs)
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nMake sure to set GROQ_API_KEY or OPENAI_API_KEY in your .env file")
        sys.exit(1)

    # Default: multi-collection (artemis_system_docs + artemis_user_docs). If you don't use system docs, it behaves like single-collection; when you do, the agent uses system collection as context.
    indexer = None
    retriever = None
    if getattr(args, "single_collection", False):
        try:
            indexer = Indexer(collection_name=args.collection)
            retriever = Retriever(
                mode=RetrievalMode.SEMANTIC,
                indexer=indexer,
            )
        except Exception as e:
            print(f"Failed to create retriever: {e}")
            print("\nMake sure QDRANT_URL and QDRANT_API_KEY are set in your .env file")
            sys.exit(1)

    if not args.query:
        print("=" * 70)
        print("A.R.T.E.M.I.S Agent - Interactive Mode")
        print("=" * 70)
        print(f"Provider: {config.provider}")
        print(f"Model: {config.model_name}")
        if args.v2:
            print("Mode: Supervisor v2 (multi-agent routing)")
        elif retriever is None:
            print("Mode: multi-collection (artemis_system_docs + artemis_user_docs); agent chooses by task. Use --single-collection to pin to one collection.")
        else:
            print(f"Mode: single collection (all ingest and search): {args.collection}")
        print("\nEnter queries (or 'quit' to exit):\n")

        # For v2, build registry once so we don't rebuild Embedder/Indexers/Retrievers per query
        v2_registry = None
        if args.v2:
            v2_registry = _build_registry_v2(config, retriever, indexer, args.collection)

        while True:
            try:
                query = input("Query: ").strip()

                if query.lower() in ("quit", "exit", "q"):
                    break
                if not query:
                    continue

                if args.v2:
                    result = run_agent_v2(query, registry=v2_registry, config=config)
                else:
                    result = run_agent(query, retriever=retriever, indexer=indexer, config=config)

                print("\n" + "-" * 70)
                print("Answer:")
                print("-" * 70)
                print(result.get("final_answer", "No answer generated"))

                tool_calls = result.get("tool_calls", [])
                if tool_calls:
                    print(f"\nUsed {len(tool_calls)} tool call(s)")
                print(f"Intent: {result.get('intent', 'unknown')}")
                print(f"Confidence: {result.get('confidence', 0.0):.2f}")
                if args.v2:
                    print(f"Routed to: {result.get('routed_to', 'unknown')}")

                if result.get("error"):
                    print(f"\nError: {result['error']}")

                print("\n" + "=" * 70 + "\n")

            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                logger.exception("Error in interactive mode", exc_info=True)

    else:
        try:
            if args.v2:
                result = run_agent_v2(args.query, retriever=retriever, indexer=indexer, config=config)
            else:
                result = run_agent(
                    args.query,
                    retriever=retriever,
                    indexer=indexer,
                    config=config,
                )
            print(result.get("final_answer", "No answer generated"))
            if args.v2:
                print(f"Routed to: {result.get('routed_to', 'unknown')}")

            if result.get("error"):
                print(f"\nError: {result['error']}", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            logger.exception("Error processing query", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    main()
