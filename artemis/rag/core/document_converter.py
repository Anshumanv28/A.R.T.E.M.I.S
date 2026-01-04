"""
Document conversion utilities for A.R.T.E.M.I.S.

Converts structured data (e.g., CSV) to text documents suitable for
embedding and retrieval. Uses schema-specific converters for optimal
semantic representation.
"""

import os
import json
import pandas as pd
from enum import Enum
from pathlib import Path
from typing import List, Dict, Tuple, Callable, Optional, Union
from uuid import uuid4

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

from artemis.utils import get_logger, get_docs_dir

logger = get_logger(__name__)

# Default directory for storing converted documents
DOCS_DIR = get_docs_dir()


class DocumentSchema(str, Enum):
    """Document schemas supported by the converter."""
    RESTAURANT = "restaurant"
    TRAVEL = "travel"
    SUPPORT = "support"


# Registry for schema converters
SCHEMA_CONVERTERS: Dict[DocumentSchema, Callable[[str], Tuple[List[str], List[Dict]]]] = {}


def register_schema(schema: DocumentSchema):
    """
    Decorator to register a converter function for a schema.
    
    Use this decorator to register custom schema converters. The decorated
    function should take a csv_path (str) and return (documents, metadata).
    
    Args:
        schema: DocumentSchema enum value to register
        
    Example:
        >>> @register_schema(DocumentSchema.RESTAURANT)
        >>> def convert_restaurants(csv_path: str):
        >>>     # conversion logic
        >>>     return docs, metadata
    """
    def wrapper(func: Callable[[str], Tuple[List[str], List[Dict]]]):
        SCHEMA_CONVERTERS[schema] = func
        logger.debug(f"Registered converter for schema: {schema.value}")
        return func
    return wrapper


def format_doc(parts: Dict[str, str]) -> str:
    """
    Utility to turn a dict of labeled fields into a formatted document string.
    
    Takes a dictionary of field labels and values, and formats them into
    a natural language document string. Automatically filters out empty,
    None, or "N/A" values.
    
    Args:
        parts: Dictionary mapping field labels to values
        
    Returns:
        Formatted document string with "Label: value." format
        
    Example:
        >>> doc_parts = {
        >>>     "Restaurant": "Le Petit Souffle",
        >>>     "Location": "Makati City",
        >>>     "Rating": "4.8"
        >>> }
        >>> format_doc(doc_parts)
        >>> # Returns: "Restaurant: Le Petit Souffle. Location: Makati City. Rating: 4.8."
    """
    return " ".join(
        f"{label}: {value}."
        for label, value in parts.items()
        if value not in (None, "", "N/A")
    )


def _save_documents_to_files(
    documents: List[str],
    metadata: List[Dict],
    output_dir: Optional[Path] = None
) -> Tuple[List[str], List[Dict]]:
    """
    Save documents and metadata to files in the docs directory.
    
    Creates one file per document with a unique ID. Also saves a metadata
    JSON file mapping document IDs to metadata.
    
    Args:
        documents: List of document text strings
        metadata: List of metadata dictionaries
        output_dir: Optional directory path (defaults to DOCS_DIR)
        
    Returns:
        Tuple of (document_file_paths, metadata_file_path) where:
        - document_file_paths: List of paths to saved document files
        - metadata_file_path: Path to the metadata JSON file
    """
    if output_dir is None:
        output_dir = DOCS_DIR
    
    # Create docs directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Using docs directory: {output_dir.absolute()}")
    
    # Generate unique batch ID for this conversion
    batch_id = str(uuid4())[:8]
    
    # Save each document to a separate file
    document_paths = []
    doc_id_to_metadata = {}
    
    for idx, (doc, meta) in enumerate(zip(documents, metadata)):
        # Generate unique document ID
        doc_id = f"{batch_id}_{idx:06d}"
        
        # Save document text to file
        doc_file = output_dir / f"{doc_id}.txt"
        try:
            with open(doc_file, "w", encoding="utf-8") as f:
                f.write(doc)
            document_paths.append(str(doc_file))
            doc_id_to_metadata[doc_id] = meta
            logger.debug(f"Saved document {idx+1}/{len(documents)} to {doc_file.name}")
        except Exception as e:
            logger.exception(f"Failed to save document {idx+1} to {doc_file}: {e}")
            raise
    
    # Save metadata mapping to JSON file
    metadata_file = output_dir / f"{batch_id}_metadata.json"
    try:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(doc_id_to_metadata, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved metadata to {metadata_file.name}")
    except Exception as e:
        logger.exception(f"Failed to save metadata to {metadata_file}: {e}")
        raise
    
    logger.info(
        f"Saved {len(documents)} documents to {output_dir.absolute()}, "
        f"metadata in {metadata_file.name}"
    )
    
    return document_paths, str(metadata_file)


def _auto_convert_csv(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Automatically convert CSV to documents using column headers.
    
    Uses CSV column names as labels and creates formatted documents
    for each row. Works with any CSV structure.
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        Tuple of (documents, metadata) where:
        - documents: List of formatted text strings (one per row)
        - metadata: List of dictionaries containing row data for filtering
    """
    logger.info(f"Auto-converting CSV using headers: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.exception(f"Failed to load CSV file: {csv_path}", exc_info=True)
        raise
    
    documents = []
    metadata_list = []
    
    logger.debug("Starting auto-conversion using CSV headers")
    for idx, row in df.iterrows():
        # Create dict mapping column names to string values
        # Handle NaN values by converting to empty string
        doc_parts = {}
        metadata = {}
        
        for col_name in df.columns:
            value = row.get(col_name)
            
            # Convert NaN to empty string for format_doc filtering
            if pd.isna(value):
                str_value = ""
            else:
                str_value = str(value).strip()
            
            # Use column name as label (can be improved with title case later)
            doc_parts[col_name] = str_value
            metadata[col_name] = value if not pd.isna(value) else None
        
        # Format document using format_doc helper
        document_text = format_doc(doc_parts)
        documents.append(document_text)
        metadata_list.append(metadata)
    
    logger.info(f"Auto-conversion complete: {len(documents)} documents created")
    return documents, metadata_list


def csv_to_documents(
    csv_path: str,
    schema: Optional[DocumentSchema] = None,
    save_to_disk: Optional[bool] = None,
    output_dir: Optional[Union[str, Path]] = None
) -> Union[Tuple[List[str], str], Tuple[List[str], List[Dict]]]:
    """
    Convert CSV rows to formatted text documents.
    
    By default, documents are returned in-memory (fast, simple). Optionally,
    documents can be saved to the `docs/` folder for unit testing or handling
    very large document sets. Files are automatically deleted after ingestion
    by the retriever.
    
    Simple usage (in-memory, default):
        >>> docs, metadata = csv_to_documents("any_file.csv")
    
    With registered schema:
        >>> docs, metadata = csv_to_documents("restaurants.csv", DocumentSchema.RESTAURANT)
    
    File-based mode (advanced, for testing/large datasets):
        >>> doc_paths, metadata_path = csv_to_documents("data.csv", save_to_disk=True)
    
    Args:
        csv_path: Path to the CSV file
        schema: Optional document schema type. If None, auto-detects using CSV headers.
                If provided, uses registered schema converter if available.
        save_to_disk: If None, uses ARTEMIS_SAVE_DOCS_TO_DISK env var (defaults to False).
                      If True, saves documents to files. If False, returns in-memory lists.
        output_dir: Optional directory to save documents (defaults to "docs/")
        
    Returns:
        If save_to_disk=False (default):
            Tuple of (documents, metadata) where:
            - documents: List of formatted text strings (one per row)
            - metadata: List of dictionaries containing row data for filtering
        
        If save_to_disk=True:
            Tuple of (document_file_paths, metadata_file_path) where:
            - document_file_paths: List of paths to saved document .txt files
            - metadata_file_path: Path to metadata JSON file
        
    Example:
        >>> from artemis.rag import csv_to_documents, DocumentSchema
        >>> # In-memory mode (default, fast)
        >>> docs, metadata = csv_to_documents("data.csv")
        >>> # Use registered schema
        >>> docs, metadata = csv_to_documents("restaurants.csv", DocumentSchema.RESTAURANT)
        >>> # File-based mode (for testing/large datasets)
        >>> doc_paths, metadata_path = csv_to_documents("data.csv", save_to_disk=True)
    """
    # Determine save_to_disk mode (env var > parameter > default False)
    if save_to_disk is None:
        env_value = os.getenv("ARTEMIS_SAVE_DOCS_TO_DISK", "false").lower()
        save_to_disk = env_value in ("true", "1", "yes")
        if save_to_disk:
            logger.debug("save_to_disk enabled via ARTEMIS_SAVE_DOCS_TO_DISK environment variable")
    
    # Convert CSV to documents (in memory first)
    if schema is None:
        logger.info(f"Converting CSV to documents (auto-detect): path={csv_path}")
        documents, metadata = _auto_convert_csv(csv_path)
    else:
        logger.info(f"Converting CSV to documents: path={csv_path}, schema={schema.value}")
        try:
            # Check if schema is registered
            if schema not in SCHEMA_CONVERTERS:
                logger.error(f"Schema '{schema.value}' is not registered")
                available_schemas = [s.value for s in SCHEMA_CONVERTERS.keys()]
                raise NotImplementedError(
                    f"Schema '{schema.value}' is not implemented. "
                    f"Available schemas: {available_schemas}. "
                    "You can extend A.R.T.E.M.I.S by registering a converter:\n"
                    "  from artemis.rag.core.document_converter import register_schema\n"
                    f"  @register_schema(DocumentSchema.{schema.name})\n"
                    "  def convert_your_schema(csv_path: str): ..."
                )
            
            # Get and call the registered converter
            converter = SCHEMA_CONVERTERS[schema]
            documents, metadata = converter(csv_path)
        except NotImplementedError:
            # Re-raise NotImplementedError as-is
            raise
        except Exception as e:
            logger.exception(
                f"Error converting CSV to documents: path={csv_path}, schema={schema.value}",
                exc_info=True
            )
            raise
    
    # Save to disk if requested
    if save_to_disk:
        output_path = Path(output_dir) if output_dir else None
        doc_paths, metadata_path = _save_documents_to_files(documents, metadata, output_path)
        return doc_paths, metadata_path
    else:
        # Return in-memory (backward compatibility)
        return documents, metadata
