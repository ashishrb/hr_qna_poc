# src/api/endpoints.py
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional
import asyncio
import time
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.core.models import (
    QueryRequest, QueryResponse, EmployeeSearchRequest, EmployeeSearchResponse,
    CountRequest, CountResponse, AnalyticsResponse, SuggestionRequest, 
    SuggestionResponse, HealthResponse, ErrorResponse
)
from src.core.exceptions import (
    HRQAException, ValidationException, QueryException, SearchException
)
from src.query.hr_query_engine import RobustHRQueryEngine
from src.query.intent_detector import intent_detector
from src.query.response_generator import response_generator
from src.database.collections import employee_collections
from src.search.azure_search_client import azure_search_client
from src.processing.etl_pipeline import etl_pipeline

# Create routers for different API sections
main_router = APIRouter()
query_router = APIRouter(prefix="/query", tags=["Query Processing"])
search_router = APIRouter(prefix="/search", tags=["Employee Search"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])
admin_router = APIRouter(prefix="/admin", tags=["Administration"])

# Initialize query engine
query_engine = RobustHRQueryEngine()

# =============================================================================
# MAIN ENDPOINTS
# =============================================================================

@main_router.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API information"""
    return HealthResponse(
        status="active",
        message="HR Q&A System API is running",
        version="1.0.0",
        services={
            "database": "MongoDB Atlas",
            "search": "Azure AI Search", 
            "ai": "Azure OpenAI GPT-4"
        }
    )

@main_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Test database connection
        collections = await employee_collections.get_all_employee_ids()
        db_status = "healthy" if collections else "no_data"
        
        # Test search service
        try:
            count = azure_search_client.get_document_count()
            search_status = "healthy" if count > 0 else "no_data"
        except:
            search_status = "error"
        
        overall_status = "healthy" if all([
            db_status == "healthy",
            search_status in ["healthy", "no_data"]
        ]) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            message="System health check completed",
            version="1.0.0",
            services={
                "database": db_status,
                "search": search_status,
                "ai": "healthy"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# =============================================================================
# QUERY PROCESSING ENDPOINTS
# =============================================================================

@query_router.post("/", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Main query processing endpoint with intent detection and response generation"""
    start_time = time.time()
    
    try:
        # Validate request
        if not request.query.strip():
            raise ValidationException("Query cannot be empty", "query", request.query)
        
        if len(request.query) > 500:
            raise ValidationException("Query too long (max 500 characters)", "query", str(len(request.query)))
        
        # Process query using the query engine
        result = await query_engine.process_query(request.query)
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        result["processing_time_ms"] = processing_time
        
        # Convert to response model
        response = QueryResponse(
            query=result["query"],
            intent=result["intent"],
            entities=result["entities"],
            search_results=result["search_results"],
            response=result["response"],
            count=result["count"],
            status=result["status"],
            error=result.get("error"),
            processing_time_ms=processing_time
        )
        
        return response
        
    except ValidationException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500, 
            detail=f"Query processing failed: {str(e)}"
        )

@query_router.post("/analyze", response_model=Dict[str, Any])
async def analyze_query(request: QueryRequest):
    """Analyze query complexity and provide metadata without executing search"""
    try:
        # Detect intent
        intent = intent_detector.detect_intent(request.query)
        
        # Extract entities
        entities = intent_detector.extract_entities(request.query)
        
        # Analyze complexity
        analysis = intent_detector.analyze_query_complexity(request.query)
        
        # Get suggestions
        suggestions = intent_detector.get_entity_suggestions(request.query)
        
        return {
            "query": request.query,
            "intent": intent.value,
            "entities": entities.dict(),
            "analysis": analysis,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")

# =============================================================================
# SEARCH ENDPOINTS  
# =============================================================================

@search_router.post("/employees", response_model=EmployeeSearchResponse)
async def search_employees(request: EmployeeSearchRequest):
    """Search for employees with advanced filtering"""
    try:
        # Convert filters to dict if present
        filters_dict = request.filters.dict() if request.filters else None
        
        # Perform search
        employees = await query_engine.search_employees(
            query=request.query,
            filters=filters_dict,
            top_k=request.top_k
        )
        
        return EmployeeSearchResponse(
            employees=employees,
            total_count=len(employees),
            query=request.query,
            filters=request.filters
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Employee search failed: {str(e)}")

@search_router.get("/employees/count", response_model=CountResponse)
async def count_employees(
    department: Optional[str] = Query(None, description="Filter by department"),
    location: Optional[str] = Query(None, description="Filter by location"),
    position: Optional[str] = Query(None, description="Filter by position"),
    certification: Optional[str] = Query(None, description="Filter by certification")
):
    """Count employees with optional filters"""
    try:
        filters = {}
        if department:
            filters["department"] = department
        if location:
            filters["location"] = location
        if position:
            filters["position"] = position
        if certification:
            filters["certification"] = certification
        
        count = query_engine.count_employees(filters)
        
        return CountResponse(count=count, filters=filters)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Count query failed: {str(e)}")

@search_router.get("/suggestions")
async def get_search_suggestions(q: str = Query(..., description="Query for suggestions")):
    """Get search suggestions based on partial query"""
    try:
        if len(q) < 2:
            return SuggestionResponse(suggestions=[], query=q)
        
        # Get entity suggestions
        suggestions = intent_detector.get_entity_suggestions(q)
        
        # Flatten suggestions
        all_suggestions = []
        for category, items in suggestions.items():
            all_suggestions.extend(items[:3])  # Max 3 per category
        
        # Add search suggestions from index
        try:
            search_suggestions = azure_search_client.suggest(q, "sg", 5)
            all_suggestions.extend(search_suggestions)
        except:
            pass  # Ignore search suggestion errors
        
        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(all_suggestions))[:10]
        
        return SuggestionResponse(suggestions=unique_suggestions, query=q)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@analytics_router.get("/departments", response_model=AnalyticsResponse)
async def get_department_analytics():
    """Get department analytics and statistics"""
    try:
        # Get department distribution from database
        dept_stats = await employee_collections.get_department_statistics()
        
        # Convert to analytics format
        departments = [
            {"department": dept, "count": count}
            for dept, count in dept_stats.items()
        ]
        
        total_employees = sum(dept_stats.values())
        
        return AnalyticsResponse(
            departments=departments,
            total_employees=total_employees
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Department analytics failed: {str(e)}")

@analytics_router.get("/positions", response_model=AnalyticsResponse)
async def get_position_analytics():
    """Get position/role analytics and statistics"""
    try:
        # Get role distribution from database
        role_stats = await employee_collections.get_role_statistics()
        
        # Convert to analytics format
        positions = [
            {"position": role, "count": count}
            for role, count in role_stats.items()
        ]
        
        total_employees = sum(role_stats.values())
        
        return AnalyticsResponse(
            positions=positions,
            total_employees=total_employees
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Position analytics failed: {str(e)}")

@analytics_router.get("/overview", response_model=Dict[str, Any])
async def get_overview_analytics():
    """Get comprehensive overview analytics"""
    try:
        # Get basic statistics
        employee_ids = await employee_collections.get_all_employee_ids()
        total_employees = len(employee_ids)
        
        # Get department and role stats
        dept_stats = await employee_collections.get_department_statistics()
        role_stats = await employee_collections.get_role_statistics()
        
        # Get search index stats
        try:
            indexed_count = azure_search_client.get_document_count()
        except:
            indexed_count = 0
        
        return {
            "total_employees": total_employees,
            "total_departments": len(dept_stats),
            "total_roles": len(role_stats),
            "indexed_employees": indexed_count,
            "top_departments": dict(list(dept_stats.items())[:5]),
            "top_roles": dict(list(role_stats.items())[:5]),
            "data_coverage": {
                "personal_info": "✅",
                "employment_info": "✅", 
                "learning_info": "✅",
                "performance_info": "✅"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overview analytics failed: {str(e)}")

# =============================================================================
# ADMINISTRATION ENDPOINTS
# =============================================================================

@admin_router.post("/etl/run")
async def run_etl_pipeline(
    background_tasks: BackgroundTasks,
    excel_file_path: str = Query(..., description="Path to Excel file"),
    skip_indexing: bool = Query(False, description="Skip search indexing"),
    skip_embeddings: bool = Query(False, description="Skip embeddings generation")
):
    """Run ETL pipeline in background"""
    try:
        # Validate file path
        if not excel_file_path:
            raise ValidationException("Excel file path is required", "excel_file_path", excel_file_path)
        
        # Run ETL pipeline in background
        background_tasks.add_task(
            etl_pipeline.run_full_pipeline,
            excel_file_path=excel_file_path,
            skip_indexing=skip_indexing,
            skip_embeddings=skip_embeddings
        )
        
        return {
            "status": "started",
            "message": "ETL pipeline started in background",
            "file_path": excel_file_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ETL pipeline: {str(e)}")

@admin_router.get("/etl/status")
async def get_etl_status():
    """Get ETL pipeline status and statistics"""
    try:
        return {
            "status": "available",
            "stats": etl_pipeline.stats,
            "message": "ETL pipeline is ready"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ETL status: {str(e)}")

@admin_router.post("/search/reindex")
async def reindex_search(background_tasks: BackgroundTasks):
    """Reindex search data in background"""
    try:
        async def reindex_task():
            from src.search.fixed_indexer import FixedAzureSearchIndexer
            indexer = FixedAzureSearchIndexer()
            
            try:
                await indexer.connect_to_mongodb()
                await indexer.create_or_update_index()
                await indexer.index_all_employees()
                await indexer.verify_index()
            finally:
                await indexer.close_connections()
        
        background_tasks.add_task(reindex_task)
        
        return {
            "status": "started",
            "message": "Search reindexing started in background"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start reindexing: {str(e)}")

@admin_router.get("/system/info")
async def get_system_info():
    """Get system information and configuration"""
    try:
        return {
            "version": "1.0.0",
            "environment": "development",
            "services": {
                "database": "MongoDB Atlas",
                "search": "Azure AI Search",
                "ai": "Azure OpenAI GPT-4",
                "embeddings": "text-embedding-ada-002"
            },
            "features": {
                "query_processing": True,
                "semantic_search": True,
                "intent_detection": True,
                "response_generation": True,
                "analytics": True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")

# =============================================================================
# ERROR HANDLERS
# =============================================================================

def setup_error_handlers(app):
    """Setup global error handlers"""
    
    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request, exc: ValidationException):
        return ErrorResponse(
            error="Validation Error",
            message=exc.message,
            status_code=400,
            details=exc.details
        )
    
    @app.exception_handler(QueryException)
    async def query_exception_handler(request, exc: QueryException):
        return ErrorResponse(
            error="Query Processing Error",
            message=exc.message,
            status_code=500,
            details=exc.details
        )
    
    @app.exception_handler(SearchException)
    async def search_exception_handler(request, exc: SearchException):
        return ErrorResponse(
            error="Search Error", 
            message=exc.message,
            status_code=500,
            details=exc.details
        )
    
    @app.exception_handler(HRQAException)
    async def hrqa_exception_handler(request, exc: HRQAException):
        return ErrorResponse(
            error="System Error",
            message=exc.message,
            status_code=500,
            details=exc.details
        )

# =============================================================================
# ROUTER COLLECTION
# =============================================================================

# Collect all routers
all_routers = [
    main_router,
    query_router, 
    search_router,
    analytics_router,
    admin_router
]