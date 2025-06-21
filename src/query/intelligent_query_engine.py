# src/query/intelligent_query_engine.py
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from openai import AzureOpenAI
from dataclasses import dataclass
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings
from src.database.mongodb_client import mongodb_client
from src.search.azure_search_client import azure_search_client

class QueryType(Enum):
    ANALYTICS = "analytics"           # Counts, averages, aggregations
    TEXT_SEARCH = "text_search"       # Name search, semantic search
    COMPLEX_FILTER = "complex_filter" # Multi-criteria filtering
    COMPARISON = "comparison"         # Department vs department
    TREND_ANALYSIS = "trend_analysis" # Time-based analysis
    RECOMMENDATION = "recommendation" # AI suggestions

class DataSource(Enum):
    MONGODB = "mongodb"
    AZURE_SEARCH = "azure_search" 
    HYBRID = "hybrid"

@dataclass
class QueryIntent:
    query_type: QueryType
    data_source: DataSource
    confidence: float
    extracted_entities: Dict[str, Any]
    suggested_pipeline: Optional[Dict] = None

@dataclass
class QueryResult:
    data: List[Dict[str, Any]]
    count: int
    metadata: Dict[str, Any]
    source: DataSource
    execution_time_ms: float

class IntelligentQueryEngine:
    """State-of-the-art query engine with AI-powered routing and execution"""
    
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version="2023-05-15",
            azure_endpoint=settings.azure_openai_endpoint
        )
        
        # Query type classifiers
        self.query_patterns = {
            QueryType.ANALYTICS: [
                "how many", "count", "total", "average", "percentage", 
                "highest", "lowest", "most", "least", "top", "bottom"
            ],
            QueryType.TEXT_SEARCH: [
                "find employee named", "who is", "search for", "employee profile"
            ],
            QueryType.COMPLEX_FILTER: [
                "with", "and", "having", "where", "criteria", "conditions"
            ],
            QueryType.COMPARISON: [
                "compare", "vs", "versus", "difference between", "better than"
            ],
            QueryType.TREND_ANALYSIS: [
                "trend", "over time", "monthly", "yearly", "growth", "change"
            ]
        }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Main query processing with intelligent routing"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Step 1: AI-powered intent and entity extraction
            intent = await self._extract_intent_and_entities(query)
            
            # Step 2: Route to optimal data source
            result = await self._execute_query(query, intent)
            
            # Step 3: Generate intelligent response
            response = await self._generate_intelligent_response(query, intent, result)
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "query": query,
                "intent": intent.query_type.value,
                "entities": intent.extracted_entities,
                "data_source": intent.data_source.value,
                "results": result.data,
                "count": result.count,
                "response": response,
                "execution_time_ms": execution_time,
                "confidence": intent.confidence,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "query": query,
                "status": "error",
                "error": str(e),
                "response": "I encountered an error processing your query. Please try rephrasing or contact support."
            }
    
    async def _extract_intent_and_entities(self, query: str) -> QueryIntent:
        """AI-powered intent detection and entity extraction using GPT-4"""
        
        system_prompt = """You are an expert HR data analyst. Extract intent and entities from HR queries.

        Query Types:
        - analytics: Counts, averages, statistics, aggregations
        - text_search: Finding specific people by name or description  
        - complex_filter: Multi-criteria filtering and search
        - comparison: Comparing groups or departments
        - trend_analysis: Time-based analysis
        - recommendation: AI suggestions and insights

        Data Sources:
        - mongodb: For analytics, counts, aggregations, complex filtering
        - azure_search: For text search, semantic search, name lookup
        - hybrid: For queries needing both sources

        Extract ALL relevant entities including:
        - Basic: department, role, location, skills, employee_name
        - Advanced: work_mode, performance_level, leave_pattern, experience_range
        - Numeric: salary_range, experience_years, age_range
        - Temporal: date_range, tenure_period

        Return JSON format:
        {
            "query_type": "analytics|text_search|complex_filter|comparison|trend_analysis|recommendation",
            "data_source": "mongodb|azure_search|hybrid", 
            "confidence": 0.0-1.0,
            "entities": {
                "department": "string or null",
                "role": "string or null", 
                "skills": ["array of strings"],
                "work_mode": "Remote|Hybrid|Onsite or null",
                "performance_level": "high|medium|low or null",
                "leave_pattern": "maximum|minimum|average or null",
                "experience_range": "junior|mid|senior or null",
                "salary_range": {"min": number, "max": number} or null,
                "comparison_type": "department|role|performance or null",
                "aggregation_type": "count|average|sum|max|min or null",
                "sort_by": "string or null",
                "limit": number or null
            }
        }"""
        
        user_prompt = f"""
        Query: "{query}"
        
        Analyze this HR query and extract the intent and entities.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-llm",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            return QueryIntent(
                query_type=QueryType(analysis["query_type"]),
                data_source=DataSource(analysis["data_source"]),
                confidence=analysis["confidence"],
                extracted_entities=analysis["entities"]
            )
            
        except Exception as e:
            # Fallback to pattern-based detection
            return self._fallback_intent_detection(query)
    
    def _fallback_intent_detection(self, query: str) -> QueryIntent:
        """Fallback pattern-based intent detection"""
        query_lower = query.lower()
        
        # Simple pattern matching as fallback
        if any(pattern in query_lower for pattern in self.query_patterns[QueryType.ANALYTICS]):
            return QueryIntent(
                query_type=QueryType.ANALYTICS,
                data_source=DataSource.MONGODB,
                confidence=0.7,
                extracted_entities={}
            )
        else:
            return QueryIntent(
                query_type=QueryType.TEXT_SEARCH,
                data_source=DataSource.AZURE_SEARCH,
                confidence=0.6,
                extracted_entities={}
            )
    
    async def _execute_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute query using the optimal data source"""
        
        if intent.data_source == DataSource.MONGODB:
            return await self._execute_mongodb_query(query, intent)
        elif intent.data_source == DataSource.AZURE_SEARCH:
            return await self._execute_azure_search_query(query, intent)
        else:  # HYBRID
            return await self._execute_hybrid_query(query, intent)
    
    async def _execute_mongodb_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute analytics queries using MongoDB aggregation"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Connect to MongoDB
            await mongodb_client.connect()
            
            # Build aggregation pipeline based on intent
            pipeline = self._build_aggregation_pipeline(intent)
            
            # Execute the pipeline
            if intent.query_type == QueryType.ANALYTICS:
                results = await self._execute_analytics_pipeline(pipeline, intent)
            else:
                results = await self._execute_filter_pipeline(pipeline, intent)
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return QueryResult(
                data=results.get("data", []),
                count=results.get("count", 0),
                metadata=results.get("metadata", {}),
                source=DataSource.MONGODB,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            print(f"MongoDB query failed: {e}")
            return QueryResult(data=[], count=0, metadata={}, source=DataSource.MONGODB, execution_time_ms=0)
    
    def _build_aggregation_pipeline(self, intent: QueryIntent) -> List[Dict[str, Any]]:
        """Build MongoDB aggregation pipeline based on extracted entities"""
        pipeline = []
        entities = intent.extracted_entities
        
        # Start with lookup to combine collections
        pipeline.extend([
            {
                "$lookup": {
                    "from": "employment",
                    "localField": "employee_id", 
                    "foreignField": "employee_id",
                    "as": "employment"
                }
            },
            {
                "$lookup": {
                    "from": "performance", 
                    "localField": "employee_id",
                    "foreignField": "employee_id", 
                    "as": "performance"
                }
            },
            {
                "$lookup": {
                    "from": "attendance",
                    "localField": "employee_id",
                    "foreignField": "employee_id",
                    "as": "attendance" 
                }
            },
            {
                "$lookup": {
                    "from": "engagement",
                    "localField": "employee_id", 
                    "foreignField": "employee_id",
                    "as": "engagement"
                }
            },
            {
                "$lookup": {
                    "from": "learning",
                    "localField": "employee_id",
                    "foreignField": "employee_id", 
                    "as": "learning"
                }
            }
        ])
        
        # Unwind arrays
        pipeline.extend([
            {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$attendance", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$engagement", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$learning", "preserveNullAndEmptyArrays": True}}
        ])
        
        # Build match conditions based on entities
        match_conditions = {}
        
        if entities.get("department"):
            match_conditions["employment.department"] = entities["department"]
        
        if entities.get("role"):
            match_conditions["employment.role"] = entities["role"]
        
        if entities.get("work_mode"):
            match_conditions["employment.work_mode"] = entities["work_mode"]
        
        if entities.get("performance_level"):
            if entities["performance_level"] == "high":
                match_conditions["performance.performance_rating"] = {"$gte": 4}
            elif entities["performance_level"] == "low":
                match_conditions["performance.performance_rating"] = {"$lte": 2}
        
        if entities.get("leave_pattern"):
            if entities["leave_pattern"] == "maximum":
                match_conditions["attendance.leave_days_taken"] = {"$gte": 20}
            elif entities["leave_pattern"] == "minimum":
                match_conditions["attendance.leave_days_taken"] = {"$lte": 5}
        
        if entities.get("experience_range"):
            if entities["experience_range"] == "senior":
                match_conditions["experience.total_experience_years"] = {"$gte": 8}
            elif entities["experience_range"] == "junior":
                match_conditions["experience.total_experience_years"] = {"$lte": 3}
        
        if match_conditions:
            pipeline.append({"$match": match_conditions})
        
        # Add aggregation stage based on query type
        if intent.query_type == QueryType.ANALYTICS:
            if entities.get("aggregation_type") == "count":
                pipeline.append({"$count": "total"})
            elif entities.get("aggregation_type") == "average":
                pipeline.append({
                    "$group": {
                        "_id": None,
                        "average": {"$avg": "$performance.performance_rating"}
                    }
                })
            else:
                # Default count
                pipeline.append({"$count": "total"})
        else:
            # For complex filters, return actual documents
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "work_mode": "$employment.work_mode",
                    "performance_rating": "$performance.performance_rating",
                    "leave_days_taken": "$attendance.leave_days_taken",
                    "engagement_score": "$engagement.engagement_score"
                }
            })
            
            if entities.get("sort_by"):
                sort_field = entities["sort_by"]
                pipeline.append({"$sort": {sort_field: -1}})
            
            if entities.get("limit"):
                pipeline.append({"$limit": entities["limit"]})
        
        return pipeline
    
    async def _execute_analytics_pipeline(self, pipeline: List[Dict[str, Any]], intent: QueryIntent) -> Dict[str, Any]:
        """Execute analytics aggregation pipeline"""
        try:
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            if results and "total" in results[0]:
                return {
                    "data": [],
                    "count": results[0]["total"],
                    "metadata": {"aggregation_type": "count"}
                }
            elif results and "average" in results[0]:
                return {
                    "data": [],
                    "count": 1,
                    "metadata": {"average": results[0]["average"], "aggregation_type": "average"}
                }
            else:
                return {"data": [], "count": 0, "metadata": {}}
                
        except Exception as e:
            print(f"Analytics pipeline failed: {e}")
            return {"data": [], "count": 0, "metadata": {}}
    
    async def _execute_filter_pipeline(self, pipeline: List[Dict[str, Any]], intent: QueryIntent) -> Dict[str, Any]:
        """Execute filtering pipeline that returns documents"""
        try:
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=1000)  # Limit for performance
            
            return {
                "data": results,
                "count": len(results),
                "metadata": {"filter_type": "documents"}
            }
            
        except Exception as e:
            print(f"Filter pipeline failed: {e}")
            return {"data": [], "count": 0, "metadata": {}}
    
    async def _execute_azure_search_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute text search queries using Azure Search"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Use existing Azure Search client
            search_results = azure_search_client.search(query, top_k=10)
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return QueryResult(
                data=search_results,
                count=len(search_results),
                metadata={"search_type": "text"},
                source=DataSource.AZURE_SEARCH,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            print(f"Azure Search query failed: {e}")
            return QueryResult(data=[], count=0, metadata={}, source=DataSource.AZURE_SEARCH, execution_time_ms=0)
    
    async def _execute_hybrid_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute hybrid queries using both MongoDB and Azure Search"""
        # For now, route to MongoDB for analytics, Azure Search for text
        if intent.query_type == QueryType.ANALYTICS:
            return await self._execute_mongodb_query(query, intent)
        else:
            return await self._execute_azure_search_query(query, intent)
    
    async def _generate_intelligent_response(self, query: str, intent: QueryIntent, result: QueryResult) -> str:
        """Generate intelligent natural language response"""
        
        system_prompt = """You are an expert HR assistant. Generate natural, helpful responses to HR queries based on the data provided.

        Guidelines:
        - Be concise but informative
        - Use specific numbers and data points
        - Provide context when helpful
        - Format lists clearly
        - Suggest follow-up questions when appropriate
        - Be professional and helpful"""
        
        context = {
            "query": query,
            "intent": intent.query_type.value,
            "data_source": intent.data_source.value,
            "count": result.count,
            "has_data": len(result.data) > 0,
            "execution_time": result.execution_time_ms
        }
        
        if result.count > 0 and result.data:
            context["sample_data"] = result.data[:3]  # First 3 results
        
        if result.metadata:
            context["metadata"] = result.metadata
        
        user_prompt = f"""
        Query: "{query}"
        Context: {json.dumps(context, default=str)}
        
        Generate a natural language response to this HR query based on the results.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-llm",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback response
            if intent.query_type == QueryType.ANALYTICS:
                return f"Found {result.count} employees matching your criteria."
            else:
                return f"Here are {result.count} employees that match your search."

# Example usage and testing
async def main():
    """Test the intelligent query engine"""
    engine = IntelligentQueryEngine()
    
    test_queries = [
        "How many employees took maximum leave?",
        "Find employees working in hybrid mode",
        "Show me high-performing employees in Sales",
        "Count employees with GCP certification", 
        "Who works on multiple projects?",
        "Average performance rating by department",
        "Find employees named John",
        "Top 5 employees with most experience"
    ]
    
    print("🧠 Testing Intelligent Query Engine")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = await engine.process_query(query)
        print(f"💡 Intent: {result['intent']} | Source: {result['data_source']}")
        print(f"📊 Count: {result['count']} | Time: {result['execution_time_ms']:.1f}ms")
        print(f"💬 Response: {result['response']}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())