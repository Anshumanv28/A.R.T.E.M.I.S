"""
Travel booking converter for A.R.T.E.M.I.S.

Converts travel booking CSV data (hotels, flights, etc.) to formatted
text documents optimized for semantic search.
"""

import pandas as pd
from typing import List, Dict, Tuple

from artemis.rag.ingestion.converters.csv_converter import register_csv_schema, format_doc, DocumentSchema
from artemis.utils import get_logger

logger = get_logger(__name__)


@register_csv_schema(DocumentSchema.TRAVEL)
def convert_travel(csv_path: str) -> Tuple[List[str], List[Dict]]:
    """
    Convert travel booking CSV rows to formatted text documents.
    
    Each row becomes a semantically rich text document optimized for
    semantic search queries like:
    - "Hotels in Paris under $200"
    - "Resorts with spa and pool in Bali"
    - "Hotels with free cancellation in Tokyo"
    
    Expected CSV columns:
    - hotel_name (or flight_number, attraction_name, etc.)
    - city, country
    - check_in, check_out (optional, for bookings)
    - price_per_night (or price)
    - rating
    - amenities (comma-separated)
    - room_type (optional)
    - cancellation_policy (optional)
    
    Args:
        csv_path: Path to the travel booking CSV file
        
    Returns:
        Tuple of (documents, metadata) where:
        - documents: List of formatted text strings (one per row)
        - metadata: List of dictionaries containing key fields for filtering
    """
    logger.info(f"Converting travel CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.exception(f"Failed to load CSV file: {csv_path}", exc_info=True)
        raise
    
    documents = []
    metadata_list = []
    
    logger.debug("Starting travel document conversion")
    for idx, row in df.iterrows():
        # Extract fields with safe handling of NaN values
        # Support multiple column name variations
        hotel_name = (
            str(row.get("hotel_name", "")).strip() or
            str(row.get("name", "")).strip() or
            str(row.get("property_name", "")).strip() or
            ""
        )
        
        city = str(row.get("city", "")).strip() if pd.notna(row.get("city")) else ""
        country = str(row.get("country", "")).strip() if pd.notna(row.get("country")) else ""
        
        # Optional date fields
        check_in = str(row.get("check_in", "")) if pd.notna(row.get("check_in")) else ""
        check_out = str(row.get("check_out", "")) if pd.notna(row.get("check_out")) else ""
        
        # Price (support multiple column names)
        price_per_night = (
            row.get("price_per_night") if pd.notna(row.get("price_per_night")) else
            row.get("price") if pd.notna(row.get("price")) else
            row.get("rate") if pd.notna(row.get("rate")) else
            None
        )
        
        rating = row.get("rating", None)
        amenities = str(row.get("amenities", "")).strip() if pd.notna(row.get("amenities")) else ""
        room_type = str(row.get("room_type", "")).strip() if pd.notna(row.get("room_type")) else ""
        cancellation = str(row.get("cancellation_policy", "")).strip() if pd.notna(row.get("cancellation_policy")) else ""
        
        # Build location string
        location_parts = [loc for loc in [city, country] if loc]
        location = ", ".join(location_parts) if location_parts else "Unknown"
        
        # Format price (handle string values)
        try:
            price_float = float(price_per_night) if price_per_night is not None and pd.notna(price_per_night) else None
            price_str = f"${int(price_float)}" if price_float is not None else "N/A"
        except (ValueError, TypeError):
            price_str = str(price_per_night) if price_per_night is not None and pd.notna(price_per_night) else "N/A"
        
        # Format rating (handle string values)
        try:
            rating_float = float(rating) if rating is not None and pd.notna(rating) else None
            rating_str = f"{rating_float:.1f}" if rating_float is not None else "N/A"
        except (ValueError, TypeError):
            rating_str = str(rating) if rating is not None and pd.notna(rating) else "N/A"
        
        # Format dates
        dates_str = ""
        if check_in and check_out:
            dates_str = f"{check_in} to {check_out}"
        elif check_in:
            dates_str = f"from {check_in}"
        
        # Build document using format_doc helper
        doc_parts = {
            "Hotel": hotel_name,
            "Location": location,
        }
        
        # Add optional fields only if they have values
        if dates_str:
            doc_parts["Dates"] = dates_str
        if price_str != "N/A":
            doc_parts["Price per night"] = price_str
        if rating_str != "N/A":
            doc_parts["Rating"] = rating_str
        if room_type:
            doc_parts["Room type"] = room_type
        if amenities:
            doc_parts["Amenities"] = amenities
        if cancellation:
            doc_parts["Cancellation"] = cancellation
        
        document_text = format_doc(doc_parts)
        documents.append(document_text)
        
        # Store metadata for filtering
        metadata = {}
        try:
            metadata["hotel_name"] = hotel_name
            metadata["city"] = city
            metadata["country"] = country
            metadata["price_per_night"] = float(price_per_night) if price_per_night is not None and pd.notna(price_per_night) else None
            metadata["rating"] = float(rating) if rating is not None and pd.notna(rating) else None
            metadata["room_type"] = room_type if room_type else None
        except (ValueError, TypeError) as e:
            logger.warning(f"Row {idx}: Error parsing some metadata fields: {e}")
            metadata["hotel_name"] = hotel_name
            metadata["city"] = city
            metadata["country"] = country
            metadata["price_per_night"] = None
            metadata["rating"] = None
            metadata["room_type"] = None
        
        metadata_list.append(metadata)
    
    logger.info(f"Conversion complete: {len(documents)} travel documents created")
    return documents, metadata_list

