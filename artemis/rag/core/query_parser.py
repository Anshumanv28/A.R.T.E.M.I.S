"""
Query parser for metadata filtering in A.R.T.E.M.I.S.

Extracts filter conditions from natural language queries to enable
metadata-based filtering in semantic search.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple, Any, Optional, Dict

from artemis.rag.core.metadata_config import MetadataConfig
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


def _find_field_by_alias(
    alias: str,
    discovered_fields: Dict[str, str],
    metadata_config: Optional[MetadataConfig] = None
) -> Optional[str]:
    """
    Find field name by alias using discovered fields and optional config.
    
    Args:
        alias: Alias or field name hint
        discovered_fields: Dictionary of discovered field names and types
        metadata_config: Optional metadata configuration
        
    Returns:
        Field name if found, None otherwise
    """
    alias_lower = alias.lower().strip()
    
    # First check if it's a direct field name match
    if alias_lower in discovered_fields:
        return alias_lower
    
    # Check config aliases if provided
    if metadata_config:
        for field_name, aliases in metadata_config.field_aliases.items():
            if alias_lower in [a.lower() for a in aliases]:
                # Verify field exists in discovered fields
                if field_name in discovered_fields:
                    return field_name
    
    # Check common generic aliases that might map to discovered fields
    generic_aliases = {
        "location": ["city", "country", "place", "area"],
        "price": ["cost", "price", "cost_for_two", "price_per_night", "rate"],
        "rating": ["rating", "rate", "stars", "score"],
    }
    
    for generic_type, possible_fields in generic_aliases.items():
        if alias_lower in generic_type.split() or any(word in alias_lower for word in generic_type.split()):
            # Try to find matching field in discovered fields
            for field in possible_fields:
                if field in discovered_fields:
                    return field
    
    return None


def parse_query(
    query: str,
    discovered_fields: Optional[Dict[str, str]] = None,
    metadata_config: Optional[MetadataConfig] = None
) -> Tuple[str, List[FilterCondition]]:
    """
    Parse natural language query to extract filter conditions.
    
    Extracts filter conditions from queries like:
    - "Italian restaurants in Mumbai" → city == "Mumbai"
    - "Restaurants under 500 rupees" → cost_for_two < 500 (or price_per_night, etc.)
    - "Rating above 4.5" → rating > 4.5
    - "With online delivery" → has_online_delivery == true
    
    Uses discovered fields to validate extracted field names and determine types.
    If no discovered_fields provided, falls back to generic patterns (backward compatible).
    
    Args:
        query: Natural language query string
        discovered_fields: Optional dictionary of discovered field names and types
                          {field_name: 'string'|'number'|'boolean'}
        metadata_config: Optional metadata configuration for custom aliases and patterns
        
    Returns:
        Tuple of (cleaned_query, filter_conditions) where:
        - cleaned_query: Query with filter phrases removed (for embedding)
        - filter_conditions: List of FilterCondition objects
    """
    # Use empty dict if no discovered fields (backward compatible)
    if discovered_fields is None:
        discovered_fields = {}
    original_query = query
    conditions = []
    cleaned_parts = []
    
    # Track what we've removed to build cleaned query
    query_lower = query.lower()
    
    # Pattern 1: Location constraints - "in {location}", "from {location}"
    # Match: "in Mumbai", "from Bangalore", "located in Delhi"
    # Try to find a location field (city, country, etc.) in discovered fields
    location_field = None
    if discovered_fields:
        # Look for common location field names
        for field in ["city", "country", "location", "place"]:
            if field in discovered_fields and discovered_fields[field] == "string":
                location_field = field
                break
    
    # Fallback to "city" if no discovered fields (backward compatible)
    if not location_field:
        location_field = "city" if not discovered_fields else None
    
    if location_field:
        location_patterns = [
            r'\b(?:in|from|located in|at)\s+([A-Z][a-zA-Z\s]+?)(?:\s|$|,|\.)',
            r'\b(?:in|from|located in|at)\s+([a-z]+(?:\s+[a-z]+)*?)(?:\s|$|,|\.)',
        ]
        
        for pattern in location_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                location_value = match.group(1).strip()
                # Remove common trailing words
                location_value = re.sub(r'\s+(city|place|area|country)$', '', location_value, flags=re.IGNORECASE)
                
                if location_value and len(location_value) > 1:  # Valid location name
                    conditions.append(FilterCondition(
                        field=location_field,
                        operator="eq",
                        value=location_value.strip()
                    ))
                    # Remove this phrase from cleaned query
                    query = query[:match.start()] + " " + query[match.end():]
                    logger.debug(f"Extracted location filter: {location_field} == '{location_value}'")
    
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
                
                # Detect field from context using discovered fields
                match_text = match.group(0).lower()
                field = None
                
                # Check for price/cost indicators
                if any(word in match_text for word in ['rupee', 'rs', 'dollar', '$', 'cost', 'price', 'budget']):
                    # Try to find a price field in discovered fields
                    for price_field in ["cost_for_two", "price_per_night", "price", "cost"]:
                        if price_field in discovered_fields and discovered_fields[price_field] == "number":
                            field = price_field
                            break
                    # Fallback if no discovered fields (backward compatible)
                    if not field and not discovered_fields:
                        field = "cost_for_two"
                # Check for rating indicators
                elif any(word in match_text for word in ['rating', 'star', 'score']):
                    # Try to find rating field
                    if "rating" in discovered_fields:
                        field = "rating"
                    elif not discovered_fields:
                        field = "rating"  # Fallback
                # Default: if value is < 10, likely rating; if >= 10, likely price
                else:
                    if value < 10:
                        # Try rating field
                        if "rating" in discovered_fields:
                            field = "rating"
                        elif not discovered_fields:
                            field = "rating"  # Fallback
                    else:
                        # Try price fields
                        for price_field in ["cost_for_two", "price_per_night", "price", "cost"]:
                            if price_field in discovered_fields and discovered_fields[price_field] == "number":
                                field = price_field
                                break
                        # Fallback
                        if not field and not discovered_fields:
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
    
    # Pattern 2.5: Qualitative rating phrases - "best rated", "top rated", "highly rated"
    # These imply a minimum rating threshold
    if "rating" in discovered_fields or not discovered_fields:
        qualitative_rating_patterns = [
            (r'\b(?:best|top|highest)\s+rated\b', 4.0),  # "best rated" → rating >= 4.0
            (r'\b(?:highly|very)\s+rated\b', 4.0),       # "highly rated" → rating >= 4.0
            (r'\b(?:excellent|outstanding)\s+rating\b', 4.5),  # "excellent rating" → rating >= 4.5
            (r'\b(?:great|good)\s+rating\b', 3.5),      # "good rating" → rating >= 3.5
        ]
        
        for pattern, min_rating in qualitative_rating_patterns:
            matches = list(re.finditer(pattern, query, re.IGNORECASE))
            for match in matches:
                # Check if we already have a rating filter
                has_rating_filter = any(
                    cond.field == "rating" for cond in conditions
                )
                
                if not has_rating_filter:
                    conditions.append(FilterCondition(
                        field="rating",
                        operator="gte",
                        value=min_rating
                    ))
                    # Remove this phrase from cleaned query
                    query = query[:match.start()] + " " + query[match.end():]
                    logger.debug(f"Extracted qualitative rating filter: rating >= {min_rating}")
                    break  # Only extract one qualitative rating phrase
    
    # Pattern 3: Boolean features - "with {feature}", "has {feature}", "{feature} available"
    # Build boolean patterns from discovered fields and config
    boolean_patterns = []
    
    # Add patterns from config if provided
    if metadata_config:
        for field_name, pattern in metadata_config.boolean_patterns:
            if field_name in discovered_fields and discovered_fields[field_name] == "boolean":
                # Create regex pattern for the feature
                pattern_escaped = re.escape(pattern)
                boolean_patterns.extend([
                    (rf'\bwith\s+{pattern_escaped}\b', field_name, True),
                    (rf'\bhas\s+{pattern_escaped}\b', field_name, True),
                    (rf'{pattern_escaped}\s+available\b', field_name, True),
                ])
    
    # Add patterns for discovered boolean fields (generic patterns)
    if discovered_fields:
        for field_name, field_type in discovered_fields.items():
            if field_type == "boolean" and field_name not in [p[1] for p in boolean_patterns]:
                # Use field name as pattern (e.g., "has_online_delivery" -> "online delivery")
                pattern_text = field_name.replace("has_", "").replace("_", " ")
                pattern_escaped = re.escape(pattern_text)
                boolean_patterns.extend([
                    (rf'\bwith\s+{pattern_escaped}\b', field_name, True),
                    (rf'\bhas\s+{pattern_escaped}\b', field_name, True),
                    (rf'{pattern_escaped}\s+available\b', field_name, True),
                ])
    
    # Fallback: Add hardcoded patterns if no discovered fields (backward compatible)
    if not boolean_patterns and not discovered_fields:
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
