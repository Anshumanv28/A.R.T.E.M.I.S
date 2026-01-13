"""
Metadata configuration for adaptive filtering in A.R.T.E.M.I.S.

Optional configuration class for custom field mappings, aliases, and
type hints when auto-discovery isn't sufficient.
"""

from typing import Dict, List, Optional, Tuple, Any

from artemis.utils import get_logger

logger = get_logger(__name__)


class MetadataConfig:
    """
    Optional configuration for metadata filtering.
    
    Allows custom field mappings, aliases, and type hints when
    auto-discovery isn't sufficient or you want to override defaults.
    
    Example:
        >>> config = MetadataConfig(
        ...     field_aliases={"price_per_night": ["price", "rate", "cost"]},
        ...     field_types={"price_per_night": "number"},
        ...     boolean_patterns=[("has_spa", "spa"), ("has_pool", "pool")]
        ... )
    """
    
    def __init__(
        self,
        field_aliases: Optional[Dict[str, List[str]]] = None,
        field_types: Optional[Dict[str, str]] = None,
        boolean_patterns: Optional[List[Tuple[str, str]]] = None,
    ):
        """
        Initialize metadata configuration.
        
        Args:
            field_aliases: Optional mapping of field names to lists of aliases.
                         Example: {"price_per_night": ["price", "rate", "cost"]}
            field_types: Optional mapping of field names to types.
                        Example: {"price_per_night": "number", "city": "string"}
                        Types: "string", "number", "boolean"
            boolean_patterns: Optional list of (field_name, pattern) tuples for boolean fields.
                            Example: [("has_spa", "spa"), ("has_pool", "pool")]
                            Pattern is used to match in queries like "with spa" or "has pool"
        """
        self.field_aliases = field_aliases or {}
        self.field_types = field_types or {}
        self.boolean_patterns = boolean_patterns or []
        
        logger.debug(
            f"Created MetadataConfig with {len(self.field_aliases)} field aliases, "
            f"{len(self.field_types)} type hints, {len(self.boolean_patterns)} boolean patterns"
        )
    
    def get_aliases(self, field_name: str) -> List[str]:
        """
        Get aliases for a field name.
        
        Args:
            field_name: Name of the field
            
        Returns:
            List of aliases for the field, or empty list if none configured
        """
        return self.field_aliases.get(field_name, [])
    
    def get_field_type(self, field_name: str) -> Optional[str]:
        """
        Get type hint for a field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Type hint ('string', 'number', 'boolean') or None if not configured
        """
        return self.field_types.get(field_name)
    
    def get_boolean_patterns(self) -> List[Tuple[str, str]]:
        """
        Get boolean field patterns.
        
        Returns:
            List of (field_name, pattern) tuples
        """
        return self.boolean_patterns
