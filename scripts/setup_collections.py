# scripts/setup_collections.py
"""
MongoDB Collections Setup Script

Purpose:
- Create MongoDB collections with proper schemas and validation
- Set up database indexes for optimal query performance
- Initialize collection constraints and relationships
- Create sample data and validation rules
- Manage collection migrations and updates

Usage:
    python scripts/setup_collections.py --action create_all
    python scripts/setup_collections.py --action create --collection personal_info
    python scripts/setup_collections.py --action drop --collection old_collection --confirm
    python scripts/setup_collections.py --action create_indexes
    python scripts/setup_collections.py --action validate_schema
    python scripts/setup_collections.py --action migrate --from v1 --to v2
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
from src.database.mongodb_client import mongodb_client
from src.core.config import settings

# MongoDB imports
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import CollectionInvalid, DuplicateKeyError
import pymongo

class MongoDBCollectionManager:
    """Manages MongoDB collections setup and maintenance"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.schema_config = self._load_schema_config()
        
    def _load_schema_config(self) -> Dict[str, Any]:
        """Load schema configuration from employee_schema.json"""
        try:
            with open('config/employee_schema.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ employee_schema.json not found, using minimal configuration")
            return {"employee_schema": {"collections": {}}}
    
    async def connect(self):
        """Connect to MongoDB"""
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
    
    async def create_collection_with_schema(self, collection_name: str, schema_config: Dict[str, Any]) -> bool:
        """Create collection with JSON schema validation"""
        try:
            # Build JSON schema from configuration
            json_schema = self._build_json_schema(schema_config)
            
            # Create collection with validation
            await self.db.create_collection(
                collection_name,
                validator={
                    "$jsonSchema": json_schema
                },
                validationLevel="moderate",  # Can be "strict", "moderate", or "off"
                validationAction="warn"       # Can be "error" or "warn"
            )
            
            print(f"✅ Created collection '{collection_name}' with schema validation")
            return True
            
        except CollectionInvalid as e:
            if "already exists" in str(e):
                print(f"⚠️ Collection '{collection_name}' already exists")
                return True
            else:
                print(f"❌ Failed to create collection '{collection_name}': {e}")
                return False
        except Exception as e:
            print(f"❌ Failed to create collection '{collection_name}': {e}")
            return False
    
    def _build_json_schema(self, schema_config: Dict[str, Any]) -> Dict[str, Any]:
        """Build MongoDB JSON schema from configuration"""
        fields = schema_config.get("fields", {})
        
        properties = {}
        required_fields = []
        
        for field_name, field_config in fields.items():
            field_type = field_config.get("type", "string")
            
            # Map configuration types to JSON schema types
            json_type = self._map_type_to_json_schema(field_type)
            field_schema = {"bsonType": json_type}
            
            # Add validation rules
            if field_config.get("required", False):
                required_fields.append(field_name)
            
            if "min" in field_config:
                field_schema["minimum"] = field_config["min"]
            
            if "max" in field_config:
                field_schema["maximum"] = field_config["max"]
            
            if "enum" in field_config:
                field_schema["enum"] = field_config["enum"]
            
            if "format" in field_config:
                if field_config["format"] == "email":
                    field_schema["pattern"] = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            
            if field_config.get("min_length"):
                field_schema["minLength"] = field_config["min_length"]
            
            if field_config.get("max_length"):
                field_schema["maxLength"] = field_config["max_length"]
            
            properties[field_name] = field_schema
        
        schema = {
            "bsonType": "object",
            "properties": properties
        }
        
        if required_fields:
            schema["required"] = required_fields
        
        return schema
    
    def _map_type_to_json_schema(self, config_type: str) -> str:
        """Map configuration types to JSON schema BSON types"""
        type_mapping = {
            "string": "string",
            "integer": "int",
            "int": "int",
            "float": "double",
            "double": "double",
            "boolean": "bool",
            "date": "date",
            "datetime": "date",
            "object": "object",
            "array": "array"
        }
        return type_mapping.get(config_type, "string")
    
    async def create_indexes(self, collection_name: str, schema_config: Dict[str, Any]) -> bool:
        """Create indexes for a collection based on schema configuration"""
        try:
            collection = self.db[collection_name]
            fields = schema_config.get("fields", {})
            
            indexes_created = 0
            
            for field_name, field_config in fields.items():
                # Create single field indexes
                if field_config.get("indexed", False):
                    await collection.create_index(field_name)
                    indexes_created += 1
                    print(f"   📇 Created index on '{field_name}'")
                
                # Create unique indexes
                if field_config.get("unique", False):
                    await collection.create_index(field_name, unique=True)
                    indexes_created += 1
                    print(f"   🔑 Created unique index on '{field_name}'")
                
                # Create text indexes for searchable fields
                if field_config.get("searchable", False):
                    try:
                        await collection.create_index([(field_name, "text")])
                        indexes_created += 1
                        print(f"   🔍 Created text index on '{field_name}'")
                    except DuplicateKeyError:
                        pass  # Text index might already exist
            
            # Create compound indexes for common query patterns
            if collection_name == "personal_info":
                await collection.create_index([("full_name", 1), ("email", 1)])
                indexes_created += 1
                print(f"   🔗 Created compound index on 'full_name' + 'email'")
            
            elif collection_name == "employment":
                await collection.create_index([("department", 1), ("role", 1)])
                await collection.create_index([("employee_id", 1), ("department", 1)])
                indexes_created += 2
                print(f"   🔗 Created compound indexes for employment queries")
            
            elif collection_name == "learning":
                await collection.create_index([("employee_id", 1), ("certifications", "text")])
                indexes_created += 1
                print(f"   🔗 Created compound index for certifications search")
            
            print(f"✅ Created {indexes_created} indexes for '{collection_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create indexes for '{collection_name}': {e}")
            return False
    
    async def create_all_collections(self) -> bool:
        """Create all HR collections with schemas and indexes"""
        print("🏗️ Creating all HR collections...")
        
        collections_config = self.schema_config.get("employee_schema", {}).get("collections", {})
        
        if not collections_config:
            print("❌ No collections configuration found")
            return False
        
        success_count = 0
        total_collections = len(collections_config)
        
        for collection_name, schema_config in collections_config.items():
            print(f"\n📋 Creating collection: {collection_name}")
            
            # Create collection with schema
            if await self.create_collection_with_schema(collection_name, schema_config):
                # Create indexes
                if await self.create_indexes(collection_name, schema_config):
                    success_count += 1
        
        print(f"\n🎉 Successfully created {success_count}/{total_collections} collections")
        return success_count == total_collections
    
    async def drop_collection(self, collection_name: str, confirm: bool = False) -> bool:
        """Drop a collection"""
        try:
            if not confirm:
                response = input(f"⚠️ Are you sure you want to drop collection '{collection_name}'? (yes/no): ")
                if response.lower() != 'yes':
                    print("❌ Collection drop cancelled.")
                    return False
            
            await self.db.drop_collection(collection_name)
            print(f"✅ Successfully dropped collection '{collection_name}'")
            return True
            
        except Exception as e:
            print(f"❌ Failed to drop collection '{collection_name}': {e}")
            return False
    
    async def validate_collection_schema(self, collection_name: str) -> Dict[str, Any]:
        """Validate existing collection against schema"""
        try:
            print(f"🔍 Validating schema for collection '{collection_name}'...")
            
            collection = self.db[collection_name]
            
            # Get collection info
            collections_info = await self.db.list_collections(filter={"name": collection_name})
            collection_info = await collections_info.to_list(length=1)
            
            if not collection_info:
                return {"error": f"Collection '{collection_name}' not found"}
            
            # Get sample documents
            sample_docs = await collection.find().limit(10).to_list(length=10)
            
            # Get collection statistics
            stats = await self.db.command("collStats", collection_name)
            
            # Analyze schema compliance
            schema_config = self.schema_config.get("employee_schema", {}).get("collections", {}).get(collection_name, {})
            fields_config = schema_config.get("fields", {})
            
            validation_results = {
                "collection_name": collection_name,
                "document_count": stats.get("count", 0),
                "avg_document_size": stats.get("avgObjSize", 0),
                "total_size_mb": stats.get("size", 0) / (1024 * 1024),
                "indexes": [],
                "schema_compliance": {},
                "field_analysis": {},
                "recommendations": []
            }
            
            # Analyze indexes
            indexes = await collection.list_indexes().to_list(length=None)
            validation_results["indexes"] = [
                {
                    "name": idx.get("name"),
                    "keys": idx.get("key"),
                    "unique": idx.get("unique", False)
                }
                for idx in indexes
            ]
            
            # Analyze field compliance
            if sample_docs and fields_config:
                all_fields = set()
                field_types = {}
                field_coverage = {}
                
                for doc in sample_docs:
                    for field, value in doc.items():
                        if field != "_id":
                            all_fields.add(field)
                            field_type = type(value).__name__
                            if field not in field_types:
                                field_types[field] = {}
                            field_types[field][field_type] = field_types[field].get(field_type, 0) + 1
                
                # Check field coverage
                for field_name, field_config in fields_config.items():
                    present_count = 0
                    for doc in sample_docs:
                        if field_name in doc and doc[field_name] is not None:
                            present_count += 1
                    
                    coverage = present_count / len(sample_docs) if sample_docs else 0
                    field_coverage[field_name] = {
                        "coverage_percent": coverage * 100,
                        "is_required": field_config.get("required", False),
                        "expected_type": field_config.get("type", "string")
                    }
                    
                    # Check for compliance issues
                    if field_config.get("required", False) and coverage < 1.0:
                        validation_results["recommendations"].append(
                            f"Required field '{field_name}' missing in {(1-coverage)*100:.1f}% of documents"
                        )
                
                validation_results["field_analysis"] = {
                    "total_fields_found": len(all_fields),
                    "expected_fields": len(fields_config),
                    "field_types": field_types,
                    "field_coverage": field_coverage
                }
                
                # Check for unexpected fields
                expected_fields = set(fields_config.keys())
                expected_fields.add("_id")  # MongoDB default
                expected_fields.update(["created_at", "updated_at"])  # Common metadata
                
                unexpected_fields = all_fields - expected_fields
                if unexpected_fields:
                    validation_results["recommendations"].append(
                        f"Unexpected fields found: {', '.join(unexpected_fields)}"
                    )
            
            # Check required indexes
            required_indexes = ["employee_id"] if collection_name != "personal_info" else ["employee_id", "email"]
            existing_index_fields = [list(idx["keys"].keys())[0] for idx in validation_results["indexes"] 
                                   if idx["keys"] and len(idx["keys"]) == 1]
            
            missing_indexes = set(required_indexes) - set(existing_index_fields)
            if missing_indexes:
                validation_results["recommendations"].append(
                    f"Missing recommended indexes: {', '.join(missing_indexes)}"
                )
            
            print(f"   📊 Documents: {validation_results['document_count']}")
            print(f"   📇 Indexes: {len(validation_results['indexes'])}")
            print(f"   📋 Fields: {validation_results['field_analysis'].get('total_fields_found', 0)}")
            
            if validation_results["recommendations"]:
                print(f"   ⚠️ Issues: {len(validation_results['recommendations'])}")
                for rec in validation_results["recommendations"][:3]:
                    print(f"      - {rec}")
            else:
                print(f"   ✅ Schema validation passed")
            
            return validation_results
            
        except Exception as e:
            print(f"❌ Schema validation failed for '{collection_name}': {e}")
            return {"error": str(e)}
    
    async def create_sample_data(self, collection_name: str, count: int = 10) -> bool:
        """Create sample data for testing"""
        try:
            print(f"📝 Creating {count} sample documents for '{collection_name}'...")
            
            collection = self.db[collection_name]
            
            # Generate sample data based on collection type
            sample_docs = []
            
            if collection_name == "personal_info":
                for i in range(count):
                    doc = {
                        "employee_id": f"EMP{1000 + i:04d}",
                        "full_name": f"Test Employee {i+1}",
                        "email": f"test.employee{i+1}@company.com",
                        "age": 25 + (i % 15),
                        "gender": ["Male", "Female", "Other"][i % 3],
                        "location": ["New York", "San Francisco", "Chicago", "Austin"][i % 4],
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    sample_docs.append(doc)
            
            elif collection_name == "employment":
                departments = ["IT", "Sales", "Operations", "HR", "Finance"]
                roles = ["Developer", "Manager", "Analyst", "Director", "Lead"]
                
                for i in range(count):
                    doc = {
                        "employee_id": f"EMP{1000 + i:04d}",
                        "department": departments[i % len(departments)],
                        "role": roles[i % len(roles)],
                        "employment_type": ["Full-time", "Part-time", "Contract"][i % 3],
                        "work_mode": ["Remote", "Onsite", "Hybrid"][i % 3],
                        "joining_date": "2023-01-01",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    sample_docs.append(doc)
            
            elif collection_name == "learning":
                certifications = ["AWS", "PMP", "GCP", "Azure", "Python", "Java"]
                
                for i in range(count):
                    doc = {
                        "employee_id": f"EMP{1000 + i:04d}",
                        "certifications": ", ".join(certifications[i:i+2] if i < len(certifications)-1 else certifications[-2:]),
                        "courses_completed": 5 + (i % 10),
                        "learning_hours_ytd": 20 + (i % 30),
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    sample_docs.append(doc)
            
            else:
                # Generic sample data for other collections
                for i in range(count):
                    doc = {
                        "employee_id": f"EMP{1000 + i:04d}",
                        "sample_field": f"Sample value {i+1}",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    sample_docs.append(doc)
            
            # Insert sample documents
            if sample_docs:
                result = await collection.insert_many(sample_docs)
                print(f"✅ Created {len(result.inserted_ids)} sample documents")
                return True
            
        except Exception as e:
            print(f"❌ Failed to create sample data for '{collection_name}': {e}")
            return False
    
    async def migrate_collection(self, collection_name: str, from_version: str, to_version: str) -> bool:
        """Migrate collection from one version to another"""
        try:
            print(f"🔄 Migrating '{collection_name}' from {from_version} to {to_version}...")
            
            collection = self.db[collection_name]
            
            # Example migration: add version field to all documents
            if from_version == "v1" and to_version == "v2":
                result = await collection.update_many(
                    {"data_version": {"$exists": False}},
                    {"$set": {
                        "data_version": to_version,
                        "migrated_at": datetime.utcnow().isoformat()
                    }}
                )
                
                print(f"✅ Migrated {result.modified_count} documents to {to_version}")
                return True
            
            # Add more migration logic as needed
            print(f"⚠️ No migration path defined for {from_version} -> {to_version}")
            return False
            
        except Exception as e:
            print(f"❌ Migration failed for '{collection_name}': {e}")
            return False
    
    async def get_collection_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all collections"""
        try:
            print("📊 Gathering collection statistics...")
            
            collections = await self.db.list_collection_names()
            hr_collections = [col for col in collections if not col.startswith('system')]
            
            stats = {
                "database_name": settings.mongodb_database,
                "total_collections": len(hr_collections),
                "collections": {},
                "summary": {
                    "total_documents": 0,
                    "total_size_mb": 0,
                    "total_indexes": 0
                }
            }
            
            for collection_name in hr_collections:
                try:
                    collection_stats = await self.db.command("collStats", collection_name)
                    indexes = await self.db[collection_name].list_indexes().to_list(length=None)
                    
                    col_stat = {
                        "document_count": collection_stats.get("count", 0),
                        "size_mb": collection_stats.get("size", 0) / (1024 * 1024),
                        "avg_document_size": collection_stats.get("avgObjSize", 0),
                        "index_count": len(indexes),
                        "indexes": [idx.get("name") for idx in indexes]
                    }
                    
                    stats["collections"][collection_name] = col_stat
                    stats["summary"]["total_documents"] += col_stat["document_count"]
                    stats["summary"]["total_size_mb"] += col_stat["size_mb"]
                    stats["summary"]["total_indexes"] += col_stat["index_count"]
                    
                except Exception as e:
                    stats["collections"][collection_name] = {"error": str(e)}
            
            # Print summary
            print(f"   📚 Collections: {stats['total_collections']}")
            print(f"   📄 Total Documents: {stats['summary']['total_documents']}")
            print(f"   💾 Total Size: {stats['summary']['total_size_mb']:.2f} MB")
            print(f"   📇 Total Indexes: {stats['summary']['total_indexes']}")
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get collection statistics: {e}")
            return {"error": str(e)}
    
    async def repair_collection(self, collection_name: str) -> bool:
        """Repair and optimize a collection"""
        try:
            print(f"🔧 Repairing collection '{collection_name}'...")
            
            collection = self.db[collection_name]
            
            # Reindex collection
            await collection.reindex()
            print(f"   📇 Rebuilt indexes")
            
            # Compact collection (if supported)
            try:
                await self.db.command("compact", collection_name)
                print(f"   🗜️ Compacted collection")
            except:
                print(f"   ⚠️ Compact not supported/needed")
            
            # Validate collection
            try:
                validation_result = await self.db.command("validate", collection_name)
                if validation_result.get("valid", False):
                    print(f"   ✅ Collection validation passed")
                else:
                    print(f"   ❌ Collection validation failed")
                    return False
            except:
                print(f"   ⚠️ Validation not supported")
            
            print(f"✅ Collection '{collection_name}' repaired successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to repair collection '{collection_name}': {e}")
            return False
    
    async def close_connection(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("🔐 MongoDB connection closed")

async def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="MongoDB Collections Setup and Management")
    parser.add_argument("--action", required=True,
                       choices=["create_all", "create", "drop", "create_indexes", "validate_schema", 
                               "sample_data", "migrate", "stats", "repair"],
                       help="Action to perform")
    parser.add_argument("--collection", help="Specific collection name")
    parser.add_argument("--count", type=int, default=10, help="Number of sample documents to create")
    parser.add_argument("--from", dest="from_version", help="Source version for migration")
    parser.add_argument("--to", dest="to_version", help="Target version for migration")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    print("🏗️ MongoDB Collections Manager")
    print("=" * 40)
    
    manager = MongoDBCollectionManager()
    
    # Connect to database
    if not await manager.connect():
        return
    
    try:
        success = False
        
        if args.action == "create_all":
            success = await manager.create_all_collections()
        
        elif args.action == "create":
            if not args.collection:
                print("❌ Collection name required for create action")
                return
            
            schema_config = manager.schema_config.get("employee_schema", {}).get("collections", {}).get(args.collection, {})
            if not schema_config:
                print(f"❌ No schema configuration found for '{args.collection}'")
                return
            
            success = await manager.create_collection_with_schema(args.collection, schema_config)
            if success:
                await manager.create_indexes(args.collection, schema_config)
        
        elif args.action == "drop":
            if not args.collection:
                print("❌ Collection name required for drop action")
                return
            success = await manager.drop_collection(args.collection, args.confirm)
        
        elif args.action == "create_indexes":
            if args.collection:
                schema_config = manager.schema_config.get("employee_schema", {}).get("collections", {}).get(args.collection, {})
                success = await manager.create_indexes(args.collection, schema_config)
            else:
                # Create indexes for all collections
                collections_config = manager.schema_config.get("employee_schema", {}).get("collections", {})
                success_count = 0
                for collection_name, schema_config in collections_config.items():
                    if await manager.create_indexes(collection_name, schema_config):
                        success_count += 1
                success = success_count == len(collections_config)
        
        elif args.action == "validate_schema":
            if args.collection:
                await manager.validate_collection_schema(args.collection)
                success = True
            else:
                # Validate all collections
                db_collections = await manager.db.list_collection_names()
                hr_collections = [col for col in db_collections if not col.startswith('system')]
                for collection_name in hr_collections:
                    await manager.validate_collection_schema(collection_name)
                success = True
        
        elif args.action == "sample_data":
            if not args.collection:
                print("❌ Collection name required for sample_data action")
                return
            success = await manager.create_sample_data(args.collection, args.count)
        
        elif args.action == "migrate":
            if not all([args.collection, args.from_version, args.to_version]):
                print("❌ Collection name, from version, and to version required for migration")
                return
            success = await manager.migrate_collection(args.collection, args.from_version, args.to_version)
        
        elif args.action == "stats":
            await manager.get_collection_statistics()
            success = True
        
        elif args.action == "repair":
            if not args.collection:
                print("❌ Collection name required for repair action")
                return
            success = await manager.repair_collection(args.collection)
        
        print("=" * 40)
        if success:
            print("🎉 Operation completed successfully!")
        else:
            print("❌ Operation failed!")
    
    finally:
        await manager.close_connection()

if __name__ == "__main__":
    asyncio.run(main())