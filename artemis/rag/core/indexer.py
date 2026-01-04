"""
Document indexing module for A.R.T.E.M.I.S.

Handles document storage, embedding generation, and Qdrant operations.
Separated from retrieval to enable independent testing and extensibility.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from artemis.utils import get_logger
from artemis.rag.core.embedder import Embedder

logger = get_logger(__name__)


class Indexer:
    """
    Handles document indexing into the vector store.
    
    Responsibilities:
    - Document file reading (if file paths provided)
    - Embedding generation using Embedder
    - Qdrant collection management
    - Document storage with metadata
    - File cleanup after successful ingestion
    """
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "artemis_documents",
        embedder: Optional[Embedder] = None,
    ):
        """
        Initialize the indexer.
        
        Args:
            qdrant_url: Qdrant server URL (defaults to env var QDRANT_URL)
            qdrant_api_key: Qdrant API key (defaults to env var QDRANT_API_KEY)
            collection_name: Name of the Qdrant collection
            embedder: Optional Embedder instance. If None, creates a default Embedder.
                     Pass an Embedder instance to use a custom model or share embedders.
        """
        self.collection_name = collection_name
        
        # Initialize embedder
        if embedder is not None:
            self.embedder = embedder
            logger.info(f"Initializing Indexer with collection={collection_name}, using provided Embedder")
        else:
            logger.info(f"Initializing Indexer with collection={collection_name}, creating default Embedder")
            try:
                self.embedder = Embedder()  # Uses default model "all-MiniLM-L6-v2"
            except Exception as e:
                logger.exception("Failed to create default Embedder", exc_info=True)
                raise
        
        # Initialize Qdrant client
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
        
        # Ensure collection exists (needs embedder dimension)
        try:
            self._ensure_collection_exists()
        except Exception as e:
            logger.exception("Failed to ensure collection exists", exc_info=True)
            raise
        
        logger.debug("Indexer initialization complete")
    
    def _ensure_collection_exists(self) -> None:
        """Ensure the Qdrant collection exists with correct configuration."""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                # Get embedding dimension from embedder
                embedding_dim = self.embedder.get_dimension()
                logger.info(
                    f"Creating Qdrant collection '{self.collection_name}' "
                    f"with embedding dimension {embedding_dim}"
                )
                
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=embedding_dim,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Successfully created collection '{self.collection_name}'")
            else:
                logger.debug(f"Collection '{self.collection_name}' already exists")
        except Exception as e:
            logger.exception(
                f"Error ensuring collection '{self.collection_name}' exists",
                exc_info=True
            )
            raise
    
    def add_documents(
        self,
        documents: List[str],
        metadata: Optional[Union[List[Dict[str, Any]], str]] = None,
    ) -> None:
        """
        Add documents to the vector store.
        
        Accepts either:
        1. File paths (from csv_to_documents with save_to_disk=True)
        2. In-memory document strings (backward compatibility)
        
        If file paths are provided, documents are read from files and the files
        are deleted after successful ingestion.
        
        Args:
            documents: List of text documents (strings) OR list of file paths (strings)
            metadata: Optional list of metadata dicts OR path to metadata JSON file
        """
        if not documents:
            logger.warning("add_documents called with empty document list")
            return
        
        # Check if documents are file paths or in-memory strings
        # If first item is a file path (ends with .txt and file exists), treat as file paths
        is_file_paths = (
            isinstance(documents[0], str) and 
            documents[0].endswith('.txt') and 
            Path(documents[0]).exists()
        )
        
        if is_file_paths:
            # Read documents from files
            logger.info(f"Reading {len(documents)} documents from files")
            doc_texts = []
            for doc_path in documents:
                try:
                    with open(doc_path, "r", encoding="utf-8") as f:
                        doc_texts.append(f.read())
                except Exception as e:
                    logger.exception(f"Failed to read document from {doc_path}: {e}")
                    raise
            
            # Load metadata from JSON file if provided
            metadata_list = None
            if metadata and isinstance(metadata, str) and metadata.endswith('.json'):
                metadata_file = Path(metadata)
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata_dict = json.load(f)
                        # Convert dict to list in same order as documents
                        # Extract doc IDs from file paths
                        metadata_list = []
                        for doc_path in documents:
                            doc_id = Path(doc_path).stem  # filename without extension
                            metadata_list.append(metadata_dict.get(doc_id, {}))
                        logger.debug(f"Loaded metadata from {metadata_file}")
                    except Exception as e:
                        logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
                        metadata_list = None
        else:
            # In-memory documents (backward compatibility)
            doc_texts = documents
            metadata_list = metadata if isinstance(metadata, list) else None
        
        if not doc_texts:
            logger.warning("No documents to add after reading from files")
            return
        
        logger.info(f"Adding {len(doc_texts)} documents to collection '{self.collection_name}'")
        
        try:
            # Generate embeddings
            embeddings = self._generate_embeddings(doc_texts)
            
            # Prepare points for Qdrant
            points = self._prepare_points(doc_texts, embeddings, metadata_list)
            
            # Store to Qdrant
            self._store_to_qdrant(points)
            
            logger.info(f"Successfully added {len(doc_texts)} documents to collection")
            
            # Delete files after successful ingestion
            if is_file_paths:
                self._cleanup_files(documents, metadata)
                
        except Exception as e:
            logger.exception(
                f"Error adding documents to collection '{self.collection_name}'",
                exc_info=True
            )
            # Don't delete files if ingestion failed
            if is_file_paths:
                logger.warning("Documents not deleted due to ingestion failure")
            raise
    
    def _generate_embeddings(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents.
        
        Args:
            documents: List of document text strings
            
        Returns:
            List of embedding vectors
        """
        logger.debug(f"Generating embeddings for {len(documents)} documents")
        embeddings = self.embedder.encode(
            documents,
            show_progress=True,
        )
        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def _prepare_points(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[PointStruct]:
        """
        Prepare Qdrant points from documents, embeddings, and metadata.
        
        Args:
            documents: List of document text strings
            embeddings: List of embedding vectors
            metadata: Optional list of metadata dictionaries
            
        Returns:
            List of PointStruct objects for Qdrant
        """
        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            point_metadata = {
                "text": doc,
                **(metadata[i] if metadata and i < len(metadata) else {}),
            }
            
            points.append(
                PointStruct(
                    id=str(uuid4()),
                    vector=embedding,
                    payload=point_metadata,
                )
            )
        
        return points
    
    def _store_to_qdrant(self, points: List[PointStruct]) -> None:
        """
        Store points to Qdrant collection.
        
        Args:
            points: List of PointStruct objects to store
        """
        logger.debug(f"Upserting {len(points)} points to Qdrant")
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        logger.debug(f"Successfully stored {len(points)} points to Qdrant")
    
    def _cleanup_files(
        self,
        doc_paths: List[str],
        metadata_path: Optional[Union[str, List[Dict[str, Any]]]] = None,
    ) -> None:
        """
        Delete document files and metadata file after successful ingestion.
        
        Args:
            doc_paths: List of document file paths to delete
            metadata_path: Optional metadata file path or list (if list, no file to delete)
        """
        logger.debug("Deleting document files after successful ingestion")
        deleted_count = 0
        for doc_path in doc_paths:
            try:
                Path(doc_path).unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {doc_path}: {e}")
        
        # Delete metadata file if it exists
        if metadata_path and isinstance(metadata_path, str) and metadata_path.endswith('.json'):
            try:
                Path(metadata_path).unlink()
                logger.debug(f"Deleted metadata file: {metadata_path}")
            except Exception as e:
                logger.warning(f"Failed to delete metadata file {metadata_path}: {e}")
        
        logger.info(f"Deleted {deleted_count} document files after ingestion")

