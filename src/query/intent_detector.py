# src/query/intent_detector.py
import re
from typing import Tuple, Dict, Any, List
from enum import Enum
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.models import QueryType, QueryEntities
from src.core.exceptions import IntentDetectionException, EntityExtractionException

class IntentDetector:
    """Handles intent detection and entity extraction from user queries"""
    
    def __init__(self):
        # Define intent patterns with priority (higher index = higher priority)
        self.intent_patterns = {
            QueryType.COUNT_QUERY: [
                r"how many",
                r"count",
                r"number of",
                r"total",
                r"how much",
                r"quantity"
            ],
            QueryType.SKILL_SEARCH: [
                r"certification",
                r"certified",
                r"skill",
                r"experience in",
                r"knows",
                r"expert in",
                r"proficient",
                r"pmp",
                r"gcp",
                r"aws",
                r"azure",
                r"python",
                r"java",
                r"javascript",
                r"sql"
            ],
            QueryType.EMPLOYEE_SEARCH: [
                r"find",
                r"search",
                r"show me",
                r"who are",
                r"list",
                r"get me",
                r"tell me about",
                r"information about",
                r"details of",
                r"profile"
            ],
            QueryType.DEPARTMENT_INFO: [
                r"department",
                r"team",
                r"division",
                r"group",
                r"works in",
                r"from.*department"
            ],
            QueryType.COMPARISON: [
                r"compare",
                r"versus",
                r"vs",
                r"difference between",
                r"similar to",
                r"better than"
            ]
        }
        
        # Entity dictionaries with variations
        self.departments = [
            "Sales", "IT", "Operations", "HR", "Finance", "Legal", 
            "Engineering", "Marketing", "Support", "Development"
        ]
        
        self.locations = [
            "Offshore", "Onshore", "Remote", "Chennai", "Hyderabad", 
            "New York", "California", "India", "USA", "Bangalore", "Mumbai"
        ]
        
        self.skills = [
            "PMP", "GCP", "AWS", "Azure", "Python", "Java", "JavaScript", 
            "SQL", "Docker", "Kubernetes", "React", "Angular", "Node.js",
            "Machine Learning", "Data Science", "AI", "Analytics"
        ]
        
        self.positions = [
            "Developer", "Director", "Manager", "Analyst", "Engineer", 
            "Lead", "Senior", "Junior", "Principal", "Architect", "Consultant"
        ]
        
        # Common variations and synonyms
        self.skill_synonyms = {
            "ml": "Machine Learning",
            "ai": "AI",
            "js": "JavaScript",
            "node": "Node.js",
            "react": "React",
            "angular": "Angular"
        }
        
        self.position_synonyms = {
            "dev": "Developer",
            "mgr": "Manager",
            "sr": "Senior",
            "jr": "Junior"
        }
    
    def detect_intent(self, query: str) -> QueryType:
        """Detect the primary intent of the query"""
        try:
            query_lower = query.lower().strip()
            
            if not query_lower:
                raise IntentDetectionException("Empty query provided", query)
            
            # Check patterns in priority order
            intent_scores = {}
            
            for intent, patterns in self.intent_patterns.items():
                score = 0
                for pattern in patterns:
                    if re.search(pattern, query_lower):
                        score += 1
                
                if score > 0:
                    intent_scores[intent] = score
            
            # Return the intent with highest score
            if intent_scores:
                return max(intent_scores.items(), key=lambda x: x[1])[0]
            
            # Default fallback
            return QueryType.GENERAL_INFO
            
        except Exception as e:
            raise IntentDetectionException(f"Intent detection failed: {str(e)}", query)
    
    def extract_entities(self, query: str) -> QueryEntities:
        """Extract entities from the query"""
        try:
            query_lower = query.lower().strip()
            entities = QueryEntities()
            
            # Extract employee name (simple pattern matching)
            entities.employee_name = self._extract_employee_name(query)
            
            # Extract skills with synonyms
            entities.skills = self._extract_skills(query_lower)
            
            # Extract department
            entities.department = self._extract_department(query_lower)
            
            # Extract location
            entities.location = self._extract_location(query_lower)
            
            # Extract position
            entities.position = self._extract_position(query_lower)
            
            return entities
            
        except Exception as e:
            raise EntityExtractionException(f"Entity extraction failed: {str(e)}", query)
    
    def _extract_employee_name(self, query: str) -> str:
        """Extract employee name from query"""
        # Look for patterns like "tell me about John Smith" or "find John Smith"
        name_patterns = [
            r"about\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"find\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"who\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_skills(self, query_lower: str) -> List[str]:
        """Extract skills and certifications from query"""
        found_skills = []
        
        # Check for exact matches
        for skill in self.skills:
            if skill.lower() in query_lower:
                # Use word boundaries to avoid partial matches
                if re.search(rf'\b{re.escape(skill.lower())}\b', query_lower):
                    found_skills.append(skill)
        
        # Check for synonyms
        for synonym, skill in self.skill_synonyms.items():
            if re.search(rf'\b{re.escape(synonym)}\b', query_lower):
                if skill not in found_skills:
                    found_skills.append(skill)
        
        # Check for certification-specific patterns
        cert_patterns = [
            r'\b(pmp)\b',
            r'\b(gcp)\b',
            r'\b(aws)\b',
            r'\b(azure)\b'
        ]
        
        for pattern in cert_patterns:
            match = re.search(pattern, query_lower)
            if match:
                cert = match.group(1).upper()
                if cert not in found_skills:
                    found_skills.append(cert)
        
        return found_skills
    
    def _extract_department(self, query_lower: str) -> str:
        """Extract department from query"""
        for dept in self.departments:
            # Use word boundaries for better matching
            if re.search(rf'\b{re.escape(dept.lower())}\b', query_lower):
                return dept
        
        # Check for common department abbreviations
        dept_abbrev = {
            "hr": "HR",
            "it": "IT",
            "tech": "IT",
            "technology": "IT",
            "sales": "Sales",
            "finance": "Finance",
            "ops": "Operations"
        }
        
        for abbrev, full_name in dept_abbrev.items():
            if re.search(rf'\b{re.escape(abbrev)}\b', query_lower):
                return full_name
        
        return None
    
    def _extract_location(self, query_lower: str) -> str:
        """Extract location from query"""
        for location in self.locations:
            if re.search(rf'\b{re.escape(location.lower())}\b', query_lower):
                return location
        
        # Check for location patterns
        location_patterns = {
            r'\bremote\b': "Remote",
            r'\bonshore\b': "Onshore",
            r'\boffshore\b': "Offshore",
            r'\bindia\b': "India",
            r'\busa\b': "USA",
            r'\bus\b': "USA"
        }
        
        for pattern, location in location_patterns.items():
            if re.search(pattern, query_lower):
                return location
        
        return None
    
    def _extract_position(self, query_lower: str) -> str:
        """Extract position/role from query"""
        for position in self.positions:
            # Handle plural forms
            position_variants = [
                position.lower(),
                position.lower() + "s",  # plural
                position.lower() + "es"  # plural for words ending in 's'
            ]
            
            for variant in position_variants:
                if re.search(rf'\b{re.escape(variant)}\b', query_lower):
                    return position
        
        # Check for synonyms
        for synonym, position in self.position_synonyms.items():
            if re.search(rf'\b{re.escape(synonym)}\b', query_lower):
                return position
        
        # Check for specific role patterns
        role_patterns = {
            r'\bdeveloper[s]?\b': "Developer",
            r'\bdirector[s]?\b': "Director",
            r'\bmanager[s]?\b': "Manager",
            r'\banalyst[s]?\b': "Analyst",
            r'\bengineer[s]?\b': "Engineer",
            r'\blead[s]?\b': "Lead"
        }
        
        for pattern, role in role_patterns.items():
            if re.search(pattern, query_lower):
                return role
        
        return None
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze query complexity and provide metadata"""
        try:
            query_lower = query.lower().strip()
            
            analysis = {
                "word_count": len(query.split()),
                "character_count": len(query),
                "has_entities": False,
                "entity_types": [],
                "complexity_score": 0,
                "suggested_intent": None
            }
            
            # Extract entities to check complexity
            entities = self.extract_entities(query)
            
            # Check if entities were found
            if entities.employee_name:
                analysis["has_entities"] = True
                analysis["entity_types"].append("employee_name")
            
            if entities.skills:
                analysis["has_entities"] = True
                analysis["entity_types"].append("skills")
            
            if entities.department:
                analysis["has_entities"] = True
                analysis["entity_types"].append("department")
            
            if entities.location:
                analysis["has_entities"] = True
                analysis["entity_types"].append("location")
            
            if entities.position:
                analysis["has_entities"] = True
                analysis["entity_types"].append("position")
            
            # Calculate complexity score
            complexity_score = 0
            complexity_score += min(analysis["word_count"] / 5, 2)  # Max 2 points for length
            complexity_score += len(analysis["entity_types"])  # 1 point per entity type
            
            # Check for complex patterns
            complex_patterns = [
                r"compare",
                r"versus",
                r"difference",
                r"and.*or",
                r"not.*but",
                r"except"
            ]
            
            for pattern in complex_patterns:
                if re.search(pattern, query_lower):
                    complexity_score += 1
            
            analysis["complexity_score"] = complexity_score
            
            # Suggest intent
            analysis["suggested_intent"] = self.detect_intent(query).value
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"Query analysis failed: {str(e)}",
                "word_count": 0,
                "character_count": 0,
                "has_entities": False,
                "entity_types": [],
                "complexity_score": 0,
                "suggested_intent": "unknown"
            }
    
    def get_entity_suggestions(self, query: str) -> Dict[str, List[str]]:
        """Get suggestions for entities that might be in the query"""
        query_lower = query.lower()
        
        suggestions = {
            "departments": [],
            "locations": [],
            "skills": [],
            "positions": []
        }
        
        # Suggest departments that partially match
        for dept in self.departments:
            if any(word in dept.lower() for word in query_lower.split()):
                suggestions["departments"].append(dept)
        
        # Suggest locations that partially match
        for location in self.locations:
            if any(word in location.lower() for word in query_lower.split()):
                suggestions["locations"].append(location)
        
        # Suggest skills that partially match
        for skill in self.skills:
            if any(word in skill.lower() for word in query_lower.split()):
                suggestions["skills"].append(skill)
        
        # Suggest positions that partially match
        for position in self.positions:
            if any(word in position.lower() for word in query_lower.split()):
                suggestions["positions"].append(position)
        
        return suggestions

# Global instance
intent_detector = IntentDetector()