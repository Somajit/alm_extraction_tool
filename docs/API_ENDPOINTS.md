# ReleaseCraft API Endpoint Specification

## Overview
Simplified, rationalized API endpoints that map directly to ALM operations.

## Critical Architecture Principle

**ALL endpoints follow this flow**:
```
Frontend → Backend API → ALM/Mock ALM → Store in MongoDB → Query MongoDB → Transform to Display → Return to Frontend
```

**NEVER return ALM data directly to frontend. Always store in MongoDB first, then query from MongoDB.**

This ensures:
- MongoDB is single source of truth for frontend
- Offline capability when ALM is unavailable
- Consistent data format with field metadata
- Display control through configuration

## Authentication Flow

### 1. POST /api/authenticate
**Purpose**: Authenticate with ALM server (username/password only)

**Request Body**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Operations**:
1. Call ALM `/authentication-point/authenticate` endpoint
2. Call ALM `/rest/site-session` endpoint
3. Store 4 cookies (LWSSO_COOKIE_KEY, QCSession, ALM_USER, XSRF-TOKEN) in ALM class
4. Store username, encrypted password in `user_credentials` collection
5. **Query `user_credentials` from MongoDB** to get stored credentials
6. Return success with data from MongoDB (not directly from ALM)

**Response**:
```json
{
  "success": true,
  "message": "Authenticated successfully",
  "username": "john.doe"
}
```

### 2. GET /api/get_domains?username={username}
**Purpose**: Fetch and store available domains from ALM

**Operations**:
1. Call ALM `/rest/domains` endpoint using ALMConfig.build_alm_url() and build_query_params()
2. Parse ALM response using ALMConfig.parse_alm_response_to_entity()
3. Store in `domains` collection with standardized entity format (user, id, name, parent_id, fields array)
4. **Query `domains` collection from MongoDB** with filter: {"user": username}
5. Transform to display format using ALMConfig.entity_to_display_format()
6. Return domains list from MongoDB (not from ALM response)

**Response**:
```json
{
  "success": true,
  "domains": [
    {"id": "DEFAULT", "name": "Default Domain"},
    {"id": "CUSTOM", "name": "Custom Domain"}
  ]
}
```

### 3. GET /api/get_projects?username={username}&domain={domain}
**Operations**:
1. Call ALM `/rest/domains/{domain}/projects` endpoint using ALMConfig
2. Parse ALM response using ALMConfig.parse_alm_response_to_entity()
3. Store in `projects` collection with standardized entity format
4. **Query `projects` collection from MongoDB** with filter: {"user": username, "parent_id": domain}
5. Transform to display format using ALMConfig.entity_to_display_format()
6. Return projects list from MongoDB (not from ALM response)act project list
3. Store in `projects` collection with fields: user, id, name, parent_id (domain)
4. Return projects list

**Response**:
```json
{
  "success": true,
  "projects": [
    {"id": "MyProject", "name": "My Project"},
    {"id": "TestProject", "name": "Test Project"}
  ]
}
```

### 4. POST /api/login
**Purpose**: Complete login after domain/project selection, load initial tree data

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
**Operations**:
1. Store domain/project in `user_credentials` collection
2. **Fetch root folders from ALM**: Call `/rest/domains/{domain}/projects/{project}/test-folders?query={parent-id[0]}`
   - Parse using ALMConfig.parse_alm_response_to_entity()
   - Store in `testplan_folders` collection
   - Query from MongoDB
3. **Fetch releases from ALM**: Call `/rest/domains/{domain}/projects/{project}/releases`
   - Parse and store in `testlab_releases` collection
   - Query from MongoDB
4. **Fetch defects from ALM**: Call `/rest/domains/{domain}/projects/{project}/defects?page-size=100`
   - Parse and store in `defects` collection
   - Query from MongoDB
5. Mark user as logged_in=true in `user_credentials`
6. **Return counts from MongoDB queries** (not from ALM responses)ses in `testlab_releases` collection
4. Call ALM `/rest/domains/{domain}/projects/{project}/defects?page-size=100`
   - Store defects in `defects` collection
5. Mark user as logged_in=true
6. Return counts

**Response**:
```json
{
  "success": true,
  "testplan_root_folders": 5,
  "testlab_releases": 3,
  "defects": 150
}
```

### 5. POST /api/logout
**Purpose**: Logout from ALM server

**Request Body**:
```json
{
  "username": "string"
}
```

**Operations**:
1. Call ALM `/authentication-point/logout`
2. Clear cookies from ALM class
3. Update `user_credentials` set logged_in=false

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## TestPlan Operations (Node Expansion)

### 6. POST /api/expand_testplan_folder
**Purpose**: Expand a folder node - get immediate subfolders, tests, and folder attachments

**Request Body**:
```json
{
  "username": "string",
**Operations**:
1. **Fetch subfolders from ALM**: `/rest/domains/{domain}/projects/{project}/test-folders?query={parent-id[{folder_id}]}`
   - Parse, store in `testplan_folders`, query from MongoDB
2. **Fetch tests from ALM**: `/rest/domains/{domain}/projects/{project}/tests?query={parent-id[{folder_id}]}`
   - Parse, store in `testplan_tests`, query from MongoDB
3. **Fetch attachments from ALM**: `/rest/domains/{domain}/projects/{project}/attachments?query={parent-id[{folder_id}];parent-type[test-folder]}`
   - For each attachment:
     - Parse and store metadata in `testplan_folder_attachments`
     - Download file and store in `attachment_cache`
   - Query from MongoDB
4. **Query MongoDB for counts**: Count stored subfolders, tests, attachments
5. Return counts from MongoDB (ONE level expansion only)s/{project}/tests?query={parent-id[{folder_id}]}`
   - Store tests in `testplan_tests` collection
3. Call ALM `/rest/domains/{domain}/projects/{project}/attachments?query={parent-id[{folder_id}];parent-type[test-folder]}`
   - For each attachment:
     - Store metadata in `testplan_folder_attachments` collection
     - Call download endpoint and store file in `attachment_cache`
4. Return counts only (ONE level expansion)

**Response**:
```json
{
  "success": true,
  "folder_id": "123",
  "subfolders": 5,
  "tests": 12,
  "attachments": 3
}
```

### 7. POST /api/expand_testplan_test
**Purpose**: Expand a test node - get design steps and test attachments (NOT step attachments)

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "test_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/design-steps?query={parent-id[{test_id}]}`
   - Store design steps in `testplan_test_design_steps` collection
2. Call ALM `/rest/domains/{domain}/projects/{project}/attachments?query={parent-id[{test_id}];parent-type[test]}`
   - For each attachment:
     - Store metadata in `testplan_test_attachments` collection
     - Download and store file in `attachment_cache`
3. Return counts (do NOT get step attachments yet)

**Response**:
```json
{
  "success": true,
  "test_id": "456",
  "design_steps": 8,
  "test_attachments": 2
}
```

### 8. POST /api/expand_design_step
**Purpose**: Expand a design step node - get design step attachments

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "step_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/attachments?query={parent-id[{step_id}];parent-type[design-step]}`
   - For each attachment:
     - Store metadata in `testplan_test_design_step_attachments` collection
     - Download and store file in `attachment_cache`
2. Return count

**Response**:
```json
{
  "success": true,
  "step_id": "789",
  "attachments": 3
}
```

## TestLab Operations

### 9. POST /api/expand_testlab_release
**Purpose**: Expand a release and load its cycles

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "release_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/release-cycles?query={parent-id[{release_id}]}`
2. Store cycles in `testlab_release_cycles` collection
3. Return release details with cycle count

**Response**:
```json
{
  "success": true,
## TestLab Operations (Node Expansion)

### 9. POST /api/expand_testlab_release
**Purpose**: Expand a release node - get release cycles only

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "release_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/release-cycles?query={parent-id[{release_id}]}`
2. Store cycles in `testlab_release_cycles` collection
3. Return cycle count only

**Response**:
```json
{
  "success": true,
  "release_id": "789",
  "cycles": 3
}
```

### 10. POST /api/expand_testlab_cycle
**Purpose**: Expand a cycle node - get test sets only

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "cycle_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/test-sets?query={cycle-id[{cycle_id}]}`
2. Store test sets in `testlab_testsets` collection
3. Return test set count only

**Response**:
```json
{
  "success": true,
  "cycle_id": "101",
  "test_sets": 8
}
```

### 11. POST /api/expand_testlab_testset
**Purpose**: Expand a test set node - get test runs and testset attachments

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "testset_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/runs?query={testcycl-id[{testset_id}]}`
   - Store test runs in `testlab_testruns` collection
2. Call ALM `/rest/domains/{domain}/projects/{project}/attachments?query={parent-id[{testset_id}];parent-type[test-set]}`
   - For each attachment:
     - Store metadata in `testlab_testset_attachments` collection
     - Download and store file in `attachment_cache`
3. Return counts only

**Response**:
```json
{
  "success": true,
  "testset_id": "202",
  "test_runs": 25,
  "attachments": 4
}
```urpose**: Get defect details and attachments

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "defect_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/defects/{defect_id}`
2. Update defect in `defects` collection with full details
3. Call ALM attachments endpoint
4. Store in `defect_attachments` collection
5. Download attachment files

**Response**:
```json
{
  "success": true,
  "defect_id": "303",
  "attachments": 6
}
```

## Export Operations

## Defect Operations (Node Expansion)

### 12. POST /api/expand_defect
**Purpose**: Expand a defect node - get defect attachments

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "defect_id": "string"
}
```

**Operations**:
1. Call ALM `/rest/domains/{domain}/projects/{project}/attachments?query={parent-id[{defect_id}];parent-type[defect]}`
   - For each attachment:
     - Store metadata in `defect_attachments` collection
     - Download and store file in `attachment_cache`
2. Return attachment count only

**Response**:
```json
{
  "success": true,
  "defect_id": "303",
  "attachments": 6
}
```perations**:
1. Query collection
2. Transform to display format with aliases as column headers
3. Sort columns by sequence
4. Generate Excel file
5. Return file for download

**Response**: Excel file download

## Query Operations

### 17. POST /api/query_collection
**Purpose**: Generic query endpoint for any collection

**Request Body**:
```json
{
  "collection": "testplan_folders",
  "filter": {"user": "john", "parent_id": "0"},
  "projection": ["id", "name", "description"],
  "format": "display",
## Recursive Extract Operations (Export/Extract Only)

### 13. POST /api/extract_testplan_folder_recursive
**Purpose**: RECURSIVELY extract entire folder hierarchy (for export/extract operations)

**Request Body**:
```json
{
  "username": "string",
  "domain": "string",
  "project": "string",
  "folder_id": "string",
  "include_tests": true,
  "include_attachments": true
### 17. POST /api/export_to_excel
**Purpose**: Export data to Excel with field filtering

**Request Body**:
```json
{
  "collection": "testplan_tests",
  "filter": {"parent_id": "123"},
  "filename": "tests_export.xlsx"
}
```

**Operations**:
1. Query collection
2. Transform to display format with aliases as column headers
3. Sort columns by sequence
4. Generate Excel file
5. Return file for download

**Response**: Excel file download

## Query Operations

### 18. POST /api/query_collection
**Purpose**: Generic query endpoint for any collection

**Request Body**:
```json
{
  "collection": "testplan_folders",
  "filter": {"user": "john", "parent_id": "0"},
  "projection": ["id", "name", "description"],
  "format": "display",
  "limit": 100,
  "skip": 0
}
```

**Operations**:
1. Validate collection name
2. Query with filter and projection
3. Apply format transformation if requested
4. Return results

**Response**:
```json
{
  "success": true,
  "collection": "testplan_folders",
  "data": [...],
  "count": 25
}
```

## Summary

**Total Endpoints**: 18 rationalized endpoints

**Authentication Flow** (4 steps):
1. `/api/authenticate` - username/password only
2. `/api/get_domains` - fetch domains
3. `/api/get_projects` - fetch projects for domain
4. `/api/login` - select domain/project, load initial tree (root folders, releases, defects)

**Node Expansion** (8 endpoints - ONE level per call):
- `/api/expand_testplan_folder` - get subfolders + tests + folder attachments
- `/api/expand_testplan_test` - get design steps + test attachments
- `/api/expand_design_step` - get design step attachments
- `/api/expand_testlab_release` - get release cycles
- `/api/expand_testlab_cycle` - get test sets
- `/api/expand_testlab_testset` - get test runs + testset attachments
- `/api/expand_defect` - get defect attachments
- `/api/logout` - logout

**Recursive Extract** (3 endpoints - for export/extract ONLY):
- `/api/extract_testplan_folder_recursive` - recursively extract entire folder tree
- `/api/extract_testlab_recursive` - recursively extract release/cycle/testset tree
- `/api/get_extraction_status` - check extraction job status

**Export/Query** (3 endpoints):
- `/api/export_to_json` - export with field filtering
- `/api/export_to_excel` - export to Excel
- `/api/query_collection` - generic query endpoint

**Key Principles**:
1. **Node expansion = ONE level only** (immediate children)
2. **Recursive extraction = ONLY for export/extract operations** (all levels)
3. Each endpoint stores data in appropriate specific collection
4. All expansions include attachments and download files
5. All exports use field configuration for display (aliases, sequence, display flag)
6. Consistent request/response formats
7. Progress tracking for long-running recursive operations
  "tests_extracted": 150,
  "design_steps_extracted": 450,
  "attachments_downloaded": 85,
  "started_at": "2025-12-05T10:30:00Z",
  "completed_at": "2025-12-05T10:35:00Z"
}
```

## Export Operations

### 16. POST /api/export_to_json
```

**Operations**:
1. Validate collection name
2. Query with filter and projection
3. Apply format transformation if requested
4. Return results

**Response**:
```json
{
  "success": true,
  "collection": "testplan_folders",
  "data": [...],
  "count": 25
}
```

## Summary

**Total Endpoints**: 17 rationalized endpoints

**Categories**:
- Authentication: 2 endpoints
- Domain/Project: 2 endpoints
- TestPlan: 4 expand + 2 extraction endpoints
- TestLab: 4 expand + 1 extraction endpoint
- Defects: 2 endpoints
- Export/Query: 3 endpoints

**Key Principles**:
1. Each endpoint has ONE clear purpose
2. All endpoints store data in appropriate collections
3. All expansions include attachments
4. All exports use field configuration for display
5. Consistent request/response formats
6. Progress tracking for long operations
