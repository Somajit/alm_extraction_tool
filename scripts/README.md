# ReleaseCraft - Scripts

This directory contains utility scripts for deployment, setup, and testing.

## Deployment Scripts

### deploy-all.bat
Deploy the complete ALM stack (MongoDB, Mock ALM, Backend, Frontend).

**Usage:**
```bash
scripts\deploy-all.bat
```

**Deploys:**
- MongoDB (port 27017)
- Mock ALM Server (port 8001)
- Backend API (port 8000)
- Frontend UI (port 5173)

### deploy-mock-alm.bat
Deploy only the Mock ALM server.

**Usage:**
```bash
scripts\deploy-mock-alm.bat
```

**Features:**
- Automatically copies required files (main.py, alm_format_utils.py)
- Builds Docker container
- Starts service on port 8001

### deploy-backend.bat
Deploy only the Backend API service.

**Usage:**
```bash
scripts\deploy-backend.bat
```

### deploy-frontend.bat
Deploy only the Frontend UI service.

**Usage:**
```bash
scripts\deploy-frontend.bat
```

## Mock ALM Scripts

### setup-mock-alm.bat
Copy required files to mock_alm directory.

**Usage:**
```bash
scripts\setup-mock-alm.bat
```

**What it does:**
- Copies `backend/app/mock_alm.py` → `mock_alm/main.py`
- Copies `backend/app/alm_format_utils.py` → `mock_alm/alm_format_utils.py`

### start-mock-alm.bat
Start Mock ALM server using existing scripts (wrapper for backward compatibility).

**Usage:**
```bash
scripts\start-mock-alm.bat
```

### start-mock-alm-standalone.bat
Start Mock ALM server without Docker (pure Python).

**Usage:**
```bash
scripts\start-mock-alm-standalone.bat
```

**Features:**
- Installs dependencies if needed
- Runs on port 8001
- Hot reload enabled

### test-mock-alm.py
Test Mock ALM server endpoints.

**Usage:**
```bash
python scripts\test-mock-alm.py
```

## MongoDB Scripts

### setup-and-test-mongo.bat
Setup and verify MongoDB connection.

**Usage:**
```bash
scripts\setup-and-test-mongo.bat
```

### switch-to-local-mongo.bat
Switch backend to use local MongoDB.

**Usage:**
```bash
scripts\switch-to-local-mongo.bat
```

### switch-to-atlas-mongo.bat
Switch backend to use MongoDB Atlas cloud.

**Usage:**
```bash
scripts\switch-to-atlas-mongo.bat
```

## Database Scripts

### add_sample_data.py
Adds sample test data to MongoDB including users, domains, projects, test trees, and defects.

**Usage:**
```bash
# Using default MongoDB URI (localhost:27017/alm_db)
python add_sample_data.py

# Using custom MongoDB URI
MONGO_URI="mongodb://localhost:27017/alm_db" python add_sample_data.py
```

**What it creates:**

- **Users:**
  - admin / admin123
  - testuser / test123
  - developer / dev123

- **Domains:**
  - DomainA, DomainB, DomainC

- **Projects:**
  - DomainA: Project1, Project2, Project3
  - DomainB: ProjectX, ProjectY
  - DomainC: ProjectAlpha

- **Test Trees:**
  - Test Plans and Test Labs for projects

- **Defects:**
  - Multiple defects with different statuses and priorities

**Features:**
- ✅ Idempotent - safe to run multiple times (checks for existing data)
- ✅ Async operations using Motor
- ✅ Detailed output showing what was created/skipped
- ✅ Summary statistics at the end

## Environment Management

### setup-pyenv.bat
Setup Python virtual environment for backend development.

**Usage:**
```bash
scripts\setup-pyenv.bat
```

### cleanup-backend-venv.bat
Clean up Python virtual environment.

**Usage:**
```bash
scripts\cleanup-backend-venv.bat
```

## Quick Start

### Full Stack Deployment
```bash
# Deploy everything
scripts\deploy-all.bat

# Services will be available at:
# - Frontend: http://localhost:5173
# - Backend: http://localhost:8000
# - Mock ALM: http://localhost:8001
# - MongoDB: localhost:27017
```

### Development Mode
```bash
# 1. Start Mock ALM (standalone Python)
scripts\start-mock-alm-standalone.bat

# 2. Start Backend (in separate terminal)
cd backend
python -m uvicorn app.main:app --reload

# 3. Start Frontend (in separate terminal)
cd frontend
npm run dev
```

## Requirements

```bash
pip install motor pymongo fastapi uvicorn
```

Or install from backend requirements:
```bash
pip install -r ../backend/requirements.txt
```
