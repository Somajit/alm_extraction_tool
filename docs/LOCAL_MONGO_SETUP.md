# Local MongoDB Setup (Docker)

For local development without using MongoDB Atlas cloud, you can run MongoDB in a Docker container.

## Quick Start

### Option 1: Using Docker Desktop (Easiest)

1. Make sure Docker Desktop is running.

2. Start MongoDB:
```powershell
docker run -d `
  --name alm_mongo `
  -p 27017:27017 `
  -e MONGO_INITDB_DATABASE=alm_db `
  mongo:6.0
```

3. Verify it's running:
```powershell
docker ps | findstr alm_mongo
```

4. Test connection:
```powershell
# Set the local MongoDB URI
$env:MONGO_URI="mongodb://localhost:27017/alm_db"

# Initialize sample data
python scripts/test_atlas_connection.py
```

### Option 2: Using docker-compose (Recommended)

The repository already has `docker-compose.yml` configured to run MongoDB locally.

1. Start all services:
```powershell
cd d:\Somajit\alm_extraction_tool
docker-compose up -d
```

2. Wait 5 seconds for MongoDB to initialize, then init data:
```powershell
curl -X POST http://localhost:8000/init
```

3. Verify:
```powershell
curl http://localhost:8000/domains
```

### Option 3: Local Python Development (No Docker)

1. Download and install MongoDB Community Edition from https://www.mongodb.com/try/download/community

2. Start MongoDB:
```powershell
# Windows - if installed in default location:
& "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" --dbpath "C:\data\db"
```

3. Test connection:
```powershell
$env:MONGO_URI="mongodb://localhost:27017/alm_db"
python scripts/test_atlas_connection.py
```

## Verify Setup

After starting MongoDB, check the connection:
```powershell
# This will show the database summary
python scripts/test_atlas_connection.py
```

Expected output:
```
✓ Connected to MongoDB successfully
✓ Database initialized with sample data
✓ Domains: ['DomainA', 'DomainB']
✓ Projects: ['Project1', 'Project2']
✓ Defects: 2 records
```

## Clean Up

### Stop Docker container:
```powershell
docker stop alm_mongo
docker rm alm_mongo
```

### Stop docker-compose:
```powershell
docker-compose down
```

## Using with Backend

### Option A: Docker Compose (All services)
```powershell
cd d:\Somajit\alm_extraction_tool
docker-compose up --build
```

Then open http://localhost:5173 (frontend) and http://localhost:8000/docs (backend API docs).

### Option B: Local Backend + Docker MongoDB
```powershell
# Terminal 1: Start MongoDB
docker run -d --name alm_mongo -p 27017:27017 mongo:6.0

# Terminal 2: Start backend
cd backend
$env:MONGO_URI="mongodb://localhost:27017/alm_db"
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Start frontend
cd frontend
npm install
npm run dev
```

## Troubleshooting

### "Port 27017 already in use"
MongoDB is already running or another container is using it:
```powershell
# Find what's using port 27017
netstat -ano | findstr :27017

# Or stop any existing MongoDB container:
docker ps
docker stop <container_id>
```

### "Connection refused"
Make sure MongoDB is running:
```powershell
docker ps | findstr alm_mongo
```

### Database not persisting
By default, Docker containers don't persist data. To add persistence:
```powershell
# Create a volume first
docker volume create mongo_data

# Then run with volume
docker run -d `
  --name alm_mongo `
  -p 27017:27017 `
  -v mongo_data:/data/db `
  mongo:6.0
```

## Next Steps

1. Run the backend and frontend together
2. Login with: `admin` / `admin123`
3. Select domain and project to see test plans, test labs, and defects
