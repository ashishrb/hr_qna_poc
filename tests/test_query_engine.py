# tests/test_query_engine.py
"""
Query Engine Tests

Purpose:
- Test query processing pipeline and intent detection
- Test entity extraction and query understanding
- Test search integration and result ranking
- Test response generation and natural language output
- Test error handling and edge cases
- Test performance and accuracy of query processing

Test Coverage:
- Intent detection for different query types
- Entity extraction (departments, roles, skills, locations)
- Search client integration and result processing
- OpenAI integration for response generation
- Query normalization and preprocessing
- Error handling for invalid queries
- Performance testing for query response times
"""

import pytest
import asyncio
from typing import Dict, List, Any
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Import components
from src.query.updated_query_engine import UpdatedHRQueryEngine, QueryType
from src.query.intent_detector import IntentDetector, intent_detector
from src.query.response_generator import ResponseGenerator, response_generator
from src.core.models import QueryEntities, SearchResult
from src.core.exceptions import IntentDetectionException, EntityExtractionException, ResponseGenerationException

class TestIntentDetection:
    """Test intent detection functionality"""
    
    def test_intent_detector_initialization(self):
        """Test intent detector initialization"""
        detector = IntentDetector()
        
        assert detector.intent_patterns is not None
        assert QueryType.EMPLOYEE_SEARCH in detector.intent_patterns
        assert QueryType.COUNT_QUERY in detector.intent_patterns
        assert QueryType.SKILL_SEARCH in detector.intent_patterns
        
        # Test that patterns are properly defined
        assert len(detector.intent_patterns[QueryType.COUNT_QUERY]) > 0
        assert "how many" in detector.intent_patterns[QueryType.COUNT_QUERY]
    
    @pytest.mark.parametrize("query,expected_intent", [
        ("How many employees work in IT?", QueryType.COUNT_QUERY),
        ("Count of developers", QueryType.COUNT_QUERY),
        ("Total employees with AWS certification", QueryType.COUNT_QUERY),
        ("Find employees with Python skills", QueryType.SKILL_SEARCH),
        ("Who has AWS certification?", QueryType.SKILL_SEARCH),
        ("Show me employees with PMP certification", QueryType.SKILL_SEARCH),
        ("Find developers in IT department", QueryType.EMPLOYEE_SEARCH),
        ("Show me managers", QueryType.EMPLOYEE_SEARCH),
        ("List employees in Operations", QueryType.EMPLOYEE_SEARCH),
        ("Tell me about the IT department", QueryType.DEPARTMENT_INFO),
        ("What is the Sales team like?", QueryType.DEPARTMENT_INFO),
    ])
    def test_detect_intent_patterns(self, query: str, expected_intent: QueryType):
        """Test intent detection for various query patterns"""
        detector = IntentDetector()
        detected_intent = detector.detect_intent(query)
        assert detected_intent == expected_intent
    
    def test_detect_intent_edge_cases(self):
        """Test intent detection edge cases"""
        detector = IntentDetector()
        
        # Empty query
        with pytest.raises(IntentDetectionException):
            detector.detect_intent("")
        
        # Very ambiguous query
        intent = detector.detect_intent("employee")
        assert intent == QueryType.GENERAL_INFO  # Should default to general info
        
        # Mixed intent query (should pick strongest signal)
        intent = detector.detect_intent("How many developers with AWS certification?")
        assert intent == QueryType.COUNT_QUERY  # Count should take precedence
    
    def test_extract_entities_departments(self):
        """Test department entity extraction"""
        detector = IntentDetector()
        
        test_cases = [
            ("Find employees in IT department", "IT"),
            ("Show me people from Sales", "Sales"),
            ("Operations team members", "Operations"),
            ("HR department staff", "HR"),
            ("Finance employees", "Finance")
        ]
        
        for query, expected_dept in test_cases:
            entities = detector.extract_entities(query)
            assert entities.department == expected_dept
    
    def test_extract_entities_roles(self):
        """Test role/position entity extraction"""
        detector = IntentDetector()
        
        test_cases = [
            ("Find developers", "Developer"),
            ("Show me managers", "Manager"),
            ("List all directors", "Director"),
            ("Analyst positions", "Analyst"),
            ("Engineering leads", "Lead")
        ]
        
        for query, expected_role in test_cases:
            entities = detector.extract_entities(query)
            assert entities.position == expected_role
    
    def test_extract_entities_skills(self):
        """Test skills and certification entity extraction"""
        detector = IntentDetector()
        
        test_cases = [
            ("Employees with Python skills", ["Python"]),
            ("Find AWS certified people", ["AWS"]),
            ("PMP certification holders", ["PMP"]),
            ("Java and SQL developers", ["Java", "SQL"]),
            ("Machine learning experts", ["Machine Learning"])
        ]
        
        for query, expected_skills in test_cases:
            entities = detector.extract_entities(query)
            for skill in expected_skills:
                assert skill in entities.skills
    
    def test_extract_entities_locations(self):
        """Test location entity extraction"""
        detector = IntentDetector()
        
        test_cases = [
            ("Remote employees", "Remote"),
            ("People in New York", "New York"),
            ("Offshore team members", "Offshore"),
            ("Onshore staff", "Onshore"),
            ("California office", "California")
        ]
        
        for query, expected_location in test_cases:
            entities = detector.extract_entities(query)
            assert entities.location == expected_location
    
    def test_extract_entities_employee_names(self):
        """Test employee name extraction"""
        detector = IntentDetector()
        
        test_cases = [
            ("Tell me about John Smith", "John Smith"),
            ("Find John Doe", "John Doe"),
            ("Who is Sarah Johnson", "Sarah Johnson")
        ]
        
        for query, expected_name in test_cases:
            entities = detector.extract_entities(query)
            assert entities.employee_name == expected_name
    
    def test_analyze_query_complexity(self):
        """Test query complexity analysis"""
        detector = IntentDetector()
        
        # Simple query
        simple_analysis = detector.analyze_query_complexity("Find developers")
        assert simple_analysis["word_count"] == 2
        assert simple_analysis["complexity_score"] > 0
        assert simple_analysis["has_entities"] is True
        
        # Complex query
        complex_analysis = detector.analyze_query_complexity(
            "Find senior developers with AWS certification in IT department who have 5+ years experience"
        )
        assert complex_analysis["word_count"] > 10
        assert complex_analysis["complexity_score"] > simple_analysis["complexity_score"]
        assert len(complex_analysis["entity_types"]) > 1
    
    def test_get_entity_suggestions(self):
        """Test entity suggestions functionality"""
        detector = IntentDetector()
        
        suggestions = detector.get_entity_suggestions("develop")
        
        assert "departments" in suggestions
        assert "locations" in suggestions
        assert "skills" in suggestions
        assert "positions" in suggestions
        
        # Should suggest related terms
        assert "Developer" in suggestions["positions"]


class TestQueryEngineCore:
    """Test core query engine functionality"""
    
    @pytest.mark.asyncio
    async def test_query_engine_initialization(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test query engine initialization"""
        assert mock_query_engine.openai_client is not None
        assert mock_query_engine.search_client is not None
    
    @pytest.mark.asyncio
    async def test_process_query_simple(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test processing simple queries"""
        query = "Find developers"
        
        result = await mock_query_engine.process_query(query)
        
        # Verify response structure
        assert "query" in result
        assert "intent" in result
        assert "entities" in result
        assert "search_results" in result
        assert "response" in result
        assert "status" in result
        
        assert result["query"] == query
        assert result["status"] == "success"
        assert isinstance(result["search_results"], list)
    
    @pytest.mark.asyncio
    async def test_process_query_count(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test processing count queries"""
        query = "How many employees in IT?"
        
        # Mock count response
        with patch.object(mock_query_engine, 'count_employees', return_value=25):
            result = await mock_query_engine.process_query(query)
        
        assert result["intent"] == "count_query"
        assert result["count"] == 25
        assert "25 employees" in result["response"]
    
    @pytest.mark.asyncio
    async def test_process_query_with_filters(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test processing queries with multiple filters"""
        query = "Find developers with AWS certification in IT department"
        
        result = await mock_query_engine.process_query(query)
        
        # Verify entity extraction
        entities = result["entities"]
        assert entities["department"] == "IT"
        assert entities["position"] == "Developer"
        assert "AWS" in entities["skills"]
    
    @pytest.mark.asyncio
    async def test_detect_intent_integration(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test intent detection integration"""
        test_queries = [
            ("How many developers?", "count_query"),
            ("Find Python developers", "skill_search"),
            ("Show me IT employees", "employee_search"),
            ("Tell me about Sales department", "department_info")
        ]
        
        for query, expected_intent in test_queries:
            intent, entities = mock_query_engine.detect_intent(query)
            assert intent.value == expected_intent
    
    def test_normalize_search_query(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test query normalization"""
        test_cases = [
            ("Find developers", "find developer"),
            ("Show me managers", "show me manager"),
            ("List directors", "list director"),
            ("Get analysts", "get analyst")
        ]
        
        for original, expected in test_cases:
            normalized = mock_query_engine.normalize_search_query(original)
            assert normalized == expected
    
    @pytest.mark.asyncio
    async def test_search_employees_integration(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test employee search integration"""
        query = "developers"
        filters = {"department": "IT"}
        
        results = await mock_query_engine.search_employees(query, filters, top_k=5)
        
        assert isinstance(results, list)
        # Mock should return at least one result
        if results:
            result = results[0]
            assert "id" in result
            assert "full_name" in result
            assert "department" in result
            assert "role" in result
    
    @pytest.mark.asyncio
    async def test_count_employees_integration(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test employee counting integration"""
        # Mock the search client count response
        mock_query_engine.search_client.search.return_value.__iter__ = lambda x: iter([])
        mock_query_engine.search_client.search.return_value.get_count.return_value = 15
        
        count = mock_query_engine.count_employees({"department": "IT"})
        
        assert isinstance(count, int)
        assert count >= 0


class TestResponseGeneration:
    """Test response generation functionality"""
    
    def test_response_generator_initialization(self):
        """Test response generator initialization"""
        generator = ResponseGenerator()
        assert generator.openai_client is not None
        assert generator.response_templates is not None
        assert generator.system_prompts is not None
    
    @pytest.mark.asyncio
    async def test_generate_count_response(self, mock_openai_client: MagicMock):
        """Test count query response generation"""
        generator = ResponseGenerator()
        generator.openai_client = mock_openai_client
        
        entities = QueryEntities(department="IT")
        response = generator._generate_count_response(entities, 25)
        
        assert "25 employees" in response
        assert "IT department" in response
    
    @pytest.mark.asyncio
    async def test_generate_no_results_response(self, mock_openai_client: MagicMock):
        """Test no results response generation"""
        generator = ResponseGenerator()
        generator.openai_client = mock_openai_client
        
        query = "Find employees with nonexistent skill"
        entities = QueryEntities(skills=["NonexistentSkill"])
        
        response = generator._generate_no_results_response(query, QueryType.SKILL_SEARCH, entities)
        
        assert "couldn't find" in response.lower()
        assert "nonexistentskill" in response.lower()
    
    def test_format_search_context(self):
        """Test search context formatting"""
        generator = ResponseGenerator()
        
        search_results = [
            SearchResult(
                id="emp_001",
                employee_id="EMP001",
                full_name="John Doe",
                department="IT",
                role="Developer",
                certifications="AWS, Python",
                score=0.95
            ),
            SearchResult(
                id="emp_002", 
                employee_id="EMP002",
                full_name="Jane Smith",
                department="IT",
                role="Senior Developer",
                certifications="GCP, Java",
                score=0.87
            )
        ]
        
        context = generator._format_search_context(search_results)
        
        assert "John Doe" in context
        assert "Jane Smith" in context
        assert "IT" in context
        assert "Developer" in context
        assert "AWS" in context
    
    def test_get_system_prompt(self):
        """Test system prompt selection"""
        generator = ResponseGenerator()
        
        # Test default prompt
        prompt = generator._get_system_prompt(QueryType.EMPLOYEE_SEARCH, False)
        assert "HR assistant" in prompt
        assert "professional" in prompt.lower()
        
        # Test sensitive data prompt
        sensitive_prompt = generator._get_system_prompt(QueryType.EMPLOYEE_SEARCH, True)
        assert "sensitive" in sensitive_prompt.lower()
        assert "salary" in sensitive_prompt.lower()
    
    def test_format_employee_details(self):
        """Test employee details formatting"""
        generator = ResponseGenerator()
        
        employee = SearchResult(
            id="emp_001",
            employee_id="EMP001", 
            full_name="John Doe",
            department="IT",
            role="Developer",
            location="New York",
            certifications="AWS, Python",
            current_project="Cloud Migration",
            total_experience_years=5.5,
            performance_rating=4
        )
        
        details = generator.format_employee_details(employee, include_sensitive_data=False)
        
        assert "**John Doe**" in details
        assert "Department: IT" in details
        assert "Role: Developer" in details
        assert "AWS, Python" in details
        assert "performance" not in details.lower()  # Sensitive data excluded
        
        # Test with sensitive data
        sensitive_details = generator.format_employee_details(employee, include_sensitive_data=True)
        assert "Performance Rating: 4" in sensitive_details


class TestSearchIntegration:
    """Test search service integration"""
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test semantic search functionality"""
        query = "software engineering expert"
        
        # Mock embedding generation
        with patch.object(mock_query_engine, 'generate_embedding', return_value=[0.1] * 1536):
            results = mock_query_engine.semantic_search(query, top_k=3)
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test hybrid search functionality"""
        query = "experienced Python developer"
        
        # Mock embedding generation
        with patch.object(mock_query_engine, 'generate_embedding', return_value=[0.1] * 1536):
            results = mock_query_engine.hybrid_search(query, top_k=5)
        
        assert isinstance(results, list)
    
    def test_generate_embedding(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test embedding generation"""
        text = "Python developer with machine learning experience"
        
        embedding = mock_query_engine.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # Standard embedding size
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_embedding_empty_text(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test embedding generation with empty text"""
        embedding = mock_query_engine.generate_embedding("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(x == 0.0 for x in embedding)  # Should return zero vector


class TestErrorHandling:
    """Test error handling in query processing"""
    
    @pytest.mark.asyncio
    async def test_invalid_query_handling(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test handling of invalid queries"""
        invalid_queries = [
            "",  # Empty query
            "   ",  # Whitespace only
            "a",  # Single character
            "xyz" * 200,  # Very long query
        ]
        
        for query in invalid_queries:
            result = await mock_query_engine.process_query(query)
            
            if query.strip() == "":
                # Empty queries might be handled specially
                assert result["status"] in ["error", "success"]
            else:
                assert result["status"] == "success"  # Should handle gracefully
                assert "response" in result
    
    @pytest.mark.asyncio
    async def test_search_service_error_handling(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test handling of search service errors"""
        # Mock search client to raise exception
        mock_query_engine.search_client.search.side_effect = Exception("Search service unavailable")
        
        result = await mock_query_engine.process_query("Find developers")
        
        # Should handle gracefully and still return a response
        assert result["status"] == "error"
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_openai_service_error_handling(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test handling of OpenAI service errors"""
        # Mock OpenAI client to raise exception
        mock_query_engine.openai_client.chat.completions.create.side_effect = Exception("OpenAI unavailable")
        
        result = await mock_query_engine.process_query("Find developers")
        
        # Should handle gracefully
        assert result["status"] == "error"
        assert "error" in result
    
    def test_intent_detection_error_handling(self):
        """Test intent detection error handling"""
        detector = IntentDetector()
        
        # Test with None input
        with pytest.raises(IntentDetectionException):
            detector.detect_intent(None)
        
        # Test with invalid input type
        with pytest.raises(IntentDetectionException):
            detector.detect_intent(123)
    
    def test_entity_extraction_error_handling(self):
        """Test entity extraction error handling"""
        detector = IntentDetector()
        
        # Should handle gracefully even with problematic input
        try:
            entities = detector.extract_entities("query with special chars: @#$%^&*()")
            assert isinstance(entities, QueryEntities)
        except EntityExtractionException:
            # This is also acceptable
            pass


class TestPerformance:
    """Test query processing performance"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_query_processing_speed(self, mock_query_engine: UpdatedHRQueryEngine, performance_tracker):
        """Test query processing speed"""
        queries = [
            "Find developers",
            "How many employees in IT?",
            "Show me managers with PMP certification",
            "List employees in Operations department",
            "Find Python developers in New York"
        ]
        
        total_time = 0
        
        for query in queries:
            performance_tracker.start()
            result = await mock_query_engine.process_query(query)
            query_time = performance_tracker.stop(f"query_{query[:20]}")
            
            assert result["status"] == "success"
            assert query_time < 5.0  # Each query should complete within 5 seconds
            total_time += query_time
        
        # Average time per query should be reasonable
        avg_time = total_time / len(queries)
        assert avg_time < 2.0  # Average under 2 seconds per query
    
    @pytest.mark.asyncio
    async def test_concurrent_query_processing(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test concurrent query processing"""
        queries = [
            "Find developers",
            "Count employees in Sales",
            "Show me IT managers",
            "List Python developers",
            "Find remote employees"
        ]
        
        # Process queries concurrently
        tasks = [mock_query_engine.process_query(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All queries should complete successfully
        assert len(results) == len(queries)
        for result in results:
            assert not isinstance(result, Exception)
            assert result["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test handling of large result sets"""
        # Mock large result set
        large_results = [
            {
                "id": f"emp_{i:03d}",
                "full_name": f"Employee {i}",
                "department": "IT",
                "role": "Developer",
                "score": 0.8
            }
            for i in range(100)
        ]
        
        mock_query_engine.search_client.search.return_value = large_results
        
        result = await mock_query_engine.process_query("Find all developers")
        
        # Should handle large result sets efficiently
        assert result["status"] == "success"
        assert len(result["search_results"]) <= 50  # Should limit results
    
    def test_memory_usage_during_processing(self, mock_query_engine: UpdatedHRQueryEngine):
        """Test memory usage during query processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple queries
        for i in range(50):
            # Create query that might consume memory
            query = f"Find developers with experience level {i} and skills in multiple technologies"
            entities = intent_detector.extract_entities(query)
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal for query processing
        assert memory_increase < 10.0  # Less than 10MB increase


class TestAccuracy:
    """Test query processing accuracy"""
    
    def test_intent_detection_accuracy(self):
        """Test intent detection accuracy with known queries"""
        detector = IntentDetector()
        
        test_cases = [
            # Count queries
            ("How many developers do we have?", QueryType.COUNT_QUERY),
            ("Count of employees in IT", QueryType.COUNT_QUERY),
            ("Total staff in Sales department", QueryType.COUNT_QUERY),
            
            # Employee search queries
            ("Find software engineers", QueryType.EMPLOYEE_SEARCH),
            ("Show me project managers", QueryType.EMPLOYEE_SEARCH),
            ("List all analysts", QueryType.EMPLOYEE_SEARCH),
            
            # Skill-based queries
            ("Employees with Python certification", QueryType.SKILL_SEARCH),
            ("Who has AWS skills?", QueryType.SKILL_SEARCH),
            ("Find people with machine learning experience", QueryType.SKILL_SEARCH),
            
            # Department queries
            ("Tell me about the Engineering team", QueryType.DEPARTMENT_INFO),
            ("What's the Operations department like?", QueryType.DEPARTMENT_INFO)
        ]
        
        correct_predictions = 0
        
        for query, expected_intent in test_cases:
            detected_intent = detector.detect_intent(query)
            if detected_intent == expected_intent:
                correct_predictions += 1
        
        accuracy = correct_predictions / len(test_cases)
        assert accuracy >= 0.8  # Should achieve at least 80% accuracy
    
    def test_entity_extraction_accuracy(self):
        """Test entity extraction accuracy"""
        detector = IntentDetector()
        
        test_cases = [
            ("Find developers in IT department", {"department": "IT", "position": "Developer"}),
            ("Show me Python developers in New York", {"skills": ["Python"], "position": "Developer", "location": "New York"}),
            ("Count employees with AWS certification", {"skills": ["AWS"]}),
            ("List managers in Sales", {"position": "Manager", "department": "Sales"}),
        ]
        
        correct_extractions = 0
        total_entities = 0
        
        for query, expected_entities in test_cases:
            entities = detector.extract_entities(query)
            
            for entity_type, expected_value in expected_entities.items():
                total_entities += 1
                actual_value = getattr(entities, entity_type)
                
                if entity_type == "skills":
                    # For skills, check if all expected skills are found
                    if all(skill in actual_value for skill in expected_value):
                        correct_extractions += 1
                else:
                    if actual_value == expected_value:
                        correct_extractions += 1
        
        accuracy = correct_extractions / total_entities if total_entities > 0 else 0
        assert accuracy >= 0.7  # Should achieve at least 70% accuracy