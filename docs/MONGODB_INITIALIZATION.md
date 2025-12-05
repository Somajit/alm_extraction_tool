# MongoDB Initialization

## Overview

MongoDB initialization script that creates all required collections and indexes for the ReleaseCraft application. Runs automatically during deployment when MongoDB data is cleaned.

## Files

- **backend/app/init_mongo.py** - Python script that creates collections and indexes
- **scripts/init-mongo.bat** - Windows batch script to run initialization

## Collections Created (18 total)

### Authentication & User Management (1)
- `user_credentials` - User login credentials and session info

### Domain & Project (2)
- `domains` - ALM domains
- `projects` - ALM projects

### TestPlan Entities (6)
- `testplan_folders` - Test plan folder hierarchy
- `testplan_tests` - Test cases
- `testplan_test_design_steps` - Test design steps
- `testplan_folder_attachments` - Folder attachments
- `testplan_test_attachments` - Test attachments
- `testplan_test_design_step_attachments` - Design step attachments

### TestLab Entities (5)
- `testlab_releases` - Releases
- `testlab_release_cycles` - Release cycles
- `testlab_testsets` - Test sets
- `testlab_testruns` - Test runs/executions
- `testlab_testset_attachments` - Test set attachments

### Defects (2)
- `defects` - Defect records
- `defect_attachments` - Defect attachments

### Cache & Support (2)
- `attachment_cache` - Downloaded attachment files
- `extraction_jobs` - Background extraction job tracking

## Indexes Created (36 total)

Each collection has:
- **Unique index** on `(user, id)` or `(user, id, parent_id)` for entity uniqueness
- **Regular index** on `(user)` for user-specific queries
- **Regular index** on `(user, parent_id)` for parent-child queries

Special indexes:
- `user_credentials`: unique on `user`, indexes on `username` and `logged_in`
- `attachment_cache`: unique on `(domain, project, attachment_id)`
- `extraction_jobs`: unique on `(user, job_id)`, index on `(user, status)`

## Usage

### Automatic (via deploy-all.bat)

When running `deploy-all.bat`, if you choose to clean MongoDB data, the initialization runs automatically:

```batch
scripts\deploy-all.bat
```

1. Select MongoDB type (local/atlas)
2. Choose "yes" when asked to clean MongoDB data
3. Script automatically runs initialization after deployment

### Manual Initialization

**For Local MongoDB:**
```batch
scripts\init-mongo.bat local
```

**For MongoDB Atlas:**
```batch
scripts\init-mongo.bat atlas "mongodb+srv://user:pass@cluster.mongodb.net/releasecraftdb"
```

**Via Docker (local only):**
```batch
docker exec backend python -m app.init_mongo
```

## Output

Successful initialization shows:
```
============================================================
ReleaseCraft MongoDB Initialization
============================================================

Connecting to MongoDB: mongodb://mongo:27017/releasecraftdb
Found X existing collections
✓ Created collection: domains
✓ Created collection: projects
...

Created 14 new collections

Creating indexes...
✓ Created unique index on user_credentials: [('user', 1)]
✓ Created regular index on user_credentials: [('username', 1)]
...

Created/verified 36 indexes

Database initialized successfully!
Database: releasecraftdb
Collections: 18
Data Size: 0.01 MB
Storage Size: 0.15 MB

============================================================
✓ MongoDB initialization completed successfully
============================================================
```

## Verification

**Check collections:**
```batch
docker exec mongo mongosh releasecraftdb --quiet --eval "db.getCollectionNames().sort()"
```

**Check indexes on a collection:**
```batch
docker exec mongo mongosh releasecraftdb --quiet --eval "db.user_credentials.getIndexes()"
```

**Check database stats:**
```batch
scripts\show-detailed-mongo-stats.bat local
```

## Index Benefits

Indexes improve query performance for:
- ✅ User-specific data queries (all collections indexed on `user`)
- ✅ Entity uniqueness checks (unique indexes on `user + id`)
- ✅ Parent-child hierarchy queries (indexes on `user + parent_id`)
- ✅ Login status checks (index on `logged_in`)
- ✅ Attachment caching (unique index on `domain + project + attachment_id`)
- ✅ Job status tracking (index on `user + status`)

## Notes

- Script is **idempotent** - safe to run multiple times
- Existing collections are not dropped
- Existing indexes are not recreated (MongoDB handles duplicates)
- No sample data is inserted (use `initialize-sample-data.bat` for that)
- Collections are created empty with proper indexes ready for data
