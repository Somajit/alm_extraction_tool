# Test Mock ALM Server
# This script tests the mock ALM server endpoints

import requests
import json

BASE_URL = "http://localhost:8001"

def print_response(title, response):
    """Pretty print API response."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(json.dumps(data, indent=2))
        except:
            print(response.text[:200])
    else:
        print(response.text)
    print()

def test_mock_alm():
    """Test all mock ALM endpoints."""
    
    print("\n" + "="*70)
    print("Testing Mock ALM Server")
    print("="*70)
    
    # Create session to persist cookies
    session = requests.Session()
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    response = session.get(f"{BASE_URL}/")
    print_response("Root Endpoint", response)
    
    # Test 2: Authentication
    print("\n2. Testing authentication...")
    auth_data = "username=admin&password=admin123"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = session.post(
        f"{BASE_URL}/qcbin/authentication-point/authenticate",
        data=auth_data,
        headers=headers
    )
    print_response("Authentication", response)
    print(f"Cookies after auth: {session.cookies.get_dict()}")
    
    # Test 3: Site session
    print("\n3. Testing site session creation...")
    response = session.post(f"{BASE_URL}/qcbin/rest/site-session")
    print_response("Site Session", response)
    print(f"Cookies after site-session: {session.cookies.get_dict()}")
    
    # Test 4: Get domains
    print("\n4. Testing get domains...")
    response = session.get(f"{BASE_URL}/qcbin/rest/domains")
    print_response("Domains", response)
    
    # Test 5: Get projects
    print("\n5. Testing get projects...")
    response = session.get(f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects")
    print_response("Projects", response)
    
    # Test 6: Get root test folders
    print("\n6. Testing get root test folders...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/test-folders",
        params={"query": "{parent-id[0]}"}
    )
    print_response("Root Test Folders", response)
    
    # Test 7: Get subfolders
    print("\n7. Testing get subfolders of Subject (id=1)...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/test-folders",
        params={"query": "{parent-id[1]}"}
    )
    print_response("Subfolders", response)
    
    # Test 8: Get tests in Login Module folder (id=5)
    print("\n8. Testing get tests in Login Module folder...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/tests",
        params={"query": "{parent-id[5]}"}
    )
    print_response("Tests", response)
    
    # Test 9: Get test details
    print("\n9. Testing get test details...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/tests/1001"
    )
    print_response("Test Details", response)
    
    # Test 10: Get design steps
    print("\n10. Testing get design steps...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/design-steps",
        params={"query": "{parent-id[1001]}"}
    )
    print_response("Design Steps", response)
    
    # Test 11: Get test attachments
    print("\n11. Testing get test attachments...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/attachments",
        params={"query": "{parent-type[test];parent-id[1001]}"}
    )
    print_response("Test Attachments", response)
    
    # Test 12: Get folder attachments
    print("\n12. Testing get folder attachments...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/attachments",
        params={"query": "{parent-type[test-folder];parent-id[4]}"}
    )
    print_response("Folder Attachments", response)
    
    # Test 13: Get releases
    print("\n13. Testing get releases...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/releases"
    )
    print_response("Releases", response)
    
    # Test 14: Get defects
    print("\n14. Testing get defects...")
    response = session.get(
        f"{BASE_URL}/qcbin/rest/domains/DEFAULT/projects/DEMO_PROJECT/defects"
    )
    print_response("Defects", response)
    
    # Test 15: Logout
    print("\n15. Testing logout...")
    response = session.delete(f"{BASE_URL}/qcbin/rest/site-session")
    print(f"Site session delete status: {response.status_code}")
    
    response = session.get(f"{BASE_URL}/qcbin/authentication-point/logout")
    print(f"Logout status: {response.status_code}")
    
    print("\n" + "="*70)
    print("All tests completed!")
    print("="*70)

if __name__ == "__main__":
    try:
        test_mock_alm()
    except requests.exceptions.ConnectionError:
        print("\n" + "="*70)
        print("ERROR: Could not connect to mock ALM server")
        print("="*70)
        print("\nPlease ensure the mock ALM server is running:")
        print("  cd backend/app")
        print("  python mock_alm.py")
        print("\nOr run: scripts\\start-mock-alm.bat")
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
