"""
Example: Extending A.R.T.E.M.I.S. Document Converter for Travel Booking

This example shows how to create a custom schema converter for travel/booking data.
You can add this to your own project and register it with A.R.T.E.M.I.S.
"""

import pandas as pd
from artemis.rag import DocumentSchema, register_csv_schema, format_doc, csv_to_documents


# Step 1: Define or use a schema for travel data
# Option A: Use existing TRAVEL enum value (already defined in DocumentSchema)
TRAVEL_SCHEMA = DocumentSchema.TRAVEL

# Option B: Create a custom schema value (if you want a different name)
# TRAVEL_SCHEMA = DocumentSchema("travel_booking")  # Custom schema name


# Step 2: Create your converter function and register it
@register_csv_schema(TRAVEL_SCHEMA)
def convert_travel_bookings(csv_path: str):
    """
    Convert travel booking CSV to formatted text documents.
    
    Expected CSV columns:
    - hotel_name, city, country, check_in, check_out, price_per_night, 
      rating, amenities, room_type, cancellation_policy
    """
    import pandas as pd
    from artemis.utils import get_logger
    
    logger = get_logger(__name__)
    logger.info(f"Converting travel bookings CSV: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.exception(f"Failed to load CSV file: {csv_path}", exc_info=True)
        raise
    
    documents = []
    metadata_list = []
    
    for idx, row in df.iterrows():
        # Extract fields with safe handling
        hotel_name = str(row.get("hotel_name", "")).strip()
        city = str(row.get("city", "")).strip() if pd.notna(row.get("city")) else ""
        country = str(row.get("country", "")).strip() if pd.notna(row.get("country")) else ""
        check_in = str(row.get("check_in", "")) if pd.notna(row.get("check_in")) else ""
        check_out = str(row.get("check_out", "")) if pd.notna(row.get("check_out")) else ""
        price_per_night = row.get("price_per_night", "")
        rating = row.get("rating", "")
        amenities = str(row.get("amenities", "")).strip() if pd.notna(row.get("amenities")) else ""
        room_type = str(row.get("room_type", "")).strip() if pd.notna(row.get("room_type")) else ""
        cancellation = str(row.get("cancellation_policy", "")).strip() if pd.notna(row.get("cancellation_policy")) else ""
        
        # Build location string
        location_parts = [loc for loc in [city, country] if loc]
        location = ", ".join(location_parts) if location_parts else "Unknown"
        
        # Format price
        price_str = f"${int(price_per_night)}" if pd.notna(price_per_night) else "N/A"
        
        # Format rating
        rating_str = f"{rating:.1f}" if pd.notna(rating) else "N/A"
        
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
            "Dates": dates_str,
            "Price per night": price_str,
            "Rating": rating_str,
            "Room type": room_type,
            "Amenities": amenities,
            "Cancellation": cancellation,
        }
        
        document_text = format_doc(doc_parts)
        documents.append(document_text)
        
        # Store metadata for filtering
        metadata = {}
        try:
            metadata["hotel_name"] = hotel_name
            metadata["city"] = city
            metadata["country"] = country
            metadata["price_per_night"] = float(price_per_night) if pd.notna(price_per_night) else None
            metadata["rating"] = float(rating) if pd.notna(rating) else None
            metadata["room_type"] = room_type
        except (ValueError, TypeError) as e:
            logger.warning(f"Row {idx}: Error parsing some metadata: {e}")
            metadata["hotel_name"] = hotel_name
            metadata["city"] = city
            metadata["country"] = country
            metadata["price_per_night"] = None
            metadata["rating"] = None
        
        metadata_list.append(metadata)
    
    logger.info(f"Conversion complete: {len(documents)} travel booking documents created")
    return documents, metadata_list


# Step 3: Use your custom converter
if __name__ == "__main__":
    # Example usage
    csv_path = "data/travel_bookings.csv"
    
    # Convert CSV to documents using your custom converter
    docs, metadata = csv_to_documents(csv_path, TRAVEL_SCHEMA)
    
    print(f"Converted {len(docs)} travel booking documents")
    print("\nFirst document:")
    print(docs[0])
    print("\nFirst metadata:")
    print(metadata[0])
    
    # Now you can use these documents with the retriever
    # from artemis.rag import Retriever, RetrievalMode
    # retriever = Retriever(...)
    # retriever.add_documents(docs, metadata)
    # results = retriever.retrieve("Hotels in Paris under $200", k=5)

