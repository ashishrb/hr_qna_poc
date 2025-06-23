# src/query/intelligent_query_engine.py
import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Validate and import external libraries
try:
    from openai import AzureOpenAI
except ImportError as e:
    print(f"❌ OpenAI library not found: {e}")
    print("💡 Install with: pip install openai")
    raise

try:
    from src.core.config import settings
except ImportError as e:
    print(f"❌ Config module not found: {e}")
    print("💡 Check if src/core/config.py exists")
    raise

try:
    from src.database.mongodb_client import mongodb_client
except ImportError as e:
    print(f"❌ MongoDB client not found: {e}")
    print("💡 Check if src/database/mongodb_client.py exists")
    raise

try:
    from src.search.azure_search_client import azure_search_client
except ImportError as e:
    print(f"❌ Azure Search client not found: {e}")
    print("💡 Check if src/search/azure_search_client.py exists")
    raise

# Try to import fallback engine - with graceful handling
try:
    from src.query.query_engine import HRQueryEngine
    FALLBACK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Fallback engine not found: {e}")
    print("💡 Check if src/query/query_engine.py exists")
    FALLBACK_AVAILABLE = False

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

class EnhancedIntelligentQueryEngine:
    """Enhanced intelligent query engine with P1 fixes and fallback mechanism"""
    
    def __init__(self):
        # Validate required settings
        required_settings = ['azure_openai_api_key', 'azure_openai_endpoint']
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                raise ValueError(f"❌ Missing required setting: {setting}")
        
        try:
            self.openai_client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version="2023-05-15",
                azure_endpoint=settings.azure_openai_endpoint
            )
        except Exception as e:
            raise ValueError(f"❌ Failed to initialize OpenAI client: {e}")
        
        # Initialize fallback engine if available
        if FALLBACK_AVAILABLE:
            try:
                self.fallback_engine = HRQueryEngine()
                print("✅ Fallback engine initialized")
            except Exception as e:
                print(f"⚠️ Fallback engine failed to initialize: {e}")
                self.fallback_engine = None
        else:
            self.fallback_engine = None
            print("⚠️ No fallback engine available")
        
        # Enhanced query patterns for better detection
        self.hr_domain_patterns = {
            "leave_queries": [
                "maximum leave", "max leave", "highest leave", "most leave",
                "leave days taken", "annual leave", "vacation days",
                "20 days", "30 days", "leave balance", "leave pattern"
            ],
            "performance_queries": [
                "high performing", "top performers", "performance rating",
                "best employees", "excellent", "outstanding"
            ],
            "attendance_queries": [
                "attendance", "absent", "present", "working days",
                "monthly attendance", "attendance percentage"
            ],
            "count_queries": [
                "how many", "count", "total", "number of", "quantity"
            ]
        }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Main query processing with enhanced error handling and fallback"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Step 1: Enhanced AI-powered intent and entity extraction
            intent = await self._extract_intent_and_entities_enhanced(query)
            
            # Step 2: Route to optimal data source with error handling
            result = await self._execute_query_with_fallback(query, intent)
            
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
            print(f"❌ IntelligentQueryEngine failed: {e}")
            # Fallback to simple engine if available
            if self.fallback_engine is not None:
                return await self._fallback_to_simple_engine(query, start_time)
            else:
                # Return error response if no fallback available
                return {
                    "query": query,
                    "intent": "unknown",
                    "entities": {},
                    "data_source": "none",
                    "results": [],
                    "count": 0,
                    "response": f"I apologize, but I encountered an error processing your query: {str(e)}",
                    "execution_time_ms": 0,
                    "confidence": 0.0,
                    "status": "error"
                }
    
    async def _extract_intent_and_entities_enhanced(self, query: str) -> QueryIntent:
        """Enhanced AI-powered intent detection with HR domain optimization"""
        
        # Enhanced system prompt optimized for HR domain
        system_prompt = """You are an expert HR data analyst specializing in employee queries. Extract intent and entities from HR queries with high precision.

        Query Types:
        - analytics: Counts, statistics, aggregations (how many, total, average, maximum, minimum)
        - text_search: Finding specific people by name or description  
        - complex_filter: Multi-criteria filtering and search
        - comparison: Comparing groups or departments
        - trend_analysis: Time-based analysis
        - recommendation: AI suggestions and insights

        Data Sources:
        - mongodb: For analytics, counts, aggregations, complex filtering, leave analysis
        - azure_search: For text search, semantic search, name lookup
        - hybrid: For queries needing both sources

        HR Domain Entities to Extract:
        - Basic: department, role, location, skills, employee_name
        - Leave & Attendance: leave_pattern, attendance_level, leave_threshold
        - Performance: performance_level, rating_range
        - Experience: experience_range, tenure_period
        - Numeric: leave_days, experience_years, age_range, salary_range
        - Temporal: date_range, time_period

        Special Leave Patterns:
        - "maximum leave" or "max leave" → leave_pattern: "maximum", aggregation_type: "count"
        - "20 days" or "30 days" → leave_threshold: number
        - "annual leave" → leave_type: "annual"
        - "high leave" → leave_pattern: "high"

        Return JSON format:
        {
            "query_type": "analytics|text_search|complex_filter|comparison|trend_analysis|recommendation",
            "data_source": "mongodb|azure_search|hybrid", 
            "confidence": 0.0-1.0,
            "entities": {
                "department": "string or null",
                "role": "string or null", 
                "skills": ["array of strings"],
                "leave_pattern": "maximum|minimum|high|low|average or null",
                "leave_threshold": number or null,
                "performance_level": "high|medium|low or null",
                "attendance_level": "high|medium|low or null",
                "experience_range": "junior|mid|senior or null",
                "aggregation_type": "count|average|sum|max|min or null",
                "sort_by": "string or null",
                "limit": number or null
            }
        }"""
        
        user_prompt = f"""
        Query: "{query}"
        
        Analyze this HR query and extract the intent and entities with focus on:
        1. Leave and attendance patterns
        2. Performance metrics
        3. Employee demographics
        4. Skills and certifications
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
            print(f"❌ Enhanced AI extraction failed: {e}")
            # Fallback to pattern-based detection
            return self._fallback_intent_detection(query)
    
    def _fallback_intent_detection(self, query: str) -> QueryIntent:
        """Enhanced pattern-based intent detection as fallback"""
        query_lower = query.lower()
        
        # Check for leave-related queries
        if any(pattern in query_lower for pattern in self.hr_domain_patterns["leave_queries"]):
            entities = {}
            
            # Extract leave patterns
            if any(word in query_lower for word in ["maximum", "max", "highest", "most"]):
                entities["leave_pattern"] = "maximum"
                entities["aggregation_type"] = "count"
            
            # Extract numeric thresholds
            if "20" in query_lower or "twenty" in query_lower:
                entities["leave_threshold"] = 20
            if "30" in query_lower or "thirty" in query_lower:
                entities["leave_threshold"] = 30
            
            return QueryIntent(
                query_type=QueryType.ANALYTICS,
                data_source=DataSource.MONGODB,
                confidence=0.8,
                extracted_entities=entities
            )
        
        # Check for count queries
        elif any(pattern in query_lower for pattern in self.hr_domain_patterns["count_queries"]):
            return QueryIntent(
                query_type=QueryType.ANALYTICS,
                data_source=DataSource.MONGODB,
                confidence=0.7,
                extracted_entities={"aggregation_type": "count"}
            )
        
        # Default to text search
        else:
            return QueryIntent(
                query_type=QueryType.TEXT_SEARCH,
                data_source=DataSource.AZURE_SEARCH,
                confidence=0.6,
                extracted_entities={}
            )
    
    async def _execute_query_with_fallback(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute query with error handling and fallback"""
        try:
            if intent.data_source == DataSource.MONGODB:
                return await self._execute_mongodb_query_enhanced(query, intent)
            elif intent.data_source == DataSource.AZURE_SEARCH:
                return await self._execute_azure_search_query(query, intent)
            else:  # HYBRID
                return await self._execute_hybrid_query(query, intent)
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            # Return empty result instead of crashing
            return QueryResult(
                data=[],
                count=0,
                metadata={"error": str(e)},
                source=intent.data_source,
                execution_time_ms=0
            )
    
    async def _execute_mongodb_query_enhanced(self, query: str, intent: QueryIntent) -> QueryResult:
        """Enhanced MongoDB execution with proper data type handling"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Connect to MongoDB
            await mongodb_client.connect()
            
            # Build enhanced aggregation pipeline
            pipeline = self._build_aggregation_pipeline_enhanced(intent)
            
            # Execute the pipeline
            if intent.query_type == QueryType.ANALYTICS:
                results = await self._execute_analytics_pipeline_enhanced(pipeline, intent)
            else:
                results = await self._execute_filter_pipeline_enhanced(pipeline, intent)
            
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return QueryResult(
                data=results.get("data", []),
                count=results.get("count", 0),
                metadata=results.get("metadata", {}),
                source=DataSource.MONGODB,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            print(f"❌ Enhanced MongoDB query failed: {e}")
            return QueryResult(data=[], count=0, metadata={"error": str(e)}, source=DataSource.MONGODB, execution_time_ms=0)
    
    def _build_aggregation_pipeline_enhanced(self, intent: QueryIntent) -> List[Dict[str, Any]]:
        """Enhanced MongoDB aggregation pipeline with proper data type handling"""
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
            }
        ])
        
        # Unwind arrays
        pipeline.extend([
            {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$attendance", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$engagement", "preserveNullAndEmptyArrays": True}}
        ])
        
        # CRITICAL FIX: Add field conversion for proper data type handling
        pipeline.append({
            "$addFields": {
                "attendance.leave_days_taken_num": {
                    "$toInt": {
                        "$ifNull": [
                            {"$toInt": "$attendance.leave_days_taken"}, 
                            0
                        ]
                    }
                },
                "performance.performance_rating_num": {
                    "$toInt": {
                        "$ifNull": [
                            {"$toInt": "$performance.performance_rating"}, 
                            0
                        ]
                    }
                }
            }
        })
        
        # Build match conditions based on entities
        match_conditions = {}
        
        if entities.get("department"):
            match_conditions["employment.department"] = entities["department"]
        
        if entities.get("role"):
            match_conditions["employment.role"] = entities["role"]
        
        if entities.get("performance_level"):
            if entities["performance_level"] == "high":
                match_conditions["performance.performance_rating_num"] = {"$gte": 4}
            elif entities["performance_level"] == "low":
                match_conditions["performance.performance_rating_num"] = {"$lte": 2}
        
        # ENHANCED: Handle leave pattern queries with proper thresholds
        if entities.get("leave_pattern"):
            if entities["leave_pattern"] == "maximum":
                # Find employees with very high leave (top 20% threshold)
                threshold = entities.get("leave_threshold", 20)  # Default to 20 days
                match_conditions["attendance.leave_days_taken_num"] = {"$gte": threshold}
            elif entities["leave_pattern"] == "minimum":
                match_conditions["attendance.leave_days_taken_num"] = {"$lte": 5}
            elif entities["leave_pattern"] == "high":
                match_conditions["attendance.leave_days_taken_num"] = {"$gte": 15}
        
        # Handle specific leave thresholds
        if entities.get("leave_threshold"):
            threshold = entities["leave_threshold"]
            match_conditions["attendance.leave_days_taken_num"] = {"$gte": threshold}
        
        # Add match stage if we have conditions
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
                        "average": {"$avg": "$performance.performance_rating_num"}
                    }
                })
            elif entities.get("aggregation_type") == "max":
                pipeline.append({
                    "$group": {
                        "_id": None,
                        "maximum": {"$max": "$attendance.leave_days_taken_num"}
                    }
                })
            else:
                # Default count for analytics queries
                pipeline.append({"$count": "total"})
        else:
            # For complex filters, return actual documents
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "performance_rating": "$performance.performance_rating_num",
                    "leave_days_taken": "$attendance.leave_days_taken_num",
                    "engagement_score": "$engagement.engagement_score"
                }
            })
            
            if entities.get("limit"):
                pipeline.append({"$limit": entities["limit"]})
        
        return pipeline
    
    async def _execute_analytics_pipeline_enhanced(self, pipeline: List[Dict[str, Any]], intent: QueryIntent) -> Dict[str, Any]:
        """Enhanced analytics pipeline execution with better error handling"""
        try:
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            if results and "total" in results[0]:
                return {
                    "data": [],
                    "count": results[0]["total"],
                    "metadata": {"aggregation_type": "count", "pipeline_success": True}
                }
            elif results and "average" in results[0]:
                return {
                    "data": [],
                    "count": 1,
                    "metadata": {"average": results[0]["average"], "aggregation_type": "average"}
                }
            elif results and "maximum" in results[0]:
                return {
                    "data": [],
                    "count": 1,
                    "metadata": {"maximum": results[0]["maximum"], "aggregation_type": "maximum"}
                }
            else:
                return {"data": [], "count": 0, "metadata": {"pipeline_success": False}}
                
        except Exception as e:
            print(f"❌ Analytics pipeline failed: {e}")
            return {"data": [], "count": 0, "metadata": {"error": str(e)}}
    
    async def _execute_filter_pipeline_enhanced(self, pipeline: List[Dict[str, Any]], intent: QueryIntent) -> Dict[str, Any]:
        """Enhanced filtering pipeline that returns documents"""
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
            print(f"❌ Filter pipeline failed: {e}")
            return {"data": [], "count": 0, "metadata": {"error": str(e)}}
    
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
            print(f"❌ Azure Search query failed: {e}")
            return QueryResult(data=[], count=0, metadata={"error": str(e)}, source=DataSource.AZURE_SEARCH, execution_time_ms=0)
    
    async def _execute_hybrid_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute hybrid queries using both MongoDB and Azure Search"""
        # For now, route to MongoDB for analytics, Azure Search for text
        if intent.query_type == QueryType.ANALYTICS:
            return await self._execute_mongodb_query_enhanced(query, intent)
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
    
    async def _fallback_to_simple_engine(self, query: str, start_time: float) -> Dict[str, Any]:
        """Fallback to HRQueryEngine when IntelligentQueryEngine fails"""
        if self.fallback_engine is None:
            return {
                "query": query,
                "intent": "unknown", 
                "entities": {},
                "data_source": "none",
                "results": [],
                "count": 0,
                "response": "I apologize, but I cannot process your query due to system limitations.",
                "execution_time_ms": 0,
                "confidence": 0.0,
                "status": "error"
            }
        
        try:
            print("🔄 Falling back to HRQueryEngine...")
            result = await self.fallback_engine.process_query(query)
            
            # Convert HRQueryEngine response to IntelligentQueryEngine format
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            return {
                "query": result["query"],
                "intent": result["intent"],
                "entities": result["entities"],
                "data_source": "fallback_engine",
                "results": result.get("search_results", []),
                "count": result.get("count", len(result.get("search_results", []))),
                "response": result["response"],
                "execution_time_ms": execution_time,
                "confidence": 0.7,  # Medium confidence for fallback
                "status": "success_fallback"
            }
            
        except Exception as e:
            return {
                "query": query,
                "intent": "unknown",
                "entities": {},
                "data_source": "none",
                "results": [],
                "count": 0,
                "response": f"I apologize, but I encountered an error processing your query: {str(e)}",
                "execution_time_ms": 0,
                "confidence": 0.0,
                "status": "error"
            }

# Global instance with error handling
try:
    intelligent_query_engine = EnhancedIntelligentQueryEngine()
    print("✅ Intelligent Query Engine initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Intelligent Query Engine: {e}")
    intelligent_query_engine = None