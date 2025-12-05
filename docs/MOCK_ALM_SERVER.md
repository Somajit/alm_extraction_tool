# Mock ALM Server Documentation

## Overview

The Mock ALM Server is a FastAPI-based simulation of the HP ALM REST API. It provides all the endpoints required for development and testing without needing access to a real ALM server.

## Features

- **Complete Authentication Flow**: Simulates 2-step ALM authentication with proper cookie management
- **ALM-Style JSON Responses**: Returns data in the exact format expected by the ALM client
- **Hierarchical Test Structure**: Provides realistic test folder hierarchy with tests and design steps
- **Attachments Support**: Simulates attachments for tests and folders
- **Multiple Domains & Projects**: Returns sample domains and projects
- **No External Dependencies**: Runs standalone on port 8001

## Starting the Mock Server

### Windows
```cmd
scripts\start-mock-alm.bat
```

### Manual Start
```cmd
cd backend\app
python mock_alm.py
```

The server will start on `http://localhost:8001`

## Configuring the Application

To use the mock ALM server, update `backend/.env`:

```env
# Use mock ALM server (localhost)
ALM_BASE_URL=http://localhost:8001/qcbin

# Or use real ALM server
# ALM_BASE_URL=https://your-alm-server.com/qcbin
```

## Authentication Flow

The mock server simulates the 2-step ALM authentication:

### Step 1: Authenticate
```bash
POST http://localhost:8001/qcbin/authentication-point/authenticate
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response**: Sets `LWSSO_COOKIE_KEY` cookie

### Step 2: Create Site Session
```bash
POST http://localhost:8001/qcbin/rest/site-session
Cookie: LWSSO_COOKIE_KEY=mock_lwsso_token_12345
```

**Response**: Sets `QCSession`, `ALM_USER`, and `XSRF-TOKEN` cookies

### Required Cookies for API Calls
All subsequent API calls require these 4 cookies:
- `LWSSO_COOKIE_KEY`
- `QCSession`
- `ALM_USER`
- `XSRF-TOKEN`

## Available Endpoints

### Domains
```
GET /qcbin/rest/domains
```
Returns list of available domains.

**Response**:
```json
{
  "entities": [
    {
      "Type": "Domain",
      "Fields": [
        {"Name": "DOMAIN_NAME", "values": [{"value": "DEFAULT"}]}
      ]
    },
    {
      "Type": "Domain",
      "Fields": [
        {"Name": "DOMAIN_NAME", "values": [{"value": "QUALITY_CENTER"}]}
      ]
    }
  ],
  "TotalResults": 2
}
```

### Projects
```
GET /qcbin/rest/domains/{domain}/projects
```
Returns projects in the specified domain.

**Response**:
```json
{
  "entities": [
    {
      "Type": "Project",
      "Fields": [
        {"Name": "PROJECT_NAME", "values": [{"value": "DEMO_PROJECT"}]}
      ]
    }
  ],
  "TotalResults": 1
}
```

### Test Folders
```
GET /qcbin/rest/domains/{domain}/projects/{project}/test-folders?query={parent-id[0]}
```
Returns test folders. Use `parent-id[0]` for root folders.

**Response**:
```json
{
  "entities": [
    {
      "Type": "test-folder",
      "Fields": [
        {"Name": "id", "values": [{"value": "1"}]},
        {"Name": "name", "values": [{"value": "Subject"}]},
        {"Name": "parent-id", "values": [{"value": "0"}]},
        {"Name": "description", "values": [{"value": "Root test folder"}]},
        {"Name": "has-attachments", "values": [{"value": "N"}]}
      ]
    }
  ],
  "TotalResults": 1
}
```

### Tests
```
GET /qcbin/rest/domains/{domain}/projects/{project}/tests?query={parent-id[folder_id]}
```
Returns tests in the specified folder.

**Response**:
```json
{
  "entities": [
    {
      "Type": "test",
      "Fields": [
        {"Name": "id", "values": [{"value": "1001"}]},
        {"Name": "name", "values": [{"value": "TC_Login_ValidCredentials"}]},
        {"Name": "status", "values": [{"value": "Ready"}]},
        {"Name": "owner", "values": [{"value": "john.doe"}]},
        {"Name": "parent-id", "values": [{"value": "5"}]},
        {"Name": "test-type", "values": [{"value": "MANUAL"}]}
      ]
    }
  ],
  "TotalResults": 1
}
```

### Test Details
```
GET /qcbin/rest/domains/{domain}/projects/{project}/tests/{test_id}
```
Returns detailed information for a specific test.

### Design Steps
```
GET /qcbin/rest/domains/{domain}/projects/{project}/design-steps?query={parent-id[test_id]}
```
Returns design steps for a test.

**Response**:
```json
{
  "entities": [
    {
      "Type": "design-step",
      "Fields": [
        {"Name": "id", "values": [{"value": "10011"}]},
        {"Name": "parent-id", "values": [{"value": "1001"}]},
        {"Name": "step-order", "values": [{"value": "1"}]},
        {"Name": "step-name", "values": [{"value": "Step 1: Open Application"}]},
        {"Name": "description", "values": [{"value": "<html><body>Launch the application</body></html>"}]},
        {"Name": "expected", "values": [{"value": "<html><body>Home page loads</body></html>"}]}
      ]
    }
  ],
  "TotalResults": 4
}
```

### Attachments
```
GET /qcbin/rest/domains/{domain}/projects/{project}/attachments?query={parent-type[test];parent-id[1001]}
```
Returns attachments for an entity.

**Response**:
```json
{
  "entities": [
    {
      "Type": "attachment",
      "Fields": [
        {"Name": "id", "values": [{"value": "10011"}]},
        {"Name": "name", "values": [{"value": "TestCase_Specification_1001.docx"}]},
        {"Name": "file-size", "values": [{"value": "25600"}]},
        {"Name": "parent-id", "values": [{"value": "1001"}]},
        {"Name": "parent-type", "values": [{"value": "test"}]}
      ]
    }
  ],
  "TotalResults": 2
}
```

### Releases
```
GET /qcbin/rest/domains/{domain}/projects/{project}/releases
```
Returns releases for Test Lab.

### Defects
```
GET /qcbin/rest/domains/{domain}/projects/{project}/defects
```
Returns defects.

## Sample Data Structure

### Test Folder Hierarchy
```
Subject (id: 1, parent-id: 0)
├── Functional Tests (id: 2, parent-id: 1)
│   ├── Login Module (id: 5, parent-id: 2)
│   │   ├── TC_Login_ValidCredentials (test id: 1001)
│   │   ├── TC_Login_InvalidPassword (test id: 1002)
│   │   └── TC_Login_EmptyFields (test id: 1003)
│   └── User Management (id: 6, parent-id: 2)
│       ├── TC_CreateUser_Success (test id: 2001)
│       └── TC_UpdateUser_Profile (test id: 2002)
├── Integration Tests (id: 3, parent-id: 1)
└── Regression (id: 4, parent-id: 1)

Automation (id: 100, parent-id: 0)
├── API Tests (id: 101, parent-id: 100)
│   └── API_GET_Users (test id: 3001)
└── UI Tests (id: 102, parent-id: 100)
```

### Test Fields
Each test includes:
- `id`: Unique test identifier
- `name`: Test case name
- `status`: Ready, Design, Repair
- `owner`: Test owner username
- `parent-id`: Folder ID containing the test
- `description`: HTML-formatted description
- `test-type`: MANUAL, API-TEST, etc.
- `creation-time`: Test creation timestamp
- `designer`: Test creator username

### Design Steps Fields
Each design step includes:
- `id`: Unique step identifier
- `parent-id`: Test ID
- `step-order`: Step sequence number
- `step-name`: Step title
- `description`: HTML-formatted step description
- `expected`: HTML-formatted expected result

## Testing with cURL

### Full Authentication Flow
```bash
# Step 1: Authenticate
curl -X POST http://localhost:8001/qcbin/authentication-point/authenticate \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" \
  -c cookies.txt

# Step 2: Create site session
curl -X POST http://localhost:8001/qcbin/rest/site-session \
  -b cookies.txt \
  -c cookies.txt

# Step 3: Get domains
curl http://localhost:8001/qcbin/rest/domains \
  -b cookies.txt

# Step 4: Get projects
curl http://localhost:8001/qcbin/rest/domains/DEFAULT/projects \
  -b cookies.txt

# Step 5: Get test folders
curl "http://localhost:8001/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/test-folders?query={parent-id[0]}" \
  -b cookies.txt

# Step 6: Get tests in folder
curl "http://localhost:8001/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/tests?query={parent-id[5]}" \
  -b cookies.txt

# Step 7: Get design steps for test
curl "http://localhost:8001/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/design-steps?query={parent-id[1001]}" \
  -b cookies.txt

# Step 8: Get attachments for test
curl "http://localhost:8001/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/attachments?query={parent-type[test];parent-id[1001]}" \
  -b cookies.txt
```

## Integration with ALM Client

The mock server is designed to work seamlessly with `backend/app/alm.py`. Simply update the `ALM_BASE_URL` in `.env`:

```env
# Development (mock server)
ALM_BASE_URL=http://localhost:8001/qcbin

# Production (real ALM server)
# ALM_BASE_URL=https://your-alm-server.com/qcbin
```

No code changes required in the application!

## Running Both Servers

To run the complete application with mock ALM:

1. **Terminal 1**: Start MongoDB
   ```cmd
   docker start alm_mongo
   ```

2. **Terminal 2**: Start Mock ALM Server
   ```cmd
   scripts\start-mock-alm.bat
   ```

3. **Terminal 3**: Start Backend API
   ```cmd
   cd backend
   %USERPROFILE%\pyenv\Scripts\activate
   uvicorn app.main:app --reload
   ```

4. **Terminal 4**: Start Frontend
   ```cmd
   cd frontend
   npm run dev
   ```

Access the application at `http://localhost:5173` and use any credentials to login (mock server accepts all).

## Troubleshooting

### Port 8001 Already in Use
Kill the existing process:
```cmd
netstat -ano | findstr :8001
taskkill /PID <process_id> /F
```

### Mock Server Not Responding
Check if Python virtual environment is activated:
```cmd
%USERPROFILE%\pyenv\Scripts\activate
python --version
```

### Cookie Issues
The mock server requires all 4 cookies. Verify cookies are set:
```bash
curl -v http://localhost:8001/qcbin/rest/domains -b cookies.txt
```

## Extending the Mock Server

To add more test data, edit `backend/app/mock_alm.py`:

### Adding New Test Folders
In the `get_test_folders()` function, add new folder dictionaries:
```python
{
    "id": 200,
    "name": "My New Folder",
    "parent-id": 1,
    "description": "Custom folder",
    "has-attachments": "N"
}
```

### Adding New Tests
In the `get_tests()` function, add test cases:
```python
{
    "id": 5001,
    "name": "TC_MyNewTest",
    "status": "Ready",
    "owner": "tester",
    "parent-id": 5,
    "description": "<html><body>Test description</body></html>",
    "test-type": "MANUAL"
}
```

### Adding New Design Steps
In the `get_design_steps()` function, add steps for your tests.

Restart the mock server after making changes.
