# Mock ALM Service - Separation Complete! 🎉

## What Changed?

The Mock ALM service has been separated from the backend into its own standalone Docker container for better modularity and easier testing.

## New Directory Structure

```
alm_extraction_tool/
├── mock_alm/                          # NEW - Standalone Mock ALM Service
│   ├── Dockerfile                     # Container definition
│   ├── requirements.txt               # Python dependencies
│   ├── README.md                      # API documentation
│   ├── SETUP.md                       # Setup instructions
│   ├── main.py                        # Mock ALM server (copied from backend)
│   └── alm_format_utils.py            # Format utilities (copied from backend)
├── backend/
│   └── app/
│       ├── mock_alm.py                # Source file (kept for reference)
│       └── alm_format_utils.py        # Source file
├── scripts/
│   ├── setup-mock-alm.bat             # NEW - Copy files to mock_alm
│   ├── deploy-mock-alm.bat            # NEW - Deploy Mock ALM container
│   ├── start-mock-alm-standalone.bat  # NEW - Run without Docker
│   ├── deploy-all.bat                 # UPDATED - Now includes Mock ALM
│   └── README.md                      # UPDATED - Documents all scripts
└── docker-compose.yml                 # UPDATED - Added mock-alm service
```

## Setup Steps (One-Time)

### Option 1: Automatic Setup (Recommended)
```bash
# This will copy files and deploy the container
scripts\deploy-mock-alm.bat
```

### Option 2: Manual Setup
```bash
# Step 1: Copy files
scripts\setup-mock-alm.bat

# Step 2: Deploy
docker-compose up -d --build mock-alm
```

## Deployment Options

### Full Stack (All Services)
```bash
scripts\deploy-all.bat
```
Deploys:
- MongoDB (27017)
- Mock ALM (8001)
- Backend (8000)
- Frontend (5173)

### Mock ALM Only
```bash
# Using Docker
scripts\deploy-mock-alm.bat

# OR using standalone Python
scripts\start-mock-alm-standalone.bat
```

### Individual Services
```bash
docker-compose up -d mock-alm    # Just Mock ALM
docker-compose up -d backend     # Just Backend
docker-compose up -d frontend    # Just Frontend
```

## Key Benefits

### 1. **Isolation**
- Mock ALM runs independently
- Can be started/stopped without affecting other services
- Easier to debug and test

### 2. **Flexibility**
- Run with Docker Compose (production-like)
- Run standalone Python (development)
- Easy to switch between real and mock ALM

### 3. **Reusability**
- Can be used by multiple backend instances
- Shareable across teams
- Easy to extend with new endpoints

### 4. **Better Development**
- Hot reload in standalone mode
- Independent versioning
- Clear separation of concerns

## Configuration

### Backend Connection
Update backend to point to Mock ALM:

**Docker Compose** (`docker-compose.yml`):
```yaml
backend:
  environment:
    - ALM_BASE_URL=http://mock-alm:8001  # Container name
```

**Local Development** (`.env`):
```env
ALM_BASE_URL=http://localhost:8001  # Localhost
```

### Port Configuration
Default ports:
- Mock ALM: 8001
- Backend: 8000
- Frontend: 5173
- MongoDB: 27017

## Verification

### 1. Health Check
```bash
curl http://localhost:8001/
```

Expected:
```json
{
  "status": "ok",
  "service": "Mock ALM REST API Server",
  "version": "2.0.0"
}
```

### 2. Test Authentication
```bash
# Authenticate
curl -X POST http://localhost:8001/qcbin/authentication-point/authenticate \
  -d "username=test&password=test"

# Create session
curl -X POST http://localhost:8001/qcbin/rest/site-session \
  -b "LWSSO_COOKIE_KEY=mock_lwsso_token_12345"
```

### 3. Get Test Data
```bash
# Get domains
curl http://localhost:8001/qcbin/rest/domains \
  -b "LWSSO_COOKIE_KEY=mock_lwsso_token_12345; QCSession=mock_session_67890; ALM_USER=mock_user; XSRF-TOKEN=mock_xsrf_token"
```

## Docker Commands

```bash
# View logs
docker logs alm_mock_server -f

# Stop service
docker-compose stop mock-alm

# Restart service
docker-compose restart mock-alm

# Rebuild service
docker-compose up -d --build mock-alm

# Remove service
docker-compose down mock-alm
```

## Available Test Data

The Mock ALM provides rich test data:
- ✅ **5 root test folders** with 3-level deep hierarchy
- ✅ **Multiple tests per folder** with attachments
- ✅ **3+ design steps per test** (some with attachments)
- ✅ **5 releases** with 2-3 cycles each
- ✅ **3-5 test sets per cycle** with attachments
- ✅ **2-3 runs per test set** with attachments
- ✅ **12 defects** (8 with PNG attachments)
- ✅ **PNG/PDF/TXT attachments** at all levels

## API Endpoints

All endpoints are documented in `mock_alm/README.md`:

**Authentication:**
- POST `/qcbin/authentication-point/authenticate`
- POST `/qcbin/rest/site-session`

**Test Plan:**
- GET `/qcbin/rest/domains`
- GET `/qcbin/rest/domains/{domain}/projects`
- GET `/qcbin/rest/domains/{domain}/projects/{project}/test-folders`
- GET `/qcbin/rest/domains/{domain}/projects/{project}/tests`
- GET `/qcbin/rest/domains/{domain}/projects/{project}/design-steps`

**Test Lab:**
- GET `/qcbin/rest/domains/{domain}/projects/{project}/releases`
- GET `/qcbin/rest/domains/{domain}/projects/{project}/release-cycles`
- GET `/qcbin/rest/domains/{domain}/projects/{project}/test-sets`
- GET `/qcbin/rest/domains/{domain}/projects/{project}/runs`

**Defects:**
- GET `/qcbin/rest/domains/{domain}/projects/{project}/defects`

**Attachments:**
- GET `/qcbin/rest/domains/{domain}/projects/{project}/attachments`
- GET `/qcbin/rest/domains/{domain}/projects/{project}/attachments/{id}`

## Troubleshooting

### Files not found error?
```bash
# Run the setup script
scripts\setup-mock-alm.bat
```

### Port 8001 already in use?
```bash
# Check what's using the port
netstat -ano | findstr :8001

# Stop other services or change port in docker-compose.yml
```

### Container fails to build?
```bash
# Check if files exist
dir mock_alm\main.py
dir mock_alm\alm_format_utils.py

# If missing, run setup
scripts\setup-mock-alm.bat
```

### Import errors in logs?
```bash
# View container logs
docker logs alm_mock_server

# Ensure both files are in mock_alm/
# Rebuild container
docker-compose up -d --build mock-alm
```

## Next Steps

1. **Run Full Stack:**
   ```bash
   scripts\deploy-all.bat
   ```

2. **Open Frontend:**
   - Navigate to http://localhost:5173
   - Configure ALM URL to http://localhost:8001
   - Login and test

3. **Test Mock ALM:**
   ```bash
   python scripts\test-mock-alm.py
   ```

4. **View Logs:**
   ```bash
   docker logs alm_mock_server -f
   ```

## Documentation

- **API Reference:** `mock_alm/README.md`
- **Setup Guide:** `mock_alm/SETUP.md`
- **Scripts Reference:** `scripts/README.md`
- **Docker Compose:** `docker-compose.yml`

## Support

For issues or questions:
1. Check `mock_alm/SETUP.md` for detailed troubleshooting
2. View container logs: `docker logs alm_mock_server`
3. Test endpoints: `python scripts/test-mock-alm.py`

---

**Status:** ✅ Mock ALM service is now fully separated and containerized!
