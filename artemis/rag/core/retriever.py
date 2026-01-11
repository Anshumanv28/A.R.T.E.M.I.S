"""
Retrieval abstraction layer for A.R.T.E.M.I.S.

Supports semantic vector search (MVP) with extensible design for
future keyword/BM25 and hybrid search capabilities via registry pattern.
"""

import os
from enum import Enum
from typing import List, Dict, Optional, Any, Callable

from qdrant_client import QdrantClient

from artemis.utils import get_logger
from artemis.rag.core.indexer import Indexer
from artemis.rag.core.embedder import Embedder

logger = get_logger(__name__)


class RetrievalMode(str, Enum):
    """Retrieval modes supported by the system."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"  # Future: BM25/TF-IDF based
    HYBRID = "hybrid"    # Future: Combined semantic + keyword


# Registry for retrieval strategies
RETRIEVAL_STRATEGIES: Dict[RetrievalMode, Callable] = {}


def register_strategy(mode: RetrievalMode):
    """
    Decorator to register a retrieval strategy function.
    
    The decorated function should have the signature:
    (retriever: Retriever, query: str, k: int) -> List[Dict[str, Any]]
    
    Args:
        mode: RetrievalMode enum value to register
        
    Example:
        >>> @register_strategy(RetrievalMode.SEMANTIC)
        >>> def semantic_search_strategy(retriever, query: str, k: int):
        >>>     # implementation
        >>>     return results
    """
    def wrapper(func: Callable):
        RETRIEVAL_STRATEGIES[mode] = func
        logger.debug(f"Registered retrieval strategy for mode: {mode.value}")
        return func
    return wrapper


class Retriever:
    """
    Pluggable retrieval abstraction that supports multiple search strategies.
    
    Uses a registry pattern to delegate retrieval to registered strategy functions.
    Currently implements semantic vector search. Keyword and hybrid search
    can be added via the registry system.
    
    **Why is Indexer recommended but optional?**
    
    The Indexer parameter is a convenience that bundles together resources needed
    for retrieval (embedder, Qdrant client, collection name). It's OPTIONAL but
    RECOMMENDED because:
    
    1. **Guarantees consistency**: Ensures you use the same embedder model that
       was used for indexing (critical - different models = broken search)
    2. **Simpler API**: One parameter instead of multiple (embedder, qdrant_url,
       collection_name)
    3. **Prevents errors**: Can't accidentally use wrong embedder or collection
    
    You can create a Retriever without an Indexer, but you must manually ensure
    the embedder and collection match what was used for indexing.
    """
    
    def __init__(
        self,
        mode: RetrievalMode = RetrievalMode.SEMANTIC,
        indexer: Optional[Indexer] = None,
        embedder: Optional[Embedder] = None,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "artemis_documents",
    ):
        """
        Initialize the retriever.
        
        **Recommended: Pass an Indexer instance** (ensures consistency)
        
        If you pass an Indexer, the Retriever automatically uses:
        - The same embedder (critical for semantic search to work correctly)
        - The same Qdrant connection
        - The same collection name
        
        This guarantees that queries use the same embedding model that was used
        to index the documents, which is required for consistent semantic search.
        
        **Alternative: Pass resources separately** (must match indexing configuration)
        
        You can also create a Retriever without an Indexer by providing:
        - embedder: Embedder instance (MUST match the one used for indexing!)
        - qdrant_url: Qdrant server URL (must match indexing configuration)
        - collection_name: Collection name (MUST match the one used for indexing!)
        
        Use this approach only if you're doing retrieval-only (didn't create an
        Indexer yourself) and need to manually specify resources.
        
        Args:
            mode: Retrieval mode (SEMANTIC, KEYWORD, or HYBRID)
            indexer: Optional Indexer instance. If provided, automatically uses its
                    embedder, Qdrant client, and collection name. This is the
                    RECOMMENDED approach as it guarantees consistency.
            embedder: Optional Embedder instance. Only used if indexer is None.
                     - If indexer is provided: Always uses indexer's embedder (ignores this parameter)
                     - If indexer is None and mode is SEMANTIC/HYBRID: Required, raises ValueError if not provided
                     - If indexer is None and mode is KEYWORD: Not needed, can be None
            qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL, only used if indexer is None)
            qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY, only used if indexer is None)
            collection_name: Name of the Qdrant collection (only used if indexer is None)
        
        Examples:
            >>> # Recommended: Use Indexer (guarantees consistency)
            >>> indexer = Indexer(collection_name="docs")
            >>> ingest_file("file.pdf", FileType.PDF, indexer)
            >>> retriever = Retriever(mode=RetrievalMode.SEMANTIC, indexer=indexer)
            >>> # Uses same embedder/collection automatically
            >>> results = retriever.retrieve("query", k=5)
            >>> 
            >>> # Alternative: Without Indexer (must match configuration manually)
            >>> embedder = Embedder(model_name="all-MiniLM-L6-v2")
            >>> retriever = Retriever(
            ...     mode=RetrievalMode.SEMANTIC,
            ...     embedder=embedder,  # Must match indexing embedder!
            ...     qdrant_url="http://localhost:6333",
            ...     collection_name="docs"  # Must match indexing collection!
            ... )
            >>> results = retriever.retrieve("query", k=5)
        """
        self.mode = mode
        self.collection_name = collection_name
        
        logger.info(f"Initializing Retriever with mode={mode.value}, collection={collection_name}")
        
        # Use provided indexer or create internal resources
        if indexer is not None:
            self.indexer = indexer
            self.qdrant_client = indexer.qdrant_client
            self.embedder = indexer.embedder
            logger.debug("Using provided Indexer instance")
        else:
            # Create internal resources for retrieval only
            qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
            qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
            
            if not qdrant_url:
                logger.error("Qdrant URL is required but not provided")
                raise ValueError(
                    "Qdrant URL is required. Set QDRANT_URL environment variable "
                    "or pass qdrant_url parameter."
                )
            
            try:
                logger.debug(f"Connecting to Qdrant at {qdrant_url}")
                self.qdrant_client = QdrantClient(
                    url=qdrant_url,
                    api_key=qdrant_api_key,
                )
                logger.info("Successfully connected to Qdrant")
            except Exception as e:
                logger.exception("Failed to connect to Qdrant", exc_info=True)
                raise
            
            # Initialize embedder for semantic/hybrid search
            if mode == RetrievalMode.SEMANTIC or mode == RetrievalMode.HYBRID:
                if embedder is not None:
                    self.embedder = embedder
                    logger.debug("Using provided Embedder instance")
                else:
                    raise ValueError(
                        f"Embedder is required for {mode.value} retrieval mode. "
                        "Either pass an embedder parameter, use an Indexer instance, "
                        "or create an Embedder explicitly: "
                        "Retriever(embedder=Embedder(model_name='...'))"
                    )
            else:
                self.embedder = None
            
            self.indexer = None
        
        # Keyword search index (for future implementation)
        self.keyword_index = None
        logger.debug("Retriever initialization complete")
    
    def add_documents(
        self,
        documents: List[str],
        metadata: Optional[Any] = None,
    ) -> None:
        """
        Add documents to the vector store.
        
        For backward compatibility, delegates to Indexer.
        If no indexer was provided, creates one internally using the existing embedder.
        
        Args:
            documents: List of text documents or file paths
            metadata: Optional metadata list or file path
        """
        if self.indexer is None:
            # Create internal indexer for backward compatibility
            logger.debug("Creating internal Indexer for backward compatibility")
            self.indexer = Indexer(
                collection_name=self.collection_name,
                embedder=self.embedder  # Use existing embedder or None (will create default)
            )
            # Update references to use indexer's resources
            self.qdrant_client = self.indexer.qdrant_client
            self.embedder = self.indexer.embedder
        
        self.indexer.add_documents(documents, metadata)
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve documents based on the configured retrieval mode.
        
        Delegates to the registered strategy for the current mode.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of dictionaries containing retrieved documents with metadata
            
        Raises:
            NotImplementedError: If no strategy is registered for the current mode
        """
        logger.info(f"Retrieving documents: mode={self.mode.value}, query='{query[:50]}...', k={k}")
        
        if self.mode not in RETRIEVAL_STRATEGIES:
            available_modes = [m.value for m in RETRIEVAL_STRATEGIES.keys()]
            raise NotImplementedError(
                f"Strategy for {self.mode.value} is not registered. "
                f"Available strategies: {available_modes}. "
                "You can register a custom strategy:\n"
                "  from artemis.rag.core.retriever import register_strategy, RetrievalMode\n"
                f"  @register_strategy(RetrievalMode.{self.mode.name})\n"
                "  def my_strategy(retriever, query: str, k: int): ..."
            )
        
        try:
            strategy = RETRIEVAL_STRATEGIES[self.mode]
            results = strategy(self, query, k)
            logger.info(f"Retrieved {len(results)} documents")
            return results
        except Exception as e:
            logger.exception(f"Error during retrieval: query='{query[:50]}...'", exc_info=True)
            raise


# Auto-register retrieval strategies
# Strategies are defined in artemis/rag/strategies/ and registered via decorators
try:
    from artemis.rag import strategies  # noqa: F401
except ImportError:
    # Strategies module not available or not yet implemented
    pass

