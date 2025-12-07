"""
Simplified Mock ALM Server for Testing
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import re
import logging
from pathlib import Path

# Configure logging
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'mock-alm.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info('Mock ALM service starting...')

app = FastAPI(title="Mock ALM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_PREFIX = "/qcbin/rest/domains/{domain}/projects/{project}"

def set_alm_cookies(response):
    """Set all required ALM authentication cookies"""
    response.set_cookie("LWSSO_COOKIE_KEY", "mock-lwsso-token")
    response.set_cookie("QCSession", "mock-session-id")
    response.set_cookie("ALM_USER", "testuser")
    response.set_cookie("XSRF-TOKEN", "mock-xsrf-token")
    return response

def validate_cookies(request: Request) -> bool:
    """Check if request has required cookies"""
    cookie = request.headers.get("cookie", "")
    # For mock, just check if ANY auth cookie is present
    required = ["LWSSO_COOKIE_KEY", "QCSession", "ALM_USER", "XSRF-TOKEN"]
    return any(req in cookie for req in required)

def make_entity(entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert simple dict to ALM entity format"""
    fields = []
    for key, value in data.items():
        fields.append({
            "Name": key,
            "values": [{"value": str(value)}]
        })
    return {
        "Type": entity_type,
        "Fields": fields
    }

def make_list_response(entity_type: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create ALM-style list response"""
    return {
        "entities": [make_entity(entity_type, e) for e in entities],
        "TotalResults": len(entities)
    }

# Authentication endpoints
@app.post("/qcbin/authentication-point/authenticate")
@app.post("/authentication-point/authenticate")
def authenticate(request: Request):
    """Mock authentication endpoint - Step 1: Set LWSSO cookie only"""
    logger.info("Authentication request received")
    resp = PlainTextResponse("OK")
    resp.set_cookie("LWSSO_COOKIE_KEY", "mock-lwsso-token", path="/")
    logger.info("Authentication successful")
    return resp

@app.post("/qcbin/rest/site-session")
@app.post("/rest/site-session")
def site_session(request: Request):
    """Mock site session endpoint - Step 2: Set QC session cookies"""
    logger.info("Site session request received")
    resp = PlainTextResponse("SITE-SESSION-OK")
    resp.set_cookie("QCSession", "mock-session-id", path="/")
    resp.set_cookie("ALM_USER", "testuser", path="/")
    resp.set_cookie("XSRF-TOKEN", "mock-xsrf-token", path="/")
    logger.info("Site session created")
    return resp

@app.get("/qcbin/rest/domains")
@app.get("/rest/domains")
def get_domains(request: Request):
    """Return mock domains in ALM format"""
    logger.info("Get domains request received")
    if not validate_cookies(request):
        logger.warning("Domains request without valid cookies")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return domains in proper ALM entities format
    from alm_format_utils import simple_to_alm
    
    domains = [
        {"id": "DEFAULT", "name": "DEFAULT"},
        {"id": "TESTDOMAIN", "name": "TESTDOMAIN"}
    ]
    
    logger.info(f"Returning {len(domains)} domains")
    return JSONResponse(content=simple_to_alm(domains, entity_type="domain"))

@app.get("/qcbin/rest/domains/{domain}/projects")
@app.get("/rest/domains/{domain}/projects")
def get_projects(domain: str, request: Request):
    """Return mock projects in ALM format"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return projects in proper ALM entities format
    from alm_format_utils import simple_to_alm
    
    projects = [
        {"id": "1", "name": "Test Project 1"},
        {"id": "2", "name": "Test Project 2"}
    ]
    
    return JSONResponse(content=simple_to_alm(projects, entity_type="project"))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/test-folders")
@app.get("/rest/domains/{domain}/projects/{project}/test-folders")
def get_test_folders(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """Return mock test folders in ALM entity format, filtered by parent-id"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # All available folders - 3 levels deep
    all_folders = [
        # Level 0 - Root folders
        {"id": "1", "name": "Subject", "parent-id": "0"},
        {"id": "2", "name": "Regression Tests", "parent-id": "0"},
        {"id": "3", "name": "Smoke Tests", "parent-id": "0"},
        
        # Level 1 - Under Subject (id=1)
        {"id": "4", "name": "Integration Tests", "parent-id": "1"},
        {"id": "5", "name": "Unit Tests", "parent-id": "1"},
        {"id": "6", "name": "System Tests", "parent-id": "1"},
        
        # Level 1 - Under Regression Tests (id=2)
        {"id": "7", "name": "UI Tests", "parent-id": "2"},
        {"id": "8", "name": "API Tests", "parent-id": "2"},
        {"id": "9", "name": "Performance Tests", "parent-id": "2"},
        
        # Level 1 - Under Smoke Tests (id=3)
        {"id": "10", "name": "Login Tests", "parent-id": "3"},
        {"id": "11", "name": "Navigation Tests", "parent-id": "3"},
        {"id": "12", "name": "Critical Path Tests", "parent-id": "3"},
        
        # Level 2 - Under Integration Tests (id=4)
        {"id": "13", "name": "Database Integration", "parent-id": "4"},
        {"id": "14", "name": "API Integration", "parent-id": "4"},
        
        # Level 2 - Under UI Tests (id=7)
        {"id": "15", "name": "Forms Testing", "parent-id": "7"},
        {"id": "16", "name": "Navigation Testing", "parent-id": "7"},
    ]
    
    # Parse query parameter to filter by parent-id
    # Query format: {parent-id[0]} or {parent-id[1]}
    parent_id = "0"  # default to root
    if query:
        import re
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = match.group(1)
    
    # Filter folders by parent-id
    folders = [f for f in all_folders if f["parent-id"] == parent_id]
    
    return JSONResponse(content=make_list_response("test-folder", folders))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/tests")
@app.get("/rest/domains/{domain}/projects/{project}/tests")
def get_tests(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """Return mock tests in ALM entity format, filtered by parent-id"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # All available tests distributed across folders
    all_tests = [
        # Tests under Integration Tests (id=4)
        {"id": "101", "name": "Database Connection Test", "parent-id": "4", "status": "Passed", "owner": "admin"},
        {"id": "102", "name": "Service Integration Test", "parent-id": "4", "status": "Passed", "owner": "admin"},
        {"id": "103", "name": "Third Party API Test", "parent-id": "4", "status": "Ready", "owner": "testuser"},
        # Tests under Unit Tests (id=5)
        {"id": "104", "name": "Calculator Unit Test", "parent-id": "5", "status": "Passed", "owner": "testuser"},
        {"id": "105", "name": "String Utils Test", "parent-id": "5", "status": "Passed", "owner": "testuser"},
        {"id": "106", "name": "Date Utils Test", "parent-id": "5", "status": "Ready", "owner": "admin"},
        # Tests under System Tests (id=6)
        {"id": "107", "name": "End to End Test", "parent-id": "6", "status": "Passed", "owner": "admin"},
        {"id": "108", "name": "System Load Test", "parent-id": "6", "status": "Ready", "owner": "testuser"},
        # Tests under UI Tests (id=7)
        {"id": "109", "name": "Button Click Test", "parent-id": "7", "status": "Passed", "owner": "testuser"},
        {"id": "110", "name": "Form Validation Test", "parent-id": "7", "status": "Ready", "owner": "admin"},
        {"id": "111", "name": "Modal Dialog Test", "parent-id": "7", "status": "Failed", "owner": "testuser"},
        # Tests under API Tests (id=8)
        {"id": "112", "name": "REST API Test", "parent-id": "8", "status": "Passed", "owner": "testuser"},
        {"id": "113", "name": "GraphQL Test", "parent-id": "8", "status": "Ready", "owner": "testuser"},
        {"id": "114", "name": "WebSocket Test", "parent-id": "8", "status": "Ready", "owner": "admin"},
        # Tests under Performance Tests (id=9)
        {"id": "115", "name": "Load Test", "parent-id": "9", "status": "Passed", "owner": "admin"},
        {"id": "116", "name": "Stress Test", "parent-id": "9", "status": "Ready", "owner": "testuser"},
        # Tests under Login Tests (id=10)
        {"id": "117", "name": "User Login Test", "parent-id": "10", "status": "Passed", "owner": "admin"},
        {"id": "118", "name": "Admin Login Test", "parent-id": "10", "status": "Failed", "owner": "admin"},
        {"id": "119", "name": "SSO Login Test", "parent-id": "10", "status": "Ready", "owner": "testuser"},
        # Tests under Navigation Tests (id=11)
        {"id": "120", "name": "Menu Navigation Test", "parent-id": "11", "status": "Passed", "owner": "testuser"},
        {"id": "121", "name": "Breadcrumb Test", "parent-id": "11", "status": "Ready", "owner": "testuser"},
        # Tests under Critical Path Tests (id=12)
        {"id": "122", "name": "User Registration Test", "parent-id": "12", "status": "Passed", "owner": "admin"},
        {"id": "123", "name": "Checkout Process Test", "parent-id": "12", "status": "Passed", "owner": "testuser"},
        {"id": "124", "name": "Payment Gateway Test", "parent-id": "12", "status": "Ready", "owner": "admin"},
        # Tests under Database Integration (id=13)
        {"id": "125", "name": "CRUD Operations Test", "parent-id": "13", "status": "Passed", "owner": "testuser"},
        {"id": "126", "name": "Transaction Test", "parent-id": "13", "status": "Ready", "owner": "admin"},
        # Tests under API Integration (id=14)
        {"id": "127", "name": "External API Test", "parent-id": "14", "status": "Passed", "owner": "testuser"},
        {"id": "128", "name": "Microservices Test", "parent-id": "14", "status": "Ready", "owner": "admin"},
        # Tests under Forms Testing (id=15)
        {"id": "129", "name": "Input Validation Test", "parent-id": "15", "status": "Passed", "owner": "testuser"},
        {"id": "130", "name": "Form Submit Test", "parent-id": "15", "status": "Ready", "owner": "admin"},
        # Tests under Navigation Testing (id=16)
        {"id": "131", "name": "Link Navigation Test", "parent-id": "16", "status": "Passed", "owner": "testuser"},
        {"id": "132", "name": "Back Button Test", "parent-id": "16", "status": "Ready", "owner": "admin"}
    ]
    
    # Parse query parameter to filter by parent-id
    if query:
        import re
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = match.group(1)
            tests = [t for t in all_tests if t["parent-id"] == parent_id]
            return JSONResponse(content=make_list_response("test", tests))
    
    # Return all tests if no filter
    return JSONResponse(content=make_list_response("test", all_tests))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/tests/{test_id}")
@app.get("/rest/domains/{domain}/projects/{project}/tests/{test_id}")
def get_test_details(
    domain: str,
    project: str,
    test_id: str,
    request: Request
):
    """Return mock test details"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    test = {
        "id": test_id,
        "name": f"Test {test_id}",
        "description": f"Description for test {test_id}",
        "status": "Ready",
        "owner": "testuser"
    }
    return JSONResponse(content=make_entity("test", test))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/defects")
@app.get("/rest/domains/{domain}/projects/{project}/defects")
def get_defects(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """Return mock defects in ALM entity format with query filtering support"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    all_defects = [
        {
            "id": "1",
            "name": "Login button not working",
            "status": "Open",
            "severity": "2-High",
            "priority": "High",
            "detected-by": "tester1",
            "assigned-to": "developer1",
            "owner": "developer1",
            "creation-time": "2024-11-15 10:30:00",
            "last-modified": "2024-11-20 14:45:00",
            "detected-in-rel": "Release 1.0",
            "detected-in-rcyc": "Sprint 1",
            "target-rel": "Release 1.0",
            "target-rcyc": "Sprint 2",
            "has-attachments": "Y",
            "reproducible": "Y",
            "description": "Login button does not respond to clicks",
            "steps-to-reproduce": "1. Navigate to login page\n2. Enter valid credentials\n3. Click login button\n4. Observe no response",
            "expected-result": "User should be logged in and redirected to home page",
            "actual-result": "Button does not respond, no action taken"
        },
        {
            "id": "2",
            "name": "Dashboard crash on load",
            "status": "Fixed",
            "severity": "1-Critical",
            "priority": "Critical",
            "detected-by": "tester2",
            "assigned-to": "developer2",
            "owner": "developer2",
            "creation-time": "2024-11-10 09:15:00",
            "last-modified": "2024-11-25 16:20:00",
            "detected-in-rel": "Release 1.0",
            "detected-in-rcyc": "Sprint 1",
            "target-rel": "Release 1.0",
            "target-rcyc": "Sprint 1",
            "has-attachments": "Y",
            "reproducible": "Y",
            "description": "Application crashes when loading dashboard",
            "steps-to-reproduce": "1. Login with admin account\n2. Navigate to dashboard\n3. Wait for data to load\n4. Application crashes",
            "expected-result": "Dashboard loads successfully with all data",
            "actual-result": "Application crashes with out of memory error",
            "resolution": "Fixed memory leak in dashboard data loading component"
        },
        {
            "id": "3",
            "name": "Data export incomplete",
            "status": "Open",
            "severity": "3-Medium",
            "priority": "Medium",
            "detected-by": "tester1",
            "assigned-to": "developer3",
            "owner": "developer3",
            "creation-time": "2024-11-18 13:00:00",
            "last-modified": "2024-11-22 11:30:00",
            "detected-in-rel": "Release 2.0",
            "detected-in-rcyc": "Sprint 3",
            "target-rel": "Release 2.0",
            "target-rcyc": "Sprint 4",
            "has-attachments": "Y",
            "reproducible": "Y",
            "description": "Export feature missing some data fields",
            "steps-to-reproduce": "1. Click export button\n2. Select CSV format\n3. Export data\n4. Open CSV file",
            "expected-result": "All data fields should be present in CSV export",
            "actual-result": "Missing email, phone number, and department fields"
        }
    ]
    
    # Filter by ID if query contains id filter (e.g., {id[1]})
    defects = all_defects
    if query:
        import re
        id_match = re.search(r'id\[(\d+)\]', query)
        if id_match:
            defect_id = id_match.group(1)
            defects = [d for d in all_defects if d["id"] == defect_id]
    
    return JSONResponse(content=make_list_response("defect", defects))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/defects/{defect_id}")
@app.get("/rest/domains/{domain}/projects/{project}/defects/{defect_id}")
def get_defect_by_id(
    domain: str,
    project: str,
    defect_id: str,
    request: Request
):
    """Return a single defect by ID"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    all_defects = [
        {
            "id": "1",
            "name": "Login button not working",
            "status": "Open",
            "severity": "2-High",
            "priority": "High",
            "detected-by": "tester1",
            "assigned-to": "developer1",
            "owner": "developer1",
            "creation-time": "2024-11-15 10:30:00",
            "last-modified": "2024-11-20 14:45:00",
            "detected-in-rel": "Release 1.0",
            "detected-in-rcyc": "Sprint 1",
            "target-rel": "Release 1.0",
            "target-rcyc": "Sprint 2",
            "has-attachments": "Y",
            "reproducible": "Y",
            "description": "Login button does not respond to clicks",
            "steps-to-reproduce": "1. Navigate to login page\n2. Enter valid credentials\n3. Click login button\n4. Observe no response",
            "expected-result": "User should be logged in and redirected to home page",
            "actual-result": "Button does not respond, no action taken"
        },
        {
            "id": "2",
            "name": "Dashboard crash on load",
            "status": "Fixed",
            "severity": "1-Critical",
            "priority": "Critical",
            "detected-by": "tester2",
            "assigned-to": "developer2",
            "owner": "developer2",
            "creation-time": "2024-11-10 09:15:00",
            "last-modified": "2024-11-25 16:20:00",
            "detected-in-rel": "Release 1.0",
            "detected-in-rcyc": "Sprint 1",
            "target-rel": "Release 1.0",
            "target-rcyc": "Sprint 1",
            "has-attachments": "Y",
            "reproducible": "Y",
            "description": "Application crashes when loading dashboard",
            "steps-to-reproduce": "1. Login with admin account\n2. Navigate to dashboard\n3. Wait for data to load\n4. Application crashes",
            "expected-result": "Dashboard loads successfully with all data",
            "actual-result": "Application crashes with out of memory error",
            "resolution": "Fixed memory leak in dashboard data loading component"
        },
        {
            "id": "3",
            "name": "Data export incomplete",
            "status": "Open",
            "severity": "3-Medium",
            "priority": "Medium",
            "detected-by": "tester1",
            "assigned-to": "developer3",
            "owner": "developer3",
            "creation-time": "2024-11-18 13:00:00",
            "last-modified": "2024-11-22 11:30:00",
            "detected-in-rel": "Release 2.0",
            "detected-in-rcyc": "Sprint 3",
            "target-rel": "Release 2.0",
            "target-rcyc": "Sprint 4",
            "has-attachments": "Y",
            "reproducible": "Y",
            "description": "Export feature missing some data fields",
            "steps-to-reproduce": "1. Click export button\n2. Select CSV format\n3. Export data\n4. Open CSV file",
            "expected-result": "All data fields should be present in CSV export",
            "actual-result": "Missing email, phone number, and department fields"
        }
    ]
    
    defect = next((d for d in all_defects if d["id"] == defect_id), None)
    if not defect:
        raise HTTPException(status_code=404, detail=f"Defect {defect_id} not found")
    
    return JSONResponse(content=make_entity("defect", defect))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/tests/{test_id}/design-steps")
@app.get("/rest/domains/{domain}/projects/{project}/tests/{test_id}/design-steps")
@app.get("/qcbin/rest/domains/{domain}/projects/{project}/design-steps")
@app.get("/rest/domains/{domain}/projects/{project}/design-steps")
def get_design_steps(
    domain: str,
    project: str,
    request: Request,
    test_id: Optional[str] = None,
    query: Optional[str] = Query(None)
):
    """Return mock design steps for a test"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get parent_id from path parameter or query parameter
    parent_id = test_id
    if not parent_id and query:
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = match.group(1)
    
    # Return design steps for any test (3-5 steps with details)
    steps = [
        {
            "id": f"{parent_id}01" if parent_id else "1",
            "name": "Test Preconditions",
            "parent-id": parent_id or "101",
            "step-order": "1",
            "description": "1. Navigate to the application login page\n2. Ensure test data is prepared\n3. Clear browser cache and cookies",
            "expected": "Login page is displayed correctly with username and password fields"
        },
        {
            "id": f"{parent_id}02" if parent_id else "2",
            "name": "Execute Test Steps",
            "parent-id": parent_id or "101",
            "step-order": "2",
            "description": "1. Enter valid username in the username field\n2. Enter valid password in the password field\n3. Click the Login button",
            "expected": "User is successfully authenticated and redirected to the home page"
        },
        {
            "id": f"{parent_id}03" if parent_id else "3",
            "name": "Verify Results",
            "parent-id": parent_id or "101",
            "step-order": "3",
            "description": "1. Check that the home page loads completely\n2. Verify user name is displayed in the header\n3. Confirm all navigation menu items are visible",
            "expected": "Home page displays correctly with all expected elements"
        },
        {
            "id": f"{parent_id}04" if parent_id else "4",
            "name": "Verify Additional Features",
            "parent-id": parent_id or "101",
            "step-order": "4",
            "description": "1. Click on each main navigation item\n2. Verify page transitions work smoothly\n3. Check for any console errors",
            "expected": "All navigation works without errors and pages load correctly"
        },
        {
            "id": f"{parent_id}05" if parent_id else "5",
            "name": "Cleanup",
            "parent-id": parent_id or "101",
            "step-order": "5",
            "description": "1. Logout from the application\n2. Verify session is terminated\n3. Close the browser",
            "expected": "User is logged out successfully and redirected to login page"
        }
    ]
    
    return JSONResponse(content=make_list_response("design-step", steps))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/releases")
@app.get("/rest/domains/{domain}/projects/{project}/releases")
def get_releases(
    domain: str,
    project: str,
    request: Request
):
    """Return mock releases in ALM entity format"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    releases = [
        {"id": "1001", "name": "Release 1.0", "start-date": "2024-01-01", "end-date": "2024-03-31"},
        {"id": "1002", "name": "Release 2.0", "start-date": "2024-04-01", "end-date": "2024-06-30"},
        {"id": "1003", "name": "Release 3.0", "start-date": "2024-07-01", "end-date": "2024-09-30"}
    ]
    return JSONResponse(content=make_list_response("release", releases))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/release-cycles")
@app.get("/rest/domains/{domain}/projects/{project}/release-cycles")
def get_release_cycles(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """Return mock release cycles in ALM entity format"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse parent-id (release ID) from query
    parent_id = None
    if query:
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = match.group(1)
    
    # All cycles across all releases
    all_cycles = [
        # Release 1.0 cycles
        {"id": "2001", "name": "Sprint 1", "parent-id": "1001", "start-date": "2024-01-01", "end-date": "2024-01-31"},
        {"id": "2002", "name": "Sprint 2", "parent-id": "1001", "start-date": "2024-02-01", "end-date": "2024-02-29"},
        {"id": "2003", "name": "Sprint 3", "parent-id": "1001", "start-date": "2024-03-01", "end-date": "2024-03-31"},
        # Release 2.0 cycles
        {"id": "2004", "name": "Sprint 4", "parent-id": "1002", "start-date": "2024-04-01", "end-date": "2024-04-30"},
        {"id": "2005", "name": "Sprint 5", "parent-id": "1002", "start-date": "2024-05-01", "end-date": "2024-05-31"},
        {"id": "2006", "name": "Sprint 6", "parent-id": "1002", "start-date": "2024-06-01", "end-date": "2024-06-30"},
        # Release 3.0 cycles
        {"id": "2007", "name": "Sprint 7", "parent-id": "1003", "start-date": "2024-07-01", "end-date": "2024-07-31"},
        {"id": "2008", "name": "Sprint 8", "parent-id": "1003", "start-date": "2024-08-01", "end-date": "2024-08-31"},
    ]
    
    # Filter by parent-id if provided
    if parent_id:
        cycles = [c for c in all_cycles if c["parent-id"] == parent_id]
    else:
        cycles = all_cycles
    
    return JSONResponse(content=make_list_response("cycle", cycles))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/test-sets")
@app.get("/rest/domains/{domain}/projects/{project}/test-sets")
def get_test_sets(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """Return mock test sets in ALM entity format"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse parent-id (cycle ID) from query
    parent_id = None
    if query:
        match = re.search(r'parent-id\[(\d+)\]', query)
        if match:
            parent_id = match.group(1)
    
    # All test sets across all cycles
    all_test_sets = [
        # Sprint 1 test sets
        {"id": "3001", "name": "Regression Test Set", "parent-id": "2001", "status": "Passed"},
        {"id": "3002", "name": "Smoke Test Set", "parent-id": "2001", "status": "Passed"},
        # Sprint 2 test sets
        {"id": "3003", "name": "Integration Test Set", "parent-id": "2002", "status": "Failed"},
        {"id": "3004", "name": "Performance Test Set", "parent-id": "2002", "status": "Passed"},
        # Sprint 3 test sets
        {"id": "3005", "name": "UI Test Set", "parent-id": "2003", "status": "Passed"},
        {"id": "3006", "name": "API Test Set", "parent-id": "2003", "status": "Passed"},
        # Sprint 4 test sets
        {"id": "3007", "name": "Security Test Set", "parent-id": "2004", "status": "Passed"},
        {"id": "3008", "name": "End-to-End Test Set", "parent-id": "2004", "status": "In Progress"},
        # Sprint 5 test sets
        {"id": "3009", "name": "Mobile Test Set", "parent-id": "2005", "status": "Passed"},
        {"id": "3010", "name": "Cross-Browser Test Set", "parent-id": "2005", "status": "Failed"},
        # Sprint 6 test sets
        {"id": "3011", "name": "Accessibility Test Set", "parent-id": "2006", "status": "Passed"},
        # Sprint 7 test sets
        {"id": "3012", "name": "Load Test Set", "parent-id": "2007", "status": "Passed"},
        # Sprint 8 test sets
        {"id": "3013", "name": "Database Test Set", "parent-id": "2008", "status": "Not Started"},
    ]
    
    # Filter by parent-id if provided
    if parent_id:
        test_sets = [ts for ts in all_test_sets if ts["parent-id"] == parent_id]
    else:
        test_sets = all_test_sets
    
    return JSONResponse(content=make_list_response("test-set", test_sets))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/runs")
@app.get("/rest/domains/{domain}/projects/{project}/runs")
def get_test_runs(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """Return mock test runs in ALM entity format"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse test set ID from query (supports both parent-id and testcycl-id)
    parent_id = None
    if query:
        # Try testcycl-id first (used by backend)
        match = re.search(r'testcycl-id\[(\d+)\]', query)
        if match:
            parent_id = match.group(1)
        else:
            # Fallback to parent-id
            match = re.search(r'parent-id\[(\d+)\]', query)
            if match:
                parent_id = match.group(1)
    
    # Generate test runs dynamically based on test set ID
    runs = []
    if parent_id:
        test_set_num = int(parent_id) - 3000  # Convert to 1-13 range
        for i in range(1, 4):  # 3 runs per test set
            run_id = f"{parent_id}{i:02d}"
            statuses = ["Passed", "Failed", "Not Completed", "No Run"]
            runs.append({
                "id": run_id,
                "name": f"Test Run {i}",
                "test-set-id": parent_id,
                "status": statuses[i % len(statuses)],
                "execution-date": f"2024-{(test_set_num % 12) + 1:02d}-{(i * 5):02d}",
                "tester": f"tester{i}"
            })
    
    return JSONResponse(content=make_list_response("run", runs))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/runs/{run_id}")
@app.get("/rest/domains/{domain}/projects/{project}/runs/{run_id}")
def get_run_details(
    domain: str,
    project: str,
    run_id: str,
    request: Request
):
    """Return detailed test run information"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse test set ID from run_id (format: testsetid + 01/02/03)
    test_set_id = run_id[:-2] if len(run_id) > 2 else "3001"
    run_num = int(run_id[-2:]) if len(run_id) > 2 else 1
    
    statuses = ["Passed", "Failed", "Not Completed", "No Run"]
    status = statuses[run_num % len(statuses)]
    
    run_details = {
        "id": run_id,
        "name": f"Test Run {run_num}",
        "test-id": "101",  # Mock test ID
        "test-name": "Sample Test",
        "test-set-id": test_set_id,
        "cycle-id": "2001",  # Mock cycle ID
        "status": status,
        "execution-date": f"2024-11-{10 + run_num:02d}",
        "execution-time": f"14:{run_num * 15:02d}:00",
        "duration": f"{30 + run_num * 10}",
        "tester": f"tester{run_num}",
        "host": "test-machine-01",
        "comments": f"Test execution {status.lower()}. {'All steps completed successfully.' if status == 'Passed' else 'Some issues encountered during execution.' if status == 'Failed' else 'Execution incomplete.'}",
        "actual-duration": f"{25 + run_num * 12}",
        "steps": "5",
        "passed-steps": "5" if status == "Passed" else "3",
        "failed-steps": "0" if status == "Passed" else "2",
        "na-steps": "0" if status != "Not Completed" else "2"
    }
    
    return JSONResponse(content=make_entity("run", run_details))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/runs/{run_id}/run-steps")
@app.get("/rest/domains/{domain}/projects/{project}/runs/{run_id}/run-steps")
def get_run_steps(
    domain: str,
    project: str,
    run_id: str,
    request: Request
):
    """Return mock run steps for a test run"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Generate 5 run steps with status
    run_num = int(run_id[-2:]) if len(run_id) > 2 else 1
    statuses = ["Passed", "Failed", "Not Completed", "No Run"]
    run_status = statuses[run_num % len(statuses)]
    
    steps = []
    for i in range(1, 6):
        step_status = "Passed"
        if run_status == "Failed" and i > 3:
            step_status = "Failed"
        elif run_status == "Not Completed" and i > 3:
            step_status = "Not Completed"
        
        steps.append({
            "id": f"{run_id}{i:02d}",
            "name": f"Step {i}",
            "parent-id": run_id,
            "step-order": str(i),
            "description": f"Execute test step {i}",
            "expected": f"Expected result for step {i}",
            "actual": f"Actual result for step {i}" if step_status == "Passed" else f"Different result in step {i}",
            "status": step_status
        })
    
    return JSONResponse(content=make_list_response("run-step", steps))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/attachments")
@app.get("/rest/domains/{domain}/projects/{project}/attachments")
def get_attachments(
    domain: str,
    project: str,
    request: Request,
    query: Optional[str] = Query(None)
):
    """Return mock attachments in ALM entity format"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # All mock attachments - distributed across folders and tests
    attachments = [
        # Folder attachments (levels 0-2)
        {"id": "1", "name": "requirements.pdf", "file-size": "45678", "parent-type": "test-folder", "parent-id": "1"},
        {"id": "2", "name": "test_plan.docx", "file-size": "23456", "parent-type": "test-folder", "parent-id": "2"},
        {"id": "3", "name": "smoke_test_checklist.xlsx", "file-size": "12345", "parent-type": "test-folder", "parent-id": "3"},
        {"id": "4", "name": "integration_diagram.png", "file-size": "67890", "parent-type": "test-folder", "parent-id": "4"},
        {"id": "5", "name": "unit_test_guidelines.pdf", "file-size": "34567", "parent-type": "test-folder", "parent-id": "5"},
        {"id": "6", "name": "system_architecture.png", "file-size": "78901", "parent-type": "test-folder", "parent-id": "6"},
        {"id": "7", "name": "ui_mockup.png", "file-size": "56789", "parent-type": "test-folder", "parent-id": "7"},
        {"id": "8", "name": "api_documentation.pdf", "file-size": "89012", "parent-type": "test-folder", "parent-id": "8"},
        {"id": "9", "name": "performance_baseline.xlsx", "file-size": "23456", "parent-type": "test-folder", "parent-id": "9"},
        {"id": "10", "name": "login_flow.png", "file-size": "34567", "parent-type": "test-folder", "parent-id": "10"},
        {"id": "11", "name": "navigation_map.png", "file-size": "45678", "parent-type": "test-folder", "parent-id": "11"},
        {"id": "12", "name": "critical_scenarios.docx", "file-size": "23456", "parent-type": "test-folder", "parent-id": "12"},
        {"id": "13", "name": "db_schema.png", "file-size": "56789", "parent-type": "test-folder", "parent-id": "13"},
        {"id": "14", "name": "api_endpoints.xlsx", "file-size": "12345", "parent-type": "test-folder", "parent-id": "14"},
        {"id": "15", "name": "form_examples.png", "file-size": "34567", "parent-type": "test-folder", "parent-id": "15"},
        {"id": "16", "name": "navigation_spec.pdf", "file-size": "45678", "parent-type": "test-folder", "parent-id": "16"},
        
        # Test attachments (2 per test for variety)
        {"id": "101", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "101"},
        {"id": "102", "name": "test_data.csv", "file-size": "5678", "parent-type": "test", "parent-id": "101"},
        {"id": "103", "name": "error_log.txt", "file-size": "2345", "parent-type": "test", "parent-id": "102"},
        {"id": "104", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "102"},
        {"id": "105", "name": "test_results.xml", "file-size": "3456", "parent-type": "test", "parent-id": "104"},
        {"id": "106", "name": "coverage_report.html", "file-size": "23456", "parent-type": "test", "parent-id": "105"},
        {"id": "107", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "107"},
        {"id": "108", "name": "performance_metrics.csv", "file-size": "4567", "parent-type": "test", "parent-id": "109"},
        {"id": "109", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "110"},
        {"id": "110", "name": "api_response.json", "file-size": "1234", "parent-type": "test", "parent-id": "112"},
        {"id": "111", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "117"},
        {"id": "112", "name": "login_trace.log", "file-size": "5678", "parent-type": "test", "parent-id": "118"},
        {"id": "113", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "120"},
        {"id": "114", "name": "test_evidence.pdf", "file-size": "34567", "parent-type": "test", "parent-id": "122"},
        {"id": "115", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "125"},
        {"id": "116", "name": "db_queries.sql", "file-size": "2345", "parent-type": "test", "parent-id": "126"},
        {"id": "117", "name": "screenshot.png", "file-size": "12345", "parent-type": "test", "parent-id": "129"},
        
        # Defect attachments
        {"id": "201", "name": "login_error_screenshot.png", "file-size": "23456", "parent-type": "defect", "parent-id": "1"},
        {"id": "202", "name": "browser_console_log.txt", "file-size": "5678", "parent-type": "defect", "parent-id": "1"},
        {"id": "203", "name": "network_trace.har", "file-size": "12345", "parent-type": "defect", "parent-id": "1"},
        {"id": "204", "name": "crash_dump.log", "file-size": "67890", "parent-type": "defect", "parent-id": "2"},
        {"id": "205", "name": "memory_profile.png", "file-size": "45678", "parent-type": "defect", "parent-id": "2"},
        {"id": "206", "name": "stack_trace.txt", "file-size": "8901", "parent-type": "defect", "parent-id": "2"},
        {"id": "207", "name": "exported_data_sample.csv", "file-size": "12345", "parent-type": "defect", "parent-id": "3"},
        {"id": "208", "name": "expected_vs_actual.xlsx", "file-size": "23456", "parent-type": "defect", "parent-id": "3"},
        {"id": "209", "name": "export_settings.json", "file-size": "3456", "parent-type": "defect", "parent-id": "3"},
        
        # Run attachments (2-3 per run sample)
        {"id": "301", "name": "execution_screenshot.png", "file-size": "23456", "parent-type": "run", "parent-id": "300101"},
        {"id": "302", "name": "test_log.txt", "file-size": "5678", "parent-type": "run", "parent-id": "300101"},
        {"id": "303", "name": "execution_video.mp4", "file-size": "456789", "parent-type": "run", "parent-id": "300201"},
        {"id": "304", "name": "error_screenshot.png", "file-size": "34567", "parent-type": "run", "parent-id": "300202"},
        {"id": "305", "name": "debug_log.txt", "file-size": "12345", "parent-type": "run", "parent-id": "300301"}
    ]
    
    # Filter by query if provided
    if query:
        # Parse parent-type and parent-id from query
        parent_type_match = re.search(r'parent-type\[([^\]]+)\]', query)
        parent_id_match = re.search(r'parent-id\[(\d+)\]', query)
        
        if parent_type_match and parent_id_match:
            parent_type = parent_type_match.group(1)
            parent_id = parent_id_match.group(1)
            attachments = [a for a in attachments 
                          if a["parent-type"] == parent_type and a["parent-id"] == parent_id]
    
    return JSONResponse(content=make_list_response("attachment", attachments))

@app.get("/qcbin/rest/domains/{domain}/projects/{project}/attachments/{attachment_id}")
@app.get("/rest/domains/{domain}/projects/{project}/attachments/{attachment_id}")
def download_attachment(
    domain: str,
    project: str,
    attachment_id: str,
    request: Request
):
    """Download attachment file content"""
    if not validate_cookies(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Return mock binary content (a small red square PNG - 10x10 pixels)
    from fastapi.responses import Response
    # Red 10x10 PNG
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x02\x00\x00\x00\x02PX\xea\x00\x00\x00\x19IDATx\x9cc\xf8\xcf\xc0\xc0\xc0\xf0\x9f\x81\x81\x19\x18\x18\x18\x00\x00\x00\x00\xff\xff\x03\x00\x0c\xd0\x01\x0fG\x0c\x8e\xf4\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=png_content, media_type="image/png")

@app.get("/")
@app.get("/qcbin")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Mock ALM server running"
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Mock ALM Server')
    parser.add_argument('--port', type=int, default=8001, help='Port to run the server on')
    args = parser.parse_args()
    
    logger.info(f'Starting Mock ALM server on port {args.port}')
    uvicorn.run(app, host="0.0.0.0", port=args.port)
