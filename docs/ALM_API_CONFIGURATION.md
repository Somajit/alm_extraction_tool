# ALM API Configuration System

## Overview
Unified configuration system for ALM and Mock ALM API interactions with standardized entity storage format.

## Key Principles

1. **Single Source of Truth**: All ALM endpoint configurations in `alm_config.py`
2. **Environment-Based Base URL**: Real ALM vs Mock ALM determined by `.env` (ALM_URL or MOCK_ALM_URL)
3. **Identical Signatures**: Real ALM and Mock ALM have identical API signatures
4. **Standardized Entity Format**: All entities stored with field metadata
5. **Display Control**: Only show fields where display=True, using aliases

## Configuration Structure

### ALM_API_CONFIGS in alm_config.py

Each endpoint configuration contains:
```python
"test-folders": {
    "path": "/rest/domains/{domain}/projects/{project}/test-folders",
    "method": "GET",
    "params": {"domain": "required", "project": "required", "parent_id": "optional"},
    "fields": ["id", "name", "parent-id", "description"],
    "query_filter": "parent-id[{parent_id}]",
    "sort_by": "id",
    "sort_order": "asc",
    "page_size": 100
}
```

**Fields**:
- `path`: API endpoint path with placeholders
- `method`: HTTP method (GET, POST, etc.)
- `params`: Required and optional parameters
- `fields`: Fields to extract from response
- `query_filter`: Query filter template with placeholders
- `sort_by`: Field name to sort by
- `sort_order`: Sort direction (asc/desc)
- `page_size`: Items per page (None if no pagination)

### Available Endpoints

| Endpoint | Path | Purpose |
|----------|------|---------|
| domains | /rest/domains | Get domains |
| projects | /rest/domains/{domain}/projects | Get projects |
| test-folders | /rest/domains/{domain}/projects/{project}/test-folders | Get test folders |
| tests | /rest/domains/{domain}/projects/{project}/tests | Get tests |
| design-steps | /rest/domains/{domain}/projects/{project}/design-steps | Get design steps |
| attachments | /rest/domains/{domain}/projects/{project}/attachments | Get attachments |
| attachment-download | /rest/domains/{domain}/projects/{project}/attachments/{id} | Download attachment |
| releases | /rest/domains/{domain}/projects/{project}/releases | Get releases |
| release-cycles | /rest/domains/{domain}/projects/{project}/release-cycles | Get release cycles |
| test-sets | /rest/domains/{domain}/projects/{project}/test-sets | Get test sets |
| test-runs | /rest/domains/{domain}/projects/{project}/runs | Get test runs |
| defects | /rest/domains/{domain}/projects/{project}/defects | Get defects |

## Usage Examples

### 1. Building ALM URL

```python
from alm_config import ALMConfig
import os

# Get base URL from environment
base_url = os.getenv("ALM_URL")  # or MOCK_ALM_URL

# Build complete URL
url = ALMConfig.build_alm_url(
    base_url=base_url,
    endpoint_name="test-folders",
    domain="DEFAULT",
    project="MyProject"
)
# Result: "http://alm.example.com/rest/domains/DEFAULT/projects/MyProject/test-folders"
```

### 2. Building Query Parameters

```python
# For test folders under parent folder 123
params = ALMConfig.build_query_params(
    endpoint_name="test-folders",
    parent_id="123",
    start_index=1,
    page_size=100
)
# Result: {
#     "query": "{parent-id[123]}",
#     "page-size": "100",
#     "start-index": "1",
#     "order-by": "{id[asc]}",
#     "fields": "id,name,parent-id,description"
# }

# For attachments
params = ALMConfig.build_query_params(
    endpoint_name="attachments",
    parent_id="456",
    parent_type="test"
)
# Result: {
#     "query": "{parent-id[456];parent-type[test]}",
#     "page-size": "100",
#     "start-index": "1",
#     "order-by": "{id[asc]}",
#     "fields": "id,name,parent-id,parent-type,file-size,description"
# }
```

### 3. Making API Call

```python
import httpx
from alm_config import ALMConfig

async def fetch_test_folders(domain: str, project: str, parent_id: str):
    base_url = os.getenv("ALM_URL")
    
    # Build URL
    url = ALMConfig.build_alm_url(
        base_url=base_url,
        endpoint_name="test-folders",
        domain=domain,
        project=project
    )
    
    # Build query params
    params = ALMConfig.build_query_params(
        endpoint_name="test-folders",
        parent_id=parent_id
    )
    
    # Make request
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        return response.json()
```

### 4. Parsing ALM Response to Standardized Entity

```python
# ALM response structure:
alm_response = {
    "Fields": [
        {"Name": "id", "values": [{"value": "123"}]},
        {"Name": "name", "values": [{"value": "Test Folder 1"}]},
        {"Name": "parent-id", "values": [{"value": "0"}]},
        {"Name": "description", "values": [{"value": "Root folder"}]}
    ]
}

# Parse to standardized entity
entity = ALMConfig.parse_alm_response_to_entity(
    endpoint_name="test-folders",
    response_data=alm_response,
    username="john.doe",
    parent_id="0"
)

# Result:
{
    "user": "john.doe",
    "id": "123",
    "name": "Test Folder 1",
    "parent_id": "0",
    "entity_type": "test-folders",
    "description": "Root folder",
    "fields": [
        {
            "field": "user",
            "alias": "Username",
            "sequence": 1,
            "display": False,
            "value": "john.doe"
        },
        {
            "field": "id",
            "alias": "Folder ID",
            "sequence": 2,
            "display": True,
            "value": "123"
        },
        {
            "field": "name",
            "alias": "Folder Name",
            "sequence": 3,
            "display": True,
            "value": "Test Folder 1"
        },
        {
            "field": "parent_id",
            "alias": "Parent Folder ID",
            "sequence": 4,
            "display": False,
            "value": "0"
        },
        {
            "field": "description",
            "alias": "Description",
            "sequence": 5,
            "display": True,
            "value": "Root folder"
        }
    ]
}
```

### 5. Storing in MongoDB

```python
# Store entity in MongoDB (includes all metadata)
await db.testplan_folders.replace_one(
    {"user": entity["user"], "id": entity["id"]},
    entity,
    upsert=True
)
```

### 6. Converting to Display Format

```python
# Convert entity to display format (for UI)
display_data = ALMConfig.entity_to_display_format(entity)

# Result (only fields where display=True, with aliases as keys):
{
    "Folder ID": "123",
    "Folder Name": "Test Folder 1",
    "Description": "Root folder"
}

# Fields with display=False are excluded:
# - "user" (Username)
# - "parent_id" (Parent Folder ID)
```

## Standardized Entity Storage Format

All entities stored in MongoDB follow this structure:

```json
{
  "user": "john.doe",
  "id": "123",
  "name": "Entity Name",
  "parent_id": "parent_id_value",
  "entity_type": "test-folder",
  "field1": "value1",
  "field2": "value2",
  "fields": [
    {
      "field": "user",
      "alias": "Username",
      "sequence": 1,
      "display": false,
      "value": "john.doe"
    },
    {
      "field": "id",
      "alias": "Entity ID",
      "sequence": 2,
      "display": true,
      "value": "123"
    },
    {
      "field": "name",
      "alias": "Entity Name",
      "sequence": 3,
      "display": true,
      "value": "Entity Name"
    }
  ]
}
```

**Key Points**:
- Top-level fields (user, id, name, parent_id) for easy querying
- Additional fields at top level for convenience
- `fields` array contains complete metadata for each field
- Each field in array has: field name, alias, sequence, display flag, value

## Environment Configuration (.env)

```ini
# For Real ALM
ALM_URL=http://alm.example.com:8080/qcbin
USE_MOCK_ALM=false

# For Mock ALM
MOCK_ALM_URL=http://localhost:5001
USE_MOCK_ALM=true
```

**Usage in code**:
```python
import os

# Determine which base URL to use
use_mock = os.getenv("USE_MOCK_ALM", "false").lower() == "true"
base_url = os.getenv("MOCK_ALM_URL" if use_mock else "ALM_URL")
```

## Mock ALM Requirements

Mock ALM must implement identical API signatures:

### Example: GET /rest/domains/{domain}/projects/{project}/test-folders

**Query Parameters** (same as real ALM):
- `query`: `{parent-id[123]}`
- `page-size`: `100`
- `start-index`: `1`
- `order-by`: `{id[asc]}`
- `fields`: `id,name,parent-id,description`

**Response Format** (same as real ALM):
```json
{
  "entities": [
    {
      "Fields": [
        {"Name": "id", "values": [{"value": "123"}]},
        {"Name": "name", "values": [{"value": "Folder Name"}]},
        {"Name": "parent-id", "values": [{"value": "0"}]},
        {"Name": "description", "values": [{"value": "Description"}]}
      ]
    }
  ],
  "TotalResults": 1
}
```

## Display Rules

### UI Display
- Show only fields where `display: true`
- Use `alias` as column header or label
- Sort columns by `sequence`

### Export (JSON/Excel)
- Show only fields where `display: true`
- Use `alias` as column header in Excel
- Use `alias` as key in JSON (pretty format)
- Sort by `sequence`

### Raw Data Access
- Use field names as keys
- Include all fields regardless of display flag
- For debugging/admin purposes only

## Helper Methods Reference

### ALMConfig.get_alm_api_config(endpoint_name)
Get complete API configuration for an endpoint.

### ALMConfig.build_alm_url(base_url, endpoint_name, **path_params)
Build complete URL with base URL and path parameters.

### ALMConfig.build_query_params(endpoint_name, start_index, page_size, **filter_params)
Build query parameters for API call.

### ALMConfig.parse_alm_response_to_entity(endpoint_name, response_data, username, parent_id)
Parse ALM response to standardized entity format with field metadata.

### ALMConfig.entity_to_display_format(entity)
Convert entity to display format (alias as keys, display=True only).

### ALMConfig.get_collection_name_from_entity_type(entity_type, parent_type)
Map ALM entity type to MongoDB collection name.

### ALMConfig.get_display_fields(collection_name)
Get list of displayable fields for a collection, sorted by sequence.

### ALMConfig.transform_to_display_format(collection_name, data)
Transform data dict to display format using aliases (legacy method).

## Complete Workflow Example

```python
import os
import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from alm_config import ALMConfig

async def expand_folder(username: str, domain: str, project: str, folder_id: str):
    """Complete workflow: fetch, parse, store, display"""
    
    # 1. Get base URL from environment
    use_mock = os.getenv("USE_MOCK_ALM", "false").lower() == "true"
    base_url = os.getenv("MOCK_ALM_URL" if use_mock else "ALM_URL")
    
    # 2. Build URL and params
    url = ALMConfig.build_alm_url(
        base_url=base_url,
        endpoint_name="test-folders",
        domain=domain,
        project=project
    )
    
    params = ALMConfig.build_query_params(
        endpoint_name="test-folders",
        parent_id=folder_id
    )
    
    # 3. Make API call
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        alm_data = response.json()
    
    # 4. Parse each entity
    entities = []
    for raw_entity in alm_data.get("entities", []):
        entity = ALMConfig.parse_alm_response_to_entity(
            endpoint_name="test-folders",
            response_data=raw_entity,
            username=username,
            parent_id=folder_id
        )
        entities.append(entity)
    
    # 5. Store in MongoDB
    mongo_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = mongo_client[os.getenv("MONGODB_DB")]
    
    for entity in entities:
        await db.testplan_folders.replace_one(
            {"user": entity["user"], "id": entity["id"]},
            entity,
            upsert=True
        )
    
    # 6. Convert to display format for API response
    display_entities = [
        ALMConfig.entity_to_display_format(entity)
        for entity in entities
    ]
    
    return {
        "success": True,
        "folder_id": folder_id,
        "subfolders": len(entities),
        "data": display_entities  # Only displayable fields with aliases
    }
```

## Benefits

1. **Centralized Configuration**: All ALM endpoint details in one place
2. **Easy Switching**: Real ALM vs Mock ALM is just an environment variable
3. **Consistent Format**: All entities stored with same structure
4. **Display Control**: Easy to control what users see
5. **Type Safety**: Configuration includes field types and requirements
6. **Maintainability**: Changes to ALM API only need updates in alm_config.py
7. **Testing**: Mock ALM uses identical configuration
8. **Documentation**: Configuration serves as API documentation

## Migration Path

### Existing Code
```python
# Old way
url = f"{base_url}/rest/domains/{domain}/projects/{project}/test-folders"
params = {"query": f"{{parent-id[{parent_id}]}}", "page-size": "100"}
```

### New Code
```python
# New way - use configuration
url = ALMConfig.build_alm_url(base_url, "test-folders", domain=domain, project=project)
params = ALMConfig.build_query_params("test-folders", parent_id=parent_id)
```

### Benefits of Migration
- All endpoints use consistent query structure
- Sorting/pagination configured automatically
- Field list always matches configuration
- Easy to update when ALM API changes
