"""
ALM Integration Module - Refactored with Generic Fetch Engine

This module provides a generic ALM/Mock ALM fetch engine with:
- Automatic retry (3 attempts) with re-authentication
- Automatic pagination (loop until entities < page_size)
- Single source of truth for all ALM operations
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx
from cryptography.fernet import Fernet
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.alm_config import ALMConfig

logger = logging.getLogger(__name__)


class ALM:
    """Generic ALM Integration with retry, pagination, and automatic re-authentication."""
    
    def __init__(self, db: AsyncIOMotorDatabase, encryption_key: Optional[str] = None):
        self.db = db
        self.use_mock = os.getenv("USE_MOCK_ALM", "false").lower() == "true"
        self.base_url = os.getenv("ALM_BASE_URL", "").rstrip("/")
        if not self.base_url:
            raise ValueError("ALM_BASE_URL not set")
        self.lwsso_cookie = None
        self.qc_session_cookie = None
        self.alm_user_cookie = None
        self.xsrf_token = None
        self.is_authenticated = False
        # Encryption - Use provided key or generate/retrieve persistent key
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        else:
            generated_key = Fernet.generate_key()
            self.cipher = Fernet(generated_key)
            logger.warning("No encryption key provided. Using generated key. Set ENCRYPTION_KEY in .env for production.")
        logger.info(f"ALM Client initialized. Using {'Mock ALM' if self.use_mock else 'Real ALM'}: {self.base_url}")
    
    # =========================================================================
    # CORE GENERIC FUNCTIONS
    # =========================================================================
    
    async def _make_request_with_retry(self, url: str, method: str = "GET", params: Dict = None, 
                                      json_data: Dict = None, username: str = None) -> Optional[Dict]:
        """
        Generic HTTP request with 3 retry attempts and automatic re-authentication.
        Updates class cookies from response. Returns response JSON or None on failure.
        """
        for attempt in range(1, 4):  # 3 attempts
            try:
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
                
                # Build cookie header from class variables
                if self.is_authenticated:
                    cookies = []
                    if self.lwsso_cookie: cookies.append(f"LWSSO_COOKIE_KEY={self.lwsso_cookie}")
                    if self.qc_session_cookie: cookies.append(f"QCSession={self.qc_session_cookie}")
                    if self.alm_user_cookie: cookies.append(f"ALM_USER={self.alm_user_cookie}")
                    if self.xsrf_token: cookies.append(f"XSRF-TOKEN={self.xsrf_token}")
                    if cookies:
                        headers["Cookie"] = "; ".join(cookies)
                
                async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                    if method == "GET":
                        response = await client.get(url, params=params, headers=headers)
                    elif method == "POST":
                        response = await client.post(url, json=json_data, headers=headers)
                    else:
                        return None
                    
                    # Update class cookies from response
                    if response.cookies:
                        if "LWSSO_COOKIE_KEY" in response.cookies:
                            self.lwsso_cookie = response.cookies["LWSSO_COOKIE_KEY"]
                        if "QCSession" in response.cookies:
                            self.qc_session_cookie = response.cookies["QCSession"]
                        if "ALM_USER" in response.cookies:
                            self.alm_user_cookie = response.cookies["ALM_USER"]
                        if "XSRF-TOKEN" in response.cookies:
                            self.xsrf_token = response.cookies["XSRF-TOKEN"]
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 401 and username and attempt < 3:
                        logger.warning(f"Auth failed (attempt {attempt}/3), re-authenticating...")
                        if await self._ensure_authenticated(username):
                            # Rebuild headers with new cookies after re-auth
                            continue
                    else:
                        logger.error(f"Request failed: {response.status_code}")
                        if attempt < 3:
                            continue
                        return None
            except Exception as e:
                logger.error(f"Request error (attempt {attempt}/3): {str(e)}")
                if attempt < 3:
                    continue
                return None
        
        return None
    
    async def _fetch_all_pages(self, endpoint_name: str, username: str, domain: str, project: str, 
                               **filter_params) -> List[Dict]:
        """
        Generic pagination engine: Fetch ALL pages until entities < page_size (100).
        Automatically loops with start_index += 100.
        Handles both 'results' format (domains/projects) and 'entities' format (everything else).
        """
        url = ALMConfig.build_alm_url(self.base_url, endpoint_name, domain=domain, project=project)
        all_entities = []
        start_index = 1
        page_size = 100
        
        # Remove pagination params from filter_params to avoid conflicts
        clean_filter_params = {k: v for k, v in filter_params.items() if k not in ['start_index', 'page_size']}
        
        # Domains and projects use 'results' format without pagination
        if endpoint_name in ["domains", "projects"]:
            response = await self._make_request_with_retry(url, "GET", clean_filter_params, username=username)
            
            if not response:
                logger.error(f"Failed to fetch {endpoint_name}")
                return []
            
            # Handle 'results' format for domains/projects
            entities = response.get("results", [])
            logger.info(f"Fetched {len(entities)} {endpoint_name}")
            return entities
        
        # Standard entities with pagination
        while True:
            params = ALMConfig.build_query_params(endpoint_name, start_index=start_index, 
                                                  page_size=page_size, **clean_filter_params)
            
            response = await self._make_request_with_retry(url, "GET", params, username=username)
            
            if not response:
                logger.error(f"Failed to fetch {endpoint_name} at start_index={start_index}")
                break
            
            entities = response.get("entities", [])
            all_entities.extend(entities)
            
            logger.info(f"Fetched {len(entities)} {endpoint_name} (start={start_index}, total={len(all_entities)})")
            
            if len(entities) < page_size:
                logger.info(f"All pages fetched. Total {endpoint_name}: {len(all_entities)}")
                break
            
            start_index += page_size
        
        return all_entities
    
    async def _store_entities(self, endpoint_name: str, entities: List[Dict], username: str, 
                             parent_id: Optional[str] = None, project_group: str = "default") -> int:
        """
        Generic entity storage: Parse and store entities in MongoDB.
        Returns count of stored entities.
        Handles both simple format (domains/projects) and complex ALM format (other entities).
        """
        collection_map = {
            "domains": self.db.domains,
            "projects": self.db.projects,
            "test-folders": self.db.testplan_folders,
            "tests": self.db.testplan_tests,
            "release-folders": self.db.testlab_release_folders,
            "releases": self.db.testlab_releases,
            "release-cycles": self.db.testlab_release_cycles,
            "test-sets": self.db.testlab_testsets,
            "test-runs": self.db.testlab_testruns,
            "defects": self.db.defects,
            "attachments": self.db.attachments,
            "design-steps": self.db.design_steps
        }
        
        collection = collection_map.get(endpoint_name, self.db.attachment_cache)
        stored_count = 0
        
        for raw_entity in entities:
            # Handle simple format for domains and projects
            if endpoint_name == "domains":
                # Format: {"name": "DOMAIN_NAME", "projects": []}
                entity = {
                    "user": username,
                    "project_group": project_group,
                    "id": raw_entity.get("name"),  # Use name as ID for domains
                    "name": raw_entity.get("name"),
                    "entity_type": "domain"
                }
            elif endpoint_name == "projects":
                # Format: {"name": "Project_Name"}
                entity = {
                    "user": username,
                    "project_group": project_group,
                    "id": raw_entity.get("name"),  # Use name as ID for projects
                    "name": raw_entity.get("name"),
                    "parent_id": parent_id,
                    "entity_type": "project"
                }
            else:
                # Standard ALM format with Fields array
                entity = ALMConfig.parse_alm_response_to_entity(endpoint_name, raw_entity, username, parent_id, project_group)
            
            await collection.replace_one(
                {"user": username, "project_group": project_group, "id": entity["id"]}, 
                entity, 
                upsert=True
            )
            stored_count += 1
        
        return stored_count
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with ALM and store credentials."""
        try:
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                # Step 1: LWSSO authentication using Basic Auth
                auth_url = f"{self.base_url}/authentication-point/authenticate"
                auth_response = await client.get(
                    auth_url,
                    auth=(username, password),  # Basic Auth
                    headers={"Accept": "application/json"}
                )
                
                if auth_response.status_code != 200:
                    return {"success": False, "message": f"Authentication failed: {auth_response.status_code}"}
                
                self.lwsso_cookie = auth_response.cookies.get("LWSSO_COOKIE_KEY")
                if not self.lwsso_cookie:
                    return {"success": False, "message": "Failed to get LWSSO_COOKIE_KEY"}
                
                # Step 2: Site session with XML content and LWSSO cookie
                session_url = f"{self.base_url}/rest/site-session"
                session_content = '<session-parameters><client-type>REST-MobileQA-MyTIAAMobile</client-type></session-parameters>'
                session_response = await client.post(
                    session_url,
                    headers={
                        "Accept": "application/xml",
                        "Content-Type": "application/xml",
                        "Cookie": f"LWSSO_COOKIE_KEY={self.lwsso_cookie}"
                    },
                    content=session_content
                )
                
                if session_response.status_code != 200 and session_response.status_code != 201:
                    return {"success": False, "message": f"Site session failed: {session_response.status_code}"}
                
                # Retrieve all 4 cookies from session response
                self.qc_session_cookie = session_response.cookies.get("QCSession")
                self.alm_user_cookie = session_response.cookies.get("ALM_USER")
                self.xsrf_token = session_response.cookies.get("XSRF-TOKEN")
                
                # LWSSO_COOKIE_KEY might also be refreshed
                if "LWSSO_COOKIE_KEY" in session_response.cookies:
                    self.lwsso_cookie = session_response.cookies["LWSSO_COOKIE_KEY"]
                
                self.is_authenticated = True
                
                logger.info(f"Authentication successful for {username}. Cookies: LWSSO={bool(self.lwsso_cookie)}, QCSession={bool(self.qc_session_cookie)}, ALM_USER={bool(self.alm_user_cookie)}, XSRF={bool(self.xsrf_token)}")
            
            # Store encrypted credentials
            encrypted_pwd = self.cipher.encrypt(password.encode()).decode()
            await self.db.user_credentials.replace_one(
                {"username": username},
                {"username": username, "encrypted_password": encrypted_pwd, "created_at": datetime.utcnow().isoformat()},
                upsert=True
            )
            
            return {"success": True, "message": "Authenticated", "username": username}
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return {"success": False, "message": str(e)}
    
    async def _ensure_authenticated(self, username: str) -> bool:
        """Re-authenticate if needed using stored credentials."""
        if self.is_authenticated:
            return True
        
        cred = await self.db.user_credentials.find_one({"username": username})
        if not cred:
            logger.warning(f"No stored credentials found for user: {username}")
            return False
        
        try:
            password = self.cipher.decrypt(cred["encrypted_password"].encode()).decode()
        except Exception as decrypt_error:
            logger.error(f"Failed to decrypt password for {username}: {str(decrypt_error)}")
            logger.error("This usually means the encryption key has changed. User needs to re-authenticate.")
            # Delete invalid credential
            await self.db.user_credentials.delete_one({"username": username})
            return False
        
        result = await self.authenticate(username, password)
        return result.get("success", False)
    
    async def logout(self, username: str) -> Dict[str, Any]:
        """Logout from ALM."""
        try:
            if self.is_authenticated:
                url = f"{self.base_url}/authentication-point/logout"
                await self._make_request_with_retry(url, "POST", username=username)
            
            self.is_authenticated = False
            self.lwsso_cookie = None
            self.qc_session_cookie = None
            self.alm_user_cookie = None
            self.xsrf_token = None
            return {"success": True, "message": "Logged out"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    # =========================================================================
    # GENERIC FETCH & STORE (ALL ENTITIES USE THIS)
    # =========================================================================
    
    async def fetch_and_store(self, endpoint_name: str, username: str, domain: str, project: str, 
                             project_group: str = "default", **filter_params) -> Dict[str, Any]:
        """
        Universal fetch & store function for ANY ALM entity.
        Handles: domains, projects, folders, tests, releases, cycles, test-sets, runs, defects, attachments, etc.
        
        Flow: Fetch ALL pages → Store in MongoDB → Return count
        """
        try:
            if not await self._ensure_authenticated(username):
                return {"success": False, "message": "Authentication failed"}
            
            # Fetch all pages
            all_entities = await self._fetch_all_pages(endpoint_name, username, domain, project, **filter_params)
            
            if not all_entities:
                return {"success": True, "count": 0, "entities": []}
            
            # Store in MongoDB with project_group
            stored_count = await self._store_entities(
                endpoint_name, all_entities, username, 
                filter_params.get("parent_id"), project_group
            )
            
            logger.info(f"Stored {stored_count} {endpoint_name} for {username}/{project_group} in MongoDB")
            
            return {"success": True, "count": stored_count, "entities": all_entities}
            
        except Exception as e:
            logger.error(f"Error in fetch_and_store for {endpoint_name}: {str(e)}", exc_info=True)
            return {"success": False, "message": str(e)}
    
    # =========================================================================
    # CONVENIENCE WRAPPERS (Call generic fetch_and_store)
    # =========================================================================
    
    async def fetch_and_store_domains(self, username: str) -> Dict[str, Any]:
        """Fetch domains using generic engine."""
        result = await self.fetch_and_store("domains", username, "", "")
        if result["success"]:
            # Query MongoDB to get parsed entities (with id/name at top level)
            cursor = self.db.domains.find({"user": username})
            domains = []
            async for d in cursor:
                domains.append({
                    "id": d.get("id"),
                    "name": d.get("name")
                })
            
            result["domains_raw"] = domains
            result["domains"] = [{"Domain ID": d.get("id"), "Domain Name": d.get("name")} for d in domains]
        return result
    
    async def fetch_and_store_projects(self, username: str, domain: str) -> Dict[str, Any]:
        """Fetch projects using generic engine."""
        result = await self.fetch_and_store("projects", username, domain, "", parent_id=domain)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.projects.find({"user": username, "parent_id": domain})
            projects = []
            async for p in cursor:
                projects.append({
                    "id": p.get("id"),
                    "name": p.get("name")
                })
            
            result["projects_raw"] = projects
            result["projects"] = [{"Project ID": p.get("id"), "Project Name": p.get("name")} for p in projects]
        return result
        return result
    
    async def fetch_and_store_root_test_folders(self, username: str, domain: str, project: str, project_group: str = "default") -> Dict[str, Any]:
        """Fetch root test folders (parent_id=0) using generic engine."""
        return await self.fetch_and_store("test-folders", username, domain, project, project_group, parent_id="0")
    
    async def fetch_and_store_root_release_folders(self, username: str, domain: str, project: str, project_group: str = "default") -> Dict[str, Any]:
        """Fetch root release folders (parent_id=0) using generic engine."""
        return await self.fetch_and_store("release-folders", username, domain, project, project_group, parent_id="0")
    
    async def fetch_and_store_releases(self, username: str, domain: str, project: str, project_group: str = "default", parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch releases using generic engine."""
        return await self.fetch_and_store("releases", username, domain, project, project_group, parent_id=parent_id)
    
    async def fetch_and_store_defects(self, username: str, domain: str, project: str, project_group: str = "default", **kwargs) -> Dict[str, Any]:
        """Fetch defects using generic engine."""
        return await self.fetch_and_store("defects", username, domain, project, project_group, **kwargs)
    
    async def fetch_release_cycles(self, username: str, domain: str, project: str, release_id: str) -> List[Dict]:
        """Fetch release cycles using generic engine."""
        result = await self.fetch_and_store("release-cycles", username, domain, project, parent_id=release_id)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.testlab_release_cycles.find({"user": username, "parent_id": release_id})
            cycles = []
            async for c in cursor:
                cycles.append({"id": c.get("id"), "name": c.get("name")})
            return cycles
        return []
    
    async def fetch_test_folders(self, username: str, domain: str, project: str, parent_id: int) -> List[Dict]:
        """Fetch test folders using generic engine."""
        result = await self.fetch_and_store("test-folders", username, domain, project, parent_id=str(parent_id))
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.testplan_folders.find({"user": username, "parent_id": str(parent_id)})
            folders = []
            async for f in cursor:
                folders.append({"id": f.get("id"), "name": f.get("name")})
            return folders
        return []
    
    async def fetch_release_folders(self, username: str, domain: str, project: str, parent_id: str) -> List[Dict]:
        """Fetch release folders using generic engine."""
        result = await self.fetch_and_store("release-folders", username, domain, project, parent_id=parent_id)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.testlab_release_folders.find({"user": username, "parent_id": parent_id})
            folders = []
            async for f in cursor:
                folders.append({"id": f.get("id"), "name": f.get("name")})
            return folders
        return []
    
    async def fetch_tests_for_folder(self, username: str, domain: str, project: str, folder_id: str) -> List[Dict]:
        """Fetch tests using generic engine."""
        result = await self.fetch_and_store("tests", username, domain, project, parent_id=folder_id)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.testplan_tests.find({"user": username, "parent_id": folder_id})
            tests = []
            async for t in cursor:
                tests.append({"id": t.get("id"), "name": t.get("name")})
            return tests
        return []
    
    async def fetch_releases_for_folder(self, username: str, domain: str, project: str, folder_id: str) -> List[Dict]:
        """Fetch releases for a folder using generic engine."""
        result = await self.fetch_and_store("releases", username, domain, project, parent_id=folder_id)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.testlab_releases.find({"user": username, "parent_id": folder_id})
            releases = []
            async for r in cursor:
                releases.append({"id": r.get("id"), "name": r.get("name")})
            return releases
        return []
    
    async def fetch_test_sets(self, username: str, domain: str, project: str, cycle_id: str) -> List[Dict]:
        """Fetch test sets using generic engine."""
        # For test-sets, cycle_id is used in query filter, and we store it as parent_id
        result = await self.fetch_and_store("test-sets", username, domain, project, cycle_id=cycle_id, parent_id=cycle_id)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.testlab_testsets.find({"user": username, "parent_id": cycle_id})
            test_sets = []
            async for ts in cursor:
                test_sets.append({"id": ts.get("id"), "name": ts.get("name")})
            return test_sets
        return []
    
    async def fetch_test_runs(self, username: str, domain: str, project: str, testset_id: str) -> List[Dict]:
        """Fetch test runs using generic engine."""
        # For test-runs, testset_id is used in query filter, and we store it as parent_id
        result = await self.fetch_and_store("test-runs", username, domain, project, testset_id=testset_id, parent_id=testset_id)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.testlab_testruns.find({"user": username, "parent_id": testset_id})
            runs = []
            async for r in cursor:
                # Extract status from fields array
                status = ""
                for field in r.get("fields", []):
                    if field.get("field") == "status":
                        status = field.get("value", "")
                        break
                runs.append({"id": r.get("id"), "name": r.get("name", f"Run {r.get('id')}"), "status": status})
            return runs
        return []
    
    async def fetch_attachments(self, username: str, domain: str, project: str, entity_type: str, entity_id: str) -> List[Dict]:
        """Fetch attachments using generic attachments endpoint with parent_type filter."""
        # Single attachments endpoint with parent_type and parent_id
        result = await self.fetch_and_store("attachments", username, domain, project, 
                                           parent_type=entity_type, parent_id=entity_id)
        if result["success"]:
            # Query MongoDB to get parsed entities
            cursor = self.db.attachments.find({
                "user": username, 
                "parent_id": entity_id,
                "parent_type": entity_type
            })
            attachments = []
            async for a in cursor:
                # Extract file-size from fields array
                file_size = None
                for field in a.get("fields", []):
                    if field.get("field") == "file-size":
                        file_size = field.get("value")
                        break
                
                attachments.append({
                    "id": a.get("id"), 
                    "name": a.get("name", "Unnamed"),
                    "file-size": file_size,
                    "sanitized_name": self.sanitize_name(a.get("name", "attachment"))
                })
            return attachments
        return []
    
    # =========================================================================
    # SINGLE ENTITY FETCH (for details)
    # =========================================================================
    
    async def fetch_test_details(self, username: str, domain: str, project: str, test_id: str) -> Dict[str, Any]:
        """Fetch single test with design steps."""
        if not await self._ensure_authenticated(username):
            return {}
        
        url = f"{ALMConfig.build_alm_url(self.base_url, 'tests', domain=domain, project=project)}/{test_id}"
        test_data = await self._make_request_with_retry(url, "GET", username=username)
        
        if test_data:
            entity = ALMConfig.parse_alm_response_to_entity("tests", test_data, username, None)
            
            # Fetch design steps
            steps_url = f"{url}/design-steps"
            steps_data = await self._make_request_with_retry(steps_url, "GET", username=username)
            entity["design_steps"] = steps_data.get("entities", []) if steps_data else []
            
            # Remove fields array to keep export clean (field values are already at top level)
            entity.pop("fields", None)
            
            await self.db.testplan_tests.replace_one({"user": username, "id": entity["id"]}, entity, upsert=True)
            return entity
        
        return {}
    
    async def fetch_defect_details(self, username: str, domain: str, project: str, defect_id: str) -> Dict[str, Any]:
        """Fetch single defect details."""
        if not await self._ensure_authenticated(username):
            return {}
        
        url = f"{ALMConfig.build_alm_url(self.base_url, 'defects', domain=domain, project=project)}/{defect_id}"
        defect_data = await self._make_request_with_retry(url, "GET", username=username)
        
        if defect_data:
            entity = ALMConfig.parse_alm_response_to_entity("defects", defect_data, username, project)
            # Remove fields array to keep export clean (field values are already at top level)
            entity.pop("fields", None)
            await self.db.defects.replace_one({"user": username, "id": entity["id"]}, entity, upsert=True)
            return entity
        
        return {}
    
    async def fetch_run_details(self, username: str, domain: str, project: str, run_id: str) -> Dict[str, Any]:
        """Fetch single run with run steps."""
        if not await self._ensure_authenticated(username):
            return {}
        
        url = f"{ALMConfig.build_alm_url(self.base_url, 'test-runs', domain=domain, project=project)}/{run_id}"
        run_data = await self._make_request_with_retry(url, "GET", username=username)
        
        if run_data:
            entity = ALMConfig.parse_alm_response_to_entity("test-runs", run_data, username, None)
            
            # Fetch run steps
            steps_url = f"{url}/run-steps"
            steps_data = await self._make_request_with_retry(steps_url, "GET", username=username)
            entity["run_steps"] = steps_data.get("entities", []) if steps_data else []
            
            await self.db.testlab_testruns.replace_one({"user": username, "id": entity["id"]}, entity, upsert=True)
            return entity
        
        return {}
    
    async def download_attachment(self, username: str, domain: str, project: str, attachment_id: str, 
                                 entity_type: str = "attachment") -> bytes:
        """Download attachment with retry using class cookies."""
        if not await self._ensure_authenticated(username):
            return b""
        
        url = f"{self.base_url}/rest/domains/{domain}/projects/{project}/attachments/{attachment_id}"
        
        for attempt in range(1, 4):
            try:
                # Build headers with class cookies
                headers = {"Accept": "*/*"}
                cookies = []
                if self.lwsso_cookie: cookies.append(f"LWSSO_COOKIE_KEY={self.lwsso_cookie}")
                if self.qc_session_cookie: cookies.append(f"QCSession={self.qc_session_cookie}")
                if self.alm_user_cookie: cookies.append(f"ALM_USER={self.alm_user_cookie}")
                if self.xsrf_token: cookies.append(f"XSRF-TOKEN={self.xsrf_token}")
                if cookies:
                    headers["Cookie"] = "; ".join(cookies)
                
                async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                    response = await client.get(url, headers=headers)
                    
                    # Update class cookies from response
                    if response.cookies:
                        if "LWSSO_COOKIE_KEY" in response.cookies:
                            self.lwsso_cookie = response.cookies["LWSSO_COOKIE_KEY"]
                        if "QCSession" in response.cookies:
                            self.qc_session_cookie = response.cookies["QCSession"]
                        if "ALM_USER" in response.cookies:
                            self.alm_user_cookie = response.cookies["ALM_USER"]
                        if "XSRF-TOKEN" in response.cookies:
                            self.xsrf_token = response.cookies["XSRF-TOKEN"]
                    
                    if response.status_code == 200:
                        return response.content
                    elif response.status_code == 401 and attempt < 3:
                        await self._ensure_authenticated(username)
                        continue
            except Exception as e:
                logger.error(f"Download error (attempt {attempt}/3): {str(e)}")
                if attempt < 3:
                    continue
        
        return b""
    
    def sanitize_name(self, name: str) -> str:
        """Sanitize filename."""
        import re
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        return sanitized.strip('. ')[:200] or "unnamed"
