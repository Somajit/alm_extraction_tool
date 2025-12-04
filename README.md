# ALM Extraction Tool (Frontend + Backend + MongoDB Atlas)

This repository contains a Vite + React (TypeScript) frontend and a FastAPI backend connected to MongoDB Atlas.

## Quick Start (Docker - Recommended)

Run the entire stack with one command:

```cmd
scripts\deploy-all.bat
```

This will:
- Start MongoDB (local Docker container)
- Build and deploy backend (port 8000)
- Build and deploy frontend (port 5173)
- Initialize sample data

Then open http://localhost:5173 and login with: `admin` / `admin123`

## Local Development Setup

### Python Environment

This project uses a global Python virtual environment located at `%USERPROFILE%\pyenv`.

**One-time setup:**
```cmd
scripts\setup-pyenv.bat
```

This will create the virtual environment and install all required packages.

**VS Code Integration:**
- Virtual environment auto-activates when opening a terminal
- Python interpreter automatically configured
- No manual activation needed

**Manual activation (if needed):**
```cmd
%USERPROFILE%\pyenv\Scripts\activate.bat
```

### Backend (Python)

1. **Ensure pyenv is set up** (see above)

2. **Create .env file** (if not exists):
```
MONGO_URI=mongodb+srv://admin:admin123@cluster0.uilvvya.mongodb.net/alm_db?retryWrites=true&w=majority
CORS_ORIGINS=http://localhost:5173
```

3. **Run backend:**
```cmd
cd backend
uvicorn app.main:app --reload
```

Backend will run on http://localhost:8000

### Frontend (React + TypeScript)

1. **Install dependencies:**
```cmd
cd frontend
npm install
```

2. **Run development server:**
```cmd
npm run dev
```

Frontend will run on http://localhost:5173

### Add Sample Data

```cmd
cd scripts
python add_sample_data.py
```

## Login Credentials

- **admin** / admin123
- **testuser** / test123
- **developer** / dev123

## MongoDB Setup

Currently using **MongoDB Atlas (cloud)** - Free tier M0.

Connection string in `backend/.env`:
```
MONGO_URI=mongodb+srv://admin:admin123@cluster0.uilvvya.mongodb.net/alm_db?retryWrites=true&w=majority
```
2. Add an IP access list entry for the machine(s) that will connect. For local testing you can add `0.0.0.0/0` (not recommended for production).
3. Copy the connection string (SRV form) from the Atlas UI. It will look like:

```
mongodb+srv://<username>:<password>@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority
```

4. Configure your backend to use that URI. Options:

- With `docker-compose`: set `MONGO_URI` for the `backend` service in the `environment` section. Do NOT commit credentials to version control. Example (use a `docker-compose.override.yml` or environment file):

```yaml
services:
	backend:
		environment:
			- MONGO_URI=mongodb+srv://<username>:<password>@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority
```

- With Helm / Kubernetes: set the value `mongo.uri` in `helm/values.yaml` or create a Kubernetes Secret and mount it into the backend deployment as an environment variable.

5. Ensure DNS libraries are present so `mongodb+srv` URIs work. The backend requirements include `dnspython` which is required by the MongoDB driver for SRV resolution.

6. Restart the backend and run the seed endpoint to populate demo data (if desired):

```powershell
curl -X POST http://localhost:8000/init
```

Security notes:
- Never store Atlas credentials in plaintext in the repository. Use environment variables or secrets (Docker secrets, Kubernetes Secrets, or a secret store).
- Restrict IP access lists to known CIDR blocks for production.
- Use role-based accounts and minimum privileges.

Quick MongoDB Atlas Setup (Local)
---------------------------------

For a full step-by-step guide, see `docs/ATLAS_SETUP.md`.

**Quick Start:**

1. Create a free MongoDB Atlas cluster at https://www.mongodb.com/cloud/atlas
2. Create a database user (e.g., `almuser` with password)
3. Add your local IP to the IP whitelist (Network Access → Add IP)
4. Get your connection string (Connect → Drivers)

**Option A: Using PowerShell Helper (Recommended)**

First, install the required Python packages:
```powershell
pip install motor dnspython
```

Then create the env file and test connection:
```powershell
# Create .env.atlas file
.\scripts\setup-atlas-env.ps1 `
  -MongoUri "mongodb+srv://almuser:MyPassword@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority" `
  -CreateEnvFile

# Test the connection (initializes sample data)
.\scripts\setup-atlas-env.ps1 -TestConnection
```

**Option B: Manual Setup**

1. Create `backend/.env.atlas`:
```
MONGO_URI=mongodb+srv://almuser:MyPassword@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority
CORS_ORIGINS=http://localhost:5173
```

2. Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  backend:
    env_file:
      - ./backend/.env.atlas
```

3. Start Docker services:
```powershell
docker-compose up --build
```

4. Test the backend:
```powershell
curl -X POST http://localhost:8000/init
curl http://localhost:8000/domains
```

**Option C: Test Script**

```powershell
cd d:\Somajit\alm_extraction_tool
# Set your MongoDB URI
$env:MONGO_URI="mongodb+srv://almuser:MyPassword@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority"
# Run test and init
python scripts/test_atlas_connection.py
```

