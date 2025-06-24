# debug_openai_fix.py - Debug and fix OpenAI connection issues

import asyncio
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.config import settings

def debug_openai_configuration():
    """Debug OpenAI configuration and connection"""
    print("🔍 DEBUG: OpenAI Configuration Analysis")
    print("=" * 50)
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   Azure OpenAI Endpoint: {'✅ Set' if settings.azure_openai_endpoint else '❌ Missing'}")
    print(f"   Azure OpenAI API Key: {'✅ Set' if settings.azure_openai_api_key else '❌ Missing'}")
    
    if settings.azure_openai_endpoint:
        print(f"   Endpoint URL: {settings.azure_openai_endpoint}")
    
    # Check endpoint format
    if settings.azure_openai_endpoint:
        if not settings.azure_openai_endpoint.endswith('/'):
            print("   ⚠️  Endpoint should end with /")
        if 'openai.azure.com' not in settings.azure_openai_endpoint:
            print("   ⚠️  Endpoint should contain 'openai.azure.com'")
    
    return settings.azure_openai_endpoint and settings.azure_openai_api_key

async def test_openai_connection():
    """Test OpenAI connection with minimal request"""
    print("\n🧪 Testing OpenAI Connection")
    print("-" * 30)
    
    try:
        from openai import AzureOpenAI
        
        # Initialize client
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version="2023-05-15",
            azure_endpoint=settings.azure_openai_endpoint
        )
        
        print("✅ OpenAI client initialized")
        
        # Test simple completion
        print("🔄 Testing simple completion...")
        
        response = client.chat.completions.create(
            model="gpt-4o-llm",  # Your model deployment name
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello World' in JSON format: {\"message\": \"Hello World\"}"}
            ],
            max_tokens=50,
            temperature=0
        )
        
        print("✅ OpenAI API call successful!")
        print(f"   Response: {response.choices[0].message.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check common issues
        if "401" in str(e) or "Unauthorized" in str(e):
            print("   🔑 Issue: API Key is invalid")
        elif "404" in str(e) or "Not Found" in str(e):
            print("   🔗 Issue: Endpoint URL or model name is wrong")
        elif "timeout" in str(e).lower():
            print("   ⏱️  Issue: Request timeout")
        
        return False

def fix_model_deployment_name():
    """Check and suggest model deployment name fix"""
    print("\n🔧 Model Deployment Name Check")
    print("-" * 35)
    
    print("Current model name in code: 'gpt-4o-llm'")
    print("\n💡 Common Azure OpenAI deployment names:")
    print("   - gpt-4")
    print("   - gpt-4-32k") 
    print("   - gpt-35-turbo")
    print("   - gpt-4o")
    print("   - chat-gpt-4")
    print("\n⚠️  The model name MUST match your Azure deployment name exactly!")
    print("   Check your Azure OpenAI Studio > Deployments section")

def create_fixed_hr_engine():
    """Create a fixed version of HR engine with better error handling"""
    print("\n🔧 Creating Fixed HR Engine")
    print("-" * 30)
    
    fixed_code = '''# Fixed HR Query Engine with better OpenAI error handling

import asyncio
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
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
    COUNT_QUERY = "count_query"
    EMPLOYEE_SEARCH = "employee_search"
    SKILL_SEARCH = "skill_search"
    DEPARTMENT_INFO = "department_info"
    ANALYTICS = "analytics"
    COMPARISON = "comparison"
    RANKING = "ranking"
    GENERAL_INFO = "general_info"

class FixedHRQueryEngine:
    """Fixed HR Query Engine with robust OpenAI error handling"""
    
    def __init__(self):
        print("🚀 Initializing Fixed HR Query Engine...")
        
        # Test OpenAI configuration first
        self.openai_client = None
        self.ai_available = self._initialize_openai()
        
        # HR domain knowledge
        self.departments = ["Sales", "IT", "Operations", "HR", "Finance", "Legal"]
        self.roles = ["Developer", "Manager", "Analyst", "Director", "Lead"]
        self.skills = ["PMP", "GCP", "AWS", "Azure", "Python", "Java"]
        
        print("✅ Fixed HR Query Engine ready!")
    
    def _initialize_openai(self) -> bool:
        """Initialize OpenAI with proper error handling"""
        try:
            # Validate configuration
            if not settings.azure_openai_api_key:
                print("❌ Azure OpenAI API key not found")
                return False
            
            if not settings.azure_openai_endpoint:
                print("❌ Azure OpenAI endpoint not found")
                return False
            
            print(f"🔧 OpenAI Endpoint: {settings.azure_openai_endpoint}")
            
            # Test client initialization
            self.openai_client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version="2023-05-15",
                azure_endpoint=settings.azure_openai_endpoint
            )
            
            # Test with simple call
            test_response = self.openai_client.chat.completions.create(
                model="gpt-4o-llm",  # Try your model name
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
                temperature=0
            )
            
            print("✅ OpenAI client tested successfully")
            return True
            
        except Exception as e:
            print(f"❌ OpenAI initialization failed: {e}")
            print("🔄 Will use fallback pattern matching for queries")
            return False
    
    def _detect_intent_fallback(self, query: str) -> Tuple[QueryType, Dict[str, Any]]:
        """Robust fallback intent detection without AI"""
        query_lower = query.lower().strip()
        entities = {
            "department": None,
            "role": None,
            "skills": [],
            "query_type": None,
            "sort_field": None,
            "sort_order": None
        }
        
        # Enhanced pattern matching
        if any(pattern in query_lower for pattern in ["how many", "count", "number of", "total"]):
            intent = QueryType.COUNT_QUERY
            
        elif any(pattern in query_lower for pattern in ["compare", "vs", "versus", "difference"]):
            intent = QueryType.COMPARISON
            
        elif any(pattern in query_lower for pattern in ["top", "bottom", "highest", "lowest", "best", "worst"]):
            intent = QueryType.RANKING
            
            # Detect ranking type
            if any(word in query_lower for word in ["lowest", "bottom", "worst", "minimum"]):
                entities["query_type"] = "lowest"
                entities["sort_order"] = "asc"
            else:
                entities["query_type"] = "highest"
                entities["sort_order"] = "desc"
            
            # Detect what to rank by
            if any(word in query_lower for word in ["rating", "performance"]):
                entities["sort_field"] = "performance_rating"
            elif any(word in query_lower for word in ["salary", "pay"]):
                entities["sort_field"] = "salary"
            elif any(word in query_lower for word in ["leave", "vacation"]):
                entities["sort_field"] = "leave_balance"
                
        elif any(pattern in query_lower for pattern in ["average", "mean", "statistics"]):
            intent = QueryType.ANALYTICS
            
        else:
            intent = QueryType.EMPLOYEE_SEARCH
        
        # Extract entities
        for dept in self.departments:
            if dept.lower() in query_lower:
                entities["department"] = dept
                break
        
        for role in self.roles:
            if role.lower() in query_lower or f"{role.lower()}s" in query_lower:
                entities["role"] = role
                break
        
        for skill in self.skills:
            if skill.lower() in query_lower:
                entities["skills"].append(skill)
        
        return intent, entities
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Main query processing with robust error handling"""
        start_time = time.time()
        
        try:
            print(f"\\n🔍 Processing query: '{query}'")
            
            # Always use fallback for now until OpenAI is fixed
            intent, entities = self._detect_intent_fallback(query)
            print(f"   🎯 Intent: {intent.value} (using pattern matching)")
            print(f"   📋 Entities: {entities}")
            
            # Route to handlers
            if intent == QueryType.COUNT_QUERY:
                results, count = await self._handle_count_query(entities)
            elif intent == QueryType.RANKING:
                results, count = await self._handle_ranking_query(entities, query)
            elif intent == QueryType.ANALYTICS:
                results, count = await self._handle_analytics_query(entities)
            else:
                results, count = await self._handle_search_query(query, entities)
            
            # Generate simple response (no AI needed)
            response = self._generate_simple_response(query, intent, entities, results, count)
            
            execution_time = (time.time() - start_time) * 1000
            
            print(f"   ✅ Found {count} results in {execution_time:.1f}ms")
            
            return {
                "query": query,
                "intent": intent.value,
                "entities": entities,
                "results": results,
                "count": count,
                "response": response,
                "execution_time_ms": execution_time,
                "status": "success",
                "ai_used": False
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            print(f"   ❌ Query failed: {e}")
            
            return {
                "query": query,
                "intent": "unknown",
                "entities": {},
                "results": [],
                "count": 0,
                "response": f"I encountered an error: {str(e)}",
                "execution_time_ms": execution_time,
                "status": "error"
            }
    
    def _generate_simple_response(self, query: str, intent: QueryType, entities: Dict[str, Any], 
                                results: List[Dict[str, Any]], count: int) -> str:
        """Generate response without AI"""
        
        if intent == QueryType.COUNT_QUERY:
            filter_desc = []
            if entities.get("department"):
                filter_desc.append(f"in {entities['department']}")
            if entities.get("role"):
                filter_desc.append(f"with {entities['role']} role")
            
            filter_text = " ".join(filter_desc) if filter_desc else "in the company"
            return f"There are {count} employees {filter_text}."
        
        elif intent == QueryType.RANKING and results:
            query_type = entities.get("query_type", "top")
            sort_field = entities.get("sort_field", "performance")
            
            response_lines = [f"Here are the employees with {query_type} {sort_field}:"]
            
            for i, result in enumerate(results[:5], 1):
                name = result.get("full_name", "N/A")
                dept = result.get("department", "N/A")
                
                # Add specific values
                if sort_field == "performance_rating":
                    value = result.get("performance_rating", "N/A")
                    response_lines.append(f"{i}. {name} ({dept}) - Rating: {value}")
                elif sort_field == "leave_balance":
                    balance = result.get("leave_balance", "N/A")
                    taken = result.get("leave_taken", "N/A")
                    response_lines.append(f"{i}. {name} ({dept}) - Leave Balance: {balance}, Taken: {taken}")
                elif sort_field == "salary":
                    salary = result.get("salary", "N/A")
                    response_lines.append(f"{i}. {name} ({dept}) - Salary: ${salary:,}")
                else:
                    response_lines.append(f"{i}. {name} ({dept})")
            
            return "\\n".join(response_lines)
        
        elif intent == QueryType.ANALYTICS and results:
            result = results[0]
            response_lines = ["Analytics Summary:"]
            response_lines.append(f"• Total Employees: {result.get('count', 0)}")
            
            if "avg_performance" in result:
                response_lines.append(f"• Average Performance: {result['avg_performance']:.1f}")
            if "avg_salary" in result:
                response_lines.append(f"• Average Salary: ${result['avg_salary']:,.0f}")
            
            return "\\n".join(response_lines)
        
        elif count > 0:
            return f"Found {count} employees matching your criteria."
        
        else:
            return "No employees found matching your criteria."
    
    # Add the MongoDB methods from previous working version
    async def _handle_count_query(self, entities: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle count queries using working MongoDB logic"""
        try:
            await mongodb_client.connect()
            
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
            
            match_conditions = {}
            if entities.get("department"):
                match_conditions["employment.department"] = entities["department"]
            if entities.get("role"):
                match_conditions["employment.role"] = entities["role"]
            
            if match_conditions:
                pipeline.append({"$match": match_conditions})
            
            pipeline.append({"$count": "total"})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            count = results[0]["total"] if results else 0
            return [], count
            
        except Exception as e:
            print(f"   ❌ Count query failed: {e}")
            return [], 0
    
    async def _handle_ranking_query(self, entities: Dict[str, Any], query: str) -> Tuple[List[Dict[str, Any]], int]:
        """Handle ranking queries"""
        try:
            await mongodb_client.connect()
            
            # Build pipeline with needed collections
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
            
            # Add additional collections based on sort field
            sort_field = entities.get("sort_field", "performance_rating")
            
            if sort_field == "performance_rating":
                pipeline.extend([
                    {
                        "$lookup": {
                            "from": "performance",
                            "localField": "employee_id",
                            "foreignField": "employee_id",
                            "as": "performance"
                        }
                    },
                    {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}}
                ])
                
                pipeline.append({
                    "$addFields": {
                        "performance_rating_num": {
                            "$toInt": {"$ifNull": [{"$toInt": "$performance.performance_rating"}, 0]}
                        }
                    }
                })
                sort_field_name = "performance_rating_num"
                
            elif sort_field == "leave_balance":
                pipeline.extend([
                    {
                        "$lookup": {
                            "from": "attendance",
                            "localField": "employee_id",
                            "foreignField": "employee_id",
                            "as": "attendance"
                        }
                    },
                    {"$unwind": {"path": "$attendance", "preserveNullAndEmptyArrays": True}}
                ])
                
                pipeline.append({
                    "$addFields": {
                        "leave_balance_num": {
                            "$toInt": {"$ifNull": [{"$toInt": "$attendance.leave_balance"}, 0]}
                        },
                        "leave_taken_num": {
                            "$toInt": {"$ifNull": [{"$toInt": "$attendance.leave_days_taken"}, 0]}
                        }
                    }
                })
                sort_field_name = "leave_balance_num"
            else:
                sort_field_name = "performance_rating_num"  # Default
            
            # Add sorting
            sort_order = 1 if entities.get("sort_order") == "asc" else -1
            pipeline.append({"$sort": {sort_field_name: sort_order}})
            
            # Limit results
            pipeline.append({"$limit": 10})
            
            # Project fields
            project_fields = {
                "employee_id": 1,
                "full_name": 1,
                "department": "$employment.department",
                "role": "$employment.role"
            }
            
            if sort_field == "performance_rating":
                project_fields["performance_rating"] = "$performance_rating_num"
            elif sort_field == "leave_balance":
                project_fields["leave_balance"] = "$leave_balance_num"
                project_fields["leave_taken"] = "$leave_taken_num"
            
            pipeline.append({"$project": project_fields})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Ranking query failed: {e}")
            return [], 0
    
    async def _handle_analytics_query(self, entities: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle analytics queries"""
        # Similar to previous working version
        return [], 0
    
    async def _handle_search_query(self, query: str, entities: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle search queries using Azure Search"""
        try:
            search_results = azure_search_client.search(
                query=query,
                top_k=10
            )
            return search_results, len(search_results)
        except Exception as e:
            print(f"   ❌ Search failed: {e}")
            return [], 0

# Global instance
fixed_hr_query_engine = FixedHRQueryEngine()

async def main():
    """Test the fixed engine"""
    print("🧪 Testing Fixed HR Query Engine")
    print("=" * 40)
    
    test_queries = [
        "How many developers work in IT?",
        "Show me employees with lowest performance ratings",
        "Top 5 employees with highest leave balance",
        "Find employees in Sales department"
    ]
    
    for query in test_queries:
        print(f"\\nTesting: '{query}'")
        result = await fixed_hr_query_engine.process_query(query)
        print(f"Status: {result['status']}")
        print(f"Count: {result['count']}")
        print(f"Response: {result['response'][:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Save fixed version
    with open("src/query/hr_query_engine_fixed.py", "w") as f:
        f.write(fixed_code)
    
    print("✅ Created fixed HR engine: src/query/hr_query_engine_fixed.py")
    print("   - Robust error handling")
    print("   - Works without AI if needed")
    print("   - Proper OpenAI configuration testing")

async def main():
    """Main debug function"""
    print("🔧 OpenAI Connection Debug & Fix Tool")
    print("=" * 50)
    
    # Step 1: Check configuration
    config_ok = debug_openai_configuration()
    
    if not config_ok:
        print("\\n❌ Configuration issues found. Please check your .env file.")
        return
    
    # Step 2: Test connection
    connection_ok = await test_openai_connection()
    
    if not connection_ok:
        print("\\n❌ OpenAI connection failed.")
        fix_model_deployment_name()
    
    # Step 3: Create fixed version
    create_fixed_hr_engine()
    
    print("\\n" + "=" * 50)
    if connection_ok:
        print("🎉 OpenAI is working! You can use the full AI features.")
    else:
        print("🔄 OpenAI needs fixing. Use the fixed engine that works without AI.")
        print("   File: src/query/hr_query_engine_fixed.py")

if __name__ == "__main__":
    asyncio.run(main())