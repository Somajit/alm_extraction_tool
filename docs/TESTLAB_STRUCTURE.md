# TestLab Tree Structure and Recursive Extraction

## Overview

The TestLab module provides a hierarchical view of test execution data organized in a three-level structure:

```
Releases
  └─ Release Cycles
      └─ Test Sets
          ├─ Test Runs
          └─ Attachments
```

This document explains the TestLab tree structure, how to navigate it, and how to use the recursive extraction feature.

---

## Tree Hierarchy

### 1. Releases (Top Level)

**Releases** are the top-level nodes in the TestLab tree. They represent major product releases or versions.

- **Icon**: 📁 Folder (blue)
- **Click to expand**: Shows release cycles under this release
- **Right-click context menu**: "Extract Release (Recursive)" option
- **Fields**:
  - `id`: Unique release identifier
  - `name`: Release name/version
  - `description`: Release description
  - `start-date`: Release start date
  - `end-date`: Release end date

**Example**:
```
Release 1.0
Release 2.0
Release 3.0 - Beta
```

---

### 2. Release Cycles (Second Level)

**Release Cycles** represent test execution cycles within a release (e.g., Sprint 1, Sprint 2, Alpha Testing, Beta Testing).

- **Icon**: 📁 Folder (blue)
- **Parent**: Release
- **Click to expand**: Shows test sets under this cycle
- **Right-click context menu**: "Extract Cycle (Recursive)" option
- **Fields**:
  - `id`: Unique cycle identifier
  - `name`: Cycle name
  - `parent-id`: Parent release ID
  - `description`: Cycle description
  - `start-date`: Cycle start date
  - `end-date`: Cycle end date

**Example** (under Release 1.0):
```
├─ Sprint 1
├─ Sprint 2
└─ Regression Cycle
```

---

### 3. Test Sets (Third Level)

**Test Sets** are collections of tests grouped together for execution within a cycle.

- **Icon**: 📁 Folder (blue)
- **Parent**: Release Cycle
- **Click to expand**: Shows "Test Runs" and "Attachments" containers
- **Fields**:
  - `id`: Unique test set identifier
  - `name`: Test set name
  - `parent-id`: Parent cycle ID
  - `description`: Test set description
  - `status`: Test set status (Open, Passed, Failed, etc.)

**Example** (under Sprint 1):
```
├─ Login Tests
├─ User Management Tests
└─ API Tests
```

---

### 4. Test Set Children

When you expand a Test Set, you see two containers:

#### a) Test Runs

**Test Runs** represent individual test executions within the test set.

- **Icon**: 📄 File (green)
- **Type**: `run`
- **Fields**:
  - `id`: Unique run identifier
  - `name`: Run name
  - `testcycl-id`: Parent test set ID
  - `test-id`: Associated test ID from TestPlan
  - `status`: Execution status (Passed, Failed, etc.)
  - `execution-date`: Date when test was executed
  - `execution-time`: Time when test was executed
  - `owner`: User who executed the test
  - `comments`: Execution comments/notes

**Example**:
```
Test Runs
├─ Run 1 of Test Set 3001 (Passed)
├─ Run 2 of Test Set 3001 (Failed)
└─ Run 3 of Test Set 3001 (Passed)
```

#### b) Attachments

**Attachments** are files associated with the test set (screenshots, logs, reports, etc.).

- **Icon**: 📄 File
- **Type**: `attachment`
- **Fields**:
  - `id`: Unique attachment identifier
  - `name`: File name
  - `parent-id`: Parent test set ID
  - `file-size`: Size in bytes
  - `last-modified`: Last modification timestamp

---

## Navigation

### Expanding Nodes

1. **Click the + icon** or **click on the node label** to expand
2. The application fetches children from the backend:
   - Releases → Fetch cycles
   - Cycles → Fetch test sets
   - Test Sets → Fetch runs and attachments

### Viewing Test Set Details

1. Expand a Test Set node
2. Click on the **testset.json** node
3. An embedded JSON viewer displays:
   - Test set metadata
   - All test runs with execution details
   - Attachments list

**Example testset.json structure**:
```json
{
  "testset_id": "3001",
  "test_runs": [
    {
      "id": 30011,
      "name": "Run 1 of Test Set 3001",
      "status": "Passed",
      "execution-date": "2024-01-05",
      "owner": "tester1",
      "comments": "All test steps passed"
    }
  ],
  "attachments": [
    {
      "id": "1234",
      "name": "test_results.pdf",
      "sanitized_name": "test_results.pdf"
    }
  ]
}
```

---

## Recursive Extraction

### Feature Description

The **Recursive Extraction** feature allows you to download the complete subtree structure starting from a Release or Cycle node, including:

- All child cycles (if starting from Release)
- All test sets
- All test runs with execution details
- All attachments metadata

This is useful for:
- **Bulk export** of test execution data
- **Offline analysis** of test results
- **Archiving** test execution history
- **Reporting** across multiple test cycles

---

### How to Use

#### Step 1: Right-Click on Release or Cycle

1. Navigate to the TestLab tab
2. Right-click on a **Release** or **Release Cycle** node
3. A context menu appears

#### Step 2: Select "Extract Release/Cycle (Recursive)"

- The menu shows:
  - **"Extract Release (Recursive)"** for release nodes
  - **"Extract Cycle (Recursive)"** for cycle nodes

#### Step 3: Wait for Extraction

- A blue progress banner appears: "Extracting release/cycle data recursively..."
- The extraction process:
  1. Fetches all cycles (if release)
  2. Fetches all test sets for each cycle
  3. Fetches all test runs for each test set
  4. Fetches all attachments for each test set
  5. Stores results in MongoDB
  6. Returns complete JSON structure

**Note**: Large releases with many cycles and test sets may take several minutes.

#### Step 4: Download JSON File

- Upon success, a snackbar notification appears
- The complete extraction is automatically downloaded as:
  - `{ReleaseName}_extraction.json` (for releases)
  - `{CycleName}_extraction.json` (for cycles)
- The file contains the complete hierarchical structure

---

## Extraction JSON Structure

### Release Extraction Format

```json
{
  "success": true,
  "node_id": "1001",
  "node_type": "release",
  "data": {
    "release_id": "1001",
    "cycles": [
      {
        "cycle_id": "2001",
        "cycle_info": {
          "id": 2001,
          "name": "Sprint 1",
          "parent-id": 1001,
          "description": "First sprint",
          "start-date": "2024-01-01",
          "end-date": "2024-01-14"
        },
        "test_sets": [
          {
            "testset_id": "3001",
            "testset_info": {
              "id": 3001,
              "name": "Login Tests",
              "parent-id": 2001,
              "status": "Open"
            },
            "test_runs": [
              {
                "id": 30011,
                "name": "Run 1 of Test Set 3001",
                "status": "Passed",
                "execution-date": "2024-01-05",
                "owner": "tester1"
              }
            ],
            "attachments": [
              {
                "id": "1234",
                "name": "screenshot.png",
                "file-size": 102400
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### Cycle Extraction Format

```json
{
  "success": true,
  "node_id": "2001",
  "node_type": "cycle",
  "data": {
    "cycle_id": "2001",
    "test_sets": [
      {
        "testset_id": "3001",
        "testset_info": {
          "id": 3001,
          "name": "Login Tests",
          "status": "Open"
        },
        "test_runs": [...],
        "attachments": [...]
      }
    ]
  }
}
```

---

## Backend Implementation

### API Endpoints

#### 1. GET /tree (TestLab Mode)

**Parameters**:
- `project`: Project name
- `username`: ALM username
- `domain`: Domain name
- `type`: "testlab"
- `folder_id`: Optional - entity ID with prefix:
  - `release_{id}` - fetch cycles for release
  - `cycle_{id}` - fetch test sets for cycle
  - `testset_{id}` - fetch runs and attachments for test set

**Returns**: Tree nodes for the requested level

#### 2. GET /testset-details

**Parameters**:
- `username`, `domain`, `project`
- `testset_id`: Test set ID

**Returns**: Test set details with runs and attachments

#### 3. GET /testset-children

**Parameters**:
- `username`, `domain`, `project`
- `testset_id`: Test set ID

**Returns**: Tree structure with testset.json node and Attachments folder

#### 4. POST /extract-testlab-recursive

**Parameters**:
- `username`, `domain`, `project`
- `node_id`: Release or cycle ID (without prefix)
- `node_type`: "release" or "cycle"

**Returns**: Complete recursive extraction result

---

### ALM API Integration

The backend calls these ALM REST API endpoints:

1. **GET /releases** - Fetch all releases
2. **GET /release-cycles?query={parent-id[releaseId]}** - Fetch cycles for release
3. **GET /test-sets?query={parent-id[cycleId]}** - Fetch test sets for cycle
4. **GET /runs?query={testcycl-id[testSetId]}** - Fetch runs for test set
5. **GET /attachments?query={parent-type[test-set];parent-id[testSetId]}** - Fetch test set attachments

All endpoints support **pagination** (100 entities per page) using `start-index` parameter.

---

## Performance Considerations

### Pagination

- ALM returns maximum 100 entities per request
- Backend automatically handles pagination
- Large releases may require multiple API calls

### Depth Limiting

- Recursive extraction is limited to **20 levels** to prevent infinite loops
- Typical TestLab structure has 3-4 levels maximum

### Caching

- Extraction results are cached in MongoDB collection: `testlab_extraction_results`
- Test set details are cached in: `testset_details`
- Cache includes timestamp for freshness tracking

### Async Operations

- All ALM API calls are asynchronous (Python async/await)
- Frontend shows progress indicator during extraction
- Large extractions may take 2-5 minutes

---

## Error Handling

### Common Errors

1. **Authentication Failed**
   - Solution: Re-authenticate with valid ALM credentials

2. **Node Not Found**
   - Cause: Invalid release/cycle ID
   - Solution: Refresh tree and try again

3. **Max Depth Reached**
   - Cause: Circular references or deep hierarchy
   - Solution: Extract at a lower level (cycle instead of release)

4. **Timeout**
   - Cause: Large dataset or slow ALM server
   - Solution: Extract smaller portions (individual cycles)

### Error Messages

- **Frontend**: Snackbar with red error alert
- **Backend**: HTTP 500 with detailed error message in response
- **Logs**: Full stack trace in backend logs

---

## Use Cases

### 1. Sprint Report Generation

**Scenario**: Generate test execution report for Sprint 1

**Steps**:
1. Navigate to Release → Sprint 1
2. Right-click on "Sprint 1"
3. Select "Extract Cycle (Recursive)"
4. Download JSON file
5. Use JSON for custom reporting/visualization

### 2. Release Summary

**Scenario**: Get complete test execution summary for Release 1.0

**Steps**:
1. Right-click on "Release 1.0"
2. Select "Extract Release (Recursive)"
3. Download JSON with all cycles, test sets, runs, and attachments

### 3. Test Metrics Analysis

**Scenario**: Analyze pass/fail rates across multiple test sets

**Steps**:
1. Extract cycle or release
2. Parse JSON to count:
   - Total test runs
   - Passed runs
   - Failed runs
   - Pass rate percentage

**Example Python script**:
```python
import json

with open('Sprint_1_extraction.json') as f:
    data = json.load(f)

total_runs = 0
passed_runs = 0

for testset in data['data']['test_sets']:
    for run in testset['test_runs']:
        total_runs += 1
        if run['status'] == 'Passed':
            passed_runs += 1

pass_rate = (passed_runs / total_runs) * 100 if total_runs > 0 else 0
print(f"Pass Rate: {pass_rate:.2f}% ({passed_runs}/{total_runs})")
```

### 4. Audit Trail

**Scenario**: Archive test execution history for compliance

**Steps**:
1. Extract releases periodically (e.g., end of each release)
2. Store JSON files in version control or document management system
3. JSON includes all execution details, dates, owners, and comments

---

## Comparison with TestPlan

| Feature | TestPlan | TestLab |
|---------|----------|---------|
| **Top Level** | Test Folders | Releases |
| **Second Level** | Subfolders/Tests | Release Cycles |
| **Third Level** | Test Details/Attachments | Test Sets |
| **Fourth Level** | - | Test Runs/Attachments |
| **Extract From** | Folders | Releases, Cycles |
| **Primary Focus** | Test design | Test execution |
| **Key Data** | Design steps, parameters | Execution results, status |

---

## Best Practices

### 1. Extract by Cycle

- Extract individual cycles instead of entire releases for faster results
- Reduces API load and download size

### 2. Use Filters

- If available, filter test sets by status before extraction
- Focus on failed tests for debugging

### 3. Schedule Extractions

- Run extractions after test execution completes
- Automate with backend API for nightly reports

### 4. Archive Regularly

- Store extraction JSONs in backup location
- Maintain history for trend analysis

### 5. Monitor Performance

- Check backend logs for API call durations
- Identify slow endpoints for optimization

---

## Troubleshooting

### Tree Not Loading

**Symptoms**: Empty tree or "Loading..." never completes

**Solutions**:
1. Check browser console for errors
2. Verify ALM authentication
3. Check backend logs for API errors
4. Ensure mock ALM server is running (for testing)

### Extraction Fails

**Symptoms**: Error notification after clicking Extract

**Solutions**:
1. Check if node has children (some cycles may be empty)
2. Verify network connectivity to ALM server
3. Check ALM permissions (user may not have access)
4. Try extracting smaller subset (cycle instead of release)

### JSON Viewer Not Opening

**Symptoms**: Click on testset.json doesn't show dialog

**Solutions**:
1. Verify test set has test runs
2. Check browser console for JavaScript errors
3. Ensure testset-details endpoint is working

### Missing Data

**Symptoms**: Extraction JSON incomplete

**Solutions**:
1. Check if pagination is working correctly
2. Verify ALM API responses in backend logs
3. Increase timeout settings if needed

---

## Future Enhancements

### Planned Features

1. **Progress Percentage**: Show extraction progress (e.g., "25% complete")
2. **Parallel Extraction**: Extract multiple test sets simultaneously
3. **Excel Export**: Download as Excel workbook with multiple sheets
4. **Filtered Extraction**: Extract only failed test runs
5. **Incremental Updates**: Update existing extractions with new runs
6. **WebSocket Support**: Real-time progress updates during extraction
7. **Test Run Details**: Include run steps and step results
8. **Defect Linkage**: Include linked defects in extraction

---

## Technical Details

### Frontend Components

**File**: `frontend/src/components/TestTree.tsx`

**Key Functions**:
- `toggleNode()`: Handles node expansion for releases, cycles, test sets
- `handleContextMenu()`: Shows context menu for releases and cycles
- `handleExtractFolder()`: Triggers recursive extraction
- `getNodeIcon()`: Returns appropriate icon for node type

### Backend Endpoints

**File**: `backend/app/main.py`

**Key Functions**:
- `get_tree()`: Returns tree nodes based on type and folder_id
- `get_testset_details()`: Fetches test runs and attachments
- `extract_testlab_recursive()`: Performs recursive extraction

### ALM Client

**File**: `backend/app/alm.py`

**Key Functions**:
- `fetch_releases()`: Paginated release fetching
- `fetch_release_cycles()`: Paginated cycle fetching
- `fetch_test_sets()`: Paginated test set fetching
- `fetch_test_runs()`: Paginated run fetching

### Mock ALM Server

**File**: `backend/app/mock_alm.py`

**Key Endpoints**:
- `/qcbin/rest/domains/{domain}/projects/{project}/releases`
- `/qcbin/rest/domains/{domain}/projects/{project}/release-cycles`
- `/qcbin/rest/domains/{domain}/projects/{project}/test-sets`
- `/qcbin/rest/domains/{domain}/projects/{project}/runs`

---

## Conclusion

The TestLab tree structure provides a comprehensive view of test execution data organized by releases, cycles, and test sets. The recursive extraction feature enables efficient bulk export of execution results for reporting, analysis, and archiving purposes.

For questions or issues, refer to the main README or contact the development team.
