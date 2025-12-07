"""
Initialize admin user in MongoDB
Creates or updates admin user with default password
"""
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime

async def init_admin_user():
    """Create or update admin user in MongoDB"""
    # Get MongoDB URI from environment
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    db_name = os.getenv('MONGODB_DATABASE', 'almdb')
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_uri)
        db = client[db_name]
        
        # Check if admin user exists
        admin_user = await db.users.find_one({"username": "admin"})
        
        admin_data = {
            "username": "admin",
            "password": "admin123",  # Plain text for now, can be hashed later
            "email": "admin@releasecraft.com",
            "role": "admin",
            "project_groups": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if admin_user:
            # Update existing admin user
            await db.users.update_one(
                {"username": "admin"},
                {"$set": {
                    "password": "admin123",
                    "email": "admin@releasecraft.com",
                    "role": "admin",
                    "updated_at": datetime.utcnow()
                }}
            )
            print("✓ Admin user updated successfully")
        else:
            # Create new admin user
            await db.users.insert_one(admin_data)
            print("✓ Admin user created successfully")
        
        # Close connection
        client.close()
        return True
        
    except Exception as e:
        print(f"✗ Error initializing admin user: {e}")
        return False

if __name__ == "__main__":
    # Run async function
    result = asyncio.run(init_admin_user())
    sys.exit(0 if result else 1)
