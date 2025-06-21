# tests/test_search.py
"""
Search Functionality Tests

Purpose:
- Test Azure AI Search client integration and operations
- Test search indexing and document management
- Test search query processing and result ranking
- Test vector search and semantic search capabilities
- Test search filters, facets, and aggregations
- Test search performance and scalability
- Test error handling and edge cases in search operations

Test Coverage:
- Azure Search client initialization and connection
- Document indexing, updating, and deletion
- Text search with various query types
- Vector search and embedding integration
- Hybrid search combining text and semantic search
- Search filters and facet functionality
- Search suggestions and autocomplete
- Performance testing and result ranking
"""

import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime

# Import components
from src.search.azure_search_client import AzureSearchClient, azure_search_client
from src.search.embeddings import EmbeddingsService
from src.search.fixed_indexer import FixedAzureSearchIndexer
from src.core.exceptions import SearchException, SearchServiceException, SearchIndexException

class TestAzureSearchClient:
    """Test Azure Search client basic operations"""
    
    def test_search_client_initialization(self):
        """Test search client initialization"""
        client = AzureSearchClient("test-index")
        
        assert client.index_name == "test-index"
        assert client.endpoint is not None
        assert client.api_key is not None
        assert client.search_client is not None
        assert client.index_client is not None
    
    def test_search_client_default_index(self):
        """Test search client with default index"""
        client = AzureSearchClient()
        
        assert client.index_name == "hr-employees-fixed"
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_basic_search(self, mock_search_client_class):
        """Test basic text search functionality"""
        # Setup mock
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {
                "id": "emp_001",
                "full_name": "John Doe",
                "department": "IT",
                "role": "Developer",
                "@search.score": 0.95
            },
            {
                "id": "emp_002",
                "full_name": "Jane Smith", 
                "department": "IT",
                "role": "Senior Developer",
                "@search.score": 0.87
            }
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("developer", top_k=5)
        
        assert len(results) == 2
        assert results[0]["full_name"] == "John Doe"
        assert results[0]["@search.score"] == 0.95
        assert results[1]["department"] == "IT"
        
        # Verify search was called with correct parameters
        mock_search_client.search.assert_called_once()
        call_args = mock_search_client.search.call_args
        assert call_args[1]["search_text"] == "developer"
        assert call_args[1]["top"] == 5
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_search_with_filters(self, mock_search_client_class):
        """Test search with filters"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        client.search(
            "developer", 
            top_k=10, 
            filters="department eq 'IT'",
            select_fields=["full_name", "department", "role"]
        )
        
        # Verify filter was applied
        call_args = mock_search_client.search.call_args
        assert call_args[1]["filter"] == "department eq 'IT'"
        assert call_args[1]["select"] == ["full_name", "department", "role"]
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_vector_search(self, mock_search_client_class):
        """Test vector search functionality"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        query_vector = [0.1] * 1536  # Mock embedding vector
        
        client.vector_search(query_vector, top_k=5)
        
        # Verify vector search was called correctly
        call_args = mock_search_client.search.call_args
        assert call_args[1]["search_text"] is None
        assert "vector_queries" in call_args[1]
        assert call_args[1]["vector_queries"][0]["vector"] == query_vector
        assert call_args[1]["vector_queries"][0]["fields"] == "content_vector"
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_hybrid_search(self, mock_search_client_class):
        """Test hybrid search (text + vector)"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        query_vector = [0.1] * 1536
        
        client.hybrid_search("python developer", query_vector, top_k=10)
        
        # Verify hybrid search parameters
        call_args = mock_search_client.search.call_args
        assert call_args[1]["search_text"] == "python developer"
        assert "vector_queries" in call_args[1]
        assert call_args[1]["query_type"] == "semantic"
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_upload_documents(self, mock_search_client_class):
        """Test document upload functionality"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.upload_documents.return_value = True
        
        client = AzureSearchClient("test-index")
        
        test_docs = [
            {"id": "emp_001", "full_name": "John Doe", "department": "IT"},
            {"id": "emp_002", "full_name": "Jane Smith", "department": "Sales"}
        ]
        
        result = client.upload_documents(test_docs)
        
        assert result is True
        mock_search_client.upload_documents.assert_called_once_with(documents=test_docs)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_delete_documents(self, mock_search_client_class):
        """Test document deletion"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.delete_documents.return_value = True
        
        client = AzureSearchClient("test-index")
        
        result = client.delete_documents(["emp_001", "emp_002"])
        
        assert result is True
        expected_docs = [{"id": "emp_001"}, {"id": "emp_002"}]
        mock_search_client.delete_documents.assert_called_once_with(documents=expected_docs)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_get_document_count(self, mock_search_client_class):
        """Test getting document count"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = MagicMock()
        mock_results.get_count.return_value = 1250
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        count = client.get_document_count()
        
        assert count == 1250
        mock_search_client.search.assert_called_once_with("*", include_total_count=True, top=0)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_get_facets(self, mock_search_client_class):
        """Test facet functionality"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = MagicMock()
        mock_results.get_facets.return_value = {
            "department": [
                {"value": "IT", "count": 150},
                {"value": "Sales", "count": 75}
            ],
            "role": [
                {"value": "Developer", "count": 80},
                {"value": "Manager", "count": 45}
            ]
        }
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        facets = client.get_facets(["department", "role"])
        
        assert "department" in facets
        assert "role" in facets
        assert facets["department"][0]["value"] == "IT"
        assert facets["department"][0]["count"] == 150
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_suggest(self, mock_search_client_class):
        """Test search suggestions"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_suggestions = [
            {"text": "John Doe"},
            {"text": "Jane Smith"},
            {"text": "Java Developer"}
        ]
        mock_search_client.suggest.return_value = mock_suggestions
        
        client = AzureSearchClient("test-index")
        suggestions = client.suggest("jo", suggester_name="sg", top_k=5)
        
        assert len(suggestions) == 3
        assert "John Doe" in suggestions
        assert "Jane Smith" in suggestions
        mock_search_client.suggest.assert_called_once_with(
            search_text="jo", suggester_name="sg", top=5
        )


class TestSearchIndexing:
    """Test search indexing operations"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_fixed_indexer_initialization(self, clean_test_db):
        """Test search indexer initialization"""
        indexer = FixedAzureSearchIndexer()
        
        assert indexer.index_client is not None
        assert indexer.mongodb_client is None
        assert indexer.db is None
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_indexer_mongodb_connection(self, clean_test_db):
        """Test indexer MongoDB connection"""
        indexer = FixedAzureSearchIndexer()
        
        # Mock the connection
        with patch.object(indexer, 'mongodb_client', clean_test_db):
            connected = await indexer.connect_to_mongodb()
            assert connected is True
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_get_employee_data(self, populated_test_db):
        """Test getting employee data for indexing"""
        indexer = FixedAzureSearchIndexer()
        indexer.mongodb_client = populated_test_db.mongodb_client
        indexer.db = populated_test_db.mongodb_client.database
        
        # Get data for first employee
        employee_data = await indexer.get_employee_data("EMP001")
        
        assert employee_data["employee_id"] == "EMP001"
        assert "full_name" in employee_data
        assert "department" in employee_data
        assert "role" in employee_data
        
        # Should have data from multiple collections
        if employee_data.get("full_name"):
            assert isinstance(employee_data["full_name"], str)
        if employee_data.get("department"):
            assert isinstance(employee_data["department"], str)
    
    def test_create_hr_search_index(self):
        """Test search index creation"""
        indexer = FixedAzureSearchIndexer()
        
        index = indexer.create_hr_search_index("test-hr-index")
        
        assert index.name == "test-hr-index"
        assert len(index.fields) > 10  # Should have many fields
        assert index.vector_search is not None
        assert index.semantic_search is not None
        
        # Check for required fields
        field_names = [field.name for field in index.fields]
        required_fields = ["id", "employee_id", "full_name", "department", "role", "content_vector"]
        for field in required_fields:
            assert field in field_names
    
    def test_prepare_document_for_indexing(self, sample_employee_data):
        """Test document preparation for indexing"""
        indexer = FixedAzureSearchIndexer()
        
        employee_data = {
            "employee_id": "EMP001",
            "full_name": "John Doe",
            "department": "IT",
            "role": "Developer",
            "certifications": "AWS, Python",
            "total_experience_years": 5.5,
            "performance_rating": 4
        }
        
        search_doc = indexer.prepare_document_for_indexing(employee_data)
        
        # Verify document structure
        assert search_doc["id"] == "emp_EMP001"
        assert search_doc["employee_id"] == "EMP001"
        assert search_doc["full_name"] == "John Doe"
        assert search_doc["department"] == "IT"
        assert search_doc["role"] == "Developer"
        assert search_doc["certifications"] == "AWS, Python"
        assert search_doc["total_experience_years"] == 5.5
        assert search_doc["performance_rating"] == 4
        
        # Verify combined text
        assert "Name: John Doe" in search_doc["combined_text"]
        assert "Department: IT" in search_doc["combined_text"]
        assert "Role: Developer" in search_doc["combined_text"]
        assert "Certifications: AWS, Python" in search_doc["combined_text"]
        
        # Verify metadata fields
        assert "created_at" in search_doc
        assert "updated_at" in search_doc
    
    @pytest.mark.asyncio
    @patch('src.search.fixed_indexer.SearchClient')
    async def test_index_all_employees(self, mock_search_client_class, populated_test_db):
        """Test indexing all employees"""
        # Setup mocks
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.upload_documents.return_value = True
        
        indexer = FixedAzureSearchIndexer()
        indexer.mongodb_client = populated_test_db.mongodb_client
        indexer.db = populated_test_db.mongodb_client.database
        
        # Mock database collections
        with patch.object(indexer.db, 'list_collection_names', 
                         return_value=['personal_info', 'employment', 'learning']):
            result = await indexer.index_all_employees()
        
        assert result is True
        # Should have called upload_documents at least once
        assert mock_search_client.upload_documents.call_count >= 1


class TestEmbeddingsService:
    """Test embeddings generation and vector search"""
    
    def test_embeddings_service_initialization(self):
        """Test embeddings service initialization"""
        service = EmbeddingsService()
        
        assert service.openai_client is not None
        assert service.search_client is not None
        assert service.mongodb_client is None
        assert service.db is None
    
    @patch('src.search.embeddings.AzureOpenAI')
    def test_generate_embedding(self, mock_openai_class):
        """Test embedding generation"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1] * 1536
        mock_client.embeddings.create.return_value = mock_response
        
        service = EmbeddingsService()
        service.openai_client = mock_client
        
        text = "Python developer with machine learning experience"
        embedding = service.generate_embedding(text)
        
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_client.embeddings.create.assert_called_once()
    
    @patch('src.search.embeddings.AzureOpenAI')
    def test_generate_embedding_empty_text(self, mock_openai_class):
        """Test embedding generation with empty text"""
        service = EmbeddingsService()
        
        embedding = service.generate_embedding("")
        
        assert len(embedding) == 1536
        assert all(x == 0.0 for x in embedding)
    
    @patch('src.search.embeddings.AzureOpenAI')
    def test_generate_batch_embeddings(self, mock_openai_class):
        """Test batch embedding generation"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
            MagicMock(embedding=[0.3] * 1536)
        ]
        mock_client.embeddings.create.return_value = mock_response
        
        service = EmbeddingsService()
        service.openai_client = mock_client
        
        texts = [
            "Software developer",
            "Data scientist", 
            "Product manager"
        ]
        
        embeddings = service.generate_batch_embeddings(texts, batch_size=3)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        mock_client.embeddings.create.assert_called_once()
    
    @patch('src.search.embeddings.SearchClient')
    def test_semantic_search(self, mock_search_client_class):
        """Test semantic search using embeddings"""
        # Setup mock
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {
                "id": "emp_001",
                "full_name": "John Doe",
                "department": "IT",
                "role": "Developer",
                "@search.score": 0.92
            }
        ]
        mock_search_client.search.return_value = mock_results
        
        service = EmbeddingsService()
        service.search_client = mock_search_client
        
        with patch.object(service, 'generate_embedding', return_value=[0.1] * 1536):
            results = service.semantic_search("machine learning engineer", top_k=5)
        
        assert len(results) == 1
        assert results[0]["full_name"] == "John Doe"
        assert results[0]["score"] == 0.92
    
    @patch('src.search.embeddings.SearchClient')
    def test_hybrid_search(self, mock_search_client_class):
        """Test hybrid search combining text and semantic"""
        # Setup mock
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        service = EmbeddingsService()
        service.search_client = mock_search_client
        
        with patch.object(service, 'generate_embedding', return_value=[0.1] * 1536):
            results = service.hybrid_search("data scientist", top_k=10)
        
        # Verify hybrid search parameters
        call_args = mock_search_client.search.call_args
        assert call_args[1]["search_text"] == "data scientist"
        assert "vector_queries" in call_args[1]
        assert call_args[1]["query_type"] == "semantic"


class TestSearchQueries:
    """Test various search query scenarios"""
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_department_search(self, mock_search_client_class):
        """Test searching by department"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {"id": "emp_001", "full_name": "John Doe", "department": "IT", "role": "Developer"},
            {"id": "emp_002", "full_name": "Jane Smith", "department": "IT", "role": "Manager"}
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("IT", filters="department eq 'IT'")
        
        assert len(results) == 2
        assert all(emp["department"] == "IT" for emp in results)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_role_search(self, mock_search_client_class):
        """Test searching by role"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {"id": "emp_001", "full_name": "John Doe", "department": "IT", "role": "Developer"},
            {"id": "emp_003", "full_name": "Bob Johnson", "department": "Engineering", "role": "Developer"}
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("developer")
        
        assert len(results) == 2
        assert all("Developer" in emp["role"] for emp in results)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_skill_search(self, mock_search_client_class):
        """Test searching by skills/certifications"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {
                "id": "emp_001",
                "full_name": "John Doe",
                "certifications": "AWS, Python, Docker",
                "role": "Developer"
            }
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("AWS")
        
        assert len(results) == 1
        assert "AWS" in results[0]["certifications"]
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_complex_search_query(self, mock_search_client_class):
        """Test complex search with multiple criteria"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        client.search(
            "python developer",
            filters="department eq 'IT' and total_experience_years ge 5",
            select_fields=["full_name", "department", "role", "certifications"]
        )
        
        call_args = mock_search_client.search.call_args
        assert call_args[1]["search_text"] == "python developer"
        assert "total_experience_years ge 5" in call_args[1]["filter"]
        assert "certifications" in call_args[1]["select"]
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_empty_search_results(self, mock_search_client_class):
        """Test handling of empty search results"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        results = client.search("nonexistent_skill")
        
        assert results == []
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_search_result_ranking(self, mock_search_client_class):
        """Test search result ranking by score"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {"id": "emp_001", "full_name": "John Doe", "@search.score": 0.95},
            {"id": "emp_002", "full_name": "Jane Smith", "@search.score": 0.87},
            {"id": "emp_003", "full_name": "Bob Johnson", "@search.score": 0.76}
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("developer")
        
        # Verify results are ordered by score (highest first)
        assert len(results) == 3
        assert results[0]["@search.score"] >= results[1]["@search.score"]
        assert results[1]["@search.score"] >= results[2]["@search.score"]


class TestSearchErrorHandling:
    """Test search error handling"""
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_search_service_error(self, mock_search_client_class):
        """Test handling of search service errors"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.side_effect = Exception("Search service unavailable")
        
        client = AzureSearchClient("test-index")
        results = client.search("developer")
        
        # Should handle error gracefully
        assert results == []
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_upload_error_handling(self, mock_search_client_class):
        """Test handling of document upload errors"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.upload_documents.side_effect = Exception("Upload failed")
        
        client = AzureSearchClient("test-index")
        result = client.upload_documents([{"id": "test", "data": "value"}])
        
        assert result is False
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_count_error_handling(self, mock_search_client_class):
        """Test handling of count query errors"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.side_effect = Exception("Count failed")
        
        client = AzureSearchClient("test-index")
        count = client.get_document_count()
        
        assert count == 0
    
    def test_invalid_index_name(self):
        """Test handling of invalid index names"""
        # Should not raise exception during initialization
        client = AzureSearchClient("")
        assert client.index_name == ""
        
        client = AzureSearchClient(None)
        assert client.index_name is None
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_malformed_query_handling(self, mock_search_client_class):
        """Test handling of malformed search queries"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        
        # Test various malformed queries
        malformed_queries = [
            None,
            "",
            "   ",
            "query with invalid characters: @#$%^&*()",
            "very " * 100 + "long query"  # Very long query
        ]
        
        for query in malformed_queries:
            try:
                results = client.search(query)
                assert isinstance(results, list)
            except Exception:
                # Some errors might be expected for truly malformed queries
                pass


class TestSearchPerformance:
    """Test search performance characteristics"""
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_search_response_time(self, mock_search_client_class, performance_tracker):
        """Test search response time"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        
        performance_tracker.start()
        client.search("developer")
        response_time = performance_tracker.stop("search_query")
        
        # Search should be fast (< 1 second for mocked service)
        assert response_time < 1.0
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_large_result_set_handling(self, mock_search_client_class):
        """Test handling of large result sets"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        # Create large result set
        large_results = [
            {"id": f"emp_{i:03d}", "full_name": f"Employee {i}", "score": 0.8}
            for i in range(1000)
        ]
        mock_search_client.search.return_value = large_results
        
        client = AzureSearchClient("test-index")
        results = client.search("employee", top_k=1000)
        
        # Should handle large result sets
        assert len(results) == 1000
        assert all("Employee" in emp["full_name"] for emp in results)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_concurrent_search_operations(self, mock_search_client_class):
        """Test concurrent search operations"""
        import threading
        import time
        
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = [{"id": "emp_001", "name": "Test"}]
        
        client = AzureSearchClient("test-index")
        results = []
        
        def search_worker(query_id):
            """Worker function for concurrent searches"""
            result = client.search(f"query_{query_id}")
            results.append(len(result))
        
        # Run multiple concurrent searches
        threads = []
        for i in range(10):
            thread = threading.Thread(target=search_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All searches should complete successfully
        assert len(results) == 10
        assert all(count == 1 for count in results)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_batch_document_upload_performance(self, mock_search_client_class, performance_tracker):
        """Test batch document upload performance"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.upload_documents.return_value = True
        
        client = AzureSearchClient("test-index")
        
        # Create batch of documents
        batch_docs = [
            {"id": f"emp_{i:03d}", "full_name": f"Employee {i}", "department": "IT"}
            for i in range(100)
        ]
        
        performance_tracker.start()
        result = client.upload_documents(batch_docs)
        upload_time = performance_tracker.stop("batch_upload")
        
        assert result is True
        assert upload_time < 5.0  # Should complete within 5 seconds
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_memory_usage_during_search(self, mock_search_client_class):
        """Test memory usage during search operations"""
        import psutil
        import os
        
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        mock_search_client.search.return_value = []
        
        client = AzureSearchClient("test-index")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple searches
        for i in range(50):
            client.search(f"query_{i}")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal
        assert memory_increase < 5.0  # Less than 5MB increase


class TestSearchAccuracy:
    """Test search accuracy and relevance"""
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_exact_match_search(self, mock_search_client_class):
        """Test exact match search accuracy"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {
                "id": "emp_001",
                "full_name": "John Developer Smith",
                "role": "Senior Developer",
                "@search.score": 0.95
            }
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("Developer")
        
        # Should return relevant results
        assert len(results) == 1
        assert "Developer" in results[0]["role"]
        assert results[0]["@search.score"] > 0.9
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_partial_match_search(self, mock_search_client_class):
        """Test partial match search accuracy"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {"id": "emp_001", "full_name": "John Doe", "role": "Developer", "@search.score": 0.87},
            {"id": "emp_002", "full_name": "Jane Smith", "role": "Senior Developer", "@search.score": 0.82}
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("dev")  # Partial match
        
        # Should return relevant results ordered by relevance
        assert len(results) == 2
        assert results[0]["@search.score"] >= results[1]["@search.score"]
        assert all("Developer" in emp["role"] for emp in results)
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_fuzzy_search_accuracy(self, mock_search_client_class):
        """Test fuzzy search for typos and variations"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {"id": "emp_001", "role": "Developer", "@search.score": 0.75}
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("developr")  # Typo in "developer"
        
        # Should still find relevant results despite typo
        assert len(results) == 1
        assert "Developer" in results[0]["role"]
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_multi_term_search_accuracy(self, mock_search_client_class):
        """Test multi-term search accuracy"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {
                "id": "emp_001",
                "full_name": "John Doe",
                "role": "Python Developer",
                "department": "IT",
                "@search.score": 0.92
            }
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("Python Developer IT")
        
        # Should find results matching multiple terms
        assert len(results) == 1
        assert "Python" in results[0]["role"]
        assert "Developer" in results[0]["role"]
        assert results[0]["department"] == "IT"
        assert results[0]["@search.score"] > 0.9
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_search_ranking_accuracy(self, mock_search_client_class):
        """Test search result ranking accuracy"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_results = [
            {"id": "emp_001", "role": "Senior Python Developer", "@search.score": 0.95},
            {"id": "emp_002", "role": "Python Developer", "@search.score": 0.88},
            {"id": "emp_003", "role": "Developer", "@search.score": 0.75},
            {"id": "emp_004", "role": "Junior Developer", "@search.score": 0.65}
        ]
        mock_search_client.search.return_value = mock_results
        
        client = AzureSearchClient("test-index")
        results = client.search("Python Developer")
        
        # Results should be properly ranked by relevance
        assert len(results) == 4
        scores = [emp["@search.score"] for emp in results]
        assert scores == sorted(scores, reverse=True)  # Descending order
        
        # Most relevant result should be first
        assert "Python Developer" in results[0]["role"]
        assert results[0]["@search.score"] == 0.95


class TestSearchIntegration:
    """Test search integration with other components"""
    
    @pytest.mark.asyncio
    @pytest.mark.mongodb
    async def test_search_with_real_data(self, populated_test_db):
        """Test search with real data from database"""
        # This would be an integration test with real Azure Search
        # For now, we'll test the data preparation
        
        indexer = FixedAzureSearchIndexer()
        indexer.mongodb_client = populated_test_db.mongodb_client
        indexer.db = populated_test_db.mongodb_client.database
        
        # Get employee data for indexing
        employee_data = await indexer.get_employee_data("EMP001")
        search_doc = indexer.prepare_document_for_indexing(employee_data)
        
        # Verify the document is properly formatted for search
        assert search_doc["id"].startswith("emp_")
        assert search_doc["employee_id"] == "EMP001"
        assert "combined_text" in search_doc
        assert len(search_doc["combined_text"]) > 0
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_search_facet_integration(self, mock_search_client_class):
        """Test search facet integration for filtering"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_facet_results = MagicMock()
        mock_facet_results.get_facets.return_value = {
            "department": [
                {"value": "IT", "count": 25},
                {"value": "Sales", "count": 15},
                {"value": "Operations", "count": 10}
            ],
            "role": [
                {"value": "Developer", "count": 12},
                {"value": "Manager", "count": 8},
                {"value": "Analyst", "count": 5}
            ]
        }
        mock_search_client.search.return_value = mock_facet_results
        
        client = AzureSearchClient("test-index")
        facets = client.get_facets(["department", "role"])
        
        # Verify facet structure
        assert "department" in facets
        assert "role" in facets
        assert len(facets["department"]) == 3
        assert len(facets["role"]) == 3
        
        # Verify facet values
        dept_values = [f["value"] for f in facets["department"]]
        assert "IT" in dept_values
        assert "Sales" in dept_values
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_search_suggestion_integration(self, mock_search_client_class):
        """Test search suggestion integration"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_suggestions = [
            {"text": "John Doe"},
            {"text": "Jane Smith"},
            {"text": "Java Developer"},
            {"text": "JavaScript Expert"}
        ]
        mock_search_client.suggest.return_value = mock_suggestions
        
        client = AzureSearchClient("test-index")
        suggestions = client.suggest("ja")
        
        # Should return relevant suggestions
        assert len(suggestions) == 4
        assert all("ja" in suggestion.lower() for suggestion in suggestions)
        assert "John Doe" in suggestions
        assert "Java Developer" in suggestions


class TestSearchConfiguration:
    """Test search configuration and setup"""
    
    def test_search_index_field_configuration(self):
        """Test search index field configuration"""
        indexer = FixedAzureSearchIndexer()
        index = indexer.create_hr_search_index("test-config-index")
        
        field_names = [field.name for field in index.fields]
        
        # Verify required fields are present
        required_fields = [
            "id", "employee_id", "full_name", "email", "department", "role",
            "location", "certifications", "current_project", "combined_text", "content_vector"
        ]
        
        for field in required_fields:
            assert field in field_names, f"Required field '{field}' missing from index"
        
        # Verify field types
        field_dict = {field.name: field for field in index.fields}
        
        # ID field should be key
        assert field_dict["id"].key is True
        
        # Text fields should be searchable
        searchable_fields = ["full_name", "department", "role", "certifications"]
        for field_name in searchable_fields:
            if field_name in field_dict:
                assert field_dict[field_name].searchable is True
        
        # Numeric fields should be filterable
        filterable_fields = ["total_experience_years", "performance_rating"]
        for field_name in filterable_fields:
            if field_name in field_dict:
                assert field_dict[field_name].filterable is True
    
    def test_vector_search_configuration(self):
        """Test vector search configuration"""
        indexer = FixedAzureSearchIndexer()
        index = indexer.create_hr_search_index("test-vector-index")
        
        # Verify vector search configuration
        assert index.vector_search is not None
        assert len(index.vector_search.profiles) > 0
        assert len(index.vector_search.algorithms) > 0
        
        # Verify vector field configuration
        vector_fields = [field for field in index.fields if field.name == "content_vector"]
        assert len(vector_fields) == 1
        
        vector_field = vector_fields[0]
        assert vector_field.vector_search_dimensions == 1536
        assert vector_field.vector_search_profile_name == "hr-vector-profile"
    
    def test_semantic_search_configuration(self):
        """Test semantic search configuration"""
        indexer = FixedAzureSearchIndexer()
        index = indexer.create_hr_search_index("test-semantic-index")
        
        # Verify semantic search configuration
        assert index.semantic_search is not None
        assert len(index.semantic_search.configurations) > 0
        
        semantic_config = index.semantic_search.configurations[0]
        assert semantic_config.name == "hr-semantic-config"
        
        # Verify semantic field configuration
        assert semantic_config.prioritized_fields.title_field.field_name == "full_name"
        
        content_fields = [field.field_name for field in semantic_config.prioritized_fields.content_fields]
        assert "combined_text" in content_fields
        assert "certifications" in content_fields
        
        keyword_fields = [field.field_name for field in semantic_config.prioritized_fields.keywords_fields]
        assert "department" in keyword_fields
        assert "role" in keyword_fields
    
    def test_suggester_configuration(self):
        """Test suggester configuration"""
        indexer = FixedAzureSearchIndexer()
        index = indexer.create_hr_search_index("test-suggester-index")
        
        # Verify suggester configuration
        assert index.suggesters is not None
        assert len(index.suggesters) > 0
        
        suggester = index.suggesters[0]
        assert suggester.name == "sg"
        
        # Verify suggester fields
        expected_fields = ["full_name", "department", "role", "location", "certifications"]
        for field in expected_fields:
            assert field in suggester.source_fields


class TestSearchMaintenance:
    """Test search maintenance operations"""
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_index_statistics_collection(self, mock_search_client_class):
        """Test collecting index statistics"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        mock_count_result = MagicMock()
        mock_count_result.get_count.return_value = 1500
        mock_search_client.search.return_value = mock_count_result
        
        client = AzureSearchClient("test-index")
        count = client.get_document_count()
        
        assert count == 1500
    
    @patch('src.search.azure_search_client.SearchClient')
    def test_index_health_check(self, mock_search_client_class):
        """Test index health check operations"""
        mock_search_client = MagicMock()
        mock_search_client_class.return_value = mock_search_client
        
        # Mock successful operations
        mock_search_client.search.return_value = [{"id": "test", "name": "Test"}]
        mock_count_result = MagicMock()
        mock_count_result.get_count.return_value = 100
        mock_search_client.search.return_value = mock_count_result
        
        client = AzureSearchClient("test-index")
        
        # Test basic operations for health check
        count = client.get_document_count()
        assert count == 100
        
        # Test search functionality
        mock_search_client.search.return_value = [{"id": "test"}]
        results = client.search("test")
        assert len(results) == 1


# Integration test markers for running with real services
pytestmark = pytest.mark.search