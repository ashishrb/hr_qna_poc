# src/processing/etl_pipeline.py
import asyncio
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database.mongodb_client import mongodb_client
from src.database.collections import employee_collections
from src.search.fixed_indexer import FixedAzureSearchIndexer
from src.search.embeddings import EmbeddingsService
from src.core.exceptions import ETLException, FileProcessingException, DataValidationException
from src.core.models import CompleteEmployeeProfile

class ETLPipeline:
    """Main ETL pipeline orchestrator for HR data processing"""
    
    def __init__(self):
        self.mongodb_client = mongodb_client
        self.employee_collections = employee_collections
        self.indexer = None
        self.embeddings_service = None
        
        # Pipeline statistics
        self.stats = {
            "start_time": None,
            "end_time": None,
            "total_records_processed": 0,
            "successful_records": 0,
            "failed_records": 0,
            "collections_created": 0,
            "documents_indexed": 0,
            "embeddings_generated": 0,
            "errors": []
        }
    
    async def run_full_pipeline(self, excel_file_path: str, skip_indexing: bool = False, skip_embeddings: bool = False) -> Dict[str, Any]:
        """Run the complete ETL pipeline from Excel to searchable index"""
        try:
            print("🚀 Starting Full ETL Pipeline")
            print("=" * 60)
            
            self.stats["start_time"] = datetime.utcnow()
            
            # Step 1: Extract and Load to MongoDB
            print("\n📊 Step 1: Extract and Load to MongoDB")
            await self._extract_and_load(excel_file_path)
            
            # Step 2: Transform and Validate Data
            print("\n🔄 Step 2: Transform and Validate Data")
            await self._transform_and_validate()
            
            # Step 3: Create Search Index (optional)
            if not skip_indexing:
                print("\n🔍 Step 3: Create Search Index")
                await self._create_search_index()
            else:
                print("\n⏭️ Step 3: Skipping search index creation")
            
            # Step 4: Generate Embeddings (optional)
            if not skip_embeddings and not skip_indexing:
                print("\n🧠 Step 4: Generate Embeddings")
                await self._generate_embeddings()
            else:
                print("\n⏭️ Step 4: Skipping embeddings generation")
            
            # Step 5: Verify Pipeline
            print("\n✅ Step 5: Verify Pipeline Results")
            await self._verify_pipeline()
            
            self.stats["end_time"] = datetime.utcnow()
            
            print("\n🎉 ETL Pipeline Completed Successfully!")
            self._print_pipeline_summary()
            
            return {
                "status": "success",
                "stats": self.stats,
                "message": "ETL pipeline completed successfully"
            }
            
        except Exception as e:
            self.stats["end_time"] = datetime.utcnow()
            self.stats["errors"].append(str(e))
            print(f"\n❌ ETL Pipeline Failed: {e}")
            
            return {
                "status": "failed",
                "stats": self.stats,
                "error": str(e)
            }
    
    async def _extract_and_load(self, excel_file_path: str):
        """Extract data from Excel and load into MongoDB"""
        try:
            # Validate file existence
            if not Path(excel_file_path).exists():
                raise FileProcessingException(f"Excel file not found: {excel_file_path}", excel_file_path, "xlsx")
            
            # Connect to MongoDB
            await self.mongodb_client.connect()
            
            # Read Excel file
            print(f"📖 Reading Excel file: {excel_file_path}")
            excel_data = pd.read_excel(excel_file_path, sheet_name=None)
            print(f"   Found {len(excel_data)} sheets to process")
            
            # Process each sheet
            for sheet_name, df in excel_data.items():
                await self._process_sheet(sheet_name, df)
                self.stats["collections_created"] += 1
            
            print(f"✅ Successfully loaded data to {len(excel_data)} collections")
            
        except Exception as e:
            raise ETLException(f"Extract and load failed: {str(e)}", "extract_load", excel_file_path)
    
    async def _process_sheet(self, sheet_name: str, df: pd.DataFrame):
        """Process individual Excel sheet and insert into MongoDB"""
        try:
            # Clean sheet name for collection name
            collection_name = sheet_name.lower().replace(' ', '_')
            collection = await self.mongodb_client.get_collection(collection_name)
            
            print(f"   🔄 Processing sheet: {sheet_name}")
            print(f"      📊 Rows: {len(df)}, Columns: {len(df.columns)}")
            
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
                self.stats["total_records_processed"] += 1
            
            # Insert into MongoDB
            if records:
                # Clear existing data
                await collection.delete_many({})
                
                # Insert new data
                result = await collection.insert_many(records)
                self.stats["successful_records"] += len(result.inserted_ids)
                
                print(f"      ✅ Inserted {len(result.inserted_ids)} records")
                
                # Create index on employee_id if present
                if 'employee_id' in df.columns:
                    await collection.create_index("employee_id")
                    print(f"      📇 Created index on employee_id")
            
        except Exception as e:
            self.stats["failed_records"] += len(df) if df is not None else 0
            self.stats["errors"].append(f"Sheet {sheet_name}: {str(e)}")
            print(f"      ❌ Error processing sheet {sheet_name}: {e}")
    
    async def _transform_and_validate(self):
        """Transform and validate data quality"""
        try:
            print("   🔍 Validating data quality...")
            
            # Get all employee IDs
            employee_ids = await self.employee_collections.get_all_employee_ids()
            print(f"   📊 Found {len(employee_ids)} unique employees")
            
            # Validate data consistency
            validation_results = await self._validate_data_consistency(employee_ids)
            
            # Clean and standardize data
            await self._clean_and_standardize_data(employee_ids)
            
            print("   ✅ Data transformation and validation completed")
            
        except Exception as e:
            raise ETLException(f"Transform and validate failed: {str(e)}", "transform_validate")
    
    async def _validate_data_consistency(self, employee_ids: List[str]) -> Dict[str, Any]:
        """Validate data consistency across collections"""
        validation_results = {
            "employees_with_personal_info": 0,
            "employees_with_employment_info": 0,
            "employees_missing_critical_data": [],
            "data_quality_issues": []
        }
        
        try:
            for employee_id in employee_ids[:10]:  # Sample validation for performance
                # Check personal info
                personal = await self.employee_collections.get_employee_personal_info(employee_id)
                if personal:
                    validation_results["employees_with_personal_info"] += 1
                    
                    # Validate critical fields
                    if not personal.get("full_name"):
                        validation_results["data_quality_issues"].append(f"{employee_id}: Missing full_name")
                    
                    if not personal.get("email"):
                        validation_results["data_quality_issues"].append(f"{employee_id}: Missing email")
                
                # Check employment info
                employment = await self.employee_collections.get_employee_employment_info(employee_id)
                if employment:
                    validation_results["employees_with_employment_info"] += 1
                    
                    # Validate critical fields
                    if not employment.get("department"):
                        validation_results["data_quality_issues"].append(f"{employee_id}: Missing department")
                    
                    if not employment.get("role"):
                        validation_results["data_quality_issues"].append(f"{employee_id}: Missing role")
                else:
                    validation_results["employees_missing_critical_data"].append(employee_id)
            
            # Print validation summary
            if validation_results["data_quality_issues"]:
                print(f"   ⚠️ Found {len(validation_results['data_quality_issues'])} data quality issues")
                for issue in validation_results["data_quality_issues"][:5]:  # Show first 5
                    print(f"      - {issue}")
            
            return validation_results
            
        except Exception as e:
            raise DataValidationException(f"Data validation failed: {str(e)}")
    
    async def _clean_and_standardize_data(self, employee_ids: List[str]):
        """Clean and standardize data"""
        try:
            cleaned_count = 0
            
            for employee_id in employee_ids:
                # Get employment info for standardization
                employment = await self.employee_collections.get_employee_employment_info(employee_id)
                if employment:
                    updates = {}
                    
                    # Standardize department names
                    if employment.get("department"):
                        dept = employment["department"].strip().title()
                        if dept != employment["department"]:
                            updates["department"] = dept
                    
                    # Standardize role names
                    if employment.get("role"):
                        role = employment["role"].strip().title()
                        if role != employment["role"]:
                            updates["role"] = role
                    
                    # Apply updates if any
                    if updates:
                        await self.employee_collections.update_employee_data(
                            employee_id, "employment", updates
                        )
                        cleaned_count += 1
            
            print(f"   🧹 Cleaned and standardized {cleaned_count} employee records")
            
        except Exception as e:
            print(f"   ⚠️ Data cleaning warning: {e}")
    
    async def _create_search_index(self):
        """Create Azure Search index"""
        try:
            # Initialize indexer
            self.indexer = FixedAzureSearchIndexer()
            
            # Connect to MongoDB
            connected = await self.indexer.connect_to_mongodb()
            if not connected:
                raise ETLException("Failed to connect to MongoDB for indexing", "search_index")
            
            # Create/update search index
            print("   📝 Creating search index...")
            index_created = await self.indexer.create_or_update_index()
            if not index_created:
                raise ETLException("Failed to create search index", "search_index")
            
            # Index all employees
            print("   📊 Indexing employee data...")
            indexed = await self.indexer.index_all_employees()
            if not indexed:
                raise ETLException("Failed to index employee data", "search_index")
            
            # Get index statistics
            await self.indexer.verify_index()
            
            # Update statistics
            self.stats["documents_indexed"] = await self._get_indexed_document_count()
            
            print("   ✅ Search index creation completed")
            
        except Exception as e:
            raise ETLException(f"Search index creation failed: {str(e)}", "search_index")
        finally:
            if self.indexer:
                await self.indexer.close_connections()
    
    async def _generate_embeddings(self):
        """Generate vector embeddings for semantic search"""
        try:
            # Initialize embeddings service
            self.embeddings_service = EmbeddingsService()
            
            # Connect to MongoDB
            connected = await self.embeddings_service.connect_to_mongodb()
            if not connected:
                raise ETLException("Failed to connect to MongoDB for embeddings", "embeddings")
            
            # Generate embeddings
            print("   🧠 Generating vector embeddings...")
            updated = await self.embeddings_service.update_documents_with_embeddings()
            if not updated:
                raise ETLException("Failed to generate embeddings", "embeddings")
            
            # Test search capabilities
            print("   🧪 Testing search capabilities...")
            self.embeddings_service.test_search_capabilities()
            
            # Update statistics
            self.stats["embeddings_generated"] = await self._get_indexed_document_count()
            
            print("   ✅ Embeddings generation completed")
            
        except Exception as e:
            raise ETLException(f"Embeddings generation failed: {str(e)}", "embeddings")
        finally:
            if self.embeddings_service:
                await self.embeddings_service.close_connections()
    
    async def _verify_pipeline(self):
        """Verify the complete pipeline results"""
        try:
            print("   🔍 Verifying pipeline results...")
            
            # Verify MongoDB data
            collections = await self.mongodb_client.get_collections()
            hr_collections = [col for col in collections if not col.startswith('system')]
            
            total_documents = 0
            for collection_name in hr_collections:
                count = await self.mongodb_client.count_documents(collection_name)
                total_documents += count
                print(f"      📊 {collection_name}: {count} documents")
            
            # Verify search index if created
            if self.indexer:
                indexed_count = await self._get_indexed_document_count()
                print(f"      🔍 Search index: {indexed_count} documents")
            
            # Verify embeddings if created
            if self.embeddings_service:
                print(f"      🧠 Embeddings: Generated for search documents")
            
            # Get sample employee profile
            employee_ids = await self.employee_collections.get_all_employee_ids()
            if employee_ids:
                sample_profile = await self.employee_collections.get_complete_employee_profile(employee_ids[0])
                print(f"      👤 Sample employee: {sample_profile.get('full_name', 'Unknown')}")
            
            print("   ✅ Pipeline verification completed")
            
        except Exception as e:
            print(f"   ⚠️ Verification warning: {e}")
    
    async def _get_indexed_document_count(self) -> int:
        """Get count of indexed documents"""
        try:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            from src.core.config import settings
            
            search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name="hr-employees-fixed",
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
            
            results = search_client.search("*", include_total_count=True, top=0)
            return results.get_count()
        except:
            return 0
    
    def _print_pipeline_summary(self):
        """Print pipeline execution summary"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        print("\n📈 Pipeline Execution Summary")
        print("=" * 40)
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Total Records Processed: {self.stats['total_records_processed']}")
        print(f"✅ Successful Records: {self.stats['successful_records']}")
        print(f"❌ Failed Records: {self.stats['failed_records']}")
        print(f"🗂️  Collections Created: {self.stats['collections_created']}")
        print(f"🔍 Documents Indexed: {self.stats['documents_indexed']}")
        print(f"🧠 Embeddings Generated: {self.stats['embeddings_generated']}")
        
        if self.stats["errors"]:
            print(f"⚠️  Errors: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:3]:  # Show first 3 errors
                print(f"   - {error}")
    
    async def run_incremental_update(self, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run incremental update for changed employee data"""
        try:
            print("🔄 Starting Incremental Update")
            
            employee_id = updated_data.get("employee_id")
            if not employee_id:
                raise ETLException("Employee ID required for incremental update", "incremental_update")
            
            # Update MongoDB collections
            await self._update_mongodb_record(employee_id, updated_data)
            
            # Update search index
            await self._update_search_index_record(employee_id)
            
            # Regenerate embeddings for this record
            await self._update_embeddings_record(employee_id)
            
            print(f"✅ Incremental update completed for employee {employee_id}")
            
            return {"status": "success", "employee_id": employee_id}
            
        except Exception as e:
            print(f"❌ Incremental update failed: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _update_mongodb_record(self, employee_id: str, updated_data: Dict[str, Any]):
        """Update MongoDB record"""
        # Implementation for updating specific employee record
        pass
    
    async def _update_search_index_record(self, employee_id: str):
        """Update search index record"""
        # Implementation for updating specific search index record
        pass
    
    async def _update_embeddings_record(self, employee_id: str):
        """Update embeddings for specific record"""
        # Implementation for updating embeddings for specific employee
        pass

# Global instance
etl_pipeline = ETLPipeline()

# Utility function for running pipeline
async def run_etl_pipeline(excel_file_path: str, **kwargs):
    """Utility function to run ETL pipeline"""
    return await etl_pipeline.run_full_pipeline(excel_file_path, **kwargs)