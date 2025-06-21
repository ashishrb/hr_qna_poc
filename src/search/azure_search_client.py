# src/search/azure_search_client.py
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings

class AzureSearchClient:
    def __init__(self, index_name: str = "hr-employees-fixed"):
        self.index_name = index_name
        self.endpoint = settings.azure_search_endpoint
        self.api_key = settings.azure_search_api_key
        
        # Initialize clients
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.api_key)
        )
        
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
    
    def search(self, query: str, top_k: int = 5, filters: str = None, 
               select_fields: List[str] = None) -> List[Dict[str, Any]]:
        """Perform basic text search"""
        try:
            results = self.search_client.search(
                search_text=query,
                filter=filters,
                select=select_fields,
                top=top_k,
                include_total_count=True
            )
            
            search_results = []
            for result in results:
                search_results.append(dict(result))
            
            return search_results
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def vector_search(self, query_vector: List[float], top_k: int = 5, 
                     filters: str = None) -> List[Dict[str, Any]]:
        """Perform vector search"""
        try:
            results = self.search_client.search(
                search_text=None,
                vector_queries=[{
                    "kind": "vector",
                    "vector": query_vector,
                    "fields": "content_vector",
                    "k": top_k
                }],
                filter=filters,
                top=top_k
            )
            
            search_results = []
            for result in results:
                search_results.append(dict(result))
            
            return search_results
        except Exception as e:
            print(f"❌ Vector search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, query_vector: List[float], 
                     top_k: int = 5, filters: str = None) -> List[Dict[str, Any]]:
        """Perform hybrid search (text + vector)"""
        try:
            results = self.search_client.search(
                search_text=query,
                vector_queries=[{
                    "kind": "vector",
                    "vector": query_vector,
                    "fields": "content_vector",
                    "k": top_k
                }],
                filter=filters,
                top=top_k,
                query_type="semantic",
                semantic_configuration_name="hr-semantic-config"
            )
            
            search_results = []
            for result in results:
                search_results.append(dict(result))
            
            return search_results
        except Exception as e:
            print(f"❌ Hybrid search failed: {e}")
            return []
    
    def upload_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Upload documents to search index"""
        try:
            result = self.search_client.upload_documents(documents=documents)
            return True
        except Exception as e:
            print(f"❌ Document upload failed: {e}")
            return False
    
    def delete_documents(self, document_keys: List[str]) -> bool:
        """Delete documents from search index"""
        try:
            documents = [{"id": key} for key in document_keys]
            result = self.search_client.delete_documents(documents=documents)
            return True
        except Exception as e:
            print(f"❌ Document deletion failed: {e}")
            return False
    
    def get_document_count(self) -> int:
        """Get total document count in index"""
        try:
            results = self.search_client.search("*", include_total_count=True, top=0)
            return results.get_count()
        except Exception as e:
            print(f"❌ Failed to get document count: {e}")
            return 0
    
    def get_facets(self, facet_fields: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Get facet information"""
        try:
            results = self.search_client.search(
                "*",
                facets=facet_fields,
                top=0
            )
            
            facets = results.get_facets()
            return facets or {}
        except Exception as e:
            print(f"❌ Failed to get facets: {e}")
            return {}
    
    def suggest(self, query: str, suggester_name: str = "sg", top_k: int = 5) -> List[str]:
        """Get search suggestions"""
        try:
            results = self.search_client.suggest(
                search_text=query,
                suggester_name=suggester_name,
                top=top_k
            )
            
            suggestions = []
            for result in results:
                suggestions.append(result["text"])
            
            return suggestions
        except Exception as e:
            print(f"❌ Suggestions failed: {e}")
            return []

# Global instance
azure_search_client = AzureSearchClient()