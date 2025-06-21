# src/api/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import uvicorn
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.query.query_engine import HRQueryEngine

# Initialize FastAPI app
app = FastAPI(
    title="HR Q&A System API",
    description="Intelligent HR Query and Response System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize query engine
query_engine = HRQueryEngine()

# Pydantic models for request/response
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    query: str
    intent: str
    entities: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    response: str
    count: int
    status: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: Optional[int] = 5

class EmployeeResponse(BaseModel):
    employees: List[Dict[str, Any]]
    total_count: int
    query: str

# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with API information"""
    return HealthResponse(
        status="active",
        message="HR Q&A System API is running",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Basic health check - could add more comprehensive checks
        return HealthResponse(
            status="healthy",
            message="All systems operational",
            version="1.0.0"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Main query processing endpoint"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        result = await query_engine.process_query(request.query)
        
        return QueryResponse(
            query=result["query"],
            intent=result["intent"],
            entities=result["entities"],
            search_results=result["search_results"],
            response=result["response"],
            count=result["count"],
            status=result["status"],
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/search/employees", response_model=EmployeeResponse)
async def search_employees(request: SearchRequest):
    """Search for employees with optional filters"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        employees = await query_engine.search_employees(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k
        )
        
        return EmployeeResponse(
            employees=employees,
            total_count=len(employees),
            query=request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Employee search failed: {str(e)}")

@app.get("/search/employees/count")
async def count_employees(
    department: Optional[str] = Query(None, description="Filter by department"),
    location: Optional[str] = Query(None, description="Filter by location"),
    position: Optional[str] = Query(None, description="Filter by position")
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
        
        count = query_engine.count_employees(filters)
        
        return {
            "count": count,
            "filters": filters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Count query failed: {str(e)}")

@app.get("/analytics/departments")
async def get_department_analytics():
    """Get department analytics"""
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        from src.core.config import settings
        
        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="hr-employees-index",
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        
        # Get department distribution
        results = search_client.search("*", facets=["department"], top=0)
        
        departments = []
        if results.get_facets():
            for facet in results.get_facets()["department"]:
                departments.append({
                    "department": facet["value"],
                    "count": facet["count"]
                })
        
        return {
            "departments": departments,
            "total_departments": len(departments)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics query failed: {str(e)}")

@app.get("/analytics/positions")
async def get_position_analytics():
    """Get position analytics"""
    try:
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        from src.core.config import settings
        
        search_client = SearchClient(
            endpoint=settings.azure_search_endpoint,
            index_name="hr-employees-index",
            credential=AzureKeyCredential(settings.azure_search_api_key)
        )
        
        # Get position distribution
        results = search_client.search("*", facets=["position"], top=0)
        
        positions = []
        if results.get_facets():
            for facet in results.get_facets()["position"]:
                positions.append({
                    "position": facet["value"],
                    "count": facet["count"]
                })
        
        return {
            "positions": positions,
            "total_positions": len(positions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics query failed: {str(e)}")

@app.get("/search/suggestions")
async def get_search_suggestions(q: str = Query(..., description="Query for suggestions")):
    """Get search suggestions based on partial query"""
    try:
        # Simple suggestion logic - can be enhanced
        suggestions = []
        
        if len(q) >= 2:
            from azure.search.documents import SearchClient
            from azure.core.credentials import AzureKeyCredential
            from src.core.config import settings
            
            search_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name="hr-employees-index",
                credential=AzureKeyCredential(settings.azure_search_api_key)
            )
            
            # Search for partial matches
            results = search_client.search(
                f"{q}*",
                select="full_name,department,position",
                top=5
            )
            
            for result in results:
                suggestions.append({
                    "text": result.get("full_name", ""),
                    "type": "employee",
                    "department": result.get("department", ""),
                    "position": result.get("position", "")
                })
        
        return {
            "suggestions": suggestions,
            "query": q
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

# Development server configuration
if __name__ == "__main__":
    print("🚀 Starting HR Q&A API Server")
    print("=" * 40)
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Interactive API: http://localhost:8000/redoc")
    print("💡 Health Check: http://localhost:8000/health")
    print("=" * 40)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )