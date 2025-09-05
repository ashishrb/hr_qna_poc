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
        """Get facet data for a specific field"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            # Determine which collection to search based on field
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
        """Determine which collection contains the specified field"""
        field_mapping = {
            'department': 'employee_employment_info',
            'performance_rating': 'employee_performance_info',
            'current_salary': 'employee_compensation_info',
            'attrition_risk_score': 'employee_attrition_info',
            'engagement_score': 'employee_engagement_info',
            'full_name': 'employee_personal_info',
            'employee_id': 'employee_personal_info',
            'role': 'employee_employment_info',
            'location': 'employee_personal_info'
        }
        
        return field_mapping.get(field, 'employee_personal_info')
    
    async def suggest(self, query: str) -> List[str]:
        """Get search suggestions based on partial query"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            suggestions = []
            
            # Search in employee names
            personal_collection = self.collections['personal']
            cursor = self.mongodb_client.client[settings.mongodb_database][personal_collection].find(
                {"full_name": {"$regex": query, "$options": "i"}},
                {"full_name": 1}
            ).limit(5)
            
            async for doc in cursor:
                suggestions.append(doc.get('full_name', ''))
            
            # Search in departments
            employment_collection = self.collections['employment']
            cursor = self.mongodb_client.client[settings.mongodb_database][employment_collection].find(
                {"department": {"$regex": query, "$options": "i"}},
                {"department": 1}
            ).limit(3)
            
            async for doc in cursor:
                dept = doc.get('department', '')
                if dept not in suggestions:
                    suggestions.append(dept)
            
            return suggestions[:10]  # Limit to 10 suggestions
            
        except Exception as e:
            print(f"Suggestions error: {e}")
            return []
    
    async def get_employee_details(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive employee details by joining all collections"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            db = self.mongodb_client.client[settings.mongodb_database]
            
            # Build aggregation pipeline to join all employee data
            pipeline = [
                {"$match": {"employee_id": employee_id}},
                {
                    "$lookup": {
                        "from": self.collections['employment'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {
                    "$lookup": {
                        "from": self.collections['performance'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "performance"
                    }
                },
                {
                    "$lookup": {
                        "from": self.collections['compensation'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "compensation"
                    }
                },
                {
                    "$lookup": {
                        "from": self.collections['attendance'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "attendance"
                    }
                },
                {
                    "$lookup": {
                        "from": self.collections['learning'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "learning"
                    }
                },
                {
                    "$lookup": {
                        "from": self.collections['engagement'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "engagement"
                    }
                },
                {
                    "$lookup": {
                        "from": self.collections['attrition'],
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "attrition"
                    }
                },
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
                        "employment": {
                            "$let": {
                                "vars": {"emp": {"$arrayElemAt": ["$employment", 0]}},
                                "in": {
                                    "$cond": {
                                        "if": {"$ne": ["$$emp", None]},
                                        "then": {
                                            "_id": {"$toString": "$$emp._id"},
                                            "employee_id": "$$emp.employee_id",
                                            "department": "$$emp.department",
                                            "role": "$$emp.role",
                                            "grade_band": "$$emp.grade_band",
                                            "employment_type": "$$emp.employment_type",
                                            "manager_id": "$$emp.manager_id",
                                            "joining_date": {"$dateToString": {"date": "$$emp.joining_date"}},
                                            "work_mode": "$$emp.work_mode",
                                            "created_at": {"$dateToString": {"date": "$$emp.created_at"}},
                                            "updated_at": {"$dateToString": {"date": "$$emp.updated_at"}}
                                        },
                                        "else": None
                                    }
                                }
                            }
                        },
                        "performance": {
                            "$let": {
                                "vars": {"perf": {"$arrayElemAt": ["$performance", 0]}},
                                "in": {
                                    "$cond": {
                                        "if": {"$ne": ["$$perf", None]},
                                        "then": {
                                            "_id": {"$toString": "$$perf._id"},
                                            "employee_id": "$$perf.employee_id",
                                            "performance_rating": "$$perf.performance_rating",
                                            "kpis_met_pct": "$$perf.kpis_met_pct",
                                            "promotions_count": "$$perf.promotions_count",
                                            "awards": "$$perf.awards",
                                            "improvement_areas": "$$perf.improvement_areas",
                                            "last_review_date": {"$dateToString": {"date": "$$perf.last_review_date"}},
                                            "created_at": {"$dateToString": {"date": "$$perf.created_at"}},
                                            "updated_at": {"$dateToString": {"date": "$$perf.updated_at"}}
                                        },
                                        "else": None
                                    }
                                }
                            }
                        },
                        "compensation": {
                            "$let": {
                                "vars": {"comp": {"$arrayElemAt": ["$compensation", 0]}},
                                "in": {
                                    "$cond": {
                                        "if": {"$ne": ["$$comp", None]},
                                        "then": {
                                            "_id": {"$toString": "$$comp._id"},
                                            "employee_id": "$$comp.employee_id",
                                            "current_salary": "$$comp.current_salary",
                                            "bonus_amount": "$$comp.bonus_amount",
                                            "stock_options": "$$comp.stock_options",
                                            "benefits": "$$comp.benefits",
                                            "last_salary_review": {"$dateToString": {"date": "$$comp.last_salary_review"}},
                                            "next_salary_review": {"$dateToString": {"date": "$$comp.next_salary_review"}},
                                            "created_at": {"$dateToString": {"date": "$$comp.created_at"}},
                                            "updated_at": {"$dateToString": {"date": "$$comp.updated_at"}}
                                        },
                                        "else": None
                                    }
                                }
                            }
                        },
                        "attendance": {
                            "$let": {
                                "vars": {"att": {"$arrayElemAt": ["$attendance", 0]}},
                                "in": {
                                    "$cond": {
                                        "if": {"$ne": ["$$att", None]},
                                        "then": {
                                            "_id": {"$toString": "$$att._id"},
                                            "employee_id": "$$att.employee_id",
                                            "attendance_pct": "$$att.attendance_pct",
                                            "days_present": "$$att.days_present",
                                            "days_absent": "$$att.days_absent",
                                            "late_arrivals": "$$att.late_arrivals",
                                            "early_departures": "$$att.early_departures",
                                            "overtime_hours": "$$att.overtime_hours",
                                            "vacation_days_taken": "$$att.vacation_days_taken",
                                            "vacation_days_remaining": "$$att.vacation_days_remaining",
                                            "sick_days_taken": "$$att.sick_days_taken",
                                            "created_at": {"$dateToString": {"date": "$$att.created_at"}},
                                            "updated_at": {"$dateToString": {"date": "$$att.updated_at"}}
                                        },
                                        "else": None
                                    }
                                }
                            }
                        },
                        "learning": {
                            "$let": {
                                "vars": {"learn": {"$arrayElemAt": ["$learning", 0]}},
                                "in": {
                                    "$cond": {
                                        "if": {"$ne": ["$$learn", None]},
                                        "then": {
                                            "_id": {"$toString": "$$learn._id"},
                                            "employee_id": "$$learn.employee_id",
                                            "courses_completed": "$$learn.courses_completed",
                                            "certifications": "$$learn.certifications",
                                            "skills_developed": "$$learn.skills_developed",
                                            "training_hours": "$$learn.training_hours",
                                            "learning_budget_used": "$$learn.learning_budget_used",
                                            "learning_budget_allocated": "$$learn.learning_budget_allocated",
                                            "mentor": "$$learn.mentor",
                                            "mentee": "$$learn.mentee",
                                            "created_at": {"$dateToString": {"date": "$$learn.created_at"}},
                                            "updated_at": {"$dateToString": {"date": "$$learn.updated_at"}}
                                        },
                                        "else": None
                                    }
                                }
                            }
                        },
                        "engagement": {
                            "$let": {
                                "vars": {"eng": {"$arrayElemAt": ["$engagement", 0]}},
                                "in": {
                                    "$cond": {
                                        "if": {"$ne": ["$$eng", None]},
                                        "then": {
                                            "_id": {"$toString": "$$eng._id"},
                                            "employee_id": "$$eng.employee_id",
                                            "engagement_score": "$$eng.engagement_score",
                                            "job_satisfaction": "$$eng.job_satisfaction",
                                            "team_satisfaction": "$$eng.team_satisfaction",
                                            "manager_satisfaction": "$$eng.manager_satisfaction",
                                            "company_satisfaction": "$$eng.company_satisfaction",
                                            "recommendation_score": "$$eng.recommendation_score",
                                            "feedback_given": "$$eng.feedback_given",
                                            "feedback_received": "$$eng.feedback_received",
                                            "participation_events": "$$eng.participation_events",
                                            "created_at": {"$dateToString": {"date": "$$eng.created_at"}},
                                            "updated_at": {"$dateToString": {"date": "$$eng.updated_at"}}
                                        },
                                        "else": None
                                    }
                                }
                            }
                        },
                        "attrition": {
                            "$let": {
                                "vars": {"attr": {"$arrayElemAt": ["$attrition", 0]}},
                                "in": {
                                    "$cond": {
                                        "if": {"$ne": ["$$attr", None]},
                                        "then": {
                                            "_id": {"$toString": "$$attr._id"},
                                            "employee_id": "$$attr.employee_id",
                                            "attrition_risk_score": "$$attr.attrition_risk_score",
                                            "risk_factors": "$$attr.risk_factors",
                                            "retention_probability": "$$attr.retention_probability",
                                            "last_engagement_date": {"$dateToString": {"date": "$$attr.last_engagement_date"}},
                                            "internal_transfer_requests": "$$attr.internal_transfer_requests",
                                            "external_job_applications": "$$attr.external_job_applications",
                                            "exit_interview_score": "$$attr.exit_interview_score",
                                            "created_at": {"$dateToString": {"date": "$$attr.created_at"}},
                                            "updated_at": {"$dateToString": {"date": "$$attr.updated_at"}}
                                        },
                                        "else": None
                                    }
                                }
                            }
                        }
                    }
                }
            ]
            
            collection = db[self.collections['personal']]
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=1)
            
            return result[0] if result else None
            
        except Exception as e:
            print(f"Get employee details error: {e}")
            return None
    
    async def get_employees(self, page: int = 1, limit: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get paginated list of employees with optional filters"""
        try:
            if not self.mongodb_client.client:
                await self.mongodb_client.connect()
            
            db = self.mongodb_client.client[settings.mongodb_database]
            
            # Build aggregation pipeline
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
            
            # Apply filters
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
                        "manager_id": "$employment.manager_id",
                        "joining_date": "$employment.joining_date",
                        "work_mode": "$employment.work_mode",
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