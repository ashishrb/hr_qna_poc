#!/usr/bin/env python3
"""
HR Analytics AI Agent
Advanced AI-powered HR analytics and insights generation
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.ai.ollama_client import OllamaClient
from src.database.mongodb_client import MongoDBClient
from src.core.config import settings

class HRAnalyticsAgent:
    """Advanced AI Agent for HR Analytics and Insights"""
    
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.mongodb_client = MongoDBClient()
        self.collections = {
            'personal': 'employee_personal_info',
            'employment': 'employee_employment_info',
            'performance': 'employee_performance_info',
            'compensation': 'employee_compensation_info',
            'attendance': 'employee_attendance_info',
            'learning': 'employee_learning_info',
            'engagement': 'employee_engagement_info',
            'attrition': 'employee_attrition_info'
        }
    
    async def generate_executive_dashboard_insights(self) -> Dict[str, Any]:
        """Generate comprehensive executive dashboard insights"""
        try:
            await self.mongodb_client.connect()
            
            # Get comprehensive analytics data
            analytics_data = await self._get_comprehensive_analytics()
            
            # Generate AI-powered insights
            insights = await self._generate_ai_insights(analytics_data)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "analytics": analytics_data,
                "ai_insights": insights,
                "recommendations": await self._generate_recommendations(analytics_data),
                "risk_alerts": await self._identify_risk_alerts(analytics_data),
                "opportunities": await self._identify_opportunities(analytics_data)
            }
            
        except Exception as e:
            print(f"❌ Error generating executive insights: {e}")
            return {"error": str(e)}
    
    async def _get_comprehensive_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics data from all collections"""
        try:
            # Use the working get_employees method to get all employee data
            from src.search.local_search_client import LocalSearchClient
            search_client = LocalSearchClient()
            
            # Ensure MongoDB connection
            await search_client.mongodb_client.connect()
            
            # Get all employees (limit to 100 for performance)
            employees = await search_client.get_employees(page=1, limit=100)
            
            # Calculate comprehensive analytics
            analytics = {
                "total_employees": len(employees),
                "departments": self._analyze_departments(employees),
                "performance": self._analyze_performance(employees),
                "compensation": self._analyze_compensation(employees),
                "attendance": self._analyze_attendance(employees),
                "learning": self._analyze_learning(employees),
                "engagement": self._analyze_engagement(employees),
                "attrition": self._analyze_attrition(employees),
                "diversity": self._analyze_diversity(employees),
                "retention": self._analyze_retention(employees)
            }
            
            return analytics
            
        except Exception as e:
            print(f"❌ Error getting analytics data: {e}")
            return {}
    
    def _analyze_departments(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze department-wise metrics"""
        dept_stats = {}
        
        for emp in employees:
            dept = emp.get("department", "Unknown")
            if dept not in dept_stats:
                dept_stats[dept] = {
                    "count": 0,
                    "avg_performance": 0,
                    "avg_salary": 0,
                    "avg_engagement": 0,
                    "high_performers": 0,
                    "at_risk": 0,
                    "total_performance": 0,
                    "total_salary": 0,
                    "total_engagement": 0
                }
            
            stats = dept_stats[dept]
            stats["count"] += 1
            
            perf = emp.get("performance_rating", 0)
            salary = emp.get("current_salary", 0)
            engagement = emp.get("engagement_score", 0)
            risk = emp.get("attrition_risk_score", 0)
            
            # Convert to float safely
            try:
                perf_val = float(perf) if perf is not None else 0
                salary_val = float(salary) if salary is not None else 0
                engagement_val = float(engagement) if engagement is not None else 0
                risk_val = float(risk) if risk is not None else 0
            except (ValueError, TypeError):
                perf_val = 0
                salary_val = 0
                engagement_val = 0
                risk_val = 0
            
            stats["total_performance"] += perf_val
            stats["total_salary"] += salary_val
            stats["total_engagement"] += engagement_val
            
            if perf_val >= 4.0:
                stats["high_performers"] += 1
            if risk_val >= 7:
                stats["at_risk"] += 1
        
        # Calculate averages
        for dept, stats in dept_stats.items():
            if stats["count"] > 0:
                stats["avg_performance"] = round(stats["total_performance"] / stats["count"], 2)
                stats["avg_salary"] = round(stats["total_salary"] / stats["count"], 0)
                stats["avg_engagement"] = round(stats["total_engagement"] / stats["count"], 2)
                stats["high_performer_pct"] = round((stats["high_performers"] / stats["count"]) * 100, 1)
                stats["at_risk_pct"] = round((stats["at_risk"] / stats["count"]) * 100, 1)
        
        return dept_stats
    
    def _analyze_performance(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        ratings = []
        kpis = []
        
        for emp in employees:
            rating = emp.get("performance_rating", 0)
            kpi = emp.get("kpis_met_pct", 0)
            
            # Convert to float safely
            try:
                if rating is not None:
                    ratings.append(float(rating))
            except (ValueError, TypeError):
                pass
                
            try:
                if kpi is not None:
                    # Handle percentage strings like "65%"
                    if isinstance(kpi, str) and kpi.endswith('%'):
                        kpi_val = float(kpi[:-1])
                    else:
                        kpi_val = float(kpi)
                    kpis.append(kpi_val)
            except (ValueError, TypeError):
                pass
        
        if not ratings:
            return {}
        
        return {
            "avg_rating": round(sum(ratings) / len(ratings), 2),
            "min_rating": min(ratings),
            "max_rating": max(ratings),
            "high_performers": len([r for r in ratings if r >= 4.0]),
            "low_performers": len([r for r in ratings if r < 3.0]),
            "avg_kpis": round(sum(kpis) / len(kpis), 1) if kpis else 0,
            "performance_distribution": {
                "excellent": len([r for r in ratings if r >= 4.5]),
                "good": len([r for r in ratings if 3.5 <= r < 4.5]),
                "satisfactory": len([r for r in ratings if 3.0 <= r < 3.5]),
                "needs_improvement": len([r for r in ratings if r < 3.0])
            }
        }
    
    def _analyze_compensation(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze compensation metrics"""
        salaries = []
        bonuses = []
        
        for emp in employees:
            salary = emp.get("current_salary", 0)
            bonus = emp.get("bonus_amount", 0)
            
            # Convert to float safely
            try:
                if salary is not None:
                    salaries.append(float(salary))
            except (ValueError, TypeError):
                pass
                
            try:
                if bonus is not None:
                    bonuses.append(float(bonus))
            except (ValueError, TypeError):
                pass
        
        if not salaries:
            return {}
        
        return {
            "avg_salary": round(sum(salaries) / len(salaries), 0),
            "min_salary": min(salaries),
            "max_salary": max(salaries),
            "salary_range": max(salaries) - min(salaries),
            "avg_bonus": round(sum(bonuses) / len(bonuses), 0) if bonuses else 0,
            "bonus_pct": round((len([b for b in bonuses if b > 0]) / len(bonuses)) * 100, 1) if bonuses else 0,
            "salary_quartiles": {
                "q1": sorted(salaries)[len(salaries)//4],
                "median": sorted(salaries)[len(salaries)//2],
                "q3": sorted(salaries)[3*len(salaries)//4]
            }
        }
    
    def _analyze_attendance(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze attendance metrics"""
        attendance = []
        
        for emp in employees:
            att = emp.get("attendance_pct", 0)
            
            # Convert to float safely
            try:
                if att is not None:
                    attendance.append(float(att))
            except (ValueError, TypeError):
                pass
        
        if not attendance:
            return {}
        
        return {
            "avg_attendance": round(sum(attendance) / len(attendance), 1),
            "min_attendance": min(attendance),
            "max_attendance": max(attendance),
            "excellent_attendance": len([a for a in attendance if a >= 98]),
            "good_attendance": len([a for a in attendance if 95 <= a < 98]),
            "poor_attendance": len([a for a in attendance if a < 95])
        }
    
    def _analyze_learning(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze learning and development metrics"""
        courses = []
        certs = []
        
        for emp in employees:
            course = emp.get("courses_completed", 0)
            cert = emp.get("certifications", 0)
            
            # Convert to float safely
            try:
                if course is not None:
                    courses.append(float(course))
            except (ValueError, TypeError):
                pass
                
            try:
                if cert is not None:
                    certs.append(float(cert))
            except (ValueError, TypeError):
                pass
        
        return {
            "avg_courses": round(sum(courses) / len(courses), 1) if courses else 0,
            "avg_certifications": round(sum(certs) / len(certs), 1) if certs else 0,
            "high_learners": len([c for c in courses if c >= 8]),
            "learning_gaps": len([c for c in courses if c < 3])
        }
    
    def _analyze_engagement(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze engagement metrics"""
        engagement = []
        
        for emp in employees:
            eng = emp.get("engagement_score", 0)
            
            # Convert to float safely
            try:
                if eng is not None:
                    engagement.append(float(eng))
            except (ValueError, TypeError):
                pass
        
        if not engagement:
            return {}
        
        return {
            "avg_engagement": round(sum(engagement) / len(engagement), 2),
            "highly_engaged": len([e for e in engagement if e >= 4.0]),
            "moderately_engaged": len([e for e in engagement if 3.0 <= e < 4.0]),
            "disengaged": len([e for e in engagement if e < 3.0])
        }
    
    def _analyze_attrition(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze attrition risk metrics"""
        risks = []
        
        for emp in employees:
            risk = emp.get("attrition_risk_score", 0)
            
            # Convert to float safely
            try:
                if risk is not None:
                    risks.append(float(risk))
            except (ValueError, TypeError):
                pass
        
        if not risks:
            return {}
        
        return {
            "avg_risk_score": round(sum(risks) / len(risks), 2),
            "high_risk": len([r for r in risks if r >= 7]),
            "medium_risk": len([r for r in risks if 4 <= r < 7]),
            "low_risk": len([r for r in risks if r < 4]),
            "risk_distribution": {
                "critical": len([r for r in risks if r >= 8]),
                "high": len([r for r in risks if 6 <= r < 8]),
                "medium": len([r for r in risks if 4 <= r < 6]),
                "low": len([r for r in risks if r < 4])
            }
        }
    
    def _analyze_diversity(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze diversity metrics"""
        genders = [emp.get("gender", "Unknown") for emp in employees]
        locations = [emp.get("location", "Unknown") for emp in employees]
        ages = [emp.get("age", 0) for emp in employees if emp.get("age")]
        
        gender_dist = {}
        for gender in genders:
            gender_dist[gender] = gender_dist.get(gender, 0) + 1
        
        location_dist = {}
        for location in locations:
            location_dist[location] = location_dist.get(location, 0) + 1
        
        return {
            "gender_distribution": gender_dist,
            "location_distribution": location_dist,
            "avg_age": round(sum(ages) / len(ages), 1) if ages else 0,
            "age_groups": {
                "young": len([a for a in ages if a < 30]),
                "mid": len([a for a in ages if 30 <= a < 50]),
                "senior": len([a for a in ages if a >= 50])
            }
        }
    
    def _analyze_retention(self, employees: List[Dict]) -> Dict[str, Any]:
        """Analyze retention metrics"""
        # Calculate tenure distribution
        tenures = []
        for emp in employees:
            joining_date = emp.get("joining_date")
            if joining_date:
                try:
                    join_date = datetime.fromisoformat(joining_date.replace('Z', '+00:00'))
                    tenure_days = (datetime.now() - join_date).days
                    tenures.append(tenure_days)
                except:
                    pass
        
        return {
            "avg_tenure_days": round(sum(tenures) / len(tenures), 0) if tenures else 0,
            "tenure_distribution": {
                "new": len([t for t in tenures if t < 365]),
                "experienced": len([t for t in tenures if 365 <= t < 1095]),
                "veteran": len([t for t in tenures if t >= 1095])
            }
        }
    
    async def _generate_ai_insights(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered insights from analytics data"""
        try:
            prompt = f"""
            As an expert HR Analytics AI, analyze the following comprehensive HR data and provide strategic insights:
            
            {json.dumps(analytics_data, indent=2)}
            
            Provide:
            1. KEY INSIGHTS (3-5 bullet points)
            2. PERFORMANCE ANALYSIS (strengths and concerns)
            3. RISK ASSESSMENT (attrition and engagement risks)
            4. OPPORTUNITIES (areas for improvement)
            5. STRATEGIC RECOMMENDATIONS (actionable next steps)
            
            Format as executive-ready analysis suitable for C-level presentation.
            """
            
            response = self.ollama_client.generate_text(
                prompt=prompt,
                query_type="complex_analytics",
                query_complexity="high"
            )
            
            return {
                "analysis": response,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error generating AI insights: {e}")
            return {"error": str(e)}
    
    async def _generate_recommendations(self, analytics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        # Performance recommendations
        perf_data = analytics_data.get("performance", {})
        if perf_data.get("low_performers", 0) > 0:
            recommendations.append({
                "category": "Performance Management",
                "priority": "High",
                "title": "Address Low Performers",
                "description": f"Focus on {perf_data['low_performers']} employees with performance ratings below 3.0",
                "action": "Implement performance improvement plans and additional support"
            })
        
        # Attrition recommendations
        attrition_data = analytics_data.get("attrition", {})
        if attrition_data.get("high_risk", 0) > 0:
            recommendations.append({
                "category": "Retention",
                "priority": "Critical",
                "title": "High Attrition Risk",
                "description": f"{attrition_data['high_risk']} employees at high risk of leaving",
                "action": "Conduct retention interviews and implement retention strategies"
            })
        
        # Engagement recommendations
        engagement_data = analytics_data.get("engagement", {})
        if engagement_data.get("disengaged", 0) > 0:
            recommendations.append({
                "category": "Employee Engagement",
                "priority": "Medium",
                "title": "Improve Employee Engagement",
                "description": f"{engagement_data['disengaged']} employees showing low engagement",
                "action": "Implement engagement surveys and team-building initiatives"
            })
        
        return recommendations
    
    async def _identify_risk_alerts(self, analytics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical risk alerts"""
        alerts = []
        
        # High attrition risk alert
        attrition_data = analytics_data.get("attrition", {})
        if attrition_data.get("high_risk", 0) > 5:
            alerts.append({
                "type": "Critical",
                "category": "Attrition Risk",
                "message": f"High attrition risk detected: {attrition_data['high_risk']} employees at risk",
                "impact": "Potential loss of key talent and knowledge"
            })
        
        # Low performance alert
        perf_data = analytics_data.get("performance", {})
        if perf_data.get("low_performers", 0) > 3:
            alerts.append({
                "type": "High",
                "category": "Performance",
                "message": f"Multiple low performers identified: {perf_data['low_performers']} employees",
                "impact": "Team productivity and morale concerns"
            })
        
        return alerts
    
    async def _identify_opportunities(self, analytics_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify growth opportunities"""
        opportunities = []
        
        # High performer opportunities
        perf_data = analytics_data.get("performance", {})
        if perf_data.get("high_performers", 0) > 0:
            opportunities.append({
                "type": "Growth",
                "category": "Talent Development",
                "title": "High Performer Development",
                "description": f"{perf_data['high_performers']} high performers ready for advancement",
                "benefit": "Accelerated career development and retention"
            })
        
        # Learning opportunities
        learning_data = analytics_data.get("learning", {})
        if learning_data.get("learning_gaps", 0) > 0:
            opportunities.append({
                "type": "Development",
                "category": "Skills Enhancement",
                "title": "Learning & Development Investment",
                "description": f"{learning_data['learning_gaps']} employees need skill development",
                "benefit": "Improved capabilities and job satisfaction"
            })
        
        return opportunities

# Global instance
hr_analytics_agent = HRAnalyticsAgent()
