"""
mongo_service.py

Generic MongoDB service layer for storing and retrieving ALM entities and attachments.
Provides CRUD operations with parent-child linkage tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging


class MongoService:
    """Service class for MongoDB operations with entity hierarchy support."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize MongoDB service.
        
        Args:
            db: AsyncIO Motor database instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Collection names
        self.COLLECTIONS = {
            "entities": "entities",
            "attachments": "attachments",
            "attachment_files": "attachment_files"
        }
    
    async def insert_entity(
        self,
        entity_type: str,
        entity_id: str,
        domain: str,
        project: str,
        data: Dict[str, Any],
        parent_id: Optional[str] = None,
        parent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Insert or update an entity in MongoDB.
        
        Args:
            entity_type: Type of entity (test-folder, test, defect, etc.)
            entity_id: Unique ID of the entity
            domain: ALM domain
            project: ALM project
            data: Entity data (all fields)
            parent_id: ID of parent entity
            parent_type: Type of parent entity
            metadata: Additional metadata
        
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db[self.COLLECTIONS["entities"]]
            
            doc = {
                "_id": f"{domain}_{project}_{entity_type}_{entity_id}",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "domain": domain,
                "project": project,
                "parent_id": parent_id,
                "parent_type": parent_type,
                "data": data,
                "metadata": metadata or {},
                "updated_at": datetime.utcnow()
            }
            
            await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": doc},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting entity {entity_type}:{entity_id}: {e}")
            return False
    
    async def get_entity(
        self,
        entity_type: str,
        entity_id: str,
        domain: str,
        project: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an entity from MongoDB.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            domain: ALM domain
            project: ALM project
        
        Returns:
            Entity document or None if not found
        """
        try:
            collection = self.db[self.COLLECTIONS["entities"]]
            doc_id = f"{domain}_{project}_{entity_type}_{entity_id}"
            doc = await collection.find_one({"_id": doc_id})
            return doc
            
        except Exception as e:
            self.logger.error(f"Error retrieving entity {entity_type}:{entity_id}: {e}")
            return None
    
    async def get_children(
        self,
        entity_type: str,
        entity_id: str,
        domain: str,
        project: str,
        child_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all children of an entity.
        
        Args:
            entity_type: Type of parent entity
            entity_id: Parent entity ID
            domain: ALM domain
            project: ALM project
            child_type: Optional filter for specific child type
        
        Returns:
            List of child entity documents
        """
        try:
            collection = self.db[self.COLLECTIONS["entities"]]
            
            query = {
                "domain": domain,
                "project": project,
                "parent_id": entity_id,
                "parent_type": entity_type
            }
            
            if child_type:
                query["entity_type"] = child_type
            
            cursor = collection.find(query)
            children = []
            async for doc in cursor:
                children.append(doc)
            
            return children
            
        except Exception as e:
            self.logger.error(f"Error retrieving children of {entity_type}:{entity_id}: {e}")
            return []
    
    async def bulk_insert_entities(
        self,
        entities: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk insert multiple entities.
        
        Args:
            entities: List of entity documents with all required fields
        
        Returns:
            Number of entities successfully inserted
        """
        try:
            if not entities:
                return 0
            
            collection = self.db[self.COLLECTIONS["entities"]]
            
            operations = []
            for entity in entities:
                operations.append({
                    "updateOne": {
                        "filter": {"_id": entity["_id"]},
                        "update": {"$set": entity},
                        "upsert": True
                    }
                })
            
            result = await collection.bulk_write(operations, ordered=False)
            return result.upserted_count + result.modified_count
            
        except Exception as e:
            self.logger.error(f"Error bulk inserting entities: {e}")
            return 0
    
    async def insert_attachment(
        self,
        attachment_id: str,
        domain: str,
        project: str,
        parent_id: str,
        parent_type: str,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Insert attachment metadata.
        
        Args:
            attachment_id: Attachment ID
            domain: ALM domain
            project: ALM project
            parent_id: Parent entity ID
            parent_type: Parent entity type
            filename: File name
            metadata: Additional metadata (file-size, description, etc.)
        
        Returns:
            True if successful
        """
        try:
            collection = self.db[self.COLLECTIONS["attachments"]]
            
            doc = {
                "_id": f"{domain}_{project}_{attachment_id}",
                "attachment_id": attachment_id,
                "domain": domain,
                "project": project,
                "parent_id": parent_id,
                "parent_type": parent_type,
                "filename": filename,
                "metadata": metadata or {},
                "updated_at": datetime.utcnow()
            }
            
            await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": doc},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting attachment {attachment_id}: {e}")
            return False
    
    async def insert_attachment_file(
        self,
        attachment_id: str,
        domain: str,
        project: str,
        filename: str,
        content: bytes
    ) -> bool:
        """
        Store attachment file content.
        
        Args:
            attachment_id: Attachment ID
            domain: ALM domain
            project: ALM project
            filename: File name
            content: Binary file content
        
        Returns:
            True if successful
        """
        try:
            collection = self.db[self.COLLECTIONS["attachment_files"]]
            
            doc = {
                "_id": f"{domain}_{project}_{attachment_id}",
                "attachment_id": attachment_id,
                "domain": domain,
                "project": project,
                "filename": filename,
                "content": content,
                "downloaded_at": datetime.utcnow()
            }
            
            await collection.update_one(
                {"_id": doc["_id"]},
                {"$set": doc},
                upsert=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing attachment file {attachment_id}: {e}")
            return False
    
    async def get_attachment_file(
        self,
        attachment_id: str,
        domain: str,
        project: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve attachment file content.
        
        Args:
            attachment_id: Attachment ID
            domain: ALM domain
            project: ALM project
        
        Returns:
            Document with filename and content, or None
        """
        try:
            collection = self.db[self.COLLECTIONS["attachment_files"]]
            doc_id = f"{domain}_{project}_{attachment_id}"
            doc = await collection.find_one({"_id": doc_id})
            return doc
            
        except Exception as e:
            self.logger.error(f"Error retrieving attachment file {attachment_id}: {e}")
            return None
    
    async def get_attachments_for_entity(
        self,
        entity_id: str,
        entity_type: str,
        domain: str,
        project: str
    ) -> List[Dict[str, Any]]:
        """
        Get all attachments for a specific entity.
        
        Args:
            entity_id: Entity ID
            entity_type: Entity type
            domain: ALM domain
            project: ALM project
        
        Returns:
            List of attachment metadata documents
        """
        try:
            collection = self.db[self.COLLECTIONS["attachments"]]
            
            query = {
                "domain": domain,
                "project": project,
                "parent_id": entity_id,
                "parent_type": entity_type
            }
            
            cursor = collection.find(query)
            attachments = []
            async for doc in cursor:
                attachments.append(doc)
            
            return attachments
            
        except Exception as e:
            self.logger.error(f"Error retrieving attachments for {entity_type}:{entity_id}: {e}")
            return []
    
    async def query_entities(
        self,
        entity_type: str,
        domain: str,
        project: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query entities with filters.
        
        Args:
            entity_type: Type of entity
            domain: ALM domain
            project: ALM project
            filters: Additional query filters
            limit: Maximum number of results
            skip: Number of results to skip
        
        Returns:
            List of entity documents
        """
        try:
            collection = self.db[self.COLLECTIONS["entities"]]
            
            query = {
                "entity_type": entity_type,
                "domain": domain,
                "project": project
            }
            
            if filters:
                query.update(filters)
            
            cursor = collection.find(query).skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            entities = []
            async for doc in cursor:
                entities.append(doc)
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Error querying entities {entity_type}: {e}")
            return []
    
    async def count_entities(
        self,
        entity_type: str,
        domain: str,
        project: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count entities matching criteria.
        
        Args:
            entity_type: Type of entity
            domain: ALM domain
            project: ALM project
            filters: Additional query filters
        
        Returns:
            Count of matching entities
        """
        try:
            collection = self.db[self.COLLECTIONS["entities"]]
            
            query = {
                "entity_type": entity_type,
                "domain": domain,
                "project": project
            }
            
            if filters:
                query.update(filters)
            
            count = await collection.count_documents(query)
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting entities {entity_type}: {e}")
            return 0
    
    async def delete_entity(
        self,
        entity_type: str,
        entity_id: str,
        domain: str,
        project: str,
        recursive: bool = False
    ) -> bool:
        """
        Delete an entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            domain: ALM domain
            project: ALM project
            recursive: If True, also delete all children
        
        Returns:
            True if successful
        """
        try:
            collection = self.db[self.COLLECTIONS["entities"]]
            
            if recursive:
                # Delete all children first
                await collection.delete_many({
                    "domain": domain,
                    "project": project,
                    "parent_id": entity_id,
                    "parent_type": entity_type
                })
            
            # Delete the entity
            doc_id = f"{domain}_{project}_{entity_type}_{entity_id}"
            result = await collection.delete_one({"_id": doc_id})
            
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"Error deleting entity {entity_type}:{entity_id}: {e}")
            return False
