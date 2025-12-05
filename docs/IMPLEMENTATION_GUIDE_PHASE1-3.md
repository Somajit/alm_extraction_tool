# Implementation Guide - Backend Refactoring Phase 1-3

## Status: NEW ALM CLIENT CREATED ✅

Location: `backend/app/alm_client_new.py`

## Next Steps (Continue Implementation)

### Step 1: Replace old alm.py with new implementation
```bash
# Backup old file
mv backend/app/alm.py backend/app/alm_old.py.bak
# Use new implementation
mv backend/app/alm_client_new.py backend/app/alm.py
# Update class name in file
sed -i 's/class ALMClient/class ALM/g' backend/app/alm.py
```

### Step 2: Add new API endpoints to main.py

Add these imports at the top:
```python
from pydantic import BaseModel
from app.alm import ALM  # Updated ALM client
```

Add request models:
```python
class AuthenticateRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    domain: str
    project: str

class LogoutRequest(BaseModel):
    username: str
```

Add endpoints:
```python
@app.post("/api/authenticate")
async def authenticate(request: AuthenticateRequest):
    """POST /api/authenticate - Authenticate with ALM"""
    alm_client = ALM(db=db)
    result = await alm_client.authenticate(request.username, request.password)
    return result

@app.get("/api/get_domains")
async def get_domains(username: str):
    """GET /api/get_domains?username={username}"""
    alm_client = ALM(db=db)
    result = await alm_client.fetch_and_store_domains(username)
    return result

@app.get("/api/get_projects")
async def get_projects(username: str, domain: str):
    """GET /api/get_projects?username={username}&domain={domain}"""
    alm_client = ALM(db=db)
    result = await alm_client.fetch_and_store_projects(username, domain)
    return result

@app.post("/api/login")
async def login(request: LoginRequest):
    """POST /api/login - Complete login, fetch initial data"""
    alm_client = ALM(db=db)
    
    # Store domain/project in user_credentials
    await db.user_credentials.update_one(
        {"user": request.username},
        {"$set": {
            "domain": request.domain,
            "project": request.project,
            "logged_in": True
        }}
    )
    
    # Fetch root folders
    folders_result = await alm_client.fetch_and_store_root_folders(
        request.username,
        request.domain,
        request.project
    )
    
    # Fetch releases
    releases_result = await alm_client.fetch_and_store_releases(
        request.username,
        request.domain,
        request.project
    )
    
    # Fetch defects
    defects_result = await alm_client.fetch_and_store_defects(
        request.username,
        request.domain,
        request.project
    )
    
    return {
        "success": True,
        "testplan_root_folders": folders_result.get("count", 0),
        "testlab_releases": releases_result.get("count", 0),
        "defects": defects_result.get("count", 0)
    }

@app.post("/api/logout")
async def logout(request: LogoutRequest):
    """POST /api/logout"""
    alm_client = ALM(db=db)
    result = await alm_client.logout(request.username)
    return result
```

### Step 3: Update .env file

Add these variables:
```ini
# ALM Configuration
USE_MOCK_ALM=true
MOCK_ALM_URL=http://localhost:5001
ALM_URL=http://alm.example.com:8080/qcbin
ALM_ENCRYPTION_KEY=your-encryption-key-here

# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=releasecraftdb
```

### Step 4: Update docker-compose.yml

Add environment variables to backend service:
```yaml
backend:
  environment:
    - USE_MOCK_ALM=${USE_MOCK_ALM:-true}
    - MOCK_ALM_URL=${MOCK_ALM_URL:-http://mock-alm:5001}
    - ALM_URL=${ALM_URL:-http://alm:8080/qcbin}
    - ALM_ENCRYPTION_KEY=${ALM_ENCRYPTION_KEY}
    - MONGODB_URI=${MONGODB_URI:-mongodb://mongo:27017}
    - MONGODB_DB=${MONGODB_DB:-releasecraftdb}
```

### Step 5: Update backend/Dockerfile

Ensure environment variables are available:
```dockerfile
# Already should be there, but verify
ENV USE_MOCK_ALM=${USE_MOCK_ALM}
ENV MOCK_ALM_URL=${MOCK_ALM_URL}
ENV ALM_URL=${ALM_URL}
ENV ALM_ENCRYPTION_KEY=${ALM_ENCRYPTION_KEY}
```

### Step 6: Create backend unit tests

Create `backend/tests/test_api_auth.py`:
```python
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app

@pytest.mark.asyncio
async def test_authenticate_success():
    """Test successful authentication"""
    with patch('app.alm.ALM.authenticate') as mock_auth:
        mock_auth.return_value = {
            "success": True,
            "message": "Authenticated successfully",
            "username": "testuser"
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/authenticate",
                json={"username": "testuser", "password": "testpass"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["username"] == "testuser"

@pytest.mark.asyncio
async def test_get_domains_success():
    """Test fetching domains"""
    with patch('app.alm.ALM.fetch_and_store_domains') as mock_domains:
        mock_domains.return_value = {
            "success": True,
            "domains": [
                {"Domain ID": "DEFAULT", "Domain Name": "Default"},
                {"Domain ID": "CUSTOM", "Domain Name": "Custom"}
            ],
            "count": 2
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/get_domains?username=testuser")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2

# Add more tests for projects, login, logout
```

### Step 7: Update Helm chart

Update `helm/releasecraft/values.yaml`:
```yaml
backend:
  env:
    USE_MOCK_ALM: "true"
    MOCK_ALM_URL: "http://mock-alm:5001"
    ALM_URL: "http://alm:8080/qcbin"
    ALM_ENCRYPTION_KEY: "changeme"
    MONGODB_URI: "mongodb://mongo:27017"
    MONGODB_DB: "releasecraftdb"
```

Update `helm/releasecraft/templates/backend-deployment.yaml`:
```yaml
env:
  - name: USE_MOCK_ALM
    value: {{ .Values.backend.env.USE_MOCK_ALM | quote }}
  - name: MOCK_ALM_URL
    value: {{ .Values.backend.env.MOCK_ALM_URL | quote }}
  - name: ALM_URL
    value: {{ .Values.backend.env.ALM_URL | quote }}
  - name: ALM_ENCRYPTION_KEY
    valueFrom:
      secretKeyRef:
        name: backend-secrets
        key: alm-encryption-key
```

### Step 8: Update frontend API calls

Create `frontend/src/services/api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const authApi = {
  authenticate: async (username: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/api/authenticate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    return response.json();
  },
  
  getDomains: async (username: string) => {
    const response = await fetch(`${API_BASE_URL}/api/get_domains?username=${username}`);
    return response.json();
  },
  
  getProjects: async (username: string, domain: string) => {
    const response = await fetch(`${API_BASE_URL}/api/get_projects?username=${username}&domain=${domain}`);
    return response.json();
  },
  
  login: async (username: string, domain: string, project: string) => {
    const response = await fetch(`${API_BASE_URL}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, domain, project })
    });
    return response.json();
  },
  
  logout: async (username: string) => {
    const response = await fetch(`${API_BASE_URL}/api/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username })
    });
    return response.json();
  }
};
```

### Step 9: Create frontend unit tests

Create `frontend/tests/api.test.ts`:
```typescript
import { describe, it, expect, vi } from 'vitest';
import { authApi } from '../src/services/api';

describe('Authentication API', () => {
  it('should authenticate successfully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      json: async () => ({
        success: true,
        username: 'testuser'
      })
    });
    
    const result = await authApi.authenticate('testuser', 'testpass');
    expect(result.success).toBe(true);
    expect(result.username).toBe('testuser');
  });
  
  it('should fetch domains', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      json: async () => ({
        success: true,
        domains: [
          { 'Domain ID': 'DEFAULT', 'Domain Name': 'Default' }
        ],
        count: 1
      })
    });
    
    const result = await authApi.getDomains('testuser');
    expect(result.success).toBe(true);
    expect(result.count).toBe(1);
  });
});
```

### Step 10: Testing

```bash
# Start services
docker-compose up -d

# Test authentication flow
curl -X POST http://localhost:8000/api/authenticate \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Test domains
curl "http://localhost:8000/api/get_domains?username=test"

# Test projects
curl "http://localhost:8000/api/get_projects?username=test&domain=DEFAULT"

# Test login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","domain":"DEFAULT","project":"MyProject"}'

# Verify MongoDB
docker exec mongo mongosh releasecraftdb --eval "db.domains.find().pretty()"
docker exec mongo mongosh releasecraftdb --eval "db.projects.find().pretty()"
docker exec mongo mongosh releasecraftdb --eval "db.user_credentials.find().pretty()"
```

## Summary

**Files Created**:
- ✅ `backend/app/alm_client_new.py` - New ALM client implementation

**Files to Modify**:
- `backend/app/alm.py` - Replace with new implementation
- `backend/app/main.py` - Add new API endpoints
- `.env` - Add environment variables
- `docker-compose.yml` - Add backend environment variables
- `helm/releasecraft/values.yaml` - Add configuration
- `helm/releasecraft/templates/backend-deployment.yaml` - Add env vars
- `frontend/src/services/api.ts` - Create API service layer

**Files to Create**:
- `backend/tests/test_api_auth.py` - Backend unit tests
- `frontend/tests/api.test.ts` - Frontend unit tests

**Testing Checklist**:
- [ ] Backend unit tests pass
- [ ] Frontend unit tests pass
- [ ] Authentication flow works end-to-end
- [ ] Domains fetched and stored in MongoDB
- [ ] Projects fetched and stored in MongoDB
- [ ] Login completes and fetches initial data
- [ ] All data uses standardized entity format
- [ ] Display format shows only displayable fields with aliases
- [ ] MongoDB queries return correct data

## Next Phase

Once Phase 1-3 is complete and tested, proceed with:
- Phase 4: TestPlan expansion endpoints (expand_folder, expand_test, expand_design_step)
- Phase 5: TestLab expansion endpoints
- Phase 6: Defect expansion endpoints
- Phase 7: Export/query endpoints
- Phase 8: Recursive extraction endpoints
