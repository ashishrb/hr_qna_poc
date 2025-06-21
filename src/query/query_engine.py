# src/query/updated_query_engine.py
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings

class QueryType(Enum):
    EMPLOYEE_SEARCH = "employee_search"
    SKILL_SEARCH = "skill_search"
    DEPARTMENT_INFO = "department_info"
    GENERAL_INFO = "general_info"
    COUNT_QUERY = "count_query"
    COMPARISON = "comparison"
    UNKNOWN = "unknown"

class UpdatedHRQueryEngine:
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version="2023-05-15",
            azure_endpoint=settings.azure_openai_endpoint
        )
        self.search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="hr-employees-fixed",  # Updated to use the fixed index
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
    
    def detect_intent(self, query: str) -> Tuple[QueryType, Dict[str, Any]]:
        """Detect the intent and extract entities from the query"""
        query_lower = query.lower()
        
        # Intent detection patterns - more specific patterns first
        if any(pattern in query_lower for pattern in ["how many", "count", "number of", "total"]):
            intent = QueryType.COUNT_QUERY
        elif any(pattern in query_lower for pattern in ["find", "search", "show me", "who are", "list"]):
            if any(skill in query_lower for skill in ["python", "java", "javascript", "aws", "azure", "sql", "react", "pmp", "gcp", "certification"]):
                intent = QueryType.SKILL_SEARCH
            else:
                intent = QueryType.EMPLOYEE_SEARCH
        elif any(pattern in query_lower for pattern in ["department", "team", "division"]):
            intent = QueryType.DEPARTMENT_INFO
        elif any(pattern in query_lower for pattern in ["who is", "tell me about", "information about"]):
            intent = QueryType.EMPLOYEE_SEARCH
        else:
            intent = QueryType.GENERAL_INFO
        
        # Extract entities based on actual data
        entities = {
            "employee_name": None,
            "skills": [],
            "department": None,
            "location": None,
            "position": None
        }
        
        # Enhanced entity extraction based on actual data
        departments = ["Sales", "IT", "Operations", "HR", "Finance", "Legal", "Engineering", "Marketing"]
        locations = ["Offshore", "Onshore", "Remote", "Chennai", "Hyderabad", "New York", "California", "India"]
        skills = ["PMP", "GCP", "AWS", "Azure", "Python", "Java", "JavaScript", "SQL", "Docker", "Kubernetes"]
        positions = ["Developer", "Director", "Manager", "Analyst", "Engineer", "Lead", "Senior"]
        
        for dept in departments:
            if f" {dept.lower()}" in f" {query_lower}" or f"{dept.lower()} " in f"{query_lower} ":
                entities["department"] = dept  # Keep original case
                break
        
        for loc in locations:
            if f" {loc.lower()}" in f" {query_lower}" or f"{loc.lower()} " in f"{query_lower} ":
                entities["location"] = loc  # Keep original case
                break
        
        for skill in skills:
            if f" {skill.lower()}" in f" {query_lower}" or f"{skill.lower()} " in f"{query_lower} ":
                entities["skills"].append(skill)  # Keep original case
        
        for pos in positions:
            if f" {pos.lower()}" in f" {query_lower}" or f"{pos.lower()} " in f"{query_lower} ":
                entities["position"] = pos  # Keep original case
                break
        
        return intent, entities
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text"""
        try:
            clean_text = text.strip().replace('\n', ' ').replace('\r', '')
            if not clean_text:
                return [0.0] * 1536
            
            response = self.openai_client.embeddings.create(
                input=clean_text,
                model="text-embedding-ada-002"
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"❌ Failed to generate embedding: {e}")
            return [0.0] * 1536
    
    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform semantic search using vector embeddings"""
        try:
            query_embedding = self.generate_embedding(query)
            
            results = self.search_client.search(
                search_text=None,
                vector_queries=[{
                    "kind": "vector",
                    "vector": query_embedding,
                    "fields": "content_vector",
                    "k": top_k
                }],
                select="id,full_name,department,role,location,certifications,combined_text,current_project",
                top=top_k
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    'id': result['id'],
                    'full_name': result.get('full_name', ''),
                    'department': result.get('department', ''),
                    'role': result.get('role', ''),  # This is position
                    'location': result.get('location', ''),
                    'certifications': result.get('certifications', ''),  # This is skills
                    'combined_text': result.get('combined_text', ''),
                    'current_project': result.get('current_project', ''),
                    'score': result.get('@search.score', 0)
                })
            
            return search_results
            
        except Exception as e:
            print(f"❌ Semantic search failed: {e}")
            return []
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform hybrid search combining text and vector search"""
        try:
            query_embedding = self.generate_embedding(query)
            
            results = self.search_client.search(
                search_text=query,
                vector_queries=[{
                    "kind": "vector",
                    "vector": query_embedding,
                    "fields": "content_vector",
                    "k": top_k
                }],
                select="id,full_name,department,role,location,certifications,combined_text,current_project,total_experience_years,performance_rating",
                top=top_k,
                query_type="semantic",
                semantic_configuration_name="hr-semantic-config"
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    'id': result['id'],
                    'full_name': result.get('full_name', ''),
                    'department': result.get('department', ''),
                    'role': result.get('role', ''),
                    'location': result.get('location', ''),
                    'certifications': result.get('certifications', ''),
                    'combined_text': result.get('combined_text', ''),
                    'current_project': result.get('current_project', ''),
                    'total_experience_years': result.get('total_experience_years', 0),
                    'performance_rating': result.get('performance_rating', 0),
                    'score': result.get('@search.score', 0),
                    'reranker_score': result.get('@search.reranker_score', 0)
                })
            
            return search_results
            
        except Exception as e:
            print(f"❌ Hybrid search failed: {e}")
            return []
    
    def normalize_search_query(self, query: str) -> str:
        """Normalize search query to handle plural/singular forms"""
        query_normalized = query.lower()
        
        # Common plural to singular conversions
        plural_mappings = {
            'developers': 'developer',
            'directors': 'director', 
            'managers': 'manager',
            'analysts': 'analyst',
            'engineers': 'engineer',
            'leads': 'lead'
        }
        
        for plural, singular in plural_mappings.items():
            if plural in query_normalized:
                query_normalized = query_normalized.replace(plural, singular)
        
        return query_normalized
    
    async def search_employees(self, query: str, filters: Dict[str, Any] = None, top_k: int = 5, intent: QueryType = None) -> List[Dict[str, Any]]:
        """Search for employees using text search with optional filters"""
        try:
            # Normalize the query to handle plural forms
            normalized_query = self.normalize_search_query(query)
            
            # Build filter string based on actual field names
            filter_parts = []
            # Only apply department and location filters, not position filters for searches
            if filters and intent not in [QueryType.SKILL_SEARCH, QueryType.EMPLOYEE_SEARCH]:
                if filters.get("department"):
                    filter_parts.append(f"department eq '{filters['department']}'")
                if filters.get("location"):
                    filter_parts.append(f"location eq '{filters['location']}'")
            
            filter_string = " and ".join(filter_parts) if filter_parts else None
            
            # Use normalized query for search
            results = self.search_client.search(
                search_text=normalized_query,
                filter=filter_string,
                select="id,full_name,department,role,location,certifications,combined_text,current_project,total_experience_years,performance_rating",
                top=top_k
            )
            
            search_results = []
            for result in results:
                search_results.append({
                    'id': result['id'],
                    'full_name': result.get('full_name', ''),
                    'department': result.get('department', ''),
                    'role': result.get('role', ''),
                    'location': result.get('location', ''),
                    'certifications': result.get('certifications', ''),
                    'combined_text': result.get('combined_text', ''),
                    'current_project': result.get('current_project', ''),
                    'total_experience_years': result.get('total_experience_years', 0),
                    'performance_rating': result.get('performance_rating', 0),
                    'score': result.get('@search.score', 0)
                })
            
            return search_results
            
        except Exception as e:
            print(f"❌ Employee search failed: {e}")
            return []
    
    def count_employees(self, filters: Dict[str, Any] = None) -> int:
        """Count employees matching criteria"""
        try:
            filter_parts = []
            if filters:
                if filters.get("department"):
                    filter_parts.append(f"department eq '{filters['department']}'")
                if filters.get("location"):
                    filter_parts.append(f"location eq '{filters['location']}'")
                if filters.get("position"):
                    filter_parts.append(f"role eq '{filters['position']}'")
            
            filter_string = " and ".join(filter_parts) if filter_parts else None
            
            results = self.search_client.search(
                "*",
                filter=filter_string,
                include_total_count=True,
                top=0
            )
            
            return results.get_count()
            
        except Exception as e:
            print(f"❌ Count query failed: {e}")
            return 0
    
    def generate_response(self, query: str, intent: QueryType, entities: Dict[str, Any], search_results: List[Dict[str, Any]], count: int = 0) -> str:
        """Generate natural language response using GPT"""
        try:
            # Handle count queries specially
            if intent == QueryType.COUNT_QUERY:
                if count > 0:
                    filter_desc = []
                    if entities.get("department"):
                        filter_desc.append(f"in the {entities['department']} department")
                    if entities.get("location"):
                        filter_desc.append(f"in {entities['location']}")
                    if entities.get("position"):
                        filter_desc.append(f"with {entities['position']} role")
                    
                    filter_text = " ".join(filter_desc) if filter_desc else "in the company"
                    return f"There are {count} employees {filter_text}."
                else:
                    return f"No employees found matching your criteria: {query}"
            
            # Handle empty search results for non-count queries
            if not search_results:
                return f"I couldn't find any employees matching your criteria. You searched for: {query}. Please try a different search or check if the information exists in our system."
            
            context = ""
            if search_results:
                context = "Relevant employee information:\n"
                for i, result in enumerate(search_results[:5], 1):
                    context += f"{i}. {result.get('full_name', 'N/A')} - {result.get('department', 'N/A')} - {result.get('role', 'N/A')}\n"
                    context += f"   Location: {result.get('location', 'N/A')}\n"
                    context += f"   Certifications: {result.get('certifications', 'N/A')}\n"
                    if result.get('current_project'):
                        context += f"   Current Project: {result.get('current_project', 'N/A')}\n"
                    context += "\n"
            
            system_prompt = f"""You are an HR assistant that helps answer questions about employees and company information. 
            Use ONLY the provided employee data to answer questions accurately and professionally.
            
            Guidelines:
            - Be concise but informative
            - If no relevant information is found, clearly state that
            - Only provide information that exists in the data provided
            - Format responses in a readable way
            - Include relevant details like department, role, location, and certifications when appropriate
            - If the search returned empty results, acknowledge that no matches were found
            """
            
            user_prompt = f"""
            Query: {query}
            Intent: {intent.value}
            Entities detected: {entities}
            
            {context if context else "No matching employee data found."}
            
            Please provide a helpful response to the user's query based on the employee information above.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-llm",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Main query processing pipeline"""
        try:
            print(f"🔍 Processing query: '{query}'")
            
            # Step 1: Intent detection
            intent, entities = self.detect_intent(query)
            print(f"   🎯 Intent: {intent.value}")
            print(f"   📋 Entities: {entities}")
            
            # Step 2: Search based on intent
            search_results = []
            count = 0
            
            if intent in [QueryType.EMPLOYEE_SEARCH, QueryType.SKILL_SEARCH, QueryType.DEPARTMENT_INFO, QueryType.GENERAL_INFO]:
                search_results = await self.search_employees(query, entities, top_k=5, intent=intent)
                print(f"   📊 Found {len(search_results)} relevant results")
                
            elif intent == QueryType.COUNT_QUERY:
                count = self.count_employees(entities)
                print(f"   📊 Count: {count}")
            
            # Step 3: Generate response
            response = self.generate_response(query, intent, entities, search_results, count)
            
            result = {
                "query": query,
                "intent": intent.value,
                "entities": entities,
                "search_results": search_results,
                "count": count,
                "response": response,
                "status": "success"
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Query processing failed: {e}")
            return {
                "query": query,
                "intent": "unknown",
                "entities": {},
                "search_results": [],
                "count": 0,
                "response": "I apologize, but I encountered an error processing your query. Please try again.",
                "status": "error",
                "error": str(e)
            }
    
    async def test_query_engine(self):
        """Test the query engine with sample queries"""
        print("\n🧪 Testing Updated Query Engine")
        print("=" * 40)
        
        test_queries = [
            "Who are the developers in our company?",
            "Find employees with PMP certification",
            "How many people work in the Operations department?",
            "Show me directors",
            "Tell me about employees with GCP certification",
            "Who works in the IT department?",
            "Find employees in Operations"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Testing: '{query}'")
            result = await self.process_query(query)
            print(f"   🎯 Intent: {result['intent']}")
            print(f"   📊 Results: {len(result['search_results'])} found")
            print(f"   💬 Response: {result['response'][:150]}...")
            if result['search_results']:
                for emp in result['search_results'][:2]:
                    print(f"     - {emp['full_name']} ({emp['department']}) - {emp['role']}")
            print("-" * 40)

async def main():
    """Main function to test the updated query engine"""
    print("🤖 Updated HR Query Engine Pipeline")
    print("=" * 50)
    
    query_engine = UpdatedHRQueryEngine()
    
    try:
        # Test the query engine
        await query_engine.test_query_engine()
        
        # Interactive testing
        print("\n🎮 Interactive Testing (type 'quit' to exit)")
        print("=" * 50)
        
        while True:
            user_query = input("\n💬 Enter your query: ").strip()
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            
            if user_query:
                result = await query_engine.process_query(user_query)
                print(f"\n🤖 Response: {result['response']}")
                if result['search_results']:
                    print(f"📊 Found employees:")
                    for emp in result['search_results']:
                        print(f"  - {emp['full_name']} ({emp['department']}) - {emp['role']}")
        
        print("\n🎉 Query engine testing completed!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
    except KeyboardInterrupt:
        print("\n👋 Testing stopped by user")

if __name__ == "__main__":
    asyncio.run(main())