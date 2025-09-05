# src/ai/ollama_client.py
"""
Ollama-based AI client to replace Azure OpenAI dependencies
Supports local LLM inference for HR Q&A system
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional, Union
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class OllamaClient:
    """Client for interacting with Ollama models with smart model selection"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.timeout = 30
        self.max_retries = 3
        
        # Model hierarchy for different use cases
        self.model_config = {
            "complex_analytics": [
                "gpt-oss:20B",           # Highest accuracy for complex queries
                "llama3:8b",             # Excellent fallback
                "mistral:7b-instruct-v0.2-q4_K_M"  # Good instruction following
            ],
            "structured_queries": [
                "mistral:7b-instruct-v0.2-q4_K_M",  # Best for structured queries
                "llama3:8b",             # Excellent general performance
                "llama3.2:3b-instruct-q4_K_M"  # Balanced performance
            ],
            "data_calculations": [
                "codellama:7b-instruct-q4_K_M",  # Optimized for data processing
                "qwen2.5-coder:1.5b",    # Fast calculations
                "llama3.2:3b-instruct-q4_K_M"  # General fallback
            ],
            "simple_queries": [
                "qwen2.5-coder:1.5b",   # Fastest response
                "llama3.2:1b-instruct-q4_K_M",  # Lightweight
                "llama3.2:3b-instruct-q4_K_M"  # Balanced
            ],
            "multilingual": [
                "qwen3:latest",          # Multilingual support
                "llama3:8b",             # Good general performance
                "mistral:7b-instruct-v0.2-q4_K_M"  # Instruction following
            ],
            "default": [
                "llama3.2:3b-instruct-q4_K_M",  # Balanced default
                "mistral:7b-instruct-v0.2-q4_K_M",  # Good instruction following
                "llama3:8b"              # High quality fallback
            ]
        }
        
        # Embedding model
        self.embedding_model = "nomic-embed-text:v1.5"
        
        # Available models cache
        self.available_models = []
        
        # Test connection on initialization
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Connected to Ollama server")
                self._check_available_models()
            else:
                print(f"❌ Ollama server returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to Ollama server: {e}")
            print("💡 Make sure Ollama is running: ollama serve")
    
    def _check_available_models(self):
        """Check which models are available and update configuration"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                self.available_models = [model['name'] for model in models]
                
                print(f"📋 Available models: {self.available_models}")
                
                # Validate embedding model
                if not any('nomic-embed' in name for name in self.available_models):
                    print("⚠️ nomic-embed-text not found for embeddings")
                    self.embedding_model = None
                else:
                    # Find the exact embedding model name
                    for model in self.available_models:
                        if 'nomic-embed' in model:
                            self.embedding_model = model
                            break
                
                # Validate model configurations
                self._validate_model_configs()
                    
        except Exception as e:
            print(f"❌ Failed to check available models: {e}")
    
    def _validate_model_configs(self):
        """Validate and update model configurations based on available models"""
        for category, models in self.model_config.items():
            available_in_category = [model for model in models if model in self.available_models]
            if available_in_category:
                print(f"✅ {category}: {available_in_category[0]} (primary)")
            else:
                print(f"⚠️ {category}: No preferred models available")
    
    def select_optimal_model(self, query_type: str = "default", query_complexity: str = "medium") -> str:
        """
        Select the optimal model based on query type and complexity
        
        Args:
            query_type: Type of query (complex_analytics, structured_queries, etc.)
            query_complexity: Complexity level (low, medium, high)
            
        Returns:
            Selected model name
        """
        # Determine model category based on query type and complexity
        if query_complexity == "high" or query_type in ["complex_analytics", "correlation"]:
            category = "complex_analytics"
        elif query_type in ["data_calculations", "analytics"]:
            category = "data_calculations"
        elif query_type in ["simple_queries", "count_query"]:
            category = "simple_queries"
        elif query_type in ["multilingual"]:
            category = "multilingual"
        elif query_type in ["structured_queries", "comparison", "ranking"]:
            category = "structured_queries"
        else:
            category = "default"
        
        # Select first available model in the category
        for model in self.model_config[category]:
            if model in self.available_models:
                print(f"🎯 Selected {model} for {category} ({query_type})")
                return model
        
        # Fallback to any available model
        if self.available_models:
            fallback = self.available_models[0]
            print(f"⚠️ Using fallback model: {fallback}")
            return fallback
        
        # Last resort
        return "llama3.2:3b"
    
    def _validate_response(self, response: str, query_type: str) -> bool:
        """Validate response quality based on query type"""
        if not response or len(response.strip()) < 10:
            return False
        
        # Check for error indicators
        error_indicators = ["❌", "error", "failed", "unable to", "cannot"]
        if any(indicator in response.lower() for indicator in error_indicators):
            return False
        
        # Check for appropriate content based on query type
        if query_type == "complex_analytics":
            # Should contain structured data or analysis
            return any(keyword in response.lower() for keyword in 
                      ["analysis", "insights", "recommendations", "summary", "findings"])
        elif query_type == "structured_queries":
            # Should contain structured information
            return any(keyword in response.lower() for keyword in 
                      ["employee", "department", "performance", "salary", "data"])
        
        return True
    
    def _get_fallback_model(self, current_model: str, query_type: str) -> Optional[str]:
        """Get a fallback model for the given query type"""
        try:
            model_list = self.model_config.get(query_type, self.model_config["default"])
            current_index = model_list.index(current_model)
            if current_index < len(model_list) - 1:
                return model_list[current_index + 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def generate_text(self, 
                     prompt: str, 
                     model: Optional[str] = None,
                     max_tokens: int = 500,
                     temperature: float = 0.3,
                     system_prompt: Optional[str] = None,
                     query_type: str = "default",
                     query_complexity: str = "medium") -> str:
        """
        Generate text using Ollama model with smart model selection
        
        Args:
            prompt: User prompt
            model: Model name (optional, will auto-select if not provided)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: System prompt (optional)
            query_type: Type of query for model selection
            query_complexity: Complexity level for model selection
            
        Returns:
            Generated text
        """
        # Smart model selection if no model specified
        if not model:
            model = self.select_optimal_model(query_type, query_complexity)
        
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request payload
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            # Make request with retries
            for attempt in range(self.max_retries):
                try:
                    response = requests.post(
                        f"{self.base_url}/api/chat",
                        json=payload,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        generated_text = result['message']['content'].strip()
                        
                        # Validate response quality
                        if self._validate_response(generated_text, query_type):
                            print(f"✅ Generated response using {model} (attempt {attempt + 1})")
                            return generated_text
                        else:
                            print(f"⚠️ Low quality response from {model}, trying fallback...")
                            if attempt < self.max_retries - 1:
                                # Try with a different model
                                fallback_model = self._get_fallback_model(model, query_type)
                                if fallback_model:
                                    payload["model"] = fallback_model
                                    continue
                        
                        return generated_text  # Return even if validation fails
                    else:
                        print(f"❌ Ollama API error (attempt {attempt + 1}): {response.status_code}")
                        if attempt < self.max_retries - 1:
                            time.sleep(1)
                        
                except requests.exceptions.Timeout:
                    print(f"⏰ Request timeout (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(2)
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ Request error (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
            
            return "I apologize, but I'm unable to process your request at the moment."
            
        except Exception as e:
            print(f"❌ Text generation failed: {e}")
            return "I encountered an error while processing your request."
    
    def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Input text
            model: Embedding model name (optional)
            
        Returns:
            Embedding vector
        """
        model = model or self.embedding_model
        
        if not model:
            print("⚠️ No embedding model available")
            return [0.0] * 384  # Return zero vector
        
        try:
            payload = {
                "model": model,
                "prompt": text
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['embedding']
            else:
                print(f"❌ Embedding generation failed: {response.status_code}")
                return [0.0] * 384
                
        except Exception as e:
            print(f"❌ Embedding generation error: {e}")
            return [0.0] * 384
    
    def generate_batch_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            model: Embedding model name (optional)
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            print(f"   📊 Generating embedding {i + 1}/{len(texts)}")
            embedding = self.generate_embedding(text, model)
            embeddings.append(embedding)
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        return embeddings
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze query intent using Ollama
        
        Args:
            query: Natural language query
            
        Returns:
            Analysis result with intent, entities, etc.
        """
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
        
        try:
            response = self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=800,
                temperature=0.1,
                query_type="structured_queries",
                query_complexity="medium"
            )
            
            # Try to parse JSON response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                # Fallback to basic analysis
                return self._fallback_query_analysis(query)
                
        except Exception as e:
            print(f"❌ Query analysis failed: {e}")
            return self._fallback_query_analysis(query)
    
    def _fallback_query_analysis(self, query: str) -> Dict[str, Any]:
        """Fallback query analysis using pattern matching"""
        query_lower = query.lower()
        
        # Basic intent detection
        if any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            intent = "comparison"
        elif any(word in query_lower for word in ["top", "bottom", "highest", "lowest", "best", "worst"]):
            intent = "ranking"
        elif any(word in query_lower for word in ["how many", "count", "total"]):
            intent = "count_query"
        elif any(word in query_lower for word in ["average", "mean", "statistics"]):
            intent = "analytics"
        else:
            intent = "employee_search"
        
        # Basic entity extraction
        entities = {}
        departments = ["Sales", "IT", "Operations", "HR", "Finance", "Legal", "Engineering", "Marketing", "Support"]
        for dept in departments:
            if dept.lower() in query_lower:
                if "departments" not in entities:
                    entities["departments"] = []
                entities["departments"].append(dept)
        
        return {
            "intent": intent,
            "entities": entities,
            "fields_to_analyze": ["performance_rating"],
            "comparison_groups": [],
            "filters": {},
            "sorting": {},
            "aggregation_type": None,
            "limit": 10
        }
    
    def generate_response(self, 
                         query: str, 
                         results: List[Dict[str, Any]], 
                         count: int,
                         intent: str) -> str:
        """
        Generate natural language response for query results
        
        Args:
            query: Original query
            results: Query results
            count: Number of results
            intent: Query intent
            
        Returns:
            Natural language response
        """
        system_prompt = """You are a senior HR analytics executive providing board-level insights and strategic recommendations.

        CRITICAL: Generate responses in a professional, executive-ready format suitable for C-level presentations.

        Response Structure (MANDATORY):
        1. EXECUTIVE SUMMARY (2-3 sentences max)
        2. KEY FINDINGS (bullet points with specific metrics)
        3. DETAILED ANALYSIS (professional table format)
        4. STRATEGIC IMPLICATIONS (business impact)
        5. RECOMMENDED ACTIONS (numbered priority list)

        Formatting Requirements:
        - Use professional business language
        - Include specific metrics and percentages
        - Create clean, readable tables with proper alignment
        - Use bullet points for clarity
        - Avoid casual language or informal tone
        - Focus on business value and ROI
        - Include comparative analysis where relevant

        Table Format Example:
        | Rank | Employee | Department | Role | Rating | KPIs | Status |
        |------|----------|------------|------|--------|------|--------|
        | 1    | Name     | Dept       | Role  | 4.2    | 85%  | Top    |

        Tone: Professional, data-driven, strategic, executive-level
        """
        
        # Build context
        context = {
            "query": query,
            "intent": intent,
            "count": count,
            "has_results": len(results) > 0,
            "results": results[:5] if results else []  # Limit for context
        }
        
        user_prompt = f"""
        EXECUTIVE BRIEFING REQUEST
        
        Query: "{query}"
        Analysis Type: {intent}
        Data Points Available: {count}
        
        EMPLOYEE DATA SET:
        {json.dumps(results, default=str, indent=2) if results else "No specific employee data found"}
        
        EXECUTIVE PRESENTATION REQUIREMENTS:
        
        1. EXECUTIVE SUMMARY (2-3 sentences):
           - High-level overview of findings
           - Key performance indicators
           - Strategic significance
        
        2. KEY FINDINGS (bullet format):
           • Specific metrics with percentages
           • Department performance comparisons
           • Notable trends or patterns
        
        3. DETAILED ANALYSIS (professional table):
           - Clean, aligned table format
           - Include all relevant employee data
           - Use proper column headers
           - Sort by performance metrics
        
        4. STRATEGIC IMPLICATIONS:
           - Business impact analysis
           - Competitive advantages
           - Risk assessment
        
        5. RECOMMENDED ACTIONS (numbered):
           1. Immediate actions (next 30 days)
           2. Medium-term initiatives (next quarter)
           3. Long-term strategic moves
        
        CRITICAL: Format for C-level executives. Use professional business language, include specific metrics, and focus on ROI and business value.
        
        Generate an executive-ready analysis using the provided employee data.
        """
        
        try:
            # Determine query complexity based on results
            complexity = "high" if len(results) > 10 or intent in ["correlation", "complex_filter"] else "medium"
            
            response = self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=600,
                temperature=0.3,
                query_type="complex_analytics" if complexity == "high" else "structured_queries",
                query_complexity=complexity
            )
            return response.strip()
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            return self._generate_fallback_response(query, results, count, intent)
    
    def _generate_fallback_response(self, 
                                  query: str, 
                                  results: List[Dict[str, Any]], 
                                  count: int,
                                  intent: str) -> str:
        """Generate fallback response when AI fails"""
        if intent == "count_query":
            return f"Found {count} employees matching your criteria."
        
        elif intent == "comparison" and results:
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
        
        elif intent == "ranking" and results:
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
        
        elif intent == "analytics" and results:
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

# Global instance
ollama_client = OllamaClient()

def test_ollama_connection():
    """Test Ollama connection and models"""
    print("🧪 Testing Ollama Connection")
    print("=" * 40)
    
    try:
        # Test basic text generation
        print("📝 Testing text generation...")
        response = ollama_client.generate_text("Hello, how are you?")
        print(f"✅ Text generation: {response[:100]}...")
        
        # Test query analysis
        print("🔍 Testing query analysis...")
        analysis = ollama_client.analyze_query_intent("How many employees work in IT?")
        print(f"✅ Query analysis: {analysis['intent']}")
        
        # Test embedding generation (if available)
        if ollama_client.embedding_model:
            print("🧠 Testing embedding generation...")
            embedding = ollama_client.generate_embedding("test text")
            print(f"✅ Embedding generated: {len(embedding)} dimensions")
        else:
            print("⚠️ Embedding model not available")
        
        print("\n🎉 Ollama connection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")

if __name__ == "__main__":
    test_ollama_connection()
