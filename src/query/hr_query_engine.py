# src/query/robust_hr_query_engine.py
"""
Robust 360° HR Query Engine - Handles ALL possible employee queries
Supports complex analytics, comparisons, rankings, and comprehensive employee data
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from openai import AzureOpenAI
    from src.core.config import settings
    from src.database.mongodb_client import mongodb_client
    from src.search.azure_search_client import azure_search_client
except ImportError as e:
    print(f"❌ Import error: {e}")
    raise

class QueryType(Enum):
    """Comprehensive query types for 360° HR analytics"""
    COUNT_QUERY = "count_query"                    # "How many employees..."
    EMPLOYEE_SEARCH = "employee_search"            # "Find employees..."
    SKILL_SEARCH = "skill_search"                  # "Who has AWS certification?"
    DEPARTMENT_INFO = "department_info"            # "Show me IT department"
    ANALYTICS = "analytics"                        # "Average salary", "Top performers"
    COMPARISON = "comparison"                      # "Compare IT vs Sales"
    RANKING = "ranking"                           # "Top 10", "Bottom 5"
    CORRELATION = "correlation"                   # "High performers with low engagement"
    RECOMMENDATION = "recommendation"             # "Who needs training?"
    TREND_ANALYSIS = "trend_analysis"            # "Who joined recently?"
    COMPLEX_FILTER = "complex_filter"            # Multiple criteria
    GENERAL_INFO = "general_info"                # General questions

class DataField(Enum):
    """All possible data fields for analysis"""
    # Personal
    AGE = "age"
    GENDER = "gender"
    LOCATION = "location"
    
    # Employment
    DEPARTMENT = "department"
    ROLE = "role"
    WORK_MODE = "work_mode"
    EMPLOYMENT_TYPE = "employment_type"
    JOINING_DATE = "joining_date"
    
    # Skills & Learning
    CERTIFICATIONS = "certifications"
    COURSES_COMPLETED = "courses_completed"
    LEARNING_HOURS = "learning_hours_ytd"
    
    # Experience
    TOTAL_EXPERIENCE = "total_experience_years"
    COMPANY_TENURE = "years_in_current_company"
    SKILLS_COUNT = "known_skills_count"
    
    # Performance
    PERFORMANCE_RATING = "performance_rating"
    AWARDS = "awards"
    KPI_MET = "kpis_met_pct"
    
    # Engagement
    CURRENT_PROJECT = "current_project"
    ENGAGEMENT_SCORE = "engagement_score"
    MANAGER_FEEDBACK = "manager_feedback"
    
    # Compensation
    SALARY = "current_salary"
    BONUS = "bonus"
    TOTAL_CTC = "total_ctc"
    
    # Attendance
    LEAVE_BALANCE = "leave_balance"
    LEAVE_TAKEN = "leave_days_taken"
    ATTENDANCE_PCT = "monthly_attendance_pct"
    
    # Attrition
    ATTRITION_RISK = "attrition_risk_score"
    EXIT_INTENT = "exit_intent_flag"

@dataclass
class QueryContext:
    """Rich query context with extracted information"""
    original_query: str
    intent: QueryType
    entities: Dict[str, Any]
    fields_to_analyze: List[DataField]
    comparison_groups: List[str]
    filters: Dict[str, Any]
    sorting: Dict[str, Any]
    aggregation_type: Optional[str]
    limit: Optional[int]

class RobustHRQueryEngine:
    """Robust 360° HR Query Engine supporting all employee data scenarios"""
    
    def __init__(self):
        """Initialize the comprehensive query engine with better error handling"""
        print("🚀 Initializing Robust 360° HR Query Engine...")
        
        # Initialize OpenAI client with detailed error handling
        self.openai_client = None
        self.model_name = None
        self.ai_available = False
        
        try:
            # Import with correct path handling
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            
            from src.core.config import settings
            
            # Validate required settings
            required_settings = ['azure_openai_api_key', 'azure_openai_endpoint']
            missing_settings = []
            
            for setting in required_settings:
                if not hasattr(settings, setting) or not getattr(settings, setting):
                    missing_settings.append(setting)
            
            if missing_settings:
                print(f"❌ Missing OpenAI settings: {missing_settings}")
                print("🔄 Will use fallback mode without AI")
            else:
                # Try to initialize OpenAI client
                from openai import AzureOpenAI
                
                self.openai_client = AzureOpenAI(
                    api_key=settings.azure_openai_api_key,
                    api_version="2023-05-15",
                    azure_endpoint=settings.azure_openai_endpoint
                )
                
                # Get model name
                self.model_name = getattr(settings, 'azure_openai_chat_deployment', 'gpt-4o-llm')
                print(f"✅ Model name set to: {self.model_name}")
                
                # Test the connection
                test_response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5,
                    temperature=0
                )
                
                self.ai_available = True
                print(f"✅ Azure OpenAI client initialized successfully with model: {self.model_name}")
                print("✅ OpenAI connection tested successfully")
                
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {e}")
            print(f"   Error details: {type(e).__name__}: {str(e)}")
            print("🔄 Continuing in fallback mode without AI")
            self.ai_available = False
        
        # Initialize other components regardless of OpenAI status
        self.departments = ["Sales", "IT", "Operations", "HR", "Finance", "Legal", "Engineering", "Marketing", "Support"]
        self.roles = ["Developer", "Manager", "Analyst", "Director", "Lead", "Engineer", "Consultant", "Specialist"]
        self.skills = ["PMP", "GCP", "AWS", "Azure", "Python", "Java", "JavaScript", "SQL", "Docker", "Kubernetes"]
        self.locations = ["Remote", "Onshore", "Offshore", "New York", "California", "India", "Chennai", "Hyderabad"]
        
        # Collection mappings for comprehensive data access
        self.collection_fields = {
            "personal_info": ["full_name", "age", "gender", "location", "email", "contact_number"],
            "employment": ["department", "role", "work_mode", "employment_type", "joining_date", "grade_band"],
            "learning": ["certifications", "courses_completed", "learning_hours_ytd", "internal_trainings"],
            "experience": ["total_experience_years", "years_in_current_company", "known_skills_count"],
            "performance": ["performance_rating", "awards", "kpis_met_pct", "improvement_areas"],
            "engagement": ["current_project", "engagement_score", "manager_feedback", "days_on_bench"],
            "compensation": ["current_salary", "bonus", "total_ctc", "currency"],
            "attendance": ["leave_balance", "leave_days_taken", "monthly_attendance_pct", "leave_pattern"],
            "attrition": ["attrition_risk_score", "exit_intent_flag", "retention_plan"]
        }
        
        status = "with AI features" if self.ai_available else "in fallback mode"
        print(f"✅ Robust 360° HR Query Engine ready {status}!")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main query processing pipeline for comprehensive HR analytics
        
        Args:
            query: Natural language query
            
        Returns:
            Complete query result with detailed analysis
        """
        start_time = time.time()
        
        try:
            print(f"\n🔍 Processing 360° query: '{query}'")
            
            # Step 1: Advanced query analysis using AI
            query_context = await self._analyze_query_with_ai(query)
            print(f"   🎯 Intent: {query_context.intent.value}")
            print(f"   📋 Fields to analyze: {[f.value for f in query_context.fields_to_analyze]}")
            print(f"   🔧 Filters: {query_context.filters}")
            
            # Step 2: Route to appropriate handler based on complexity
            if query_context.intent == QueryType.COMPARISON:
                results, count = await self._handle_comparison_query(query_context)
            elif query_context.intent == QueryType.RANKING:
                results, count = await self._handle_ranking_query(query_context)
            elif query_context.intent == QueryType.CORRELATION:
                results, count = await self._handle_correlation_query(query_context)
            elif query_context.intent == QueryType.RECOMMENDATION:
                results, count = await self._handle_recommendation_query(query_context)
            elif query_context.intent == QueryType.TREND_ANALYSIS:
                results, count = await self._handle_trend_query(query_context)
            elif query_context.intent == QueryType.COMPLEX_FILTER:
                results, count = await self._handle_complex_filter_query(query_context)
            elif query_context.intent == QueryType.COUNT_QUERY:
                results, count = await self._handle_count_query(query_context)
            elif query_context.intent == QueryType.ANALYTICS:
                results, count = await self._handle_analytics_query(query_context)
            else:
                results, count = await self._handle_search_query(query_context)
            
            # Step 3: Generate comprehensive response
            response = await self._generate_comprehensive_response(query_context, results, count)
            
            execution_time = (time.time() - start_time) * 1000
            
            print(f"   ✅ Found {count} results in {execution_time:.1f}ms")
            
            return {
                "query": query,
                "intent": query_context.intent.value,
                "entities": query_context.entities,
                "fields_analyzed": [f.value for f in query_context.fields_to_analyze],
                "results": results,
                "count": count,
                "response": response,
                "execution_time_ms": execution_time,
                "status": "success",
                "query_complexity": self._assess_complexity(query_context)
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Query processing failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            return {
                "query": query,
                "intent": "unknown",
                "entities": {},
                "fields_analyzed": [],
                "results": [],
                "count": 0,
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "execution_time_ms": execution_time,
                "status": "error",
                "error": error_msg
            }
    
    async def _analyze_query_with_ai(self, query: str) -> QueryContext:
        """
        Advanced AI-powered query analysis for comprehensive intent and entity detection
        
        Args:
            query: Natural language query
            
        Returns:
            Rich QueryContext with all extracted information
        """
        if not self.ai_available or not self.openai_client:
            print("   ⚠️ AI not available, using fallback")
        return self._fallback_query_analysis(query)
    
        try:
            # Enhanced system prompt for comprehensive analysis
            system_prompt = """You are an expert HR analytics specialist. Analyze queries about employee data comprehensively.

QUERY TYPES:
- count_query: "How many", "Count of", "Total number"
- comparison: "Compare X vs Y", "Difference between", "X versus Y"
- ranking: "Top 10", "Bottom 5", "Highest", "Lowest", "Best", "Worst"
- correlation: "High X with low Y", "Employees who have X and Y", complex relationships
- recommendation: "Who needs", "Suggest", "Should we", "Recommend"
- trend_analysis: "Recent", "Last 6 months", "New joiners", "Over time"
- complex_filter: Multiple criteria (department AND skills AND experience)
- analytics: Average, mean, median, statistics
- employee_search: Simple "Find" or "Show me"

DATA FIELDS:
- Personal: age, gender, location
- Employment: department, role, work_mode, employment_type, joining_date
- Skills: certifications, courses_completed, learning_hours_ytd
- Experience: total_experience_years, years_in_current_company, known_skills_count
- Performance: performance_rating, awards, kpis_met_pct
- Engagement: current_project, engagement_score, manager_feedback
- Compensation: current_salary, bonus, total_ctc
- Attendance: leave_balance, leave_days_taken, monthly_attendance_pct
- Attrition: attrition_risk_score, exit_intent_flag

COMPARISON GROUPS:
Detect what to compare: departments, roles, locations, etc.

Return JSON with:
{
    "intent": "query_type",
    "entities": {
        "departments": ["IT", "Sales"],
        "roles": ["Developer"],
        "skills": ["AWS", "Python"],
        "locations": ["Remote"],
        "experience_range": {"min": 5, "max": 10},
        "performance_range": {"min": 4, "max": 5},
        "age_range": {"min": 25, "max": 35}
    },
    "fields_to_analyze": ["performance_rating", "current_salary"],
    "comparison_groups": ["IT", "Sales"],
    "filters": {
        "department": "IT",
        "experience_min": 5
    },
    "sorting": {
        "field": "performance_rating",
        "order": "desc"
    },
    "aggregation_type": "average|count|max|min|sum",
    "limit": 10
}"""
            
            user_prompt = f"""
            Analyze this HR query comprehensively: "{query}"
            
            Extract all possible intent, entities, fields to analyze, filters, and requirements.
            Be thorough in detecting comparison groups, data fields needed, and query complexity.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # Convert to QueryContext
            intent = QueryType(analysis.get("intent", "general_info"))
            
            # Convert field names to DataField enums
            fields_to_analyze = []
            for field_name in analysis.get("fields_to_analyze", []):
                try:
                    fields_to_analyze.append(DataField(field_name))
                except ValueError:
                    print(f"   ⚠️ Unknown field: {field_name}")
            
            return QueryContext(
                original_query=query,
                intent=intent,
                entities=analysis.get("entities", {}),
                fields_to_analyze=fields_to_analyze,
                comparison_groups=analysis.get("comparison_groups", []),
                filters=analysis.get("filters", {}),
                sorting=analysis.get("sorting", {}),
                aggregation_type=analysis.get("aggregation_type"),
                limit=analysis.get("limit", 10)
            )
            
        except Exception as e:
            print(f"   ⚠️ AI analysis failed, using fallback: {e}")
            return self._fallback_query_analysis(query)
    
    def _fallback_query_analysis(self, query: str) -> QueryContext:
        """Fallback query analysis using pattern matching"""
        query_lower = query.lower()
        
        # Basic intent detection
        if any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            intent = QueryType.COMPARISON
        elif any(word in query_lower for word in ["top", "bottom", "highest", "lowest", "best", "worst"]):
            intent = QueryType.RANKING
        elif any(word in query_lower for word in ["how many", "count", "total"]):
            intent = QueryType.COUNT_QUERY
        elif any(word in query_lower for word in ["average", "mean", "statistics"]):
            intent = QueryType.ANALYTICS
        else:
            intent = QueryType.EMPLOYEE_SEARCH
        
        # Basic entity extraction
        entities = {}
        for dept in self.departments:
            if dept.lower() in query_lower:
                if "departments" not in entities:
                    entities["departments"] = []
                entities["departments"].append(dept)
        
        return QueryContext(
            original_query=query,
            intent=intent,
            entities=entities,
            fields_to_analyze=[DataField.PERFORMANCE_RATING],
            comparison_groups=[],
            filters={},
            sorting={},
            aggregation_type=None,
            limit=10
        )
    
    async def _build_comprehensive_pipeline(self, query_context: QueryContext) -> List[Dict[str, Any]]:
        """
        Build comprehensive MongoDB aggregation pipeline based on query context
        
        Args:
            query_context: Rich query context
            
        Returns:
            MongoDB aggregation pipeline
        """
        pipeline = []
        
        # Determine which collections we need to join
        needed_collections = self._determine_needed_collections(query_context.fields_to_analyze)
        
        # Stage 1: Lookup all needed collections
        for collection in needed_collections:
            if collection != "personal_info":  # personal_info is the base
                pipeline.append({
                    "$lookup": {
                        "from": collection,
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": collection
                    }
                })
                pipeline.append({
                    "$unwind": {"path": f"${collection}", "preserveNullAndEmptyArrays": True}
                })
        
        # Stage 2: Add computed fields and type conversions
        computed_fields = self._build_computed_fields(query_context.fields_to_analyze)
        if computed_fields:
            pipeline.append({"$addFields": computed_fields})
        
        # Stage 3: Apply filters
        match_conditions = self._build_match_conditions(query_context)
        if match_conditions:
            pipeline.append({"$match": match_conditions})
        
        return pipeline
    
    def _determine_needed_collections(self, fields: List[DataField]) -> List[str]:
        """Determine which MongoDB collections are needed"""
        needed = {"personal_info"}  # Always need base collection
        
        field_to_collection = {
            DataField.AGE: "personal_info",
            DataField.GENDER: "personal_info",
            DataField.LOCATION: "personal_info",
            DataField.DEPARTMENT: "employment",
            DataField.ROLE: "employment",
            DataField.WORK_MODE: "employment",
            DataField.JOINING_DATE: "employment",
            DataField.CERTIFICATIONS: "learning",
            DataField.COURSES_COMPLETED: "learning",
            DataField.LEARNING_HOURS: "learning",
            DataField.TOTAL_EXPERIENCE: "experience",
            DataField.COMPANY_TENURE: "experience",
            DataField.SKILLS_COUNT: "experience",
            DataField.PERFORMANCE_RATING: "performance",
            DataField.AWARDS: "performance",
            DataField.KPI_MET: "performance",
            DataField.CURRENT_PROJECT: "engagement",
            DataField.ENGAGEMENT_SCORE: "engagement",
            DataField.MANAGER_FEEDBACK: "engagement",
            DataField.SALARY: "compensation",
            DataField.BONUS: "compensation",
            DataField.TOTAL_CTC: "compensation",
            DataField.LEAVE_BALANCE: "attendance",
            DataField.LEAVE_TAKEN: "attendance",
            DataField.ATTENDANCE_PCT: "attendance",
            DataField.ATTRITION_RISK: "attrition",
            DataField.EXIT_INTENT: "attrition"
        }
        
        for field in fields:
            if field in field_to_collection:
                needed.add(field_to_collection[field])
        
        return list(needed)
    
    def _build_computed_fields(self, fields: List[DataField]) -> Dict[str, Any]:
        """Build computed fields for type conversion and calculations"""
        computed = {}
        
        for field in fields:
            if field == DataField.PERFORMANCE_RATING:
                computed["performance_rating_num"] = {
                    "$toInt": {"$ifNull": [{"$toInt": "$performance.performance_rating"}, 0]}
                }
            elif field == DataField.AGE:
                computed["age_num"] = {
                    "$toInt": {"$ifNull": [{"$toInt": "$age"}, 0]}
                }
            elif field == DataField.TOTAL_EXPERIENCE:
                computed["total_experience_num"] = {
                    "$toDouble": {"$ifNull": [{"$toDouble": "$experience.total_experience_years"}, 0]}
                }
            elif field == DataField.SALARY:
                computed["salary_num"] = {
                    "$toInt": {"$ifNull": [{"$toInt": "$compensation.current_salary"}, 0]}
                }
            elif field == DataField.LEAVE_BALANCE:
                computed["leave_balance_num"] = {
                    "$toInt": {"$ifNull": [{"$toInt": "$attendance.leave_balance"}, 0]}
                }
                computed["leave_taken_num"] = {
                    "$toInt": {"$ifNull": [{"$toInt": "$attendance.leave_days_taken"}, 0]}
                }
            elif field == DataField.ENGAGEMENT_SCORE:
                computed["engagement_score_num"] = {
                    "$toInt": {"$ifNull": [{"$toInt": "$engagement.engagement_score"}, 0]}
                }
        
        return computed
    
    def _build_match_conditions(self, query_context: QueryContext) -> Dict[str, Any]:
        """Build match conditions from filters"""
        conditions = {}
        
        filters = query_context.filters
        
        if filters.get("department"):
            conditions["employment.department"] = filters["department"]
        
        if filters.get("role"):
            conditions["employment.role"] = filters["role"]
        
        if filters.get("experience_min"):
            conditions["total_experience_num"] = {"$gte": filters["experience_min"]}
        
        if filters.get("performance_min"):
            conditions["performance_rating_num"] = {"$gte": filters["performance_min"]}
        
        return conditions
    
    async def _handle_comparison_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle comparison queries (Compare IT vs Sales salary)"""
        try:
            await mongodb_client.connect()
            
            pipeline = await self._build_comprehensive_pipeline(query_context)
            
            # Group by comparison groups and calculate statistics
            group_field = None
            if "department" in query_context.entities:
                group_field = "$employment.department"
            elif "role" in query_context.entities:
                group_field = "$employment.role"
            
            if group_field:
                # Build aggregation for each field to analyze
                group_stage = {
                    "_id": group_field,
                    "count": {"$sum": 1}
                }
                
                for field in query_context.fields_to_analyze:
                    if field == DataField.SALARY:
                        group_stage.update({
                            "avg_salary": {"$avg": "$salary_num"},
                            "max_salary": {"$max": "$salary_num"},
                            "min_salary": {"$min": "$salary_num"}
                        })
                    elif field == DataField.PERFORMANCE_RATING:
                        group_stage.update({
                            "avg_rating": {"$avg": "$performance_rating_num"},
                            "max_rating": {"$max": "$performance_rating_num"},
                            "min_rating": {"$min": "$performance_rating_num"}
                        })
                    elif field == DataField.TOTAL_EXPERIENCE:
                        group_stage.update({
                            "avg_experience": {"$avg": "$total_experience_num"},
                            "max_experience": {"$max": "$total_experience_num"},
                            "min_experience": {"$min": "$total_experience_num"}
                        })
                
                pipeline.append({"$group": group_stage})
                pipeline.append({"$sort": {"_id": 1}})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Comparison query failed: {e}")
            return [], 0
    
    async def _handle_ranking_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle ranking queries (Top 10 performers, Bottom 5 in attendance)"""
        try:
            await mongodb_client.connect()
            
            pipeline = await self._build_comprehensive_pipeline(query_context)
            
            # Determine sort field and order
            sort_field = None
            sort_order = -1  # Default to descending (highest first)
            
            if query_context.sorting:
                sort_field = query_context.sorting.get("field")
                sort_order = -1 if query_context.sorting.get("order", "desc") == "desc" else 1
            elif query_context.fields_to_analyze:
                # Infer from field
                field = query_context.fields_to_analyze[0]
                if field == DataField.PERFORMANCE_RATING:
                    sort_field = "performance_rating_num"
                elif field == DataField.SALARY:
                    sort_field = "salary_num"
                elif field == DataField.TOTAL_EXPERIENCE:
                    sort_field = "total_experience_num"
                elif field == DataField.LEAVE_BALANCE:
                    sort_field = "leave_balance_num"
                elif field == DataField.ENGAGEMENT_SCORE:
                    sort_field = "engagement_score_num"
            
            # Check for "bottom", "lowest", "worst" in query
            if any(word in query_context.original_query.lower() for word in ["bottom", "lowest", "worst", "minimum"]):
                sort_order = 1  # Ascending for lowest values
            
            if sort_field:
                pipeline.append({"$sort": {sort_field: sort_order}})
                
                # Limit results
                limit = query_context.limit or 10
                pipeline.append({"$limit": limit})
                
                # Project useful fields
                project_fields = {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "sort_value": f"${sort_field}"
                }
                
                # Add specific fields based on analysis
                for field in query_context.fields_to_analyze:
                    if field == DataField.PERFORMANCE_RATING:
                        project_fields["performance_rating"] = "$performance_rating_num"
                    elif field == DataField.SALARY:
                        project_fields["salary"] = "$salary_num"
                    elif field == DataField.LEAVE_BALANCE:
                        project_fields["leave_balance"] = "$leave_balance_num"
                        project_fields["leave_taken"] = "$leave_taken_num"
                    elif field == DataField.ENGAGEMENT_SCORE:
                        project_fields["engagement_score"] = "$engagement_score_num"
                
                pipeline.append({"$project": project_fields})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Ranking query failed: {e}")
            return [], 0
    
    async def _handle_correlation_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle correlation queries (High performers with low engagement)"""
        try:
            await mongodb_client.connect()
            
            pipeline = await self._build_comprehensive_pipeline(query_context)
            
            # Build complex conditions for correlations
            correlation_conditions = {}
            
            # Example: High performance (>=4) with low engagement (<=3)
            if DataField.PERFORMANCE_RATING in query_context.fields_to_analyze:
                if "high" in query_context.original_query.lower():
                    correlation_conditions["performance_rating_num"] = {"$gte": 4}
                elif "low" in query_context.original_query.lower():
                    correlation_conditions["performance_rating_num"] = {"$lte": 2}
            
            if DataField.ENGAGEMENT_SCORE in query_context.fields_to_analyze:
                if "low engagement" in query_context.original_query.lower():
                    correlation_conditions["engagement_score_num"] = {"$lte": 3}
                elif "high engagement" in query_context.original_query.lower():
                    correlation_conditions["engagement_score_num"] = {"$gte": 4}
            
            if correlation_conditions:
                pipeline.append({"$match": correlation_conditions})
            
            # Project useful fields
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "performance_rating": "$performance_rating_num",
                    "engagement_score": "$engagement_score_num",
                    "leave_balance": "$leave_balance_num"
                }
            })
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Correlation query failed: {e}")
            return [], 0
    
    async def _handle_recommendation_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle recommendation queries (Who needs training? Flight risk employees?)"""
        try:
            await mongodb_client.connect()
            
            pipeline = await self._build_comprehensive_pipeline(query_context)
            
            # Build recommendation conditions based on query
            query_lower = query_context.original_query.lower()
            recommendation_conditions = {}
            
            if "training" in query_lower or "learning" in query_lower:
                # Low learning hours or courses completed
                recommendation_conditions["$or"] = [
                    {"learning.learning_hours_ytd": {"$lt": 20}},
                    {"learning.courses_completed": {"$lt": 3}}
                ]
            elif "flight risk" in query_lower or "attrition" in query_lower:
                # High attrition risk
                recommendation_conditions["attrition.attrition_risk_score"] = "High"
            elif "promotion" in query_lower:
                # High performers with long tenure
                recommendation_conditions["$and"] = [
                    {"performance_rating_num": {"$gte": 4}},
                    {"experience.years_in_current_company": {"$gte": 3}}
                ]
            elif "engagement" in query_lower:
                # Low engagement scores
                recommendation_conditions["engagement_score_num"] = {"$lte": 3}
            
            if recommendation_conditions:
                pipeline.append({"$match": recommendation_conditions})
            
            # Project useful fields for recommendations
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "performance_rating": "$performance_rating_num",
                    "engagement_score": "$engagement_score_num",
                    "learning_hours": "$learning.learning_hours_ytd",
                    "courses_completed": "$learning.courses_completed",
                    "attrition_risk": "$attrition.attrition_risk_score",
                    "years_in_company": "$experience.years_in_current_company"
                }
            })
            
            # Limit to manageable number
            pipeline.append({"$limit": 20})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Recommendation query failed: {e}")
            return [], 0
    
    async def _handle_trend_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle trend analysis queries (Recent joiners, employees joining in last 6 months)"""
        try:
            await mongodb_client.connect()
            
            pipeline = await self._build_comprehensive_pipeline(query_context)
            
            # Build date-based conditions
            query_lower = query_context.original_query.lower()
            date_conditions = {}
            
            # Calculate date ranges
            current_date = datetime.now()
            
            if "recent" in query_lower or "last" in query_lower:
                if "6 months" in query_lower:
                    cutoff_date = current_date - timedelta(days=180)
                elif "year" in query_lower:
                    cutoff_date = current_date - timedelta(days=365)
                elif "month" in query_lower:
                    cutoff_date = current_date - timedelta(days=30)
                else:
                    cutoff_date = current_date - timedelta(days=90)  # Default 3 months
                
                date_conditions["employment.joining_date"] = {
                    "$gte": cutoff_date.strftime("%Y-%m-%d")
                }
            
            if date_conditions:
                pipeline.append({"$match": date_conditions})
            
            # Sort by joining date (most recent first)
            pipeline.append({"$sort": {"employment.joining_date": -1}})
            
            # Project useful fields
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "joining_date": "$employment.joining_date",
                    "work_mode": "$employment.work_mode"
                }
            })
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Trend query failed: {e}")
            return [], 0
    
    async def _handle_complex_filter_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle complex multi-criteria queries"""
        try:
            await mongodb_client.connect()
            
            pipeline = await self._build_comprehensive_pipeline(query_context)
            
            # Complex filters are already built in _build_match_conditions
            # Add sorting if specified
            if query_context.sorting and query_context.sorting.get("field"):
                sort_field = query_context.sorting["field"]
                sort_order = -1 if query_context.sorting.get("order", "desc") == "desc" else 1
                
                # Map field names to computed field names
                field_mapping = {
                    "performance_rating": "performance_rating_num",
                    "salary": "salary_num",
                    "experience": "total_experience_num",
                    "leave_balance": "leave_balance_num"
                }
                
                actual_field = field_mapping.get(sort_field, sort_field)
                pipeline.append({"$sort": {actual_field: sort_order}})
            
            # Limit results
            limit = query_context.limit or 20
            pipeline.append({"$limit": limit})
            
            # Comprehensive projection
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "location": 1,
                    "work_mode": "$employment.work_mode",
                    "certifications": "$learning.certifications",
                    "total_experience": "$total_experience_num",
                    "performance_rating": "$performance_rating_num",
                    "current_project": "$engagement.current_project",
                    "engagement_score": "$engagement_score_num",
                    "leave_balance": "$leave_balance_num"
                }
            })
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Complex filter query failed: {e}")
            return [], 0
    
    async def _handle_count_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle count queries with comprehensive filtering"""
        try:
            await mongodb_client.connect()
            
            # Build the pipeline using the WORKING logic
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Build match conditions from query_context filters
            match_conditions = {}
            
            # Check entities for department filter
            if query_context.entities.get("departments"):
                departments = query_context.entities["departments"]
                if len(departments) == 1:
                    match_conditions["employment.department"] = departments[0]
                else:
                    match_conditions["employment.department"] = {"$in": departments}
            
            # Check entities for role filter  
            if query_context.entities.get("roles"):
                roles = query_context.entities["roles"]
                if len(roles) == 1:
                    match_conditions["employment.role"] = roles[0]
                else:
                    match_conditions["employment.role"] = {"$in": roles}
            
            # Add match stage if we have conditions
            if match_conditions:
                pipeline.append({"$match": match_conditions})
                print(f"   🎯 Applied filters: {match_conditions}")
            
            # Add count stage
            pipeline.append({"$count": "total"})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            count = results[0]["total"] if results else 0
            
            return [], count
            
        except Exception as e:
            print(f"   ❌ Count query failed: {e}")
            return [], 0
    
    async def _handle_analytics_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle analytics queries with comprehensive statistics"""
        try:
            await mongodb_client.connect()
            
            pipeline = await self._build_comprehensive_pipeline(query_context)
            
            # Build comprehensive aggregation
            group_stage = {
                "_id": None,
                "count": {"$sum": 1}
            }
            
            # Add statistics for each field to analyze
            for field in query_context.fields_to_analyze:
                if field == DataField.PERFORMANCE_RATING:
                    group_stage.update({
                        "avg_performance": {"$avg": "$performance_rating_num"},
                        "max_performance": {"$max": "$performance_rating_num"},
                        "min_performance": {"$min": "$performance_rating_num"}
                    })
                elif field == DataField.SALARY:
                    group_stage.update({
                        "avg_salary": {"$avg": "$salary_num"},
                        "max_salary": {"$max": "$salary_num"},
                        "min_salary": {"$min": "$salary_num"}
                    })
                elif field == DataField.TOTAL_EXPERIENCE:
                    group_stage.update({
                        "avg_experience": {"$avg": "$total_experience_num"},
                        "max_experience": {"$max": "$total_experience_num"},
                        "min_experience": {"$min": "$total_experience_num"}
                    })
                elif field == DataField.LEAVE_BALANCE:
                    group_stage.update({
                        "avg_leave_balance": {"$avg": "$leave_balance_num"},
                        "max_leave_balance": {"$max": "$leave_balance_num"},
                        "min_leave_balance": {"$min": "$leave_balance_num"}
                    })
                elif field == DataField.AGE:
                    group_stage.update({
                        "avg_age": {"$avg": "$age_num"},
                        "max_age": {"$max": "$age_num"},
                        "min_age": {"$min": "$age_num"}
                    })
            
            pipeline.append({"$group": group_stage})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            if results:
                count = results[0].get("count", 0)
                return results, count
            else:
                return [], 0
                
        except Exception as e:
            print(f"   ❌ Analytics query failed: {e}")
            return [], 0
    
    async def _handle_search_query(self, query_context: QueryContext) -> Tuple[List[Dict[str, Any]], int]:
        """Handle general search queries using Azure Search"""
        try:
            # Use Azure Search for employee lookup
            search_results = azure_search_client.search(
                query=query_context.original_query,
                top_k=query_context.limit or 10,
                select_fields=["id", "full_name", "department", "role", "location", "certifications", "current_project"]
            )
            
            # Apply additional filters if needed
            filtered_results = []
            for result in search_results:
                # Apply entity filters
                entities = query_context.entities
                
                if entities.get("departments"):
                    if result.get("department") not in entities["departments"]:
                        continue
                
                if entities.get("roles"):
                    if result.get("role") not in entities["roles"]:
                        continue
                
                filtered_results.append(result)
            
            return filtered_results, len(filtered_results)
            
        except Exception as e:
            print(f"   ❌ Search query failed: {e}")
            return [], 0
    
    async def _generate_comprehensive_response(self, query_context: QueryContext, 
                                             results: List[Dict[str, Any]], count: int) -> str:
        """Generate comprehensive natural language response"""
        try:
            # Build rich context for AI
            context = {
                "query": query_context.original_query,
                "intent": query_context.intent.value,
                "entities": query_context.entities,
                "fields_analyzed": [f.value for f in query_context.fields_to_analyze],
                "count": count,
                "has_results": len(results) > 0,
                "complexity": self._assess_complexity(query_context)
            }
            
            # Add results based on query type
            if query_context.intent == QueryType.COMPARISON and results:
                context["comparison_data"] = results
            elif query_context.intent == QueryType.RANKING and results:
                context["ranked_employees"] = results[:10]
            elif query_context.intent == QueryType.ANALYTICS and results:
                context["analytics_data"] = results[0] if results else {}
            elif results:
                context["employees"] = results[:5]
            
            # Enhanced system prompt for comprehensive responses
            system_prompt = """You are an expert HR analytics assistant providing comprehensive insights.
            
            Generate detailed, professional responses that:
            - Provide specific numbers and statistics
            - Include employee names and relevant details when appropriate
            - Explain the significance of findings
            - Use clear formatting with bullet points for multiple results
            - Provide actionable insights when possible
            - Handle complex comparisons, rankings, and correlations intelligently
            
            For different query types:
            - Comparisons: Show side-by-side statistics with analysis
            - Rankings: List employees with their specific values in order
            - Analytics: Provide comprehensive statistics with context
            - Recommendations: Explain why employees are recommended and what actions to take
            - Correlations: Highlight the relationships found and their implications
            """
            
            user_prompt = f"""
            Query: "{query_context.original_query}"
            Intent: {query_context.intent.value}
            Context: {json.dumps(context, default=str)}
            
            Provide a comprehensive, professional response to this HR analytics query.
            Include specific data points, employee details, and actionable insights.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=600,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"   ⚠️ AI response generation failed: {e}")
            return self._generate_fallback_response(query_context, results, count)
    
    def _generate_fallback_response(self, query_context: QueryContext, 
                                  results: List[Dict[str, Any]], count: int) -> str:
        """Generate fallback response when AI fails"""
        intent = query_context.intent
        
        if intent == QueryType.COUNT_QUERY:
            return f"Found {count} employees matching your criteria."
        
        elif intent == QueryType.COMPARISON and results:
            response_lines = ["Comparison Results:"]
            for result in results:
                group_name = result.get("_id", "Unknown")
                emp_count = result.get("count", 0)
                response_lines.append(f"• {group_name}: {emp_count} employees")
                
                # Add specific statistics if available
                if "avg_salary" in result:
                    response_lines.append(f"  - Average Salary: ${result['avg_salary']:,.0f}")
                if "avg_rating" in result:
                    response_lines.append(f"  - Average Rating: {result['avg_rating']:.1f}")
            
            return "\n".join(response_lines)
        
        elif intent == QueryType.RANKING and results:
            response_lines = ["Top Results:"]
            for i, result in enumerate(results[:10], 1):
                name = result.get("full_name", "Unknown")
                dept = result.get("department", "N/A")
                
                # Add specific value based on field analyzed
                value_text = ""
                if "performance_rating" in result:
                    value_text = f" - Rating: {result['performance_rating']}"
                elif "salary" in result:
                    value_text = f" - Salary: ${result['salary']:,}"
                elif "leave_balance" in result:
                    value_text = f" - Leave Balance: {result['leave_balance']} days"
                
                response_lines.append(f"{i}. {name} ({dept}){value_text}")
            
            return "\n".join(response_lines)
        
        elif intent == QueryType.ANALYTICS and results:
            result = results[0]
            response_lines = ["Analytics Summary:"]
            response_lines.append(f"• Total Employees: {result.get('count', 0)}")
            
            # Add specific analytics
            if "avg_performance" in result:
                response_lines.append(f"• Average Performance: {result['avg_performance']:.1f}")
            if "avg_salary" in result:
                response_lines.append(f"• Average Salary: ${result['avg_salary']:,.0f}")
            
            return "\n".join(response_lines)
        
        elif count > 0:
            return f"Found {count} employees matching your criteria. Use more specific queries for detailed information."
        
        else:
            return "No employees found matching your criteria. Try adjusting your search parameters."
    
    def _assess_complexity(self, query_context: QueryContext) -> str:
        """Assess query complexity for analytics"""
        complexity_score = 0
        
        # Intent complexity
        complex_intents = [QueryType.COMPARISON, QueryType.CORRELATION, QueryType.RECOMMENDATION]
        if query_context.intent in complex_intents:
            complexity_score += 2
        
        # Number of fields to analyze
        complexity_score += len(query_context.fields_to_analyze)
        
        # Number of filters
        complexity_score += len(query_context.filters)
        
        # Comparison groups
        complexity_score += len(query_context.comparison_groups)
        
        if complexity_score <= 2:
            return "Simple"
        elif complexity_score <= 5:
            return "Moderate"
        else:
            return "Complex"
    
    async def test_comprehensive_queries(self):
        """Test the engine with comprehensive query examples"""
        print("\n🧪 Testing Robust 360° HR Query Engine")
        print("=" * 60)
        
        comprehensive_test_queries = [
            # Basic queries
            "How many employees work in IT?",
            "Find developers with AWS certification",
            
            # Analytics queries
            "What's the average salary in each department?",
            "Show me employees with lowest performance ratings",
            "Who has the highest leave balance?",
            
            # Comparison queries
            "Compare average performance between IT and Sales departments",
            "What's the salary difference between developers and managers?",
            
            # Ranking queries
            "Top 5 performers in the company",
            "Bottom 3 employees in attendance",
            "Highest paid employees in IT department",
            
            # Complex filter queries
            "IT developers with AWS certification and more than 5 years experience",
            "Remote employees with high performance ratings",
            "Employees in Sales with PMP certification and low attrition risk",
            
            # Correlation queries
            "High performers with low engagement scores",
            "Employees with high salary but low performance",
            
            # Recommendation queries
            "Who needs training based on low learning hours?",
            "Which employees are flight risk?",
            "Who should be considered for promotion?",
            
            # Trend queries
            "Show me employees who joined in the last 6 months",
            "Recent joiners in IT department"
        ]
        
        for i, query in enumerate(comprehensive_test_queries, 1):
            print(f"\n{i:2d}. Testing: '{query}'")
            result = await self.process_query(query)
            
            print(f"    🎯 Intent: {result['intent']}")
            print(f"    📊 Count: {result['count']}")
            print(f"    🔧 Complexity: {result.get('query_complexity', 'Unknown')}")
            print(f"    ⏱️ Time: {result['execution_time_ms']:.1f}ms")
            print(f"    💬 Response: {result['response'][:120]}...")
            
            if result['results'] and result['intent'] in ['ranking', 'employee_search']:
                print(f"    👥 Sample results:")
                for emp in result['results'][:2]:
                    name = emp.get('full_name', 'N/A')
                    dept = emp.get('department', 'N/A')
                    role = emp.get('role', 'N/A')
                    print(f"       - {name} ({dept}) - {role}")
            
            print("-" * 40)
        
        print(f"\n🎉 Comprehensive testing completed!")

# Global instance
robust_hr_query_engine = RobustHRQueryEngine()

async def main():
    """Main function for testing the robust engine"""
    print("🚀 Robust 360° HR Query Engine - Complete Solution")
    print("=" * 70)
    
    try:
        # Run comprehensive tests
        await robust_hr_query_engine.test_comprehensive_queries()
        
        # Interactive mode
        print(f"\n🎮 Interactive Mode - Test ANY HR Question")
        print("Type complex queries about employee analytics, comparisons, rankings, etc.")
        print("Examples:")
        print("- 'Compare IT vs Sales average performance'")
        print("- 'Top 10 highest paid remote employees'") 
        print("- 'Who needs training based on low learning hours?'")
        print("- 'High performers with low engagement scores'")
        print("Type 'quit' to exit")
        print("=" * 50)
        
        while True:
            try:
                user_query = input("\n💬 Enter your comprehensive HR query: ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_query:
                    continue
                
                result = await robust_hr_query_engine.process_query(user_query)
                
                print(f"\n🤖 Analysis:")
                print(f"   Intent: {result['intent']}")
                print(f"   Complexity: {result.get('query_complexity', 'Unknown')}")
                print(f"   Fields Analyzed: {result.get('fields_analyzed', [])}")
                print(f"   Count: {result['count']}")
                
                print(f"\n📋 Response:")
                print(result['response'])
                
                if result['results'] and len(result['results']) > 0:
                    print(f"\n📊 Sample Data:")
                    for emp in result['results'][:3]:
                        if isinstance(emp, dict):
                            key_info = []
                            if emp.get('full_name'):
                                key_info.append(emp['full_name'])
                            if emp.get('department'):
                                key_info.append(f"({emp['department']})")
                            if emp.get('performance_rating'):
                                key_info.append(f"Rating: {emp['performance_rating']}")
                            if emp.get('salary'):
                                key_info.append(f"Salary: ${emp['salary']:,}")
                            print(f"   - {' '.join(key_info)}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Robust HR Query Engine testing completed!")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())