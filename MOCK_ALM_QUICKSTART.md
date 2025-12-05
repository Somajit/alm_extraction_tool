# Quick Start Guide - Mock ALM Server

## What is the Mock ALM Server?

A standalone FastAPI server that simulates HP ALM REST API responses. Perfect for development and testing without needing access to a real ALM instance.

## Quick Start

### 1. Start Mock ALM Server

**Option A: Using batch script (Windows)**
```cmd
scripts\start-mock-alm.bat
```

**Option B: Manual start**
```cmd
cd backend\app
python mock_alm.py
```

Server will start on: **http://localhost:8001**

### 2. Configure Backend to Use Mock Server

Edit `backend\.env`:
```env
ALM_BASE_URL=http://localhost:8001/qcbin
```

### 3. Test the Mock Server

Run the test script:
```cmd
cd scripts
python test-mock-alm.py
```

Or use the application normally - login with any credentials (e.g., username: `admin`, password: `admin123`)

## What You Get

### Domains
- DEFAULT
- QUALITY_CENTER
- DEMO_DOMAIN

### Projects (in DEFAULT domain)
- DEMO_PROJECT
- TEST_PROJECT

### Test Folder Structure
```
Subject (id: 1)
├── Functional Tests (id: 2)
│   ├── Login Module (id: 5)
│   │   ├── TC_Login_ValidCredentials (1001)
│   │   ├── TC_Login_InvalidPassword (1002)
│   │   └── TC_Login_EmptyFields (1003)
│   └── User Management (id: 6)
│       ├── TC_CreateUser_Success (2001)
│       └── TC_UpdateUser_Profile (2002)
├── Integration Tests (id: 3)
└── Regression (id: 4)

Automation (id: 100)
├── API Tests (id: 101)
│   └── API_GET_Users (3001)
└── UI Tests (id: 102)
```

### Test Details
Each test includes:
- Complete metadata (id, name, status, owner, etc.)
- 4 design steps with descriptions and expected results
- 2 attachments (documents/screenshots)

## Running Full Application with Mock ALM

Open 4 terminals:

**Terminal 1 - MongoDB**
```cmd
docker start alm_mongo
```

**Terminal 2 - Mock ALM Server** (port 8001)
```cmd
scripts\start-mock-alm.bat
```

**Terminal 3 - Backend API** (port 8000)
```cmd
cd backend
%USERPROFILE%\pyenv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 4 - Frontend** (port 5173)
```cmd
cd frontend
npm run dev
```

Access: http://localhost:5173

## Switching Between Mock and Real ALM

### Use Mock ALM (Development)
```env
# backend/.env
ALM_BASE_URL=http://localhost:8001/qcbin
```

### Use Real ALM (Production)
```env
# backend/.env
ALM_BASE_URL=https://your-alm-server.com/qcbin
```

**No code changes needed!**

## Features

✅ Complete 2-step authentication flow  
✅ Proper cookie management (4 cookies)  
✅ Hierarchical test folder structure  
✅ Tests with design steps  
✅ Attachments for tests and folders  
✅ Releases and defects  
✅ ALM-compliant JSON format  

## Troubleshooting

### Port 8001 in use
```cmd
netstat -ano | findstr :8001
taskkill /PID <pid> /F
```

### Cannot connect to mock server
1. Check if server is running: http://localhost:8001
2. Verify Python venv is activated
3. Check firewall settings

### Login fails
- Mock server accepts **any credentials**
- Ensure backend is pointing to mock server URL
- Check browser console for errors

## Documentation

Full documentation: [docs/MOCK_ALM_SERVER.md](../docs/MOCK_ALM_SERVER.md)

## Adding Custom Data

Edit `backend/app/mock_alm.py`:
- **Folders**: Modify `get_test_folders()` function
- **Tests**: Modify `get_tests()` function  
- **Design Steps**: Modify `get_design_steps()` function
- **Attachments**: Modify `get_attachments()` function

Restart server after changes.
