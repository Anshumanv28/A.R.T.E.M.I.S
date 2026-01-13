"""
Filter builder for Qdrant metadata filtering in A.R.T.E.M.I.S.

Converts FilterCondition objects to Qdrant Filter objects for use
in query_points() calls.
"""

from typing import List, Optional

from qdrant_client.models import Filter, FieldCondition, Range, MatchValue

from artemis.rag.core.query_parser import FilterCondition
from artemis.utils import get_logger

logger = get_logger(__name__)


def build_qdrant_filter(conditions: List[FilterCondition]) -> Optional[Filter]:
    """
    Build a Qdrant Filter object from filter conditions.
    
    Converts FilterCondition objects to Qdrant's Filter format,
    which can be used in query_points() calls.
    
    Args:
        conditions: List of FilterCondition objects
        
    Returns:
        Qdrant Filter object, or None if no conditions provided
        
    Example:
        >>> conditions = [
        ...     FilterCondition(field="city", operator="eq", value="Mumbai"),
        ...     FilterCondition(field="rating", operator="gt", value=4.5)
        ... ]
        >>> filter_obj = build_qdrant_filter(conditions)
        >>> # Use in query_points(query_filter=filter_obj)
    """
    if not conditions:
        return None
    
    field_conditions = []
    
    for condition in conditions:
        try:
            field_condition = _build_field_condition(condition)
            if field_condition:
                field_conditions.append(field_condition)
        except Exception as e:
            logger.warning(
                f"Failed to build filter condition for {condition}: {e}. "
                "Skipping this condition."
            )
            continue
    
    if not field_conditions:
        logger.debug("No valid field conditions built, returning None")
        return None
    
    # Combine all conditions with AND logic (must satisfy all)
    qdrant_filter = Filter(must=field_conditions)
    logger.debug(f"Built Qdrant filter with {len(field_conditions)} condition(s)")
    return qdrant_filter


def _build_field_condition(condition: FilterCondition) -> Optional[FieldCondition]:
    """
    Build a Qdrant FieldCondition from a FilterCondition.
    
    Args:
        condition: FilterCondition object
        
    Returns:
        Qdrant FieldCondition object, or None if condition is invalid
    """
    field = condition.field
    operator = condition.operator
    value = condition.value
    
    # Handle string equality
    if operator == "eq":
        if isinstance(value, str):
            return FieldCondition(
                key=field,
                match=MatchValue(value=value)
            )
        elif isinstance(value, bool):
            return FieldCondition(
                key=field,
                match=MatchValue(value=value)
            )
        elif isinstance(value, (int, float)):
            # For numeric equality, use range with same min/max
            return FieldCondition(
                key=field,
                range=Range(gte=value, lte=value)
            )
    
    # Handle numeric comparisons
    elif operator == "gt":
        if isinstance(value, (int, float)):
            return FieldCondition(
                key=field,
                range=Range(gt=value)
            )
    
    elif operator == "lt":
        if isinstance(value, (int, float)):
            return FieldCondition(
                key=field,
                range=Range(lt=value)
            )
    
    elif operator == "gte":
        if isinstance(value, (int, float)):
            return FieldCondition(
                key=field,
                range=Range(gte=value)
            )
    
    elif operator == "lte":
        if isinstance(value, (int, float)):
            return FieldCondition(
                key=field,
                range=Range(lte=value)
            )
    
    # Handle contains (for string matching)
    elif operator == "contains":
        if isinstance(value, str):
            # Qdrant doesn't have direct "contains", use match with text
            # This is a simplified approach - for full text search, might need different approach
            return FieldCondition(
                key=field,
                match=MatchValue(value=value)
            )
    
    else:
        logger.warning(f"Unsupported operator: {operator} for field {field}")
        return None
    
    return None
