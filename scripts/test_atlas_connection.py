#!/usr/bin/env python3
"""
Test and initialize MongoDB Atlas connection.
Verifies connectivity and seeds sample data if needed.
"""
import asyncio
import os
import sys
from pathlib import Path

# Fix Unicode encoding on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    sys.stdout.reconfigure(encoding="utf-8")

from motor.motor_asyncio import AsyncIOMotorClient

# Load .env.atlas or .env.local if they exist
for env_name in [".env.local", ".env.atlas"]:
    env_file = Path(__file__).parent.parent / "backend" / env_name
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    os.environ[key.strip()] = value.strip()
        break

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/almdb')

async def test_connection():
    """Test Atlas connection and initialize sample data."""
    print(f"📡 Connecting to MongoDB Atlas...")
    print(f"   URI: {MONGO_URI[:50]}...")
    
    try:
        client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client.get_default_database()
        
        # Test connection
        await db.command("ping")
        print("✓ Connected to MongoDB Atlas successfully")
        
        # Check/create collections
        collections = await db.list_collection_names()
        
        # Initialize sample data if empty
        if "users" not in collections or await db.users.count_documents({}) == 0:
            print("📝 Initializing sample data...")
            
            await db.users.delete_many({})
            await db.domains.delete_many({})
            await db.projects.delete_many({})
            await db.tree_cache.delete_many({})
            await db.defects.delete_many({})
            
            await db.users.insert_one({
                "username": "admin",
                "password": "admin123"
            })
            print("✓ Created user: admin / admin123")
            
            await db.domains.insert_many([
                {"name": "DomainA"},
                {"name": "DomainB"}
            ])
            print("✓ Created domains: DomainA, DomainB")
            
            await db.projects.insert_many([
                {"name": "Project1", "domain": "DomainA"},
                {"name": "Project2", "domain": "DomainA"},
                {"name": "ProjectX", "domain": "DomainB"}
            ])
            print("✓ Created projects: Project1, Project2, ProjectX")
            
            await db.tree_cache.insert_many([
                {"type": "testplan", "project": "Project1", "tree": [
                    {"id": "tp1", "label": "Root Plan", "children": [
                        {"id": "tp1-1", "label": "Suite 1"},
                        {"id": "tp1-2", "label": "Suite 2"}
                    ]}
                ]},
                {"type": "testlab", "project": "Project1", "tree": [
                    {"id": "tl1", "label": "Execution Root", "children": [
                        {"id": "tl1-1", "label": "Cycle 1"}
                    ]}
                ]}
            ])
            print("✓ Created test plans and labs")
            
            await db.defects.insert_many([
                {"id": "D-1", "summary": "Crash on load", "status": "Open", "priority": "High", "project": "Project1"},
                {"id": "D-2", "summary": "UI glitch", "status": "Closed", "priority": "Low", "project": "Project1"}
            ])
            print("✓ Created defects: 2 records")
        else:
            user_count = await db.users.count_documents({})
            domain_count = await db.domains.count_documents({})
            project_count = await db.projects.count_documents({})
            defect_count = await db.defects.count_documents({})
            
            print(f"✓ Database already initialized")
            print(f"   Users: {user_count}")
            print(f"   Domains: {domain_count}")
            print(f"   Projects: {project_count}")
            print(f"   Defects: {defect_count}")
        
        # Verify data
        domains = await db.domains.find({}).to_list(None)
        projects = await db.projects.find({}).to_list(None)
        defects = await db.defects.find({}).to_list(None)
        
        domain_names = [d['name'] for d in domains]
        project_names = [p['name'] for p in projects]
        
        print(f"\n📊 Database Summary:")
        print(f"   Domains: {domain_names}")
        print(f"   Projects: {project_names}")
        print(f"   Defects: {len(defects)} records")
        
        print(f"\n✅ Atlas setup complete!")
        print(f"\n🚀 Quick next steps:")
        print(f"   1. Start the backend: cd backend && uvicorn app.main:app --reload")
        print(f"   2. Start the frontend: cd frontend && npm run dev")
        print(f"   3. Open http://localhost:5173")
        print(f"   4. Login with: admin / admin123")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Check your MONGO_URI environment variable")
        print(f"   2. Verify IP whitelist in Atlas Network Access")
        print(f"   3. Ensure dnspython is installed: pip install dnspython")
        print(f"   4. Check cluster status in Atlas UI")
        exit(1)

if __name__ == '__main__':
    asyncio.run(test_connection())
