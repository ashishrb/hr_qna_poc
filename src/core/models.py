# src/core/models.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class QueryType(Enum):
    """Types of queries the system can handle"""
    EMPLOYEE_SEARCH = "employee_search"
    SKILL_SEARCH = "skill_search"
    DEPARTMENT_INFO = "department_info"
    GENERAL_INFO = "general_info"
    COUNT_QUERY = "count_query"
    COMPARISON = "comparison"
    UNKNOWN = "unknown"

class EmployeePersonalInfo(BaseModel):
    """Employee personal information model"""
    employee_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    location: Optional[str] = None
    nationality: Optional[str] = None
    contact_number: Optional[str] = None
    emergency_contact: Optional[str] = None
    address: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeEmploymentInfo(BaseModel):
    """Employee employment information model"""
    employee_id: str
    department: Optional[str] = None
    role: Optional[str] = None
    grade_band: Optional[str] = None
    employment_type: Optional[str] = None
    manager_id: Optional[str] = None
    joining_date: Optional[Union[str, datetime]] = None
    work_mode: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeLearningInfo(BaseModel):
    """Employee learning and certification model"""
    employee_id: str
    courses_completed: Optional[int] = None
    certifications: Optional[str] = None
    internal_trainings: Optional[int] = None
    learning_hours_ytd: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeExperienceInfo(BaseModel):
    """Employee experience information model"""
    employee_id: str
    total_experience_years: Optional[float] = None
    years_in_current_company: Optional[float] = None
    years_in_current_skillset: Optional[float] = None
    known_skills_count: Optional[int] = None
    previous_companies_resigned: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeePerformanceInfo(BaseModel):
    """Employee performance information model"""
    employee_id: str
    performance_rating: Optional[int] = None
    kpis_met_pct: Optional[str] = None
    promotions_count: Optional[int] = None
    awards: Optional[str] = None
    improvement_areas: Optional[str] = None
    last_review_date: Optional[Union[str, datetime]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeEngagementInfo(BaseModel):
    """Employee engagement information model"""
    employee_id: str
    current_project: Optional[str] = None
    allocation_percentage: Optional[str] = None
    multiple_project_allocations: Optional[str] = None
    peer_review_score: Optional[int] = None
    manager_feedback: Optional[str] = None
    days_on_bench: Optional[int] = None
    engagement_score: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeCompensationInfo(BaseModel):
    """Employee compensation information model"""
    employee_id: str
    current_salary: Optional[int] = None
    bonus: Optional[int] = None
    total_ctc: Optional[int] = None
    currency: Optional[str] = None
    last_appraisal_date: Optional[Union[str, datetime]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeAttendanceInfo(BaseModel):
    """Employee attendance information model"""
    employee_id: str
    monthly_attendance_pct: Optional[str] = None
    leave_days_taken: Optional[int] = None
    leave_balance: Optional[int] = None
    leave_pattern: Optional[str] = None
    leave_transaction_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class EmployeeAttritionInfo(BaseModel):
    """Employee attrition risk information model"""
    employee_id: str
    attrition_risk_score: Optional[str] = None
    internal_transfers: Optional[int] = None
    exit_intent_flag: Optional[str] = None
    retention_plan: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProjectHistory(BaseModel):
    """Project history model"""
    employee_id: str
    project_name: Optional[str] = None
    project_start_date: Optional[Union[str, datetime]] = None
    project_end_date: Optional[Union[str, datetime]] = None
    project_success: Optional[str] = None
    client_feedback: Optional[str] = None
    contribution_level: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CompleteEmployeeProfile(BaseModel):
    """Complete employee profile combining all information"""
    employee_id: str
    
    # Personal Info
    full_name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
    
    # Employment Info
    department: Optional[str] = None
    role: Optional[str] = None
    grade_band: Optional[str] = None
    employment_type: Optional[str] = None
    manager_id: Optional[str] = None
    joining_date: Optional[Union[str, datetime]] = None
    work_mode: Optional[str] = None
    
    # Learning Info
    certifications: Optional[str] = None
    courses_completed: Optional[int] = None
    learning_hours_ytd: Optional[int] = None
    internal_trainings: Optional[int] = None
    
    # Experience Info
    total_experience_years: Optional[float] = None
    years_in_current_company: Optional[float] = None
    known_skills_count: Optional[int] = None
    
    # Performance Info
    performance_rating: Optional[int] = None
    awards: Optional[str] = None
    improvement_areas: Optional[str] = None
    
    # Engagement Info
    current_project: Optional[str] = None
    engagement_score: Optional[int] = None
    manager_feedback: Optional[str] = None
    
    # Compensation Info (sensitive)
    current_salary: Optional[int] = None
    total_ctc: Optional[int] = None
    
    # Attendance Info
    monthly_attendance_pct: Optional[str] = None
    leave_balance: Optional[int] = None
    
    # Attrition Info
    attrition_risk_score: Optional[str] = None
    exit_intent_flag: Optional[str] = None
    
    # Project History
    project_history: Optional[List[ProjectHistory]] = []

class QueryEntities(BaseModel):
    """Entities extracted from a query"""
    employee_name: Optional[str] = None
    skills: List[str] = []
    department: Optional[str] = None
    location: Optional[str] = None
    position: Optional[str] = None
    
class SearchFilters(BaseModel):
    """Search filters for employee queries"""
    department: Optional[str] = None
    location: Optional[str] = None
    position: Optional[str] = None
    certification: Optional[str] = None
    experience_min: Optional[float] = None
    experience_max: Optional[float] = None
    performance_rating_min: Optional[int] = None
    performance_rating_max: Optional[int] = None

class SearchResult(BaseModel):
    """Individual search result"""
    id: str
    employee_id: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    certifications: Optional[str] = None
    combined_text: Optional[str] = None
    current_project: Optional[str] = None
    total_experience_years: Optional[float] = None
    performance_rating: Optional[int] = None
    score: float = 0.0
    reranker_score: Optional[float] = None

class QueryRequest(BaseModel):
    """Query request model"""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: Optional[int] = Field(default=5, ge=1, le=50)
    filters: Optional[SearchFilters] = None
    include_sensitive_data: bool = False

class QueryResponse(BaseModel):
    """Query response model"""
    query: str
    intent: str
    entities: QueryEntities
    search_results: List[SearchResult]
    response: str
    count: int = 0
    status: str
    error: Optional[str] = None
    processing_time_ms: Optional[float] = None

class EmployeeSearchRequest(BaseModel):
    """Employee search request model"""
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    top_k: Optional[int] = Field(default=5, ge=1, le=50)

class EmployeeSearchResponse(BaseModel):
    """Employee search response model"""
    employees: List[SearchResult]
    total_count: int
    query: str
    filters: Optional[SearchFilters] = None

class CountRequest(BaseModel):
    """Count request model"""
    filters: Optional[SearchFilters] = None

class CountResponse(BaseModel):
    """Count response model"""
    count: int
    filters: Optional[SearchFilters] = None

class AnalyticsResponse(BaseModel):
    """Analytics response model"""
    departments: Optional[List[Dict[str, Any]]] = None
    positions: Optional[List[Dict[str, Any]]] = None
    locations: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    total_employees: int = 0

class SuggestionRequest(BaseModel):
    """Suggestion request model"""
    query: str = Field(..., min_length=1, max_length=100)
    max_suggestions: Optional[int] = Field(default=5, ge=1, le=10)

class SuggestionResponse(BaseModel):
    """Suggestion response model"""
    suggestions: List[str]
    query: str

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    message: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Optional[Dict[str, str]] = None

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None

# Validators
class QueryRequestValidator:
    """Validates query requests"""
    
    @staticmethod
    def validate_query(query: str) -> bool:
        """Validate query string"""
        if not query or len(query.strip()) == 0:
            return False
        if len(query) > 500:
            return False
        return True
    
    @staticmethod
    def validate_top_k(top_k: int) -> bool:
        """Validate top_k parameter"""
        return 1 <= top_k <= 50

# Configuration models
class DatabaseConfig(BaseModel):
    """Database configuration model"""
    connection_string: str
    database_name: str
    max_pool_size: Optional[int] = 10
    timeout_ms: Optional[int] = 5000

class SearchConfig(BaseModel):
    """Search configuration model"""
    service_name: str
    api_key: str
    endpoint: str
    index_name: str
    max_results: Optional[int] = 50

class OpenAIConfig(BaseModel):
    """OpenAI configuration model"""
    endpoint: str
    api_key: str
    api_version: str
    chat_deployment: str
    embedding_deployment: str
    max_tokens: Optional[int] = 500
    temperature: Optional[float] = 0.3