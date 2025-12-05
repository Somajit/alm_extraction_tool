"""
mock_alm.py

FastAPI-based mock server for HP ALM /qcbin REST APIs.

This mock server simulates ALM REST API responses with proper authentication,
cookies, and entity structures. It returns ALM-style JSON format:

{
  "entities": [
    {
      "Type": "<entity-type>",
      "Fields": [
        {"Name": "<field-name>", "values": [{"value": "<value>"}]}
      ]
    }
  ],
  "TotalResults": N
}

Authentication workflow:
1. POST /qcbin/authentication-point/authenticate → Sets LWSSO_COOKIE_KEY
2. POST /qcbin/rest/site-session → Sets QCSession, ALM_USER, XSRF-TOKEN

All subsequent API calls require these 4 cookies.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# Add parent directory to path to import alm_format_utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alm_format_utils import simple_to_alm

app = FastAPI(title="Mock ALM API", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------
# In-memory session storage (simulates server-side sessions)
# --------------------------------------------------------------------
active_sessions = {}

# --------------------------------------------------------------------
# ALM JSON helper builders - Using generic format utilities
# --------------------------------------------------------------------

def make_alm_response(entity_type: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build an ALM-style response from simplified entity dictionaries.
    
    This is the SINGLE generic function to convert simplified format to ALM format.
    Update this function if ALM response format changes.
    
    Args:
        entity_type: Type of entity (test, defect, test-folder, etc.)
        entities: List of simplified entity dictionaries like {"id": "1", "name": "Test"}
    
    Returns:
        ALM-formatted response: {"entities": [...], "TotalResults": N}
    """
    return simple_to_alm(entities, entity_type)


def validate_cookies(request: Request) -> bool:
    """Check if request has all required ALM cookies."""
    cookie = request.headers.get("cookie", "")
    required = ["LWSSO_COOKIE_KEY", "QCSession", "ALM_USER", "XSRF-TOKEN"]
    return all(req in cookie for req in required)


# --------------------------------------------------------------------
# Authentication & site-session
# --------------------------------------------------------------------

@app.post("/qcbin/authentication-point/authenticate")
async def authenticate(request: Request):
    """
    Step 1: Authenticate user and set LWSSO_COOKIE_KEY.
    
    Request body (form-encoded or Basic Auth):
      username=<user>&password=<pass>
    
    Response: Sets LWSSO_COOKIE_KEY cookie
    """
    # In real ALM, this validates credentials. Here we accept any.
    body = await request.body()
    body_str = body.decode('utf-8') if body else ""
    
    # Simple validation - check if username/password present
    if "username" not in body_str and not request.headers.get("authorization"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    response = Response(content="<html><body>Authenticated</body></html>", media_type="text/html")
    response.set_cookie(
        key="LWSSO_COOKIE_KEY",
        value="mock_lwsso_token_12345",
        path="/",
        httponly=True
    )
    return response


@app.post("/qcbin/rest/site-session")
async def create_site_session(request: Request):
    """
    Step 2: Create site session and set QCSession, ALM_USER, XSRF-TOKEN.
    
    Requires: LWSSO_COOKIE_KEY cookie from step 1
    
    Response: Sets QCSession, ALM_USER, XSRF-TOKEN cookies
    """
    cookie = request.headers.get("cookie", "")
    if "LWSSO_COOKIE_KEY" not in cookie:
        raise HTTPException(status_code=401, detail="LWSSO cookie required")
    
    session_id = "mock_session_67890"
    active_sessions[session_id] = {"username": "mock_user", "authenticated": True}
    
    response = Response(content="<SessionId>mock_session_67890</SessionId>", media_type="text/xml")
    response.set_cookie(key="QCSession", value=session_id, path="/", httponly=True)
    response.set_cookie(key="ALM_USER", value="mock_user", path="/", httponly=False)
    response.set_cookie(key="XSRF-TOKEN", value="mock_xsrf_token", path="/", httponly=False)
    
    return response


@app.delete("/qcbin/rest/site-session")
async def delete_site_session(request: Request):
    """Delete site session (logout)."""
    cookie = request.headers.get("cookie", "")
    if "QCSession" in cookie:
        # Extract session ID and remove from active sessions
        session_id = "mock_session_67890"
        active_sessions.pop(session_id, None)
    
    return Response(status_code=200)


@app.get("/qcbin/authentication-point/logout")
async def logout():
    """Final logout step - clear LWSSO cookie."""
    return Response(content="Logged out", status_code=200)


# --------------------------------------------------------------------
# Domains
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains")
async def get_domains(request: Request):
    """
    Get list of ALM domains.
    
    Requires: All 4 cookies (LWSSO, QCSession, ALM_USER, XSRF-TOKEN)
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Simplified format
    domains = [
        {"DOMAIN_NAME": "DEFAULT"},
        {"DOMAIN_NAME": "QUALITY_CENTER"},
        {"DOMAIN_NAME": "DEMO_DOMAIN"}
    ]
    
    # Convert to ALM format
    data = make_alm_response("Domain", domains)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains/{domain}/projects")
async def get_projects(domain: str, request: Request):
    """
    Get list of projects in a domain.
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return different projects based on domain
    if domain.upper() == "DEFAULT":
        projects = [
            {"PROJECT_NAME": "DEMO_PROJECT"},
            {"PROJECT_NAME": "TEST_PROJECT"}
        ]
    elif domain.upper() == "QUALITY_CENTER":
        projects = [
            {"PROJECT_NAME": "QC_PROJECT_1"},
            {"PROJECT_NAME": "QC_PROJECT_2"}
        ]
    else:
        projects = [
            {"PROJECT_NAME": f"{domain}_PROJECT_1"}
        ]
    
    data = make_list_response("Project", projects)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# Test Folders (Test Plan hierarchy)
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/test-folders")
async def get_test_folders(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get test folders from Test Plan.
    
    Query parameter format: {parent-id[0]} for root folders
                           {parent-id[123]} for children of folder 123
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse parent_id from query parameter
    parent_id = 0
    if query:
        # Extract parent-id from query like {parent-id[123]}
        import re
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = int(match.group(1))
    
    # Return hierarchical folder structure
    if parent_id == 0:
        # Root folders - 5 top-level nodes
        folders = [
            {
                "id": 1,
                "name": "Subject",
                "parent-id": 0,
                "description": "Root test folder",
                "has-attachments": "Y"
            },
            {
                "id": 100,
                "name": "Automation",
                "parent-id": 0,
                "description": "Automated tests",
                "has-attachments": "Y"
            },
            {
                "id": 200,
                "name": "Security Tests",
                "parent-id": 0,
                "description": "Security and penetration tests",
                "has-attachments": "Y"
            },
            {
                "id": 300,
                "name": "Performance Tests",
                "parent-id": 0,
                "description": "Load and performance testing",
                "has-attachments": "Y"
            },
            {
                "id": 400,
                "name": "Mobile Tests",
                "parent-id": 0,
                "description": "iOS and Android test cases",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 1:
        # Children of Subject folder - Level 1
        folders = [
            {
                "id": 2,
                "name": "Functional Tests",
                "parent-id": 1,
                "description": "Functional test cases",
                "has-attachments": "Y"
            },
            {
                "id": 3,
                "name": "Integration Tests",
                "parent-id": 1,
                "description": "Integration test cases",
                "has-attachments": "Y"
            },
            {
                "id": 4,
                "name": "Regression",
                "parent-id": 1,
                "description": "Regression test suite",
                "has-attachments": "Y"
            },
            {
                "id": 7,
                "name": "Smoke Tests",
                "parent-id": 1,
                "description": "Quick smoke tests",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 2:
        # Children of Functional Tests - Level 2
        folders = [
            {
                "id": 5,
                "name": "Login Module",
                "parent-id": 2,
                "description": "Login functionality tests",
                "has-attachments": "Y"
            },
            {
                "id": 6,
                "name": "User Management",
                "parent-id": 2,
                "description": "User CRUD operations",
                "has-attachments": "Y"
            },
            {
                "id": 8,
                "name": "Payment Processing",
                "parent-id": 2,
                "description": "Payment gateway tests",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 5:
        # Children of Login Module - Level 3
        folders = [
            {
                "id": 51,
                "name": "SSO Login",
                "parent-id": 5,
                "description": "Single Sign-On tests",
                "has-attachments": "Y"
            },
            {
                "id": 52,
                "name": "OAuth Login",
                "parent-id": 5,
                "description": "OAuth authentication tests",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 6:
        # Children of User Management - Level 3
        folders = [
            {
                "id": 61,
                "name": "User Roles",
                "parent-id": 6,
                "description": "Role-based access control",
                "has-attachments": "Y"
            },
            {
                "id": 62,
                "name": "User Permissions",
                "parent-id": 6,
                "description": "Permission management tests",
                "has-attachments": "Y"
            },
            {
                "id": 63,
                "name": "User Profile",
                "parent-id": 6,
                "description": "Profile update tests",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 100:
        # Children of Automation folder
        folders = [
            {
                "id": 101,
                "name": "API Tests",
                "parent-id": 100,
                "description": "REST API test automation",
                "has-attachments": "Y"
            },
            {
                "id": 102,
                "name": "UI Tests",
                "parent-id": 100,
                "description": "Selenium UI tests",
                "has-attachments": "Y"
            },
            {
                "id": 103,
                "name": "Database Tests",
                "parent-id": 100,
                "description": "Database validation tests",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 101:
        # Children of API Tests - Level 3 under Automation
        folders = [
            {
                "id": 1011,
                "name": "REST API",
                "parent-id": 101,
                "description": "RESTful API tests",
                "has-attachments": "Y"
            },
            {
                "id": 1012,
                "name": "GraphQL API",
                "parent-id": 101,
                "description": "GraphQL endpoint tests",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 200:
        # Children of Security Tests
        folders = [
            {
                "id": 201,
                "name": "Authentication Security",
                "parent-id": 200,
                "description": "Auth security tests",
                "has-attachments": "Y"
            },
            {
                "id": 202,
                "name": "SQL Injection",
                "parent-id": 200,
                "description": "SQL injection tests",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 300:
        # Children of Performance Tests
        folders = [
            {
                "id": 301,
                "name": "Load Tests",
                "parent-id": 300,
                "description": "Load testing scenarios",
                "has-attachments": "Y"
            },
            {
                "id": 302,
                "name": "Stress Tests",
                "parent-id": 300,
                "description": "Stress testing scenarios",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 400:
        # Children of Mobile Tests
        folders = [
            {
                "id": 401,
                "name": "iOS Tests",
                "parent-id": 400,
                "description": "iOS app tests",
                "has-attachments": "Y"
            },
            {
                "id": 402,
                "name": "Android Tests",
                "parent-id": 400,
                "description": "Android app tests",
                "has-attachments": "Y"
            }
        ]
    else:
        # No children for other folders
        folders = []
    
    data = make_list_response("test-folder", folders)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/tests")
async def get_tests(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get tests in a folder.
    
    Query parameter format: {parent-id[folder_id]}
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse parent_id (folder_id) from query
    folder_id = 1
    if query:
        import re
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            folder_id = int(match.group(1))
    
    # Return tests based on folder
    if folder_id == 5:  # Login Module
        tests = [
            {
                "id": 1001,
                "name": "TC_Login_ValidCredentials",
                "status": "Ready",
                "owner": "john.doe",
                "parent-id": 5,
                "description": "<html><body>Test login with valid username and password</body></html>",
                "creation-time": "2025-01-15 10:30:00",
                "designer": "john.doe",
                "test-type": "MANUAL",
                "has-attachments": "Y"
            },
            {
                "id": 1002,
                "name": "TC_Login_InvalidPassword",
                "status": "Design",
                "owner": "jane.smith",
                "parent-id": 5,
                "description": "<html><body>Verify error message with invalid password</body></html>",
                "creation-time": "2025-01-16 14:20:00",
                "designer": "jane.smith",
                "test-type": "MANUAL",
                "has-attachments": "Y"
            },
            {
                "id": 1003,
                "name": "TC_Login_EmptyFields",
                "status": "Ready",
                "owner": "john.doe",
                "parent-id": 5,
                "description": "<html><body>Test validation for empty login fields</body></html>",
                "creation-time": "2025-01-17 09:15:00",
                "designer": "john.doe",
                "test-type": "MANUAL",
                "has-attachments": "N"
            },
            {
                "id": 1004,
                "name": "TC_Login_RememberMe",
                "status": "Ready",
                "owner": "john.doe",
                "parent-id": 5,
                "description": "<html><body>Test remember me functionality</body></html>",
                "creation-time": "2025-01-18 11:00:00",
                "designer": "john.doe",
                "test-type": "MANUAL",
                "has-attachments": "Y"
            }
        ]
    elif folder_id == 6:  # User Management
        tests = [
            {
                "id": 2001,
                "name": "TC_CreateUser_Success",
                "status": "Ready",
                "owner": "admin",
                "parent-id": 6,
                "description": "<html><body>Create new user with all required fields</body></html>",
                "creation-time": "2025-01-18 11:00:00",
                "designer": "admin",
                "test-type": "MANUAL",
                "has-attachments": "Y"
            },
            {
                "id": 2002,
                "name": "TC_UpdateUser_Profile",
                "status": "Repair",
                "owner": "jane.smith",
                "parent-id": 6,
                "description": "<html><body>Update user profile information</body></html>",
                "creation-time": "2025-01-19 15:45:00",
                "designer": "jane.smith",
                "test-type": "MANUAL",
                "has-attachments": "Y"
            },
            {
                "id": 2003,
                "name": "TC_DeleteUser",
                "status": "Ready",
                "owner": "admin",
                "parent-id": 6,
                "description": "<html><body>Delete user and verify cleanup</body></html>",
                "creation-time": "2025-01-20 09:30:00",
                "designer": "admin",
                "test-type": "MANUAL",
                "has-attachments": "N"
            }
        ]
    elif folder_id == 51:  # SSO Login
        tests = [
            {
                "id": 5101,
                "name": "TC_SSO_GoogleAuth",
                "status": "Ready",
                "owner": "john.doe",
                "parent-id": 51,
                "description": "<html><body>Test Google SSO authentication</body></html>",
                "creation-time": "2025-01-21 10:00:00",
                "designer": "john.doe",
                "test-type": "MANUAL",
                "has-attachments": "Y"
            },
            {
                "id": 5102,
                "name": "TC_SSO_MicrosoftAuth",
                "status": "Ready",
                "owner": "john.doe",
                "parent-id": 51,
                "description": "<html><body>Test Microsoft SSO authentication</body></html>",
                "creation-time": "2025-01-21 11:00:00",
                "designer": "john.doe",
                "test-type": "MANUAL",
                "has-attachments": "Y"
            }
        ]
    elif folder_id == 101:  # API Tests
        tests = [
            {
                "id": 3001,
                "name": "API_GET_Users",
                "status": "Ready",
                "owner": "automation",
                "parent-id": 101,
                "description": "<html><body>Test GET /api/users endpoint</body></html>",
                "creation-time": "2025-01-20 10:00:00",
                "designer": "automation",
                "test-type": "API-TEST",
                "has-attachments": "Y"
            },
            {
                "id": 3002,
                "name": "API_POST_CreateUser",
                "status": "Ready",
                "owner": "automation",
                "parent-id": 101,
                "description": "<html><body>Test POST /api/users endpoint</body></html>",
                "creation-time": "2025-01-20 11:00:00",
                "designer": "automation",
                "test-type": "API-TEST",
                "has-attachments": "Y"
            }
        ]
    elif folder_id == 1011:  # REST API
        tests = [
            {
                "id": 10111,
                "name": "REST_Authentication",
                "status": "Ready",
                "owner": "automation",
                "parent-id": 1011,
                "description": "<html><body>Test REST API authentication</body></html>",
                "creation-time": "2025-01-22 10:00:00",
                "designer": "automation",
                "test-type": "API-TEST",
                "has-attachments": "Y"
            },
            {
                "id": 10112,
                "name": "REST_CRUD_Operations",
                "status": "Ready",
                "owner": "automation",
                "parent-id": 1011,
                "description": "<html><body>Test REST CRUD operations</body></html>",
                "creation-time": "2025-01-22 11:00:00",
                "designer": "automation",
                "test-type": "API-TEST",
                "has-attachments": "Y"
            }
        ]
    else:
        # Return generic tests for other folders
        tests = [
            {
                "id": folder_id * 100 + 1,
                "name": f"TC_Test_1_Folder_{folder_id}",
                "status": "Ready",
                "owner": "tester",
                "parent-id": folder_id,
                "description": f"<html><body>Test case 1 in folder {folder_id}</body></html>",
                "creation-time": "2025-01-01 10:00:00",
                "designer": "tester",
                "test-type": "MANUAL"
            },
            {
                "id": folder_id * 100 + 2,
                "name": f"TC_Test_2_Folder_{folder_id}",
                "status": "Design",
                "owner": "tester",
                "parent-id": folder_id,
                "description": f"<html><body>Test case 2 in folder {folder_id}</body></html>",
                "creation-time": "2025-01-02 11:00:00",
                "designer": "tester",
                "test-type": "MANUAL"
            }
        ]
    
    data = make_list_response("test", tests)
    return JSONResponse(content=data)


@app.get("/qcbin/rest/domains/{domain}/projects/{project}/tests/{test_id}")
async def get_test_details(
    domain: str,
    project: str,
    test_id: int,
    request: Request
):
    """
    Get detailed information for a specific test.
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return detailed test information
    test = {
        "id": test_id,
        "name": f"TC_TestDetails_{test_id}",
        "status": "Ready",
        "owner": "john.doe",
        "parent-id": 5,
        "description": f"<html><body>Detailed description for test {test_id}</body></html>",
        "creation-time": "2025-01-15 10:30:00",
        "last-modified": "2025-02-01 14:20:00",
        "designer": "john.doe",
        "test-type": "MANUAL",
        "exec-status": "Not Completed",
        "estimated-time": "15",
        "steps": "See design steps"
    }
    
    entities = [make_entity("test", test)]
    data = {"entities": entities, "TotalResults": 1}
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# Design Steps
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/design-steps")
async def get_design_steps(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get design steps for a test.
    
    Query parameter format: {parent-id[test_id]}
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse test_id from query
    test_id = 1001
    if query:
        import re
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            test_id = int(match.group(1))
    
    # Return design steps for the test (3+ steps, some with attachments)
    steps = [
        {
            "id": test_id * 10 + 1,
            "parent-id": test_id,
            "step-order": 1,
            "step-name": "Step 1: Open Application",
            "description": "<html><body>Launch the application and verify home page loads</body></html>",
            "expected": "<html><body>Home page should display with all elements</body></html>",
            "link-test": "",
            "has-attachments": "Y"
        },
        {
            "id": test_id * 10 + 2,
            "parent-id": test_id,
            "step-order": 2,
            "step-name": "Step 2: Navigate to Login",
            "description": "<html><body>Click on Login button in navigation bar</body></html>",
            "expected": "<html><body>Login page should be displayed</body></html>",
            "link-test": "",
            "has-attachments": "N"
        },
        {
            "id": test_id * 10 + 3,
            "parent-id": test_id,
            "step-order": 3,
            "step-name": "Step 3: Enter Credentials",
            "description": "<html><body>Enter username and password in respective fields</body></html>",
            "expected": "<html><body>Fields should accept input</body></html>",
            "link-test": "",
            "has-attachments": "Y"
        },
        {
            "id": test_id * 10 + 4,
            "parent-id": test_id,
            "step-order": 4,
            "step-name": "Step 4: Click Login Button",
            "description": "<html><body>Click the Login submit button</body></html>",
            "expected": "<html><body>User should be logged in and redirected to dashboard</body></html>",
            "link-test": "",
            "has-attachments": "N"
        }
    ]
    
    data = make_alm_response("design-step", steps)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# Attachments
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/attachments")
async def get_attachments(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get attachments for an entity (test-folder, test, run, defect, etc.).
    
    Query parameter format: {parent-type[test];parent-id[1001]}
                           {parent-type[test-folder];parent-id[5]}
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse parent-type and parent-id from query
    parent_type = "test"
    parent_id = 1001
    
    if query:
        import re
        type_match = re.search(r'parent-type\[([^\]]+)\]', query)
        id_match = re.search(r'parent-id\[(\d+)\]', query)
        
        if type_match:
            parent_type = type_match.group(1)
        if id_match:
            parent_id = int(id_match.group(1))
    
    # Return attachments based on parent type (PNG files for screenshots)
    if parent_type == "test":
        attachments = [
            {
                "id": parent_id * 10 + 1,
                "name": f"TestCase_Specification_{parent_id}.docx",
                "description": "Test case specification document",
                "file-size": 25600,
                "parent-id": parent_id,
                "parent-type": "test",
                "ref-type": "File",
                "last-modified": "2025-01-20 09:30:00"
            },
            {
                "id": parent_id * 10 + 2,
                "name": f"Screenshot_TestData_{parent_id}.png",
                "description": "Sample test data screenshot",
                "file-size": 102400,
                "parent-id": parent_id,
                "parent-type": "test",
                "ref-type": "File",
                "last-modified": "2025-01-21 11:15:00"
            },
            {
                "id": parent_id * 10 + 3,
                "name": f"TestEnvironment_{parent_id}.png",
                "description": "Test environment setup screenshot",
                "file-size": 156800,
                "parent-id": parent_id,
                "parent-type": "test",
                "ref-type": "File",
                "last-modified": "2025-01-22 10:00:00"
            }
        ]
    elif parent_type == "test-folder":
        attachments = [
            {
                "id": parent_id * 10 + 1,
                "name": f"Folder_Documentation_{parent_id}.pdf",
                "description": "Folder documentation and guidelines",
                "file-size": 51200,
                "parent-id": parent_id,
                "parent-type": "test-folder",
                "ref-type": "File",
                "last-modified": "2025-01-15 14:00:00"
            },
            {
                "id": parent_id * 10 + 2,
                "name": f"Folder_Overview_{parent_id}.png",
                "description": "Folder structure overview diagram",
                "file-size": 204800,
                "parent-id": parent_id,
                "parent-type": "test-folder",
                "ref-type": "File",
                "last-modified": "2025-01-16 09:00:00"
            }
        ]
    elif parent_type == "design-step":
        attachments = [
            {
                "id": parent_id * 10 + 1,
                "name": f"Step_Screenshot_{parent_id}.png",
                "description": "Screenshot for design step",
                "file-size": 307200,
                "parent-id": parent_id,
                "parent-type": "design-step",
                "ref-type": "File",
                "last-modified": "2025-01-23 14:30:00"
            },
            {
                "id": parent_id * 10 + 2,
                "name": f"Step_ExpectedResult_{parent_id}.png",
                "description": "Expected result screenshot",
                "file-size": 256000,
                "parent-id": parent_id,
                "parent-type": "design-step",
                "ref-type": "File",
                "last-modified": "2025-01-23 14:35:00"
            }
        ]
    elif parent_type == "test-set":
        attachments = [
            {
                "id": parent_id * 10 + 1,
                "name": f"TestSet_Plan_{parent_id}.pdf",
                "description": "Test set execution plan",
                "file-size": 76800,
                "parent-id": parent_id,
                "parent-type": "test-set",
                "ref-type": "File",
                "last-modified": "2025-01-24 10:00:00"
            },
            {
                "id": parent_id * 10 + 2,
                "name": f"TestSet_Results_{parent_id}.png",
                "description": "Test set results screenshot",
                "file-size": 409600,
                "parent-id": parent_id,
                "parent-type": "test-set",
                "ref-type": "File",
                "last-modified": "2025-01-24 16:30:00"
            }
        ]
    elif parent_type == "run":
        attachments = [
            {
                "id": parent_id * 10 + 1,
                "name": f"Run_Screenshot_{parent_id}.png",
                "description": "Test run execution screenshot",
                "file-size": 512000,
                "parent-id": parent_id,
                "parent-type": "run",
                "ref-type": "File",
                "last-modified": "2025-01-25 11:30:00"
            },
            {
                "id": parent_id * 10 + 2,
                "name": f"Run_Logs_{parent_id}.txt",
                "description": "Test run execution logs",
                "file-size": 20480,
                "parent-id": parent_id,
                "parent-type": "run",
                "ref-type": "File",
                "last-modified": "2025-01-25 11:35:00"
            }
        ]
    elif parent_type == "defect":
        attachments = [
            {
                "id": parent_id * 10 + 1,
                "name": f"Defect_Screenshot_{parent_id}.png",
                "description": "Defect screenshot showing the issue",
                "file-size": 614400,
                "parent-id": parent_id,
                "parent-type": "defect",
                "ref-type": "File",
                "last-modified": "2025-01-26 09:15:00"
            },
            {
                "id": parent_id * 10 + 2,
                "name": f"Defect_Logs_{parent_id}.txt",
                "description": "Application logs during defect occurrence",
                "file-size": 30720,
                "parent-id": parent_id,
                "parent-type": "defect",
                "ref-type": "File",
                "last-modified": "2025-01-26 09:20:00"
            }
        ]
    else:
        attachments = []
    
    data = make_alm_response("attachment", attachments)
    return JSONResponse(content=data)


@app.get("/qcbin/rest/domains/{domain}/projects/{project}/attachments/{attachment_id}")
async def download_attachment(
    domain: str,
    project: str,
    attachment_id: str,
    request: Request
):
    """
    Download attachment file content.
    Returns dummy file content for testing.
    For PNG files, returns a minimal valid PNG binary.
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Determine file type based on attachment_id pattern
    attachment_num = int(attachment_id) % 10
    
    if attachment_num in [2, 3]:  # PNG screenshots
        filename = f"attachment_{attachment_id}.png"
        # Minimal valid PNG file (1x1 transparent pixel)
        png_content = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xb4'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        return Response(
            content=png_content,
            media_type="image/png",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    else:  # Text/document files
        filename = f"attachment_{attachment_id}.txt"
        content = f"This is a mock attachment file with ID: {attachment_id}\n"
        content += f"Generated at: {datetime.now().isoformat()}\n"
        content += "=" * 50 + "\n"
        content += "This is dummy content for testing attachment downloads.\n"
        content += "In production, this would be the actual file content from ALM.\n"
        
        return Response(
            content=content.encode('utf-8'),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )


# --------------------------------------------------------------------
# Releases & Cycles (Test Lab)
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/releases")
async def get_releases(
    domain: str,
    project: str,
    request: Request
):
    """Get releases for Test Lab."""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    releases = [
        {
            "id": 1001,
            "name": "Release 1.0",
            "start-date": "2025-01-01",
            "end-date": "2025-03-31",
            "description": "Initial release",
            "parent-id": ""
        },
        {
            "id": 1002,
            "name": "Release 2.0",
            "start-date": "2025-04-01",
            "end-date": "2025-06-30",
            "description": "Major feature release",
            "parent-id": ""
        }
    ]
    
    data = make_list_response("release", releases)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# Defects
# --------------------------------------------------------------------

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/defects")
async def get_defects(
    domain: str,
    project: str,
    request: Request
):
    """Get defects."""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    defects = [
        {
            "id": 1,
            "name": "Login button not responsive",
            "description": "<html><body>Login button does not respond to click</body></html>",
            "status": "New",
            "severity": "2-High",
            "priority": "1-High",
            "detected-by": "john.doe",
            "owner": "jane.smith",
            "creation-time": "2025-01-25 10:00:00",
            "has-attachments": "Y"
        },
        {
            "id": 2,
            "name": "Incorrect error message",
            "description": "<html><body>Error message shows wrong text</body></html>",
            "status": "Open",
            "severity": "3-Medium",
            "priority": "2-Medium",
            "detected-by": "jane.smith",
            "owner": "john.doe",
            "creation-time": "2025-01-26 14:30:00",
            "has-attachments": "Y"
        },
        {
            "id": 3,
            "name": "Page load timeout",
            "description": "<html><body>Dashboard page takes too long to load</body></html>",
            "status": "Open",
            "severity": "2-High",
            "priority": "1-High",
            "detected-by": "john.doe",
            "owner": "dev.team",
            "creation-time": "2025-01-27 09:15:00",
            "has-attachments": "Y"
        },
        {
            "id": 4,
            "name": "Data validation error",
            "description": "<html><body>Form accepts invalid email format</body></html>",
            "status": "Fixed",
            "severity": "3-Medium",
            "priority": "2-Medium",
            "detected-by": "tester1",
            "owner": "jane.smith",
            "creation-time": "2025-01-28 11:00:00",
            "has-attachments": "N"
        },
        {
            "id": 5,
            "name": "UI alignment issue",
            "description": "<html><body>Buttons misaligned on mobile view</body></html>",
            "status": "Open",
            "severity": "4-Low",
            "priority": "3-Low",
            "detected-by": "tester2",
            "owner": "ui.team",
            "creation-time": "2025-01-29 14:20:00",
            "has-attachments": "Y"
        },
        {
            "id": 6,
            "name": "Database connection timeout",
            "description": "<html><body>Intermittent database connection failures</body></html>",
            "status": "New",
            "severity": "1-Critical",
            "priority": "1-High",
            "detected-by": "john.doe",
            "owner": "db.team",
            "creation-time": "2025-01-30 10:45:00",
            "has-attachments": "Y"
        },
        {
            "id": 7,
            "name": "Memory leak in dashboard",
            "description": "<html><body>Dashboard consumes excessive memory over time</body></html>",
            "status": "Open",
            "severity": "2-High",
            "priority": "1-High",
            "detected-by": "performance.team",
            "owner": "dev.team",
            "creation-time": "2025-01-31 09:00:00",
            "has-attachments": "N"
        },
        {
            "id": 8,
            "name": "API returns 500 error",
            "description": "<html><body>GET /api/users endpoint returns 500</body></html>",
            "status": "Fixed",
            "severity": "1-Critical",
            "priority": "1-High",
            "detected-by": "automation",
            "owner": "api.team",
            "creation-time": "2025-02-01 11:30:00",
            "has-attachments": "Y"
        },
        {
            "id": 9,
            "name": "Search not returning results",
            "description": "<html><body>Search functionality returns empty results</body></html>",
            "status": "Open",
            "severity": "3-Medium",
            "priority": "2-Medium",
            "detected-by": "tester1",
            "owner": "search.team",
            "creation-time": "2025-02-02 14:00:00",
            "has-attachments": "N"
        },
        {
            "id": 10,
            "name": "File upload fails for large files",
            "description": "<html><body>Cannot upload files larger than 10MB</body></html>",
            "status": "New",
            "severity": "2-High",
            "priority": "2-Medium",
            "detected-by": "john.doe",
            "owner": "storage.team",
            "creation-time": "2025-02-03 10:15:00",
            "has-attachments": "Y"
        },
        {
            "id": 11,
            "name": "Session timeout not working",
            "description": "<html><body>User session does not timeout after inactivity</body></html>",
            "status": "Open",
            "severity": "2-High",
            "priority": "1-High",
            "detected-by": "security.team",
            "owner": "auth.team",
            "creation-time": "2025-02-04 09:30:00",
            "has-attachments": "Y"
        },
        {
            "id": 12,
            "name": "Export to Excel broken",
            "description": "<html><body>Excel export feature generates corrupted files</body></html>",
            "status": "Fixed",
            "severity": "3-Medium",
            "priority": "2-Medium",
            "detected-by": "tester2",
            "owner": "export.team",
            "creation-time": "2025-02-05 11:00:00",
            "has-attachments": "Y"
        }
    ]
    
    data = make_alm_response("defect", defects)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# Root / Health
# --------------------------------------------------------------------

@app.get("/")
@app.get("/qcbin")
def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "service": "Mock ALM REST API Server",
        "version": "2.0.0",
        "message": "Mock ALM server running. Use /qcbin/* endpoints for API access."
    }


# --------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Mock ALM REST API Server")
    print("=" * 70)
    print("\nStarting server on http://localhost:8001")
    print("\nAuthentication flow:")
    print("  1. POST /qcbin/authentication-point/authenticate")
    print("  2. POST /qcbin/rest/site-session")
    print("\nAvailable endpoints:")
    print("  - GET  /qcbin/rest/domains")
    print("  - GET  /qcbin/rest/domains/{domain}/projects")
    print("  - GET  /qcbin/rest/domains/{domain}/projects/{project}/test-folders")
    print("  - GET  /qcbin/rest/domains/{domain}/projects/{project}/tests")
    print("  - GET  /qcbin/rest/domains/{domain}/projects/{project}/tests/{id}")
    print("  - GET  /qcbin/rest/domains/{domain}/projects/{project}/design-steps")
    print("  - GET  /qcbin/rest/domains/{domain}/projects/{project}/attachments")
    print("  - GET  /qcbin/rest/domains/{domain}/projects/{project}/releases")
    print("  - GET  /qcbin/rest/domains/{domain}/projects/{project}/defects")
    print("\n" + "=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)

    """
    resp.set_cookie("ALM_USER", "mock_user", httponly=False, path="/qcbin")
    resp.set_cookie("LWSSO_COOKIE_KEY", "mock_lwsso", httponly=True, path="/qcbin")
    resp.set_cookie("QCSession", "mock_qcsession", httponly=True, path="/qcbin")
    resp.set_cookie("XSRF-TOKEN", "mock_xsrf", httponly=False, path="/qcbin")


# --------------------------------------------------------------------
# Authentication & site-session (ALM-style)
# --------------------------------------------------------------------


@app.post("/qcbin/authentication-point/authenticate")
@app.post("/qcbin/api/authentication/sign-in")
def sign_in(request: Request):
    """
    Mock sign-in endpoint.

    In real ALM this returns 200 with auth cookies set.
    Here we simply set the cookies without validating credentials.
    """
    resp = PlainTextResponse("OK")
    set_alm_cookies(resp)
    return resp


@app.post("/qcbin/rest/site-session")
def site_session(request: Request):
    """
    Mock site-session endpoint.

    In real ALM this creates a site session and returns QCSession,
    ALM_USER, and XSRF-TOKEN cookies.
    """
    resp = PlainTextResponse("SITE-SESSION-OK")
    set_alm_cookies(resp)
    return resp


# --------------------------------------------------------------------
# Base prefix used by alm.py
# --------------------------------------------------------------------

BASE_PREFIX = "/qcbin/rest/domains/{domain}/projects/{project}"


# --------------------------------------------------------------------
# TEST PLAN - test-folders & tests (minimal but ALM-style)
# --------------------------------------------------------------------


@app.get(BASE_PREFIX + "/test-folders")
def get_test_folders(domain: str, project: str):
    """
    Mocked test-folder list.

    Typical fields: id, name, parent-id, description, last-modified.
    """
    data = make_list_response(
        "test-folder",
        [
            {
                "id": 1,
                "name": "Subject",
                "parent-id": 0,
                "description": "",
                "last-modified": "2025-01-01 10:00:00",
            },
            {
                "id": 2,
                "name": "Regression",
                "parent-id": 1,
                "description": "",
                "last-modified": "2025-01-02 14:15:00",
            },
        ],
    )
    return JSONResponse(content=data)


@app.get(BASE_PREFIX + "/tests")
def get_tests(
    domain: str,
    project: str,
    folder_id: Optional[str] = Query(default=None, alias="folder-id"),
):
    """
    Mocked tests under a given folder.

    Fields follow typical ALM test entity: id, name, status, owner, subject (folder id).
    """
    folder = folder_id or "2"
    data = make_list_response(
        "test",
        [
            {
                "id": 1001,
                "name": "Login_ValidUser",
                "status": "Design",
                "owner": "sa",
                "subject": folder,
            },
            {
                "id": 1002,
                "name": "Checkout_PlaceOrder",
                "status": "Ready",
                "owner": "sa",
                "subject": folder,
            },
        ],
    )
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# RELEASES & RELEASE-CYCLES
# --------------------------------------------------------------------


@app.get(BASE_PREFIX + "/releases")
def get_releases(domain: str, project: str):
    """
    Mocked releases.

    Based on Micro Focus sample JSON: fields like end-date, start-date,
    last-modified, name, description, scope-items-count, milestones-count,
    id, parent-id, has-attachments, req-count, ver-stamp.
    """
    data = make_list_response(
        "release",
        [
            {
                "end-date": "2020-02-29",
                "last-modified": "2020-02-24 14:11:26",
                "req-count": 1,
                "ver-stamp": 2,
                "name": "release1",
                "description": "",
                "scope-items-count": 0,
                "start-date": "2020-02-24",
                "milestones-count": 0,
                "id": 1001,
                "parent-id": 101,
                "has-attachments": None,
            },
            {
                "end-date": "2020-03-31",
                "last-modified": "2020-03-01 09:00:00",
                "req-count": 5,
                "ver-stamp": 1,
                "name": "release2",
                "description": "",
                "scope-items-count": 2,
                "start-date": "2020-03-01",
                "milestones-count": 1,
                "id": 1002,
                "parent-id": 101,
                "has-attachments": None,
            },
        ],
    )
    return JSONResponse(content=data)


@app.get(BASE_PREFIX + "/release-cycles")
def get_release_cycles(
    domain: str,
    project: str,
    release_id: str = Query(..., alias="release_id"),
):
    """
    Mocked release-cycles for a given release.

    Fields: id, name, parent-id (release id), start-date, end-date,
    last-modified, status.
    """
    data = make_list_response(
        "release-cycle",
        [
            {
                "id": int(f"{release_id}01"),
                "name": "Cycle 1",
                "parent-id": release_id,
                "start-date": "2020-02-24",
                "end-date": "2020-02-29",
                "last-modified": "2020-02-24 14:11:26",
                "status": "Open",
            },
            {
                "id": int(f"{release_id}02"),
                "name": "Cycle 2",
                "parent-id": release_id,
                "start-date": "2020-03-01",
                "end-date": "2020-03-31",
                "last-modified": "2020-03-01 09:00:00",
                "status": "Planned",
            },
        ],
    )
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# TEST LAB - test-sets & test-instances
# --------------------------------------------------------------------


@app.get(BASE_PREFIX + "/test-sets")
def get_test_sets(
    domain: str,
    project: str,
    cycle_id: str = Query(..., alias="cycle_id"),
):
    """
    Mocked test-sets for a given cycle.

    Typical fields: id, name, cycle-id, status, description.
    """
    data = make_list_response(
        "test-set",
        [
            {
                "id": int(f"{cycle_id}01"),
                "name": "Smoke Tests",
                "cycle-id": cycle_id,
                "status": "Open",
                "description": "",
            },
            {
                "id": int(f"{cycle_id}02"),
                "name": "Regression Tests",
                "cycle-id": cycle_id,
                "status": "Open",
                "description": "",
            },
        ],
    )
    return JSONResponse(content=data)


@app.get(BASE_PREFIX + "/test-instances")
def get_test_instances(
    domain: str,
    project: str,
    cycle_id: str = Query(..., alias="cycle_id"),
):
    """
    Mocked test-instances for a given cycle.

    Based on "GET Test Instances" JSON example: fields like test-id, id,
    test-config-id, owner, actual-tester, name, status, order-id, environment.
    """
    data = make_list_response(
        "test-instance",
        [
            {
                "test-id": 1001,
                "os-config": None,
                "data-obj": None,
                "is-dynamic": "N",
                "exec-time": "14:13:41",
                "cycle": cycle_id,
                "has-linkage": "N",
                "exec-status": "Passed",
                "host-name": "",
                "iterations": "",
                "environment": "",
                "actual-tester": "sa",
                "name": "Login Test [1]",
                "status": "Passed",
                "id": 1,
                "test-config-id": 2001,
                "order-id": 1,
            },
            {
                "test-id": 1002,
                "os-config": None,
                "data-obj": None,
                "is-dynamic": "N",
                "exec-time": "15:00:00",
                "cycle": cycle_id,
                "has-linkage": "N",
                "exec-status": "No Run",
                "host-name": "",
                "iterations": "",
                "environment": "",
                "actual-tester": "sa",
                "name": "Checkout Test [1]",
                "status": "No Run",
                "id": 2,
                "test-config-id": 2002,
                "order-id": 2,
            },
        ],
    )
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# RUNS & RUN-STEPS
# --------------------------------------------------------------------


@app.get(BASE_PREFIX + "/runs")
def get_runs(
    domain: str,
    project: str,
    test_instance_id: str = Query(..., alias="test_instance_id"),
):
    """
    Mocked runs for a given test instance.

    Based on "GET Runs" JSON examples - using a subset of key fields:
    test-id, status, owner, testcycl-id, execution-date/time, name, id, cycle-name.
    """
    data = make_list_response(
        "run",
        [
            {
                "id": int(f"{test_instance_id}01"),
                "name": f"Run_{test_instance_id}_1",
                "test-id": 1001,
                "test-instance": test_instance_id,
                "testcycl-id": test_instance_id,
                "status": "Passed",
                "owner": "sa",
                "execution-date": "2020-02-24",
                "execution-time": "14:13:41",
                "cycle-name": "testset1",
            },
            {
                "id": int(f"{test_instance_id}02"),
                "name": f"Run_{test_instance_id}_2",
                "test-id": 1001,
                "test-instance": test_instance_id,
                "testcycl-id": test_instance_id,
                "status": "Failed",
                "owner": "sa",
                "execution-date": "2020-02-24",
                "execution-time": "14:30:00",
                "cycle-name": "testset1",
            },
        ],
    )
    return JSONResponse(content=data)


@app.get(BASE_PREFIX + "/run-steps")
def get_run_steps(
    domain: str,
    project: str,
    run_id: str = Query(..., alias="run_id"),
):
    """
    Mocked run-steps for a given run.

    Based on "GET Run Steps" JSON examples - using fields:
    id, name, status, test-id, desstep-id, parent-id, execution-date/time, step-order.
    """
    data = make_list_response(
        "run-step",
        [
            {
                "test-id": 1001,
                "desstep-id": 5001,
                "id": int(f"{run_id}01"),
                "parent-id": run_id,
                "name": "Open browser",
                "status": "Passed",
                "execution-date": "2020-02-24",
                "execution-time": "14:13:40",
                "step-order": 1,
            },
            {
                "test-id": 1001,
                "desstep-id": 5002,
                "id": int(f"{run_id}02"),
                "parent-id": run_id,
                "name": "Login",
                "status": "Passed",
                "execution-date": "2020-02-24",
                "execution-time": "14:13:41",
                "step-order": 2,
            },
        ],
    )
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# ATTACHMENTS (test instances / runs / defects)
# --------------------------------------------------------------------


@app.get(BASE_PREFIX + "/attachments")
def list_attachments(
    domain: str,
    project: str,
    parent_id: str = Query(..., alias="parent_id"),
):
    """
    Mocked attachments list for a given parent entity.

    Entity shape based on "GET Entity Attachments" JSON examples:
    last-modified, file-size, name, id, parent-id, ref-type, parent-type, etc.
    """
    data = make_list_response(
        "attachment",
        [
            {
                "last-modified": "2020-03-12 18:37:12",
                "vc-cur-ver": None,
                "name": "screenshot1.png",
                "vc-user-name": None,
                "file-size": 102400,
                "ref-subtype": 0,
                "description": "",
                "id": int(f"{parent_id}01"),
                "parent-id": parent_id,
                "ref-type": "File",
                "parent-type": "run",
            },
            {
                "last-modified": "2020-03-12 18:40:00",
                "vc-cur-ver": None,
                "name": "logs.txt",
                "vc-user-name": None,
                "file-size": 2048,
                "ref-subtype": 0,
                "description": "",
                "id": int(f"{parent_id}02"),
                "parent-id": parent_id,
                "ref-type": "File",
                "parent-type": "run",
            },
        ],
    )
    return JSONResponse(content=data)


@app.get(BASE_PREFIX + "/attachments/{attachment_id}")
def download_attachment(
    domain: str,
    project: str,
    attachment_id: str = Path(...),
):
    """
    Mocked binary attachment download.

    Real ALM returns the file stream with application/octet-stream content type.
    """
    binary = f"Dummy content for attachment {attachment_id}\n".encode("utf-8")
    headers = {
        "Content-Disposition": f'attachment; filename="{attachment_id}.txt"',
        "Content-Type": "application/octet-stream",
    }
    return StreamingResponse(
        iter([binary]),
        media_type="application/octet-stream",
        headers=headers,
    )


# --------------------------------------------------------------------
# RELEASES (TestLab)
# --------------------------------------------------------------------

@app.get(BASE_PREFIX + "/releases")
def get_releases(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get list of releases in TestLab.
    
    Releases are the top-level nodes in TestLab hierarchy.
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    releases = [
        {
            "id": 1001,
            "name": "Release 1.0",
            "description": "Initial release",
            "start-date": "2024-01-01",
            "end-date": "2024-03-31",
            "has-linkage": "Y",
            "has-attachments": "Y"
        },
        {
            "id": 1002,
            "name": "Release 2.0",
            "description": "Major feature release",
            "start-date": "2024-04-01",
            "end-date": "2024-06-30",
            "has-linkage": "Y",
            "has-attachments": "Y"
        },
        {
            "id": 1003,
            "name": "Release 3.0",
            "description": "Feature enhancement release",
            "start-date": "2024-07-01",
            "end-date": "2024-09-30",
            "has-linkage": "Y",
            "has-attachments": "Y"
        },
        {
            "id": 1004,
            "name": "Release 4.0",
            "description": "Performance improvements",
            "start-date": "2024-10-01",
            "end-date": "2024-12-31",
            "has-linkage": "Y",
            "has-attachments": "Y"
        },
        {
            "id": 1005,
            "name": "Release 5.0",
            "description": "Next generation platform",
            "start-date": "2025-01-01",
            "end-date": "2025-03-31",
            "has-linkage": "Y",
            "has-attachments": "Y"
        }
    ]
    
    data = make_alm_response("release", releases)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# RELEASE CYCLES (TestLab)
# --------------------------------------------------------------------

@app.get(BASE_PREFIX + "/release-cycles")
def get_release_cycles(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get release cycles for a release.
    
    Query parameter format: {parent-id[1001]} to get cycles for release 1001
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse parent_id from query parameter
    parent_id = None
    if query:
        import re
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = int(match.group(1))
    
    # Return cycles based on parent release (2-3 cycles per release)
    if parent_id == 1001:
        cycles = [
            {
                "id": 2001,
                "name": "Sprint 1",
                "parent-id": 1001,
                "description": "First sprint",
                "start-date": "2024-01-01",
                "end-date": "2024-01-14",
                "has-attachments": "Y"
            },
            {
                "id": 2002,
                "name": "Sprint 2",
                "parent-id": 1001,
                "description": "Second sprint",
                "start-date": "2024-01-15",
                "end-date": "2024-01-28",
                "has-attachments": "Y"
            },
            {
                "id": 2003,
                "name": "Regression Cycle",
                "parent-id": 1001,
                "description": "Full regression testing",
                "start-date": "2024-02-01",
                "end-date": "2024-02-14",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 1002:
        cycles = [
            {
                "id": 2004,
                "name": "Alpha Testing",
                "parent-id": 1002,
                "description": "Internal alpha tests",
                "start-date": "2024-04-01",
                "end-date": "2024-04-15",
                "has-attachments": "Y"
            },
            {
                "id": 2005,
                "name": "Beta Testing",
                "parent-id": 1002,
                "description": "External beta tests",
                "start-date": "2024-04-16",
                "end-date": "2024-05-31",
                "has-attachments": "Y"
            },
            {
                "id": 2006,
                "name": "Production Readiness",
                "parent-id": 1002,
                "description": "Final production validation",
                "start-date": "2024-06-01",
                "end-date": "2024-06-30",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 1003:
        cycles = [
            {
                "id": 2007,
                "name": "Feature Cycle 1",
                "parent-id": 1003,
                "description": "First feature cycle",
                "start-date": "2024-07-01",
                "end-date": "2024-07-31",
                "has-attachments": "Y"
            },
            {
                "id": 2008,
                "name": "Feature Cycle 2",
                "parent-id": 1003,
                "description": "Second feature cycle",
                "start-date": "2024-08-01",
                "end-date": "2024-08-31",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 1004:
        cycles = [
            {
                "id": 2009,
                "name": "Performance Cycle 1",
                "parent-id": 1004,
                "description": "First performance cycle",
                "start-date": "2024-10-01",
                "end-date": "2024-10-31",
                "has-attachments": "Y"
            },
            {
                "id": 2010,
                "name": "Performance Cycle 2",
                "parent-id": 1004,
                "description": "Second performance cycle",
                "start-date": "2024-11-01",
                "end-date": "2024-11-30",
                "has-attachments": "Y"
            }
        ]
    elif parent_id == 1005:
        cycles = [
            {
                "id": 2011,
                "name": "Platform Cycle 1",
                "parent-id": 1005,
                "description": "First platform cycle",
                "start-date": "2025-01-01",
                "end-date": "2025-01-31",
                "has-attachments": "Y"
            },
            {
                "id": 2012,
                "name": "Platform Cycle 2",
                "parent-id": 1005,
                "description": "Second platform cycle",
                "start-date": "2025-02-01",
                "end-date": "2025-02-28",
                "has-attachments": "Y"
            }
        ]
    else:
        cycles = []
    
    data = make_alm_response("release-cycle", cycles)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# TEST SETS (TestLab)
# --------------------------------------------------------------------

@app.get(BASE_PREFIX + "/test-sets")
def get_test_sets(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get test sets for a release cycle.
    
    Query parameter format: {parent-id[2001]} to get test sets for cycle 2001
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse parent_id from query parameter
    parent_id = None
    if query:
        import re
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = int(match.group(1))
    
    # Return test sets based on parent cycle
    if parent_id == 2001:
        test_sets = [
            {
                "id": 3001,
                "name": "Login Tests",
                "parent-id": 2001,
                "description": "Test set for login functionality",
                "status": "Open",
                "subtype-id": "hp.qc.test-set.default"
            },
            {
                "id": 3002,
                "name": "User Management Tests",
                "parent-id": 2001,
                "description": "CRUD operations for users",
                "status": "Passed",
                "subtype-id": "hp.qc.test-set.default"
            }
        ]
    elif parent_id == 2002:
        test_sets = [
            {
                "id": 3003,
                "name": "API Tests",
                "parent-id": 2002,
                "description": "REST API validation",
                "status": "Open",
                "subtype-id": "hp.qc.test-set.default"
            },
            {
                "id": 3004,
                "name": "UI Tests",
                "parent-id": 2002,
                "description": "UI component tests",
                "status": "Failed",
                "subtype-id": "hp.qc.test-set.default"
            }
        ]
    elif parent_id == 2003:
        test_sets = [
            {
                "id": 3005,
                "name": "Full Regression Suite",
                "parent-id": 2003,
                "description": "Complete regression test suite",
                "status": "Open",
                "subtype-id": "hp.qc.test-set.default"
            }
        ]
    elif parent_id == 2004:
        test_sets = [
            {
                "id": 3006,
                "name": "Alpha Smoke Tests",
                "parent-id": 2004,
                "description": "Quick smoke tests for alpha",
                "status": "Passed",
                "subtype-id": "hp.qc.test-set.default"
            }
        ]
    elif parent_id == 2005:
        test_sets = [
            {
                "id": 3007,
                "name": "Beta User Tests",
                "parent-id": 2005,
                "description": "End user testing",
                "status": "Open",
                "subtype-id": "hp.qc.test-set.default"
            }
        ]
    elif parent_id == 2006:
        test_sets = [
            {
                "id": 3008,
                "name": "Beta Regression",
                "parent-id": 2006,
                "description": "Regression for beta",
                "status": "Failed",
                "subtype-id": "hp.qc.test-set.default"
            }
        ]
    else:
        test_sets = []
    
    data = make_alm_response("test-set", test_sets)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# TEST RUNS (TestLab)
# --------------------------------------------------------------------

@app.get(BASE_PREFIX + "/runs")
def get_test_runs(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Get test runs for a test set.
    
    Query parameter format: {testcycl-id[3001]} to get runs for test set 3001
    
    Note: ALM uses 'testcycl-id' field to link runs to test sets.
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse testcycl-id from query parameter
    testcycl_id = None
    if query:
        import re
        match = re.search(r'testcycl-id\[(\d+)\]', query)
        if match:
            testcycl_id = int(match.group(1))
    
    # Return test runs based on test set (2-3 runs per test set)
    # Generate 2-4 runs per test set
    if testcycl_id:
        run_base = testcycl_id * 10
        runs = [
            {
                "id": run_base + 1,
                "name": f"Run 1 of Test Set {testcycl_id}",
                "testcycl-id": testcycl_id,
                "test-id": 1,
                "status": "Passed",
                "execution-date": "2024-01-05",
                "execution-time": "10:30:00",
                "owner": "tester1",
                "comments": "All test steps passed",
                "has-attachments": "Y"
            },
            {
                "id": run_base + 2,
                "name": f"Run 2 of Test Set {testcycl_id}",
                "testcycl-id": testcycl_id,
                "test-id": 2,
                "status": "Failed",
                "execution-date": "2024-01-06",
                "execution-time": "11:15:00",
                "owner": "tester1",
                "comments": "Step 3 failed - timeout issue",
                "has-attachments": "Y"
            },
            {
                "id": run_base + 3,
                "name": f"Run 3 of Test Set {testcycl_id}",
                "testcycl-id": testcycl_id,
                "test-id": 3,
                "status": "Passed",
                "execution-date": "2024-01-07",
                "execution-time": "09:45:00",
                "owner": "tester2",
                "comments": "Test executed successfully",
                "has-attachments": "N"
            }
        ]
    else:
        runs = []
    
    data = make_alm_response("run", runs)
    return JSONResponse(content=data)


# --------------------------------------------------------------------
# DEFECTS
# --------------------------------------------------------------------

@app.get(BASE_PREFIX + "/defects")
def get_defects(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """
    Mocked defect list with pagination support.
    
    Returns defects with various statuses, priorities, and fields.
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Generate 120 mock defects for pagination testing
    all_defects = []
    
    for i in range(1, 121):
        status_options = ["New", "Open", "Fixed", "Closed", "Rejected", "Reopen"]
        severity_options = ["1-Critical", "2-High", "3-Medium", "4-Low", "5-Urgent"]
        priority_options = ["1-High", "2-Medium", "3-Low"]
        detected_by_options = ["john.doe", "jane.smith", "alice.johnson", "bob.wilson"]
        owner_options = ["", "john.doe", "jane.smith", "dev.team"]
        
        defect = {
            "id": 1000 + i,
            "name": f"Defect {i}: {['Login issue', 'UI glitch', 'Performance problem', 'Data validation error', 'API timeout'][i % 5]}",
            "description": f"<html><body>Description for defect {i}. This is a detailed explanation of the issue found during testing.</body></html>",
            "status": status_options[i % len(status_options)],
            "severity": severity_options[i % len(severity_options)],
            "priority": priority_options[i % len(priority_options)],
            "detected-by": detected_by_options[i % len(detected_by_options)],
            "owner": owner_options[i % len(owner_options)],
            "creation-time": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "detected-in-rcyc": 2001 + (i % 6),
            "target-rcyc": 2001 + (i % 6),
            "subject": f"Defects/{['Login', 'UI', 'API', 'Database', 'Performance'][i % 5]}",
            "reproducible": "Y" if i % 3 == 0 else "N",
            "has-attachments": "Y" if i % 4 == 0 else "N"
        }
        all_defects.append(defect)
    
    # Handle pagination
    from fastapi import Query as FastAPIQuery
    start_index = request.query_params.get("start-index", "1")
    page_size = request.query_params.get("page-size", "100")
    
    try:
        start_idx = int(start_index) - 1  # Convert to 0-based
        page_sz = int(page_size)
    except:
        start_idx = 0
        page_sz = 100
    
    # Slice defects for pagination
    paginated_defects = all_defects[start_idx:start_idx + page_sz]
    
    response_data = {
        "entities": [make_entity("defect", d) for d in paginated_defects],
        "TotalResults": len(all_defects)
    }
    
    return JSONResponse(content=response_data)


@app.get(BASE_PREFIX + "/defects/{defect_id}")
def get_defect_by_id(
    domain: str,
    project: str,
    defect_id: str,
    request: Request
):
    """
    Get detailed information for a specific defect.
    
    Requires: All 4 cookies
    """
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    defect_num = int(defect_id) if defect_id.isdigit() else 1001
    
    # Generate detailed defect data
    defect = {
        "id": defect_num,
        "name": f"Defect {defect_num - 1000}: Test defect",
        "description": f"<html><body><h3>Detailed Description</h3><p>This is a comprehensive description for defect {defect_id}.</p><ul><li>Steps to reproduce</li><li>Expected behavior</li><li>Actual behavior</li></ul></body></html>",
        "status": ["New", "Open", "Fixed", "Closed"][defect_num % 4],
        "severity": ["1-Critical", "2-High", "3-Medium", "4-Low"][defect_num % 4],
        "priority": ["1-High", "2-Medium", "3-Low"][defect_num % 3],
        "detected-by": "john.doe",
        "owner": "jane.smith",
        "creation-time": "2024-01-15 10:30:00",
        "last-modified": "2024-01-20 14:45:00",
        "detected-in-rcyc": 2001,
        "target-rcyc": 2002,
        "subject": "Defects/Login",
        "reproducible": "Y",
        "has-attachments": "Y" if defect_num % 4 == 0 else "N",
        "dev-comments": "Investigated the issue. Root cause identified.",
        "environment": "Windows 10, Chrome 120",
        "steps": "1. Navigate to login page\n2. Enter credentials\n3. Click submit\n4. Observe error"
    }
    
    return JSONResponse(content=make_entity("defect", defect))


# --------------------------------------------------------------------
# Root / health
# --------------------------------------------------------------------


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": (
            "Mock ALM server running with ALM-style entities/Fields/TotalResults; "
            "field names follow HP/Micro Focus REST examples per entity type."
        ),
    }
