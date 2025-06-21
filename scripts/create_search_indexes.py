# scripts/create_search_indexes.py
"""
Azure Search Index Creation and Management Script

Purpose:
- Create new Azure AI Search indexes for HR data
- Update existing indexes with new field mappings
- Delete and recreate indexes when needed
- Validate index configuration and test search functionality
- Manage multiple index versions and configurations

Usage:
    python scripts/create_search_indexes.py --action create --index hr-employees-v2
    python scripts/create_search_indexes.py --action update --index hr-employees-fixed
    python scripts/create_search_indexes.py --action delete --index old-index
    python scripts/create_search_indexes.py --action list
    python scripts/create_search_indexes.py --action validate --index hr-employees-fixed
"""

import asyncio
import argparse
import json
import yaml
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.core.config import settings

# Azure Search imports
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, 
    SearchableField, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, SemanticConfiguration, SemanticSearch,
    SemanticField, SemanticPrioritizedFields, SearchSuggester
)
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError

class SearchIndexManager:
    """Manages Azure Search indexes for HR data"""
    
    def __init__(self):
        self.index_client = SearchIndexClient(
            endpoint=settings.azure_search_endpoint,
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        self.config = self._load_configuration()
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from settings.yaml and employee_schema.json"""
        config = {}
        
        # Load settings.yaml
        try:
            with open('config/settings.yaml', 'r') as f:
                settings_config = yaml.safe_load(f)
                config['settings'] = settings_config
        except FileNotFoundError:
            print("⚠️ settings.yaml not found, using defaults")
            config['settings'] = {}
        
        # Load employee_schema.json
        try:
            with open('config/employee_schema.json', 'r') as f:
                schema_config = json.load(f)
                config['schema'] = schema_config
        except FileNotFoundError:
            print("⚠️ employee_schema.json not found, using defaults")
            config['schema'] = {}
        
        return config
    
    def create_hr_search_index(self, index_name: str = "hr-employees-v2") -> SearchIndex:
        """Create comprehensive HR search index based on schema configuration"""
        
        print(f"📝 Creating search index: {index_name}")
        
        # Define core search fields
        fields = [
            # Primary key and identifiers
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="employee_id", type=SearchFieldDataType.String, filterable=True, sortable=True),
            
            # Personal information
            SearchableField(name="full_name", type=SearchFieldDataType.String, 
                          analyzer_name="standard.lucene", suggester_names=["sg"]),
            SearchableField(name="email", type=SearchFieldDataType.String),
            
            # Employment information  
            SearchableField(name="department", type=SearchFieldDataType.String, 
                          filterable=True, facetable=True, sortable=True),
            SearchableField(name="role", type=SearchFieldDataType.String, 
                          filterable=True, facetable=True, sortable=True),
            SearchableField(name="location", type=SearchFieldDataType.String, 
                          filterable=True, facetable=True, sortable=True),
            SimpleField(name="grade_band", type=SearchFieldDataType.String, 
                       filterable=True, facetable=True),
            SimpleField(name="employment_type", type=SearchFieldDataType.String, 
                       filterable=True, facetable=True),
            SimpleField(name="work_mode", type=SearchFieldDataType.String, 
                       filterable=True, facetable=True),
            
            # Skills and learning
            SearchableField(name="certifications", type=SearchFieldDataType.String, 
                          analyzer_name="standard.lucene"),
            SearchableField(name="skills", type=SearchFieldDataType.String, 
                          analyzer_name="standard.lucene"),
            SimpleField(name="courses_completed", type=SearchFieldDataType.Int32, 
                       filterable=True, sortable=True),
            SimpleField(name="learning_hours_ytd", type=SearchFieldDataType.Int32, 
                       filterable=True, sortable=True),
            
            # Experience and performance
            SimpleField(name="total_experience_years", type=SearchFieldDataType.Double, 
                       filterable=True, sortable=True),
            SimpleField(name="years_in_current_company", type=SearchFieldDataType.Double, 
                       filterable=True, sortable=True),
            SimpleField(name="performance_rating", type=SearchFieldDataType.Int32, 
                       filterable=True, sortable=True, facetable=True),
            SearchableField(name="awards", type=SearchFieldDataType.String),
            SearchableField(name="improvement_areas", type=SearchFieldDataType.String),
            
            # Current engagement
            SearchableField(name="current_project", type=SearchFieldDataType.String, 
                          analyzer_name="standard.lucene"),
            SimpleField(name="engagement_score", type=SearchFieldDataType.Int32, 
                       filterable=True, sortable=True, facetable=True),
            SearchableField(name="manager_feedback", type=SearchFieldDataType.String),
            
            # Attrition and retention
            SimpleField(name="attrition_risk_score", type=SearchFieldDataType.String, 
                       filterable=True, facetable=True),
            SimpleField(name="exit_intent_flag", type=SearchFieldDataType.String, 
                       filterable=True, facetable=True),
            
            # Computed fields
            SearchableField(name="combined_text", type=SearchFieldDataType.String, 
                          analyzer_name="standard.lucene"),
            SearchableField(name="searchable_text", type=SearchFieldDataType.String, 
                          analyzer_name="keyword"),
            
            # Vector field for semantic search
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="hr-vector-profile"
            ),
            
            # Metadata fields
            SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, 
                       filterable=True, sortable=True),
            SimpleField(name="updated_at", type=SearchFieldDataType.DateTimeOffset, 
                       filterable=True, sortable=True),
            SimpleField(name="data_version", type=SearchFieldDataType.String, 
                       filterable=True)
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
                    SemanticField(field_name="current_project"),
                    SemanticField(field_name="skills")
                ],
                keywords_fields=[
                    SemanticField(field_name="department"),
                    SemanticField(field_name="role"),
                    SemanticField(field_name="location")
                ]
            )
        )
        
        semantic_search = SemanticSearch(configurations=[semantic_config])
        
        # Configure suggester for autocomplete
        suggester = SearchSuggester(
            name="sg",
            source_fields=["full_name", "department", "role", "location", "certifications"]
        )
        
        # Create the index
        index = SearchIndex(
            name=index_name,
            fields=fields,
            vector_search=vector_search,
            semantic_search=semantic_search,
            suggesters=[suggester]
        )
        
        return index
    
    def create_index(self, index_name: str, force_recreate: bool = False) -> bool:
        """Create a new search index"""
        try:
            # Check if index exists
            try:
                existing_index = self.index_client.get_index(index_name)
                if existing_index and not force_recreate:
                    print(f"⚠️ Index '{index_name}' already exists. Use --force to recreate.")
                    return False
                elif existing_index and force_recreate:
                    print(f"🗑️ Deleting existing index '{index_name}'...")
                    self.index_client.delete_index(index_name)
            except ResourceNotFoundError:
                pass  # Index doesn't exist, which is fine
            
            # Create new index
            index = self.create_hr_search_index(index_name)
            result = self.index_client.create_index(index)
            
            print(f"✅ Successfully created index '{result.name}'")
            print(f"   📊 Fields: {len(result.fields)}")
            print(f"   🔍 Vector search: {'✅' if result.vector_search else '❌'}")
            print(f"   🧠 Semantic search: {'✅' if result.semantic_search else '❌'}")
            print(f"   📝 Suggesters: {len(result.suggesters) if result.suggesters else 0}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create index '{index_name}': {e}")
            return False
    
    def update_index(self, index_name: str) -> bool:
        """Update an existing search index"""
        try:
            # Get current index
            try:
                existing_index = self.index_client.get_index(index_name)
                print(f"📝 Updating existing index '{index_name}'...")
            except ResourceNotFoundError:
                print(f"❌ Index '{index_name}' not found. Cannot update non-existent index.")
                return False
            
            # Create updated index configuration
            updated_index = self.create_hr_search_index(index_name)
            
            # Update the index
            result = self.index_client.create_or_update_index(updated_index)
            
            print(f"✅ Successfully updated index '{result.name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update index '{index_name}': {e}")
            return False
    
    def delete_index(self, index_name: str, confirm: bool = False) -> bool:
        """Delete a search index"""
        try:
            if not confirm:
                response = input(f"⚠️ Are you sure you want to delete index '{index_name}'? (yes/no): ")
                if response.lower() != 'yes':
                    print("❌ Index deletion cancelled.")
                    return False
            
            self.index_client.delete_index(index_name)
            print(f"✅ Successfully deleted index '{index_name}'")
            return True
            
        except ResourceNotFoundError:
            print(f"❌ Index '{index_name}' not found.")
            return False
        except Exception as e:
            print(f"❌ Failed to delete index '{index_name}': {e}")
            return False
    
    def list_indexes(self) -> List[str]:
        """List all search indexes"""
        try:
            indexes = self.index_client.list_indexes()
            index_names = []
            
            print("📋 Available Search Indexes:")
            print("=" * 40)
            
            for index in indexes:
                index_names.append(index.name)
                
                # Get index stats
                try:
                    search_client = SearchClient(
                        endpoint=settings.azure_search_endpoint,
                        index_name=index.name,
                        credential=AzureKeyCredential(settings.azure_search_api_key)
                    )
                    results = search_client.search("*", include_total_count=True, top=0)
                    doc_count = results.get_count()
                except:
                    doc_count = "Unknown"
                
                print(f"📊 {index.name}")
                print(f"   Fields: {len(index.fields)}")
                print(f"   Documents: {doc_count}")
                print(f"   Vector Search: {'✅' if index.vector_search else '❌'}")
                print(f"   Semantic Search: {'✅' if index.semantic_search else '❌'}")
                print()
            
            if not index_names:
                print("No indexes found.")
            
            return index_names
            
        except Exception as e:
            print(f"❌ Failed to list indexes: {e}")
            return []
    
    def validate_index(self, index_name: str) -> bool:
        """Validate index configuration and test basic functionality"""
        try:
            print(f"🔍 Validating index '{index_name}'...")
            
            # Get index details
            index = self.index_client.get_index(index_name)
            
            # Validate index structure
            required_fields = ["id", "employee_id", "full_name", "department", "role"]
            missing_fields = []
            
            existing_fields = [field.name for field in index.fields]
            for field in required_fields:
                if field not in existing_fields:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Test search client connection
            search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=index_name,
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
            
            # Get document count
            results = search_client.search("*", include_total_count=True, top=0)
            doc_count = results.get_count()
            
            # Test basic search
            test_results = search_client.search("*", top=1)
            test_doc = next(iter(test_results), None)
            
            # Test facets
            facet_results = search_client.search("*", facets=["department"], top=0)
            facets = facet_results.get_facets()
            
            print("✅ Index validation results:")
            print(f"   📊 Total documents: {doc_count}")
            print(f"   📋 Total fields: {len(index.fields)}")
            print(f"   🔍 Vector search: {'✅' if index.vector_search else '❌'}")
            print(f"   🧠 Semantic search: {'✅' if index.semantic_search else '❌'}")
            print(f"   📝 Suggesters: {len(index.suggesters) if index.suggesters else 0}")
            print(f"   📊 Facets available: {'✅' if facets else '❌'}")
            print(f"   🔬 Test query: {'✅' if test_doc else '❌'}")
            
            if test_doc:
                print(f"   📄 Sample document: {test_doc.get('full_name', 'N/A')} - {test_doc.get('department', 'N/A')}")
            
            return True
            
        except ResourceNotFoundError:
            print(f"❌ Index '{index_name}' not found.")
            return False
        except Exception as e:
            print(f"❌ Index validation failed: {e}")
            return False
    
    def get_index_statistics(self, index_name: str) -> Dict[str, Any]:
        """Get detailed statistics for an index"""
        try:
            search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=index_name,
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
            
            # Get total count
            results = search_client.search("*", include_total_count=True, top=0)
            total_count = results.get_count()
            
            # Get facet statistics
            facet_fields = ["department", "role", "location", "performance_rating"]
            facet_results = search_client.search("*", facets=facet_fields, top=0)
            facets = facet_results.get_facets()
            
            stats = {
                "total_documents": total_count,
                "facets": facets,
                "last_checked": datetime.utcnow().isoformat()
            }
            
            print(f"📈 Index Statistics for '{index_name}':")
            print(f"   Total Documents: {total_count}")
            
            if facets:
                for facet_field, facet_values in facets.items():
                    print(f"   {facet_field.title()}: {len(facet_values)} unique values")
                    for facet in facet_values[:5]:  # Show top 5
                        print(f"     - {facet['value']}: {facet['count']}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
            return {}

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Azure Search Index Management Tool")
    parser.add_argument("--action", required=True, 
                       choices=["create", "update", "delete", "list", "validate", "stats"],
                       help="Action to perform")
    parser.add_argument("--index", help="Index name")
    parser.add_argument("--force", action="store_true", help="Force recreate existing index")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    print("🔧 Azure Search Index Manager")
    print("=" * 40)
    
    manager = SearchIndexManager()
    
    if args.action == "create":
        if not args.index:
            print("❌ Index name required for create action")
            return
        success = manager.create_index(args.index, args.force)
        
    elif args.action == "update":
        if not args.index:
            print("❌ Index name required for update action")
            return
        success = manager.update_index(args.index)
        
    elif args.action == "delete":
        if not args.index:
            print("❌ Index name required for delete action")
            return
        success = manager.delete_index(args.index, args.confirm)
        
    elif args.action == "list":
        manager.list_indexes()
        success = True
        
    elif args.action == "validate":
        if not args.index:
            print("❌ Index name required for validate action")
            return
        success = manager.validate_index(args.index)
        
    elif args.action == "stats":
        if not args.index:
            print("❌ Index name required for stats action")
            return
        manager.get_index_statistics(args.index)
        success = True
    
    print("=" * 40)
    if success:
        print("🎉 Operation completed successfully!")
    else:
        print("❌ Operation failed!")

if __name__ == "__main__":
    main()