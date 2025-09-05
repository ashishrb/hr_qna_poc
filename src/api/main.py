# src/api/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import uvicorn
import sys
import os
import json
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.query.ollama_query_engine import OllamaHRQueryEngine
from src.search.local_search_client import LocalSearchClient
from src.ai.hr_analytics_agent import hr_analytics_agent

# Initialize FastAPI app
app = FastAPI(
    title="HR Q&A System API",
    description="Intelligent HR Query and Response System with Ollama AI",
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize components
query_engine = OllamaHRQueryEngine()
search_client = LocalSearchClient()

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
    response_time: float
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
@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse('static/index.html')

@app.get("/api", response_model=HealthResponse)
async def api_info():
    """API information endpoint"""
    return HealthResponse(
        status="active",
        message="HR Q&A System API is running",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        return HealthResponse(
            status="healthy",
            message="All systems operational",
            version="1.0.0"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
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
            response_time=result.get("response_time", 0.0),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.post("/api/search", response_model=EmployeeResponse)
async def search_employees(request: SearchRequest):
    """Search for employees with optional filters"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
        # Use local search client
        results = await search_client.search(
            query=request.query,
            filters=request.filters or {},
            top_k=request.top_k
        )
        
        return EmployeeResponse(
            employees=results,
            total_count=len(results),
            query=request.query
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Employee search failed: {str(e)}")

@app.get("/api/employee-count")
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
        
        count = await search_client.get_document_count(filters)
        
        return {
            "count": count,
            "filters": filters
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Count query failed: {str(e)}")

@app.get("/api/analytics/departments")
async def get_department_analytics():
    """Get department analytics"""
    try:
        # Get employees data and calculate department analytics
        employees_data = await search_client.get_employees(page=1, limit=100)
        
        # Calculate department statistics
        dept_stats = {}
        total_employees = len(employees_data)
        
        for emp in employees_data:
            dept = emp.get("department", "Unknown")
            if dept not in dept_stats:
                dept_stats[dept] = {
                    "employee_count": 0,
                    "total_performance": 0,
                    "total_kpis": 0,
                    "performance_count": 0,
                    "kpis_count": 0
                }
            
            dept_stats[dept]["employee_count"] += 1
            
            # Add performance data if available
            perf_rating = emp.get("performance_rating")
            if perf_rating is not None:
                try:
                    perf_val = float(perf_rating)
                    dept_stats[dept]["total_performance"] += perf_val
                    dept_stats[dept]["performance_count"] += 1
                except (ValueError, TypeError):
                    pass
            
            kpis = emp.get("kpis_met_pct")
            if kpis is not None:
                try:
                    if isinstance(kpis, str) and kpis.endswith('%'):
                        kpi_val = float(kpis[:-1])
                    else:
                        kpi_val = float(kpis)
                    dept_stats[dept]["total_kpis"] += kpi_val
                    dept_stats[dept]["kpis_count"] += 1
                except (ValueError, TypeError):
                    pass
        
        # Convert to final format
        departments = []
        for dept, stats in dept_stats.items():
            avg_performance = round(stats["total_performance"] / stats["performance_count"], 2) if stats["performance_count"] > 0 else 0
            avg_kpis = round(stats["total_kpis"] / stats["kpis_count"], 1) if stats["kpis_count"] > 0 else 0
            
            departments.append({
                "department": dept,
                "employee_count": stats["employee_count"],
                "avg_performance": avg_performance,
                "avg_kpis": avg_kpis
            })
        
        # Sort by employee count
        departments.sort(key=lambda x: x["employee_count"], reverse=True)
        
        return {
            "departments": departments,
            "total_departments": len(departments),
            "total_employees": total_employees
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Department analytics failed: {str(e)}")

@app.get("/api/analytics/performance")
async def get_performance_analytics():
    """Get performance analytics"""
    try:
        # Get employees data and calculate performance analytics
        employees_data = await search_client.get_employees(page=1, limit=100)
        
        # Calculate performance statistics
        total_employees = len(employees_data)
        performance_ratings = []
        kpis_values = []
        high_performers = 0
        low_performers = 0
        
        for emp in employees_data:
            perf_rating = emp.get("performance_rating")
            if perf_rating is not None:
                try:
                    perf_val = float(perf_rating)
                    performance_ratings.append(perf_val)
                    if perf_val >= 4.0:
                        high_performers += 1
                    elif perf_val < 3.0:
                        low_performers += 1
                except (ValueError, TypeError):
                    pass
            
            kpis = emp.get("kpis_met_pct")
            if kpis is not None:
                try:
                    if isinstance(kpis, str) and kpis.endswith('%'):
                        kpi_val = float(kpis[:-1])
                    else:
                        kpi_val = float(kpis)
                    kpis_values.append(kpi_val)
                except (ValueError, TypeError):
                    pass
        
        # Calculate statistics
        avg_performance = round(sum(performance_ratings) / len(performance_ratings), 2) if performance_ratings else 0
        min_performance = min(performance_ratings) if performance_ratings else 0
        max_performance = max(performance_ratings) if performance_ratings else 0
        avg_kpis = round(sum(kpis_values) / len(kpis_values), 1) if kpis_values else 0
        
        high_performer_pct = round((high_performers / total_employees) * 100, 1) if total_employees > 0 else 0
        low_performer_pct = round((low_performers / total_employees) * 100, 1) if total_employees > 0 else 0
        
        return {
            "total_employees": total_employees,
            "avg_performance": avg_performance,
            "min_performance": min_performance,
            "max_performance": max_performance,
            "avg_kpis": avg_kpis,
            "high_performers": high_performers,
            "low_performers": low_performers,
            "high_performer_pct": high_performer_pct,
            "low_performer_pct": low_performer_pct
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance analytics failed: {str(e)}")

@app.get("/api/analytics/salary")
async def get_salary_analytics():
    """Get salary analytics"""
    try:
        # Get employees data and calculate salary analytics
        employees_data = await search_client.get_employees(page=1, limit=100)
        
        # Calculate salary statistics
        total_employees = len(employees_data)
        salaries = []
        dept_salaries = {}
        
        for emp in employees_data:
            salary = emp.get("current_salary")
            if salary is not None:
                try:
                    salary_val = float(salary)
                    salaries.append(salary_val)
                    
                    # Group by department
                    dept = emp.get("department", "Unknown")
                    if dept not in dept_salaries:
                        dept_salaries[dept] = []
                    dept_salaries[dept].append(salary_val)
                except (ValueError, TypeError):
                    pass
        
        # Calculate overall statistics
        avg_salary = round(sum(salaries) / len(salaries), 0) if salaries else 0
        min_salary = min(salaries) if salaries else 0
        max_salary = max(salaries) if salaries else 0
        salary_range = max_salary - min_salary
        
        # Calculate department-wise analytics
        dept_analytics = []
        for dept, dept_salary_list in dept_salaries.items():
            if dept_salary_list:
                dept_analytics.append({
                    "department": dept,
                    "avg_salary": round(sum(dept_salary_list) / len(dept_salary_list), 0),
                    "employee_count": len(dept_salary_list),
                    "min_salary": min(dept_salary_list),
                    "max_salary": max(dept_salary_list)
                })
        
        # Sort by average salary
        dept_analytics.sort(key=lambda x: x["avg_salary"], reverse=True)
        
        return {
            "total_employees": total_employees,
            "avg_salary": avg_salary,
            "min_salary": min_salary,
            "max_salary": max_salary,
            "salary_range": salary_range,
            "department_analytics": dept_analytics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Salary analytics failed: {str(e)}")

@app.get("/api/search/suggestions")
async def get_search_suggestions(q: str = Query(..., description="Query for suggestions")):
    """Get search suggestions based on partial query"""
    try:
        if len(q) >= 2:
            suggestions = await search_client.suggest(q)
            return {
                "suggestions": suggestions,
                "query": q
            }
        else:
            return {
                "suggestions": [],
                "query": q
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

# Additional HR 360 view endpoints
@app.get("/api/analytics/attrition")
async def get_attrition_analytics():
    """Get attrition risk analytics"""
    try:
        # Get employees data and calculate attrition analytics
        employees_data = await search_client.get_employees(page=1, limit=100)
        
        # Calculate attrition statistics
        total_employees = len(employees_data)
        risk_scores = []
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        dept_risks = {}
        
        for emp in employees_data:
            risk_score = emp.get("attrition_risk_score")
            if risk_score is not None:
                try:
                    risk_val = float(risk_score)
                    risk_scores.append(risk_val)
                    
                    # Categorize risk levels
                    if risk_val >= 7:
                        high_risk += 1
                    elif risk_val >= 4:
                        medium_risk += 1
                    else:
                        low_risk += 1
                
                    # Group by department
                    dept = emp.get("department", "Unknown")
                    if dept not in dept_risks:
                        dept_risks[dept] = []
                    dept_risks[dept].append(risk_val)
                except (ValueError, TypeError):
                    pass
        
        # Calculate overall statistics
        avg_risk_score = round(sum(risk_scores) / len(risk_scores), 2) if risk_scores else 0
        high_risk_pct = round((high_risk / total_employees) * 100, 1) if total_employees > 0 else 0
        medium_risk_pct = round((medium_risk / total_employees) * 100, 1) if total_employees > 0 else 0
        low_risk_pct = round((low_risk / total_employees) * 100, 1) if total_employees > 0 else 0
        
        # Calculate department-wise analytics
        dept_analytics = []
        for dept, dept_risk_list in dept_risks.items():
            if dept_risk_list:
                dept_analytics.append({
                    "department": dept,
                    "avg_risk": round(sum(dept_risk_list) / len(dept_risk_list), 2),
                    "employee_count": len(dept_risk_list),
                    "high_risk_count": sum(1 for r in dept_risk_list if r >= 7)
                })
        
        # Sort by average risk
        dept_analytics.sort(key=lambda x: x["avg_risk"], reverse=True)
        
        return {
            "total_employees": total_employees,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk,
            "avg_risk_score": avg_risk_score,
            "high_risk_pct": high_risk_pct,
            "medium_risk_pct": medium_risk_pct,
            "low_risk_pct": low_risk_pct,
            "department_analytics": dept_analytics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attrition analytics failed: {str(e)}")

@app.get("/api/employee/{employee_id}")
async def get_employee_details(employee_id: str):
    """Get detailed information for a specific employee"""
    try:
        # Get comprehensive employee data by joining all collections
        employee_data = await search_client.get_employee_details(employee_id)
        
        if not employee_data:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        return employee_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employee details: {str(e)}")

@app.post("/api/employee")
async def add_employee(employee_data: Dict[str, Any]):
    """Add a new employee"""
    try:
        # Generate a new employee ID
        from datetime import datetime
        import random
        
        # Get the next employee ID
        employees = await search_client.get_employees(page=1, limit=1000)
        existing_ids = [emp.get("employee_id", "") for emp in employees if emp.get("employee_id")]
        next_id = f"EMP{len(existing_ids) + 1:04d}"
        
        # Create employee data structure
        personal_data = {
            "employee_id": next_id,
            "full_name": employee_data.get("full_name", "New Employee"),
            "email": employee_data.get("email", f"employee{len(existing_ids) + 1}@company.com"),
            "age": employee_data.get("age", 30),
            "gender": employee_data.get("gender", "Other"),
            "location": employee_data.get("location", "Remote"),
            "contact_number": employee_data.get("contact_number", "+1-555-0123"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        employment_data = {
            "employee_id": next_id,
            "department": employee_data.get("department", "General"),
            "role": employee_data.get("role", "Employee"),
            "grade_band": employee_data.get("grade_band", "A1"),
            "employment_type": employee_data.get("employment_type", "Full-time"),
            "manager_id": employee_data.get("manager_id"),
            "joining_date": datetime.utcnow(),
            "work_mode": employee_data.get("work_mode", "Hybrid"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        performance_data = {
            "employee_id": next_id,
            "performance_rating": employee_data.get("performance_rating", 3.5),
            "kpis_met_pct": employee_data.get("kpis_met_pct", "75%"),
            "promotions_count": 0,
            "awards": "None",
            "improvement_areas": "None",
            "last_review_date": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        compensation_data = {
            "employee_id": next_id,
            "current_salary": employee_data.get("current_salary", 75000),
            "bonus_amount": employee_data.get("bonus_amount", 0),
            "stock_options": employee_data.get("stock_options", 0),
            "benefits": employee_data.get("benefits", "Standard"),
            "last_salary_review": datetime.utcnow(),
            "next_salary_review": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        attendance_data = {
            "employee_id": next_id,
            "attendance_pct": employee_data.get("attendance_pct", 95.0),
            "days_present": employee_data.get("days_present", 20),
            "days_absent": employee_data.get("days_absent", 1),
            "late_arrivals": employee_data.get("late_arrivals", 0),
            "early_departures": employee_data.get("early_departures", 0),
            "overtime_hours": employee_data.get("overtime_hours", 0),
            "vacation_days_taken": employee_data.get("vacation_days_taken", 0),
            "vacation_days_remaining": employee_data.get("vacation_days_remaining", 20),
            "sick_days_taken": employee_data.get("sick_days_taken", 0),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        learning_data = {
            "employee_id": next_id,
            "courses_completed": employee_data.get("courses_completed", 0),
            "certifications": employee_data.get("certifications", 0),
            "skills_developed": employee_data.get("skills_developed", []),
            "training_hours": employee_data.get("training_hours", 0),
            "learning_budget_used": employee_data.get("learning_budget_used", 0),
            "learning_budget_allocated": employee_data.get("learning_budget_allocated", 1000),
            "mentor": employee_data.get("mentor"),
            "mentee": employee_data.get("mentee"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        engagement_data = {
            "employee_id": next_id,
            "engagement_score": employee_data.get("engagement_score", 4.0),
            "job_satisfaction": employee_data.get("job_satisfaction", 4.0),
            "team_satisfaction": employee_data.get("team_satisfaction", 4.0),
            "manager_satisfaction": employee_data.get("manager_satisfaction", 4.0),
            "company_satisfaction": employee_data.get("company_satisfaction", 4.0),
            "recommendation_score": employee_data.get("recommendation_score", 4.0),
            "feedback_given": employee_data.get("feedback_given", 0),
            "feedback_received": employee_data.get("feedback_received", 0),
            "participation_events": employee_data.get("participation_events", 0),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        attrition_data = {
            "employee_id": next_id,
            "attrition_risk_score": employee_data.get("attrition_risk_score", 3.0),
            "risk_factors": employee_data.get("risk_factors", []),
            "retention_probability": employee_data.get("retention_probability", 85.0),
            "last_engagement_date": datetime.utcnow(),
            "internal_transfer_requests": employee_data.get("internal_transfer_requests", 0),
            "external_job_applications": employee_data.get("external_job_applications", 0),
            "exit_interview_score": employee_data.get("exit_interview_score", 0),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert all employee data
        await search_client.mongodb_client.insert_documents("employee_personal_info", [personal_data])
        await search_client.mongodb_client.insert_documents("employee_employment_info", [employment_data])
        await search_client.mongodb_client.insert_documents("employee_performance_info", [performance_data])
        await search_client.mongodb_client.insert_documents("employee_compensation_info", [compensation_data])
        await search_client.mongodb_client.insert_documents("employee_attendance_info", [attendance_data])
        await search_client.mongodb_client.insert_documents("employee_learning_info", [learning_data])
        await search_client.mongodb_client.insert_documents("employee_engagement_info", [engagement_data])
        await search_client.mongodb_client.insert_documents("employee_attrition_info", [attrition_data])
        
        return {
            "message": "Employee added successfully",
            "employee_id": next_id,
            "employee_data": personal_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add employee: {str(e)}")

@app.get("/api/employees")
async def get_all_employees(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of employees per page"),
    department: str = Query(None, description="Filter by department"),
    role: str = Query(None, description="Filter by role")
):
    """Get paginated list of all employees with optional filters"""
    try:
        filters = {}
        if department:
            filters["department"] = department
        if role:
            filters["role"] = role
            
        employees = await search_client.get_employees(page=page, limit=limit, filters=filters)
        
        return {
            "employees": employees,
            "page": page,
            "limit": limit,
            "total": len(employees)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get employees: {str(e)}")

@app.get("/api/analytics/engagement")
async def get_engagement_analytics():
    """Get engagement analytics"""
    try:
        engagement_data = await search_client.get_facets("engagement_score")
        
        return {
            "engagement_scores": engagement_data,
            "total_scores": len(engagement_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engagement analytics failed: {str(e)}")

# Advanced AI-Powered Analytics Endpoints
@app.get("/api/analytics/executive-dashboard")
async def get_executive_dashboard():
    """Get comprehensive executive dashboard with AI insights"""
    try:
        insights = await hr_analytics_agent.generate_executive_dashboard_insights()
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Executive dashboard failed: {str(e)}")

@app.get("/api/analytics/predictive-insights")
async def get_predictive_insights():
    """Get AI-powered predictive insights"""
    try:
        # Get comprehensive analytics
        analytics_data = await hr_analytics_agent._get_comprehensive_analytics()
        
        # Generate predictive insights
        prompt = f"""
        As an expert HR Predictive Analytics AI, analyze the following data and provide predictive insights:
        
        {json.dumps(analytics_data, indent=2)}
        
        Provide predictions for:
        1. ATTRITION RISK (next 6 months)
        2. PERFORMANCE TRENDS (upcoming quarter)
        3. ENGAGEMENT FORECAST (next 3 months)
        4. RETENTION PROBABILITY (by department)
        5. GROWTH OPPORTUNITIES (talent pipeline)
        
        Format as executive-ready predictive analysis with confidence levels.
        """
        
        response = query_engine.ai_client.generate_text(
            prompt=prompt,
            query_type="complex_analytics",
            query_complexity="high"
        )
        
        return {
            "predictions": response,
            "confidence_level": "High",
            "generated_at": datetime.utcnow().isoformat(),
            "data_points": analytics_data.get("total_employees", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Predictive insights failed: {str(e)}")

@app.get("/api/analytics/talent-intelligence")
async def get_talent_intelligence():
    """Get AI-powered talent intelligence report"""
    try:
        # Get comprehensive analytics
        analytics_data = await hr_analytics_agent._get_comprehensive_analytics()
        
        # Generate talent intelligence
        prompt = f"""
        As an expert Talent Intelligence AI, analyze the following HR data and provide comprehensive talent insights:
        
        {json.dumps(analytics_data, indent=2)}
        
        Provide analysis for:
        1. TALENT PORTFOLIO (skills, capabilities, potential)
        2. SUCCESSION PLANNING (leadership pipeline)
        3. SKILL GAPS (critical competencies needed)
        4. DEVELOPMENT ROADMAPS (individual growth paths)
        5. TALENT ACQUISITION STRATEGY (hiring priorities)
        
        Format as strategic talent intelligence report for executive leadership.
        """
        
        response = query_engine.ai_client.generate_text(
            prompt=prompt,
            query_type="complex_analytics",
            query_complexity="high"
        )
        
        return {
            "talent_intelligence": response,
            "analysis_type": "Comprehensive Talent Assessment",
            "generated_at": datetime.utcnow().isoformat(),
            "scope": "Organization-wide talent analysis"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Talent intelligence failed: {str(e)}")

@app.get("/api/analytics/workforce-optimization")
async def get_workforce_optimization():
    """Get AI-powered workforce optimization recommendations"""
    try:
        # Get comprehensive analytics
        analytics_data = await hr_analytics_agent._get_comprehensive_analytics()
        
        # Generate optimization recommendations
        prompt = f"""
        As an expert Workforce Optimization AI, analyze the following data and provide optimization strategies:
        
        {json.dumps(analytics_data, indent=2)}
        
        Provide optimization strategies for:
        1. WORKFORCE PLANNING (headcount, structure, roles)
        2. PRODUCTIVITY ENHANCEMENT (process improvements)
        3. COST OPTIMIZATION (compensation, benefits, efficiency)
        4. ORGANIZATIONAL DESIGN (structure, reporting, teams)
        5. PERFORMANCE OPTIMIZATION (goals, metrics, processes)
        
        Format as actionable workforce optimization plan with ROI projections.
        """
        
        response = query_engine.ai_client.generate_text(
            prompt=prompt,
            query_type="complex_analytics",
            query_complexity="high"
        )
        
        return {
            "optimization_plan": response,
            "focus_areas": ["Productivity", "Cost", "Structure", "Performance"],
            "generated_at": datetime.utcnow().isoformat(),
            "implementation_timeline": "90 days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workforce optimization failed: {str(e)}")

@app.get("/api/analytics/risk-assessment")
async def get_risk_assessment():
    """Get comprehensive HR risk assessment"""
    try:
        # Get comprehensive analytics
        analytics_data = await hr_analytics_agent._get_comprehensive_analytics()
        
        # Generate risk assessment
        prompt = f"""
        As an expert HR Risk Assessment AI, analyze the following data and provide comprehensive risk analysis:
        
        {json.dumps(analytics_data, indent=2)}
        
        Assess risks in:
        1. ATTRITION RISK (talent loss probability)
        2. PERFORMANCE RISK (productivity concerns)
        3. COMPLIANCE RISK (regulatory, policy)
        4. ENGAGEMENT RISK (morale, satisfaction)
        5. SUCCESSION RISK (leadership gaps)
        
        Format as executive risk assessment with mitigation strategies.
        """
        
        response = query_engine.ai_client.generate_text(
            prompt=prompt,
            query_type="complex_analytics",
            query_complexity="high"
        )
        
        return {
            "risk_assessment": response,
            "risk_levels": ["Low", "Medium", "High", "Critical"],
            "generated_at": datetime.utcnow().isoformat(),
            "assessment_scope": "Comprehensive HR risk analysis"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

@app.get("/api/employees")
async def get_all_employees(
    limit: int = Query(10, description="Number of employees to return"),
    offset: int = Query(0, description="Number of employees to skip")
):
    """Get all employees with pagination"""
    try:
        # Get employees from MongoDB
        employees = await search_client.search("*", top_k=limit)
        
        return {
            "employees": employees,
            "total_count": len(employees),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get employees failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)