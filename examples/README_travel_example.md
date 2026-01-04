# Using A.R.T.E.M.I.S. Document Converters

This guide shows you how to use A.R.T.E.M.I.S. document converters, from simple auto-detect to advanced custom schemas.

---

## 🎯 Quick Start

**For most users - just works with any CSV:**

```python
from artemis.rag import csv_to_documents

# Auto-detects CSV headers - works with any CSV structure
docs, metadata = csv_to_documents("travel_bookings.csv")

# Add to retriever and search
from artemis.rag import Retriever, RetrievalMode

retriever = Retriever(mode=RetrievalMode.SEMANTIC, collection_name="travel")
retriever.add_documents(docs, metadata)
results = retriever.retrieve("Hotels in Paris under $200", k=5)
```

**That's it!** No configuration needed - A.R.T.E.M.I.S. automatically uses your CSV column headers.

---

## 🔧 Advanced: Custom Schema Converters (Future Extensibility)

For advanced users who want optimized conversion for specific data types, you can register custom schema converters. This is optional and only needed if you want specialized formatting.

### 📍 Where to Add Custom Converters

### Option 1: In Your Own Project (Recommended)

If you're using A.R.T.E.M.I.S. as a library in your own project, add converters in **your project**, not in the A.R.T.E.M.I.S. repository.

#### Project Structure

```
my-travel-app/
├── main.py                 # Your main application
├── converters/             # Your custom converters
│   ├── __init__.py
│   └── travel_converter.py # Your travel converter
├── data/
│   └── travel_bookings.csv
└── requirements.txt
```

#### Step 1: Create Your Converter File

**`converters/travel_converter.py`:**

```python
from artemis.rag import DocumentSchema, register_schema, format_doc
import pandas as pd

@register_schema(DocumentSchema.TRAVEL)
def convert_travel_bookings(csv_path: str):
    """Your custom travel converter."""
    df = pd.read_csv(csv_path)
    docs, metadata = [], []

    for _, row in df.iterrows():
        doc_parts = {
            "Hotel": str(row.get("hotel_name", "")).strip(),
            "Location": f"{row.get('city', '')}, {row.get('country', '')}",
            "Price": f"${row.get('price_per_night', 0)}",
            "Rating": f"{row.get('rating', 0):.1f}",
        }
        docs.append(format_doc(doc_parts))
        metadata.append({"hotel_name": row.get("hotel_name")})

    return docs, metadata
```

#### Step 2: Import in Your Main Application

**`main.py`:**

```python
# Import your converter (this registers it automatically)
from converters.travel_converter import convert_travel_bookings

# Now use it with the registered schema
from artemis.rag import csv_to_documents, DocumentSchema, Retriever, RetrievalMode

# Use registered schema (optional - auto-detect also works)
docs, metadata = csv_to_documents("data/travel_bookings.csv", DocumentSchema.TRAVEL)

# Add to retriever
retriever = Retriever(
    mode=RetrievalMode.SEMANTIC,
    collection_name="travel_bookings"
)
retriever.add_documents(docs, metadata)

# Search for travel options
results = retriever.retrieve("Hotels in Paris under $200 with free cancellation", k=5)
```

**Note:** For MVP, you can skip custom converters entirely. Just use `csv_to_documents("travel_bookings.csv")` and it will auto-detect headers.

---

### Option 2: In A.R.T.E.M.I.S. Repository (For Development)

If you're contributing to A.R.T.E.M.I.S. itself, you can add converters in the `artemis/rag/converters/` directory.

#### Project Structure

```
A.R.T.E.M.I.S/
├── artemis/
│   └── rag/
│       ├── document_converter.py  # Core converter (RESTAURANT)
│       ├── converters/             # Additional converters
│       │   ├── __init__.py        # Auto-imports converters
│       │   ├── travel.py          # Travel converter ✅ Created
│       │   └── support.py         # Support converter (future)
│       └── __init__.py            # Auto-registers converters
└── examples/                       # Example converters and guides for users
    ├── travel_converter_example.py # Example travel converter
    ├── travel_bookings_sample.csv  # Sample CSV data
    ├── README_travel_example.md    # Travel example documentation
    └── WHERE_TO_ADD_CONVERTERS.md  # This guide
```

#### File: `artemis/rag/converters/travel.py`

The travel converter is already implemented! It:

- Registers with `DocumentSchema.TRAVEL`
- Uses `format_doc()` helper for consistent formatting
- Handles multiple column name variations (hotel_name, name, property_name)
- Supports optional fields (dates, cancellation policy)
- Includes proper error handling and logging

#### Adding a New Converter (e.g., Support)

1. **Create** `artemis/rag/converters/support.py`:

```python
from artemis.rag.core.document_converter import register_schema, format_doc, DocumentSchema
import pandas as pd

@register_schema(DocumentSchema.SUPPORT)
def convert_support(csv_path: str):
    # Your implementation
    ...
```

2. **Add import** to `artemis/rag/converters/__init__.py`:

```python
from artemis.rag.converters.support import convert_support
```

That's it! The converter is automatically registered when the module is imported.

---

### Option 3: Standalone Script (Quick Testing)

For quick testing, create a single file that does everything:

**`my_travel_app.py`:**

```python
#!/usr/bin/env python3
"""Standalone travel booking app with custom converter."""

# Import A.R.T.E.M.I.S.
from artemis.rag import DocumentSchema, register_schema, format_doc, csv_to_documents, Retriever, RetrievalMode
import pandas as pd
import os

# Define and register converter in the same file
@register_schema(DocumentSchema.TRAVEL)
def convert_travel(csv_path: str):
    df = pd.read_csv(csv_path)
    docs, metadata = [], []
    # ... conversion logic ...
    return docs, metadata

# Main application
if __name__ == "__main__":
    # Convert CSV
    docs, metadata = csv_to_documents("travel_bookings.csv", DocumentSchema.TRAVEL)

    # Setup retriever
    retriever = Retriever(
        mode=RetrievalMode.SEMANTIC,
        qdrant_url=os.getenv("QDRANT_URL"),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        collection_name="travel"
    )

    # Add documents
    retriever.add_documents(docs, metadata)

    # Search
    results = retriever.retrieve("Hotels in Paris under $200", k=5)
    print(results)
```

---

## 🧳 Travel Booking Example

### Complete Travel Converter Implementation

See `travel_converter_example.py` for a full implementation. Here's what it does:

```python
from artemis.rag import DocumentSchema, register_schema, format_doc
import pandas as pd

@register_schema(DocumentSchema.TRAVEL)
def convert_travel_bookings(csv_path: str):
    """Convert travel booking CSV to documents."""
    df = pd.read_csv(csv_path)
    docs, metadata = [], []

    for _, row in df.iterrows():
        # Extract and format fields
        hotel = str(row.get("hotel_name", "")).strip()
        city = str(row.get("city", "")).strip()
        country = str(row.get("country", "")).strip()
        price = f"${int(row.get('price_per_night', 0))}" if pd.notna(row.get('price_per_night')) else "N/A"
        rating = f"{row.get('rating', 0):.1f}" if pd.notna(row.get('rating')) else "N/A"

        # Use format_doc helper for consistent formatting
        doc_parts = {
            "Hotel": hotel,
            "Location": f"{city}, {country}",
            "Price per night": price,
            "Rating": rating,
            "Amenities": str(row.get("amenities", "")).strip(),
        }

        docs.append(format_doc(doc_parts))

        # Store metadata
        metadata.append({
            "hotel_name": hotel,
            "city": city,
            "price_per_night": float(row.get("price_per_night", 0)) if pd.notna(row.get("price_per_night")) else None,
            "rating": float(row.get("rating", 0)) if pd.notna(row.get("rating")) else None,
        })

    return docs, metadata
```

### CSV Format

Your travel bookings CSV should have these columns:

- `hotel_name` - Name of the hotel
- `city` - City location
- `country` - Country location
- `check_in` - Check-in date (optional)
- `check_out` - Check-out date (optional)
- `price_per_night` - Price per night (numeric)
- `rating` - Hotel rating (numeric, 0-5)
- `amenities` - Comma-separated amenities
- `room_type` - Type of room (optional)
- `cancellation_policy` - Cancellation policy description (optional)

### Generated Document Format

Each row becomes a document like:

```
Hotel: Grand Hotel Paris. Location: Paris, France. Dates: 2025-06-15 to 2025-06-20.
Price per night: $250. Rating: 4.5. Room type: Deluxe Suite.
Amenities: WiFi, Pool, Gym, Spa. Cancellation: Free cancellation until 24h before.
```

This format is optimized for semantic search queries like:

- "Hotels in Paris under $200"
- "Resorts with spa and pool in Bali"
- "Hotels with free cancellation in Tokyo"

---

## 🔑 Key Points

### Simple Usage (Recommended for MVP)

1. **Auto-Detect Works**: `csv_to_documents("any_file.csv")` works with any CSV structure
2. **Zero Configuration**: No schemas, registries, or converters needed
3. **Works Out of the Box**: Just pass your CSV file path

### Advanced Usage (Future Extensibility)

1. **Import = Registration**: Just importing the module registers the converter (decorator runs on import)
2. **Your Project**: Add converters in your own project, not in A.R.T.E.M.I.S. repo
3. **Any Location**: Converters can be in any Python file, just import them before use
4. **No Core Changes**: You never need to modify A.R.T.E.M.I.S. core code
5. **Use format_doc()**: The helper function ensures consistent formatting across converters

---

## 📁 Complete Project Structure Example

```
my-travel-booking-app/
├── app.py                    # Main application
├── converters/
│   ├── __init__.py          # Empty or imports converters
│   ├── travel.py            # Travel converter
│   └── support.py           # Support tickets converter (if needed)
├── data/
│   └── travel_bookings.csv
├── .env
└── requirements.txt
```

**`app.py` (Simple - Recommended):**

```python
# Simple usage - auto-detect works with any CSV
from artemis.rag import csv_to_documents, Retriever, RetrievalMode

docs, metadata = csv_to_documents("data/travel_bookings.csv")  # Auto-detects headers
retriever = Retriever(mode=RetrievalMode.SEMANTIC, collection_name="travel")
retriever.add_documents(docs, metadata)
results = retriever.retrieve("Hotels in Paris under $200", k=5)
```

**`app.py` (Advanced - With Custom Schema):**

```python
# Import converters first (registers them)
from converters import travel  # Registers travel converter

# Now use A.R.T.E.M.I.S. with registered schema
from artemis.rag import csv_to_documents, DocumentSchema, Retriever, RetrievalMode

docs, metadata = csv_to_documents("data/travel_bookings.csv", DocumentSchema.TRAVEL)
retriever = Retriever(mode=RetrievalMode.SEMANTIC, collection_name="travel")
retriever.add_documents(docs, metadata)
results = retriever.retrieve("Hotels in Paris under $200", k=5)
```

---

## 🛠️ Using the format_doc Helper

The `format_doc()` helper provides consistent document formatting:

```python
from artemis.rag import format_doc

doc_parts = {
    "Product": "Laptop",
    "Category": "Electronics",
    "Price": "$999",
    "In Stock": "Yes",
}

document = format_doc(doc_parts)
# Returns: "Product: Laptop. Category: Electronics. Price: $999. In Stock: Yes."
```

This helper automatically:

- Filters out empty, None, or "N/A" values
- Formats as "Label: value." pairs
- Joins them with spaces for readability

---

## 💡 Benefits

### Simple Usage (Auto-Detect)

- **Zero Configuration**: Works with any CSV structure automatically
- **No Learning Curve**: Just pass your CSV file path
- **Fast Setup**: Get started in seconds, not minutes

### Advanced Usage (Custom Schemas)

- **No Core Changes**: Add new schemas without modifying A.R.T.E.M.I.S. code
- **Consistent Formatting**: Use `format_doc()` for uniform document structure
- **Easy Integration**: Your converters work seamlessly with the retrieval system
- **Framework Feel**: A.R.T.E.M.I.S. becomes a true extensible framework
- **Future-Proof**: Registry system ready for when you need it
