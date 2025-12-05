# ReleaseCraft Refactoring Implementation Plan

## Overview
This document outlines the step-by-step plan to refactor the backend using:
1. Unified ALM API configuration system (alm_config.py)
2. Specific entity collections (16 collections)
3. Standardized entity storage format with field metadata
4. Rationalized API endpoints (18 endpoints)

## Current State Assessment

### Files Status
| File | Lines | Status | Issues |
|------|-------|--------|--------|
| alm_config.py | ~650 | ✅ UPDATED | Complete with ALM_API_CONFIGS |
| mongo_service.py | ~150 | ❌ OUTDATED | Uses generic collections |
| alm.py | ~800 | ❌ OUTDATED | Stores in generic collections |
| main.py | 1224 | ❌ OUTDATED | Uses generic collections, many endpoints |

### Configuration Complete
- ✅ ALM_API_CONFIGS with full endpoint specifications
- ✅ build_alm_url() method for URL construction
- ✅ build_query_params() method for query parameters
- ✅ parse_alm_response_to_entity() method for standardized parsing
- ✅ entity_to_display_format() method for UI display
- ✅ All 16 entity collections configured with field metadata

### Database State
- All 24 collections created but empty
- No data inserted yet with new structure

## Implementation Phases

### Phase 1: Core Infrastructure (2-3 hours)

#### Step 1.1: Refactor mongo_service.py
**Purpose**: Update or deprecate mongo_service.py

**Option A - Update**:
```python
# Update MongoService to work with specific collections
class MongoService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        # Define all 24 collections
        self.users = db.users
        self.domains = db.domains
        self.projects = db.projects
        self.testplan_folders = db.testplan_folders
        # ... all other collections
        
    async def insert_entity(self, collection_name: str, entity: Dict, username: str):
        """Insert entity with mandatory fields"""
        collection = getattr(self, collection_name)
        entity["user"] = username
        # Ensure mandatory fields: id, name, parent_id
        await collection.replace_one(
            {"user": username, "id": entity["id"]},
            entity,
            upsert=True
        )
```

**Option B - Deprecate**:
- Move collection definitions directly to main.py
- Remove mongo_service.py
- Use Motor collections directly in endpoints

**Recommendation**: Option B (simpler, more direct)

**Files to modify**:
- `backend/app/mongo_service.py` (deprecate or update)
- `backend/app/main.py` (remove MongoService dependency if deprecated)

#### Step 1.2: Update alm.py - Storage Methods
**Purpose**: Change data storage from generic to specific collections

**Changes needed**:
1. Remove generic `store_entity()` method
2. Add specific storage methods:
   ```python
   async def store_domains(self, domains: List[Dict]):
       """Store domains in domains collection"""
       
   async def store_projects(self, domain: str, projects: List[Dict]):
       """Store projects in projects collection"""
       
   async def store_testplan_folder(self, folder: Dict):
       """Store folder in testplan_folders collection"""
       
   async def store_testplan_tests(self, tests: List[Dict]):
       """Store tests in testplan_tests collection"""
   ```

3. Update attachment storage:
   ```python
   async def store_attachment(self, attachment: Dict, parent_type: str):
       """
       Store attachment in appropriate collection based on parent_type:
       - test-folder → testplan_folder_attachments
       - test → testplan_test_attachments
       - design-step → testplan_test_design_step_attachments
       - test-set → testlab_testset_attachments
       - defect → defect_attachments
       """
   ```

**Files to modify**:
- `backend/app/alm.py`

### Phase 2: Authentication Endpoints (1 hour)

#### Step 2.1: Implement /api/authenticate
**Location**: main.py

```python
@app.post("/api/authenticate")
async def authenticate(request: AuthRequest):
    """
    Authenticate with ALM and store credentials
    """
    # 1. Call ALM authenticate endpoint
    # 2. Call site-session endpoint
    # 3. Store cookies in ALM class
    # 4. Encrypt and store credentials in user_credentials collection
    # 5. Set logged_in=true
    return {"success": True, "user": request.username}
```

#### Step 2.2: Implement /api/logout
```python
@app.post("/api/logout")
async def logout(request: LogoutRequest):
    """
    Logout from ALM
    """
    # 1. Call ALM logout endpoint
    # 2. Clear cookies
    # 3. Update user_credentials set logged_in=false
    return {"success": True}
```

**Files to modify**:
- `backend/app/main.py`

**Collections used**:
- `user_credentials`

### Phase 3: Domain & Project Endpoints (1 hour)

#### Step 3.1: Implement /api/get_domains
```python
@app.get("/api/get_domains")
async def get_domains(username: str):
    """
    Fetch and store domains
    """
    # 1. Call ALM /rest/domains
    # 2. Parse response
    # 3. Store in domains collection with: user, id, name, parent_id=null
    # 4. Return domains list
    return {"success": True, "domains": [...]}
```

#### Step 3.2: Implement /api/get_projects
```python
@app.get("/api/get_projects")
async def get_projects(username: str, domain: str):
    """
    Fetch and store projects
    """
    # 1. Call ALM /rest/domains/{domain}/projects
    # 2. Parse response
    # 3. Store in projects collection with: user, id, name, parent_id=domain
    # 4. Return projects list
    return {"success": True, "projects": [...]}
```

**Files to modify**:
- `backend/app/main.py`
- `backend/app/alm.py` (add methods for storing domains/projects)

**Collections used**:
- `domains`
- `projects`

### Phase 4: TestPlan Expansion Endpoints (3-4 hours)

#### Step 4.1: Implement /api/expand_testplan_folder
```python
@app.post("/api/expand_testplan_folder")
async def expand_testplan_folder(request: ExpandFolderRequest):
    """
    Expand folder: get subfolders, tests, attachments
    """
    # 1. Get subfolders
    subfolders = await alm_client.get_test_folders(parent_id=request.folder_id)
    await alm_client.store_testplan_folders(subfolders)
    
    # 2. Get tests
    tests = await alm_client.get_tests(parent_id=request.folder_id)
    await alm_client.store_testplan_tests(tests)
    
    # 3. Get folder attachments
    attachments = await alm_client.get_attachments(
        parent_id=request.folder_id,
        parent_type="test-folder"
    )
    for att in attachments:
        await alm_client.store_attachment(att, "test-folder")
        # Download file
        file_data = await alm_client.download_attachment(att["id"])
        await store_in_attachment_cache(att["id"], file_data)
    
    return {
        "success": True,
        "folder_id": request.folder_id,
        "subfolders": len(subfolders),
        "tests": len(tests),
        "attachments": len(attachments)
    }
```

#### Step 4.2: Implement /api/expand_testplan_test
```python
@app.post("/api/expand_testplan_test")
async def expand_testplan_test(request: ExpandTestRequest):
    """
    Expand test: get design steps, test attachments, step attachments
    """
    # 1. Get design steps
    steps = await alm_client.get_design_steps(test_id=request.test_id)
    await alm_client.store_design_steps(steps)
    
    # 2. Get test attachments
    test_atts = await alm_client.get_attachments(
        parent_id=request.test_id,
        parent_type="test"
    )
    for att in test_atts:
        await alm_client.store_attachment(att, "test")
        file_data = await alm_client.download_attachment(att["id"])
        await store_in_attachment_cache(att["id"], file_data)
    
    # 3. Get design step attachments
    step_att_count = 0
    for step in steps:
        step_atts = await alm_client.get_attachments(
            parent_id=step["id"],
            parent_type="design-step"
        )
        for att in step_atts:
            await alm_client.store_attachment(att, "design-step")
            file_data = await alm_client.download_attachment(att["id"])
            await store_in_attachment_cache(att["id"], file_data)
            step_att_count += 1
    
    return {
        "success": True,
        "test_id": request.test_id,
        "design_steps": len(steps),
        "test_attachments": len(test_atts),
        "step_attachments": step_att_count
    }
```

#### Step 4.3: Implement /api/extract_testplan_folder_recursive
```python
@app.post("/api/extract_testplan_folder_recursive")
async def extract_testplan_folder_recursive(request: ExtractFolderRequest):
    """
    Recursively extract folder hierarchy
    """
    # 1. Create extraction job
    extraction_id = str(uuid.uuid4())
    await db.testplan_extraction_results.insert_one({
        "extraction_id": extraction_id,
        "user": request.username,
        "folder_id": request.folder_id,
        "status": "in_progress",
        "started_at": datetime.utcnow(),
        "folders_extracted": 0,
        "tests_extracted": 0,
        "attachments_downloaded": 0
    })
    
    # 2. Start background task
    background_tasks.add_task(
        recursive_folder_extraction,
        extraction_id,
        request
    )
    
    return {
        "success": True,
        "extraction_id": extraction_id,
        "status": "in_progress"
    }

async def recursive_folder_extraction(extraction_id: str, request: ExtractFolderRequest):
    """Background task for recursive extraction"""
    # Implement recursive logic
    pass
```

#### Step 4.4: Implement /api/get_extraction_status
```python
@app.get("/api/get_extraction_status")
async def get_extraction_status(extraction_id: str):
    """Get status of extraction job"""
    result = await db.testplan_extraction_results.find_one(
        {"extraction_id": extraction_id}
    )
    return result
```

**Files to modify**:
- `backend/app/main.py`
- `backend/app/alm.py` (add storage methods)

**Collections used**:
- `testplan_folders`
- `testplan_tests`
- `testplan_test_design_steps`
- `testplan_folder_attachments`
- `testplan_test_attachments`
- `testplan_test_design_step_attachments`
- `attachment_cache`
- `testplan_extraction_results`

### Phase 5: TestLab Endpoints (2-3 hours)

#### Step 5.1: Implement TestLab expansion endpoints
Similar pattern to TestPlan:
- `/api/expand_testlab_release`
- `/api/expand_testlab_cycle`
- `/api/expand_testlab_testset`
- `/api/extract_testlab_recursive`

**Collections used**:
- `testlab_releases`
- `testlab_release_cycles`
- `testlab_testsets`
- `testlab_testruns`
- `testlab_testset_attachments`
- `attachment_cache`
- `testlab_extraction_results`

### Phase 6: Defect Endpoints (1 hour)

#### Step 6.1: Implement defect endpoints
- `/api/get_defects`
- `/api/expand_defect`

**Collections used**:
- `defects`
- `defect_attachments`
- `attachment_cache`
- `defect_details`

### Phase 7: Export & Query Endpoints (2 hours)

#### Step 7.1: Implement /api/export_to_json
```python
@app.post("/api/export_to_json")
async def export_to_json(request: ExportRequest):
    """
    Export data to JSON with field filtering
    """
    # 1. Query collection
    collection = getattr(db, request.collection)
    data = await collection.find(request.filter).to_list(None)
    
    # 2. Transform to display format if requested
    if request.format == "display":
        display_fields = ALMConfig.get_display_fields(request.collection)
        transformed_data = [
            ALMConfig.transform_to_display_format(request.collection, item)
            for item in data
        ]
        data = transformed_data
    
    return {
        "success": True,
        "data": data,
        "count": len(data)
    }
```

#### Step 7.2: Implement /api/export_to_excel
```python
@app.post("/api/export_to_excel")
async def export_to_excel(request: ExportRequest):
    """
    Export data to Excel with field filtering
    """
    # 1. Query collection
    # 2. Transform to display format with aliases as headers
    # 3. Sort columns by sequence
    # 4. Generate Excel file
    # 5. Return file
    return FileResponse(...)
```

#### Step 7.3: Implement /api/query_collection
```python
@app.post("/api/query_collection")
async def query_collection(request: QueryRequest):
    """
    Generic query endpoint
    """
    # Validate collection name
    # Query with filter/projection
    # Apply transformations
    # Return results
    return {"success": True, "data": [...]}
```

### Phase 8: Cleanup & Testing (2 hours)

#### Step 8.1: Remove old endpoints
- Identify and remove deprecated endpoints from main.py
- Remove or mark as deprecated in frontend API calls

#### Step 8.2: Update test scripts
- `scripts/test_atlas_connection.py` - test new collections
- `scripts/add_sample_data.py` - use new collections

#### Step 8.3: Integration testing
- Test authentication flow
- Test domain/project fetching
- Test TestPlan expansion
- Test TestLab expansion
- Test defect operations
- Test exports with field transformation

## File Change Summary

### Files to Create
- ✅ `docs/API_ENDPOINTS.md` (created)
- ✅ `docs/IMPLEMENTATION_PLAN.md` (this file)

### Files to Modify
| File | Changes | Effort |
|------|---------|--------|
| backend/app/mongo_service.py | Deprecate or refactor | 30 min |
| backend/app/alm.py | Add specific storage methods | 2 hours |
| backend/app/main.py | Add 17 new endpoints, remove old | 6 hours |
| scripts/test_atlas_connection.py | Update for new collections | 30 min |
| scripts/add_sample_data.py | Update for new collections | 30 min |

### Files Already Updated
- ✅ `backend/app/alm_config.py` - Field configs complete
- ✅ `scripts/show-detailed-mongo-stats.bat` - Collection list updated
- ✅ `docs/COLLECTION_RESTRUCTURE.md` - Documentation complete

## Estimated Timeline

| Phase | Hours | Cumulative |
|-------|-------|------------|
| Phase 1: Core Infrastructure | 2-3 | 3 |
| Phase 2: Authentication | 1 | 4 |
| Phase 3: Domain/Project | 1 | 5 |
| Phase 4: TestPlan | 3-4 | 9 |
| Phase 5: TestLab | 2-3 | 12 |
| Phase 6: Defects | 1 | 13 |
| Phase 7: Export/Query | 2 | 15 |
| Phase 8: Cleanup/Testing | 2 | 17 |
| **Total** | **15-17 hours** | |

## Risk Assessment

### High Risk
1. **Breaking existing functionality** - Mitigation: Keep old endpoints until new ones tested
2. **Data migration complexity** - Mitigation: Start with empty database
3. **ALM API changes** - Mitigation: Test each endpoint after implementation

### Medium Risk
1. **Performance with large datasets** - Mitigation: Add pagination, background tasks
2. **Attachment download failures** - Mitigation: Add retry logic
3. **Field mapping errors** - Mitigation: Validate against ENTITY_FIELD_CONFIG

### Low Risk
1. **Export format issues** - Mitigation: Test exports with sample data
2. **Frontend compatibility** - Mitigation: Update frontend API calls incrementally

## Rollback Plan

If issues arise:
1. Keep old endpoints active during transition
2. Use feature flags to toggle between old/new endpoints
3. Database is empty, so no data loss risk
4. Git commits at each phase for easy rollback

## Success Criteria

- ✅ All 17 new endpoints implemented and tested
- ✅ Data stored in correct specific collections
- ✅ Field transformation working (aliases, display filtering)
- ✅ Exports show only displayable fields with proper labels
- ✅ Attachment downloads working
- ✅ Recursive extraction working with progress tracking
- ✅ Old endpoints removed or deprecated
- ✅ Frontend updated to use new endpoints
- ✅ Integration tests passing
- ✅ Sample data script working with new structure

## Next Steps

**Immediate action**: Choose implementation approach:

1. **Full Implementation** - Implement all phases sequentially (15-17 hours)
2. **Phased Rollout** - Implement one category at a time, test, then proceed
3. **Proof of Concept** - Implement just authentication + domain/project endpoints to validate approach

**Recommendation**: Phased Rollout
- Phase 1-3 first (Authentication + Domain/Project) - 5 hours
- Test and validate
- Then proceed with TestPlan, TestLab, Defects

This allows early validation and course correction if needed.
