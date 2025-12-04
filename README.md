# ALM Extraction Tool (Frontend + Backend + Mongo)

This repository contains a Vite + React frontend and a FastAPI backend connected to MongoDB.

Quick start (Docker Desktop):

1. Setup and start MongoDB locally:

```cmd
scripts\setup-and-test-mongo.bat
```

This script will:
- Remove any existing MongoDB container
- Start a fresh MongoDB container
- Wait for initialization
- Test the connection
- Initialize sample data

2. In a new terminal, start the backend:

```cmd
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. In another terminal, start the frontend:

```cmd
cd frontend
npm install
npm run dev
```

4. Open http://localhost:5173 in your browser

5. Login with: `admin` / `admin123`

Notes:
- The local MongoDB container runs on `localhost:27017`
- Sample data includes 2 domains, 3 projects, test plans, test labs, and defects
- For MongoDB Atlas cloud setup, see `docs/ATLAS_SETUP.md`
- For Docker Compose (all services together), use: `docker-compose up --build`

MongoDB Atlas (optional)
-------------------------
If you prefer MongoDB Atlas instead of the local `mongo` container, follow these steps:

1. Create a MongoDB Atlas cluster at https://www.mongodb.com/cloud/atlas and create a database user with a secure password. Give the user at least readWrite on the target DB.
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

