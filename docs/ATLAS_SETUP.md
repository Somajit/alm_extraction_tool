# MongoDB Atlas Setup Guide

This guide walks you through setting up a MongoDB Atlas cluster locally (for testing and development).

## Prerequisites

- MongoDB Atlas account (free tier available at https://www.mongodb.com/cloud/atlas)
- Python 3.9+ with `motor` and `pymongo` installed
- Internet connection

## Step 1: Create MongoDB Atlas Cluster

1. Go to https://www.mongodb.com/cloud/atlas and sign in (or create a free account).
2. Create a new project (or use default) and click **Build a Cluster**.
3. Choose the **Free Tier** (M0) for development/testing.
4. Select your preferred cloud provider and region (AWS, Google Cloud, or Azure).
5. Click **Create Cluster**. This takes 2-3 minutes.

## Step 2: Create Database User

1. In the Atlas UI, go to **Database Access** (left sidebar).
2. Click **Add New Database User**.
3. Choose **Password** as the authentication method.
4. Set a username (e.g., `almuser`) and a strong password (e.g., `MySecurePassword123!`).
5. Under **Database User Privileges**, select **Atlas Admin** (for simplicity; use least-privilege in production).
6. Click **Add User**.

## Step 3: Configure IP Whitelist

1. Go to **Network Access** (left sidebar).
2. Click **Add IP Address**.
3. For local development, add your local machine IP:
   - Click **Add Current IP Address** (Atlas will detect your IP).
   - Or manually enter `127.0.0.1` or `0.0.0.0/0` (NOT recommended for production).
4. Click **Confirm**.

## Step 4: Get Connection String

1. Go to **Clusters** and click **Connect** on your cluster.
2. Choose **Drivers** → **Python** (or your preferred method).
3. Copy the connection string. It will look like:
   ```
   mongodb+srv://<username>:<password>@cluster0.abcd123.mongodb.net/?retryWrites=true&w=majority
   ```
4. Replace:
   - `<username>` with your DB user (e.g., `almuser`)
   - `<password>` with your DB password

## Step 5: Configure Backend to Use Atlas

### Option A: Local Docker Compose

1. Create `backend/.env.atlas` (do not commit):
   ```
   MONGO_URI=mongodb+srv://almuser:MySecurePassword123!@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority
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

3. Start services:
   ```powershell
   cd d:\Somajit\alm_extraction_tool
   docker-compose up --build
   ```

4. Test the connection:
   ```powershell
   curl -X POST http://localhost:8000/init
   curl http://localhost:8000/domains
   ```

### Option B: Local Development (no Docker)

1. Set environment variable:
   ```powershell
   $env:MONGO_URI="mongodb+srv://almuser:MySecurePassword123!@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority"
   ```

2. Install backend dependencies:
   ```powershell
   cd d:\Somajit\alm_extraction_tool\backend
   pip install -r requirements.txt
   ```

3. Run the backend:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. In another terminal, initialize data:
   ```powershell
   python scripts/test_atlas_connection.py
   ```

### Option C: Kubernetes / Helm

1. Edit `helm/values.yaml`:
   ```yaml
   mongo:
     enabled: false
     uri: "mongodb+srv://almuser:MySecurePassword123!@cluster0.abcd123.mongodb.net/alm_db?retryWrites=true&w=majority"
   ```

2. Install the chart:
   ```bash
   helm install alm ./helm --values helm/values.yaml
   ```

## Step 6: Verify Connection

Run the test script:
```powershell
cd d:\Somajit\alm_extraction_tool
python scripts/test_atlas_connection.py
```

Expected output:
```
✓ Connected to MongoDB Atlas successfully
✓ Database initialized with sample data
✓ Domains: ['DomainA', 'DomainB']
✓ Projects: ['Project1', 'Project2']
✓ Defects: 2 records
```

## Troubleshooting

### Connection Timeout
- **Cause**: IP address not whitelisted.
- **Fix**: Go to **Network Access** and add your IP address or `0.0.0.0/0`.

### Authentication Failed
- **Cause**: Wrong username or password.
- **Fix**: Double-check credentials in the Atlas UI under **Database Access**.

### DNS Resolution Error
- **Cause**: `dnspython` not installed (required for `mongodb+srv://` URIs).
- **Fix**: Install it:
  ```powershell
  pip install dnspython
  ```

### Cluster Not Ready
- **Cause**: Atlas cluster still starting up.
- **Fix**: Wait 2-3 minutes for the cluster to fully initialize, then retry.

## Security Best Practices

1. **Never hardcode credentials** in code or version control. Use environment variables or secrets (Docker secrets, Kubernetes Secrets).
2. **Use strong passwords**: Minimum 8 characters, mix of upper/lower/numbers/symbols.
3. **Restrict IP whitelist**: Use specific CIDR blocks (e.g., your office IP or VPN range) instead of `0.0.0.0/0`.
4. **Use least-privilege users**: For production, create DB users with only `readWrite` on specific databases.
5. **Enable encryption**: Atlas provides encryption at rest and in transit by default; keep them enabled.
6. **Rotate credentials regularly**: Change DB passwords quarterly or after employee changes.

## Next Steps

- Run the frontend and test the full login → domain → project → data flow.
- Integrate with MongoDB Atlas for production deployments.
- Set up automated backups in the Atlas UI (**Backup** section).
