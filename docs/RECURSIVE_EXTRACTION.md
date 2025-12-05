# Recursive Folder Extraction

## Overview

The Recursive Folder Extraction feature allows users to extract the complete subtree of a folder, including all subfolders, tests, design steps, and attachments in a single operation.

## User Interface

### Accessing the Feature

1. Navigate to Test Plan tree
2. Right-click on any folder node
3. Select **"Extract Folder (Recursive)"** from context menu
4. Wait for extraction to complete
5. Extraction result automatically downloads as JSON file

### Visual Feedback

- **Progress Indicator**: Blue banner with spinner shows extraction in progress
- **Success Message**: Green snackbar notification when extraction completes
- **Error Message**: Red snackbar notification if extraction fails
- **Auto-Download**: JSON file downloads automatically with folder name

## What Gets Extracted

### For Each Folder (Recursively)

1. **Folder Information**
   - Folder ID
   - Folder name
   - Folder metadata

2. **Subfolders**
   - All child folders
   - Recursively extracted with same structure

3. **Tests**
   - All tests in the folder
   - Complete test details including:
     - Test ID, name, status, owner
     - Description
     - All custom fields
     - Design steps with:
       - Step order
       - Step name
       - Description
       - Expected result
     - Test attachments:
       - Attachment ID
       - Attachment name
       - File size
       - Metadata

4. **Folder Attachments**
   - Documents attached to folder
   - Metadata for each attachment

## Extraction Result Structure

### JSON Format

```json
{
  "success": true,
  "folder_id": "5",
  "data": {
    "folder_id": "5",
    "subfolders": [
      {
        "folder_info": {
          "id": "10",
          "name": "Subfolder 1",
          "parent-id": "5"
        },
        "subfolders": [
          // Nested subfolders...
        ],
        "tests": [
          {
            "id": "1001",
            "name": "Test Case 1",
            "status": "Ready",
            "design_steps": [
              {
                "step-order": 1,
                "step-name": "Step 1",
                "description": "...",
                "expected": "..."
              }
            ],
            "attachments": [
              {
                "id": "10011",
                "name": "screenshot.png",
                "file-size": 102400
              }
            ]
          }
        ],
        "folder_attachments": []
      }
    ],
    "tests": [
      {
        "id": "2001",
        "name": "Test at root level",
        "status": "Ready",
        "design_steps": [...],
        "attachments": [...]
      }
    ],
    "folder_attachments": [
      {
        "id": "5001",
        "name": "folder_doc.pdf",
        "file-size": 51200
      }
    ]
  }
}
```

### Hierarchy Structure

```
Selected Folder
├── folder_attachments[]       // Attachments for this folder
├── tests[]                    // Tests in this folder
│   ├── Test 1
│   │   ├── design_steps[]
│   │   └── attachments[]
│   └── Test 2
│       ├── design_steps[]
│       └── attachments[]
└── subfolders[]               // Recursive subfolders
    ├── Subfolder 1
    │   ├── folder_attachments[]
    │   ├── tests[]
    │   └── subfolders[]       // Further nested...
    └── Subfolder 2
        ├── folder_attachments[]
        ├── tests[]
        └── subfolders[]
```

## Backend Implementation

### Endpoint

```
POST /extract-folder-recursive
```

**Parameters:**
- `username`: ALM username
- `domain`: Domain name
- `project`: Project name
- `folder_id`: Root folder ID to extract

**Response:**
```json
{
  "success": true,
  "folder_id": "5",
  "data": { /* Complete extraction tree */ }
}
```

### Recursive Algorithm

```python
async def extract_folder_tree(folder_id, depth=0):
    if depth > 20:  # Prevent infinite recursion
        return {"error": "Max depth reached"}
    
    result = {
        "folder_id": folder_id,
        "subfolders": [],
        "tests": [],
        "folder_attachments": []
    }
    
    # 1. Fetch subfolders for current folder
    subfolders = fetch_test_folders(folder_id)
    
    # 2. Fetch tests in current folder
    tests = fetch_tests_for_folder(folder_id)
    
    # 3. Fetch folder attachments
    folder_attachments = fetch_attachments("test-folder", folder_id)
    
    # 4. For each test, fetch details and attachments
    for test in tests:
        test_details = fetch_test_details(test.id)
        test_attachments = fetch_attachments("test", test.id)
        test_details["attachments"] = test_attachments
        result["tests"].append(test_details)
    
    result["folder_attachments"] = folder_attachments
    
    # 5. Recursively process subfolders
    for subfolder in subfolders:
        subfolder_tree = extract_folder_tree(subfolder.id, depth + 1)
        subfolder_tree["folder_info"] = subfolder
        result["subfolders"].append(subfolder_tree)
    
    return result
```

### Depth Limit

- **Maximum Depth**: 20 levels
- **Purpose**: Prevent infinite recursion and stack overflow
- **Typical Folder Depth**: 3-8 levels in most ALM projects

### Pagination Support

All fetch operations use pagination:
- Fetches 100 entities per batch
- Automatically handles large folders with 100+ tests
- No manual intervention required

## Performance Considerations

### Network Requests

For a folder with complex structure:
```
Folder with:
- 3 subfolders
  - Each with 2 subfolders
    - Each with 50 tests
      - Each with 4 design steps
      - Each with 2 attachments

Total API calls:
- 9 folders (1 + 3 + 6 subfolders)
- 300 tests (6 folders × 50 tests)
- 300 design steps requests
- 300 test attachments requests
- 9 folder attachments requests
= ~918 API calls
```

### Execution Time

- **Small folder** (10 tests, 2 subfolders): ~5-10 seconds
- **Medium folder** (100 tests, 10 subfolders): ~30-60 seconds
- **Large folder** (500+ tests, 20+ subfolders): ~2-5 minutes

### Optimizations

1. **Parallel Fetching**: Tests within same folder fetched with pagination
2. **MongoDB Caching**: Extraction results stored for future reference
3. **Retry Logic**: Automatic retry on transient failures
4. **Cookie Management**: Sessions maintained throughout extraction

## Storage

### MongoDB Collection: `extraction_results`

```json
{
  "username": "john.doe",
  "domain": "DEFAULT",
  "project": "DEMO_PROJECT",
  "folder_id": "5",
  "result": { /* Complete extraction data */ },
  "extracted_at": "2025-12-04T10:30:00.000Z"
}
```

**Purpose:**
- Cache extraction results
- Avoid re-extracting same folder
- Track extraction history
- Support future features (incremental updates)

## Use Cases

### 1. Complete Backup
Extract entire test suite for backup purposes:
- Right-click on root "Subject" folder
- Select "Extract Folder (Recursive)"
- Save JSON file for archival

### 2. Migration to Another Tool
Export ALM test cases for migration:
- Extract specific module folder
- Parse JSON output
- Import to target system

### 3. Reporting
Generate comprehensive test reports:
- Extract project folder
- Parse test statistics
- Create custom reports

### 4. Audit & Compliance
Document test coverage:
- Extract relevant folders
- Review test details
- Verify design step completeness

### 5. Offline Analysis
Work with test data offline:
- Extract folder before travel
- Analyze tests without ALM access
- Review attachments and design steps

## Error Handling

### Connection Errors
**Symptom**: Network timeout during extraction

**Handling:**
- Automatic retry up to 3 attempts
- Re-authentication if session expires
- Partial results saved to MongoDB

### Permission Errors
**Symptom**: 401/403 errors during extraction

**Handling:**
- Error message shows specific folder/test
- Extraction continues for accessible items
- Missing items logged in result

### Large Dataset Timeout
**Symptom**: Browser timeout on massive folders

**Handling:**
- Backend continues processing
- Check MongoDB for results
- Consider extracting smaller subfolder

## Limitations

### Current Limitations

1. **Max Depth**: 20 levels (configurable)
2. **Attachment Content**: Only metadata extracted, not file content
3. **Run Results**: Test runs not included in extraction
4. **Defects**: Linked defects not extracted
5. **UI Freezing**: Large extractions may make UI less responsive

### Future Enhancements

1. **Progress Updates**: Real-time progress via WebSocket
2. **Partial Downloads**: Download each subfolder as completed
3. **Attachment Download**: Optional full attachment download
4. **Incremental Extraction**: Update only changed items
5. **Custom Filters**: Extract only specific test statuses
6. **Excel Export**: Direct export to Excel format
7. **Parallel Execution**: Multiple folders in parallel
8. **Resume on Failure**: Continue from last successful point

## Troubleshooting

### Extraction Hangs
**Solution:**
1. Check browser console for errors
2. Verify backend logs for stuck API calls
3. Restart backend if needed
4. Try extracting smaller subfolder first

### Incomplete Results
**Solution:**
1. Check snackbar error message
2. Verify ALM connection
3. Check user permissions for all subfolders
4. Review backend logs for specific failures

### Large File Download Issues
**Solution:**
1. Check browser download settings
2. Ensure sufficient disk space
3. Try extracting smaller sections
4. Consider server-side file generation

### Context Menu Not Appearing
**Solution:**
1. Ensure clicking on folder node (not test or container)
2. Check if folder node has `type: 'folder'`
3. Verify browser allows context menus
4. Try left-click first to select node

## Best Practices

### 1. Start Small
- Extract small folders first
- Test with 10-20 tests
- Verify result structure
- Then extract larger folders

### 2. Check Permissions
- Verify access to all subfolders
- Test with read-only user
- Ensure attachment permissions

### 3. Timing
- Extract during off-peak hours
- Avoid extraction during ALM maintenance
- Consider time zones for shared ALM

### 4. Result Validation
- Open JSON file to verify structure
- Check test counts match expectations
- Verify design steps included
- Confirm attachments listed

### 5. Backup Results
- Save extraction JSON files
- Store with version/date info
- Keep for audit trail
- Use for comparison over time

## Example Usage

### Extract Login Module

1. Navigate to Test Plan
2. Expand folders to find "Login Module"
3. Right-click "Login Module" folder
4. Select "Extract Folder (Recursive)"
5. Wait for completion (shows progress)
6. JSON file downloads: `Login_Module_extraction.json`
7. Open file to review:
   - All login test cases
   - Design steps for each test
   - Attachments (screenshots, docs)
   - Any subfolders under Login Module

### Result Analysis

```bash
# Count tests in extraction
cat Login_Module_extraction.json | jq '.data.tests | length'
# Output: 15

# List all test names
cat Login_Module_extraction.json | jq '.data.tests[].name'
# Output: 
# "TC_Login_ValidCredentials"
# "TC_Login_InvalidPassword"
# ...

# Count design steps across all tests
cat Login_Module_extraction.json | jq '[.data.tests[].design_steps | length] | add'
# Output: 60 (15 tests × 4 steps average)
```

## Summary

✅ **Right-click context menu** on folder nodes  
✅ **Recursive extraction** of entire subtree  
✅ **Complete data** including tests, steps, attachments  
✅ **Auto-download** as JSON file  
✅ **Progress indication** with spinner and messages  
✅ **Error handling** with retry and notifications  
✅ **MongoDB caching** of extraction results  
✅ **Production-ready** with pagination support  

The recursive extraction feature provides a powerful way to export complete folder hierarchies from ALM for backup, migration, reporting, and offline analysis.
