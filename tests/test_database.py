# tests/test_database.py
"""
Database Functionality Tests

Purpose:
- Test MongoDB connection and basic operations
- Test employee collections CRUD operations
- Test data integrity and validation
- Test collection relationships and foreign keys
- Test database performance and error handling
- Test data aggregation and statistics functions

Test Coverage:
- MongoDB client connection and disconnection
- Collection creation and management
- Document insertion, retrieval, update, deletion
- Data validation and schema compliance
- Employee profile aggregation across collections
- Error handling and edge cases
"""

import pytest
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
import pymongo.errors

# Import fixtures and components
from src.database.mongodb_client import MongoDBClient
from src.database.collections import EmployeeCollections
from src.core.exceptions import (
    DatabaseException, DocumentNotFoundException, 
    DocumentInsertException, DocumentUpdateException
)

class TestMongoDBClient:
    """Test MongoDB client basic operations"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_mongodb_connection(self, test_mongodb_client: MongoDBClient):
        """Test MongoDB connection establishment"""
        # Test connection is established
        assert test_mongodb_client.client is not None
        assert test_mongodb_client.database is not None
        
        # Test ping to verify connection
        result = await test_mongodb_client.client.admin.command('ping')
        assert result.get('ok') == 1
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_collection(self, test_mongodb_client: MongoDBClient):
        """Test collection retrieval"""
        collection = await test_mongodb_client.get_collection("test_collection")
        assert collection is not None
        assert collection.name == "test_collection"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_insert_document(self, test_mongodb_client: MongoDBClient):
        """Test document insertion"""
        test_doc = {
            "test_field": "test_value",
            "created_at": datetime.utcnow().isoformat()
        }
        
        doc_id = await test_mongodb_client.insert_document("test_collection", test_doc)
        assert doc_id is not None
        assert isinstance(doc_id, str)
        
        # Verify document was inserted
        retrieved = await test_mongodb_client.find_document("test_collection", {"test_field": "test_value"})
        assert retrieved is not None
        assert retrieved["test_field"] == "test_value"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_insert_multiple_documents(self, test_mongodb_client: MongoDBClient):
        """Test multiple document insertion"""
        test_docs = [
            {"name": "Document 1", "value": 1},
            {"name": "Document 2", "value": 2},
            {"name": "Document 3", "value": 3}
        ]
        
        doc_ids = await test_mongodb_client.insert_documents("test_collection", test_docs)
        assert len(doc_ids) == 3
        assert all(isinstance(doc_id, str) for doc_id in doc_ids)
        
        # Verify all documents were inserted
        retrieved_docs = await test_mongodb_client.find_documents("test_collection", {})
        assert len(retrieved_docs) >= 3
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_find_document(self, test_mongodb_client: MongoDBClient):
        """Test document retrieval"""
        # Insert test document
        test_doc = {"unique_field": "unique_value_123", "data": "test"}
        await test_mongodb_client.insert_document("test_collection", test_doc)
        
        # Find the document
        found_doc = await test_mongodb_client.find_document(
            "test_collection", 
            {"unique_field": "unique_value_123"}
        )
        
        assert found_doc is not None
        assert found_doc["unique_field"] == "unique_value_123"
        assert found_doc["data"] == "test"
        assert "_id" in found_doc
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_find_documents_with_limit(self, test_mongodb_client: MongoDBClient):
        """Test multiple documents retrieval with limit"""
        # Insert multiple test documents
        test_docs = [{"batch": "test_batch", "number": i} for i in range(10)]
        await test_mongodb_client.insert_documents("test_collection", test_docs)
        
        # Find with limit
        found_docs = await test_mongodb_client.find_documents(
            "test_collection", 
            {"batch": "test_batch"}, 
            limit=5
        )
        
        assert len(found_docs) == 5
        assert all(doc["batch"] == "test_batch" for doc in found_docs)
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_update_document(self, test_mongodb_client: MongoDBClient):
        """Test document update"""
        # Insert test document
        test_doc = {"update_test": "original_value", "counter": 1}
        await test_mongodb_client.insert_document("test_collection", test_doc)
        
        # Update the document
        update_result = await test_mongodb_client.update_document(
            "test_collection",
            {"update_test": "original_value"},
            {"update_test": "updated_value", "counter": 2}
        )
        
        assert update_result is True
        
        # Verify update
        updated_doc = await test_mongodb_client.find_document(
            "test_collection", 
            {"update_test": "updated_value"}
        )
        assert updated_doc is not None
        assert updated_doc["counter"] == 2
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_delete_document(self, test_mongodb_client: MongoDBClient):
        """Test document deletion"""
        # Insert test document
        test_doc = {"delete_test": "to_be_deleted", "temp": True}
        await test_mongodb_client.insert_document("test_collection", test_doc)
        
        # Verify insertion
        found = await test_mongodb_client.find_document("test_collection", {"delete_test": "to_be_deleted"})
        assert found is not None
        
        # Delete the document
        delete_result = await test_mongodb_client.delete_document(
            "test_collection",
            {"delete_test": "to_be_deleted"}
        )
        
        assert delete_result is True
        
        # Verify deletion
        not_found = await test_mongodb_client.find_document("test_collection", {"delete_test": "to_be_deleted"})
        assert not_found is None
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_count_documents(self, test_mongodb_client: MongoDBClient):
        """Test document counting"""
        # Insert test documents
        test_docs = [{"count_test": True, "group": "A"} for _ in range(5)]
        test_docs.extend([{"count_test": True, "group": "B"} for _ in range(3)])
        await test_mongodb_client.insert_documents("test_collection", test_docs)
        
        # Count all documents with count_test=True
        total_count = await test_mongodb_client.count_documents("test_collection", {"count_test": True})
        assert total_count == 8
        
        # Count documents in group A
        group_a_count = await test_mongodb_client.count_documents("test_collection", {"group": "A"})
        assert group_a_count == 5
        
        # Count documents in group B
        group_b_count = await test_mongodb_client.count_documents("test_collection", {"group": "B"})
        assert group_b_count == 3
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_collections(self, test_mongodb_client: MongoDBClient):
        """Test collection listing"""
        # Create some test collections by inserting documents
        await test_mongodb_client.insert_document("collection1", {"test": 1})
        await test_mongodb_client.insert_document("collection2", {"test": 2})
        
        collections = await test_mongodb_client.get_collections()
        assert isinstance(collections, list)
        assert "collection1" in collections
        assert "collection2" in collections
        
        # System collections should be filtered out
        assert all(not col.startswith('system') for col in collections)


class TestEmployeeCollections:
    """Test employee collections specific operations"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_employee_personal_info(self, employee_collections: EmployeeCollections, sample_employee_data: Dict[str, Any]):
        """Test retrieving employee personal information"""
        # Insert sample data
        await employee_collections.mongodb_client.insert_document(
            "personal_info", 
            sample_employee_data["personal_info"]
        )
        
        # Retrieve personal info
        personal_info = await employee_collections.get_employee_personal_info("EMP001")
        
        assert personal_info is not None
        assert personal_info["employee_id"] == "EMP001"
        assert personal_info["full_name"] == "John Doe"
        assert personal_info["email"] == "john.doe@company.com"
        assert personal_info["department"] is None or "department" not in personal_info
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_employee_employment_info(self, employee_collections: EmployeeCollections, sample_employee_data: Dict[str, Any]):
        """Test retrieving employee employment information"""
        # Insert sample data
        await employee_collections.mongodb_client.insert_document(
            "employment", 
            sample_employee_data["employment"]
        )
        
        # Retrieve employment info
        employment_info = await employee_collections.get_employee_employment_info("EMP001")
        
        assert employment_info is not None
        assert employment_info["employee_id"] == "EMP001"
        assert employment_info["department"] == "IT"
        assert employment_info["role"] == "Developer"
        assert employment_info["work_mode"] == "Remote"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_nonexistent_employee(self, employee_collections: EmployeeCollections):
        """Test retrieving information for non-existent employee"""
        personal_info = await employee_collections.get_employee_personal_info("NONEXISTENT")
        assert personal_info is None
        
        employment_info = await employee_collections.get_employee_employment_info("NONEXISTENT")
        assert employment_info is None
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_complete_employee_profile(self, populated_test_db: EmployeeCollections):
        """Test retrieving complete employee profile from all collections"""
        # Get complete profile for first employee
        profile = await populated_test_db.get_complete_employee_profile("EMP001")
        
        assert profile is not None
        assert profile["employee_id"] == "EMP001"
        
        # Check that data from multiple collections is merged
        assert "full_name" in profile  # From personal_info
        assert "department" in profile  # From employment
        assert "certifications" in profile  # From learning
        assert "total_experience_years" in profile  # From experience
        assert "performance_rating" in profile  # From performance
        assert "current_project" in profile  # From engagement
        
        # Verify specific values
        assert profile["full_name"] == "Test Employee 1"
        assert profile["department"] == "IT"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_all_employee_ids(self, populated_test_db: EmployeeCollections):
        """Test retrieving all unique employee IDs"""
        employee_ids = await populated_test_db.get_all_employee_ids()
        
        assert isinstance(employee_ids, list)
        assert len(employee_ids) == 10  # We inserted 10 sample employees
        
        # Check that all IDs follow expected format
        for emp_id in employee_ids:
            assert emp_id.startswith("EMP")
            assert len(emp_id) == 6  # EMP + 3 digits
        
        # Check that IDs are unique
        assert len(set(employee_ids)) == len(employee_ids)
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_employees_by_department(self, populated_test_db: EmployeeCollections):
        """Test retrieving employees by department"""
        it_employees = await populated_test_db.get_employees_by_department("IT")
        
        assert isinstance(it_employees, list)
        assert len(it_employees) >= 1  # At least one IT employee from sample data
        
        # Verify all returned employees are in IT
        for emp_id in it_employees:
            employment_info = await populated_test_db.get_employee_employment_info(emp_id)
            assert employment_info["department"] == "IT"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_employees_by_role(self, populated_test_db: EmployeeCollections):
        """Test retrieving employees by role"""
        developers = await populated_test_db.get_employees_by_role("Developer")
        
        assert isinstance(developers, list)
        
        # If we have developers, verify they have the correct role
        for emp_id in developers:
            employment_info = await populated_test_db.get_employee_employment_info(emp_id)
            assert employment_info["role"] == "Developer"
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_employees_by_certification(self, populated_test_db: EmployeeCollections):
        """Test retrieving employees by certification"""
        aws_certified = await populated_test_db.get_employees_by_certification("AWS")
        
        assert isinstance(aws_certified, list)
        
        # Verify employees have AWS certification
        for emp_id in aws_certified:
            learning_info = await populated_test_db.get_employee_learning_info(emp_id)
            assert "AWS" in learning_info.get("certifications", "")
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_employees_by_location(self, populated_test_db: EmployeeCollections):
        """Test retrieving employees by location"""
        ny_employees = await populated_test_db.get_employees_by_location("New York")
        
        assert isinstance(ny_employees, list)
        
        # Verify employees are in New York
        for emp_id in ny_employees:
            personal_info = await populated_test_db.get_employee_personal_info(emp_id)
            assert "New York" in personal_info.get("location", "")
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_department_statistics(self, populated_test_db: EmployeeCollections):
        """Test department statistics aggregation"""
        dept_stats = await populated_test_db.get_department_statistics()
        
        assert isinstance(dept_stats, dict)
        assert len(dept_stats) > 0
        
        # Check that we have expected departments
        expected_departments = ["IT", "Sales", "Operations", "HR", "Finance"]
        for dept in expected_departments:
            if dept in dept_stats:
                assert isinstance(dept_stats[dept], int)
                assert dept_stats[dept] > 0
        
        # Verify total count matches employee count
        total_employees = sum(dept_stats.values())
        all_employee_ids = await populated_test_db.get_all_employee_ids()
        assert total_employees == len(all_employee_ids)
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_role_statistics(self, populated_test_db: EmployeeCollections):
        """Test role statistics aggregation"""
        role_stats = await populated_test_db.get_role_statistics()
        
        assert isinstance(role_stats, dict)
        assert len(role_stats) > 0
        
        # Check that counts are positive integers
        for role, count in role_stats.items():
            assert isinstance(count, int)
            assert count > 0
        
        # Verify total count
        total_employees = sum(role_stats.values())
        all_employee_ids = await populated_test_db.get_all_employee_ids()
        assert total_employees == len(all_employee_ids)
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_update_employee_data(self, employee_collections: EmployeeCollections, sample_employee_data: Dict[str, Any]):
        """Test updating employee data"""
        # Insert initial data
        await employee_collections.mongodb_client.insert_document(
            "personal_info", 
            sample_employee_data["personal_info"]
        )
        
        # Update employee data
        update_data = {
            "location": "San Francisco",
            "contact_number": "+1-555-9999"
        }
        
        result = await employee_collections.update_employee_data(
            "EMP001", 
            "personal_info", 
            update_data
        )
        
        assert result is True
        
        # Verify the update
        updated_info = await employee_collections.get_employee_personal_info("EMP001")
        assert updated_info["location"] == "San Francisco"
        assert updated_info["contact_number"] == "+1-555-9999"
        assert "updated_at" in updated_info


class TestDataIntegrity:
    """Test data integrity and validation"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_employee_id_consistency(self, populated_test_db: EmployeeCollections):
        """Test that employee_id is consistent across all collections"""
        all_employee_ids = await populated_test_db.get_all_employee_ids()
        
        for emp_id in all_employee_ids:
            # Check that employee exists in all main collections
            personal = await populated_test_db.get_employee_personal_info(emp_id)
            employment = await populated_test_db.get_employee_employment_info(emp_id)
            
            # Personal and employment should always exist
            assert personal is not None, f"Missing personal info for {emp_id}"
            assert employment is not None, f"Missing employment info for {emp_id}"
            
            # Verify employee_id consistency
            assert personal["employee_id"] == emp_id
            assert employment["employee_id"] == emp_id
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_required_fields_validation(self, employee_collections: EmployeeCollections):
        """Test that required fields are validated"""
        # Test missing employee_id
        invalid_data = {
            "full_name": "Test User",
            "email": "test@company.com"
            # Missing employee_id
        }
        
        # This should still work but we should be able to detect missing required fields
        await employee_collections.mongodb_client.insert_document("personal_info", invalid_data)
        
        # Test retrieval with None employee_id
        result = await employee_collections.get_employee_personal_info(None)
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_data_types_validation(self, employee_collections: EmployeeCollections):
        """Test data type validation"""
        # Insert data with correct types
        valid_data = {
            "employee_id": "EMP123",
            "age": 30,  # Should be integer
            "total_experience_years": 5.5,  # Should be float
            "performance_rating": 4,  # Should be integer
            "created_at": datetime.utcnow().isoformat()  # Should be string (ISO format)
        }
        
        await employee_collections.mongodb_client.insert_document("test_validation", valid_data)
        
        # Retrieve and verify types are preserved
        retrieved = await employee_collections.mongodb_client.find_document(
            "test_validation", 
            {"employee_id": "EMP123"}
        )
        
        assert isinstance(retrieved["age"], int)
        assert isinstance(retrieved["total_experience_years"], float)
        assert isinstance(retrieved["performance_rating"], int)
        assert isinstance(retrieved["created_at"], str)
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_duplicate_handling(self, employee_collections: EmployeeCollections):
        """Test handling of duplicate employee records"""
        employee_data = {
            "employee_id": "EMP999",
            "full_name": "Duplicate Test",
            "email": "duplicate@company.com"
        }
        
        # Insert first record
        result1 = await employee_collections.mongodb_client.insert_document("personal_info", employee_data)
        assert result1 is not None
        
        # Insert duplicate record (should succeed but create duplicate)
        result2 = await employee_collections.mongodb_client.insert_document("personal_info", employee_data)
        assert result2 is not None
        
        # Check that we have duplicates
        duplicates = await employee_collections.mongodb_client.find_documents(
            "personal_info", 
            {"employee_id": "EMP999"}
        )
        assert len(duplicates) == 2


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_connection_error_handling(self):
        """Test handling of connection errors"""
        # Create client with invalid connection string
        invalid_client = MongoDBClient()
        invalid_client._client = None
        
        # Test operations with no connection
        result = await invalid_client.find_document("test", {})
        assert result is None
        
        collections = await invalid_client.get_collections()
        assert collections == []
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_invalid_collection_operations(self, test_mongodb_client: MongoDBClient):
        """Test operations on invalid collections"""
        # Test operations with empty collection name
        result = await test_mongodb_client.find_document("", {})
        assert result is None
        
        # Test with None collection name
        result = await test_mongodb_client.insert_document(None, {"test": "data"})
        assert result is None
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_invalid_query_filters(self, test_mongodb_client: MongoDBClient):
        """Test handling of invalid query filters"""
        # Insert test data
        await test_mongodb_client.insert_document("test_collection", {"valid": "data"})
        
        # Test with None filter
        result = await test_mongodb_client.find_document("test_collection", None)
        assert result is not None  # Should return first document
        
        # Test with empty filter
        results = await test_mongodb_client.find_documents("test_collection", {})
        assert len(results) >= 1
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_large_document_handling(self, test_mongodb_client: MongoDBClient):
        """Test handling of large documents"""
        # Create a large document (but within MongoDB limits)
        large_text = "x" * 10000  # 10KB text
        large_doc = {
            "employee_id": "EMP_LARGE",
            "large_field": large_text,
            "metadata": {"size": len(large_text)}
        }
        
        # Insert large document
        result = await test_mongodb_client.insert_document("test_collection", large_doc)
        assert result is not None
        
        # Retrieve and verify
        retrieved = await test_mongodb_client.find_document("test_collection", {"employee_id": "EMP_LARGE"})
        assert retrieved is not None
        assert len(retrieved["large_field"]) == 10000


class TestPerformance:
    """Test database performance characteristics"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    @pytest.mark.slow
    async def test_bulk_operations_performance(self, test_mongodb_client: MongoDBClient, performance_tracker):
        """Test performance of bulk operations"""
        # Generate bulk test data
        bulk_data = [
            {"batch_id": "performance_test", "index": i, "data": f"test_data_{i}"}
            for i in range(1000)
        ]
        
        # Test bulk insertion performance
        performance_tracker.start()
        doc_ids = await test_mongodb_client.insert_documents("performance_test", bulk_data)
        insert_time = performance_tracker.stop("bulk_insert")
        
        assert len(doc_ids) == 1000
        assert insert_time < 10.0  # Should complete within 10 seconds
        
        # Test bulk retrieval performance
        performance_tracker.start()
        retrieved_docs = await test_mongodb_client.find_documents("performance_test", {"batch_id": "performance_test"})
        retrieval_time = performance_tracker.stop("bulk_retrieval")
        
        assert len(retrieved_docs) == 1000
        assert retrieval_time < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_concurrent_operations(self, test_mongodb_client: MongoDBClient):
        """Test concurrent database operations"""
        async def insert_worker(worker_id: int):
            """Worker function for concurrent inserts"""
            docs = [
                {"worker_id": worker_id, "doc_index": i, "timestamp": datetime.utcnow().isoformat()}
                for i in range(10)
            ]
            return await test_mongodb_client.insert_documents("concurrent_test", docs)
        
        # Run concurrent workers
        tasks = [insert_worker(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all workers completed successfully
        assert len(results) == 5
        for result in results:
            assert not isinstance(result, Exception)
            assert len(result) == 10
        
        # Verify total documents inserted
        total_docs = await test_mongodb_client.count_documents("concurrent_test", {})
        assert total_docs == 50  # 5 workers × 10 docs each
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_query_optimization(self, populated_test_db: EmployeeCollections, performance_tracker):
        """Test query optimization and indexing effects"""
        # Test query performance on employee_id (should be fast with index)
        performance_tracker.start()
        
        for _ in range(100):
            await populated_test_db.get_employee_personal_info("EMP001")
        
        indexed_query_time = performance_tracker.stop("indexed_queries")
        
        # Indexed queries should be fast
        assert indexed_query_time < 2.0  # 100 queries in under 2 seconds
        
        # Test aggregation performance
        performance_tracker.start()
        await populated_test_db.get_department_statistics()
        aggregation_time = performance_tracker.stop("aggregation")
        
        assert aggregation_time < 1.0  # Aggregation should be fast on small dataset