# check_all_indexes.py
import asyncio
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.core.config import settings

async def check_all_indexes():
    """Check all Azure Search indexes"""
    
    index_client = SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=AzureKeyCredential(settings.azure_search_api_key)
    )
    
    print("🔍 Checking all Azure Search indexes...")
    print("=" * 50)
    
    # List all indexes
    indexes = index_client.list_indexes()
    
    for index in indexes:
        print(f"\n📋 Index: {index.name}")
        
        # Check document count
        try:
            search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=index.name,
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
            
            results = search_client.search("*", include_total_count=True, top=1)
            count = results.get_count()
            print(f"   📊 Documents: {count}")
            
            # Sample document if any exist
            if count > 0:
                sample = next(iter(results), None)
                if sample:
                    print(f"   👤 Sample: {sample.get('full_name', 'N/A')} - {sample.get('department', 'N/A')}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_indexes())