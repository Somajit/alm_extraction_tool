# Sample Data Scripts

This directory contains scripts to manage sample data in MongoDB.

## Available Scripts

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

## Requirements

```bash
pip install motor pymongo
```

Or install from backend requirements:
```bash
pip install -r ../backend/requirements.txt
```
