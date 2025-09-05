#!/usr/bin/env python3
"""
Local Search Client for HR Employee 360 View
Provides MongoDB-based search functionality without Azure dependencies
"""

import asyncio
from typing import List, Dict, Any, Optional
from src.database.mongodb_client import MongoDBClient
from src.core.config import settings

class LocalSearchClient:
    """Local search client using MongoDB for HR data"""
    
    def __init__(self):
        self.mongodb_client = MongoDBClient()
        self.collections = {
            'personal': 'employee_personal_info',
            'employment': 'employee_employment_info',
            'performance': 'employee_performance_info',
            'compensation': 'employee_compensation_info',
            'engagement': 'employee_engagement_info',
            'learning': 'employee_learning_info',
            'experience': 'employee_experience_info',
            'attendance': 'employee_attendance_info',
            'attrition': 'employee_attrition_info'
        }
    
    async def search(self, query: str, filters: Dict[str, Any] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for employees based on query and filters"""
        try:
            # Connect to MongoDB if not already connected
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            # Build search criteria
            search_criteria = {}
            if filters:
                search_criteria.update(filters)
            
            # Search in personal info collection (main employee data)
            personal_collection = self.collections['personal']
            employees = []
            
            # Get employee documents
            cursor = self.mongodb_client.client[settings.mongodb_database][personal_collection].find(search_criteria).limit(top_k)
            
            async for doc in cursor:
                # Get additional data from other collections
                employee_id = doc.get('employee_id')
                if employee_id:
                    # Combine data from all collections
                    employee_data = await self._get_complete_employee_data(employee_id)
                    employees.append(employee_data)
            
            return employees
            
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    async def _get_complete_employee_data(self, employee_id: str) -> Dict[str, Any]:
        """Get complete employee data from all collections"""
        try:
            employee_data = {}
            
            # Get data from each collection
            for collection_type, collection_name in self.collections.items():
                doc = await self.mongodb_client.find_document(
                    collection_name, 
                    {"employee_id": employee_id}
                )
                if doc:
                    # Remove MongoDB _id field
                    doc.pop('_id', None)
                    employee_data.update(doc)
            
            return employee_data
            
        except Exception as e:
            print(f"Error getting complete employee data: {e}")
            return {"employee_id": employee_id}
    
    async def get_document_count(self, filters: Dict[str, Any] = None) -> int:
        """Get count of documents matching filters"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            search_criteria = {}
            if filters:
                search_criteria.update(filters)
            
            personal_collection = self.collections['personal']
            count = await self.mongodb_client.count_documents(personal_collection, search_criteria)
            
            return count
            
        except Exception as e:
            print(f"Count error: {e}")
            return 0
    
    async def get_facets(self, field: str) -> List[Dict[str, Any]]:
        """Get facet values for a given field"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            collection_name = self._get_collection_for_field(field)
            if not collection_name:
                return []
            
            # Use MongoDB aggregation to get facets
            pipeline = [
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}
            ]
            
            facets = []
            collection = self.mongodb_client.client[settings.mongodb_database][collection_name]
            cursor = collection.aggregate(pipeline)
            
            async for doc in cursor:
                facets.append({
                    "value": doc["_id"],
                    "count": doc["count"]
                })
            
            return facets
            
        except Exception as e:
            print(f"Facets error: {e}")
            return []
    
    def _get_collection_for_field(self, field: str) -> Optional[str]:
        """Get collection name for a given field"""
        field_mapping = {
            'department': 'employment',
            'role': 'employment',
            'location': 'personal',
            'gender': 'personal',
            'employment_type': 'employment',
            'grade_band': 'employment'
        }
        
        collection_type = field_mapping.get(field)
        return self.collections.get(collection_type) if collection_type else None
    
    async def get_search_suggestions(self, query: str) -> List[str]:
        """Get search suggestions based on query"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            suggestions = []
            
            # Get suggestions from employee names
            personal_collection = self.collections['personal']
            cursor = self.mongodb_client.client[settings.mongodb_database][personal_collection].find(
                {"full_name": {"$regex": query, "$options": "i"}},
                {"full_name": 1}
            ).limit(5)
            
            async for doc in cursor:
                suggestions.append(doc.get("full_name", ""))
            
            return suggestions
            
        except Exception as e:
            print(f"Suggestions error: {e}")
            return []
    
    async def get_employee_details(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive employee details by joining all collections"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            # Use the existing _get_complete_employee_data method which is simpler and more reliable
            employee_data = await self._get_complete_employee_data(employee_id)
            
            # Convert ObjectId fields to strings for JSON serialization
            if employee_data:
                # Remove MongoDB _id fields that might cause serialization issues
                employee_data.pop('_id', None)
                
                # Convert any remaining ObjectId fields to strings
                for key, value in employee_data.items():
                    if hasattr(value, '__class__') and value.__class__.__name__ == 'ObjectId':
                        employee_data[key] = str(value)
            
            return employee_data
            
        except Exception as e:
            print(f"Get employee details error: {e}")
            return None
    
    async def get_employees(self, page: int = 1, limit: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get paginated list of employees with optional filters"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            db = self.mongodb_client.client[settings.mongodb_database]
            
            # Simplified aggregation pipeline
            pipeline = [
                {
                    "$lookup": {
                        "from": self.collections['employment'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": self.collections['performance'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "performance"
                    }
                },
                {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": self.collections['compensation'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "compensation"
                    }
                },
                {"$unwind": {"path": "$compensation", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": self.collections['attendance'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "attendance"
                    }
                },
                {"$unwind": {"path": "$attendance", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": self.collections['learning'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "learning"
                    }
                },
                {"$unwind": {"path": "$learning", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": self.collections['engagement'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "engagement"
                    }
                },
                {"$unwind": {"path": "$engagement", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": self.collections['attrition'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "attrition"
                    }
                },
                {"$unwind": {"path": "$attrition", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Add filters if provided
            if filters:
                match_conditions = {}
                if filters.get("department"):
                    match_conditions["employment.department"] = filters["department"]
                if filters.get("role"):
                    match_conditions["employment.role"] = filters["role"]
                
                if match_conditions:
                    pipeline.append({"$match": match_conditions})
            
            # Add pagination
            skip = (page - 1) * limit
            pipeline.extend([
                {"$skip": skip},
                {"$limit": limit},
                {
                    "$project": {
                        "_id": {"$toString": "$_id"},
                        "employee_id": 1,
                        "full_name": 1,
                        "email": 1,
                        "age": 1,
                        "gender": 1,
                        "location": 1,
                        "contact_number": 1,
                        "department": "$employment.department",
                        "role": "$employment.role",
                        "grade_band": "$employment.grade_band",
                        "employment_type": "$employment.employment_type",
                        "work_mode": "$employment.work_mode",
                        "joining_date": "$employment.joining_date",
                        "performance_rating": "$performance.performance_rating",
                        "kpis_met_pct": "$performance.kpis_met_pct",
                        "awards": "$performance.awards",
                        "current_salary": "$compensation.current_salary",
                        "bonus_amount": "$compensation.bonus_amount",
                        "attendance_pct": "$attendance.attendance_pct",
                        "courses_completed": "$learning.courses_completed",
                        "certifications": "$learning.certifications",
                        "engagement_score": "$engagement.engagement_score",
                        "attrition_risk_score": "$attrition.attrition_risk_score"
                    }
                }
            ])
            
            collection = db[self.collections['personal']]
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results
            
        except Exception as e:
            print(f"Get employees error: {e}")
            return []
    
    async def get_department_analytics(self) -> Dict[str, Any]:
        """Get department analytics"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            db = self.mongodb_client.client[settings.mongodb_database]
            
            pipeline = [
                {
                    "$lookup": {
                        "from": self.collections['employment'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": "$employment.department",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            collection = db[self.collections['personal']]
            cursor = collection.aggregate(pipeline)
            departments = await cursor.to_list(length=None)
            
            return {
                "departments": departments,
                "total_departments": len(departments)
            }
            
        except Exception as e:
            print(f"Department analytics error: {e}")
            return {"departments": [], "total_departments": 0}
    
    async def get_performance_analytics(self) -> Dict[str, Any]:
        """Get performance analytics"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            db = self.mongodb_client.client[settings.mongodb_database]
            
            pipeline = [
                {
                    "$lookup": {
                        "from": self.collections['performance'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "performance"
                    }
                },
                {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": None,
                        "total_employees": {"$sum": 1},
                        "avg_performance": {"$avg": "$performance.performance_rating"},
                        "min_performance": {"$min": "$performance.performance_rating"},
                        "max_performance": {"$max": "$performance.performance_rating"},
                        "high_performers": {
                            "$sum": {
                                "$cond": [
                                    {"$gte": ["$performance.performance_rating", 4.0]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "low_performers": {
                            "$sum": {
                                "$cond": [
                                    {"$lt": ["$performance.performance_rating", 3.0]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]
            
            collection = db[self.collections['personal']]
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                data = result[0]
                total = data.get("total_employees", 0)
                return {
                    "total_employees": total,
                    "avg_performance": round(data.get("avg_performance", 0), 2),
                    "min_performance": data.get("min_performance", 0),
                    "max_performance": data.get("max_performance", 0),
                    "high_performers": data.get("high_performers", 0),
                    "low_performers": data.get("low_performers", 0),
                    "high_performer_pct": round((data.get("high_performers", 0) / total * 100) if total > 0 else 0, 1),
                    "low_performer_pct": round((data.get("low_performers", 0) / total * 100) if total > 0 else 0, 1)
                }
            
            return {
                "total_employees": 0,
                "avg_performance": 0,
                "min_performance": 0,
                "max_performance": 0,
                "high_performers": 0,
                "low_performers": 0,
                "high_performer_pct": 0,
                "low_performer_pct": 0
            }
            
        except Exception as e:
            print(f"Performance analytics error: {e}")
            return {
                "total_employees": 0,
                "avg_performance": 0,
                "min_performance": 0,
                "max_performance": 0,
                "high_performers": 0,
                "low_performers": 0,
                "high_performer_pct": 0,
                "low_performer_pct": 0
            }
    
    async def get_salary_analytics(self) -> Dict[str, Any]:
        """Get salary analytics"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            db = self.mongodb_client.client[settings.mongodb_database]
            
            pipeline = [
                {
                    "$lookup": {
                        "from": self.collections['compensation'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "compensation"
                    }
                },
                {"$unwind": {"path": "$compensation", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": self.collections['employment'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": None,
                        "total_employees": {"$sum": 1},
                        "avg_salary": {"$avg": "$compensation.current_salary"},
                        "min_salary": {"$min": "$compensation.current_salary"},
                        "max_salary": {"$max": "$compensation.current_salary"},
                        "department_analytics": {
                            "$push": {
                                "department": "$employment.department",
                                "salary": "$compensation.current_salary"
                            }
                        }
                    }
                }
            ]
            
            collection = db[self.collections['personal']]
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                data = result[0]
                avg_salary = data.get("avg_salary", 0)
                min_salary = data.get("min_salary", 0)
                max_salary = data.get("max_salary", 0)
                
                # Process department analytics
                dept_data = {}
                for item in data.get("department_analytics", []):
                    dept = item.get("department")
                    salary = item.get("salary", 0)
                    if dept:
                        if dept not in dept_data:
                            dept_data[dept] = {"salaries": [], "count": 0}
                        dept_data[dept]["salaries"].append(salary)
                        dept_data[dept]["count"] += 1
                
                department_analytics = []
                for dept, info in dept_data.items():
                    salaries = info["salaries"]
                    department_analytics.append({
                        "department": dept,
                        "employee_count": info["count"],
                        "avg_salary": round(sum(salaries) / len(salaries), 2),
                        "min_salary": min(salaries),
                        "max_salary": max(salaries)
                    })
                
                return {
                    "total_employees": data.get("total_employees", 0),
                    "avg_salary": round(avg_salary, 2),
                    "min_salary": min_salary,
                    "max_salary": max_salary,
                    "salary_range": max_salary - min_salary,
                    "department_analytics": department_analytics
                }
            
            return {
                "total_employees": 0,
                "avg_salary": 0,
                "min_salary": 0,
                "max_salary": 0,
                "salary_range": 0,
                "department_analytics": []
            }
            
        except Exception as e:
            print(f"Salary analytics error: {e}")
            return {
                "total_employees": 0,
                "avg_salary": 0,
                "min_salary": 0,
                "max_salary": 0,
                "salary_range": 0,
                "department_analytics": []
            }
    
    async def get_attrition_analytics(self) -> Dict[str, Any]:
        """Get attrition analytics"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            db = self.mongodb_client.client[settings.mongodb_database]
            
            pipeline = [
                {
                    "$lookup": {
                        "from": self.collections['attrition'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "attrition"
                    }
                },
                {"$unwind": {"path": "$attrition", "preserveNullAndEmptyArrays": True}},
                {
                    "$group": {
                        "_id": None,
                        "total_employees": {"$sum": 1},
                        "avg_risk_score": {"$avg": "$attrition.attrition_risk_score"},
                        "high_risk": {
                            "$sum": {
                                "$cond": [
                                    {"$gte": ["$attrition.attrition_risk_score", 7.0]},
                                    1,
                                    0
                                ]
                            }
                        },
                        "medium_risk": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$and": [
                                            {"$gte": ["$attrition.attrition_risk_score", 4.0]},
                                            {"$lt": ["$attrition.attrition_risk_score", 7.0]}
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        },
                        "low_risk": {
                            "$sum": {
                                "$cond": [
                                    {"$lt": ["$attrition.attrition_risk_score", 4.0]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]
            
            collection = db[self.collections['personal']]
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            if result:
                data = result[0]
                total = data.get("total_employees", 0)
                return {
                    "total_employees": total,
                    "avg_risk_score": round(data.get("avg_risk_score", 0), 2),
                    "high_risk": data.get("high_risk", 0),
                    "medium_risk": data.get("medium_risk", 0),
                    "low_risk": data.get("low_risk", 0),
                    "high_risk_pct": round((data.get("high_risk", 0) / total * 100) if total > 0 else 0, 1),
                    "medium_risk_pct": round((data.get("medium_risk", 0) / total * 100) if total > 0 else 0, 1),
                    "low_risk_pct": round((data.get("low_risk", 0) / total * 100) if total > 0 else 0, 1)
                }
            
            return {
                "total_employees": 0,
                "avg_risk_score": 0,
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0,
                "high_risk_pct": 0,
                "medium_risk_pct": 0,
                "low_risk_pct": 0
            }
            
        except Exception as e:
            print(f"Attrition analytics error: {e}")
            return {
                "total_employees": 0,
                "avg_risk_score": 0,
                "high_risk": 0,
                "medium_risk": 0,
                "low_risk": 0,
                "high_risk_pct": 0,
                "medium_risk_pct": 0,
                "low_risk_pct": 0
            }
