"""
CSV chunking strategy for A.R.T.E.M.I.S.

Converts CSV DataFrames to documents using row-based chunking.
Supports both auto-detect and schema-based conversion.
"""

from typing import List, Dict, Tuple, Any, Optional, Union
from pathlib import Path

import pandas as pd

from artemis.rag.core.chunker import register_chunker, ChunkStrategy
from artemis.rag.core.document_converter import (
    format_doc,
    DocumentSchema,
    SCHEMA_CONVERTERS,
)
from artemis.utils import get_logger

logger = get_logger(__name__)


@register_chunker(ChunkStrategy.CSV_ROW)
def csv_row_chunker(
    df: pd.DataFrame,
    schema: Optional[DocumentSchema] = None,
    csv_path: Optional[Union[str, Path]] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Chunk CSV DataFrame into row-based documents.
    
    Converts each CSV row into a formatted document. Supports both
    auto-detect (using column headers) and schema-based conversion.
    
    Args:
        df: pandas DataFrame containing CSV data
        schema: Optional DocumentSchema. If provided, uses registered schema converter.
                Schema converters require csv_path to be provided.
        csv_path: Optional path to CSV file. Required if schema is provided.
        
    Returns:
        Tuple of (documents, metadata) where:
        - documents: List of formatted text strings (one per row)
        - metadata: List of dictionaries containing row data for filtering
        
    Raises:
        NotImplementedError: If schema is provided but not registered
        ValueError: If schema is provided but csv_path is not provided
    """
    if schema is not None:
        # Use schema-based conversion
        if csv_path is None:
            raise ValueError(
                f"csv_path is required when using schema '{schema.value}'. "
                "Schema converters need the file path to process the CSV."
            )
        
        logger.info(f"Chunking CSV using schema: {schema.value}")
        
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
        # Note: Schema converters take csv_path, not DataFrame
        converter = SCHEMA_CONVERTERS[schema]
        documents, metadata = converter(str(csv_path))
        
        logger.info(f"Schema-based conversion complete: {len(documents)} documents created")
        return documents, metadata
    
    # Auto-detect conversion using column headers
    logger.debug("Chunking CSV using auto-detect (column headers)")
    
    documents = []
    metadata_list = []
    
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
            
            # Use column name as label
            doc_parts[col_name] = str_value
            metadata[col_name] = value if not pd.isna(value) else None
        
        # Format document using format_doc helper
        document_text = format_doc(doc_parts)
        documents.append(document_text)
        metadata_list.append(metadata)
    
    logger.info(f"Auto-detect conversion complete: {len(documents)} documents created")
    return documents, metadata_list

