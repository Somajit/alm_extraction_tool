# Mock ALM Service - Setup Instructions

## Overview
The Mock ALM service is now separated as a standalone Docker container for better isolation and easier testing.

## Quick Setup

### Automatic Setup (Recommended)
Run the deployment script which will automatically copy required files:

```bash
scripts\deploy-mock-alm.bat
```

### Manual Setup
If you prefer manual setup:

1. **Copy Required Files**
   ```bash
   cd d:\Somajit\alm_extraction_tool
   copy backend\app\mock_alm.py mock_alm\main.py
   copy backend\app\alm_format_utils.py mock_alm\alm_format_utils.py
   ```

2. **Build and Run**
   ```bash
   # Using Docker Compose
   docker-compose up -d --build mock-alm
   
   # OR using standalone Python
   cd mock_alm
   pip install -r requirements.txt
   python -m uvicorn main:app --host 0.0.0.0 --port 8001
   ```

## Deployment Options

### Option 1: Full Stack Deployment
Deploy all services including Mock ALM:
```bash
scripts\deploy-all.bat
```

This will deploy:
- MongoDB (port 27017)
- Mock ALM (port 8001)
- Backend (port 8000)
- Frontend (port 5173)

### Option 2: Mock ALM Only
Deploy just the Mock ALM service:
```bash
scripts\deploy-mock-alm.bat
```

### Option 3: Standalone Python
Run Mock ALM without Docker:
```bash
scripts\start-mock-alm-standalone.bat
```

## Verification

### Health Check
```bash
curl http://localhost:8001/
```

Expected response:
```json
{
  "status": "ok",
  "service": "Mock ALM REST API Server",
  "version": "2.0.0",
  "message": "Mock ALM server running. Use /qcbin/* endpoints for API access."
}
```

### Test Authentication
```bash
# Step 1: Authenticate
curl -X POST http://localhost:8001/qcbin/authentication-point/authenticate \
  -d "username=testuser&password=testpass"

# Step 2: Create Session (use cookies from step 1)
curl -X POST http://localhost:8001/qcbin/rest/site-session \
  -b "LWSSO_COOKIE_KEY=mock_lwsso_token_12345"
```

### Test Data Endpoints
```bash
# Get domains
curl http://localhost:8001/qcbin/rest/domains \
  -b "LWSSO_COOKIE_KEY=mock_lwsso_token_12345; QCSession=mock_session_67890; ALM_USER=mock_user; XSRF-TOKEN=mock_xsrf_token"

# Get projects
curl http://localhost:8001/qcbin/rest/domains/DEFAULT/projects \
  -b "LWSSO_COOKIE_KEY=mock_lwsso_token_12345; QCSession=mock_session_67890; ALM_USER=mock_user; XSRF-TOKEN=mock_xsrf_token"
```

## Docker Commands

### View Logs
```bash
docker logs alm_mock_server -f
```

### Stop Service
```bash
docker-compose stop mock-alm
```

### Restart Service
```bash
docker-compose restart mock-alm
```

### Rebuild Service
```bash
docker-compose up -d --build mock-alm
```

### Remove Service
```bash
docker-compose down mock-alm
docker rmi alm_extraction_tool-mock-alm
```

## Configuration

### Environment Variables
The Mock ALM service accepts these environment variables (set in docker-compose.yml):

- `PYTHONUNBUFFERED=1`: Disable Python output buffering for immediate log display

### Port Configuration
Default port: 8001

To change the port, update:
1. `docker-compose.yml`: ports section
2. `mock_alm/Dockerfile`: EXPOSE directive

### Connecting Backend to Mock ALM
Update backend configuration to point to Mock ALM:

**In docker-compose.yml**:
```yaml
backend:
  environment:
    - ALM_BASE_URL=http://mock-alm:8001
```

**For local development** (.env file):
```
ALM_BASE_URL=http://localhost:8001
```

## Troubleshooting

### Issue: Container fails to start
**Solution**: Check if files are copied correctly
```bash
dir mock_alm\main.py
dir mock_alm\alm_format_utils.py
```

### Issue: Port 8001 already in use
**Solution**: Stop other services or change port
```bash
# Check what's using port 8001
netstat -ano | findstr :8001

# Stop the process or change port in docker-compose.yml
```

### Issue: Import errors in logs
**Solution**: Ensure alm_format_utils.py is in the same directory as main.py
```bash
docker logs alm_mock_server
```

### Issue: 401 Authentication errors
**Solution**: Mock ALM requires all 4 cookies. Use the test scripts:
```bash
python scripts\test-mock-alm.py
```

## Test Data Available

The Mock ALM provides rich test data:
- **5 root folders** with 3-level hierarchy
- **Multiple tests** per folder with attachments
- **3+ design steps** per test
- **5 releases** with cycles and test sets
- **12 defects** with various statuses
- **Attachments** (PNG, PDF, TXT) at all levels

See `mock_alm/README.md` for complete API documentation.

## Development

### Updating Mock Data
Edit `mock_alm/main.py` to modify test data. After changes:

```bash
# Copy changes
copy backend\app\mock_alm.py mock_alm\main.py

# Rebuild
docker-compose up -d --build mock-alm
```

### Adding New Endpoints
1. Edit `backend\app\mock_alm.py`
2. Copy to `mock_alm\main.py`
3. Rebuild container

## Integration with Backend

The backend can now connect to either:
1. **Real ALM Server**: Set ALM_BASE_URL to actual ALM server
2. **Mock ALM Server**: Set ALM_BASE_URL to http://mock-alm:8001 (Docker) or http://localhost:8001 (local)

Switch between them by updating the environment variable in:
- `.env` file (local development)
- `docker-compose.yml` (Docker deployment)
