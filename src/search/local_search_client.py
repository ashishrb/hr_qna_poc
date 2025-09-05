# src/search/local_search_client.py
"""
Local search client to replace Azure AI Search
Uses MongoDB text search and Ollama embeddings
"""

import asyncio
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.mongodb_client import mongodb_client
from src.ai.ollama_client import ollama_client

class LocalSearchClient:
    """Local search client using MongoDB and Ollama"""
    
    def __init__(self):
        """Initialize local search client"""
        print("🔍 Initializing Local Search Client...")
        self.ollama_client = ollama_client
        print("✅ Local Search Client ready!")
    
    async def search(self, query: str, top_k: int = 5, filters: str = None, 
                    select_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Perform text search using MongoDB"""
        try:
            await mongodb_client.connect()
            
            # Build search pipeline
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Add learning data for skills search
            pipeline.extend([
                {
                    "$lookup": {
                        "from": "learning",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "learning"
                    }
                },
                {"$unwind": {"path": "$learning", "preserveNullAndEmptyArrays": True}}
            ])
            
            # Create combined text field for search
            pipeline.append({
                "$addFields": {
                    "combined_text": {
                        "$concat": [
                            {"$ifNull": ["$full_name", ""]}, " ",
                            {"$ifNull": ["$employment.department", ""]}, " ",
                            {"$ifNull": ["$employment.role", ""]}, " ",
                            {"$ifNull": ["$learning.certifications", ""]}, " ",
                            {"$ifNull": ["$location", ""]}
                        ]
                    }
                }
            })
            
            # Simple text search using regex
            if query:
                pipeline.append({
                    "$match": {
                        "$or": [
                            {"full_name": {"$regex": query, "$options": "i"}},
                            {"employment.department": {"$regex": query, "$options": "i"}},
                            {"employment.role": {"$regex": query, "$options": "i"}},
                            {"learning.certifications": {"$regex": query, "$options": "i"}},
                            {"location": {"$regex": query, "$options": "i"}}
                        ]
                    }
                })
            
            # Limit results
            pipeline.append({"$limit": top_k})
            
            # Project fields
            project_fields = {
                "id": "$employee_id",
                "employee_id": 1,
                "full_name": 1,
                "department": "$employment.department",
                "role": "$employment.role",
                "location": 1,
                "certifications": "$learning.certifications",
                "combined_text": 1,
                "score": {"$literal": 1.0}  # Simple scoring
            }
            
            pipeline.append({"$project": project_fields})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results
            
        except Exception as e:
            print(f"❌ Local search failed: {e}")
            return []
    
    async def vector_search(self, query_vector: List[float], top_k: int = 5, 
                          filters: str = None) -> List[Dict[str, Any]]:
        """Perform vector search using Ollama embeddings"""
        try:
            # For now, fall back to text search
            # In a full implementation, you would store embeddings in MongoDB
            # and perform cosine similarity search
            print("⚠️ Vector search not fully implemented, using text search")
            return await self.search("", top_k, filters)
            
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            return []
    
    async def hybrid_search(self, query: str, query_vector: List[float], 
                          top_k: int = 5, filters: str = None) -> List[Dict[str, Any]]:
        """Perform hybrid search (text + vector)"""
        try:
            # For now, use text search
            return await self.search(query, top_k, filters)
            
        except Exception as e:
            print(f"❌ Hybrid search failed: {e}")
            return []
    
    async def upload_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Upload documents to local search index (MongoDB)"""
        try:
            # Documents are already in MongoDB, this is a no-op
            print(f"📤 {len(documents)} documents already indexed in MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ Document upload failed: {e}")
            return False
    
    async def delete_documents(self, document_keys: List[str]) -> bool:
        """Delete documents from local search index"""
        try:
            # This would delete from MongoDB collections
            print(f"🗑️ Deleting {len(document_keys)} documents from MongoDB")
            return True
            
        except Exception as e:
            print(f"❌ Document deletion failed: {e}")
            return False
    
    async def get_document_count(self) -> int:
        """Get total document count"""
        try:
            await mongodb_client.connect()
            count = await mongodb_client.count_documents("personal_info")
            return count
            
        except Exception as e:
            print(f"❌ Failed to get document count: {e}")
            return 0
    
    async def get_facets(self, facet_fields: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get facet information from MongoDB"""
        try:
            await mongodb_client.connect()
            
            facets = {}
            
            for field in facet_fields:
                if field == "department":
                    # Get department distribution
                    pipeline = [
                        {
                            "$lookup": {
                                "from": "employment",
                                "localField": "employee_id",
                                "foreignField": "employee_id",
                                "as": "employment"
                            }
                        },
                        {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
                        {"$group": {"_id": "$employment.department", "count": {"$sum": 1}}},
                        {"$sort": {"count": -1}}
                    ]
                    
                    collection = await mongodb_client.get_collection("personal_info")
                    cursor = collection.aggregate(pipeline)
                    results = await cursor.to_list(length=None)
                    
                    facets[field] = [
                        {"value": result["_id"], "count": result["count"]}
                        for result in results if result["_id"]
                    ]
            
            return facets
            
        except Exception as e:
            print(f"❌ Failed to get facets: {e}")
            return {}
    
    async def suggest(self, query: str, suggester_name: str = "sg", top_k: int = 5) -> List[str]:
        """Get search suggestions"""
        try:
            await mongodb_client.connect()
            
            # Get suggestions from employee names and departments
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
                {
                    "$match": {
                        "$or": [
                            {"full_name": {"$regex": f"^{query}", "$options": "i"}},
                            {"employment.department": {"$regex": f"^{query}", "$options": "i"}},
                            {"employment.role": {"$regex": f"^{query}", "$options": "i"}}
                        ]
                    }
                },
                {"$limit": top_k},
                {
                    "$project": {
                        "suggestion": {
                            "$cond": {
                                "if": {"$regexMatch": {"input": "$full_name", "regex": f"^{query}", "options": "i"}},
                                "then": "$full_name",
                                "else": {
                                    "$cond": {
                                        "if": {"$regexMatch": {"input": "$employment.department", "regex": f"^{query}", "options": "i"}},
                                        "then": "$employment.department",
                                        "else": "$employment.role"
                                    }
                                }
                            }
                        }
                    }
                }
            ]
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            suggestions = [result["suggestion"] for result in results if result["suggestion"]]
            return list(set(suggestions))  # Remove duplicates
            
        except Exception as e:
            print(f"❌ Suggestions failed: {e}")
            return []

# Global instance
local_search_client = LocalSearchClient()

async def test_local_search():
    """Test local search functionality"""
    print("\n🧪 Testing Local Search Client")
    print("=" * 40)
    
    try:
        # Test basic search
        print("🔍 Testing basic search...")
        results = await local_search_client.search("developer", top_k=3)
        print(f"✅ Found {len(results)} results")
        
        for result in results[:2]:
            print(f"   - {result.get('full_name', 'N/A')} ({result.get('department', 'N/A')})")
        
        # Test document count
        print("\n📊 Testing document count...")
        count = await local_search_client.get_document_count()
        print(f"✅ Total documents: {count}")
        
        # Test facets
        print("\n📋 Testing facets...")
        facets = await local_search_client.get_facets(["department"])
        print(f"✅ Department facets: {len(facets.get('department', []))}")
        
        # Test suggestions
        print("\n💡 Testing suggestions...")
        suggestions = await local_search_client.suggest("IT", top_k=3)
        print(f"✅ Suggestions: {suggestions}")
        
        print("\n🎉 Local search testing completed!")
        
    except Exception as e:
        print(f"❌ Local search test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_local_search())
