"""
Restaurant converter for A.R.T.E.M.I.S.

Converts restaurant CSV data to formatted text documents optimized for
semantic search.
"""

import pandas as pd
from typing import List, Dict, Tuple

from artemis.rag.ingestion.converters.csv_converter import register_csv_schema, format_doc, DocumentSchema
from artemis.utils import get_logger

logger = get_logger(__name__)


@register_csv_schema(DocumentSchema.RESTAURANT)
def convert_restaurants(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Convert restaurant CSV rows to formatted text documents.
    
    Each row becomes a semantically rich text document optimized for
    semantic search queries like:
    - "French restaurants in Makati with rating above 4"
    - "Restaurants with online delivery and table booking"
    - "Places under 1500 for two"
    
    Args:
        csv_path: Path to the restaurant CSV file
        
    Returns:
        Tuple of (documents, metadata) where:
        - documents: List of formatted text strings (one per row)
        - metadata: List of dictionaries containing key fields for filtering
    """
    logger.info(f"Converting restaurant CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.exception(f"Failed to load CSV file: {csv_path}", exc_info=True)
        raise
    
    documents = []
    metadata_list = []
    skipped_rows = 0
    
    logger.debug("Starting document conversion")
    for idx, row in df.iterrows():
        # Extract fields with safe handling of NaN values
        name = str(row.get("Restaurant Name", "")).strip()
        city = str(row.get("City", "")).strip() if pd.notna(row.get("City")) else ""
        locality = str(row.get("Locality", "")).strip() if pd.notna(row.get("Locality")) else ""
        cuisines = str(row.get("Cuisines", "")).strip() if pd.notna(row.get("Cuisines")) else ""
        rating = row.get("Aggregate rating", "")
        cost_for_two = row.get("Average Cost for two", "")
        
        # Normalize Yes/No fields to be more robust
        raw_online = str(row.get("Has Online delivery", "")).strip().lower()
        has_online_delivery = "Yes" if raw_online in ("yes", "true", "1", "y") else "No"
        
        raw_booking = str(row.get("Has Table booking", "")).strip().lower()
        has_table_booking = "Yes" if raw_booking in ("yes", "true", "1", "y") else "No"
        
        # Build location string
        location_parts = [loc for loc in [locality, city] if loc]
        location = ", ".join(location_parts) if location_parts else city or "Unknown"
        
        # Format rating
        # Convert rating to float if it's a string, then format
        try:
            rating_float = float(rating) if pd.notna(rating) else None
            rating_str = f"{rating_float:.1f}" if rating_float is not None else "N/A"
        except (ValueError, TypeError):
            rating_str = str(rating) if pd.notna(rating) else "N/A"
        
        # Format cost (handle string values)
        try:
            cost_float = float(cost_for_two) if pd.notna(cost_for_two) else None
            cost_str = f"{int(cost_float)}" if cost_float is not None else "N/A"
        except (ValueError, TypeError):
            cost_str = str(cost_for_two) if pd.notna(cost_for_two) else "N/A"
        currency = str(row.get("Currency", "")).strip() if pd.notna(row.get("Currency")) else ""
        if currency and cost_str != "N/A":
            cost_str = f"{cost_str} {currency}"
        
        # Build document text using format_doc helper
        doc_parts = {
            "Restaurant": name,
            "Location": location,
            "Cuisines": cuisines,
            "Rating": rating_str,
            "Approx cost for two": cost_str,
            "Online delivery": has_online_delivery,
            "Table booking": has_table_booking,
        }
        document_text = format_doc(doc_parts)
        documents.append(document_text)
        
        # Store key metadata for filtering
        # Always add metadata, even if some fields fail parsing
        metadata = {}
        try:
            metadata["restaurant_id"] = int(row.get("Restaurant ID", 0)) if pd.notna(row.get("Restaurant ID")) else None
        except (ValueError, TypeError) as e:
            logger.debug(f"Row {idx}: Could not parse restaurant_id: {e}")
            metadata["restaurant_id"] = None
        
        try:
            metadata["city"] = city
            metadata["rating"] = float(rating) if pd.notna(rating) else None
            metadata["cost_for_two"] = int(cost_for_two) if pd.notna(cost_for_two) else None
            metadata["has_online_delivery"] = has_online_delivery == "Yes"
            metadata["has_table_booking"] = has_table_booking == "Yes"
        except (ValueError, TypeError) as e:
            logger.warning(f"Row {idx}: Error parsing some metadata fields: {e}")
            # Add what we can
            metadata["city"] = city
            metadata["rating"] = None
            metadata["cost_for_two"] = None
            metadata["has_online_delivery"] = has_online_delivery == "Yes"
            metadata["has_table_booking"] = has_table_booking == "Yes"
        
        metadata_list.append(metadata)
    
    logger.info(
        f"Conversion complete: {len(documents)} documents created, "
        f"{skipped_rows} rows skipped"
    )
    
    if skipped_rows > 0:
        logger.warning(f"Skipped {skipped_rows} rows during conversion")
    
    return documents, metadata_list
