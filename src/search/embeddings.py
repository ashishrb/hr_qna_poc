# src/search/embeddings.py
import asyncio
import json
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings

class EmbeddingsService:
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version="2023-05-15",
            azure_endpoint=settings.azure_openai_endpoint
        )
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="hr-employees-index",
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        self.mongodb_client = None
        self.db = None
        
    async def connect_to_mongodb(self):
        """Connect to MongoDB"""
        try:
            self.mongodb_client = AsyncIOMotorClient(settings.mongodb_connection_string)
            self.db = self.mongodb_client[settings.mongodb_database]
            await self.mongodb_client.admin.command('ping')
            print("✅ Connected to MongoDB")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text"""
        try:
            # Clean and prepare text
            clean_text = text.strip().replace('\n', ' ').replace('\r', '')
            if not clean_text:
                return [0.0] * 1536  # Return zero vector for empty text
            
            response = self.openai_client.embeddings.create(
                input=clean_text,
                model="text-embedding-ada-002"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"❌ Failed to generate embedding: {e}")
            return [0.0] * 1536  # Return zero vector on error
    
    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            try:
                # Clean texts
                clean_texts = []
                for text in batch_texts:
                    clean_text = text.strip().replace('\n', ' ').replace('\r', '')
                    clean_texts.append(clean_text if clean_text else "empty")
                
                response = self.openai_client.embeddings.create(
                    input=clean_texts,
                    model="text-embedding-ada-002"
                )
                
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
                
                print(f"   📊 Generated embeddings for batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
            except Exception as e:
                print(f"   ❌ Failed to generate batch embeddings: {e}")
                # Add zero vectors for failed batch
                all_embeddings.extend([[0.0] * 1536] * len(batch_texts))
        
        return all_embeddings
    
    async def get_documents_without_embeddings(self) -> List[Dict[str, Any]]:
        """Get all documents from search index that don't have embeddings"""
        try:
            # Search for documents without content_vector
            results = self.search_client.search(
                "*",
                filter="content_vector eq null",
                select="id,combined_text,full_name,department,position",
                top=1000
            )
            
            documents = []
            for result in results:
                documents.append({
                    'id': result['id'],
                    'combined_text': result.get('combined_text', ''),
                    'full_name': result.get('full_name', ''),
                    'department': result.get('department', ''),
                    'position': result.get('position', '')
                })
            
            print(f"📊 Found {len(documents)} documents without embeddings")
            return documents
            
        except Exception as e:
            print(f"❌ Failed to get documents: {e}")
            return []
    
    async def update_documents_with_embeddings(self):
        """Update search index documents with generated embeddings"""
        try:
            # Get documents without embeddings
            documents = await self.get_documents_without_embeddings()
            
            if not documents:
                print("✅ All documents already have embeddings")
                return True
            
            print(f"🔄 Generating embeddings for {len(documents)} documents...")
            
            # Prepare texts for embedding
            texts = []
            for doc in documents:
                # Use combined_text as the primary text for embedding
                text = doc.get('combined_text', '')
                if not text:
                    # Fallback to basic info if combined_text is empty
                    text = f"{doc.get('full_name', '')} {doc.get('department', '')} {doc.get('position', '')}"
                texts.append(text)
            
            # Generate embeddings in batches
            embeddings = self.generate_batch_embeddings(texts, batch_size=16)
            
            # Prepare documents for update
            documents_to_update = []
            for i, doc in enumerate(documents):
                update_doc = {
                    'id': doc['id'],
                    'content_vector': embeddings[i]
                }
                documents_to_update.append(update_doc)
            
            # Update documents in batches
            batch_size = 100
            total_updated = 0
            
            for i in range(0, len(documents_to_update), batch_size):
                batch = documents_to_update[i:i + batch_size]
                try:
                    result = self.search_client.merge_or_upload_documents(documents=batch)
                    total_updated += len(batch)
                    print(f"   📤 Updated batch {i//batch_size + 1}: {len(batch)} documents")
                except Exception as e:
                    print(f"   ❌ Failed to update batch {i//batch_size + 1}: {e}")
            
            print(f"🎉 Successfully updated {total_updated} documents with embeddings")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update documents with embeddings: {e}")
            return False
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using vector embeddings"""
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Perform vector search
            results = self.search_client.search(
                search_text=None,
                vector_queries=[{
                    "kind": "vector",
                    "vector": query_embedding,
                    "fields": "content_vector",
                    "k": top_k
                }],
                select="id,full_name,department,position,location,skills,combined_text",
                top=top_k
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    'id': result['id'],
                    'full_name': result.get('full_name', ''),
                    'department': result.get('department', ''),
                    'position': result.get('position', ''),
                    'location': result.get('location', ''),
                    'skills': result.get('skills', ''),
                    'combined_text': result.get('combined_text', ''),
                    'score': result.get('@search.score', 0)
                })
            
            return search_results
            
        except Exception as e:
            print(f"❌ Semantic search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform hybrid search combining text and vector search"""
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Perform hybrid search
            results = self.search_client.search(
                search_text=query,
                vector_queries=[{
                    "kind": "vector",
                    "vector": query_embedding,
                    "fields": "content_vector",
                    "k": top_k
                }],
                select="id,full_name,department,position,location,skills,combined_text",
                top=top_k,
                query_type="semantic",
                semantic_configuration_name="hr-semantic-config"
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    'id': result['id'],
                    'full_name': result.get('full_name', ''),
                    'department': result.get('department', ''),
                    'position': result.get('position', ''),
                    'location': result.get('location', ''),
                    'skills': result.get('skills', ''),
                    'combined_text': result.get('combined_text', ''),
                    'score': result.get('@search.score', 0),
                    'reranker_score': result.get('@search.reranker_score', 0)
                })
            
            return search_results
            
        except Exception as e:
            print(f"❌ Hybrid search failed: {e}")
            return []
    
    def test_search_capabilities(self):
        """Test different search capabilities"""
        print("\n🧪 Testing Search Capabilities")
        print("=" * 40)
        
        test_queries = [
            "software developer with Python skills",
            "manager in sales department",
            "employee in New York",
            "data scientist with machine learning experience"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            # Test semantic search
            semantic_results = self.semantic_search(query, top_k=3)
            print(f"   📊 Semantic Search Results ({len(semantic_results)}):")
            for i, result in enumerate(semantic_results[:2], 1):
                print(f"     {i}. {result['full_name']} - {result['department']} ({result['score']:.3f})")
            
            # Test hybrid search
            hybrid_results = self.hybrid_search(query, top_k=3)
            print(f"   🔀 Hybrid Search Results ({len(hybrid_results)}):")
            for i, result in enumerate(hybrid_results[:2], 1):
                print(f"     {i}. {result['full_name']} - {result['department']} ({result['score']:.3f})")
    
    async def close_connections(self):
        """Close all connections"""
        if self.mongodb_client:
            self.mongodb_client.close()
            print("🔐 MongoDB connection closed")

async def main():
    """Main function to set up embeddings"""
    print("🧠 Embeddings Service Setup Pipeline")
    print("=" * 50)
    
    embeddings_service = EmbeddingsService()
    
    try:
        # Connect to MongoDB
        connected = await embeddings_service.connect_to_mongodb()
        if not connected:
            return
        
        # Update documents with embeddings
        print("\n🔄 Generating and updating embeddings...")
        updated = await embeddings_service.update_documents_with_embeddings()
        if not updated:
            return
        
        # Test search capabilities
        embeddings_service.test_search_capabilities()
        
        print("\n🎉 Embeddings setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
    
    finally:
        await embeddings_service.close_connections()

if __name__ == "__main__":
    asyncio.run(main())