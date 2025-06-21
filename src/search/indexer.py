# src/search/fixed_indexer.py
import asyncio
import json
from typing import List, Dict, Any
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, 
    SearchableField, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, SemanticConfiguration, SemanticSearch,
    SemanticField, SemanticPrioritizedFields
)
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings

class FixedAzureSearchIndexer:
    def __init__(self):
        self.index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
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
    
    async def get_employee_data(self, employee_id: str) -> Dict[str, Any]:
        """Get comprehensive employee data from all collections"""
        employee_data = {"employee_id": employee_id}
        
        try:
            # Personal Info
            personal = await self.db.personal_info.find_one({"employee_id": employee_id})
            if personal:
                employee_data.update({
                    "full_name": personal.get("full_name", ""),
                    "email": personal.get("email", ""),
                    "location": personal.get("location", ""),
                    "age": personal.get("age", ""),
                    "contact_number": personal.get("contact_number", "")
                })
            
            # Employment Info
            employment = await self.db.employment.find_one({"employee_id": employee_id})
            if employment:
                employee_data.update({
                    "department": employment.get("department", ""),
                    "role": employment.get("role", ""),  # This is the position
                    "grade_band": employment.get("grade_band", ""),
                    "employment_type": employment.get("employment_type", ""),
                    "work_mode": employment.get("work_mode", ""),
                    "joining_date": employment.get("joining_date", "")
                })
            
            # Learning & Skills
            learning = await self.db.learning.find_one({"employee_id": employee_id})
            if learning:
                employee_data.update({
                    "certifications": learning.get("certifications", ""),
                    "courses_completed": learning.get("courses_completed", ""),
                    "learning_hours_ytd": learning.get("learning_hours_ytd", "")
                })
            
            # Experience
            experience = await self.db.experience.find_one({"employee_id": employee_id})
            if experience:
                employee_data.update({
                    "total_experience_years": experience.get("total_experience_years", ""),
                    "years_in_current_company": experience.get("years_in_current_company", ""),
                    "known_skills_count": experience.get("known_skills_count", "")
                })
            
            # Performance
            performance = await self.db.performance.find_one({"employee_id": employee_id})
            if performance:
                employee_data.update({
                    "performance_rating": performance.get("performance_rating", ""),
                    "awards": performance.get("awards", ""),
                    "improvement_areas": performance.get("improvement_areas", "")
                })
            
            # Current Project/Engagement
            engagement = await self.db.engagement.find_one({"employee_id": employee_id})
            if engagement:
                employee_data.update({
                    "current_project": engagement.get("current_project", ""),
                    "engagement_score": engagement.get("engagement_score", ""),
                    "manager_feedback": engagement.get("manager_feedback", "")
                })
            
            # Compensation
            compensation = await self.db.compensation.find_one({"employee_id": employee_id})
            if compensation:
                employee_data.update({
                    "current_salary": compensation.get("current_salary", ""),
                    "total_ctc": compensation.get("total_ctc", "")
                })
            
            return employee_data
            
        except Exception as e:
            print(f"❌ Failed to get employee data for {employee_id}: {e}")
            return employee_data
    
    def create_hr_search_index(self) -> SearchIndex:
        """Create comprehensive HR search index with proper field mapping"""
        
        # Define search fields based on actual data structure
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="employee_id", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="full_name", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
            SearchableField(name="email", type=SearchFieldDataType.String),
            SearchableField(name="department", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="role", type=SearchFieldDataType.String, filterable=True, facetable=True),  # This is position
            SearchableField(name="location", type=SearchFieldDataType.String, filterable=True, facetable=True),
            SearchableField(name="certifications", type=SearchFieldDataType.String),  # This is skills
            SearchableField(name="current_project", type=SearchFieldDataType.String),
            SearchableField(name="improvement_areas", type=SearchFieldDataType.String),
            SearchableField(name="manager_feedback", type=SearchFieldDataType.String),
            SimpleField(name="total_experience_years", type=SearchFieldDataType.Double, filterable=True),
            SimpleField(name="performance_rating", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(name="engagement_score", type=SearchFieldDataType.Int32, filterable=True),
            SearchableField(name="combined_text", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="hr-vector-profile"
            ),
            SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset),
            SimpleField(name="updated_at", type=SearchFieldDataType.DateTimeOffset)
        ]
        
        # Configure vector search
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="hr-vector-profile",
                    algorithm_configuration_name="hr-hnsw-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(
                    name="hr-hnsw-config",
                    parameters={
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                )
            ]
        )
        
        # Configure semantic search
        semantic_config = SemanticConfiguration(
            name="hr-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="full_name"),
                content_fields=[
                    SemanticField(field_name="combined_text"),
                    SemanticField(field_name="certifications"),
                    SemanticField(field_name="current_project")
                ],
                keywords_fields=[
                    SemanticField(field_name="department"),
                    SemanticField(field_name="role"),
                    SemanticField(field_name="location")
                ]
            )
        )
        
        semantic_search = SemanticSearch(configurations=[semantic_config])
        
        # Create the index
        index = SearchIndex(
            name="hr-employees-fixed",
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search
        )
        
        return index
    
    async def create_or_update_index(self):
        """Create or update the search index"""
        try:
            index = self.create_hr_search_index()
            
            # Check if index exists
            try:
                existing_index = self.index_client.get_index("hr-employees-fixed")
                print("📝 Updating existing index...")
                result = self.index_client.create_or_update_index(index)
            except Exception:
                print("🆕 Creating new index...")
                result = self.index_client.create_index(index)
            
            print(f"✅ Index '{result.name}' created/updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create/update index: {e}")
            return False
    
    def prepare_document_for_indexing(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare employee document for search indexing with proper field mapping"""
        from datetime import datetime
        
        # Create combined text for better search
        combined_parts = []
        
        # Add basic info
        if employee_data.get('full_name'):
            combined_parts.append(f"Name: {employee_data['full_name']}")
        if employee_data.get('department'):
            combined_parts.append(f"Department: {employee_data['department']}")
        if employee_data.get('role'):
            combined_parts.append(f"Role: {employee_data['role']}")
        if employee_data.get('location'):
            combined_parts.append(f"Location: {employee_data['location']}")
        
        # Add skills and certifications
        if employee_data.get('certifications'):
            combined_parts.append(f"Certifications: {employee_data['certifications']}")
        if employee_data.get('current_project'):
            combined_parts.append(f"Current Project: {employee_data['current_project']}")
        if employee_data.get('improvement_areas'):
            combined_parts.append(f"Improvement Areas: {employee_data['improvement_areas']}")
        
        # Add experience info
        if employee_data.get('total_experience_years'):
            combined_parts.append(f"Experience: {employee_data['total_experience_years']} years")
        
        combined_text = " | ".join(combined_parts)
        
        # Handle datetime fields
        def format_datetime(dt_value):
            if dt_value is None:
                return None
            if isinstance(dt_value, str):
                try:
                    dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                    return dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    return None
            return None
        
        # Create search document with proper field mapping
        search_doc = {
            "id": f"emp_{employee_data.get('employee_id')}",
            "employee_id": str(employee_data.get('employee_id', '')),
            "full_name": employee_data.get('full_name', ''),
            "email": employee_data.get('email', ''),
            "department": employee_data.get('department', ''),
            "role": employee_data.get('role', ''),  # This is the position field
            "location": employee_data.get('location', ''),
            "certifications": str(employee_data.get('certifications', '')),  # This is skills
            "current_project": str(employee_data.get('current_project', '')),
            "improvement_areas": str(employee_data.get('improvement_areas', '')),
            "manager_feedback": str(employee_data.get('manager_feedback', '')),
            "total_experience_years": float(employee_data.get('total_experience_years', 0)) if employee_data.get('total_experience_years') else 0,
            "performance_rating": int(employee_data.get('performance_rating', 0)) if employee_data.get('performance_rating') else 0,
            "engagement_score": int(employee_data.get('engagement_score', 0)) if employee_data.get('engagement_score') else 0,
            "combined_text": combined_text,
            "created_at": format_datetime(datetime.utcnow().isoformat()),
            "updated_at": format_datetime(datetime.utcnow().isoformat())
        }
        
        return search_doc
    
    async def index_all_employees(self):
        """Index all employees by combining data from multiple collections"""
        if self.db is None:
            print("❌ MongoDB not connected")
            return False
        
        try:
            search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name="hr-employees-fixed",
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
            
            # Get all unique employee IDs
            employee_ids = set()
            collections = ['personal_info', 'employment', 'learning', 'experience', 'performance', 'engagement', 'compensation']
            
            for collection_name in collections:
                if collection_name in await self.db.list_collection_names():
                    collection = self.db[collection_name]
                    async for doc in collection.find({}, {"employee_id": 1}):
                        if doc.get("employee_id"):
                            employee_ids.add(doc["employee_id"])
            
            print(f"📊 Found {len(employee_ids)} unique employees to index")
            
            all_documents = []
            
            for employee_id in employee_ids:
                print(f"🔄 Processing employee: {employee_id}")
                employee_data = await self.get_employee_data(employee_id)
                search_doc = self.prepare_document_for_indexing(employee_data)
                all_documents.append(search_doc)
            
            # Upload documents to Azure Search in batches
            batch_size = 50
            total_uploaded = 0
            
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i + batch_size]
                try:
                    result = search_client.upload_documents(documents=batch)
                    total_uploaded += len(batch)
                    print(f"   📤 Uploaded batch {i//batch_size + 1}: {len(batch)} documents")
                except Exception as e:
                    print(f"   ❌ Failed to upload batch {i//batch_size + 1}: {e}")
            
            print(f"🎉 Successfully indexed {total_uploaded} employees")
            return True
            
        except Exception as e:
            print(f"❌ Failed to index employees: {e}")
            return False
    
    async def verify_index(self):
        """Verify the search index"""
        try:
            search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name="hr-employees-fixed",
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
            
            # Get index statistics
            result = search_client.search("*", include_total_count=True, top=1)
            total_count = result.get_count()
            
            print(f"📊 Index verification:")
            print(f"   Total documents: {total_count}")
            
            # Sample search with proper field names
            if total_count > 0:
                print(f"   Sample employees:")
                sample_results = search_client.search("*", top=3, select="full_name,department,role,certifications")
                for doc in sample_results:
                    print(f"     - {doc.get('full_name', 'N/A')} ({doc.get('department', 'N/A')}) - {doc.get('role', 'N/A')}")
                    print(f"       Skills: {doc.get('certifications', 'N/A')}")
                
                # Test specific searches
                print(f"   Test searches:")
                test_terms = ["developer", "sales", "python", "aws"]
                for term in test_terms:
                    results = search_client.search(term, top=1)
                    result_list = list(results)
                    print(f"     '{term}': {len(result_list)} results")
            
            return True
            
        except Exception as e:
            print(f"❌ Index verification failed: {e}")
            return False
    
    async def close_connections(self):
        """Close all connections"""
        if self.mongodb_client:
            self.mongodb_client.close()
            print("🔐 MongoDB connection closed")

async def main():
    """Main function to create and populate fixed search index"""
    print("🔧 Fixed Azure AI Search Index Creation Pipeline")
    print("=" * 60)
    
    indexer = FixedAzureSearchIndexer()
    
    try:
        # Connect to MongoDB
        connected = await indexer.connect_to_mongodb()
        if not connected:
            return
        
        # Create/update search index
        print("\n📝 Creating fixed search index...")
        index_created = await indexer.create_or_update_index()
        if not index_created:
            return
        
        # Index all employees with proper data mapping
        print("\n📊 Indexing employees with proper field mapping...")
        indexed = await indexer.index_all_employees()
        if not indexed:
            return
        
        # Verify index
        print("\n🔍 Verifying fixed index...")
        await indexer.verify_index()
        
        print("\n🎉 Fixed search index creation completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
    
    finally:
        await indexer.close_connections()

if __name__ == "__main__":
    asyncio.run(main())