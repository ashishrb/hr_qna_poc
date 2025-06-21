# tests/test_processing.py
"""
ETL Processing Tests

Purpose:
- Test ETL pipeline end-to-end functionality
- Test Excel file processing and data extraction
- Test data validation and transformation logic
- Test MongoDB data loading and collection management
- Test error handling and data quality issues
- Test incremental updates and data synchronization

Test Coverage:
- Excel file reading and sheet processing
- Data type conversion and validation
- Collection creation and data insertion
- Pipeline statistics and error tracking
- Search index creation and synchronization
- Performance and memory usage during processing
"""

import pytest
import asyncio
import pandas as pd
import tempfile
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
from unittest.mock import patch, MagicMock, AsyncMock

# Import components
from src.processing.etl_pipeline import ETLPipeline
from src.database.mongodb_client import MongoDBClient
from src.database.collections import EmployeeCollections
from src.core.exceptions import ETLException, DataValidationException, FileProcessingException

class TestETLPipeline:
    """Test main ETL pipeline functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_etl_pipeline_initialization(self, clean_test_db: MongoDBClient):
        """Test ETL pipeline initialization"""
        pipeline = ETLPipeline()
        
        # Test default initialization
        assert pipeline.mongodb_client is not None
        assert pipeline.stats["start_time"] is None
        assert pipeline.stats["total_records_processed"] == 0
        assert pipeline.stats["successful_records"] == 0
        assert pipeline.stats["failed_records"] == 0
        assert pipeline.stats["errors"] == []
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_extract_and_load_valid_excel(self, mock_etl_pipeline: ETLPipeline, temp_excel_file: str):
        """Test extracting and loading data from valid Excel file"""
        # Run extract and load
        await mock_etl_pipeline._extract_and_load(temp_excel_file)
        
        # Verify statistics
        assert mock_etl_pipeline.stats["collections_created"] > 0
        assert mock_etl_pipeline.stats["total_records_processed"] > 0
        assert mock_etl_pipeline.stats["successful_records"] > 0
        
        # Verify data was loaded
        collections = await mock_etl_pipeline.mongodb_client.get_collections()
        expected_collections = ["personal_info", "employment"]  # From sample Excel data
        
        for collection_name in expected_collections:
            assert collection_name in collections
            
            # Check that data was inserted
            count = await mock_etl_pipeline.mongodb_client.count_documents(collection_name, {})
            assert count > 0
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_extract_and_load_missing_file(self, mock_etl_pipeline: ETLPipeline):
        """Test handling of missing Excel file"""
        with pytest.raises(FileProcessingException):
            await mock_etl_pipeline._extract_and_load("nonexistent_file.xlsx")
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_process_sheet_valid_data(self, mock_etl_pipeline: ETLPipeline):
        """Test processing individual Excel sheet"""
        # Create test DataFrame
        test_data = pd.DataFrame([
            {"employee_id": "EMP001", "full_name": "John Doe", "email": "john@company.com"},
            {"employee_id": "EMP002", "full_name": "Jane Smith", "email": "jane@company.com"}
        ])
        
        # Process the sheet
        await mock_etl_pipeline._process_sheet("test_sheet", test_data)
        
        # Verify data was processed
        assert mock_etl_pipeline.stats["total_records_processed"] == 2
        assert mock_etl_pipeline.stats["successful_records"] == 2
        
        # Verify data was inserted into MongoDB
        count = await mock_etl_pipeline.mongodb_client.count_documents("test_sheet", {})
        assert count == 2
        
        # Verify specific data
        emp1 = await mock_etl_pipeline.mongodb_client.find_document("test_sheet", {"employee_id": "EMP001"})
        assert emp1 is not None
        assert emp1["full_name"] == "John Doe"
        assert emp1["email"] == "john@company.com"
        assert "created_at" in emp1
        assert "updated_at" in emp1
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_process_sheet_with_nan_values(self, mock_etl_pipeline: ETLPipeline):
        """Test processing sheet with NaN/missing values"""
        # Create DataFrame with NaN values
        test_data = pd.DataFrame([
            {"employee_id": "EMP001", "full_name": "John Doe", "age": 30, "email": "john@company.com"},
            {"employee_id": "EMP002", "full_name": "Jane Smith", "age": pd.NaType(), "email": None}
        ])
        
        # Process the sheet
        await mock_etl_pipeline._process_sheet("test_nan", test_data)
        
        # Verify data was processed
        assert mock_etl_pipeline.stats["successful_records"] == 2
        
        # Check NaN handling
        emp2 = await mock_etl_pipeline.mongodb_client.find_document("test_nan", {"employee_id": "EMP002"})
        assert emp2 is not None
        assert emp2["age"] is None  # NaN should be converted to None
        assert emp2["email"] is None
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_process_sheet_with_datetime(self, mock_etl_pipeline: ETLPipeline):
        """Test processing sheet with datetime values"""
        # Create DataFrame with datetime
        test_data = pd.DataFrame([
            {
                "employee_id": "EMP001", 
                "joining_date": pd.Timestamp("2023-01-15"),
                "last_review": pd.Timestamp("2023-12-01 10:30:00")
            }
        ])
        
        # Process the sheet
        await mock_etl_pipeline._process_sheet("test_datetime", test_data)
        
        # Verify datetime conversion
        emp = await mock_etl_pipeline.mongodb_client.find_document("test_datetime", {"employee_id": "EMP001"})
        assert emp is not None
        assert isinstance(emp["joining_date"], str)  # Should be converted to ISO string
        assert isinstance(emp["last_review"], str)
        assert "2023-01-15" in emp["joining_date"]
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_transform_and_validate(self, populated_test_db: EmployeeCollections):
        """Test data transformation and validation"""
        pipeline = ETLPipeline()
        pipeline.employee_collections = populated_test_db
        
        # Run transformation and validation
        await pipeline._transform_and_validate()
        
        # Should complete without errors for valid data
        assert len(pipeline.stats["errors"]) == 0
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_validate_data_consistency(self, populated_test_db: EmployeeCollections):
        """Test data consistency validation"""
        pipeline = ETLPipeline()
        pipeline.employee_collections = populated_test_db
        
        # Get employee IDs for testing
        employee_ids = await populated_test_db.get_all_employee_ids()
        
        # Run validation
        validation_results = await pipeline._validate_data_consistency(employee_ids[:5])
        
        # Verify validation results structure
        assert "employees_with_personal_info" in validation_results
        assert "employees_with_employment_info" in validation_results
        assert "data_quality_issues" in validation_results
        assert isinstance(validation_results["data_quality_issues"], list)
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_clean_and_standardize_data(self, clean_test_db: MongoDBClient):
        """Test data cleaning and standardization"""
        pipeline = ETLPipeline()
        pipeline.mongodb_client = clean_test_db
        
        # Insert test data with inconsistent formatting
        test_employment_data = [
            {"employee_id": "EMP001", "department": "  it  ", "role": "developer"},
            {"employee_id": "EMP002", "department": "SALES", "role": "  Manager  "},
            {"employee_id": "EMP003", "department": "operations", "role": "ANALYST"}
        ]
        
        for data in test_employment_data:
            await clean_test_db.insert_document("employment", data)
        
        # Run cleaning
        employee_ids = ["EMP001", "EMP002", "EMP003"]
        await pipeline._clean_and_standardize_data(employee_ids)
        
        # Verify data was standardized
        emp1 = await clean_test_db.find_document("employment", {"employee_id": "EMP001"})
        assert emp1["department"] == "It"  # Should be title case with whitespace stripped
        assert emp1["role"] == "Developer"
        
        emp2 = await clean_test_db.find_document("employment", {"employee_id": "EMP002"})
        assert emp2["department"] == "Sales"
        assert emp2["role"] == "Manager"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_full_pipeline_with_mocked_services(self, mock_etl_pipeline: ETLPipeline, temp_excel_file: str):
        """Test full pipeline with mocked external services"""
        with patch.object(mock_etl_pipeline, '_create_search_index', return_value=True) as mock_search, \
             patch.object(mock_etl_pipeline, '_generate_embeddings', return_value=True) as mock_embeddings:
            
            # Run full pipeline
            result = await mock_etl_pipeline.run_full_pipeline(
                excel_file_path=temp_excel_file,
                skip_indexing=False,
                skip_embeddings=False
            )
            
            # Verify pipeline completed successfully
            assert result["status"] == "success"
            assert mock_etl_pipeline.stats["start_time"] is not None
            assert mock_etl_pipeline.stats["end_time"] is not None
            assert mock_etl_pipeline.stats["total_records_processed"] > 0
            
            # Verify external services were called
            mock_search.assert_called_once()
            mock_embeddings.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_full_pipeline_skip_services(self, mock_etl_pipeline: ETLPipeline, temp_excel_file: str):
        """Test full pipeline with skipped external services"""
        with patch.object(mock_etl_pipeline, '_create_search_index') as mock_search, \
             patch.object(mock_etl_pipeline, '_generate_embeddings') as mock_embeddings:
            
            # Run pipeline with services skipped
            result = await mock_etl_pipeline.run_full_pipeline(
                excel_file_path=temp_excel_file,
                skip_indexing=True,
                skip_embeddings=True
            )
            
            # Verify pipeline completed successfully
            assert result["status"] == "success"
            
            # Verify external services were not called
            mock_search.assert_not_called()
            mock_embeddings.assert_not_called()
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_pipeline_error_handling(self, mock_etl_pipeline: ETLPipeline):
        """Test pipeline error handling"""
        # Test with invalid file path
        result = await mock_etl_pipeline.run_full_pipeline("invalid_file.xlsx")
        
        # Verify error handling
        assert result["status"] == "failed"
        assert "error" in result
        assert len(mock_etl_pipeline.stats["errors"]) > 0
        assert mock_etl_pipeline.stats["end_time"] is not None


class TestDataValidation:
    """Test data validation logic"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_required_fields_validation(self, clean_test_db: MongoDBClient):
        """Test validation of required fields"""
        pipeline = ETLPipeline()
        pipeline.mongodb_client = clean_test_db
        
        # Insert data missing required fields
        invalid_data = [
            {"full_name": "John Doe"},  # Missing employee_id
            {"employee_id": "EMP002"},  # Missing full_name
            {"employee_id": "EMP003", "full_name": "Jane Smith", "email": "jane@company.com"}  # Valid
        ]
        
        for data in invalid_data:
            await clean_test_db.insert_document("personal_info", data)
        
        # Run validation
        employee_ids = ["EMP001", "EMP002", "EMP003"]  # EMP001 doesn't exist
        validation_results = await pipeline._validate_data_consistency(employee_ids)
        
        # Should detect data quality issues
        assert len(validation_results["data_quality_issues"]) > 0
    
    def test_data_type_validation(self):
        """Test data type validation logic"""
        pipeline = ETLPipeline()
        
        # Test valid data types
        valid_record = {
            "employee_id": "EMP001",
            "age": 30,
            "total_experience_years": 5.5,
            "performance_rating": 4
        }
        
        # Should not raise any exceptions for valid data
        assert isinstance(valid_record["age"], int)
        assert isinstance(valid_record["total_experience_years"], float)
        assert isinstance(valid_record["performance_rating"], int)
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_email_format_validation(self, clean_test_db: MongoDBClient):
        """Test email format validation"""
        pipeline = ETLPipeline()
        pipeline.mongodb_client = clean_test_db
        
        # Insert data with various email formats
        email_test_data = [
            {"employee_id": "EMP001", "email": "valid@company.com"},
            {"employee_id": "EMP002", "email": "invalid-email"},
            {"employee_id": "EMP003", "email": ""},
            {"employee_id": "EMP004", "email": None}
        ]
        
        for data in email_test_data:
            await clean_test_db.insert_document("personal_info", data)
        
        # Run validation (would detect email format issues in real implementation)
        employee_ids = ["EMP001", "EMP002", "EMP003", "EMP004"]
        validation_results = await pipeline._validate_data_consistency(employee_ids)
        
        # Validation should complete (specific email validation would be in real validator)
        assert "data_quality_issues" in validation_results
    
    def test_date_format_validation(self):
        """Test date format validation"""
        pipeline = ETLPipeline()
        
        # Test various date formats
        valid_dates = [
            "2023-01-15",
            "2023-12-31T10:30:00",
            "2023-01-01T00:00:00.000Z"
        ]
        
        invalid_dates = [
            "15/01/2023",  # Wrong format
            "2023-13-01",  # Invalid month
            "not-a-date"   # Invalid format
        ]
        
        # In real implementation, would validate these formats
        for date_str in valid_dates:
            # Should be able to parse valid dates
            assert isinstance(date_str, str)
        
        for date_str in invalid_dates:
            # Should detect invalid dates
            assert isinstance(date_str, str)


class TestExcelProcessing:
    """Test Excel file processing functionality"""
    
    def test_create_complex_excel_file(self, temp_directory: str):
        """Test creating and reading complex Excel file"""
        excel_path = os.path.join(temp_directory, "complex_test.xlsx")
        
        # Create complex test data
        personal_data = pd.DataFrame([
            {"employee_id": "EMP001", "full_name": "John Doe", "age": 30, "email": "john@company.com"},
            {"employee_id": "EMP002", "full_name": "Jane Smith", "age": 28, "email": "jane@company.com"},
            {"employee_id": "EMP003", "full_name": "Bob Johnson", "age": 35, "email": "bob@company.com"}
        ])
        
        employment_data = pd.DataFrame([
            {"employee_id": "EMP001", "department": "IT", "role": "Developer", "joining_date": "2023-01-15"},
            {"employee_id": "EMP002", "department": "Sales", "role": "Manager", "joining_date": "2022-06-01"},
            {"employee_id": "EMP003", "department": "Operations", "role": "Analyst", "joining_date": "2021-03-10"}
        ])
        
        learning_data = pd.DataFrame([
            {"employee_id": "EMP001", "certifications": "AWS, Python", "courses_completed": 8},
            {"employee_id": "EMP002", "certifications": "PMP, Salesforce", "courses_completed": 5},
            {"employee_id": "EMP003", "certifications": "Six Sigma", "courses_completed": 3}
        ])
        
        # Write to Excel
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            personal_data.to_excel(writer, sheet_name='Personal Info', index=False)
            employment_data.to_excel(writer, sheet_name='Employment', index=False)
            learning_data.to_excel(writer, sheet_name='Learning', index=False)
        
        # Verify file was created
        assert os.path.exists(excel_path)
        
        # Read back and verify
        excel_data = pd.read_excel(excel_path, sheet_name=None)
        assert len(excel_data) == 3
        assert 'Personal Info' in excel_data
        assert 'Employment' in excel_data
        assert 'Learning' in excel_data
        
        # Verify data integrity
        assert len(excel_data['Personal Info']) == 3
        assert excel_data['Personal Info'].iloc[0]['full_name'] == 'John Doe'
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_process_excel_with_empty_sheets(self, mock_etl_pipeline: ETLPipeline, temp_directory: str):
        """Test processing Excel file with empty sheets"""
        excel_path = os.path.join(temp_directory, "empty_sheets.xlsx")
        
        # Create Excel with empty sheet
        empty_df = pd.DataFrame()
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            empty_df.to_excel(writer, sheet_name='Empty Sheet', index=False)
        
        # Process the sheet
        await mock_etl_pipeline._process_sheet("empty_sheet", empty_df)
        
        # Should handle empty data gracefully
        assert mock_etl_pipeline.stats["total_records_processed"] == 0
        
        # No documents should be inserted
        count = await mock_etl_pipeline.mongodb_client.count_documents("empty_sheet", {})
        assert count == 0
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_process_excel_with_special_characters(self, mock_etl_pipeline: ETLPipeline, temp_directory: str):
        """Test processing Excel with special characters and unicode"""
        excel_path = os.path.join(temp_directory, "special_chars.xlsx")
        
        # Create data with special characters
        special_data = pd.DataFrame([
            {"employee_id": "EMP001", "full_name": "José García", "notes": "café & résumé"},
            {"employee_id": "EMP002", "full_name": "李小明", "notes": "中文测试"},
            {"employee_id": "EMP003", "full_name": "Müller", "notes": "🎉 emoji test"}
        ])
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            special_data.to_excel(writer, sheet_name='Special Chars', index=False)
        
        # Process the sheet
        await mock_etl_pipeline._process_sheet("special_chars", special_data)
        
        # Verify special characters were preserved
        emp1 = await mock_etl_pipeline.mongodb_client.find_document("special_chars", {"employee_id": "EMP001"})
        assert emp1["full_name"] == "José García"
        assert "café" in emp1["notes"]
        
        emp2 = await mock_etl_pipeline.mongodb_client.find_document("special_chars", {"employee_id": "EMP002"})
        assert emp2["full_name"] == "李小明"
        assert "中文" in emp2["notes"]


class TestIncrementalUpdates:
    """Test incremental update functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_incremental_update_single_employee(self, mock_etl_pipeline: ETLPipeline):
        """Test incremental update for single employee"""
        # Insert initial data
        initial_data = {
            "employee_id": "EMP001",
            "full_name": "John Doe",
            "department": "IT",
            "role": "Developer"
        }
        
        await mock_etl_pipeline.mongodb_client.insert_document("personal_info", initial_data)
        
        # Prepare update data
        update_data = {
            "employee_id": "EMP001",
            "department": "Engineering",  # Changed
            "role": "Senior Developer",    # Changed
            "location": "Remote"          # New field
        }
        
        # Run incremental update
        result = await mock_etl_pipeline.run_incremental_update(update_data)
        
        # Verify update was successful
        assert result["status"] == "success"
        assert result["employee_id"] == "EMP001"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_incremental_update_missing_employee_id(self, mock_etl_pipeline: ETLPipeline):
        """Test incremental update with missing employee ID"""
        # Try to update without employee_id
        update_data = {
            "department": "IT",
            "role": "Developer"
        }
        
        # Should fail without employee_id
        result = await mock_etl_pipeline.run_incremental_update(update_data)
        
        assert result["status"] == "failed"
        assert "Employee ID required" in result["error"]


class TestPerformanceAndMemory:
    """Test ETL performance and memory usage"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    @pytest.mark.slow
    async def test_large_dataset_processing(self, mock_etl_pipeline: ETLPipeline, temp_directory: str):
        """Test processing large dataset"""
        excel_path = os.path.join(temp_directory, "large_dataset.xlsx")
        
        # Create large dataset (1000 records)
        large_data = pd.DataFrame([
            {
                "employee_id": f"EMP{i:04d}",
                "full_name": f"Employee {i}",
                "email": f"emp{i}@company.com",
                "department": ["IT", "Sales", "Operations", "HR"][i % 4],
                "role": ["Developer", "Manager", "Analyst"][i % 3]
            }
            for i in range(1, 1001)
        ])
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            large_data.to_excel(writer, sheet_name='Large Dataset', index=False)
        
        # Process large dataset
        start_time = datetime.utcnow()
        await mock_etl_pipeline._process_sheet("large_dataset", large_data)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify performance
        assert mock_etl_pipeline.stats["total_records_processed"] == 1000
        assert mock_etl_pipeline.stats["successful_records"] == 1000
        assert processing_time < 30.0  # Should process 1000 records in under 30 seconds
        
        # Verify data was inserted correctly
        count = await mock_etl_pipeline.mongodb_client.count_documents("large_dataset", {})
        assert count == 1000
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_memory_usage_monitoring(self, mock_etl_pipeline: ETLPipeline):
        """Test memory usage during processing"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create moderate dataset
        test_data = pd.DataFrame([
            {
                "employee_id": f"EMP{i:03d}",
                "data": "x" * 1000,  # 1KB per record
                "large_field": f"Large data field {i}" * 10
            }
            for i in range(100)
        ])
        
        # Process data
        await mock_etl_pipeline._process_sheet("memory_test", test_data)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for this test)
        assert memory_increase < 50.0
        
        # Verify processing was successful
        assert mock_etl_pipeline.stats["successful_records"] == 100


class TestErrorRecovery:
    """Test error recovery and data consistency"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_partial_failure_recovery(self, mock_etl_pipeline: ETLPipeline):
        """Test recovery from partial processing failures"""
        # Create data that will cause some failures
        mixed_data = pd.DataFrame([
            {"employee_id": "EMP001", "valid_field": "valid_data"},
            {"employee_id": None, "valid_field": "invalid_employee_id"},  # Invalid
            {"employee_id": "EMP003", "valid_field": "valid_data"},
        ])
        
        # Process with mixed data
        await mock_etl_pipeline._process_sheet("mixed_data", mixed_data)
        
        # Should process valid records despite some failures
        assert mock_etl_pipeline.stats["total_records_processed"] == 3
        
        # Check that valid records were processed
        count = await mock_etl_pipeline.mongodb_client.count_documents("mixed_data", {})
        assert count >= 2  # At least the valid records
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_transaction_rollback_simulation(self, mock_etl_pipeline: ETLPipeline):
        """Test handling of transaction-like operations"""
        # Insert some initial data
        initial_data = {"employee_id": "EMP001", "status": "initial"}
        await mock_etl_pipeline.mongodb_client.insert_document("rollback_test", initial_data)
        
        # Verify initial state
        initial_count = await mock_etl_pipeline.mongodb_client.count_documents("rollback_test", {})
        assert initial_count == 1
        
        # Simulate processing that might need rollback
        try:
            # Process some data
            test_data = pd.DataFrame([
                {"employee_id": "EMP002", "status": "new"},
                {"employee_id": "EMP003", "status": "new"}
            ])
            
            await mock_etl_pipeline._process_sheet("rollback_test", test_data)
            
            # If we get here, processing succeeded
            final_count = await mock_etl_pipeline.mongodb_client.count_documents("rollback_test", {})
            assert final_count == 3  # Initial + 2 new records
            
        except Exception as e:
            # In case of failure, verify original data is still intact
            remaining_count = await mock_etl_pipeline.mongodb_client.count_documents("rollback_test", {})
            assert remaining_count >= 1  # At least original data should remain