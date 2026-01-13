"""
Query parser for metadata filtering in A.R.T.E.M.I.S.

Extracts filter conditions from natural language queries to enable
metadata-based filtering in semantic search.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Any, Optional

from artemis.utils import get_logger

logger = get_logger(__name__)


@dataclass
class FilterCondition:
    """Represents a single filter condition extracted from a query."""
    
    field: str          # Metadata field name (e.g., "city", "rating")
    operator: str       # "eq", "gt", "lt", "gte", "lte", "contains"
    value: Any          # Filter value
    
    def __repr__(self):
        return f"FilterCondition(field='{self.field}', operator='{self.operator}', value={self.value!r})"


# Common field aliases for auto-detection
FIELD_ALIASES = {
    # Location/city
    "city": ["city", "location", "place", "area"],
    # Price/cost
    "cost_for_two": ["cost", "price", "cost_for_two", "cost for two", "budget"],
    # Rating
    "rating": ["rating", "rate", "stars", "score"],
    # Boolean features
    "has_online_delivery": ["online delivery", "delivery", "online", "has delivery"],
    "has_table_booking": ["table booking", "booking", "reservation", "table"],
}


def _normalize_field_name(field_hint: str) -> Optional[str]:
    """
    Normalize a field hint to actual metadata field name.
    
    Args:
        field_hint: Potential field name or alias from query
        
    Returns:
        Normalized field name or None if not found
    """
    field_hint_lower = field_hint.lower().strip()
    
    # Direct match
    if field_hint_lower in FIELD_ALIASES:
        return field_hint_lower
    
    # Check aliases
    for field_name, aliases in FIELD_ALIASES.items():
        if field_hint_lower in aliases:
            return field_name
    
    return None


def parse_query(query: str) -> Tuple[str, List[FilterCondition]]:
    """
    Parse natural language query to extract filter conditions.
    
    Extracts filter conditions from queries like:
    - "Italian restaurants in Mumbai" → city == "Mumbai"
    - "Restaurants under 500 rupees" → cost_for_two < 500
    - "Rating above 4.5" → rating > 4.5
    - "With online delivery" → has_online_delivery == true
    
    Args:
        query: Natural language query string
        
    Returns:
        Tuple of (cleaned_query, filter_conditions) where:
        - cleaned_query: Query with filter phrases removed (for embedding)
        - filter_conditions: List of FilterCondition objects
    """
    original_query = query
    conditions = []
    cleaned_parts = []
    
    # Track what we've removed to build cleaned query
    query_lower = query.lower()
    
    # Pattern 1: Location constraints - "in {city}", "from {city}"
    # Match: "in Mumbai", "from Bangalore", "located in Delhi"
    location_patterns = [
        r'\b(?:in|from|located in|at)\s+([A-Z][a-zA-Z\s]+?)(?:\s|$|,|\.)',
        r'\b(?:in|from|located in|at)\s+([a-z]+(?:\s+[a-z]+)*?)(?:\s|$|,|\.)',
    ]
    
    for pattern in location_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            city = match.group(1).strip()
            # Remove common trailing words
            city = re.sub(r'\s+(city|place|area)$', '', city, flags=re.IGNORECASE)
            
            if city and len(city) > 1:  # Valid city name
                conditions.append(FilterCondition(
                    field="city",
                    operator="eq",
                    value=city.strip()
                ))
                # Remove this phrase from cleaned query
                query = query[:match.start()] + " " + query[match.end():]
                logger.debug(f"Extracted location filter: city == '{city}'")
    
    # Pattern 2: Numeric comparisons - "under {n}", "above {n}", "below {n}", "over {n}"
    # Also: "less than", "more than", "greater than"
    numeric_patterns = [
        (r'\b(?:under|below|less than|lower than)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|rs|rs\.|dollars?|\$|rating|stars?)?', 'lt'),
        (r'\b(?:above|over|more than|greater than|higher than)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|rs|rs\.|dollars?|\$|rating|stars?)?', 'gt'),
        (r'\b(?:at least|minimum|min)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|rs|rs\.|dollars?|\$|rating|stars?)?', 'gte'),
        (r'\b(?:at most|maximum|max)\s+(\d+(?:\.\d+)?)\s*(?:rupees?|rs|rs\.|dollars?|\$|rating|stars?)?', 'lte'),
    ]
    
    for pattern, operator in numeric_patterns:
        matches = re.finditer(pattern, query, re.IGNORECASE)
        for match in matches:
            value_str = match.group(1)
            try:
                value = float(value_str)
                
                # Detect field from context
                match_text = match.group(0).lower()
                field = None
                
                # Check for price/cost indicators
                if any(word in match_text for word in ['rupee', 'rs', 'dollar', '$', 'cost', 'price', 'budget']):
                    field = "cost_for_two"
                # Check for rating indicators
                elif any(word in match_text for word in ['rating', 'star', 'score']):
                    field = "rating"
                # Default: if value is < 10, likely rating; if >= 10, likely price
                else:
                    if value < 10:
                        field = "rating"
                    else:
                        field = "cost_for_two"
                
                if field:
                    conditions.append(FilterCondition(
                        field=field,
                        operator=operator,
                        value=value
                    ))
                    # Remove this phrase from cleaned query
                    query = query[:match.start()] + " " + query[match.end():]
                    logger.debug(f"Extracted numeric filter: {field} {operator} {value}")
            except ValueError:
                continue
    
    # Pattern 3: Boolean features - "with {feature}", "has {feature}", "{feature} available"
    boolean_patterns = [
        (r'\bwith\s+(?:online\s+)?delivery\b', 'has_online_delivery', True),
        (r'\bhas\s+(?:online\s+)?delivery\b', 'has_online_delivery', True),
        (r'\b(?:online\s+)?delivery\s+available\b', 'has_online_delivery', True),
        (r'\bwith\s+table\s+booking\b', 'has_table_booking', True),
        (r'\bhas\s+table\s+booking\b', 'has_table_booking', True),
        (r'\btable\s+booking\s+available\b', 'has_table_booking', True),
    ]
    
    for pattern, field, value in boolean_patterns:
        matches = list(re.finditer(pattern, query, re.IGNORECASE))
        for match in matches:
            conditions.append(FilterCondition(
                field=field,
                operator="eq",
                value=value
            ))
            # Remove this phrase from cleaned query
            query = query[:match.start()] + " " + query[match.end():]
            logger.debug(f"Extracted boolean filter: {field} == {value}")
    
    # Clean up the query: remove extra spaces, normalize
    cleaned_query = re.sub(r'\s+', ' ', query).strip()
    
    # If no filters extracted, return original query
    if not conditions:
        logger.debug("No filter conditions extracted from query")
        return original_query, []
    
    logger.debug(f"Extracted {len(conditions)} filter condition(s) from query")
    return cleaned_query, conditions
