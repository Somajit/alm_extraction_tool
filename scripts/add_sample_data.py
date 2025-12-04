"""
Script to add sample data to MongoDB for ALM Extraction Tool
Usage: python add_sample_data.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/alm_db')

async def add_users(db):
    """Add sample users"""
    users = [
        {"username": "admin", "password": "admin123"},
        {"username": "testuser", "password": "test123"},
        {"username": "developer", "password": "dev123"},
    ]
    
    print("Adding users...")
    for user in users:
        existing = await db.users.find_one({"username": user["username"]})
        if not existing:
            await db.users.insert_one(user)
            print(f"  ✓ Created user: {user['username']}")
        else:
            print(f"  - User already exists: {user['username']}")


async def add_domains(db):
    """Add sample domains"""
    domains = [
        {"name": "DomainA", "description": "First test domain"},
        {"name": "DomainB", "description": "Second test domain"},
        {"name": "DomainC", "description": "Third test domain"},
    ]
    
    print("\nAdding domains...")
    for domain in domains:
        existing = await db.domains.find_one({"name": domain["name"]})
        if not existing:
            await db.domains.insert_one(domain)
            print(f"  ✓ Created domain: {domain['name']}")
        else:
            print(f"  - Domain already exists: {domain['name']}")


async def add_projects(db):
    """Add sample projects"""
    projects = [
        {"name": "Project1", "domain": "DomainA", "description": "First project in Domain A"},
        {"name": "Project2", "domain": "DomainA", "description": "Second project in Domain A"},
        {"name": "Project3", "domain": "DomainA", "description": "Third project in Domain A"},
        {"name": "ProjectX", "domain": "DomainB", "description": "Project X in Domain B"},
        {"name": "ProjectY", "domain": "DomainB", "description": "Project Y in Domain B"},
        {"name": "ProjectAlpha", "domain": "DomainC", "description": "Alpha project in Domain C"},
    ]
    
    print("\nAdding projects...")
    for project in projects:
        existing = await db.projects.find_one({"name": project["name"], "domain": project["domain"]})
        if not existing:
            await db.projects.insert_one(project)
            print(f"  ✓ Created project: {project['name']} (Domain: {project['domain']})")
        else:
            print(f"  - Project already exists: {project['name']}")


async def add_test_trees(db):
    """Add sample test plan and test lab trees"""
    trees = [
        {
            "project": "Project1",
            "type": "testplan",
            "tree": [
                {
                    "id": "tp1",
                    "label": "Root Test Plan",
                    "children": [
                        {"id": "tp1-1", "label": "Functional Tests", "children": [
                            {"id": "tp1-1-1", "label": "Login Tests"},
                            {"id": "tp1-1-2", "label": "User Management Tests"},
                        ]},
                        {"id": "tp1-2", "label": "Integration Tests", "children": [
                            {"id": "tp1-2-1", "label": "API Tests"},
                            {"id": "tp1-2-2", "label": "Database Tests"},
                        ]},
                    ]
                }
            ]
        },
        {
            "project": "Project1",
            "type": "testlab",
            "tree": [
                {
                    "id": "tl1",
                    "label": "Test Lab Root",
                    "children": [
                        {"id": "tl1-1", "label": "Sprint 1", "children": [
                            {"id": "tl1-1-1", "label": "Test Set 1"},
                            {"id": "tl1-1-2", "label": "Test Set 2"},
                        ]},
                        {"id": "tl1-2", "label": "Sprint 2", "children": [
                            {"id": "tl1-2-1", "label": "Test Set 3"},
                        ]},
                    ]
                }
            ]
        },
        {
            "project": "Project2",
            "type": "testplan",
            "tree": [
                {
                    "id": "tp2",
                    "label": "Project 2 Test Plan",
                    "children": [
                        {"id": "tp2-1", "label": "Smoke Tests"},
                        {"id": "tp2-2", "label": "Regression Tests"},
                    ]
                }
            ]
        },
    ]
    
    print("\nAdding test trees...")
    for tree_doc in trees:
        existing = await db.tree.find_one({"project": tree_doc["project"], "type": tree_doc["type"]})
        if not existing:
            await db.tree.insert_one(tree_doc)
            print(f"  ✓ Created {tree_doc['type']} tree for {tree_doc['project']}")
        else:
            print(f"  - Tree already exists: {tree_doc['type']} for {tree_doc['project']}")


async def add_defects(db):
    """Add sample defects"""
    defects = [
        {
            "id": "DEF-001",
            "summary": "Login page not loading",
            "status": "Open",
            "priority": "High",
            "project": "Project1",
            "severity": "Critical",
            "assignedTo": "developer",
            "description": "Users cannot access the login page"
        },
        {
            "id": "DEF-002",
            "summary": "Search results are incorrect",
            "status": "Fixed",
            "priority": "Medium",
            "project": "Project1",
            "severity": "Major",
            "assignedTo": "testuser",
            "description": "Search functionality returns wrong results"
        },
        {
            "id": "DEF-003",
            "summary": "UI alignment issue on mobile",
            "status": "Open",
            "priority": "Low",
            "project": "Project1",
            "severity": "Minor",
            "assignedTo": "developer",
            "description": "Button alignment is off on mobile devices"
        },
        {
            "id": "DEF-004",
            "summary": "API timeout error",
            "status": "Open",
            "priority": "High",
            "project": "Project2",
            "severity": "Critical",
            "assignedTo": "admin",
            "description": "API calls timing out after 30 seconds"
        },
        {
            "id": "DEF-005",
            "summary": "Data export functionality broken",
            "status": "Fixed",
            "priority": "Medium",
            "project": "Project2",
            "severity": "Major",
            "assignedTo": "developer",
            "description": "Export to CSV not working"
        },
    ]
    
    print("\nAdding defects...")
    for defect in defects:
        existing = await db.defects.find_one({"id": defect["id"]})
        if not existing:
            await db.defects.insert_one(defect)
            print(f"  ✓ Created defect: {defect['id']} - {defect['summary']}")
        else:
            print(f"  - Defect already exists: {defect['id']}")


async def main():
    print("=" * 60)
    print("MongoDB Sample Data Loader")
    print("=" * 60)
    print(f"\nConnecting to: {MONGO_URI}")
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.get_default_database()
    
    try:
        # Test connection
        await client.server_info()
        print("✓ Connected successfully\n")
        
        # Add data
        await add_users(db)
        await add_domains(db)
        await add_projects(db)
        await add_test_trees(db)
        await add_defects(db)
        
        # Show summary
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        users_count = await db.users.count_documents({})
        domains_count = await db.domains.count_documents({})
        projects_count = await db.projects.count_documents({})
        trees_count = await db.tree.count_documents({})
        defects_count = await db.defects.count_documents({})
        
        print(f"Total users: {users_count}")
        print(f"Total domains: {domains_count}")
        print(f"Total projects: {projects_count}")
        print(f"Total trees: {trees_count}")
        print(f"Total defects: {defects_count}")
        
        print("\n✅ Data loading complete!")
        print("\nYou can now:")
        print("  1. Login with any user: admin/admin123, testuser/test123, developer/dev123")
        print("  2. Select from available domains and projects")
        print("  3. View test plans, test labs, and defects")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    finally:
        client.close()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
