# debug_search.py
import asyncio
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.core.config import settings

async def debug_search():
    """Debug search functionality"""
    try:
        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="hr-employees-fixed",
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        
        print("🔍 Search Debug Analysis")
        print("=" * 40)
        
        # Test 1: Get all documents
        print("1. Getting all documents...")
        all_results = search_client.search("*", top=10, select="full_name,department,role,certifications")
        all_docs = list(all_results)
        print(f"   Total results: {len(all_docs)}")
        
        for i, doc in enumerate(all_docs, 1):
            print(f"   {i}. {doc.get('full_name', 'N/A')} - {doc.get('department', 'N/A')} - {doc.get('role', 'N/A')}")
            print(f"      Certifications: {doc.get('certifications', 'N/A')}")
        
        # Test 2: Search for "developer" exact
        print(f"\n2. Searching for 'developer'...")
        dev_results = search_client.search("developer", top=5, select="full_name,department,role")
        dev_docs = list(dev_results)
        print(f"   Results: {len(dev_docs)}")
        for doc in dev_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 3: Search for "Developer" with capital
        print(f"\n3. Searching for 'Developer' (capital)...")
        dev_cap_results = search_client.search("Developer", top=5, select="full_name,department,role")
        dev_cap_docs = list(dev_cap_results)
        print(f"   Results: {len(dev_cap_docs)}")
        for doc in dev_cap_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 4: Filter by role field
        print(f"\n4. Filtering by role = 'Developer'...")
        filter_results = search_client.search("*", filter="role eq 'Developer'", top=5, select="full_name,department,role")
        filter_docs = list(filter_results)
        print(f"   Results: {len(filter_docs)}")
        for doc in filter_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
        # Test 5: Check all unique roles
        print(f"\n5. Getting all unique roles...")
        role_results = search_client.search("*", facets=["role"], top=0)
        if role_results.get_facets():
            print("   Available roles:")
            for facet in role_results.get_facets()["role"]:
                print(f"     - '{facet['value']}': {facet['count']} employees")
        
        # Test 6: Search in combined_text
        print(f"\n6. Searching in combined_text for 'developer'...")
        combined_results = search_client.search("developer", search_fields=["combined_text"], top=5, select="full_name,combined_text")
        combined_docs = list(combined_results)
        print(f"   Results: {len(combined_docs)}")
        for doc in combined_docs:
            print(f"   - {doc.get('full_name', 'N/A')}")
            print(f"     Combined: {doc.get('combined_text', 'N/A')[:100]}...")
        
        # Test 7: Try wildcard search
        print(f"\n7. Wildcard search for 'dev*'...")
        wildcard_results = search_client.search("dev*", top=5, select="full_name,role")
        wildcard_docs = list(wildcard_results)
        print(f"   Results: {len(wildcard_docs)}")
        for doc in wildcard_docs:
            print(f"   - {doc.get('full_name', 'N/A')} ({doc.get('role', 'N/A')})")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_search())