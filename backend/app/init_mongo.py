"""
MongoDB Initialization Script

Creates database and collections for ReleaseCraft application.
Executed during deployment when clean mongo data is requested.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017/releasecraftdb')

# Collection names
COLLECTIONS = [
    # Authentication & User Management
    "user_credentials",
    
    # Domain & Project
    "domains",
    "projects",
    
    # TestPlan entities
    "testplan_folders",
    "testplan_tests",
    "testplan_test_design_steps",
    "testplan_folder_attachments",
    "testplan_test_attachments",
    "testplan_test_design_step_attachments",
    
    # TestLab entities
    "testlab_releases",
    "testlab_release_cycles",
    "testlab_testsets",
    "testlab_testruns",
    "testlab_testset_attachments",
    
    # Defects
    "defects",
    "defect_attachments",
    
    # Cache & Support
    "attachment_cache",
    "extraction_jobs"
]

# Indexes for performance
INDEXES = {
    "user_credentials": [
        {"keys": [("user", 1)], "unique": True},
        {"keys": [("username", 1)]},
        {"keys": [("logged_in", 1)]}
    ],
    "domains": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1)]}
    ],
    "projects": [
        {"keys": [("user", 1), ("id", 1), ("parent_id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testplan_folders": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testplan_tests": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testplan_test_design_steps": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testplan_folder_attachments": [
        {"keys": [("user", 1), ("id", 1), ("parent_id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testplan_test_attachments": [
        {"keys": [("user", 1), ("id", 1), ("parent_id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testplan_test_design_step_attachments": [
        {"keys": [("user", 1), ("id", 1), ("parent_id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testlab_releases": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1)]}
    ],
    "testlab_release_cycles": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testlab_testsets": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testlab_testruns": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "testlab_testset_attachments": [
        {"keys": [("user", 1), ("id", 1), ("parent_id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "defects": [
        {"keys": [("user", 1), ("id", 1)], "unique": True},
        {"keys": [("user", 1)]}
    ],
    "defect_attachments": [
        {"keys": [("user", 1), ("id", 1), ("parent_id", 1)], "unique": True},
        {"keys": [("user", 1), ("parent_id", 1)]}
    ],
    "attachment_cache": [
        {"keys": [("domain", 1), ("project", 1), ("attachment_id", 1)], "unique": True}
    ],
    "extraction_jobs": [
        {"keys": [("user", 1), ("job_id", 1)], "unique": True},
        {"keys": [("user", 1), ("status", 1)]}
    ]
}


async def init_mongodb():
    """Initialize MongoDB database and collections with indexes."""
    print(f"Connecting to MongoDB: {MONGO_URI}")
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client.get_default_database()
    
    try:
        # Get existing collections
        existing_collections = await db.list_collection_names()
        print(f"Found {len(existing_collections)} existing collections")
        
        # Create collections if they don't exist
        created_count = 0
        for collection_name in COLLECTIONS:
            if collection_name not in existing_collections:
                await db.create_collection(collection_name)
                print(f"✓ Created collection: {collection_name}")
                created_count += 1
            else:
                print(f"  Collection already exists: {collection_name}")
        
        print(f"\nCreated {created_count} new collections")
        
        # Create indexes
        print("\nCreating indexes...")
        index_count = 0
        for collection_name, indexes in INDEXES.items():
            collection = db[collection_name]
            for index_spec in indexes:
                try:
                    keys = index_spec["keys"]
                    unique = index_spec.get("unique", False)
                    await collection.create_index(keys, unique=unique)
                    index_type = "unique" if unique else "regular"
                    print(f"✓ Created {index_type} index on {collection_name}: {keys}")
                    index_count += 1
                except Exception as e:
                    # Index might already exist
                    if "already exists" not in str(e).lower():
                        print(f"  Warning: Could not create index on {collection_name}: {e}")
        
        print(f"\nCreated/verified {index_count} indexes")
        
        # Verify database setup
        stats = await db.command("dbStats")
        print(f"\nDatabase initialized successfully!")
        print(f"Database: {stats.get('db')}")
        print(f"Collections: {stats.get('collections')}")
        print(f"Data Size: {stats.get('dataSize', 0) / 1024 / 1024:.2f} MB")
        print(f"Storage Size: {stats.get('storageSize', 0) / 1024 / 1024:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing MongoDB: {e}")
        return False
        
    finally:
        client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("ReleaseCraft MongoDB Initialization")
    print("=" * 60)
    print()
    
    success = asyncio.run(init_mongodb())
    
    print()
    print("=" * 60)
    if success:
        print("✓ MongoDB initialization completed successfully")
    else:
        print("❌ MongoDB initialization failed")
    print("=" * 60)
    
    exit(0 if success else 1)
