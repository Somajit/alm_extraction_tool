# Mock ALM Service

Standalone Mock ALM REST API Server for testing ReleaseCraft.

## Setup

### Manual File Copy (Required)
Before building the Docker container, copy these files from the backend:

```bash
# From project root
copy backend\app\mock_alm.py mock_alm\main.py
copy backend\app\alm_format_utils.py mock_alm\alm_format_utils.py
```

### Directory Structure
```
mock_alm/
├── Dockerfile
├── requirements.txt
├── main.py (copied from backend/app/mock_alm.py)
├── alm_format_utils.py (copied from backend/app/alm_format_utils.py)
└── README.md
```

## Running Standalone

### Using Docker
```bash
cd mock_alm
docker build -t mock-alm:latest .
docker run -p 8001:8001 mock-alm:latest
```

### Using Python Directly
```bash
cd mock_alm
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

## Running with Docker Compose

From project root:
```bash
docker-compose up mock-alm
```

## API Endpoints

The Mock ALM server runs on `http://localhost:8001` and provides:

- **Authentication**: 
  - POST `/qcbin/authentication-point/authenticate`
  - POST `/qcbin/rest/site-session`

- **Test Plan**:
  - GET `/qcbin/rest/domains`
  - GET `/qcbin/rest/domains/{domain}/projects`
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/test-folders`
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/tests`
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/design-steps`

- **Test Lab**:
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/releases`
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/release-cycles`
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/test-sets`
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/runs`

- **Defects**:
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/defects`

- **Attachments**:
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/attachments`
  - GET `/qcbin/rest/domains/{domain}/projects/{project}/attachments/{id}`

## Health Check

```bash
curl http://localhost:8001/
```

## Test Data

The mock server provides:
- **5 root test folders** with 3-level deep hierarchy
- **4+ tests per folder** with attachments
- **3+ design steps per test** with attachments
- **5 releases** with 2-3 cycles each
- **3-5 test sets per cycle** with attachments
- **2-3 runs per test set** with attachments
- **12 defects** (8 with attachments)
- **PNG/PDF/TXT attachments** at all levels
