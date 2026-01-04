"""
Embedding component for A.R.T.E.M.I.S.

Handles embedding model loading and text-to-embedding conversion.
Separated from indexing and retrieval to enable reuse and independent testing.
"""

from typing import List, Union
from sentence_transformers import SentenceTransformer

from artemis.utils import get_logger

logger = get_logger(__name__)


class Embedder:
    """
    Handles embedding model loading and text-to-embedding conversion.
    
    This class provides a single source of truth for embedding operations,
    enabling reuse between Indexer and Retriever components.
    
    Responsibilities:
    - Model loading and initialization
    - Text encoding (single or batch)
    - Dimension retrieval for vector store setup
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedder with a sentence transformer model.
        
        Args:
            model_name: Name of the sentence transformer model to load
        """
        self.model_name = model_name
        
        logger.info(f"Initializing Embedder with model: {model_name}")
        
        try:
            logger.debug(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            logger.info(f"Successfully loaded embedding model: {model_name}")
        except Exception as e:
            logger.exception(f"Failed to load embedding model: {model_name}", exc_info=True)
            raise
    
    def encode(
        self,
        texts: Union[str, List[str]],
        show_progress: bool = False,
    ) -> Union[List[float], List[List[float]]]:
        """
        Encode text(s) into embedding vector(s).
        
        Args:
            texts: Single text string or list of text strings
            show_progress: Whether to show progress bar (only for batch encoding)
            
        Returns:
            If single text: List[float] (single embedding vector)
            If list of texts: List[List[float]] (list of embedding vectors)
            
        Example:
            >>> embedder = Embedder()
            >>> # Single text
            >>> embedding = embedder.encode("Hello world")
            >>> # Batch
            >>> embeddings = embedder.encode(["Hello", "World"], show_progress=True)
        """
        is_single = isinstance(texts, str)
        
        if is_single:
            texts_list = [texts]
        else:
            texts_list = texts
        
        logger.debug(f"Encoding {len(texts_list)} text(s)")
        
        try:
            embeddings = self._model.encode(
                texts_list,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )
            
            # Convert to list format
            embeddings_list = embeddings.tolist()
            
            logger.debug(f"Generated {len(embeddings_list)} embedding(s)")
            
            # Return single embedding for single text, list for batch
            if is_single:
                return embeddings_list[0]
            return embeddings_list
            
        except Exception as e:
            logger.exception(f"Error encoding text(s)", exc_info=True)
            raise
    
    def encode_single(self, text: str) -> List[float]:
        """
        Convenience method to encode a single text string.
        
        Args:
            text: Single text string to encode
            
        Returns:
            List[float]: Single embedding vector
            
        Example:
            >>> embedder = Embedder()
            >>> embedding = embedder.encode_single("Hello world")
        """
        return self.encode(text)
    
    def get_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            int: Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
            
        Example:
            >>> embedder = Embedder()
            >>> dim = embedder.get_dimension()  # Returns 384
        """
        try:
            dimension = self._model.get_sentence_embedding_dimension()
            logger.debug(f"Embedding dimension: {dimension}")
            return dimension
        except Exception as e:
            logger.exception("Error getting embedding dimension", exc_info=True)
            raise

