# delete_and_recreate_index.py
import asyncio
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.core.config import settings

async def delete_and_recreate_index():
    """Delete existing index and recreate with enhanced fields"""
    
    index_client = SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=AzureKeyCredential(settings.azure_search_api_key)
    )
    
    index_name = "hr-employees-fixed"
    
    print(f"🗑️  Deleting existing index '{index_name}'...")
    
    try:
        # Delete the existing index
        index_client.delete_index(index_name)
        print(f"✅ Successfully deleted index '{index_name}'")
    except ResourceNotFoundError:
        print(f"⚠️  Index '{index_name}' not found, skipping deletion")
    except Exception as e:
        print(f"❌ Failed to delete index: {e}")
        return False
    
    print(f"🔄 Now run your indexer to create the enhanced index...")
    print(f"   python src/search/indexer.py")
    
    return True

if __name__ == "__main__":
    asyncio.run(delete_and_recreate_index())