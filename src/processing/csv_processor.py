# src/processing/csv_processor.py
import pandas as pd
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import sys

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings

class HRDataProcessor:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect_to_mongodb(self):
        """Connect to MongoDB Atlas"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_connection_string)
            self.db = self.client[settings.mongodb_database]
            
            # Test connection
            await self.client.admin.command('ping')
            print("✅ Connected to MongoDB Atlas")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    async def process_excel_to_collections(self, excel_file_path):
        """Process Excel file and create MongoDB collections"""
        print("📊 Starting Excel to MongoDB processing...")
        
        try:
            # Read Excel file
            excel_data = pd.read_excel(excel_file_path, sheet_name=None)
            print(f"📋 Found {len(excel_data)} sheets to process")
            
            # Process each sheet
            for sheet_name, df in excel_data.items():
                await self.process_sheet(sheet_name, df)
            
            print("🎉 All sheets processed successfully!")
            
        except Exception as e:
            print(f"❌ Error processing Excel file: {e}")
    
    async def process_sheet(self, sheet_name, df):
        """Process individual sheet and insert into MongoDB"""
        try:
            # Clean sheet name for collection name
            collection_name = sheet_name.lower().replace(' ', '_')
            collection = self.db[collection_name]
            
            print(f"\n🔄 Processing sheet: {sheet_name}")
            print(f"   📊 Rows: {len(df)}, Columns: {len(df.columns)}")
            
            # Convert DataFrame to list of dictionaries
            records = []
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    value = row[col]
                    
                    # Handle NaN values
                    if pd.isna(value):
                        record[col] = None
                    # Handle datetime
                    elif isinstance(value, pd.Timestamp):
                        record[col] = value.isoformat()
                    else:
                        record[col] = value
                
                # Add metadata
                record['created_at'] = datetime.utcnow().isoformat()
                record['updated_at'] = datetime.utcnow().isoformat()
                
                records.append(record)
            
            # Insert into MongoDB
            if records:
                # Clear existing data
                await collection.delete_many({})
                
                # Insert new data
                result = await collection.insert_many(records)
                print(f"   ✅ Inserted {len(result.inserted_ids)} records into '{collection_name}' collection")
                
                # Create index on employee_id if present
                if 'employee_id' in df.columns:
                    await collection.create_index("employee_id")
                    print(f"   📇 Created index on employee_id")
            
        except Exception as e:
            print(f"   ❌ Error processing sheet {sheet_name}: {e}")
    
    async def verify_data(self):
        """Verify data was inserted correctly"""
        print("\n🔍 Verifying data insertion...")
        
        collections = await self.db.list_collection_names()
        
        for collection_name in collections:
            if not collection_name.startswith('system'):
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                print(f"   📊 {collection_name}: {count} documents")
        
        # Sample data from personal_info collection
        if 'personal_info' in collections:
            personal_info = self.db['personal_info']
            sample = await personal_info.find_one()
            if sample:
                print(f"\n👀 Sample record from personal_info:")
                print(f"   Employee ID: {sample.get('employee_id', 'N/A')}")
                print(f"   Name: {sample.get('full_name', 'N/A')}")
                print(f"   Location: {sample.get('location', 'N/A')}")
    
    async def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("🔐 MongoDB connection closed")

async def main():
    """Main function to run the ETL process"""
    print("🚀 HR Data ETL Pipeline Starting...")
    print("=" * 50)
    
    processor = HRDataProcessor()
    
    try:
        # Connect to MongoDB
        connected = await processor.connect_to_mongodb()
        if not connected:
            return
        
        # Process Excel file
        excel_file_path = "data/input/hr_employee_360_full_data.xlsx"
        await processor.process_excel_to_collections(excel_file_path)
        
        # Verify data
        await processor.verify_data()
        
    except Exception as e:
        print(f"❌ ETL Pipeline failed: {e}")
    
    finally:
        await processor.close_connection()
    
    print("\n🎉 ETL Pipeline completed!")

if __name__ == "__main__":
    asyncio.run(main())