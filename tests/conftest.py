# tests/conftest.py
"""
Pytest Configuration and Shared Fixtures

Purpose:
- Configure pytest settings and test environment
- Provide shared fixtures for database connections, mock data, and test utilities
- Set up test isolation and cleanup mechanisms
- Create reusable test data and helper functions
- Configure async test support and logging

This file is automatically loaded by pytest and provides fixtures available to all test modules.
"""

import pytest
import asyncio
import os
import json
from typing import Dict, List, Any, AsyncGenerator, Generator
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil
from pathlib import Path

# Add parent directories to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import system components
from src.database.mongodb_client import MongoDBClient
from src.database.collections import EmployeeCollections
from src.query.updated_query_engine import UpdatedHRQueryEngine
from src.search.azure_search_client import AzureSearchClient
from src.processing.etl_pipeline import ETLPipeline
from src.core.config import settings

# Test configuration constants
TEST_DATABASE_NAME = "hr_qna_test"
TEST_INDEX_NAME = "hr-employees-test"
SAMPLE_EMPLOYEE_COUNT = 50

# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest settings"""
    # Add custom markers
    config.addinivalue_line("markers", "unit: Unit tests that don't require external services")
    config.addinivalue_line("markers", "integration: Integration tests that require external services")
    config.addinivalue_line("markers", "slow: Tests that take longer than 10 seconds")
    config.addinivalue_line("markers", "mongodb: Tests that require MongoDB connection")
    config.addinivalue_line("markers", "search: Tests that require Azure Search connection")
    config.addinivalue_line("markers", "openai: Tests that require Azure OpenAI connection")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add mongodb marker to tests with 'database' or 'mongo' in name
        if "database" in item.nodeid.lower() or "mongo" in item.nodeid.lower():
            item.add_marker(pytest.mark.mongodb)
        
        # Add search marker to tests with 'search' in name
        if "search" in item.nodeid.lower():
            item.add_marker(pytest.mark.search)
        
        # Add openai marker to tests with 'query' or 'response' in name
        if "query" in item.nodeid.lower() or "response" in item.nodeid.lower():
            item.add_marker(pytest.mark.openai)

# =============================================================================
# ASYNC TEST SUPPORT
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# =============================================================================
# CONFIGURATION FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration settings"""
    return {
        "database": {
            "test_db_name": TEST_DATABASE_NAME,
            "cleanup_after_tests": True,
            "use_mock_data": True
        },
        "search": {
            "test_index_name": TEST_INDEX_NAME,
            "cleanup_indexes": True
        },
        "ai": {
            "mock_responses": True,
            "test_timeout": 30
        },
        "performance": {
            "max_test_duration": 60,
            "max_memory_usage_mb": 1000
        }
    }

@pytest.fixture(scope="session")
def temp_directory() -> Generator[str, None, None]:
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp(prefix="hr_qna_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
async def test_mongodb_client() -> AsyncGenerator[MongoDBClient, None]:
    """Create test MongoDB client with test database"""
    # Override database name for testing
    original_db_name = settings.mongodb_database
    settings.mongodb_database = TEST_DATABASE_NAME
    
    client = MongoDBClient()
    await client.connect()
    
    yield client
    
    # Cleanup: Drop test database and restore settings
    if client.client:
        await client.client.drop_database(TEST_DATABASE_NAME)
        await client.disconnect()
    
    settings.mongodb_database = original_db_name

@pytest.fixture
async def clean_test_db(test_mongodb_client: MongoDBClient) -> AsyncGenerator[MongoDBClient, None]:
    """Provide clean test database for each test"""
    # Clean all collections before test
    if test_mongodb_client.database:
        collections = await test_mongodb_client.database.list_collection_names()
        for collection_name in collections:
            if not collection_name.startswith('system'):
                await test_mongodb_client.database[collection_name].delete_many({})
    
    yield test_mongodb_client
    
    # Clean up after test (optional, can be disabled for debugging)
    if test_mongodb_client.database:
        collections = await test_mongodb_client.database.list_collection_names()
        for collection_name in collections:
            if not collection_name.startswith('system'):
                await test_mongodb_client.database[collection_name].delete_many({})

@pytest.fixture
async def employee_collections(clean_test_db: MongoDBClient) -> EmployeeCollections:
    """Employee collections instance with clean test database"""
    collections = EmployeeCollections()
    # Override the mongodb_client to use test database
    collections.mongodb_client = clean_test_db
    return collections

# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_employee_data() -> Dict[str, Any]:
    """Single employee sample data"""
    return {
        "employee_id": "EMP001",
        "personal_info": {
            "employee_id": "EMP001",
            "full_name": "John Doe",
            "email": "john.doe@company.com",
            "age": 30,
            "gender": "Male",
            "location": "New York",
            "contact_number": "+1-555-0123",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        "employment": {
            "employee_id": "EMP001",
            "department": "IT",
            "role": "Developer",
            "grade_band": "L3",
            "employment_type": "Full-time",
            "work_mode": "Remote",
            "joining_date": "2023-01-15",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        "learning": {
            "employee_id": "EMP001",
            "certifications": "AWS, Python",
            "courses_completed": 8,
            "learning_hours_ytd": 40,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        "experience": {
            "employee_id": "EMP001",
            "total_experience_years": 5.5,
            "years_in_current_company": 2.0,
            "known_skills_count": 12,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        "performance": {
            "employee_id": "EMP001",
            "performance_rating": 4,
            "awards": "Employee of the Month",
            "improvement_areas": "Communication skills",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        "engagement": {
            "employee_id": "EMP001",
            "current_project": "Cloud Migration",
            "engagement_score": 8,
            "manager_feedback": "Excellent performer",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    }

@pytest.fixture
def sample_employees_data() -> List[Dict[str, Any]]:
    """Multiple employees sample data"""
    employees = []
    
    # Create diverse sample data
    departments = ["IT", "Sales", "Operations", "HR", "Finance"]
    roles = ["Developer", "Manager", "Analyst", "Director", "Lead"]
    locations = ["New York", "San Francisco", "Chicago", "Austin", "Remote"]
    certifications = ["AWS", "PMP", "GCP", "Azure", "Python", "Java", "SQL"]
    
    for i in range(10):
        emp_id = f"EMP{i+1:03d}"
        employee = {
            "employee_id": emp_id,
            "personal_info": {
                "employee_id": emp_id,
                "full_name": f"Test Employee {i+1}",
                "email": f"test.employee{i+1}@company.com",
                "age": 25 + (i % 15),
                "gender": ["Male", "Female", "Other"][i % 3],
                "location": locations[i % len(locations)],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            "employment": {
                "employee_id": emp_id,
                "department": departments[i % len(departments)],
                "role": roles[i % len(roles)],
                "employment_type": "Full-time",
                "work_mode": ["Remote", "Onsite", "Hybrid"][i % 3],
                "joining_date": f"202{2 + i%3}-0{1 + i%9}-01",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            "learning": {
                "employee_id": emp_id,
                "certifications": ", ".join(certifications[i:i+2] if i < len(certifications)-1 else certifications[:2]),
                "courses_completed": 3 + (i % 8),
                "learning_hours_ytd": 15 + (i % 25),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            "experience": {
                "employee_id": emp_id,
                "total_experience_years": 1.0 + (i % 10),
                "years_in_current_company": 0.5 + (i % 5),
                "known_skills_count": 5 + (i % 15),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            "performance": {
                "employee_id": emp_id,
                "performance_rating": 3 + (i % 3),  # Ratings 3-5
                "awards": "Recognition Award" if i % 3 == 0 else "",
                "improvement_areas": ["Communication", "Technical Skills", "Leadership"][i % 3],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            "engagement": {
                "employee_id": emp_id,
                "current_project": f"Project {chr(65 + i % 5)}",  # Projects A-E
                "engagement_score": 6 + (i % 5),  # Scores 6-10
                "manager_feedback": "Good performance" if i % 2 == 0 else "Needs improvement",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        }
        employees.append(employee)
    
    return employees

@pytest.fixture
async def populated_test_db(employee_collections: EmployeeCollections, sample_employees_data: List[Dict[str, Any]]) -> EmployeeCollections:
    """Test database populated with sample employee data"""
    
    # Insert sample data into each collection
    for employee in sample_employees_data:
        for collection_type, data in employee.items():
            if collection_type != "employee_id":
                collection_name = collection_type if collection_type != "personal_info" else "personal_info"
                await employee_collections.mongodb_client.insert_document(collection_name, data)
    
    return employee_collections

# =============================================================================
# SEARCH SERVICE FIXTURES
# =============================================================================

@pytest.fixture
def mock_search_client() -> MagicMock:
    """Mock Azure Search client for testing"""
    mock_client = MagicMock(spec=AzureSearchClient)
    
    # Configure common return values
    mock_client.search.return_value = [
        {
            "id": "emp_001",
            "full_name": "John Doe",
            "department": "IT",
            "role": "Developer",
            "score": 0.85
        }
    ]
    mock_client.get_document_count.return_value = 10
    mock_client.upload_documents.return_value = True
    
    return mock_client

@pytest.fixture
def mock_openai_client() -> MagicMock:
    """Mock Azure OpenAI client for testing"""
    mock_client = MagicMock()
    
    # Mock chat completion response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test response from the HR assistant."
    mock_client.chat.completions.create.return_value = mock_response
    
    # Mock embedding response
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock()]
    mock_embedding_response.data[0].embedding = [0.1] * 1536  # Standard embedding size
    mock_client.embeddings.create.return_value = mock_embedding_response
    
    return mock_client

# =============================================================================
# QUERY ENGINE FIXTURES
# =============================================================================

@pytest.fixture
def mock_query_engine(mock_search_client: MagicMock, mock_openai_client: MagicMock) -> UpdatedHRQueryEngine:
    """Query engine with mocked dependencies"""
    with patch('src.query.updated_query_engine.SearchClient') as mock_search, \
         patch('src.query.updated_query_engine.AzureOpenAI') as mock_openai:
        
        mock_search.return_value = mock_search_client
        mock_openai.return_value = mock_openai_client
        
        engine = UpdatedHRQueryEngine()
        return engine

# =============================================================================
# ETL PIPELINE FIXTURES
# =============================================================================

@pytest.fixture
def sample_excel_data() -> Dict[str, Any]:
    """Sample Excel data structure for ETL testing"""
    return {
        "Personal Info": [
            {"employee_id": "EMP001", "full_name": "John Doe", "email": "john@company.com"},
            {"employee_id": "EMP002", "full_name": "Jane Smith", "email": "jane@company.com"}
        ],
        "Employment": [
            {"employee_id": "EMP001", "department": "IT", "role": "Developer"},
            {"employee_id": "EMP002", "department": "Sales", "role": "Manager"}
        ]
    }

@pytest.fixture
def temp_excel_file(temp_directory: str, sample_excel_data: Dict[str, Any]) -> str:
    """Create temporary Excel file for testing"""
    import pandas as pd
    
    excel_path = os.path.join(temp_directory, "test_data.xlsx")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for sheet_name, data in sample_excel_data.items():
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return excel_path

@pytest.fixture
def mock_etl_pipeline(clean_test_db: MongoDBClient) -> ETLPipeline:
    """ETL pipeline with test database"""
    pipeline = ETLPipeline()
    pipeline.mongodb_client = clean_test_db
    return pipeline

# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def test_queries() -> Dict[str, List[str]]:
    """Sample test queries for different scenarios"""
    return {
        "simple": [
            "Who are the developers?",
            "Find employees in IT",
            "Show me managers"
        ],
        "complex": [
            "Find developers with AWS certification in IT department",
            "Show employees with 5+ years experience in Sales"
        ],
        "count": [
            "How many employees in IT?",
            "Count of developers"
        ],
        "invalid": [
            "",  # Empty query
            "xyz123nonexistent",  # Non-existent terms
        ]
    }

@pytest.fixture
def performance_tracker():
    """Utility for tracking test performance"""
    class PerformanceTracker:
        def __init__(self):
            self.start_time = None
            self.metrics = {}
        
        def start(self):
            self.start_time = datetime.utcnow()
        
        def stop(self, operation_name: str):
            if self.start_time:
                duration = (datetime.utcnow() - self.start_time).total_seconds()
                self.metrics[operation_name] = duration
                self.start_time = None
                return duration
            return 0
        
        def get_metrics(self) -> Dict[str, float]:
            return self.metrics.copy()
    
    return PerformanceTracker()

# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_environment():
    """Automatic cleanup after each test"""
    yield
    # Cleanup code runs after each test
    # Reset any global state, clear caches, etc.
    pass

# =============================================================================
# PARAMETRIZED FIXTURES
# =============================================================================

@pytest.fixture(params=["IT", "Sales", "Operations"])
def department_name(request) -> str:
    """Parametrized fixture for testing different departments"""
    return request.param

@pytest.fixture(params=["Developer", "Manager", "Analyst"])
def role_name(request) -> str:
    """Parametrized fixture for testing different roles"""
    return request.param

@pytest.fixture(params=[1, 5, 10])
def result_count(request) -> int:
    """Parametrized fixture for testing different result counts"""
    return request.param

# =============================================================================
# ASSERTION HELPERS
# =============================================================================

class TestHelpers:
    """Collection of helper functions for tests"""
    
    @staticmethod
    def assert_valid_employee_data(employee_data: Dict[str, Any]):
        """Assert that employee data has required fields"""
        assert "employee_id" in employee_data
        assert employee_data["employee_id"]
        assert isinstance(employee_data["employee_id"], str)
    
    @staticmethod
    def assert_valid_query_response(response: Dict[str, Any]):
        """Assert that query response has expected structure"""
        required_fields = ["query", "intent", "entities", "search_results", "response", "status"]
        for field in required_fields:
            assert field in response, f"Missing required field: {field}"
    
    @staticmethod
    def assert_search_results_valid(results: List[Dict[str, Any]]):
        """Assert that search results are properly formatted"""
        for result in results:
            assert "id" in result or "employee_id" in result
            assert "full_name" in result
    
    @staticmethod
    async def wait_for_async_operation(coro, timeout: float = 5.0):
        """Wait for async operation with timeout"""
        return await asyncio.wait_for(coro, timeout=timeout)

@pytest.fixture
def test_helpers() -> TestHelpers:
    """Test helper functions"""
    return TestHelpers()

# =============================================================================
# LOGGING CONFIGURATION FOR TESTS
# =============================================================================

@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configure logging for tests"""
    import logging
    
    # Set logging level for tests
    logging.getLogger("src").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.ERROR)
    logging.getLogger("motor").setLevel(logging.ERROR)
    
    yield
    
    # Reset logging after tests
    logging.getLogger("src").setLevel(logging.INFO) 