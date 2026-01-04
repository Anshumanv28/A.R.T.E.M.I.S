"""
Retrieval abstraction layer for A.R.T.E.M.I.S.

Supports semantic vector search (MVP) with extensible design for
future keyword/BM25 and hybrid search capabilities via registry pattern.
"""

import os
from enum import Enum
from typing import List, Dict, Optional, Any, Callable

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from artemis.utils import get_logger
from artemis.rag.core.ingestion import Ingester

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
    """
    
    def __init__(
        self,
        mode: RetrievalMode = RetrievalMode.SEMANTIC,
        ingester: Optional[Ingester] = None,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "artemis_documents",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the retriever.
        
        Args:
            mode: Retrieval mode (SEMANTIC, KEYWORD, or HYBRID)
            ingester: Optional Ingester instance. If provided, uses it for shared resources.
                     If None, creates internal resources for retrieval only.
            qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
            qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
            collection_name: Name of the Qdrant collection
            embedding_model: Sentence transformer model name for embeddings (used if ingester not provided)
        """
        self.mode = mode
        self.collection_name = collection_name
        
        logger.info(f"Initializing Retriever with mode={mode.value}, collection={collection_name}")
        
        # Use provided ingester or create internal resources
        if ingester is not None:
            self.ingester = ingester
            self.qdrant_client = ingester.qdrant_client
            self.embedding_model = ingester.embedding_model
            logger.debug("Using provided Ingester instance")
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
            
            # Initialize embedding model for semantic/hybrid search
            if mode == RetrievalMode.SEMANTIC or mode == RetrievalMode.HYBRID:
                try:
                    logger.info(f"Loading embedding model: {embedding_model}")
                    self.embedding_model = SentenceTransformer(embedding_model)
                    logger.info(f"Successfully loaded embedding model: {embedding_model}")
                except Exception as e:
                    logger.exception(f"Failed to load embedding model: {embedding_model}", exc_info=True)
                    raise
            else:
                self.embedding_model = None
            
            self.ingester = None
        
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
        
        For backward compatibility, delegates to Ingester.
        If no ingester was provided, creates one internally.
        
        Args:
            documents: List of text documents or file paths
            metadata: Optional metadata list or file path
        """
        if self.ingester is None:
            # Create internal ingester for backward compatibility
            logger.debug("Creating internal Ingester for backward compatibility")
            # Get embedding model name if available
            embedding_model_name = "all-MiniLM-L6-v2"
            if self.embedding_model is not None:
                # Try to get model name from the SentenceTransformer
                try:
                    embedding_model_name = getattr(self.embedding_model, '_model_name', None) or \
                                          getattr(self.embedding_model, 'model_name', None) or \
                                          "all-MiniLM-L6-v2"
                except:
                    embedding_model_name = "all-MiniLM-L6-v2"
            
            self.ingester = Ingester(
                collection_name=self.collection_name,
                embedding_model=embedding_model_name
            )
            # Update references to use ingester's resources
            self.qdrant_client = self.ingester.qdrant_client
            self.embedding_model = self.ingester.embedding_model
        
        self.ingester.add_documents(documents, metadata)
    
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
                "  from artemis.rag.core.retrieval import register_strategy, RetrievalMode\n"
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

