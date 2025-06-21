# test_connections.py
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI

# Set environment variables
os.environ["MONGODB_CONNECTION_STRING"] = "mongodb+srv://Ashish:test1234@cluster0.ydw4hcc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
os.environ["AZURE_SEARCH_ENDPOINT"] = "https://azure-ai-search-1c-assistant.search.windows.net"
os.environ["AZURE_SEARCH_API_KEY"] = "ERuLnusdQHL7t0KGdVI2fhWheZ8zZsXMAClIEdu2dfAzSeCMDuXS"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://1c-assistant-openai-np02.openai.azure.com/"
os.environ["AZURE_OPENAI_API_KEY"] = "89bf3e8884ea44d69f64075562507b32"

async def test_all_connections():
    print("🧪 Testing All Service Connections...")
    print("=" * 50)
    
    # Test 1: MongoDB Atlas
    try:
        client = AsyncIOMotorClient(os.environ["MONGODB_CONNECTION_STRING"])
        await client.admin.command('ping')
        print("✅ MongoDB Atlas: Connected")
        client.close()
    except Exception as e:
        print(f"❌ MongoDB Atlas: Failed - {e}")
    
    # Test 2: Azure AI Search
    try:
        search_client = SearchClient(
            endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
            index_name="test",
            credential=AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"])
        )
        print("✅ Azure AI Search: Connected")
    except Exception as e:
        print(f"❌ Azure AI Search: Failed - {e}")
    
    # Test 3: Azure OpenAI
    try:
        openai_client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2023-05-15",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )
        response = openai_client.chat.completions.create(
            model="gpt-4o-llm",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("✅ Azure OpenAI: Connected")
    except Exception as e:
        print(f"❌ Azure OpenAI: Failed - {e}")
    
    print("=" * 50)
    print("🎉 Connection testing complete!")

if __name__ == "__main__":
    asyncio.run(test_all_connections())