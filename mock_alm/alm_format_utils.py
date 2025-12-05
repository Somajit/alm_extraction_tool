"""
alm_format_utils.py

Generic utilities for converting between ALM REST API format and simplified JSON format.

ALM REST API Response Format (from official documentation):
{
  "entities": [
    {
      "Type": "test",
      "Fields": [
        {"Name": "id", "values": [{"value": "1001"}]},
        {"Name": "name", "values": [{"value": "Test Name"}]},
        {"Name": "status", "values": [{"value": "Ready"}]}
      ]
    }
  ],
  "TotalResults": 1
}

Simplified Format (for internal use):
{
  "id": "1001",
  "name": "Test Name",
  "status": "Ready"
}
"""

from typing import Any, Dict, List, Optional


def alm_to_simple(alm_response: Dict[str, Any]) -> tuple[List[Dict[str, Any]], int]:
    """
    Convert ALM REST API response format to simplified dictionary format.
    
    Args:
        alm_response: ALM response with 'entities' and 'TotalResults'
    
    Returns:
        Tuple of (list of simplified entities, total count)
    
    Example:
        Input:
        {
          "entities": [{
            "Type": "test",
            "Fields": [
              {"Name": "id", "values": [{"value": "1001"}]},
              {"Name": "name", "values": [{"value": "Login Test"}]}
            ]
          }],
          "TotalResults": 1
        }
        
        Output:
        ([{"id": "1001", "name": "Login Test"}], 1)
    """
    entities = []
    total_results = alm_response.get('TotalResults', 0)
    
    for entity_data in alm_response.get('entities', []):
        entity = {}
        
        # Extract entity type (optional)
        entity_type = entity_data.get('Type', '')
        if entity_type:
            entity['_type'] = entity_type
        
        # Extract fields
        fields = entity_data.get('Fields', [])
        for field in fields:
            field_name = field.get('Name', '')
            values = field.get('values', [])
            
            if field_name:
                if values and len(values) > 0:
                    # Get first value
                    value = values[0].get('value')
                    entity[field_name] = value
                else:
                    entity[field_name] = None
        
        if entity:
            entities.append(entity)
    
    return entities, total_results


def simple_to_alm(
    entities: List[Dict[str, Any]],
    entity_type: str = "entity"
) -> Dict[str, Any]:
    """
    Convert simplified dictionary format to ALM REST API response format.
    
    Args:
        entities: List of simplified entity dictionaries
        entity_type: Type of entity (test, defect, test-folder, etc.)
    
    Returns:
        ALM-formatted response dictionary
    
    Example:
        Input:
        ([{"id": "1001", "name": "Login Test"}], "test")
        
        Output:
        {
          "entities": [{
            "Type": "test",
            "Fields": [
              {"Name": "id", "values": [{"value": "1001"}]},
              {"Name": "name", "values": [{"value": "Login Test"}]}
            ]
          }],
          "TotalResults": 1
        }
    """
    alm_entities = []
    
    for entity in entities:
        # Use entity type from data if available, otherwise use parameter
        ent_type = entity.pop('_type', entity_type)
        
        # Convert each field to ALM format
        fields = []
        for field_name, field_value in entity.items():
            field = {
                "Name": field_name,
                "values": []
            }
            
            # Add value if not None
            if field_value is not None:
                field["values"].append({"value": str(field_value)})
            
            fields.append(field)
        
        alm_entity = {
            "Type": ent_type,
            "Fields": fields
        }
        
        alm_entities.append(alm_entity)
    
    return {
        "entities": alm_entities,
        "TotalResults": len(alm_entities)
    }


def parse_alm_entity_field(field: Dict[str, Any]) -> tuple[str, Any]:
    """
    Parse a single ALM field structure.
    
    Args:
        field: ALM field dict with 'Name' and 'values'
    
    Returns:
        Tuple of (field_name, field_value)
    """
    field_name = field.get('Name', '')
    values = field.get('values', [])
    
    if values and len(values) > 0:
        field_value = values[0].get('value')
    else:
        field_value = None
    
    return field_name, field_value


def build_alm_field(field_name: str, field_value: Any) -> Dict[str, Any]:
    """
    Build a single ALM field structure.
    
    Args:
        field_name: Name of the field
        field_value: Value of the field
    
    Returns:
        ALM field dictionary
    """
    field = {
        "Name": field_name,
        "values": []
    }
    
    if field_value is not None:
        field["values"].append({"value": str(field_value)})
    
    return field


def extract_field_value(entity: Dict[str, Any], field_name: str, default: Any = None) -> Any:
    """
    Extract a field value from an ALM entity (either format).
    
    Handles both ALM format (with Fields array) and simplified format.
    
    Args:
        entity: Entity dictionary (either format)
        field_name: Name of field to extract
        default: Default value if field not found
    
    Returns:
        Field value or default
    """
    # Check if it's already in simplified format
    if field_name in entity:
        return entity.get(field_name, default)
    
    # Try to parse as ALM format
    fields = entity.get('Fields', [])
    for field in fields:
        if field.get('Name') == field_name:
            values = field.get('values', [])
            if values and len(values) > 0:
                return values[0].get('value', default)
    
    return default


def build_alm_query_filter(filters: Dict[str, Any]) -> str:
    """
    Build ALM query filter string from dictionary.
    
    Args:
        filters: Dictionary of field:value pairs
    
    Returns:
        ALM query string like "{field1[value1];field2[value2]}"
    
    Example:
        Input: {"status": "Ready", "owner": "john"}
        Output: "{status[Ready];owner[john]}"
    """
    if not filters:
        return ""
    
    filter_parts = []
    for field, value in filters.items():
        if value is not None:
            filter_parts.append(f"{field}[{value}]")
    
    if not filter_parts:
        return ""
    
    return "{" + ";".join(filter_parts) + "}"


def parse_alm_query_filter(query_string: str) -> Dict[str, Any]:
    """
    Parse ALM query filter string to dictionary.
    
    Args:
        query_string: ALM query like "{field1[value1];field2[value2]}"
    
    Returns:
        Dictionary of field:value pairs
    
    Example:
        Input: "{status[Ready];owner[john]}"
        Output: {"status": "Ready", "owner": "john"}
    """
    import re
    
    filters = {}
    
    # Remove outer braces
    query_string = query_string.strip("{}")
    
    # Split by semicolon
    parts = query_string.split(";")
    
    for part in parts:
        # Match pattern: field[value]
        match = re.match(r'([^\[]+)\[([^\]]+)\]', part.strip())
        if match:
            field = match.group(1).strip()
            value = match.group(2).strip()
            filters[field] = value
    
    return filters


class ALMResponseBuilder:
    """
    Builder class for constructing ALM response structures.
    """
    
    def __init__(self, entity_type: str):
        """
        Initialize builder with entity type.
        
        Args:
            entity_type: Type of entity (test, defect, etc.)
        """
        self.entity_type = entity_type
        self.entities = []
    
    def add_entity(self, entity_data: Dict[str, Any]) -> 'ALMResponseBuilder':
        """
        Add an entity to the response.
        
        Args:
            entity_data: Simplified entity dictionary
        
        Returns:
            Self for chaining
        """
        self.entities.append(entity_data)
        return self
    
    def add_entities(self, entities_data: List[Dict[str, Any]]) -> 'ALMResponseBuilder':
        """
        Add multiple entities to the response.
        
        Args:
            entities_data: List of simplified entity dictionaries
        
        Returns:
            Self for chaining
        """
        self.entities.extend(entities_data)
        return self
    
    def build(self) -> Dict[str, Any]:
        """
        Build the final ALM response.
        
        Returns:
            ALM-formatted response dictionary
        """
        return simple_to_alm(self.entities, self.entity_type)


class ALMResponseParser:
    """
    Parser class for extracting data from ALM responses.
    """
    
    def __init__(self, alm_response: Dict[str, Any]):
        """
        Initialize parser with ALM response.
        
        Args:
            alm_response: ALM-formatted response dictionary
        """
        self.raw_response = alm_response
        self.entities, self.total = alm_to_simple(alm_response)
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get all entities in simplified format."""
        return self.entities
    
    def get_total(self) -> int:
        """Get total count of entities."""
        return self.total
    
    def get_first(self) -> Optional[Dict[str, Any]]:
        """Get first entity or None."""
        return self.entities[0] if self.entities else None
    
    def filter_by(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """
        Filter entities by field value.
        
        Args:
            field: Field name to filter on
            value: Value to match
        
        Returns:
            List of matching entities
        """
        return [e for e in self.entities if e.get(field) == value]
    
    def get_field_values(self, field: str) -> List[Any]:
        """
        Extract all values for a specific field.
        
        Args:
            field: Field name
        
        Returns:
            List of field values
        """
        return [e.get(field) for e in self.entities if field in e]
