import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import motor.motor_asyncio
from typing import List, Optional, Dict, Any
import asyncio
from app.alm import ALM

# Configure logging
log_dir = Path(__file__).parent.parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info('Backend service starting...')

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017/almdb')
DEFAULT_ORIGINS = [os.environ.get('CORS_ORIGINS', 'http://localhost:5173')]
ALM_ENCRYPTION_KEY = os.environ.get('ALM_ENCRYPTION_KEY', '')

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client.get_default_database()
attachments_collection = db['attachment_cache']

# Get encryption key
encryption_key = os.environ.get('ALM_ENCRYPTION_KEY', '')

# Initialize ALM client with new signature
alm_client = ALM(db=db, encryption_key=encryption_key if encryption_key else None)

app = FastAPI(title='ALM Extraction Tool API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEFAULT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    ok: bool
    message: Optional[str] = None


# New request models for rationalized API
class AuthenticateRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    domain: str
    project: str
    project_group: str = "default"


class LogoutRequest(BaseModel):
    username: str


class ExtractRequest(BaseModel):
    node_type: str
    node_id: str


async def cache_attachments(
    username: str,
    domain: str,
    project: str,
    attachments: List[Dict[str, Any]]
):
    """
    Download and cache attachments in MongoDB.
    Returns the same attachments list with cached flag added.
    """
    for attachment in attachments:
        attachment_id = str(attachment.get('id'))
        filename = attachment.get('name', f'attachment_{attachment_id}')
        
        cache_key = f"{domain}_{project}_{attachment_id}"
        
        # Check if already cached
        cached = await attachments_collection.find_one({"_id": cache_key})
        if cached:
            attachment['cached'] = True
            continue
        
        try:
            # Download from ALM
            content = await alm_client.download_attachment(
                username, domain, project, attachment_id
            )
            
            if content:
                # Store in MongoDB
                await attachments_collection.update_one(
                    {"_id": cache_key},
                    {
                        "$set": {
                            "domain": domain,
                            "project": project,
                            "attachment_id": attachment_id,
                            "filename": filename,
                            "content": content,
                            "downloaded_at": datetime.utcnow()
                        }
                    },
                    upsert=True
                )
                attachment['cached'] = True
        except Exception as e:
            print(f"Failed to cache attachment {attachment_id}: {e}")
            attachment['cached'] = False
    
    return attachments


# ============================================================================
# NEW RATIONALIZED API ENDPOINTS
# Following pattern: Frontend → Backend → ALM → Store MongoDB → Query MongoDB → Return
# ============================================================================

@app.post('/api/authenticate')
async def api_authenticate(request: AuthenticateRequest):
    """
    Authenticate with ALM server (username/password only).
    For admin users, verify against stored password in MongoDB without ALM authentication.
    
    Flow:
    1. Check if user is admin
    2. If admin: Verify password against MongoDB, skip ALM authentication
    3. If regular user: Call ALM authentication endpoints
    4. Store/query credentials from MongoDB
    5. Return authentication result
    """
    try:
        # Check if this is an admin user
        admin_user = await db.users.find_one({"username": request.username, "role": "admin"})
        
        if admin_user:
            # Admin authentication - verify against stored password
            stored_password = admin_user.get("password", "")
            if stored_password == request.password:
                logger.info(f"Admin user {request.username} authenticated successfully")
                return {
                    "success": True,
                    "message": "Admin authentication successful",
                    "username": request.username
                }
            else:
                logger.warning(f"Admin authentication failed for {request.username}")
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        # Regular user - authenticate with ALM
        result = await alm_client.authenticate(request.username, request.password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/logs/{service}')
async def get_logs(service: str, lines: int = 100):
    """
    Get recent logs from a service.
    Services: backend, mock-alm, frontend
    """
    logger.info(f"Fetching {lines} lines from {service} logs")
    
    log_files = {
        'backend': log_dir / 'backend.log',
        'mock-alm': log_dir / 'mock-alm.log',
        'frontend': log_dir / 'frontend.log'
    }
    
    if service not in log_files:
        raise HTTPException(status_code=400, detail=f"Invalid service. Choose from: {list(log_files.keys())}")
    
    log_file = log_files[service]
    if not log_file.exists():
        return {"logs": [], "message": f"Log file not found for {service}"}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {"logs": recent_lines, "total": len(all_lines)}
    except Exception as e:
        logger.error(f"Error reading {service} logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/logs/{service}/stream')
async def stream_logs(service: str, level: Optional[str] = None):
    """
    Stream logs from a service in real-time (SSE).
    Optional level parameter filters logs by: ERROR, WARNING, INFO, DEBUG
    """
    logger.info(f"Starting log stream for {service} (level filter: {level})")
    
    log_files = {
        'backend': log_dir / 'backend.log',
        'mock-alm': log_dir / 'mock-alm.log',
        'frontend': log_dir / 'frontend.log'
    }
    
    if service not in log_files:
        raise HTTPException(status_code=400, detail=f"Invalid service. Choose from: {list(log_files.keys())}")
    
    # Validate level parameter
    valid_levels = ['ERROR', 'WARNING', 'INFO', 'DEBUG']
    if level and level.upper() not in valid_levels:
        raise HTTPException(status_code=400, detail=f"Invalid level. Choose from: {valid_levels}")
    
    level_filter = level.upper() if level else None
    
    log_file = log_files[service]
    
    def should_include_line(line: str) -> bool:
        """Filter log line by level."""
        if not level_filter:
            return True
        # Check if line contains the log level
        # Format: "2024-12-07 10:30:45 - module - LEVEL - message"
        return f" - {level_filter} - " in line or f"[{level_filter}]" in line
    
    async def log_generator():
        # Send last 50 lines first (filtered)
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    filtered_lines = [line for line in lines[-50:] if should_include_line(line)]
                    for line in filtered_lines:
                        yield f"data: {line}\n\n"
            except Exception as e:
                logger.error(f"Error reading initial logs: {e}")
        
        # Then stream new lines (filtered)
        last_size = log_file.stat().st_size if log_file.exists() else 0
        
        while True:
            try:
                if log_file.exists():
                    current_size = log_file.stat().st_size
                    if current_size > last_size:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            f.seek(last_size)
                            new_lines = f.readlines()
                            for line in new_lines:
                                if should_include_line(line):
                                    yield f"data: {line}\n\n"
                        last_size = current_size
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error streaming logs: {e}")
                await asyncio.sleep(1)
    
    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get('/api/get_domains')
async def api_get_domains(username: str):
    """
    Fetch and store available domains from ALM.
    
    Flow:
    1. Call ALM /rest/domains endpoint
    2. Parse and store in domains collection
    3. Query domains from MongoDB
    4. Transform to display format
    5. Return from MongoDB
    """
    try:
        result = await alm_client.fetch_and_store_domains(username)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/get_projects')
async def api_get_projects(username: str, domain: str):
    """
    Fetch and store projects for a domain from ALM.
    
    Flow:
    1. Call ALM /rest/domains/{domain}/projects endpoint
    2. Parse and store in projects collection
    3. Query projects from MongoDB
    4. Transform to display format
    5. Return from MongoDB
    """
    try:
        result = await alm_client.fetch_and_store_projects(username, domain)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/login')
async def api_login(request: LoginRequest):
    """
    Complete login after domain/project selection, load initial tree data.
    
    Flow:
    1. Store domain/project/project_group in user_credentials
    2. Fetch root folders from ALM → store with project_group → query from MongoDB
    3. Fetch releases from ALM → store with project_group → query from MongoDB
    4. Fetch defects from ALM → store with project_group → query from MongoDB
    5. Mark user as logged_in=true
    6. Return counts from MongoDB queries
    """
    try:
        # Store domain/project/project_group selection
        await db.user_credentials.update_one(
            {"user": request.username},
            {"$set": {
                "domain": request.domain,
                "project": request.project,
                "project_group": request.project_group,
                "logged_in": False  # Will be set to True after data load
            }},
            upsert=True
        )
        
        # Fetch and store root folders with project_group
        root_folders_result = await alm_client.fetch_and_store_root_folders(
            request.username, request.domain, request.project, request.project_group
        )
        
        # Fetch and store releases with project_group
        releases_result = await alm_client.fetch_and_store_releases(
            request.username, request.domain, request.project, request.project_group
        )
        
        # Fetch and store defects with project_group
        defects_result = await alm_client.fetch_and_store_defects(
            request.username, request.domain, request.project, request.project_group
        )
        
        # Mark user as logged in
        await db.user_credentials.update_one(
            {"user": request.username},
            {"$set": {"logged_in": True}}
        )
        
        # Query all data from MongoDB (filtered by user AND project_group)
        # TestPlan root folders
        testplan_folders = []
        cursor = db.testplan_folders.find({
            "user": request.username, 
            "project_group": request.project_group,
            "parent_id": "0"
        })
        async for f in cursor:
            testplan_folders.append({
                "id": f.get("id"),
                "name": f.get("name"),
                "type": "folder"
            })
        
        # TestLab releases
        testlab_releases = []
        cursor = db.testlab_releases.find({
            "user": request.username,
            "project_group": request.project_group
        })
        async for r in cursor:
            testlab_releases.append({
                "id": r.get("id"),
                "name": r.get("name"),
                "type": "release"
            })
        
        # Defects
        defects = []
        cursor = db.defects.find({
            "user": request.username,
            "project_group": request.project_group
        }).limit(100)
        async for d in cursor:
            # Extract key fields for display (fields are stored at top level)
            defect_data = {
                "id": d.get("id"),
                "name": d.get("name"),
                "status": d.get("status"),
                "severity": d.get("severity"),
                "priority": d.get("priority"),
                "detected-by": d.get("detected-by"),
                "owner": d.get("owner"),
                "creation-time": d.get("creation-time")
            }
            defects.append(defect_data)
        
        return {
            "success": True,
            "testplan": testplan_folders,
            "testlab": testlab_releases,
            "defects": defects
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/logout')
async def api_logout(request: LogoutRequest):
    """
    Logout from ALM server.
    
    Flow:
    1. Call ALM /authentication-point/logout
    2. Clear cookies from ALM client
    3. Update user_credentials set logged_in=false
    """
    try:
        result = await alm_client.logout(request.username)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@app.post('/api/users/register')
async def register_user(username: str, password: str, project_group: str = "default"):
    """Register a new user after successful ALM authentication."""
    logger.info(f"Registering new user: {username} in project group: {project_group}")
    
    # Check if user already exists
    existing = await db.users.find_one({"username": username})
    if existing:
        return {"success": True, "message": "User already exists", "role": existing.get("role", "user")}
    
    # Determine role
    role = "admin" if username.lower() == "admin" else "user"
    
    new_user = {
        "username": username,
        "password": password,
        "email": f"{username}@example.com",
        "role": role,
        "project_groups": [project_group] if project_group else [],
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(new_user)
    logger.info(f"New user registered: {username} with role: {role}")
    
    return {"success": True, "message": "User registered", "role": role}


@app.get('/api/users/profile')
async def get_user_profile(username: str):
    """Get user profile with role and project groups."""
    logger.info(f"Fetching profile for user: {username}")
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "username": user.get("username"),
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "project_groups": user.get("project_groups", []),
        "created_at": user.get("created_at")
    }


@app.post('/api/users/project-groups')
async def add_user_project_group(username: str, project_group: str):
    """Add a project group to user's list."""
    logger.info(f"Adding project group '{project_group}' for user: {username}")
    
    result = await db.users.update_one(
        {"username": username},
        {"$addToSet": {"project_groups": project_group}}
    )
    
    if result.modified_count == 0:
        user = await db.users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "message": "Project group already exists"}
    
    return {"success": True, "message": "Project group added"}


@app.delete('/api/users/project-groups')
async def remove_user_project_group(username: str, project_group: str):
    """Remove a project group from user's list."""
    logger.info(f"Removing project group '{project_group}' for user: {username}")
    
    result = await db.users.update_one(
        {"username": username},
        {"$pull": {"project_groups": project_group}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User or project group not found")
    
    return {"success": True, "message": "Project group removed"}


@app.get('/api/users/project-groups')
async def get_all_project_groups():
    """Get all unique project groups across all users."""
    logger.info("Fetching all project groups")
    
    pipeline = [
        {"$unwind": "$project_groups"},
        {"$group": {"_id": "$project_groups"}},
        {"$sort": {"_id": 1}}
    ]
    
    groups = []
    async for doc in db.users.aggregate(pipeline):
        groups.append(doc["_id"])
    
    # Always include 'default' if not present
    if "default" not in groups:
        groups.insert(0, "default")
    
    return {"project_groups": groups}


@app.get('/api/admin/users')
async def get_all_users(admin_username: str):
    """Get all users (admin only)."""
    logger.info(f"Admin {admin_username} requesting all users")
    
    # Check if requester is admin
    admin = await db.users.find_one({"username": admin_username})
    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = []
    cursor = db.users.find({})
    async for user in cursor:
        users.append({
            "username": user.get("username"),
            "email": user.get("email"),
            "role": user.get("role", "user"),
            "project_groups": user.get("project_groups", []),
            "created_at": user.get("created_at")
        })
    
    return {"users": users}


@app.put('/api/admin/users/role')
async def update_user_role(admin_username: str, target_username: str, new_role: str):
    """Update user role (admin only)."""
    logger.info(f"Admin {admin_username} updating role for {target_username} to {new_role}")
    
    # Check if requester is admin
    admin = await db.users.find_one({"username": admin_username})
    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate role
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role. Must be 'user' or 'admin'")
    
    # Don't allow changing own role
    if admin_username == target_username:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    result = await db.users.update_one(
        {"username": target_username},
        {"$set": {"role": new_role}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True, "message": f"User role updated to {new_role}"}


@app.delete('/api/admin/users/data')
async def clean_user_data(admin_username: str, target_username: str, project_group: Optional[str] = None):
    """Clean all data for a specific user or user+project_group (admin only)."""
    if project_group:
        logger.info(f"Admin {admin_username} cleaning data for user: {target_username}, project_group: {project_group}")
    else:
        logger.info(f"Admin {admin_username} cleaning ALL data for user: {target_username}")
    
    # Check if requester is admin
    admin = await db.users.find_one({"username": admin_username})
    if not admin or admin.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Don't allow cleaning own data
    if admin_username == target_username:
        raise HTTPException(status_code=400, detail="Cannot clean your own data")
    
    # Collections that store user data with project_group
    project_group_collections = [
        'domains', 'projects', 'testplan_folders', 'testplan_tests',
        'testlab_releases', 'testlab_release_cycles', 'testlab_testsets', 'testlab_testruns',
        'defects', 'attachments', 'design_steps',
        'testplan_test_details', 'testplan_extraction_results',
        'testlab_testset_details', 'testlab_extraction_results',
        'defect_details', 'attachment_cache'
    ]
    
    # Collections that only store user (no project_group)
    user_only_collections = ['user_credentials']
    
    deleted_counts = {}
    
    # Build filter
    if project_group:
        # Clean only data for this specific project_group
        filter_query = {"user": target_username, "project_group": project_group}
        for collection_name in project_group_collections:
            collection = db[collection_name]
            result = await collection.delete_many(filter_query)
            deleted_counts[collection_name] = result.deleted_count
    else:
        # Clean ALL data for this user including the user itself
        filter_query = {"user": target_username}
        for collection_name in project_group_collections + user_only_collections:
            collection = db[collection_name]
            result = await collection.delete_many(filter_query)
            deleted_counts[collection_name] = result.deleted_count
        
        # Delete the user from users collection
        user_result = await db.users.delete_one({"username": target_username})
        deleted_counts['users'] = user_result.deleted_count
    
    logger.info(f"Cleaned data for {target_username} (project_group={project_group}): {deleted_counts}")
    
    return {
        "success": True,
        "message": f"Data cleaned for user {target_username}" + (f" in project group {project_group}" if project_group else " (all data and user account deleted)"),
        "deleted_counts": deleted_counts
    }


@app.get('/api/admin/db/stats')
async def get_db_stats(admin_username: str):
    """
    Get database statistics (collection counts and sizes).
    Admin only endpoint.
    """
    admin_user = await db.users.find_one({"username": admin_username})
    if not admin_user or admin_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        collections = [
            'users', 'user_credentials', 'domains', 'projects',
            'testplan_folders', 'testplan_tests', 'testplan_test_details',
            'testplan_extraction_results', 'design_steps',
            'testlab_releases', 'testlab_release_cycles', 'testlab_testsets',
            'testlab_testruns', 'testlab_testset_details', 'testlab_extraction_results',
            'defects', 'defect_details', 'attachments', 'attachment_cache'
        ]
        
        collection_stats = {}
        total_documents = 0
        total_size = 0
        
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            
            # Get collection stats
            stats = await db.command("collStats", collection_name)
            size = stats.get("size", 0)
            
            collection_stats[collection_name] = {
                "count": count,
                "size": size
            }
            
            total_documents += count
            total_size += size
        
        return {
            "success": True,
            "collections": collection_stats,
            "total_documents": total_documents,
            "total_size": total_size
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/admin/db/clean-all')
async def clean_all_data(admin_username: str):
    """
    Clean ALL data from the database (except admin users).
    Admin only endpoint - use with extreme caution!
    """
    admin_user = await db.users.find_one({"username": admin_username})
    if not admin_user or admin_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        collections_to_clean = [
            'user_credentials', 'domains', 'projects',
            'testplan_folders', 'testplan_tests', 'testplan_test_details',
            'testplan_extraction_results', 'design_steps',
            'testlab_releases', 'testlab_release_cycles', 'testlab_testsets',
            'testlab_testruns', 'testlab_testset_details', 'testlab_extraction_results',
            'defects', 'defect_details', 'attachments', 'attachment_cache'
        ]
        
        deleted_counts = {}
        
        # Delete all documents from each collection
        for collection_name in collections_to_clean:
            collection = db[collection_name]
            result = await collection.delete_many({})
            deleted_counts[collection_name] = result.deleted_count
        
        # Delete all non-admin users
        user_result = await db.users.delete_many({"role": {"$ne": "admin"}})
        deleted_counts['users'] = user_result.deleted_count
        
        logger.warning(f"Admin {admin_username} cleaned ALL database data: {deleted_counts}")
        
        return {
            "success": True,
            "message": "All data cleaned successfully",
            "deleted_counts": deleted_counts
        }
    except Exception as e:
        logger.error(f"Error cleaning all data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OLD ENDPOINTS (to be deprecated)
# ============================================================================

@app.post('/auth', response_model=AuthResponse)
async def authenticate(payload: AuthRequest):
    # Try ALM authentication first
    try:
        result = await alm_client.authenticate(payload.username, payload.password)
        # Convert new response format (success) to old format (ok)
        if result.get("success"):
            return {"ok": True, "message": result.get("message", "Authenticated")}
        else:
            raise HTTPException(status_code=401, detail=result.get("message", "Authentication failed"))
    except Exception as e:
        # Fallback to local authentication for demo
        user = await db.users.find_one({"username": payload.username})
        if not user:
            # Do NOT create user here - only after ALM authentication
            raise HTTPException(status_code=401, detail='Invalid username or password')
        if user.get('password') != payload.password:
            raise HTTPException(status_code=401, detail='Invalid username or password')
        return {
            "ok": True, 
            "message": "Authenticated", 
            "role": user.get("role", "user"),
            "project_groups": user.get("project_groups", [])
        }


@app.get('/domains')
async def get_domains(username: str):
    # Use new ALM client method
    try:
        result = await alm_client.fetch_and_store_domains(username)
        if result.get("success"):
            # Extract simple {id, name} format from MongoDB entities
            domains = result.get("domains_raw", [])
            return [{"id": d.get("id"), "name": d.get("name")} for d in domains]
    except Exception as e:
        print(f"Error fetching domains: {e}")
    
    # Fallback to MongoDB
    docs = []
    cursor = db.domains.find({"user": username})
    async for d in cursor:
        docs.append({"name": d.get('name'), "id": d.get('id')})
    return docs


@app.get('/projects')
async def get_projects(domain: str, username: str):
    # Use new ALM client method
    try:
        result = await alm_client.fetch_and_store_projects(username, domain)
        if result.get("success"):
            # Extract simple {id, name} format from raw MongoDB entities
            projects_raw = result.get("projects_raw", [])
            return [{"id": p.get("id"), "name": p.get("name")} for p in projects_raw]
    except Exception as e:
        print(f"Error fetching projects: {e}")
    
    # Fallback to MongoDB
    docs = []
    cursor = db.projects.find({"user": username, "parent_id": domain})
    async for p in cursor:
        docs.append({"name": p.get('name'), "id": p.get('id')})
    return docs


@app.post('/init')
async def init_sample():
    # Create a demo user and sample domains/projects and tree nodes
    await db.users.delete_many({})
    await db.domains.delete_many({})
    await db.projects.delete_many({})
    await db.tree_cache.delete_many({})
    await db.defects.delete_many({})

    await db.users.insert_one({"username": "admin", "password": "admin123"})
    await db.domains.insert_many([
        {"name": "DomainA"},
        {"name": "DomainB"}
    ])
    await db.projects.insert_many([
        {"name": "Project1", "domain": "DomainA"},
        {"name": "Project2", "domain": "DomainA"},
        {"name": "ProjectX", "domain": "DomainB"}
    ])
    # Sample tree nodes for testplan/testlab
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

    # Sample defects
    await db.defects.insert_many([
        {"id": "D-1", "summary": "Crash on load", "status": "Open", "priority": "High", "project": "Project1"},
        {"id": "D-2", "summary": "UI glitch", "status": "Closed", "priority": "Low", "project": "Project1"}
    ])

    return {"ok": True}


@app.get('/tree')
async def get_tree(
    project: str, 
    username: str,
    domain: str,
    type: str = 'testplan',
    parent_id: int = 0,
    folder_id: str = None
):
    """Get tree structure with subfolders, tests, and attachments."""
    if type == 'testplan':
        # If folder_id is provided, fetch its children (subfolders, tests, attachments)
        if folder_id:
            # Fetch subfolders
            subfolders = await alm_client.fetch_test_folders(username, domain, project, int(folder_id))
            if subfolders is None:
                subfolders = []
            
            # Fetch tests
            tests = await alm_client.fetch_tests_for_folder(username, domain, project, folder_id)
            if tests is None:
                tests = []
            
            # Fetch folder attachments
            folder_attachments = await alm_client.fetch_attachments(
                username, domain, project, "test-folder", folder_id
            )
            if folder_attachments is None:
                folder_attachments = []
            
            # Build tree structure
            tree_nodes = []
            
            # Add "Subfolders" node
            subfolder_children = []
            for folder in subfolders:
                sanitized_name = alm_client.sanitize_name(folder["name"])
                subfolder_children.append({
                    "id": f"folder_{folder['id']}",
                    "label": folder["name"],
                    "type": "folder",
                    "folder_id": folder["id"],
                    "has_children": True,  # Show + by default, checked on expand
                    "children": []
                })
            
            # Always add Subfolders container, even if empty
            tree_nodes.append({
                "id": f"subfolders_{folder_id}",
                "label": "Subfolders",
                "type": "container",
                "has_children": len(subfolder_children) > 0,
                "children": subfolder_children
            })
            
            # Add "Tests" node
            test_children = []
            for test in tests:
                sanitized_name = test.get("sanitized_name", test.get("id", ""))
                test_children.append({
                    "id": f"test_{test['id']}",
                    "label": test.get("name", "Unnamed Test"),
                    "type": "test",
                    "test_id": test["id"],
                    "has_children": True,  # Show + by default, checked on expand
                    "children": []
                })
            
            # Always add Tests container, even if empty
            tree_nodes.append({
                "id": f"tests_{folder_id}",
                "label": "Tests",
                "type": "container",
                "has_children": len(test_children) > 0,
                "children": test_children
            })
            
            # Add "Attachments" node
            attachment_children = []
            for attachment in folder_attachments:
                attachment_children.append({
                    "id": f"attachment_{attachment['id']}",
                    "label": attachment.get("name", "Unnamed Attachment"),
                    "type": "attachment",
                    "attachment_id": attachment["id"],
                    "has_children": False
                })
            
            # Always add Attachments container, even if empty
            tree_nodes.append({
                "id": f"attachments_{folder_id}",
                "label": "Attachments",
                "type": "container",
                "has_children": len(attachment_children) > 0,
                "children": attachment_children
            })
            
            return {"tree": tree_nodes}
        
        # Root level - fetch top-level folders from MongoDB
        cursor = db.testplan_folders.find({
            "user": username,
            "parent_id": "0"
        })
        folders = []
        async for f in cursor:
            folders.append({"id": f.get("id"), "name": f.get("name")})
        
        # If MongoDB is empty, fetch from ALM (which stores in MongoDB)
        if not folders:
            print(f"MongoDB empty for testplan root folders, fetching from ALM for user {username}")
            await alm_client.fetch_test_folders(username, domain, project, 0)
            
            # Now query MongoDB again after storing
            cursor = db.testplan_folders.find({
                "user": username,
                "parent_id": "0"
            })
            folders = []
            async for f in cursor:
                folders.append({"id": f.get("id"), "name": f.get("name")})
        
        # Convert to tree format
        tree = []
        for folder in folders:
            sanitized_name = alm_client.sanitize_name(folder["name"])
            tree.append({
                "id": f"folder_{folder['id']}",
                "label": folder["name"],
                "type": "folder",
                "folder_id": folder["id"],
                "has_children": True,
                "children": []
            })
        return {"tree": tree}
    
    elif type == 'testlab':
        # TestLab tree: Releases -> Release Cycles -> Test Sets
        # folder_id here represents different entity IDs based on context:
        # - release_id when fetching cycles
        # - cycle_id when fetching test sets
        
        if folder_id:
            # Check if this is a release (fetch cycles) or cycle (fetch test sets)
            # We'll use a prefix to distinguish: "release_", "cycle_", "testset_"
            
            if folder_id.startswith("release_"):
                # Fetch release cycles for this release from ALM/Mock ALM
                release_id = folder_id.replace("release_", "")
                cycles = await alm_client.fetch_release_cycles(username, domain, project, release_id)
                
                tree_nodes = []
                for cycle in cycles:
                    tree_nodes.append({
                        "id": f"cycle_{cycle['id']}",
                        "label": cycle.get("name", "Unnamed Cycle"),
                        "type": "cycle",
                        "cycle_id": cycle["id"],
                        "has_children": True,
                        "children": []
                    })
                
                return {"tree": tree_nodes}
            
            elif folder_id.startswith("cycle_"):
                # Fetch test sets for this cycle
                cycle_id = folder_id.replace("cycle_", "")
                test_sets = await alm_client.fetch_test_sets(username, domain, project, cycle_id)
                
                tree_nodes = []
                for test_set in test_sets:
                    tree_nodes.append({
                        "id": f"testset_{test_set['id']}",
                        "label": test_set.get("name", "Unnamed Test Set"),
                        "type": "testset",
                        "testset_id": test_set["id"],
                        "has_children": True,  # Show + by default, checked on expand
                        "children": []
                    })
                
                return {"tree": tree_nodes}
            
            elif folder_id.startswith("testset_"):
                # Fetch test runs and attachments for this test set
                testset_id = folder_id.replace("testset_", "")
                
                # Fetch test runs
                test_runs = await alm_client.fetch_test_runs(username, domain, project, testset_id)
                
                # Fetch test set attachments
                testset_attachments = await alm_client.fetch_attachments(
                    username, domain, project, "test-set", testset_id
                )
                
                tree_nodes = []
                
                # Add "Test Runs" container
                run_children = []
                for run in test_runs:
                    run_children.append({
                        "id": f"run_{run['id']}",
                        "label": run.get("name", f"Run {run['id']}"),
                        "type": "run",
                        "run_id": run["id"],
                        "status": run.get("status", ""),
                        "has_children": True  # Run has run.json and attachments
                    })
                
                if len(run_children) > 0:
                    tree_nodes.append({
                        "id": f"runs_{testset_id}",
                        "label": "Test Runs",
                        "type": "container",
                        "has_children": True,
                        "children": run_children
                    })
                
                # Add "Attachments" container
                attachment_children = []
                for attachment in testset_attachments:
                    attachment_children.append({
                        "id": f"attachment_{attachment['id']}",
                        "label": attachment.get("name", "Unnamed Attachment"),
                        "type": "attachment",
                        "attachment_id": attachment["id"],
                        "has_children": False
                    })
                
                if len(attachment_children) > 0:
                    tree_nodes.append({
                        "id": f"attachments_{testset_id}",
                        "label": "Attachments",
                        "type": "container",
                        "has_children": True,
                        "children": attachment_children
                    })
                
                return {"tree": tree_nodes}
        
        # Root level - fetch releases from MongoDB
        cursor = db.testlab_releases.find({"user": username})
        releases = []
        async for r in cursor:
            releases.append({"id": r.get("id"), "name": r.get("name")})
        
        # If MongoDB is empty, fetch from ALM (which stores in MongoDB)
        if not releases:
            print(f"MongoDB empty for testlab releases, fetching from ALM for user {username}")
            await alm_client.fetch_and_store_releases(username, domain, project)
            
            # Now query MongoDB again after storing
            cursor = db.testlab_releases.find({"user": username})
            releases = []
            async for r in cursor:
                releases.append({"id": r.get("id"), "name": r.get("name")})
        
        # Convert to tree format
        tree = []
        for release in releases:
            tree.append({
                "id": f"release_{release['id']}",
                "label": release.get("name", "Unnamed Release"),
                "type": "release",
                "release_id": release["id"],
                "has_children": True,
                "children": []
            })
        
        return {"tree": tree}
    
    else:
        # Unknown type
        return {"tree": []}


@app.get('/test-details')
async def get_test_details(
    username: str,
    domain: str,
    project: str,
    test_id: str
):
    """Get detailed test information and create test.json."""
    try:
        # Fetch test details with design steps
        test_details = await alm_client.fetch_test_details(username, domain, project, test_id)
        
        print(f"DEBUG test-details endpoint: test_details keys = {list(test_details.keys())}")
        print(f"DEBUG test-details endpoint: Has id={test_details.get('id')}, name={test_details.get('name')}, status={test_details.get('status')}")
        
        # Fetch test attachments
        attachments = await alm_client.fetch_attachments(
            username, domain, project, "test", test_id
        )
        
        # Build display data from top-level fields (fields array was removed for clean export)
        display_data = {}
        
        # Add all top-level test fields (excluding internal fields)
        excluded_fields = ["user", "parent_id", "entity_type", "design_steps", "attachments", "fields"]
        for key, value in test_details.items():
            if key not in excluded_fields and value is not None:
                # Convert field names to display format (e.g., "creation-time" -> "Creation Time")
                display_key = key.replace("-", " ").replace("_", " ").title()
                display_data[display_key] = value
        
        # Transform design steps from ALM format to clean format
        design_steps = []
        for step in test_details.get("design_steps", []):
            if isinstance(step, dict) and "Fields" in step:
                # Parse ALM format
                step_data = {}
                for field in step.get("Fields", []):
                    field_name = field.get("Name", "")
                    values = field.get("values", [])
                    if values:
                        step_data[field_name] = values[0].get("value")
                design_steps.append(step_data)
            else:
                # Already in simple format
                design_steps.append(step)
        
        display_data["Design Steps"] = design_steps
        display_data["Attachments"] = [
            {
                "id": att.get("id"),
                "name": att.get("name"),
                "sanitized_name": att.get("sanitized_name")
            }
            for att in attachments
        ]
        
        # Store in MongoDB for quick access
        await db.testplan_test_details.update_one(
            {"test_id": test_id, "username": username, "project": project},
            {"$set": {
                "test_id": test_id,
                "username": username,
                "project": project,
                "details": display_data
            }},
            upsert=True
        )
        
        return display_data
        
    except Exception as e:
        import traceback
        print(f"ERROR in get_test_details: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/test-children')
async def get_test_children(
    username: str,
    domain: str,
    project: str,
    test_id: str
):
    """Get children nodes for a test (attachments subfolder and test.json)."""
    try:
        # Fetch test attachments
        attachments = await alm_client.fetch_attachments(
            username, domain, project, "test", test_id
        )
        if attachments is None:
            attachments = []
        
        # Build tree structure
        tree = []
        
        # Add test.json file node
        tree.append({
            "id": f"testjson_{test_id}",
            "label": "test.json",
            "type": "test-json",
            "test_id": test_id,
            "has_children": False
        })
        
        # Add attachments container (always, even if empty)
        attachment_children = []
        for attachment in attachments:
            attachment_children.append({
                "id": f"test_attachment_{attachment['id']}",
                "label": attachment.get("name", "Unnamed Attachment"),
                "type": "attachment",
                "attachment_id": attachment["id"],
                "has_children": False
            })
        
        tree.append({
            "id": f"test_attachments_{test_id}",
            "label": "Attachments",
            "type": "container",
            "has_children": len(attachment_children) > 0,
            "children": attachment_children
        })
        
        return {"tree": tree}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/run-children')
async def get_run_children(
    username: str,
    domain: str,
    project: str,
    run_id: str
):
    """Get test run details and attachments."""
    try:
        # Fetch run details
        run_details = await alm_client.fetch_run_details(username, domain, project, run_id)
        
        # Transform to display format (alias: value)
        display_data = {}
        for field in run_details.get("fields", []):
            if field.get("display", False):
                display_data[field["alias"]] = field["value"]
        
        # Add run steps
        display_data["Run Steps"] = run_details.get("run_steps", [])
        
        # Fetch run attachments
        run_attachments = await alm_client.fetch_attachments(
            username, domain, project, "run", run_id
        )
        if run_attachments is None:
            run_attachments = []
        
        tree = []
        
        # Add run.json
        tree.append({
            "id": f"runjson_{run_id}",
            "label": "run.json",
            "type": "run-json",
            "has_children": False,
            "data": display_data
        })
        
        # Add Attachments container
        attachment_children = []
        for attachment in run_attachments:
            attachment_children.append({
                "id": f"attachment_{attachment['id']}",
                "label": attachment.get("name", "Unnamed Attachment"),
                "type": "attachment",
                "attachment_id": attachment["id"],
                "has_children": False
            })
        
        tree.append({
            "id": f"run_attachments_{run_id}",
            "label": "Attachments",
            "type": "container",
            "has_children": len(attachment_children) > 0,
            "children": attachment_children
        })
        
        return {"tree": tree}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/run-json')
async def get_run_json(
    username: str,
    domain: str,
    project: str,
    run_id: str
):
    """Get detailed run information as JSON."""
    try:
        run_details = await alm_client.fetch_run_details(username, domain, project, run_id)
        
        # Transform to display format (alias: value)
        display_data = {}
        for field in run_details.get("fields", []):
            if field.get("display", False):
                display_data[field["alias"]] = field["value"]
        
        # Transform run steps to clean format
        run_steps = []
        for step in run_details.get("run_steps", []):
            if isinstance(step, dict) and "Fields" in step:
                # Parse ALM format
                step_data = {}
                for field in step.get("Fields", []):
                    field_name = field.get("Name", "")
                    values = field.get("values", [])
                    if values:
                        step_data[field_name] = values[0].get("value")
                run_steps.append(step_data)
            else:
                # Already in simple format
                run_steps.append(step)
        
        display_data["Run Steps"] = run_steps
        
        return display_data
    except Exception as e:
        logger.error(f"Error in get_run_json: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e) or "Unknown error")


@app.get('/folders')
async def get_folders(
    username: str,
    domain: str,
    project: str,
    type: str = 'testplan',
    parent_id: int = 0
):
    if type == 'testplan':
        # Fetch test folders from ALM
        folders = await alm_client.fetch_test_folders(username, domain, project, parent_id)
        
        # If ALM fetch fails, fallback to MongoDB
        if not folders:
            cursor = db.alm_test_folders.find({
                "username": username,
                "project": project,
                "parent_id": parent_id
            })
            folders = []
            async for f in cursor:
                folders.append(f)
        
        # Convert to tree format
        tree = []
        for folder in folders:
            tree.append({
                "id": folder["id"],
                "label": folder["name"],
                "children": []  # Will be loaded on demand
            })
        return {"tree": tree}
    else:
        # Fallback to old implementation for testlab
        doc = await db.tree_cache.find_one({"project": project, "type": type})
        if not doc:
            return {"tree": []}
        return {"tree": doc.get('tree', [])}


@app.post('/extract-folder-recursive')
async def extract_folder_recursive(request: ExtractRequest):
    """
    Recursively extract all subfolders, tests, and attachments for a folder.
    Returns the complete subtree structure.
    """
    # For now, use hardcoded values matching the typical test environment
    username = "admin"
    domain = "DEFAULT"
    project = "Test Project 1"
    folder_id = request.node_id
    
    try:
        async def extract_folder_tree(current_folder_id: str, depth: int = 0) -> Dict[str, Any]:
            """Recursively extract folder and its children."""
            if depth > 20:  # Prevent infinite recursion
                return {"error": "Max depth reached"}
            
            result = {
                "folder_id": current_folder_id,
                "subfolders": [],
                "tests": [],
                "folder_attachments": []
            }
            
            # Fetch subfolders
            subfolders = await alm_client.fetch_test_folders(
                username, domain, project, int(current_folder_id)
            )
            
            # Fetch tests in this folder
            tests = await alm_client.fetch_tests_for_folder(
                username, domain, project, current_folder_id
            )
            
            # Fetch folder attachments
            folder_attachments = await alm_client.fetch_attachments(
                username, domain, project, "test-folder", current_folder_id
            )
            
            # Cache folder attachments
            if folder_attachments:
                folder_attachments = await cache_attachments(
                    username, domain, project, folder_attachments
                )
            
            # Process each test to get its details and attachments
            test_data = []
            for test in tests:
                test_id = str(test.get("id"))
                
                # Fetch test details with design steps
                test_details = await alm_client.fetch_test_details(
                    username, domain, project, test_id
                )
                
                # Transform design steps from ALM format to clean format
                design_steps = []
                for step in test_details.get("design_steps", []):
                    if isinstance(step, dict) and "Fields" in step:
                        # Parse ALM format
                        step_data = {}
                        for field in step.get("Fields", []):
                            field_name = field.get("Name", "")
                            values = field.get("values", [])
                            if values:
                                step_data[field_name] = values[0].get("value")
                        design_steps.append(step_data)
                    else:
                        # Already in simple format
                        design_steps.append(step)
                
                test_details["design_steps"] = design_steps
                
                # Fetch test attachments
                test_attachments = await alm_client.fetch_attachments(
                    username, domain, project, "test", test_id
                )
                
                # Cache test attachments
                if test_attachments:
                    test_attachments = await cache_attachments(
                        username, domain, project, test_attachments
                    )
                
                test_details["attachments"] = test_attachments
                test_data.append(test_details)
            
            result["tests"] = test_data
            result["folder_attachments"] = folder_attachments
            
            # Recursively process subfolders
            subfolder_data = []
            for subfolder in subfolders:
                subfolder_id = str(subfolder.get("id"))
                subfolder_tree = await extract_folder_tree(subfolder_id, depth + 1)
                subfolder_tree["folder_info"] = subfolder
                subfolder_data.append(subfolder_tree)
            
            result["subfolders"] = subfolder_data
            
            return result
        
        # Start recursive extraction
        extraction_result = await extract_folder_tree(folder_id)
        
        # Calculate statistics
        def count_items(node: Dict[str, Any]) -> Dict[str, int]:
            stats = {"folders": 0, "tests": 0, "attachments": 0}
            stats["tests"] = len(node.get("tests", []))
            stats["attachments"] = len(node.get("folder_attachments", []))
            
            # Count attachments in tests
            for test in node.get("tests", []):
                stats["attachments"] += len(test.get("attachments", []))
            
            # Recursively count subfolder items
            for subfolder in node.get("subfolders", []):
                stats["folders"] += 1
                subfolder_stats = count_items(subfolder)
                stats["folders"] += subfolder_stats["folders"]
                stats["tests"] += subfolder_stats["tests"]
                stats["attachments"] += subfolder_stats["attachments"]
            
            return stats
        
        stats = count_items(extraction_result)
        stats["total_items"] = stats["folders"] + stats["tests"] + stats["attachments"]
        
        # Store extraction result in MongoDB for future reference
        await db.testplan_extraction_results.update_one(
            {
                "username": username,
                "project": project,
                "folder_id": folder_id
            },
            {
                "$set": {
                    "username": username,
                    "domain": domain,
                    "project": project,
                    "folder_id": folder_id,
                    "result": extraction_result,
                    "stats": stats,
                    "extracted_at": datetime.utcnow().isoformat()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "folder_id": folder_id,
            "stats": stats,
            "data": extraction_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/testset-details')
async def get_testset_details(
    username: str,
    domain: str,
    project: str,
    testset_id: str
):
    """Get detailed test set information including test runs and create testset.json."""
    try:
        # Fetch test runs for the test set
        test_runs = await alm_client.fetch_test_runs(username, domain, project, testset_id)
        
        # Fetch test set attachments
        attachments = await alm_client.fetch_attachments(
            username, domain, project, "test-set", testset_id
        )
        
        # Cache attachments
        if attachments:
            attachments = await cache_attachments(
                username, domain, project, attachments
            )
        
        # Build test set details
        testset_details = {
            "testset_id": testset_id,
            "test_runs": test_runs,
            "attachments": [
                {
                    "id": att.get("id"),
                    "name": att.get("name"),
                    "sanitized_name": att.get("sanitized_name", att.get("name", ""))
                }
                for att in attachments
            ]
        }
        
        # Store in MongoDB for quick access
        await db.testlab_testset_details.update_one(
            {"testset_id": testset_id, "username": username, "project": project},
            {"$set": {
                "testset_id": testset_id,
                "username": username,
                "domain": domain,
                "project": project,
                "data": testset_details,
                "fetched_at": datetime.utcnow().isoformat()
            }},
            upsert=True
        )
        
        return testset_details
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/testset-children')
async def get_testset_children(
    username: str,
    domain: str,
    project: str,
    testset_id: str
):
    """Get children nodes for a test set (testset.json + Attachments folder)."""
    try:
        # Get test set details
        testset_details = await get_testset_details(username, domain, project, testset_id)
        
        # Build tree structure with testset.json and Attachments
        tree_nodes = []
        
        # Add testset.json node
        tree_nodes.append({
            "id": f"testset_json_{testset_id}",
            "label": "testset.json",
            "type": "testset_json",
            "testset_id": testset_id,
            "has_children": False,
            "json_data": testset_details
        })
        
        # Add Attachments folder
        attachment_children = []
        for att in testset_details.get("attachments", []):
            attachment_children.append({
                "id": f"attachment_{att['id']}",
                "label": att.get("name", "Unnamed Attachment"),
                "type": "attachment",
                "attachment_id": att["id"],
                "has_children": False
            })
        
        tree_nodes.append({
            "id": f"attachments_{testset_id}",
            "label": "Attachments",
            "type": "container",
            "children": attachment_children
        })
        
        return {"tree": tree_nodes}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/extract-testlab-recursive')
async def extract_testlab_recursive(
    username: str,
    domain: str,
    project: str,
    node_id: str,
    node_type: str
):
    """
    Recursively extract TestLab data starting from a release or cycle.
    
    Args:
        node_id: ID of the release or cycle (without prefix)
        node_type: Either "release" or "cycle"
    
    Returns:
        Complete subtree structure with all releases, cycles, test sets, runs, and attachments
    """
    try:
        async def extract_testset_tree(testset_id: str) -> Dict[str, Any]:
            """Extract test set with runs (including run steps and attachments) and attachments."""
            result = {
                "testset_id": testset_id,
                "test_runs": [],
                "attachments": []
            }
            
            # Fetch test runs
            test_runs = await alm_client.fetch_test_runs(username, domain, project, testset_id)
            
            # For each run, fetch complete details including run steps and attachments
            enriched_runs = []
            for run in test_runs:
                run_id = str(run.get("id"))
                
                # Fetch complete run details with run steps
                run_details = await alm_client.fetch_run_details(username, domain, project, run_id)
                
                # Transform to display format (similar to /run-json endpoint)
                run_data = {
                    "id": run_id,
                    "name": run.get("name")
                }
                
                # Add all fields from run_details
                for field in run_details.get("fields", []):
                    if field.get("display", False):
                        # Skip if key already exists (avoid duplicates)
                        if field["alias"] not in run_data:
                            run_data[field["alias"]] = field["value"]
                
                # Transform run steps from ALM format to clean format
                run_steps = []
                for step in run_details.get("run_steps", []):
                    if isinstance(step, dict) and "Fields" in step:
                        # Parse ALM format
                        step_data = {}
                        for field in step.get("Fields", []):
                            field_name = field.get("Name", "")
                            values = field.get("values", [])
                            if values:
                                step_data[field_name] = values[0].get("value")
                        run_steps.append(step_data)
                    else:
                        # Already in simple format
                        run_steps.append(step)
                
                run_data["run_steps"] = run_steps
                
                # Fetch run attachments
                run_attachments = await alm_client.fetch_attachments(
                    username, domain, project, "run", run_id
                )
                
                # Cache attachments
                if run_attachments:
                    run_attachments = await cache_attachments(
                        username, domain, project, run_attachments
                    )
                
                run_data["attachments"] = run_attachments
                
                enriched_runs.append(run_data)
            
            result["test_runs"] = enriched_runs
            
            # Fetch test set attachments
            attachments = await alm_client.fetch_attachments(
                username, domain, project, "test-set", testset_id
            )
            
            # Cache attachments
            if attachments:
                attachments = await cache_attachments(
                    username, domain, project, attachments
                )
            
            result["attachments"] = attachments
            
            return result
        
        async def extract_cycle_tree(cycle_id: str, depth: int = 0) -> Dict[str, Any]:
            """Extract cycle with all test sets."""
            if depth > 20:  # Prevent infinite recursion
                return {"error": "Max depth reached"}
            
            result = {
                "cycle_id": cycle_id,
                "test_sets": []
            }
            
            # Fetch test sets for this cycle
            test_sets = await alm_client.fetch_test_sets(username, domain, project, cycle_id)
            
            # Process each test set
            testset_data = []
            for test_set in test_sets:
                testset_id = str(test_set.get("id"))
                testset_tree = await extract_testset_tree(testset_id)
                testset_tree["testset_info"] = test_set
                testset_data.append(testset_tree)
            
            result["test_sets"] = testset_data
            
            return result
        
        async def extract_release_tree(release_id: str, depth: int = 0) -> Dict[str, Any]:
            """Extract release with all cycles and test sets."""
            if depth > 20:  # Prevent infinite recursion
                return {"error": "Max depth reached"}
            
            result = {
                "release_id": release_id,
                "cycles": []
            }
            
            # Fetch cycles for this release
            cycles = await alm_client.fetch_release_cycles(username, domain, project, release_id)
            
            # Process each cycle
            cycle_data = []
            for cycle in cycles:
                cycle_id = str(cycle.get("id"))
                cycle_tree = await extract_cycle_tree(cycle_id, depth + 1)
                cycle_tree["cycle_info"] = cycle
                cycle_data.append(cycle_tree)
            
            result["cycles"] = cycle_data
            
            return result
        
        # Start recursive extraction based on node type
        if node_type == "release":
            extraction_result = await extract_release_tree(node_id)
        elif node_type == "cycle":
            extraction_result = await extract_cycle_tree(node_id)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid node_type: {node_type}")
        
        # Calculate statistics
        def count_testlab_items(node: Dict[str, Any], node_type: str) -> Dict[str, int]:
            stats = {"releases": 0, "cycles": 0, "testsets": 0, "runs": 0, "attachments": 0}
            
            if node_type == "release":
                stats["cycles"] = len(node.get("cycles", []))
                for cycle in node.get("cycles", []):
                    cycle_stats = count_testlab_items(cycle, "cycle")
                    stats["testsets"] += cycle_stats["testsets"]
                    stats["runs"] += cycle_stats["runs"]
                    stats["attachments"] += cycle_stats["attachments"]
            elif node_type == "cycle":
                stats["testsets"] = len(node.get("test_sets", []))
                for testset in node.get("test_sets", []):
                    stats["runs"] += len(testset.get("test_runs", []))
                    stats["attachments"] += len(testset.get("attachments", []))
                    # Count run attachments
                    for run in testset.get("test_runs", []):
                        stats["attachments"] += len(run.get("attachments", []))
            
            return stats
        
        stats = count_testlab_items(extraction_result, node_type)
        stats["total_items"] = stats.get("releases", 0) + stats.get("cycles", 0) + stats.get("testsets", 0) + stats.get("runs", 0) + stats.get("attachments", 0)
        
        # Store extraction result in MongoDB for future reference
        await db.testlab_extraction_results.update_one(
            {
                "username": username,
                "project": project,
                "node_id": node_id,
                "node_type": node_type
            },
            {
                "$set": {
                    "username": username,
                    "domain": domain,
                    "project": project,
                    "node_id": node_id,
                    "node_type": node_type,
                    "result": extraction_result,
                    "stats": stats,
                    "extracted_at": datetime.utcnow().isoformat()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "node_id": node_id,
            "node_type": node_type,
            "stats": stats,
            "data": extraction_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/logout')
async def logout(username: str = Body(..., embed=True)):
    """Logout user and remove credentials from MongoDB."""
    success = await alm_client.logout(username)
    return {"ok": success}


@app.get('/defects')
async def get_defects(
    username: str,
    domain: str,
    project: str,
    start_index: int = 1,
    page_size: int = 100,
    query_filter: str = None
):
    """
    Get defects with pagination and optional filtering.
    Flow: Fetch from ALM → Store in MongoDB → Query MongoDB → Return
    
    Args:
        username: ALM username
        domain: Domain name
        project: Project name
        start_index: Starting index (1-based, default=1)
        page_size: Number of defects per page (default=100)
        query_filter: Optional ALM query filter
    
    Returns:
        Dict with defects array and total count
    """
    try:
        # Get project_group from user_credentials
        user_creds = await db.user_credentials.find_one({"user": username})
        project_group = user_creds.get("project_group", "default") if user_creds else "default"
        
        # Fetch fresh data from ALM and store in MongoDB
        await alm_client.fetch_and_store_defects(
            username, domain, project, project_group,
            start_index=start_index, 
            page_size=page_size,
            query_filter=query_filter
        )
        
        # Query from MongoDB with project_group filter
        cursor = db.defects.find(
            {"user": username, "project_group": project_group},
            skip=start_index - 1,
            limit=page_size
        )
        defects = []
        async for d in cursor:
            d.pop("_id", None)
            # Build defect data from top-level fields (fields array will be removed)
            excluded_fields = ["user", "project_group", "parent_id", "entity_type", "fields"]
            defect_data = {}
            for key, value in d.items():
                if key not in excluded_fields and value is not None:
                    defect_data[key] = value
            
            defects.append(defect_data)
        
        total = await db.defects.count_documents({"user": username, "project_group": project_group})
        return {"defects": defects, "total": total}
        
    except Exception as e:
        logger.error(f"Error fetching defects: {str(e)}")
        return {"defects": [], "total": 0}


@app.get('/defect-details')
async def get_defect_details(
    username: str,
    domain: str,
    project: str,
    defect_id: str
):
    """Get detailed defect information including all fields and attachments."""
    try:
        defect_details = await alm_client.fetch_defect_details(
            username, domain, project, defect_id
        )
        
        if not defect_details:
            return {}
        
        # Fetch defect attachments
        attachments = await alm_client.fetch_attachments(
            username, domain, project, "defect", defect_id
        )
        
        # Transform to display format (similar to test-details)
        # Build display data from top-level fields (fields array was removed for clean export)
        display_data = {}
        excluded_fields = ["user", "parent_id", "entity_type", "attachments", "fields"]
        
        for key, value in defect_details.items():
            if key not in excluded_fields and value is not None:
                # Convert field names to display format (e.g., "creation-time" -> "Creation Time")
                display_key = key.replace("-", " ").replace("_", " ").title()
                display_data[display_key] = value
        
        # Add attachments (use lowercase to match frontend interface)
        display_data["attachments"] = [
            {
                "id": att.get("id"),
                "name": att.get("name"),
                "file-size": att.get("file-size"),
                "sanitized_name": att.get("sanitized_name")
            }
            for att in attachments
        ]
        
        # Cache in MongoDB
        await db.defect_details.update_one(
            {"defect_id": defect_id, "project": project},
            {"$set": {
                "defect_id": defect_id,
                "project": project,
                "username": username,
                "domain": domain,
                "data": display_data,
                "fetched_at": datetime.utcnow().isoformat()
            }},
            upsert=True
        )
        
        return display_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/download-attachment')
async def download_attachment_endpoint(
    username: str,
    domain: str,
    project: str,
    attachment_id: str,
    filename: str = "attachment"
):
    """Download attachment file from MongoDB cache or ALM."""
    try:
        # Check MongoDB cache first
        cache_key = f"{domain}_{project}_{attachment_id}"
        cached_attachment = await attachments_collection.find_one({"_id": cache_key})
        
        if cached_attachment:
            content = cached_attachment['content']
            filename = cached_attachment.get('filename', filename)
        else:
            # Download from ALM and cache it
            content = await alm_client.download_attachment(
                username, domain, project, attachment_id
            )
            
            if not content:
                raise HTTPException(status_code=404, detail="Attachment not found")
            
            # Store in MongoDB
            await attachments_collection.update_one(
                {"_id": cache_key},
                {
                    "$set": {
                        "domain": domain,
                        "project": project,
                        "attachment_id": attachment_id,
                        "filename": filename,
                        "content": content,
                        "downloaded_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
