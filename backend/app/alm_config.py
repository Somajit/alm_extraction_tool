"""
alm_config.py

Configuration file for ALM REST API endpoints and entity mappings.
Contains all endpoint patterns, entity types, and field configurations.
"""

from typing import Dict, List, Optional


class ALMConfig:
    """Configuration class for ALM REST API endpoints and entity structures."""
    
    # Authentication endpoints
    AUTH_ENDPOINTS = {
        "authenticate": "/authentication-point/authenticate",
        "site_session": "/rest/site-session",
        "logout": "/authentication-point/logout"
    }
    
    # Comprehensive ALM API endpoint configurations
    # Each endpoint has: path, method, required params, query structure, fields, sort order
    ALM_API_CONFIGS = {
        "domains": {
            "path": "/rest/domains",
            "method": "GET",
            "params": {},
            "fields": ["id", "name"],
            "query_filter": None,
            "sort_by": "name",
            "sort_order": "asc",
            "page_size": None  # No pagination for domains
        },
        "projects": {
            "path": "/rest/domains/{domain}/projects",
            "method": "GET",
            "params": {"domain": "required"},
            "fields": ["id", "name", "description"],
            "query_filter": None,
            "sort_by": "name",
            "sort_order": "asc",
            "page_size": None  # No pagination for projects
        },
        "test-folders": {
            "path": "/rest/domains/{domain}/projects/{project}/test-folders",
            "method": "GET",
            "params": {"domain": "required", "project": "required", "parent_id": "optional"},
            "fields": ["id", "name", "parent-id", "description"],
            "query_filter": "parent-id[{parent_id}]",  # Use {parent_id} placeholder
            "sort_by": "id",
            "sort_order": "asc",
            "page_size": 100
        },
        "tests": {
            "path": "/rest/domains/{domain}/projects/{project}/tests",
            "method": "GET",
            "params": {"domain": "required", "project": "required", "parent_id": "optional"},
            "fields": ["id", "name", "parent-id", "status", "description", "owner", "creation-time"],
            "query_filter": "parent-id[{parent_id}]",
            "sort_by": "id",
            "sort_order": "asc",
            "page_size": 100
        },
        "design-steps": {
            "path": "/rest/domains/{domain}/projects/{project}/design-steps",
            "method": "GET",
            "params": {"domain": "required", "project": "required", "parent_id": "required"},
            "fields": ["id", "name", "parent-id", "step-order", "description", "expected"],
            "query_filter": "parent-id[{parent_id}]",
            "sort_by": "step-order",
            "sort_order": "asc",
            "page_size": 100
        },
        "attachments": {
            "path": "/rest/domains/{domain}/projects/{project}/attachments",
            "method": "GET",
            "params": {
                "domain": "required", 
                "project": "required", 
                "parent_id": "required",
                "parent_type": "required"
            },
            "fields": ["id", "name", "parent-id", "parent-type", "file-size", "description"],
            "query_filter": "parent-id[{parent_id}];parent-type[{parent_type}]",
            "sort_by": "id",
            "sort_order": "asc",
            "page_size": 100
        },
        "attachment-download": {
            "path": "/rest/domains/{domain}/projects/{project}/attachments/{id}",
            "method": "GET",
            "params": {"domain": "required", "project": "required", "id": "required"},
            "fields": [],  # Binary response
            "query_filter": None,
            "sort_by": None,
            "sort_order": None,
            "page_size": None
        },
        "releases": {
            "path": "/rest/domains/{domain}/projects/{project}/releases",
            "method": "GET",
            "params": {"domain": "required", "project": "required"},
            "fields": ["id", "name", "start-date", "end-date", "description"],
            "query_filter": None,
            "sort_by": "id",
            "sort_order": "asc",
            "page_size": 100
        },
        "release-cycles": {
            "path": "/rest/domains/{domain}/projects/{project}/release-cycles",
            "method": "GET",
            "params": {"domain": "required", "project": "required", "parent_id": "optional"},
            "fields": ["id", "name", "parent-id", "start-date", "end-date"],
            "query_filter": "parent-id[{parent_id}]",
            "sort_by": "id",
            "sort_order": "asc",
            "page_size": 100
        },
        "test-sets": {
            "path": "/rest/domains/{domain}/projects/{project}/test-sets",
            "method": "GET",
            "params": {"domain": "required", "project": "required", "cycle_id": "optional"},
            "fields": ["id", "name", "cycle-id", "status", "open-date"],
            "query_filter": "cycle-id[{cycle_id}]",
            "sort_by": "id",
            "sort_order": "asc",
            "page_size": 100
        },
        "test-runs": {
            "path": "/rest/domains/{domain}/projects/{project}/runs",
            "method": "GET",
            "params": {"domain": "required", "project": "required", "testset_id": "optional"},
            "fields": ["id", "name", "testcycl-id", "cycle-id", "test-id", "status", "owner", "execution-date"],
            "query_filter": "testcycl-id[{testset_id}]",
            "sort_by": "id",
            "sort_order": "asc",
            "page_size": 100
        },
        "defects": {
            "path": "/rest/domains/{domain}/projects/{project}/defects",
            "method": "GET",
            "params": {"domain": "required", "project": "required"},
            "fields": [
                "id", "name", "status", "severity", "priority", 
                "detected-by", "owner", "creation-time", "detected-in-rcyc",
                "project", "has-attachments", "description"
            ],
            "query_filter": None,
            "sort_by": "id",
            "sort_order": "desc",  # Most recent first
            "page_size": 100
        }
    }
    

    
    # Entity type constants for MongoDB storage
    ENTITY_TYPES = {
        "DOMAIN": "domains",
        "PROJECT": "projects",
        "TEST_FOLDER": "test-folders",
        "TEST": "tests",
        "DESIGN_STEP": "design-steps",
        "ATTACHMENT": "attachments",
        "RELEASE": "releases",
        "RELEASE_CYCLE": "release-cycles",
        "TEST_SET": "test-sets",
        "TEST_RUN": "test-runs",
        "DEFECT": "defects"
    }
    

    

    
    # Entity field display configurations with alias, sequence, and display flag
    ENTITY_FIELD_CONFIG = {
        "users": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": True},
            {"field": "id", "alias": "User ID", "sequence": 2, "display": False},
            {"field": "name", "alias": "Full Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Parent ID", "sequence": 4, "display": False}
        ],
        "domains": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Domain ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Domain Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Parent ID", "sequence": 4, "display": False}
        ],
        "projects": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Project ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Project Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Domain", "sequence": 4, "display": True}
        ],
        "testplan_folders": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Folder ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Folder Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Parent Folder ID", "sequence": 4, "display": False},
            {"field": "description", "alias": "Description", "sequence": 5, "display": True}
        ],
        "testplan_tests": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Test ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Test Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Parent Folder ID", "sequence": 4, "display": False},
            {"field": "status", "alias": "Status", "sequence": 5, "display": True},
            {"field": "owner", "alias": "Owner", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True},
            {"field": "creation-time", "alias": "Created On", "sequence": 8, "display": True}
        ],
        "testplan_test_design_steps": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Step ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Step Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Test ID", "sequence": 4, "display": False},
            {"field": "step-order", "alias": "Step Order", "sequence": 5, "display": True},
            {"field": "description", "alias": "Description", "sequence": 6, "display": True},
            {"field": "expected", "alias": "Expected Result", "sequence": 7, "display": True}
        ],
        "testplan_folder_attachments": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Attachment ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "File Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Folder ID", "sequence": 4, "display": False},
            {"field": "parent_type", "alias": "Parent Type", "sequence": 5, "display": False},
            {"field": "file-size", "alias": "File Size", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True}
        ],
        "testplan_test_attachments": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Attachment ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "File Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Test ID", "sequence": 4, "display": False},
            {"field": "parent_type", "alias": "Parent Type", "sequence": 5, "display": False},
            {"field": "file-size", "alias": "File Size", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True}
        ],
        "testplan_test_design_step_attachments": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Attachment ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "File Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Step ID", "sequence": 4, "display": False},
            {"field": "parent_type", "alias": "Parent Type", "sequence": 5, "display": False},
            {"field": "file-size", "alias": "File Size", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True}
        ],
        "testlab_releases": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Release ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Release Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Project ID", "sequence": 4, "display": False},
            {"field": "start-date", "alias": "Start Date", "sequence": 5, "display": True},
            {"field": "end-date", "alias": "End Date", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True}
        ],
        "testlab_release_cycles": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Cycle ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Cycle Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Release ID", "sequence": 4, "display": False},
            {"field": "start-date", "alias": "Start Date", "sequence": 5, "display": True},
            {"field": "end-date", "alias": "End Date", "sequence": 6, "display": True}
        ],
        "testlab_testsets": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Test Set ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Test Set Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Cycle ID", "sequence": 4, "display": False},
            {"field": "status", "alias": "Status", "sequence": 5, "display": True},
            {"field": "open-date", "alias": "Open Date", "sequence": 6, "display": True}
        ],
        "testlab_testruns": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Test Run ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Test Run Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Test Set ID", "sequence": 4, "display": False},
            {"field": "test-id", "alias": "Test Case ID", "sequence": 5, "display": True},
            {"field": "status", "alias": "Status", "sequence": 6, "display": True},
            {"field": "owner", "alias": "Owner", "sequence": 7, "display": True},
            {"field": "execution-date", "alias": "Execution Date", "sequence": 8, "display": True}
        ],
        "testlab_testset_attachments": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Attachment ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "File Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Test Set ID", "sequence": 4, "display": False},
            {"field": "parent_type", "alias": "Parent Type", "sequence": 5, "display": False},
            {"field": "file-size", "alias": "File Size", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True}
        ],
        "defects": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Defect ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "Defect Summary", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Project ID", "sequence": 4, "display": False},
            {"field": "status", "alias": "Status", "sequence": 5, "display": True},
            {"field": "severity", "alias": "Severity", "sequence": 6, "display": True},
            {"field": "priority", "alias": "Priority", "sequence": 7, "display": True},
            {"field": "owner", "alias": "Owner", "sequence": 8, "display": True},
            {"field": "detected-by", "alias": "Detected By", "sequence": 9, "display": True},
            {"field": "assigned-to", "alias": "Assigned To", "sequence": 10, "display": True},
            {"field": "creation-time", "alias": "Created On", "sequence": 11, "display": True},
            {"field": "last-modified", "alias": "Last Modified", "sequence": 12, "display": True},
            {"field": "detected-in-rel", "alias": "Detected In Release", "sequence": 13, "display": True},
            {"field": "detected-in-rcyc", "alias": "Detected In Cycle", "sequence": 14, "display": True},
            {"field": "target-rel", "alias": "Target Release", "sequence": 15, "display": True},
            {"field": "target-rcyc", "alias": "Target Cycle", "sequence": 16, "display": True},
            {"field": "reproducible", "alias": "Reproducible", "sequence": 17, "display": True},
            {"field": "has-attachments", "alias": "Has Attachments", "sequence": 18, "display": True},
            {"field": "description", "alias": "Description", "sequence": 19, "display": True},
            {"field": "steps-to-reproduce", "alias": "Steps to Reproduce", "sequence": 20, "display": True},
            {"field": "expected-result", "alias": "Expected Result", "sequence": 21, "display": True},
            {"field": "actual-result", "alias": "Actual Result", "sequence": 22, "display": True},
            {"field": "resolution", "alias": "Resolution", "sequence": 23, "display": True}
        ],
        "attachments": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Attachment ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "File Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Parent ID", "sequence": 4, "display": False},
            {"field": "parent_type", "alias": "Parent Type", "sequence": 5, "display": False},
            {"field": "file-size", "alias": "File Size", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True}
        ],
        "defect_attachments": [
            {"field": "user", "alias": "Username", "sequence": 1, "display": False},
            {"field": "id", "alias": "Attachment ID", "sequence": 2, "display": True},
            {"field": "name", "alias": "File Name", "sequence": 3, "display": True},
            {"field": "parent_id", "alias": "Defect ID", "sequence": 4, "display": False},
            {"field": "parent_type", "alias": "Parent Type", "sequence": 5, "display": False},
            {"field": "file-size", "alias": "File Size", "sequence": 6, "display": True},
            {"field": "description", "alias": "Description", "sequence": 7, "display": True}
        ]
    }
    
    # Parent-child relationships for entity hierarchy
    PARENT_CHILD_RELATIONS = {
        "domain": {
            "children": ["project"]
        },
        "project": {
            "parent": "domain",
            "children": ["test-folder", "release", "defect"]
        },
        "test-folder": {
            "parent": "test-folder",  # Self-referencing
            "children": ["test-folder", "test", "attachment"]
        },
        "test": {
            "parent": "test-folder",
            "children": ["design-step", "attachment"]
        },
        "design-step": {
            "parent": "test",
            "children": []
        },
        "release": {
            "parent": "project",
            "children": ["release-cycle"]
        },
        "release-cycle": {
            "parent": "release",
            "children": ["test-set"]
        },
        "test-set": {
            "parent": "release-cycle",
            "children": ["test-run", "attachment"]
        },
        "test-run": {
            "parent": "test-set",
            "children": []
        },
        "defect": {
            "parent": "project",
            "children": ["attachment"]
        },
        "attachment": {
            "parent": None,  # Can have multiple parent types
            "children": []
        }
    }
    
    # Headers for different request types
    HEADERS = {
        "json": {
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        "xml": {
            "Accept": "application/xml",
            "Content-Type": "application/xml"
        },
        "octet_stream": {
            "Accept": "application/octet-stream"
        }
    }
    
    # Pagination settings
    PAGINATION = {
        "default_page_size": 100,
        "max_page_size": 500,
        "start_index_param": "start-index",  # 1-based indexing
        "page_size_param": "page-size"
    }
    
    @staticmethod
    def get_alm_api_config(endpoint_name: str) -> Dict:
        """
        Get complete API configuration for an endpoint.
        
        Args:
            endpoint_name: Name of the endpoint (e.g., 'test-folders', 'tests')
        
        Returns:
            Dictionary with path, method, params, fields, query, sort, pagination
        """
        config = ALMConfig.ALM_API_CONFIGS.get(endpoint_name)
        if not config:
            raise ValueError(f"Unknown API endpoint: {endpoint_name}")
        return config.copy()
    
    @staticmethod
    def build_alm_url(base_url: str, endpoint_name: str, **path_params) -> str:
        """
        Build complete ALM URL with base URL and path parameters.
        
        Args:
            base_url: Base URL (from .env - ALM_URL or MOCK_ALM_URL)
            endpoint_name: Name of the endpoint
            **path_params: Path parameters (domain, project, id, etc.)
        
        Returns:
            Complete formatted URL
        
        Example:
            build_alm_url("http://alm.example.com", "tests", 
                         domain="DEFAULT", project="MyProject")
            -> "http://alm.example.com/rest/domains/DEFAULT/projects/MyProject/tests"
        """
        config = ALMConfig.get_alm_api_config(endpoint_name)
        path = config["path"].format(**path_params)
        return f"{base_url.rstrip('/')}{path}"
    
    @staticmethod
    def build_query_params(endpoint_name: str, start_index: int = 1, 
                          page_size: Optional[int] = None, **filter_params) -> Dict[str, str]:
        """
        Build query parameters for ALM API call.
        
        Args:
            endpoint_name: Name of the endpoint
            start_index: Starting index for pagination (1-based)
            page_size: Number of items per page (uses config default if None)
            **filter_params: Filter parameters (parent_id, parent_type, cycle_id, etc.)
        
        Returns:
            Dictionary of query parameters
        
        Example:
            build_query_params("test-folders", parent_id="123")
            -> {"query": "{parent-id[123]}", "page-size": "100", "start-index": "1"}
        """
        config = ALMConfig.get_alm_api_config(endpoint_name)
        params = {}
        
        # Add pagination if configured
        if config.get("page_size"):
            if page_size is None:
                page_size = config["page_size"]
            params["page-size"] = str(page_size)
            params["start-index"] = str(start_index)
        
        # Build query filter
        if config.get("query_filter"):
            query = config["query_filter"]
            # Replace placeholders with actual values
            for key, value in filter_params.items():
                placeholder = f"{{{key}}}"
                if placeholder in query:
                    query = query.replace(placeholder, str(value))
            # Only add query if all required placeholders were replaced
            if "{" not in query or "}" not in query:
                params["query"] = f"{{{query}}}"
        
        # Add sort parameters
        if config.get("sort_by"):
            params["order-by"] = f"{{{config['sort_by']}[{config.get('sort_order', 'asc')}]}}"
        
        # Add fields parameter
        if config.get("fields"):
            params["fields"] = ",".join(config["fields"])
        
        return params
    
    @staticmethod
    def parse_alm_response_to_entity(endpoint_name: str, response_data: Dict, 
                                      username: str, parent_id: Optional[str] = None) -> Dict:
        """
        Parse ALM API response and convert to standardized entity format.
        
        Args:
            endpoint_name: Name of the endpoint
            response_data: Raw response data from ALM (single entity)
            username: Username for the entity
            parent_id: Parent ID (if applicable)
        
        Returns:
            Standardized entity dict with structure:
            {
                "user": "username",
                "id": "123",
                "name": "Entity Name",
                "parent_id": "parent_id",
                "entity_type": "test-folder",
                "fields": [
                    {"field": "id", "alias": "Folder ID", "sequence": 2, "display": True, "value": "123"},
                    {"field": "name", "alias": "Folder Name", "sequence": 3, "display": True, "value": "Entity Name"},
                    ...
                ]
            }
        """
        config = ALMConfig.get_alm_api_config(endpoint_name)
        
        # Extract field values from ALM response
        # ALM responses typically have structure: {"Fields": [{"Name": "id", "values": [{"value": "123"}]}]}
        field_values = {}
        
        if "Fields" in response_data:
            for field in response_data["Fields"]:
                field_name = field.get("Name")
                values = field.get("values", [])
                if values:
                    field_values[field_name] = values[0].get("value")
        
        # Build standardized entity
        entity = {
            "user": username,
            "id": field_values.get("id", ""),
            "name": field_values.get("name", ""),
            "parent_id": parent_id or field_values.get("parent-id", None),
            "entity_type": endpoint_name,
            "fields": []
        }
        
        # For attachments, explicitly store parent_type
        if endpoint_name == "attachments":
            entity["parent_type"] = field_values.get("parent-type", "")
        
        # Get collection name and field config
        parent_type = field_values.get("parent-type") if endpoint_name == "attachments" else None
        collection_name = ALMConfig.get_collection_name_from_entity_type(
            endpoint_name if endpoint_name != "attachments" else "attachment",
            parent_type
        )
        field_configs = ALMConfig.get_field_config(collection_name)
        
        # Build fields array with metadata
        for field_config in field_configs:
            field_name = field_config["field"]
            field_value = None
            
            # Map special fields
            if field_name == "user":
                field_value = username
            elif field_name == "parent_id":
                field_value = entity["parent_id"]
            elif field_name == "parent_type" and endpoint_name == "attachments":
                # For attachments, parent_type was already set from parent-type field
                field_value = entity.get("parent_type")
            else:
                field_value = field_values.get(field_name)
            
            entity["fields"].append({
                "field": field_name,
                "alias": field_config["alias"],
                "sequence": field_config["sequence"],
                "display": field_config["display"],
                "value": field_value
            })
            
            # Also store at top level for easy access (but don't overwrite parent_type for attachments)
            if not (field_name == "parent_type" and endpoint_name == "attachments"):
                entity[field_name] = field_value
        
        return entity
    
    @staticmethod
    def entity_to_display_format(entity: Dict) -> Dict:
        """
        Convert entity to display format (alias as keys, only display=True fields).
        
        Args:
            entity: Entity dict with fields array
        
        Returns:
            Dict with aliases as keys: {"Folder ID": "123", "Folder Name": "My Folder", ...}
        """
        display_data = {}
        for field in entity.get("fields", []):
            if field.get("display", False):
                display_data[field["alias"]] = field["value"]
        return display_data
    
    @staticmethod
    def get_endpoint(entity_type: str, **kwargs) -> str:
        """
        Get formatted endpoint path for an entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'test-folders', 'tests')
            **kwargs: Values to format into the endpoint (domain, project, id, etc.)
        
        Returns:
            Formatted endpoint path
        """
        config = ALMConfig.get_alm_api_config(entity_type)
        return config["path"].format(**kwargs)
    
    @staticmethod
    def get_query_params(entity_type: str, parent_id: Optional[str] = None, 
                        parent_type: Optional[str] = None,
                        start_index: int = 1, page_size: Optional[int] = None,
                        custom_query: Optional[str] = None) -> Dict[str, str]:
        """
        Build query parameters for entity fetch. Wrapper around build_query_params.
        
        Args:
            entity_type: Type of entity
            parent_id: Parent entity ID
            parent_type: Parent entity type (for attachments)
            start_index: Starting index for pagination (1-based)
            page_size: Number of items per page
            custom_query: Custom query filter
        
        Returns:
            Dictionary of query parameters
        """
        # Use build_query_params which reads from ALM_API_CONFIGS
        filter_params = {}
        if parent_id:
            filter_params["parent_id"] = parent_id
        if parent_type:
            filter_params["parent_type"] = parent_type
        
        params = ALMConfig.build_query_params(entity_type, start_index, page_size, **filter_params)
        
        # Add custom query if provided
        if custom_query:
            if "query" in params:
                params["query"] = params["query"].rstrip("}") + f";{custom_query}}}"
            else:
                params["query"] = f"{{{custom_query}}}"
        
        return params
    
    @staticmethod
    def get_entity_fields(entity_type: str) -> List[str]:
        """Get list of fields to extract for an entity type from ALM_API_CONFIGS."""
        config = ALMConfig.get_alm_api_config(entity_type)
        return config.get("fields", [])
    
    @staticmethod
    def get_parent_child_relation(entity_type: str) -> Dict[str, List[str]]:
        """Get parent-child relationship configuration for an entity type."""
        return ALMConfig.PARENT_CHILD_RELATIONS.get(entity_type, {})
    
    @staticmethod
    def get_field_config(collection_name: str) -> List[Dict[str, any]]:
        """Get field configuration for a collection."""
        return ALMConfig.ENTITY_FIELD_CONFIG.get(collection_name, [])
    
    @staticmethod
    def get_display_fields(collection_name: str) -> List[Dict[str, any]]:
        """
        Get displayable fields for a collection, sorted by sequence.
        Returns only fields where display=True, sorted by sequence.
        """
        all_fields = ALMConfig.ENTITY_FIELD_CONFIG.get(collection_name, [])
        display_fields = [f for f in all_fields if f.get("display", False)]
        return sorted(display_fields, key=lambda x: x.get("sequence", 999))
    
    @staticmethod
    def get_field_alias(collection_name: str, field_name: str) -> str:
        """Get display alias for a field, or return field name if not found."""
        all_fields = ALMConfig.ENTITY_FIELD_CONFIG.get(collection_name, [])
        for field_config in all_fields:
            if field_config.get("field") == field_name:
                return field_config.get("alias", field_name)
        return field_name
    
    @staticmethod
    def transform_to_display_format(collection_name: str, data: Dict[str, any]) -> Dict[str, any]:
        """
        Transform data dictionary to display format using aliases.
        Only includes fields where display=True, with keys as aliases.
        """
        display_fields = ALMConfig.get_display_fields(collection_name)
        transformed = {}
        for field_config in display_fields:
            field_name = field_config["field"]
            alias = field_config["alias"]
            if field_name in data:
                transformed[alias] = data[field_name]
        return transformed
    
    @staticmethod
    def get_collection_name_from_entity_type(entity_type: str, parent_type: Optional[str] = None) -> str:
        """Map ALM entity type to MongoDB collection name."""
        mapping = {
            "domain": "domains",
            "domains": "domains",
            "project": "projects",
            "projects": "projects",
            "test-folder": "testplan_folders",
            "test-folders": "testplan_folders",
            "test": "testplan_tests",
            "tests": "testplan_tests",
            "design-step": "testplan_test_design_steps",
            "design-steps": "testplan_test_design_steps",
            "release": "testlab_releases",
            "releases": "testlab_releases",
            "release-cycle": "testlab_release_cycles",
            "release-cycles": "testlab_release_cycles",
            "test-set": "testlab_testsets",
            "test-sets": "testlab_testsets",
            "test-run": "testlab_testruns",
            "test-runs": "testlab_testruns",
            "runs": "testlab_testruns",
            "defect": "defects",
            "defects": "defects",
            "attachment": "attachments",
            "attachments": "attachments"
        }
        
        # Handle attachments based on parent type
        if entity_type == "attachment":
            if parent_type == "test-folder":
                return "testplan_folder_attachments"
            elif parent_type == "test":
                return "testplan_test_attachments"
            elif parent_type == "design-step":
                return "testplan_test_design_step_attachments"
            elif parent_type == "test-set":
                return "testlab_testset_attachments"
            elif parent_type == "defect":
                return "defect_attachments"
            else:
                return "testplan_folder_attachments"  # Default
        
        return mapping.get(entity_type, entity_type)
