"""
Unit tests for authentication API endpoints

Tests the new rationalized API endpoints following the pattern:
Frontend → Backend → ALM → Store MongoDB → Query MongoDB → Return
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def mock_db():
    """Mock MongoDB database"""
    db = MagicMock()
    
    # Mock collections
    db.user_credentials = MagicMock()
    db.domains = MagicMock()
    db.projects = MagicMock()
    db.testplan_folders = MagicMock()
    db.testlab_releases = MagicMock()
    db.defects = MagicMock()
    
    return db


@pytest.fixture
def mock_alm_client(mock_db):
    """Mock ALM client"""
    with patch('app.main.alm_client') as mock:
        # Mock authenticate method
        mock.authenticate = AsyncMock(return_value={
            "success": True,
            "message": "Authenticated successfully",
            "username": "test_user"
        })
        
        # Mock fetch_and_store_domains method
        mock.fetch_and_store_domains = AsyncMock(return_value={
            "success": True,
            "domains": [
                {"id": "DEFAULT", "name": "Default Domain"},
                {"id": "CUSTOM", "name": "Custom Domain"}
            ]
        })
        
        # Mock fetch_and_store_projects method
        mock.fetch_and_store_projects = AsyncMock(return_value={
            "success": True,
            "projects": [
                {"id": "Project1", "name": "Project 1"},
                {"id": "Project2", "name": "Project 2"}
            ]
        })
        
        # Mock fetch_and_store_root_folders method
        mock.fetch_and_store_root_folders = AsyncMock(return_value={
            "success": True,
            "count": 5
        })
        
        # Mock fetch_and_store_releases method
        mock.fetch_and_store_releases = AsyncMock(return_value={
            "success": True,
            "count": 3
        })
        
        # Mock fetch_and_store_defects method
        mock.fetch_and_store_defects = AsyncMock(return_value={
            "success": True,
            "count": 150
        })
        
        # Mock logout method
        mock.logout = AsyncMock(return_value={
            "success": True,
            "message": "Logged out successfully"
        })
        
        yield mock


@pytest.mark.asyncio
async def test_authenticate_success(mock_alm_client):
    """Test /api/authenticate endpoint with successful authentication"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/authenticate",
            json={"username": "test_user", "password": "test_pass"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Authenticated successfully"
        assert data["username"] == "test_user"
        
        # Verify ALM client was called
        mock_alm_client.authenticate.assert_called_once_with("test_user", "test_pass")


@pytest.mark.asyncio
async def test_authenticate_failure(mock_alm_client):
    """Test /api/authenticate endpoint with authentication failure"""
    # Mock authentication failure
    mock_alm_client.authenticate = AsyncMock(side_effect=Exception("Invalid credentials"))
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/authenticate",
            json={"username": "test_user", "password": "wrong_pass"}
        )
        
        assert response.status_code == 500
        assert "Invalid credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_domains_success(mock_alm_client):
    """Test /api/get_domains endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/get_domains?username=test_user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["domains"]) == 2
        assert data["domains"][0]["id"] == "DEFAULT"
        assert data["domains"][0]["name"] == "Default Domain"
        
        # Verify ALM client was called
        mock_alm_client.fetch_and_store_domains.assert_called_once_with("test_user")


@pytest.mark.asyncio
async def test_get_projects_success(mock_alm_client):
    """Test /api/get_projects endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/get_projects?username=test_user&domain=DEFAULT")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["projects"]) == 2
        assert data["projects"][0]["id"] == "Project1"
        
        # Verify ALM client was called
        mock_alm_client.fetch_and_store_projects.assert_called_once_with("test_user", "DEFAULT")


@pytest.mark.asyncio
async def test_login_success(mock_alm_client):
    """Test /api/login endpoint - complete login with tree data loading"""
    with patch('app.main.db') as mock_db:
        # Mock update_one for user_credentials
        mock_db.user_credentials.update_one = AsyncMock()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/login",
                json={
                    "username": "test_user",
                    "domain": "DEFAULT",
                    "project": "Project1"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["testplan_root_folders"] == 5
            assert data["testlab_releases"] == 3
            assert data["defects"] == 150
            
            # Verify all ALM client methods were called
            mock_alm_client.fetch_and_store_root_folders.assert_called_once_with(
                "test_user", "DEFAULT", "Project1"
            )
            mock_alm_client.fetch_and_store_releases.assert_called_once_with(
                "test_user", "DEFAULT", "Project1"
            )
            mock_alm_client.fetch_and_store_defects.assert_called_once_with(
                "test_user", "DEFAULT", "Project1", page_size=100
            )
            
            # Verify user_credentials was updated twice (domain/project selection + logged_in flag)
            assert mock_db.user_credentials.update_one.call_count == 2


@pytest.mark.asyncio
async def test_logout_success(mock_alm_client):
    """Test /api/logout endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/logout",
            json={"username": "test_user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Logged out successfully"
        
        # Verify ALM client was called
        mock_alm_client.logout.assert_called_once_with("test_user")


@pytest.mark.asyncio
async def test_authentication_flow_complete(mock_alm_client):
    """Test complete authentication flow: authenticate → get_domains → get_projects → login"""
    with patch('app.main.db') as mock_db:
        mock_db.user_credentials.update_one = AsyncMock()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Step 1: Authenticate
            auth_response = await client.post(
                "/api/authenticate",
                json={"username": "test_user", "password": "test_pass"}
            )
            assert auth_response.status_code == 200
            assert auth_response.json()["success"] is True
            
            # Step 2: Get domains
            domains_response = await client.get("/api/get_domains?username=test_user")
            assert domains_response.status_code == 200
            domains_data = domains_response.json()
            assert len(domains_data["domains"]) == 2
            
            # Step 3: Get projects
            projects_response = await client.get(
                "/api/get_projects?username=test_user&domain=DEFAULT"
            )
            assert projects_response.status_code == 200
            projects_data = projects_response.json()
            assert len(projects_data["projects"]) == 2
            
            # Step 4: Login (select domain/project and load tree data)
            login_response = await client.post(
                "/api/login",
                json={
                    "username": "test_user",
                    "domain": "DEFAULT",
                    "project": "Project1"
                }
            )
            assert login_response.status_code == 200
            login_data = login_response.json()
            assert login_data["success"] is True
            assert login_data["testplan_root_folders"] > 0
            assert login_data["testlab_releases"] > 0
            assert login_data["defects"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
