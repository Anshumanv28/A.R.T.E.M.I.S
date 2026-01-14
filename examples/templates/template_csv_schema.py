"""
Template: Custom CSV Schema Converter for A.R.T.E.M.I.S.

This template shows how to create a custom CSV schema converter.
Copy this file and customize it for your specific CSV format.

Usage:
1. Copy this file to your project (e.g., my_project/my_schema.py)
2. Customize the schema name and conversion logic
3. Import it in your code before using
4. Use it with ingest_file() or csv_to_documents()

Example:
    from my_project.my_schema import convert_my_schema, SCHEMA
    from artemis.rag import ingest_file, FileType, Indexer
    
    indexer = Indexer()
    ingest_file("data.csv", FileType.CSV, indexer, schema=SCHEMA)
"""

import pandas as pd
from typing import List, Dict, Tuple

from artemis.rag.ingestion.converters.csv_converter import (
    register_csv_schema,
    format_doc,
    DocumentSchema
)
from artemis.utils import get_logger

logger = get_logger(__name__)

# TODO: Choose or create your schema
# Option 1: Use existing schema enum value
SCHEMA = DocumentSchema.SUPPORT  # or DocumentSchema.RESTAURANT, DocumentSchema.TRAVEL

# Option 2: Create custom schema (if not in enum)
# SCHEMA = DocumentSchema("my_custom_schema")


@register_csv_schema(SCHEMA)
def convert_my_schema(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Convert CSV to formatted text documents.
    
    TODO: Update this docstring with your schema's description.
    
    Expected CSV columns:
    - column1: Description of column1
    - column2: Description of column2
    - column3: Description of column3 (optional)
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Tuple of (documents, metadata_list) where:
        - documents: List of formatted text strings (one per row)
        - metadata_list: List of dictionaries containing key fields for filtering
    """
    logger.info(f"Converting CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.exception(f"Failed to load CSV file: {csv_path}", exc_info=True)
        raise
    
    documents = []
    metadata_list = []
    
    logger.debug("Starting document conversion")
    for idx, row in df.iterrows():
        # TODO: Extract and format fields from your CSV
        # Replace these examples with your actual column names
        
        field1 = str(row.get("column1", "")).strip()
        field2 = str(row.get("column2", "")).strip() if pd.notna(row.get("column2")) else ""
        field3 = str(row.get("column3", "")).strip() if pd.notna(row.get("column3")) else ""
        
        # TODO: Add any data transformation logic here
        # Examples:
        # - Format dates
        # - Convert numbers to strings
        # - Combine multiple fields
        # - Normalize values
        
        # Build document using format_doc helper
        # TODO: Customize doc_parts with your fields
        doc_parts = {
            "Field 1": field1,
            "Field 2": field2,
            "Field 3": field3,
            # Add more fields as needed...
        }
        
        document_text = format_doc(doc_parts)
        documents.append(document_text)
        
        # TODO: Store metadata for filtering
        # Include fields you want to filter on during retrieval
        metadata = {
            "column1": field1,
            "column2": field2,
            "column3": field3,
            # Add more metadata fields as needed...
        }
        
        # TODO: Add any numeric/typed fields for filtering
        # Example:
        # try:
        #     metadata["numeric_field"] = float(row.get("numeric_column", 0)) if pd.notna(row.get("numeric_column")) else None
        # except (ValueError, TypeError):
        #     metadata["numeric_field"] = None
        
        metadata_list.append(metadata)
    
    logger.info(f"Conversion complete: {len(documents)} documents created")
    return documents, metadata_list


# Example usage (uncomment to test):
# if __name__ == "__main__":
#     from artemis.rag import csv_to_documents
#     
#     # Convert CSV using your custom schema
#     docs, metadata = csv_to_documents("path/to/your/data.csv", SCHEMA)
#     
#     print(f"Converted {len(docs)} documents")
#     print("\nFirst document:")
#     print(docs[0])
#     print("\nFirst metadata:")
#     print(metadata[0])
