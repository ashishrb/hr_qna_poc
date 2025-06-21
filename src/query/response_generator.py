# src/query/response_generator.py
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
import json
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.config import settings
from src.core.models import QueryType, QueryEntities, SearchResult
from src.core.exceptions import ResponseGenerationException

class ResponseGenerator:
    """Handles natural language response generation using GPT"""
    
    def __init__(self):
        self.openai_client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version="2023-05-15",
            azure_endpoint=settings.azure_openai_endpoint
        )
        
        # Response templates for different intents
        self.response_templates = {
            QueryType.COUNT_QUERY: {
                "with_results": "There are {count} employees {filter_description}.",
                "no_results": "No employees found {filter_description}."
            },
            QueryType.EMPLOYEE_SEARCH: {
                "single_result": "Here is the employee information:",
                "multiple_results": "Here are the employees matching your criteria:",
                "no_results": "I couldn't find any employees matching your criteria."
            },
            QueryType.SKILL_SEARCH: {
                "single_result": "Here is the employee with the requested skills:",
                "multiple_results": "Here are the employees with the requested skills:",
                "no_results": "I couldn't find any employees with those skills."
            },
            QueryType.DEPARTMENT_INFO: {
                "single_result": "Here is the employee from that department:",
                "multiple_results": "Here are the employees from that department:",
                "no_results": "I couldn't find any employees in that department."
            }
        }
        
        # System prompts for different scenarios
        self.system_prompts = {
            "default": """You are an HR assistant that helps answer questions about employees and company information. 
            Use ONLY the provided employee data to answer questions accurately and professionally.
            
            Guidelines:
            - Be concise but informative
            - If no relevant information is found, clearly state that
            - Only provide information that exists in the data provided
            - Format responses in a readable way
            - Include relevant details like department, role, location, and certifications when appropriate
            - Use bullet points or numbered lists for multiple employees
            - Be professional and respectful when discussing employee information
            """,
            
            "sensitive_data": """You are an HR assistant with access to sensitive employee information. 
            Handle all data with care and provide only appropriate information based on the user's query.
            
            Guidelines:
            - Never reveal salary or compensation details unless specifically authorized
            - Be cautious with performance ratings and personal information
            - Focus on professional information like role, department, skills, and projects
            - If asked for sensitive information, politely decline and suggest contacting HR directly
            """,
            
            "count_query": """You are an HR assistant providing statistical information about employees.
            Provide clear, accurate counts and summaries.
            
            Guidelines:
            - Give exact numbers when available
            - Explain what criteria were used for counting
            - Provide context if helpful (e.g., "out of X total employees")
            - Be precise and factual
            """,
            
            "comparison": """You are an HR assistant helping with employee comparisons and analysis.
            Provide balanced, factual comparisons without making subjective judgments.
            
            Guidelines:
            - Compare only objective criteria (experience, skills, certifications)
            - Avoid subjective comparisons or rankings
            - Focus on factual differences
            - Respect employee privacy and dignity
            """
        }
    
    def generate_response(self, 
                         query: str, 
                         intent: QueryType, 
                         entities: QueryEntities, 
                         search_results: List[SearchResult], 
                         count: int = 0,
                         include_sensitive_data: bool = False) -> str:
        """Generate natural language response based on query and results"""
        
        try:
            # Handle count queries with template responses
            if intent == QueryType.COUNT_QUERY:
                return self._generate_count_response(entities, count)
            
            # Handle empty results
            if not search_results:
                return self._generate_no_results_response(query, intent, entities)
            
            # Generate context from search results
            context = self._format_search_context(search_results, include_sensitive_data)
            
            # Choose appropriate system prompt
            system_prompt = self._get_system_prompt(intent, include_sensitive_data)
            
            # Create user prompt
            user_prompt = self._create_user_prompt(query, intent, entities, context)
            
            # Generate response using GPT
            response = self._call_openai(system_prompt, user_prompt)
            
            return response
            
        except Exception as e:
            raise ResponseGenerationException(f"Response generation failed: {str(e)}", query, context[:100] if 'context' in locals() else None)
    
    def _generate_count_response(self, entities: QueryEntities, count: int) -> str:
        """Generate response for count queries"""
        filter_parts = []
        
        if entities.department:
            filter_parts.append(f"in the {entities.department} department")
        
        if entities.location:
            filter_parts.append(f"in {entities.location}")
        
        if entities.position:
            filter_parts.append(f"with {entities.position} role")
        
        if entities.skills:
            skills_text = ", ".join(entities.skills)
            filter_parts.append(f"with {skills_text} skills")
        
        filter_description = " ".join(filter_parts) if filter_parts else "in the company"
        
        if count > 0:
            return f"There are {count} employees {filter_description}."
        else:
            return f"No employees found {filter_description}."
    
    def _generate_no_results_response(self, query: str, intent: QueryType, entities: QueryEntities) -> str:
        """Generate response when no results are found"""
        base_message = self.response_templates.get(intent, {}).get("no_results", "I couldn't find any matching results.")
        
        # Add helpful suggestions
        suggestions = []
        
        if entities.department:
            suggestions.append(f"check if '{entities.department}' is the correct department name")
        
        if entities.skills:
            suggestions.append(f"verify the skills: {', '.join(entities.skills)}")
        
        if entities.position:
            suggestions.append(f"confirm the position '{entities.position}' exists")
        
        if suggestions:
            suggestion_text = " You might want to " + " or ".join(suggestions) + "."
            return base_message + suggestion_text
        
        return base_message + f" Please try a different search or check if the information exists in our system."
    
    def _format_search_context(self, search_results: List[SearchResult], include_sensitive_data: bool = False) -> str:
        """Format search results into context for GPT"""
        context_parts = ["Relevant employee information:\n"]
        
        for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results
            context_parts.append(f"{i}. {result.full_name or 'Unknown'}")
            context_parts.append(f"   - Department: {result.department or 'N/A'}")
            context_parts.append(f"   - Role: {result.role or 'N/A'}")
            context_parts.append(f"   - Location: {result.location or 'N/A'}")
            
            if result.certifications:
                context_parts.append(f"   - Certifications: {result.certifications}")
            
            if result.current_project:
                context_parts.append(f"   - Current Project: {result.current_project}")
            
            if result.total_experience_years and result.total_experience_years > 0:
                context_parts.append(f"   - Experience: {result.total_experience_years} years")
            
            # Include performance rating only if authorized
            if include_sensitive_data and result.performance_rating and result.performance_rating > 0:
                context_parts.append(f"   - Performance Rating: {result.performance_rating}")
            
            # Add search relevance score for debugging
            if result.score > 0:
                context_parts.append(f"   - Relevance Score: {result.score:.3f}")
            
            context_parts.append("")  # Empty line between employees
        
        return "\n".join(context_parts)
    
    def _get_system_prompt(self, intent: QueryType, include_sensitive_data: bool) -> str:
        """Get appropriate system prompt based on intent and sensitivity"""
        if include_sensitive_data:
            return self.system_prompts["sensitive_data"]
        elif intent == QueryType.COUNT_QUERY:
            return self.system_prompts["count_query"]
        elif intent == QueryType.COMPARISON:
            return self.system_prompts["comparison"]
        else:
            return self.system_prompts["default"]
    
    def _create_user_prompt(self, query: str, intent: QueryType, entities: QueryEntities, context: str) -> str:
        """Create user prompt for GPT"""
        prompt_parts = [
            f"Query: {query}",
            f"Intent: {intent.value}",
            f"Entities detected: {entities.dict()}",
            "",
            context,
            "",
            "Please provide a helpful response to the user's query based on the employee information above."
        ]
        
        # Add specific instructions based on intent
        if intent == QueryType.EMPLOYEE_SEARCH:
            prompt_parts.append("Focus on providing clear employee details and contact information.")
        elif intent == QueryType.SKILL_SEARCH:
            prompt_parts.append("Emphasize the skills and certifications of the employees found.")
        elif intent == QueryType.DEPARTMENT_INFO:
            prompt_parts.append("Provide department-specific information and team structure.")
        
        return "\n".join(prompt_parts)
    
    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Make API call to OpenAI"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-llm",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3,
                top_p=0.9
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise ResponseGenerationException(f"OpenAI API call failed: {str(e)}", user_prompt[:100])
    
    def generate_summary_response(self, search_results: List[SearchResult], summary_type: str = "overview") -> str:
        """Generate summary responses for analytics"""
        try:
            if not search_results:
                return "No data available for summary."
            
            if summary_type == "overview":
                return self._generate_overview_summary(search_results)
            elif summary_type == "skills":
                return self._generate_skills_summary(search_results)
            elif summary_type == "departments":
                return self._generate_department_summary(search_results)
            else:
                return self._generate_general_summary(search_results)
                
        except Exception as e:
            return f"Summary generation failed: {str(e)}"
    
    def _generate_overview_summary(self, search_results: List[SearchResult]) -> str:
        """Generate overview summary"""
        total_employees = len(search_results)
        departments = set(result.department for result in search_results if result.department)
        roles = set(result.role for result in search_results if result.role)
        locations = set(result.location for result in search_results if result.location)
        
        summary_parts = [
            f"Found {total_employees} employees",
            f"Across {len(departments)} departments: {', '.join(sorted(departments))}",
            f"In {len(roles)} different roles: {', '.join(sorted(roles))}",
            f"Located in: {', '.join(sorted(locations))}"
        ]
        
        return ". ".join(summary_parts) + "."
    
    def _generate_skills_summary(self, search_results: List[SearchResult]) -> str:
        """Generate skills-focused summary"""
        skills_count = {}
        for result in search_results:
            if result.certifications:
                certs = [cert.strip() for cert in result.certifications.split(',')]
                for cert in certs:
                    if cert and cert != 'None':
                        skills_count[cert] = skills_count.get(cert, 0) + 1
        
        if not skills_count:
            return "No specific skills or certifications found in the results."
        
        top_skills = sorted(skills_count.items(), key=lambda x: x[1], reverse=True)[:5]
        skills_summary = ", ".join([f"{skill} ({count})" for skill, count in top_skills])
        
        return f"Top skills/certifications found: {skills_summary}."
    
    def _generate_department_summary(self, search_results: List[SearchResult]) -> str:
        """Generate department-focused summary"""
        dept_count = {}
        for result in search_results:
            if result.department:
                dept_count[result.department] = dept_count.get(result.department, 0) + 1
        
        if not dept_count:
            return "No department information found in the results."
        
        dept_summary = ", ".join([f"{dept}: {count}" for dept, count in sorted(dept_count.items())])
        return f"Employee distribution by department - {dept_summary}."
    
    def _generate_general_summary(self, search_results: List[SearchResult]) -> str:
        """Generate general summary"""
        return f"Found {len(search_results)} employees matching your criteria. Use specific queries to get detailed information about individual employees."
    
    def format_employee_details(self, employee: SearchResult, include_sensitive_data: bool = False) -> str:
        """Format detailed employee information"""
        details = [f"**{employee.full_name or 'Unknown Employee'}**"]
        
        if employee.department:
            details.append(f"Department: {employee.department}")
        
        if employee.role:
            details.append(f"Role: {employee.role}")
        
        if employee.location:
            details.append(f"Location: {employee.location}")
        
        if employee.certifications and employee.certifications != 'None':
            details.append(f"Certifications: {employee.certifications}")
        
        if employee.current_project:
            details.append(f"Current Project: {employee.current_project}")
        
        if employee.total_experience_years and employee.total_experience_years > 0:
            details.append(f"Experience: {employee.total_experience_years} years")
        
        if include_sensitive_data and employee.performance_rating and employee.performance_rating > 0:
            details.append(f"Performance Rating: {employee.performance_rating}")
        
        return "\n".join(details)

# Global instance
response_generator = ResponseGenerator()