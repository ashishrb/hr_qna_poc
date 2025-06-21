# simple_search_test.py
import asyncio
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.core.config import settings

async def test_simple_searches():
    """Test simple searches to understand the discrepancies"""
    try:
        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="hr-employees-fixed",
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        
        print("🔍 Simple Search Tests")
        print("=" * 40)
        
        # Test 1: Get all with role=Developer
        print("1. Filter by role='Developer':")
        dev_filter_results = search_client.search("*", filter="role eq 'Developer'", select="full_name,role", top=10)
        dev_filter_docs = list(dev_filter_results)
        print(f"   Found {len(dev_filter_docs)} developers:")
        for doc in dev_filter_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 2: Text search for "developer"
        print(f"\n2. Text search for 'developer':")
        dev_text_results = search_client.search("developer", select="full_name,role,combined_text", top=10)
        dev_text_docs = list(dev_text_results)
        print(f"   Found {len(dev_text_docs)} results:")
        for doc in dev_text_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 3: Text search for "developers" (plural)
        print(f"\n3. Text search for 'developers' (plural):")
        devs_text_results = search_client.search("developers", select="full_name,role", top=10)
        devs_text_docs = list(devs_text_results)
        print(f"   Found {len(devs_text_docs)} results:")
        for doc in devs_text_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 4: Get all with role=Director
        print(f"\n4. Filter by role='Director':")
        dir_filter_results = search_client.search("*", filter="role eq 'Director'", select="full_name,role", top=10)
        dir_filter_docs = list(dir_filter_results)
        print(f"   Found {len(dir_filter_docs)} directors:")
        for doc in dir_filter_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 5: Text search for "director"
        print(f"\n5. Text search for 'director':")
        dir_text_results = search_client.search("director", select="full_name,role", top=10)
        dir_text_docs = list(dir_text_results)
        print(f"   Found {len(dir_text_docs)} results:")
        for doc in dir_text_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 6: Text search for "directors" (plural)
        print(f"\n6. Text search for 'directors' (plural):")
        dirs_text_results = search_client.search("directors", select="full_name,role", top=10)
        dirs_text_docs = list(dirs_text_results)
        print(f"   Found {len(dirs_text_docs)} results:")
        for doc in dirs_text_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 7: Search in specific fields
        print(f"\n7. Search 'Director' in role field only:")
        role_search_results = search_client.search("Director", search_fields=["role"], select="full_name,role", top=10)
        role_search_docs = list(role_search_results)
        print(f"   Found {len(role_search_docs)} results:")
        for doc in role_search_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_searches())