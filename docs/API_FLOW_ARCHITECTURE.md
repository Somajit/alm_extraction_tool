# API Flow Architecture

## Core Principle

**All backend API endpoints MUST follow this flow**:

```
Frontend Request
    ↓
Backend API Endpoint
    ↓
Call ALM/Mock ALM API
    ↓
Parse ALM Response
    ↓
Store/Update in MongoDB (using standardized entity format)
    ↓
Query from MongoDB
    ↓
Transform to Display Format (aliases, display=true only)
    ↓
Return to Frontend
```

## Critical Rules

### ❌ NEVER DO THIS:
```python
# BAD - Returning ALM data directly
@app.get("/api/get_domains")
async def get_domains(username: str):
    alm_response = await alm_client.fetch_domains()
    return alm_response  # ❌ WRONG
```

### ✅ ALWAYS DO THIS:
```python
# GOOD - Store in MongoDB first, then query
@app.get("/api/get_domains")
async def get_domains(username: str):
    # 1. Call ALM API
    alm_response = await alm_client.fetch_domains()
    
    # 2. Parse and store in MongoDB
    for domain_data in alm_response["entities"]:
        entity = ALMConfig.parse_alm_response_to_entity(
            endpoint_name="domains",
            response_data=domain_data,
            username=username
        )
        await db.domains.replace_one(
            {"user": username, "id": entity["id"]},
            entity,
            upsert=True
        )
    
    # 3. Query from MongoDB
    domains = await db.domains.find({"user": username}).to_list(None)
    
    # 4. Transform to display format
    display_domains = [
        ALMConfig.entity_to_display_format(domain)
        for domain in domains
    ]
    
    # 5. Return MongoDB data (not ALM data)
    return {
        "success": True,
        "domains": display_domains
    }
```

## Why This Pattern?

### Benefits

1. **Single Source of Truth**: MongoDB is always the source of truth for frontend
2. **Offline Capability**: Frontend can query cached data even if ALM is down
3. **Performance**: Subsequent queries don't hit ALM
4. **Consistency**: All data goes through same parsing/validation
5. **Audit Trail**: All ALM data is persisted with metadata
6. **Display Control**: Field filtering happens at query time
7. **Testing**: Can test frontend with MongoDB data without ALM

### Use Cases

**Scenario 1: User expands a folder**
```
1. Frontend calls: POST /api/expand_testplan_folder {folder_id: "123"}
2. Backend calls ALM: GET /rest/.../test-folders?query={parent-id[123]}
3. Backend stores: subfolders → testplan_folders collection
4. Backend calls ALM: GET /rest/.../tests?query={parent-id[123]}
5. Backend stores: tests → testplan_tests collection
6. Backend calls ALM: GET /rest/.../attachments?query={parent-id[123];parent-type[test-folder]}
7. Backend stores: attachments → testplan_folder_attachments + attachment_cache
8. Backend queries MongoDB: Count subfolders, tests, attachments
9. Backend returns: {subfolders: 5, tests: 12, attachments: 3}
```

**Scenario 2: User views folder details**
```
1. Frontend calls: GET /api/get_folder_details?folder_id=123
2. Backend queries MongoDB: testplan_folders collection
3. Backend transforms: Apply field filtering, use aliases
4. Backend returns: Display format with only displayable fields
5. NO ALM CALL - data already in MongoDB from previous expansion
```

**Scenario 3: User exports data**
```
1. Frontend calls: POST /api/export_to_json {collection: "testplan_tests", filter: {...}}
2. Backend queries MongoDB: testplan_tests collection (NO ALM CALL)
3. Backend transforms: Apply display format with aliases
4. Backend returns: JSON with displayable fields only
```

## Implementation Pattern

### Standard Endpoint Template

```python
@app.post("/api/endpoint_name")
async def endpoint_name(request: RequestModel):
    """
    Standard pattern for all endpoints
    """
    try:
        # PHASE 1: FETCH FROM ALM
        # ----------------------
        # 1. Get base URL from environment
        use_mock = os.getenv("USE_MOCK_ALM", "false").lower() == "true"
        base_url = os.getenv("MOCK_ALM_URL" if use_mock else "ALM_URL")
        
        # 2. Build URL and params using ALMConfig
        url = ALMConfig.build_alm_url(
            base_url=base_url,
            endpoint_name="entity-type",
            domain=request.domain,
            project=request.project
        )
        
        params = ALMConfig.build_query_params(
            endpoint_name="entity-type",
            parent_id=request.parent_id
        )
        
        # 3. Make ALM API call
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers)
            alm_data = response.json()
        
        # PHASE 2: STORE IN MONGODB
        # --------------------------
        # 4. Parse each entity from ALM response
        stored_count = 0
        for raw_entity in alm_data.get("entities", []):
            entity = ALMConfig.parse_alm_response_to_entity(
                endpoint_name="entity-type",
                response_data=raw_entity,
                username=request.username,
                parent_id=request.parent_id
            )
            
            # 5. Store in appropriate collection
            collection_name = ALMConfig.get_collection_name_from_entity_type("entity-type")
            collection = getattr(db, collection_name)
            
            await collection.replace_one(
                {"user": entity["user"], "id": entity["id"]},
                entity,
                upsert=True
            )
            stored_count += 1
        
        # PHASE 3: QUERY FROM MONGODB
        # ----------------------------
        # 6. Query stored data from MongoDB
        collection = getattr(db, collection_name)
        entities = await collection.find({
            "user": request.username,
            "parent_id": request.parent_id
        }).to_list(None)
        
        # PHASE 4: TRANSFORM & RETURN
        # ----------------------------
        # 7. Transform to display format
        display_entities = [
            ALMConfig.entity_to_display_format(entity)
            for entity in entities
        ]
        
        # 8. Return MongoDB data (never ALM data directly)
        return {
            "success": True,
            "count": len(display_entities),
            "data": display_entities  # From MongoDB, not ALM
        }
        
    except Exception as e:
        logger.error(f"Error in endpoint: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

## Attachment Handling

Attachments follow the same pattern but with file download:

```python
@app.post("/api/expand_with_attachments")
async def expand_with_attachments(request: RequestModel):
    # 1. Fetch attachment metadata from ALM
    url = ALMConfig.build_alm_url(base_url, "attachments", domain=..., project=...)
    params = ALMConfig.build_query_params("attachments", parent_id=..., parent_type=...)
    response = await client.get(url, params=params)
    alm_attachments = response.json()
    
    # 2. For each attachment
    for raw_att in alm_attachments.get("entities", []):
        # 2a. Parse and store metadata
        att_entity = ALMConfig.parse_alm_response_to_entity(
            endpoint_name="attachments",
            response_data=raw_att,
            username=request.username,
            parent_id=request.parent_id
        )
        
        # Determine collection based on parent type
        parent_type = att_entity.get("parent_type")
        collection_name = ALMConfig.get_collection_name_from_entity_type(
            "attachment",
            parent_type
        )
        await db[collection_name].replace_one(
            {"user": att_entity["user"], "id": att_entity["id"]},
            att_entity,
            upsert=True
        )
        
        # 2b. Download file content
        download_url = ALMConfig.build_alm_url(
            base_url,
            "attachment-download",
            domain=request.domain,
            project=request.project,
            id=att_entity["id"]
        )
        file_response = await client.get(download_url)
        
        # 2c. Store file in attachment_cache
        await db.attachment_cache.replace_one(
            {
                "user": request.username,
                "attachment_id": att_entity["id"],
                "parent_id": request.parent_id,
                "parent_type": parent_type
            },
            {
                "user": request.username,
                "attachment_id": att_entity["id"],
                "parent_id": request.parent_id,
                "parent_type": parent_type,
                "filename": att_entity.get("name"),
                "file_content": file_response.content,
                "content_type": file_response.headers.get("content-type"),
                "size": len(file_response.content),
                "downloaded_at": datetime.utcnow()
            },
            upsert=True
        )
    
    # 3. Query from MongoDB (not from ALM response)
    attachments = await db[collection_name].find({
        "user": request.username,
        "parent_id": request.parent_id
    }).to_list(None)
    
    # 4. Transform and return
    display_attachments = [
        ALMConfig.entity_to_display_format(att)
        for att in attachments
    ]
    
    return {
        "success": True,
        "attachments": len(display_attachments),
        "data": display_attachments
    }
```

## Query-Only Endpoints

Some endpoints may only query MongoDB without calling ALM:

```python
@app.get("/api/get_cached_data")
async def get_cached_data(username: str, collection: str, filter: dict):
    """
    Query-only endpoint - NO ALM CALL
    Used when data is already in MongoDB from previous operations
    """
    # 1. Validate collection name
    if collection not in ALLOWED_COLLECTIONS:
        raise ValueError(f"Invalid collection: {collection}")
    
    # 2. Query MongoDB only
    collection_obj = getattr(db, collection)
    entities = await collection_obj.find({
        "user": username,
        **filter
    }).to_list(None)
    
    # 3. Transform and return
    display_entities = [
        ALMConfig.entity_to_display_format(entity)
        for entity in entities
    ]
    
    return {
        "success": True,
        "count": len(display_entities),
        "data": display_entities
    }
```

## Error Handling

### ALM Unreachable
```python
try:
    alm_response = await client.get(url)
except httpx.RequestError as e:
    # ALM is down, try to return cached data from MongoDB
    logger.warning(f"ALM unreachable: {e}, returning cached data")
    cached_entities = await db[collection_name].find(filter).to_list(None)
    
    if cached_entities:
        return {
            "success": True,
            "cached": True,
            "warning": "Data from cache, ALM unavailable",
            "data": [ALMConfig.entity_to_display_format(e) for e in cached_entities]
        }
    else:
        raise HTTPException(503, "ALM unavailable and no cached data")
```

### ALM Error Response
```python
if response.status_code != 200:
    logger.error(f"ALM error: {response.status_code} - {response.text}")
    # Try to return cached data
    cached_entities = await db[collection_name].find(filter).to_list(None)
    
    if cached_entities:
        return {
            "success": True,
            "cached": True,
            "warning": f"ALM error {response.status_code}, returning cached data",
            "data": [ALMConfig.entity_to_display_format(e) for e in cached_entities]
        }
    else:
        raise HTTPException(502, f"ALM error: {response.status_code}")
```

## Data Freshness

### Cache Invalidation Strategy

**Option 1: Time-Based**
```python
# Add timestamp to entities
entity["fetched_at"] = datetime.utcnow()

# Check age before returning
cache_max_age = timedelta(hours=1)
if entity.get("fetched_at"):
    age = datetime.utcnow() - entity["fetched_at"]
    if age > cache_max_age:
        # Data too old, refetch from ALM
        await fetch_from_alm_and_store()
```

**Option 2: Explicit Refresh**
```python
@app.post("/api/refresh_data")
async def refresh_data(collection: str, filter: dict):
    """Force refresh from ALM"""
    # Delete cached data
    await db[collection].delete_many(filter)
    
    # Fetch fresh from ALM
    await fetch_from_alm_and_store()
```

**Option 3: User-Initiated (Recommended)**
```python
# Frontend has "Refresh" button
# User clicks → Backend fetches from ALM → Updates MongoDB → Returns new data
```

## Monitoring & Logging

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def endpoint_with_monitoring(request: RequestModel):
    start_time = datetime.utcnow()
    
    try:
        # Log ALM call
        logger.info(f"Fetching from ALM: endpoint={endpoint_name}, user={request.username}")
        alm_response = await fetch_from_alm()
        logger.info(f"ALM response: {len(alm_response.get('entities', []))} entities")
        
        # Log MongoDB storage
        logger.info(f"Storing in MongoDB: collection={collection_name}")
        await store_in_mongodb(entities)
        logger.info(f"Stored {len(entities)} entities")
        
        # Log query
        logger.info(f"Querying MongoDB: collection={collection_name}, filter={filter}")
        results = await query_mongodb()
        logger.info(f"Query returned {len(results)} results")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Request completed in {duration:.2f}s")
        
        return {"success": True, "data": results}
        
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Request failed after {duration:.2f}s: {str(e)}")
        raise
```

## Summary

### Golden Rules

1. ✅ **Always fetch from ALM first**
2. ✅ **Always store in MongoDB**
3. ✅ **Always query from MongoDB**
4. ✅ **Always transform to display format**
5. ✅ **Never return ALM data directly to frontend**

### Data Flow

```
ALM (Source) → Backend Processing → MongoDB (Cache/Storage) → Display Transform → Frontend
```

### Benefits Recap

- **Consistency**: All data flows through same pipeline
- **Reliability**: Frontend works even if ALM is down
- **Performance**: Cached data reduces ALM load
- **Auditability**: All data persisted with metadata
- **Flexibility**: Display format controlled by configuration
- **Testability**: Can mock MongoDB without ALM
