# ReleaseCraft Deployment - MongoDB Configuration

## Overview
The deployment script now supports both **Local MongoDB** (Docker container) and **MongoDB Atlas** (Cloud).

## Deployment Flow

### 1. MongoDB Selection
When you run `scripts\deploy-all.bat`, it will ask:
```
Choose MongoDB deployment type:
  1. Local MongoDB (Docker container)
  2. MongoDB Atlas (Cloud)

Enter choice (1 or 2):
```

- **Option 1 (Local)**: Creates a local MongoDB container via docker-compose
- **Option 2 (Atlas)**: Prompts for your Atlas connection string

### 2. Configuration
The script automatically creates `backend\.env.local` with the correct MongoDB connection:
- **Local**: `MONGO_URI=mongodb://localhost:27017/releasecraftdb`
- **Atlas**: `MONGO_URI=<your-atlas-connection-string>`

### 3. MongoDB Statistics
Shows detailed statistics of your current MongoDB data:
```
============================================
MongoDB Statistics - releasecraftdb
============================================

Database: releasecraftdb
Collections: 5
Total Documents: 10
Data Size: 0.02 MB
Storage Size: 0.05 MB

Collection Details:
-------------------------------------------
users: 1 documents
domains: 2 documents
projects: 3 documents
tree_cache: 0 documents
defects: 0 documents
user_credentials: 1 documents
domains_extracted: 0 documents
projects_extracted: 0 documents
testplan_folders: 0 documents
defects_extracted: 0 documents
entities: 0 documents
attachments: 0 documents
attachment_files: 0 documents
attachment_cache: 0 documents
testplan_test_details: 0 documents
testplan_extraction_results: 0 documents
testlab_testset_details: 0 documents
testlab_extraction_results: 0 documents
defect_details: 0 documents
```

### 4. Data Cleanup (Optional)
If MongoDB has existing data, the script asks:
```
Do you want to clean all MongoDB data? (yes/no):
```

- **yes**: Drops all collections and shows updated stats (Collections: 0)
- **no**: Keeps existing data

### 5. Deployment
The script then:
- Stops and removes all containers
- Removes all ReleaseCraft images
- Sets up MongoDB (if local)
- Deploys Mock ALM server
- Builds and starts all services

### 6. Final Statistics
After deployment, shows MongoDB stats again:
- Should show **Collections: 0** if you cleaned data
- **No data is auto-initialized** during deployment

## Collection Types

The application uses these MongoDB collections:

### Authentication & User Management
- **users**: Application users (basic authentication)
- **user_credentials**: ALM credentials and session management

### ALM Domain & Project Data
- **domains**: Local domains list (from sample data)
- **projects**: Local projects list (from sample data)
- **tree_cache**: Tree structure cache (TestPlan/TestLab hierarchy)
- **defects**: Local defects list (from sample data)

### ALM Extracted Data
- **domains_extracted**: Domains extracted from ALM server
- **projects_extracted**: Projects extracted from ALM server
- **testplan_folders**: Test plan folder hierarchy from ALM
- **defects_extracted**: Defects extracted from ALM server

### Entity & Attachment Storage
- **entities**: Generic entity storage (folders, tests, releases, etc.)
- **attachments**: Attachment metadata for all entity types
- **attachment_files**: Attachment file content for all entity types
- **attachment_cache**: Cached attachment downloads from ALM server

### Extraction Results
- **testplan_test_details**: Test case detailed information
- **testplan_extraction_results**: TestPlan extraction results and status
- **testlab_testset_details**: Test set detailed information
- **testlab_extraction_results**: TestLab extraction results and status
- **defect_details**: Defect detailed information

## Sample Data

After deployment, the database is **empty** by default. To initialize sample data:

```bash
scripts\initialize-sample-data.bat
```

This creates:
- 1 user (admin/admin123)
- 2 domains (DomainA, DomainB)
- 3 projects (Project1, Project2, ProjectX)
- Sample test plans and labs
- 2 defects

## Manual MongoDB Stats

To check MongoDB statistics anytime:

### Local MongoDB
```bash
scripts\show-detailed-mongo-stats.bat local
```

### MongoDB Atlas
```bash
scripts\show-detailed-mongo-stats.bat atlas "mongodb+srv://user:pass@cluster.mongodb.net/releasecraftdb"
```

## Verification

After deployment with clean data:
1. ✅ Collections should be 0
2. ✅ Total Documents should be 0
3. ✅ All collection details should show "0 documents"
4. ✅ Application should be accessible at http://localhost:5173
5. ✅ You can register a new user or initialize sample data

## Container List

### Local MongoDB Deployment
- mongo (MongoDB 6.0)
- mock-alm (Mock ALM Server)
- backend (FastAPI)
- frontend (React + Nginx)

### MongoDB Atlas Deployment
- mock-alm (Mock ALM Server)
- backend (FastAPI)
- frontend (React + Nginx)

## Notes

- The deployment **never auto-initializes** data
- Data is only created when:
  - You register users via the UI
  - You extract data from ALM
  - You manually run `initialize-sample-data.bat`
- The backend connects to MongoDB but doesn't create sample data on startup
