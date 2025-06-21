# src/database/mongodb_client.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List, Any, Optional
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings

class MongoDBClient:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance
    
    async def connect(self):
        """Connect to MongoDB Atlas"""
        if self._client is None:
            try:
                self._client = AsyncIOMotorClient(settings.mongodb_connection_string)
                self._db = self._client[settings.mongodb_database]
                
                # Test connection
                await self._client.admin.command('ping')
                print("✅ Connected to MongoDB Atlas")
                return True
            except Exception as e:
                print(f"❌ MongoDB connection failed: {e}")
                return False
        return True
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            print("🔐 MongoDB connection closed")
    
    @property
    def database(self):
        """Get database instance"""
        return self._db
    
    @property
    def client(self):
        """Get client instance"""
        return self._client
    
    async def get_collection(self, collection_name: str):
        """Get a specific collection"""
        if self._db is None:
            await self.connect()
        return self._db[collection_name]
    
    async def insert_document(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document"""
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            print(f"❌ Failed to insert document: {e}")
            return None
    
    async def insert_documents(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents"""
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            print(f"❌ Failed to insert documents: {e}")
            return []
    
    async def find_document(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document"""
        try:
            collection = await self.get_collection(collection_name)
            document = await collection.find_one(filter_dict)
            return document
        except Exception as e:
            print(f"❌ Failed to find document: {e}")
            return None
    
    async def find_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        try:
            collection = await self.get_collection(collection_name)
            cursor = collection.find(filter_dict or {})
            if limit:
                cursor = cursor.limit(limit)
            
            documents = []
            async for doc in cursor:
                documents.append(doc)
            return documents
        except Exception as e:
            print(f"❌ Failed to find documents: {e}")
            return []
    
    async def update_document(self, collection_name: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> bool:
        """Update a single document"""
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.update_one(filter_dict, {"$set": update_dict})
            return result.modified_count > 0
        except Exception as e:
            print(f"❌ Failed to update document: {e}")
            return False
    
    async def delete_document(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document"""
        try:
            collection = await self.get_collection(collection_name)
            result = await collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            print(f"❌ Failed to delete document: {e}")
            return False
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in collection"""
        try:
            collection = await self.get_collection(collection_name)
            count = await collection.count_documents(filter_dict or {})
            return count
        except Exception as e:
            print(f"❌ Failed to count documents: {e}")
            return 0
    
    async def get_collections(self) -> List[str]:
        """Get list of all collections"""
        try:
            if self._db is None:
                await self.connect()
            collections = await self._db.list_collection_names()
            return [col for col in collections if not col.startswith('system')]
        except Exception as e:
            print(f"❌ Failed to get collections: {e}")
            return []

# Global instance
mongodb_client = MongoDBClient()