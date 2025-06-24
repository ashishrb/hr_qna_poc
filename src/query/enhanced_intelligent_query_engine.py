# src/query/enhanced_intelligent_query_engine.py
import asyncio
import json
import time
import sys
import os
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict, deque

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Validate and import external libraries
try:
    from openai import AzureOpenAI
except ImportError as e:
    print(f"❌ OpenAI library not found: {e}")
    raise

try:
    from src.core.config import settings
    from src.database.mongodb_client import mongodb_client
    from src.search.azure_search_client import azure_search_client
except ImportError as e:
    print(f"❌ Core modules not found: {e}")
    raise

class QueryType(Enum):
    ANALYTICS = "analytics"
    TEXT_SEARCH = "text_search"
    COMPLEX_FILTER = "complex_filter"
    COMPARISON = "comparison"
    TREND_ANALYSIS = "trend_analysis"
    RECOMMENDATION = "recommendation"

class DataSource(Enum):
    MONGODB = "mongodb"
    AZURE_SEARCH = "azure_search"
    HYBRID = "hybrid"

@dataclass
class QueryContext:
    """Enhanced query context with user history and preferences"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    previous_queries: List[str] = None
    user_department: Optional[str] = None
    user_role: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.previous_queries is None:
            self.previous_queries = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class QueryIntent:
    query_type: QueryType
    data_source: DataSource
    confidence: float
    extracted_entities: Dict[str, Any]
    suggested_pipeline: Optional[Dict] = None
    context: Optional[QueryContext] = None

@dataclass
class QueryResult:
    data: List[Dict[str, Any]]
    count: int
    metadata: Dict[str, Any]
    source: DataSource
    execution_time_ms: float
    cache_hit: bool = False
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

class QueryIntelligenceLayer:
    """Advanced query intelligence with context awareness and optimization"""
    
    def __init__(self):
        # HR-specific synonym dictionary
        self.hr_synonyms = {
            "devs": "developers",
            "dev": "developer",
            "eng": "engineering",
            "mgr": "manager",
            "mgrs": "managers",
            "sr": "senior",
            "jr": "junior",
            "dept": "department",
            "certs": "certifications",
            "exp": "experience",
            "yrs": "years",
            "emp": "employee",
            "emps": "employees",
            "perf": "performance",
            "proj": "project",
            "projs": "projects"
        }
        
        # Common HR abbreviations
        self.hr_abbreviations = {
            "hr": "human resources",
            "it": "information technology",
            "qa": "quality assurance",
            "ui": "user interface",
            "ux": "user experience",
            "pm": "project manager",
            "pmp": "project management professional",
            "scrum": "scrum methodology",
            "agile": "agile methodology"
        }
        
        # Query templates for common HR queries
        self.query_templates = {
            "employee_count": [
                "How many employees work in {department}?",
                "What's the headcount for {department}?",
                "How many people are in {location}?"
            ],
            "skill_search": [
                "Find employees with {skill} certification",
                "Who has {skill} experience?",
                "Show me {skill} experts"
            ],
            "performance_analysis": [
                "Who are the top performers in {department}?",
                "Show high-performing {role} employees",
                "Find employees with excellent ratings"
            ]
        }
    
    def expand_query(self, query: str, context: Optional[QueryContext] = None) -> str:
        """Expand query with synonyms and context"""
        expanded_query = query.lower()
        
        # Apply HR-specific synonyms
        for abbrev, full_form in self.hr_synonyms.items():
            expanded_query = expanded_query.replace(f" {abbrev} ", f" {full_form} ")
            expanded_query = expanded_query.replace(f" {abbrev}s ", f" {full_form}s ")
        
        # Apply HR abbreviations
        for abbrev, full_form in self.hr_abbreviations.items():
            expanded_query = expanded_query.replace(f" {abbrev} ", f" {full_form} ")
        
        # Add context-based expansion
        if context and context.user_department:
            # If user asks about "our department", expand with their department
            expanded_query = expanded_query.replace("our department", context.user_department)
            expanded_query = expanded_query.replace("my department", context.user_department)
        
        return expanded_query
    
    def suggest_corrections(self, query: str) -> List[str]:
        """Suggest query corrections using Levenshtein distance"""
        suggestions = []
        
        # Common HR terms for spell check
        hr_terms = [
            "developer", "manager", "analyst", "engineer", "director",
            "department", "certification", "experience", "performance",
            "project", "employee", "salary", "benefits", "training"
        ]
        
        words = query.lower().split()
        corrected_words = []
        
        for word in words:
            best_match = word
            min_distance = float('inf')
            
            for term in hr_terms:
                distance = self._levenshtein_distance(word, term)
                if distance < min_distance and distance <= 2:  # Max 2 character differences
                    min_distance = distance
                    best_match = term
            
            corrected_words.append(best_match)
        
        suggested_query = " ".join(corrected_words)
        if suggested_query != query.lower():
            suggestions.append(f"Did you mean: {suggested_query}?")
        
        return suggestions
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def detect_context_patterns(self, query: str, context: Optional[QueryContext] = None) -> Dict[str, Any]:
        """Detect patterns and context in queries"""
        patterns = {
            "temporal": False,
            "comparative": False,
            "aggregative": False,
            "personal": False,
            "departmental": False
        }
        
        query_lower = query.lower()
        
        # Temporal patterns
        temporal_keywords = ["last", "previous", "current", "this", "next", "recent", "trend", "over time"]
        patterns["temporal"] = any(keyword in query_lower for keyword in temporal_keywords)
        
        # Comparative patterns
        comparative_keywords = ["vs", "versus", "compare", "better", "worse", "more", "less", "than"]
        patterns["comparative"] = any(keyword in query_lower for keyword in comparative_keywords)
        
        # Aggregative patterns
        aggregative_keywords = ["total", "count", "average", "sum", "maximum", "minimum", "how many"]
        patterns["aggregative"] = any(keyword in query_lower for keyword in aggregative_keywords)
        
        # Personal patterns
        personal_keywords = ["my", "me", "i", "myself"]
        patterns["personal"] = any(keyword in query_lower for keyword in personal_keywords)
        
        # Departmental patterns
        departmental_keywords = ["our", "we", "us", "team", "group"]
        patterns["departmental"] = any(keyword in query_lower for keyword in departmental_keywords)
        
        return patterns
    
    def generate_query_suggestions(self, partial_query: str, context: Optional[QueryContext] = None) -> List[str]:
        """Generate intelligent query suggestions"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Pattern-based suggestions
        if "how many" in partial_lower:
            suggestions.extend([
                "How many employees work in IT department?",
                "How many developers are there?",
                "How many people have AWS certification?"
            ])
        
        elif "find" in partial_lower or "show" in partial_lower:
            suggestions.extend([
                "Find employees with Python skills",
                "Show me all managers",
                "Find high-performing employees"
            ])
        
        elif "who" in partial_lower:
            suggestions.extend([
                "Who are the developers in our company?",
                "Who has PMP certification?",
                "Who works in the Sales department?"
            ])
        
        # Context-based suggestions
        if context and context.previous_queries:
            # Suggest related queries based on history
            last_query = context.previous_queries[-1] if context.previous_queries else ""
            if "department" in last_query.lower():
                suggestions.append("Show me roles in that department")
                suggestions.append("What skills are common in that department?")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    

    def suggest_alternatives_for_missing_data(self, query: str, result_count: int) -> List[str]:
        """Suggest smart alternatives when queries return no results"""
        suggestions = []
        query_lower = query.lower()
        
        # Smart suggestions for programming languages
        if any(lang in query_lower for lang in ["python", "javascript", "java", "node"]):
            suggestions.append("💡 Programming languages aren't tracked in our system.")
            suggestions.append("🔍 Try searching for certifications instead:")
            suggestions.append("   • 'Find employees with GCP certification'")
            suggestions.append("   • 'Who has AWS certification?'")
            suggestions.append("   • 'Show me PMP certified employees'")
        
        # Smart suggestions for department variations
        elif any(dept in query_lower for dept in ["eng", "engineering", "tech", "technology"]):
            suggestions.append("🏢 'Engineering' department not found.")
            suggestions.append("🔍 Try these actual departments:")
            suggestions.append("   • 'How many developers work in IT?' (7 employees)")
            suggestions.append("   • 'Find employees in Operations' (4 employees)")
            suggestions.append("   • 'Show me people in Sales' (6 employees)")
        
        # Smart suggestions for role variations
        elif any(role in query_lower for role in ["engineer", "programmer", "coder"]):
            suggestions.append("💼 'Engineer' role not found.")
            suggestions.append("🔍 Try these actual roles:")
            suggestions.append("   • 'Find all developers' (5 employees)")
            suggestions.append("   • 'Show me analysts' (7 employees)")
            suggestions.append("   • 'Who are the managers?' (5 employees)")
        
        # Smart suggestions for skill variations
        elif any(skill in query_lower for skill in ["coding", "programming", "software"]):
            suggestions.append("💻 Software skills aren't detailed in our system.")
            suggestions.append("🔍 Try searching by certifications:")
            suggestions.append("   • 'GCP certified employees'")
            suggestions.append("   • 'PMP certification holders'")
        
        # Generic suggestions if no specific pattern found
        elif result_count == 0:
            suggestions.append("🔍 No results found. Here's what you can search for:")
            suggestions.append("📊 Analytics: 'How many people work in [IT/Sales/Operations]?'")
            suggestions.append("👥 People: 'Find all [developers/managers/analysts]'")
            suggestions.append("🏆 Certifications: 'Who has [GCP/PMP/AWS] certification?'")
        
        return suggestions

class PerformanceCache:
    """High-performance caching layer with TTL support"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.ttl_map = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_key(self, query: str, filters: Dict[str, Any] = None) -> str:
        """Generate cache key from query and filters"""
        key_data = {"query": query.lower().strip(), "filters": filters or {}}
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, filters: Dict[str, Any] = None) -> Optional[QueryResult]:
        """Get cached result if valid"""
        key = self._generate_key(query, filters)
        
        if key in self.cache:
            expiry_time = self.ttl_map.get(key, 0)
            if time.time() < expiry_time:
                self.hit_count += 1
                result = self.cache[key]
                result.cache_hit = True
                return result
            else:
                # Expired, remove from cache
                del self.cache[key]
                del self.ttl_map[key]
        
        self.miss_count += 1
        return None
    
    def set(self, query: str, result: QueryResult, filters: Dict[str, Any] = None, ttl: int = None) -> None:
        """Cache result with TTL"""
        key = self._generate_key(query, filters)
        ttl = ttl or self.default_ttl
        
        self.cache[key] = result
        self.ttl_map[key] = time.time() + ttl
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count"""
        current_time = time.time()
        expired_keys = [key for key, expiry in self.ttl_map.items() if current_time >= expiry]
        
        for key in expired_keys:
            del self.cache[key]
            del self.ttl_map[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "expired_cleared": self.clear_expired()
        }

class QueryAnalytics:
    """Track query patterns and performance metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.query_history = deque(maxlen=max_history)
        self.performance_metrics = defaultdict(list)
        self.popular_queries = defaultdict(int)
        self.error_patterns = defaultdict(int)
    
    def track_query(self, query: str, intent: str, execution_time: float, 
                   result_count: int, success: bool) -> None:
        """Track query execution metrics"""
        record = {
            "query": query,
            "intent": intent,
            "execution_time": execution_time,
            "result_count": result_count,
            "success": success,
            "timestamp": datetime.utcnow()
        }
        
        self.query_history.append(record)
        self.performance_metrics[intent].append(execution_time)
        
        if success:
            self.popular_queries[query.lower().strip()] += 1
        else:
            self.error_patterns[intent] += 1
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance analytics summary"""
        if not self.query_history:
            return {"message": "No query data available"}
        
        # Calculate overall metrics
        total_queries = len(self.query_history)
        successful_queries = sum(1 for q in self.query_history if q["success"])
        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        
        # Average execution time by intent
        avg_times = {}
        for intent, times in self.performance_metrics.items():
            avg_times[intent] = sum(times) / len(times) if times else 0
        
        # Top 5 popular queries
        top_queries = sorted(self.popular_queries.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_queries": total_queries,
            "success_rate": success_rate,
            "average_execution_times": avg_times,
            "popular_queries": top_queries,
            "error_patterns": dict(self.error_patterns)
        }
    
    def get_trending_topics(self, hours: int = 24) -> List[str]:
        """Get trending query topics in the last N hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_queries = [q for q in self.query_history if q["timestamp"] > cutoff_time]
        
        # Extract keywords from recent queries
        keyword_counts = defaultdict(int)
        for query_record in recent_queries:
            words = query_record["query"].lower().split()
            for word in words:
                if len(word) > 3:  # Ignore short words
                    keyword_counts[word] += 1
        
        # Return top trending keywords
        trending = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [word for word, count in trending]

class EnhancedIntelligentQueryEngine:
    """Enhanced intelligent query engine with advanced features"""
    
    def __init__(self):
        # Validate required settings
        required_settings = ['azure_openai_api_key', 'azure_openai_endpoint']
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                raise ValueError(f"❌ Missing required setting: {setting}")
        
        # Initialize OpenAI client
        try:
            self.openai_client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version="2023-05-15",
                azure_endpoint=settings.azure_openai_endpoint
            )
        except Exception as e:
            raise ValueError(f"❌ Failed to initialize OpenAI client: {e}")
        
        # Initialize enhanced components
        self.intelligence_layer = QueryIntelligenceLayer()
        self.cache = PerformanceCache(default_ttl=300)  # 5 minutes
        self.analytics = QueryAnalytics(max_history=1000)
        
        # Initialize fallback engine if available
        try:
            from src.query.query_engine import HRQueryEngine
            self.fallback_engine = HRQueryEngine()
            print("✅ Fallback engine initialized")
        except ImportError:
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
    
    async def process_query(self, query: str, context: Optional[QueryContext] = None) -> Dict[str, Any]:
        """Enhanced query processing with intelligence layer and caching"""
        start_time = time.time()
        
        try:
            # Check cache first
            cached_result = self.cache.get(query)
            if cached_result:
                print(f"🚀 Cache hit for query: '{query}'")
                return self._format_response(query, cached_result, context, start_time)
            
            # Expand query using intelligence layer
            expanded_query = self.intelligence_layer.expand_query(query, context)
            if expanded_query != query:
                print(f"🔍 Query expanded: '{query}' → '{expanded_query}'")
            
            # Enhanced AI-powered intent and entity extraction
            intent = await self._extract_intent_and_entities_enhanced(expanded_query, context)
            
            # Route to optimal data source with error handling
            result = await self._execute_query_with_fallback(expanded_query, intent)
            
            # Generate intelligent response
            response = await self._generate_intelligent_response(expanded_query, intent, result)
            
            # Add query suggestions
            suggestions = self.intelligence_layer.generate_query_suggestions(query, context)
            result.suggestions = suggestions
            
            # Cache the result
            self.cache.set(query, result)
            
            # Track analytics
            execution_time = (time.time() - start_time) * 1000
            self.analytics.track_query(
                query, intent.query_type.value, execution_time, 
                result.count, result.count >= 0
            )
            
            return self._format_response(query, result, context, start_time, intent, response)
            
        except Exception as e:
            print(f"❌ Enhanced query processing failed: {e}")
            
            # Track error
            execution_time = (time.time() - start_time) * 1000
            self.analytics.track_query(query, "error", execution_time, 0, False)
            
            # Fallback to simple engine if available
            if self.fallback_engine is not None:
                return await self._fallback_to_simple_engine(query, start_time)
            else:
                return self._error_response(query, str(e), start_time)
    
    def _format_response(self, query: str, result: QueryResult, context: Optional[QueryContext], 
                        start_time: float, intent: Optional[QueryIntent] = None, 
                        response: Optional[str] = None) -> Dict[str, Any]:
        """Format the final response"""
        execution_time = (time.time() - start_time) * 1000
        
        # Generate corrections if needed
        corrections = self.intelligence_layer.suggest_corrections(query)

        if result.count == 0:
            smart_suggestions = self.intelligence_layer.suggest_alternatives_for_missing_data(query, result.count)
            if smart_suggestions:
                result.suggestions.extend(smart_suggestions)
        
        return {
            "query": query,
            "intent": intent.query_type.value if intent else "unknown",
            "entities": intent.extracted_entities if intent else {},
            "data_source": result.source.value,
            "results": result.data,
            "count": result.count,
            "response": response or f"Found {result.count} results for your query.",
            "execution_time_ms": execution_time,
            "confidence": intent.confidence if intent else 0.0,
            "status": "success",
            "cache_hit": result.cache_hit,
            "suggestions": result.suggestions,
            "corrections": corrections,
            "metadata": {
                "patterns_detected": self.intelligence_layer.detect_context_patterns(query, context),
                "trending_topics": self.analytics.get_trending_topics(hours=24)[:5]
            }
        }
    
    def _error_response(self, query: str, error: str, start_time: float) -> Dict[str, Any]:
        """Generate error response"""
        execution_time = (time.time() - start_time) * 1000
        
        return {
            "query": query,
            "intent": "unknown",
            "entities": {},
            "data_source": "none",
            "results": [],
            "count": 0,
            "response": f"I apologize, but I encountered an error processing your query: {error}",
            "execution_time_ms": execution_time,
            "confidence": 0.0,
            "status": "error",
            "cache_hit": False,
            "suggestions": self.intelligence_layer.generate_query_suggestions(query),
            "corrections": self.intelligence_layer.suggest_corrections(query)
        }
    
    async def _extract_intent_and_entities_enhanced(self, query: str, context: Optional[QueryContext] = None) -> QueryIntent:
        """Enhanced AI-powered intent detection with context awareness"""
        
        # Build context-aware system prompt
        context_info = ""
        if context:
            if context.user_department:
                context_info += f"User department: {context.user_department}\n"
            if context.user_role:
                context_info += f"User role: {context.user_role}\n"
            if context.previous_queries:
                context_info += f"Recent queries: {', '.join(context.previous_queries[-3:])}\n"
        
        system_prompt = f"""You are an expert HR data analyst specializing in employee queries. Extract intent and entities from HR queries with high precision.

        {context_info}

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

        Return JSON format:
        {{
            "query_type": "analytics|text_search|complex_filter|comparison|trend_analysis|recommendation",
            "data_source": "mongodb|azure_search|hybrid", 
            "confidence": 0.0-1.0,
            "entities": {{
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
            }}
        }}"""
        
        user_prompt = f"""
        Query: "{query}"
        
        Analyze this HR query considering the context and extract the intent and entities.
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
            
            #analysis = json.loads(response.choices[0].message.content)

            content = response.choices[0].message.content.strip()
            print(f"🔍 Debug - Raw OpenAI response: '{content}'")

            # Handle empty or invalid responses
            if not content:
                print("❌ Empty response from OpenAI")
                return self._fallback_intent_detection(query, context)

            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response if it contains extra text
                if '{' in content and '}' in content:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    clean_content = content[start:end]
                    print(f"🔧 Cleaned JSON: '{clean_content}'")
                    try:
                        analysis = json.loads(clean_content)
                    except json.JSONDecodeError:
                        print("❌ JSON parsing failed even after cleaning")
                        return self._fallback_intent_detection(query, context)
                else:
                    print("❌ No JSON found in response")
                    return self._fallback_intent_detection(query, context)
            
            return QueryIntent(
                query_type=QueryType(analysis["query_type"]),
                data_source=DataSource(analysis["data_source"]),
                confidence=analysis["confidence"],
                extracted_entities=analysis["entities"],
                context=context
            )
            
        except Exception as e:
            print(f"❌ Enhanced AI extraction failed: {e}")
            return self._fallback_intent_detection(query, context)
    
    def _fallback_intent_detection(self, query: str, context: Optional[QueryContext] = None) -> QueryIntent:
        """Enhanced pattern-based intent detection as fallback"""
        query_lower = query.lower()
        
        # Enhanced pattern matching with context
        if context and context.previous_queries:
            # Check if this is a follow-up query
            last_query = context.previous_queries[-1].lower() if context.previous_queries else ""
            if any(word in query_lower for word in ["that", "those", "them", "it"]) and "department" in last_query:
                # This is likely a follow-up about the same department
                pass
        
        # Use existing pattern logic but enhanced
        for pattern_type, patterns in self.hr_domain_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                if pattern_type == "leave_queries":
                    entities = {"leave_pattern": "maximum", "aggregation_type": "count"}
                    return QueryIntent(
                        query_type=QueryType.ANALYTICS,
                        data_source=DataSource.MONGODB,
                        confidence=0.8,
                        extracted_entities=entities,
                        context=context
                    )
        
        # Default to text search
        return QueryIntent(
            query_type=QueryType.TEXT_SEARCH,
            data_source=DataSource.AZURE_SEARCH,
            confidence=0.6,
            extracted_entities={},
            context=context
        )
    
    async def _execute_query_with_fallback(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute query with enhanced error handling and optimization"""
        try:
            if intent.data_source == DataSource.MONGODB:
                return await self._execute_mongodb_query_enhanced(query, intent)
            elif intent.data_source == DataSource.AZURE_SEARCH:
                return await self._execute_azure_search_query(query, intent)
            else:  # HYBRID
                return await self._execute_hybrid_query(query, intent)
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            return QueryResult(
                data=[],
                count=0,
                metadata={"error": str(e)},
                source=intent.data_source,
                execution_time_ms=0
            )
    
    async def _execute_mongodb_query_enhanced(self, query: str, intent: QueryIntent) -> QueryResult:
        """Enhanced MongoDB execution with optimization"""
        start_time = time.time()
        
        try:
            await mongodb_client.connect()
            
            # Build optimized aggregation pipeline
            pipeline = self._build_optimized_pipeline(intent)
            
            # Execute with proper error handling
            if intent.query_type == QueryType.ANALYTICS:
                results = await self._execute_analytics_pipeline_enhanced(pipeline, intent)
            else:
                results = await self._execute_filter_pipeline_enhanced(pipeline, intent)
            
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                data=results.get("data", []),
                count=results.get("count", 0),
                metadata=results.get("metadata", {}),
                source=DataSource.MONGODB,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            print(f"❌ Enhanced MongoDB query failed: {e}")
            return QueryResult(
                data=[], count=0, metadata={"error": str(e)}, 
                source=DataSource.MONGODB, execution_time_ms=0
            )
    
    def _build_optimized_pipeline(self, intent: QueryIntent) -> List[Dict[str, Any]]:
        """Build optimized MongoDB aggregation pipeline"""
        pipeline = []
        entities = intent.extracted_entities
        
        # Optimized lookup strategy - only join needed collections
        needed_collections = self._determine_needed_collections(entities)
        
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
        
        # Add field conversion and filtering
        pipeline.extend(self._build_filter_and_conversion_stages(entities))
        
        return pipeline
    
    def _determine_needed_collections(self, entities: Dict[str, Any]) -> List[str]:
        """Determine which collections are needed based on entities"""
        collections = ["personal_info"]  # Always need base collection
        
        if entities.get("department") or entities.get("role"):
            collections.append("employment")
        
        if entities.get("performance_level") or entities.get("rating_range"):
            collections.append("performance")
        
        if entities.get("leave_pattern") or entities.get("attendance_level"):
            collections.append("attendance")
        
        if entities.get("skills") or entities.get("certifications"):
            collections.append("learning")
        
        if entities.get("experience_range"):
            collections.append("experience")
        
        if entities.get("current_project"):
            collections.append("engagement")
        
        return collections
    
    def _build_filter_and_conversion_stages(self, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build filter and data conversion stages"""
        stages = []
        
        # Data type conversion stage
        conversion_fields = {}
        if "attendance" in self._determine_needed_collections(entities):
            conversion_fields["attendance.leave_days_taken_num"] = {
                "$toInt": {"$ifNull": [{"$toInt": "$attendance.leave_days_taken"}, 0]}
            }
        
        if "performance" in self._determine_needed_collections(entities):
            conversion_fields["performance.performance_rating_num"] = {
                "$toInt": {"$ifNull": [{"$toInt": "$performance.performance_rating"}, 0]}
            }
        
        if conversion_fields:
            stages.append({"$addFields": conversion_fields})
        
        # Build match conditions
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
        
        if entities.get("leave_pattern"):
            threshold = entities.get("leave_threshold", 20)
            if entities["leave_pattern"] == "maximum":
                match_conditions["attendance.leave_days_taken_num"] = {"$gte": threshold}
            elif entities["leave_pattern"] == "minimum":
                match_conditions["attendance.leave_days_taken_num"] = {"$lte": 5}
        
        if match_conditions:
            stages.append({"$match": match_conditions})
        
        return stages
    
    async def _execute_analytics_pipeline_enhanced(self, pipeline: List[Dict[str, Any]], intent: QueryIntent) -> Dict[str, Any]:
        """Enhanced analytics pipeline execution"""
        try:
            entities = intent.extracted_entities
            collection = await mongodb_client.get_collection("personal_info")
            
            # Add aggregation stage based on type
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
                pipeline.append({"$count": "total"})
            
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
            entities = intent.extracted_entities
            collection = await mongodb_client.get_collection("personal_info")
            
            # Add projection stage
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "location": 1,
                    "performance_rating": "$performance.performance_rating_num",
                    "leave_days_taken": "$attendance.leave_days_taken_num",
                    "engagement_score": "$engagement.engagement_score",
                    "certifications": "$learning.certifications",
                    "current_project": "$engagement.current_project"
                }
            })
            
            # Add limit if specified
            if entities.get("limit"):
                pipeline.append({"$limit": entities["limit"]})
            else:
                pipeline.append({"$limit": 100})  # Default limit for performance
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return {
                "data": results,
                "count": len(results),
                "metadata": {"filter_type": "documents"}
            }
            
        except Exception as e:
            print(f"❌ Filter pipeline failed: {e}")
            return {"data": [], "count": 0, "metadata": {"error": str(e)}}
    
    async def _execute_azure_search_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute text search queries using Azure Search with optimization"""
        start_time = time.time()
        
        try:
            # Use semantic search for better results
            search_results = azure_search_client.hybrid_search(
                query=query,
                query_vector=await self._generate_query_embedding(query),
                top_k=10
            )
            
            execution_time = (time.time() - start_time) * 1000
            
            return QueryResult(
                data=search_results,
                count=len(search_results),
                metadata={"search_type": "hybrid_semantic"},
                source=DataSource.AZURE_SEARCH,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            print(f"❌ Azure Search query failed: {e}")
            return QueryResult(
                data=[], count=0, metadata={"error": str(e)}, 
                source=DataSource.AZURE_SEARCH, execution_time_ms=0
            )
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for query with caching"""
        try:
            response = self.openai_client.embeddings.create(
                input=query.strip(),
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return [0.0] * 1536
    
    async def _execute_hybrid_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """Execute hybrid queries using both MongoDB and Azure Search"""
        if intent.query_type == QueryType.ANALYTICS:
            return await self._execute_mongodb_query_enhanced(query, intent)
        else:
            return await self._execute_azure_search_query(query, intent)
    
    async def _generate_intelligent_response(self, query: str, intent: QueryIntent, result: QueryResult) -> str:
        """Generate intelligent natural language response with context awareness"""
        
        # Enhanced system prompt with context awareness
        system_prompt = """You are an expert HR assistant with deep knowledge of employee data and HR processes. 
        Generate natural, helpful, and contextually appropriate responses to HR queries.

        Guidelines:
        - Be conversational and professional
        - Use specific numbers and data points when available
        - Provide actionable insights when possible
        - Format information clearly (use bullet points for lists)
        - Suggest follow-up questions when appropriate
        - Consider the user's role and department if provided
        - Be mindful of data sensitivity and privacy
        
        Response Style:
        - For analytics: Provide clear metrics with context
        - For searches: Summarize findings and highlight key information
        - For comparisons: Present balanced, objective analysis
        - For recommendations: Offer specific, actionable advice"""
        
        # Build enhanced context
        context = {
            "query": query,
            "intent": intent.query_type.value,
            "data_source": intent.data_source.value,
            "count": result.count,
            "has_data": len(result.data) > 0,
            "execution_time": result.execution_time_ms,
            "cache_hit": result.cache_hit
        }
        
        # Add sample data with enhanced formatting
        if result.count > 0 and result.data:
            context["sample_data"] = []
            for emp in result.data[:3]:
                emp_summary = {
                    "name": emp.get("full_name", "Unknown"),
                    "department": emp.get("department", "N/A"),
                    "role": emp.get("role", "N/A"),
                    "location": emp.get("location", "N/A")
                }
                if emp.get("certifications"):
                    emp_summary["skills"] = emp.get("certifications")
                if emp.get("current_project"):
                    emp_summary["project"] = emp.get("current_project")
                context["sample_data"].append(emp_summary)
        
        # Add metadata insights
        if result.metadata:
            context["insights"] = result.metadata
        
        # Add user context if available
        if intent.context:
            context["user_context"] = {
                "department": intent.context.user_department,
                "role": intent.context.user_role
            }
        
        user_prompt = f"""
        Query: "{query}"
        Context: {json.dumps(context, default=str, indent=2)}
        
        Generate a comprehensive, helpful response that addresses the user's query based on the results.
        Make it conversational and include relevant insights or suggestions for follow-up queries.
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
            # Enhanced fallback response
            if intent.query_type == QueryType.ANALYTICS:
                return f"Based on the data analysis, I found {result.count} employees matching your criteria. " + \
                       "This gives you a clear picture of the current workforce distribution."
            elif result.count > 0:
                return f"I found {result.count} employees that match your search. " + \
                       "Here are the key details that might be helpful for your query."
            else:
                return "I couldn't find any employees matching your specific criteria. " + \
                       "You might want to try broadening your search or checking for alternative terms."
    
    async def _fallback_to_simple_engine(self, query: str, start_time: float) -> Dict[str, Any]:
        """Enhanced fallback to HRQueryEngine with better integration"""
        if self.fallback_engine is None:
            return self._error_response(query, "No fallback engine available", start_time)
        
        try:
            print("🔄 Falling back to HRQueryEngine...")
            result = await self.fallback_engine.process_query(query)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Enhanced fallback response format
            return {
                "query": result["query"],
                "intent": result["intent"],
                "entities": result["entities"],
                "data_source": "fallback_engine",
                "results": result.get("search_results", []),
                "count": result.get("count", len(result.get("search_results", []))),
                "response": result["response"],
                "execution_time_ms": execution_time,
                "confidence": 0.7,
                "status": "success_fallback",
                "cache_hit": False,
                "suggestions": self.intelligence_layer.generate_query_suggestions(query),
                "corrections": self.intelligence_layer.suggest_corrections(query),
                "metadata": {
                    "fallback_reason": "Primary engine failed",
                    "fallback_engine": "HRQueryEngine"
                }
            }
            
        except Exception as e:
            return self._error_response(query, f"Both primary and fallback engines failed: {str(e)}", start_time)
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics"""
        return {
            "cache_stats": self.cache.get_stats(),
            "query_analytics": self.analytics.get_performance_summary(),
            "trending_topics": self.analytics.get_trending_topics(hours=24),
            "system_health": {
                "total_queries_processed": len(self.analytics.query_history),
                "cache_hit_rate": self.cache.get_stats()["hit_rate"],
                "average_response_time": sum(q["execution_time"] for q in self.analytics.query_history) / 
                                       len(self.analytics.query_history) if self.analytics.query_history else 0
            }
        }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear the performance cache"""
        cache_size = len(self.cache.cache)
        self.cache.cache.clear()
        self.cache.ttl_map.clear()
        self.cache.hit_count = 0
        self.cache.miss_count = 0
        
        return {
            "message": f"Cache cleared successfully",
            "entries_removed": cache_size
        }
    
    async def warm_up_cache(self, common_queries: List[str]) -> Dict[str, Any]:
        """Warm up cache with common queries"""
        warmed_count = 0
        failed_count = 0
        
        for query in common_queries:
            try:
                await self.process_query(query)
                warmed_count += 1
            except Exception:
                failed_count += 1
        
        return {
            "message": "Cache warm-up completed",
            "warmed_queries": warmed_count,
            "failed_queries": failed_count
        }
    
    def get_query_suggestions_for_user(self, user_context: QueryContext) -> List[str]:
        """Get personalized query suggestions based on user context"""
        suggestions = []
        
        # Department-specific suggestions
        if user_context.user_department:
            dept = user_context.user_department
            suggestions.extend([
                f"How many people work in {dept}?",
                f"Who are the top performers in {dept}?",
                f"What skills are common in {dept}?"
            ])
        
        # Role-specific suggestions
        if user_context.user_role and "manager" in user_context.user_role.lower():
            suggestions.extend([
                "Show me my team members",
                "Who needs performance reviews?",
                "What training is available?"
            ])
        
        # History-based suggestions
        if user_context.previous_queries:
            last_query = user_context.previous_queries[-1].lower()
            if "department" in last_query:
                suggestions.append("Show me roles in that department")
            elif "skill" in last_query or "certification" in last_query:
                suggestions.append("Who else has similar skills?")
        
        return suggestions[:5]

# Factory function for easy initialization
def create_enhanced_query_engine() -> EnhancedIntelligentQueryEngine:
    """Factory function to create and initialize the enhanced query engine"""
    try:
        engine = EnhancedIntelligentQueryEngine()
        print("✅ Enhanced Intelligent Query Engine initialized successfully")
        return engine
    except Exception as e:
        print(f"❌ Failed to initialize Enhanced Query Engine: {e}")
        raise

# Global instance with error handling
try:
    enhanced_query_engine = create_enhanced_query_engine()
except Exception as e:
    print(f"❌ Global Enhanced Query Engine initialization failed: {e}")
    enhanced_query_engine = None

async def debug_mongodb_data():
    """Debug what's actually in MongoDB"""
    print("\n🔍 DEBUG: Checking MongoDB Data")
    print("=" * 40)
    
    try:
        await mongodb_client.connect()
        
        # Test 1: Count all employees in personal_info
        personal_collection = await mongodb_client.get_collection("personal_info")
        total_count = await personal_collection.count_documents({})
        print(f"📊 Total employees in personal_info: {total_count}")
        
        # Test 2: Count employees in IT department
        employment_collection = await mongodb_client.get_collection("employment")
        it_count = await employment_collection.count_documents({"department": "IT"})
        print(f"🏢 Employees in IT department: {it_count}")
        
        # Test 3: Count developers
        dev_count = await employment_collection.count_documents({"role": "Developer"})
        print(f"💻 Developers total: {dev_count}")
        
        # Test 4: Count developers in IT
        it_dev_count = await employment_collection.count_documents({
            "department": "IT", 
            "role": "Developer"
        })
        print(f"🎯 Developers in IT: {it_dev_count}")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")


# Example usage and testing functions
async def demo_enhanced_features():
    """Demonstrate enhanced features of the query engine"""
    if enhanced_query_engine is None:
        print("❌ Enhanced query engine not available")
        return
    
    print("🚀 Enhanced Query Engine Demo")
    print("=" * 50)
    
    # Create sample context
    context = QueryContext(
        user_id="user123",
        user_department="IT",
        user_role="Manager",
        previous_queries=["find developers", "python certification"]
    )
    
    # Demo queries
    demo_queries = [
        "How many devs work in IT?",  # Will be expanded
        "Find employes with python skills",  # Will be corrected
        "Who are our top performers?",  # Context-aware
        "Show me analytics for my team"  # Personalized
    ]
    
    for query in demo_queries:
        print(f"\n🔍 Query: '{query}'")
        result = await enhanced_query_engine.process_query(query, context)
        
        print(f"   🎯 Intent: {result['intent']}")
        print(f"   📊 Results: {result['count']}")
        print(f"   ⚡ Cache Hit: {result['cache_hit']}")
        print(f"   ⏱️  Time: {result['execution_time_ms']:.1f}ms")
        
        if result['corrections']:
            print(f"   📝 Corrections: {result['corrections']}")
        
        if result['suggestions']:
            print(f"   💡 Suggestions: {result['suggestions'][:2]}")
        
        print(f"   💬 Response: {result['response'][:100]}...")
        print("-" * 50)
    
    # Show analytics
    analytics = enhanced_query_engine.get_performance_analytics()
    print(f"\n📈 Performance Analytics:")
    print(f"   Cache Hit Rate: {analytics['cache_stats']['hit_rate']:.1f}%")
    print(f"   Total Queries: {analytics['query_analytics']['total_queries']}")
    print(f"   Trending: {analytics['trending_topics'][:3]}")

if __name__ == "__main__":
    #asyncio.run(demo_enhanced_features())
    asyncio.run(debug_mongodb_data())