# inspect_mongodb.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.core.config import settings

async def inspect_mongodb():
    """Inspect MongoDB collections and data structure"""
    try:
        client = AsyncIOMotorClient(settings.mongodb_connection_string)
        db = client[settings.mongodb_database]
        
        print("🔍 MongoDB Data Structure Analysis")
        print("=" * 50)
        
        # Get all collections
        collections = await db.list_collection_names()
        hr_collections = [col for col in collections if not col.startswith('system')]
        
        print(f"📊 Found {len(hr_collections)} collections:")
        for col in hr_collections:
            count = await db[col].count_documents({})
            print(f"   - {col}: {count} documents")
        
        # Inspect each collection structure
        for collection_name in hr_collections:
            print(f"\n📋 Collection: {collection_name}")
            print("-" * 30)
            
            collection = db[collection_name]
            
            # Get sample document
            sample = await collection.find_one()
            if sample:
                print("🔍 Sample document structure:")
                for key, value in sample.items():
                    if key == '_id':
                        continue
                    value_preview = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"   {key}: {value_preview}")
                
                print(f"\n📊 All fields in this collection:")
                # Get all unique field names
                pipeline = [
                    {"$project": {"fields": {"$objectToArray": "$$ROOT"}}},
                    {"$unwind": "$fields"},
                    {"$group": {"_id": "$fields.k"}},
                    {"$sort": {"_id": 1}}
                ]
                
                fields = []
                async for doc in collection.aggregate(pipeline):
                    if doc['_id'] not in ['_id', 'created_at', 'updated_at']:
                        fields.append(doc['_id'])
                
                print(f"   Fields: {', '.join(fields)}")
            else:
                print("   No documents found")
        
        client.close()
        
    except Exception as e:
        print(f"❌ MongoDB inspection failed: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_mongodb())