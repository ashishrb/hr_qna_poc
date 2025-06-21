# src/database/collections.py
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.database.mongodb_client import mongodb_client

class EmployeeCollections:
    """Handles all employee-related collections"""
    
    def __init__(self):
        self.collections = {
            'personal_info': 'personal_info',
            'employment': 'employment', 
            'learning': 'learning',
            'experience': 'experience',
            'performance': 'performance',
            'engagement': 'engagement',
            'compensation': 'compensation',
            'attendance': 'attendance',
            'attrition': 'attrition',
            'project_history': 'project_history'
        }
    
    async def get_employee_personal_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee personal information"""
        return await mongodb_client.find_document(
            self.collections['personal_info'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_employment_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee employment information"""
        return await mongodb_client.find_document(
            self.collections['employment'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_learning_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee learning and certifications"""
        return await mongodb_client.find_document(
            self.collections['learning'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_experience_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee experience information"""
        return await mongodb_client.find_document(
            self.collections['experience'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_performance_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee performance information"""
        return await mongodb_client.find_document(
            self.collections['performance'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_engagement_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee engagement information"""
        return await mongodb_client.find_document(
            self.collections['engagement'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_compensation_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee compensation information"""
        return await mongodb_client.find_document(
            self.collections['compensation'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_attendance_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee attendance information"""
        return await mongodb_client.find_document(
            self.collections['attendance'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_attrition_info(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee attrition risk information"""
        return await mongodb_client.find_document(
            self.collections['attrition'], 
            {"employee_id": employee_id}
        )
    
    async def get_employee_project_history(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get employee project history"""
        return await mongodb_client.find_documents(
            self.collections['project_history'], 
            {"employee_id": employee_id}
        )
    
    async def get_complete_employee_profile(self, employee_id: str) -> Dict[str, Any]:
        """Get complete employee profile from all collections"""
        profile = {"employee_id": employee_id}
        
        # Personal Info
        personal = await self.get_employee_personal_info(employee_id)
        if personal:
            profile.update({
                "full_name": personal.get("full_name"),
                "email": personal.get("email"),
                "location": personal.get("location"),
                "age": personal.get("age"),
                "gender": personal.get("gender"),
                "contact_number": personal.get("contact_number"),
                "address": personal.get("address")
            })
        
        # Employment Info
        employment = await self.get_employee_employment_info(employee_id)
        if employment:
            profile.update({
                "department": employment.get("department"),
                "role": employment.get("role"),
                "grade_band": employment.get("grade_band"),
                "employment_type": employment.get("employment_type"),
                "manager_id": employment.get("manager_id"),
                "joining_date": employment.get("joining_date"),
                "work_mode": employment.get("work_mode")
            })
        
        # Learning Info
        learning = await self.get_employee_learning_info(employee_id)
        if learning:
            profile.update({
                "certifications": learning.get("certifications"),
                "courses_completed": learning.get("courses_completed"),
                "learning_hours_ytd": learning.get("learning_hours_ytd"),
                "internal_trainings": learning.get("internal_trainings")
            })
        
        # Experience Info
        experience = await self.get_employee_experience_info(employee_id)
        if experience:
            profile.update({
                "total_experience_years": experience.get("total_experience_years"),
                "years_in_current_company": experience.get("years_in_current_company"),
                "years_in_current_skillset": experience.get("years_in_current_skillset"),
                "known_skills_count": experience.get("known_skills_count"),
                "previous_companies_resigned": experience.get("previous_companies_resigned")
            })
        
        # Performance Info
        performance = await self.get_employee_performance_info(employee_id)
        if performance:
            profile.update({
                "performance_rating": performance.get("performance_rating"),
                "kpis_met_pct": performance.get("kpis_met_pct"),
                "promotions_count": performance.get("promotions_count"),
                "awards": performance.get("awards"),
                "improvement_areas": performance.get("improvement_areas"),
                "last_review_date": performance.get("last_review_date")
            })
        
        # Engagement Info
        engagement = await self.get_employee_engagement_info(employee_id)
        if engagement:
            profile.update({
                "current_project": engagement.get("current_project"),
                "allocation_percentage": engagement.get("allocation_percentage"),
                "peer_review_score": engagement.get("peer_review_score"),
                "manager_feedback": engagement.get("manager_feedback"),
                "engagement_score": engagement.get("engagement_score"),
                "days_on_bench": engagement.get("days_on_bench")
            })
        
        # Compensation Info (be careful with sensitive data)
        compensation = await self.get_employee_compensation_info(employee_id)
        if compensation:
            profile.update({
                "current_salary": compensation.get("current_salary"),
                "bonus": compensation.get("bonus"),
                "total_ctc": compensation.get("total_ctc"),
                "currency": compensation.get("currency"),
                "last_appraisal_date": compensation.get("last_appraisal_date")
            })
        
        # Attendance Info
        attendance = await self.get_employee_attendance_info(employee_id)
        if attendance:
            profile.update({
                "monthly_attendance_pct": attendance.get("monthly_attendance_pct"),
                "leave_days_taken": attendance.get("leave_days_taken"),
                "leave_balance": attendance.get("leave_balance"),
                "leave_pattern": attendance.get("leave_pattern")
            })
        
        # Attrition Info
        attrition = await self.get_employee_attrition_info(employee_id)
        if attrition:
            profile.update({
                "attrition_risk_score": attrition.get("attrition_risk_score"),
                "exit_intent_flag": attrition.get("exit_intent_flag"),
                "retention_plan": attrition.get("retention_plan"),
                "internal_transfers": attrition.get("internal_transfers")
            })
        
        # Project History
        projects = await self.get_employee_project_history(employee_id)
        profile["project_history"] = projects
        
        return profile
    
    async def get_all_employee_ids(self) -> List[str]:
        """Get all unique employee IDs across collections"""
        employee_ids = set()
        
        for collection_name in self.collections.values():
            try:
                documents = await mongodb_client.find_documents(
                    collection_name, 
                    {}, 
                    limit=None
                )
                for doc in documents:
                    if doc.get("employee_id"):
                        employee_ids.add(doc["employee_id"])
            except Exception as e:
                print(f"❌ Error getting employee IDs from {collection_name}: {e}")
        
        return list(employee_ids)
    
    async def get_employees_by_department(self, department: str) -> List[str]:
        """Get employee IDs by department"""
        try:
            documents = await mongodb_client.find_documents(
                self.collections['employment'], 
                {"department": department}
            )
            return [doc["employee_id"] for doc in documents if doc.get("employee_id")]
        except Exception as e:
            print(f"❌ Error getting employees by department: {e}")
            return []
    
    async def get_employees_by_role(self, role: str) -> List[str]:
        """Get employee IDs by role"""
        try:
            documents = await mongodb_client.find_documents(
                self.collections['employment'], 
                {"role": role}
            )
            return [doc["employee_id"] for doc in documents if doc.get("employee_id")]
        except Exception as e:
            print(f"❌ Error getting employees by role: {e}")
            return []
    
    async def get_employees_by_certification(self, certification: str) -> List[str]:
        """Get employee IDs by certification"""
        try:
            documents = await mongodb_client.find_documents(
                self.collections['learning'], 
                {"certifications": {"$regex": certification, "$options": "i"}}
            )
            return [doc["employee_id"] for doc in documents if doc.get("employee_id")]
        except Exception as e:
            print(f"❌ Error getting employees by certification: {e}")
            return []
    
    async def get_employees_by_location(self, location: str) -> List[str]:
        """Get employee IDs by location"""
        try:
            documents = await mongodb_client.find_documents(
                self.collections['personal_info'], 
                {"location": {"$regex": location, "$options": "i"}}
            )
            return [doc["employee_id"] for doc in documents if doc.get("employee_id")]
        except Exception as e:
            print(f"❌ Error getting employees by location: {e}")
            return []
    
    async def get_department_statistics(self) -> Dict[str, int]:
        """Get department-wise employee count"""
        try:
            pipeline = [
                {"$group": {"_id": "$department", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            collection = await mongodb_client.get_collection(self.collections['employment'])
            cursor = collection.aggregate(pipeline)
            
            stats = {}
            async for doc in cursor:
                if doc["_id"]:  # Skip null departments
                    stats[doc["_id"]] = doc["count"]
            
            return stats
        except Exception as e:
            print(f"❌ Error getting department statistics: {e}")
            return {}
    
    async def get_role_statistics(self) -> Dict[str, int]:
        """Get role-wise employee count"""
        try:
            pipeline = [
                {"$group": {"_id": "$role", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            
            collection = await mongodb_client.get_collection(self.collections['employment'])
            cursor = collection.aggregate(pipeline)
            
            stats = {}
            async for doc in cursor:
                if doc["_id"]:  # Skip null roles
                    stats[doc["_id"]] = doc["count"]
            
            return stats
        except Exception as e:
            print(f"❌ Error getting role statistics: {e}")
            return {}
    
    async def update_employee_data(self, employee_id: str, collection_type: str, update_data: Dict[str, Any]) -> bool:
        """Update employee data in specific collection"""
        if collection_type not in self.collections:
            print(f"❌ Invalid collection type: {collection_type}")
            return False
        
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            success = await mongodb_client.update_document(
                self.collections[collection_type],
                {"employee_id": employee_id},
                update_data
            )
            return success
        except Exception as e:
            print(f"❌ Error updating employee data: {e}")
            return False

# Global instance
employee_collections = EmployeeCollections()