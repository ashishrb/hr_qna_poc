# quick_data_check.py
import asyncio
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.core.config import settings

async def explore_data():
    """Quick exploration of indexed data"""
    try:
        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="hr-employees-index",
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        
        print("🔍 Exploring Indexed Data")
        print("=" * 40)
        
        # Get total count
        results = search_client.search("*", include_total_count=True, top=0)
        total_count = results.get_count()
        print(f"📊 Total employees indexed: {total_count}")
        
        # Sample employees
        print("\n👥 Sample employees:")
        sample_results = search_client.search("*", top=5, select="full_name,department,position,skills")
        for i, result in enumerate(sample_results, 1):
            print(f"{i}. {result.get('full_name', 'N/A')} - {result.get('department', 'N/A')} - {result.get('position', 'N/A')}")
            print(f"   Skills: {result.get('skills', 'N/A')}")
        
        # Department distribution
        print("\n🏢 Departments:")
        dept_results = search_client.search("*", facets=["department"], top=0)
        if dept_results.get_facets():
            for facet in dept_results.get_facets()["department"][:10]:
                print(f"   {facet['value']}: {facet['count']} employees")
        
        # Position distribution
        print("\n💼 Positions:")
        pos_results = search_client.search("*", facets=["position"], top=0)
        if pos_results.get_facets():
            for facet in pos_results.get_facets()["position"][:10]:
                print(f"   {facet['value']}: {facet['count']} employees")
        
        # Test searches
        print("\n🔍 Test searches:")
        test_terms = ["developer", "manager", "engineer", "analyst"]
        for term in test_terms:
            results = search_client.search(term, top=3)
            count = len(list(results))
            print(f"   '{term}': {count} results")
        
    except Exception as e:
        print(f"❌ Data exploration failed: {e}")

if __name__ == "__main__":
    asyncio.run(explore_data())