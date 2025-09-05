# src/query/ollama_query_engine.py
"""
Ollama-based HR Query Engine - Replaces Azure OpenAI dependencies
Uses local Ollama models for natural language processing
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.ai.ollama_client import ollama_client
from src.database.mongodb_client import mongodb_client
from src.core.models import QueryType

class OllamaHRQueryEngine:
    """HR Query Engine using Ollama for AI processing"""
    
    def __init__(self):
        """Initialize the Ollama-based query engine"""
        print("🚀 Initializing Ollama-based HR Query Engine...")
        
        self.ai_client = ollama_client
        self.departments = ["Sales", "IT", "Operations", "HR", "Finance", "Legal", "Engineering", "Marketing", "Support"]
        self.roles = ["Developer", "Manager", "Analyst", "Director", "Lead", "Engineer", "Consultant", "Specialist"]
        self.skills = ["PMP", "GCP", "AWS", "Azure", "Python", "Java", "JavaScript", "SQL", "Docker", "Kubernetes"]
        self.locations = ["Remote", "Onshore", "Offshore", "New York", "California", "India", "Chennai", "Hyderabad"]
        
        print("✅ Ollama-based HR Query Engine ready!")
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Main query processing pipeline using Ollama
        
        Args:
            query: Natural language query
            
        Returns:
            Complete query result with detailed analysis
        """
        start_time = time.time()
        
        try:
            print(f"\n🔍 Processing query with Ollama: '{query}'")
            
            # Step 1: Analyze query using Ollama
            analysis = self.ai_client.analyze_query_intent(query)
            print(f"   🎯 Intent: {analysis['intent']}")
            print(f"   📋 Fields: {analysis.get('fields_to_analyze', [])}")
            print(f"   🔧 Filters: {analysis.get('filters', {})}")
            
            # Step 2: Route to appropriate handler
            intent = analysis['intent']
            if intent == "comparison":
                results, count = await self._handle_comparison_query(analysis)
            elif intent == "ranking":
                results, count = await self._handle_ranking_query(analysis)
            elif intent == "count_query":
                results, count = await self._handle_count_query(analysis)
            elif intent == "analytics":
                results, count = await self._handle_analytics_query(analysis)
            else:
                results, count = await self._handle_search_query(analysis)
            
            # Step 3: Generate response using Ollama
            response = self.ai_client.generate_response(query, results, count, intent)
            
            execution_time = (time.time() - start_time) * 1000
            
            print(f"   ✅ Found {count} results in {execution_time:.1f}ms")
            
            return {
                "query": query,
                "intent": intent,
                "entities": analysis.get("entities", {}),
                "fields_analyzed": analysis.get("fields_to_analyze", []),
                "results": results,
                "count": count,
                "response": response,
                "execution_time_ms": execution_time,
                "status": "success"
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Query processing failed: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            return {
                "query": query,
                "intent": "unknown",
                "entities": {},
                "fields_analyzed": [],
                "results": [],
                "count": 0,
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "execution_time_ms": execution_time,
                "status": "error",
                "error": error_msg
            }
    
    async def _handle_count_query(self, analysis: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle count queries with MongoDB"""
        try:
            await mongodb_client.connect()
            
            # Build aggregation pipeline
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Apply filters from analysis
            match_conditions = {}
            entities = analysis.get("entities", {})
            
            if entities.get("departments"):
                departments = entities["departments"]
                if len(departments) == 1:
                    match_conditions["employment.department"] = departments[0]
                else:
                    match_conditions["employment.department"] = {"$in": departments}
            
            if entities.get("roles"):
                roles = entities["roles"]
                if len(roles) == 1:
                    match_conditions["employment.role"] = roles[0]
                else:
                    match_conditions["employment.role"] = {"$in": roles}
            
            if match_conditions:
                pipeline.append({"$match": match_conditions})
                print(f"   🎯 Applied filters: {match_conditions}")
            
            # Add count stage
            pipeline.append({"$count": "total"})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            count = results[0]["total"] if results else 0
            
            return [], count
            
        except Exception as e:
            print(f"   ❌ Count query failed: {e}")
            return [], 0
    
    async def _handle_comparison_query(self, analysis: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle comparison queries"""
        try:
            await mongodb_client.connect()
            
            # Build comprehensive pipeline
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Add performance data if needed
            if "performance_rating" in analysis.get("fields_to_analyze", []):
                pipeline.extend([
                    {
                        "$lookup": {
                            "from": "performance",
                            "localField": "employee_id",
                            "foreignField": "employee_id",
                            "as": "performance"
                        }
                    },
                    {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}}
                ])
            
            # Group by department and calculate statistics
            group_stage = {
                "_id": "$employment.department",
                "count": {"$sum": 1}
            }
            
            # Add performance statistics if available
            if "performance_rating" in analysis.get("fields_to_analyze", []):
                group_stage.update({
                    "avg_rating": {"$avg": {"$toInt": "$performance.performance_rating"}},
                    "max_rating": {"$max": {"$toInt": "$performance.performance_rating"}},
                    "min_rating": {"$min": {"$toInt": "$performance.performance_rating"}}
                })
            
            pipeline.append({"$group": group_stage})
            pipeline.append({"$sort": {"_id": 1}})
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Comparison query failed: {e}")
            return [], 0
    
    async def _handle_ranking_query(self, analysis: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle ranking queries"""
        try:
            await mongodb_client.connect()
            
            # Build pipeline for ranking
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Add performance data for ranking
            pipeline.extend([
                {
                    "$lookup": {
                        "from": "performance",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "performance"
                    }
                },
                {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}}
            ])
            
            # Add computed fields
            pipeline.append({
                "$addFields": {
                    "performance_rating_num": {
                        "$toInt": {"$ifNull": [{"$toInt": "$performance.performance_rating"}, 0]}
                    }
                }
            })
            
            # Sort by performance rating (descending for top performers)
            pipeline.append({"$sort": {"performance_rating_num": -1}})
            
            # Limit results
            limit = analysis.get("limit", 10)
            pipeline.append({"$limit": limit})
            
            # Project useful fields
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "performance_rating": "$performance_rating_num"
                }
            })
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Ranking query failed: {e}")
            return [], 0
    
    async def _handle_analytics_query(self, analysis: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle analytics queries"""
        try:
            await mongodb_client.connect()
            
            # Build comprehensive analytics pipeline
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Add performance data
            pipeline.extend([
                {
                    "$lookup": {
                        "from": "performance",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "performance"
                    }
                },
                {"$unwind": {"path": "$performance", "preserveNullAndEmptyArrays": True}}
            ])
            
            # Add computed fields
            pipeline.append({
                "$addFields": {
                    "performance_rating_num": {
                        "$toInt": {"$ifNull": [{"$toInt": "$performance.performance_rating"}, 0]}
                    }
                }
            })
            
            # Group and calculate statistics
            pipeline.append({
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "avg_performance": {"$avg": "$performance_rating_num"},
                    "max_performance": {"$max": "$performance_rating_num"},
                    "min_performance": {"$min": "$performance_rating_num"}
                }
            })
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            if results:
                count = results[0].get("count", 0)
                return results, count
            else:
                return [], 0
                
        except Exception as e:
            print(f"   ❌ Analytics query failed: {e}")
            return [], 0
    
    async def _handle_search_query(self, analysis: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Handle general search queries"""
        try:
            await mongodb_client.connect()
            
            # Simple search using MongoDB text search
            pipeline = [
                {
                    "$lookup": {
                        "from": "employment",
                        "localField": "employee_id",
                        "foreignField": "employee_id",
                        "as": "employment"
                    }
                },
                {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}}
            ]
            
            # Apply basic filters
            match_conditions = {}
            entities = analysis.get("entities", {})
            
            if entities.get("departments"):
                departments = entities["departments"]
                match_conditions["employment.department"] = {"$in": departments}
            
            if entities.get("roles"):
                roles = entities["roles"]
                match_conditions["employment.role"] = {"$in": roles}
            
            if match_conditions:
                pipeline.append({"$match": match_conditions})
            
            # Limit results
            limit = analysis.get("limit", 10)
            pipeline.append({"$limit": limit})
            
            # Project useful fields
            pipeline.append({
                "$project": {
                    "employee_id": 1,
                    "full_name": 1,
                    "department": "$employment.department",
                    "role": "$employment.role",
                    "location": 1
                }
            })
            
            collection = await mongodb_client.get_collection("personal_info")
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            return results, len(results)
            
        except Exception as e:
            print(f"   ❌ Search query failed: {e}")
            return [], 0

# Global instance
ollama_query_engine = OllamaHRQueryEngine()

async def test_ollama_query_engine():
    """Test the Ollama query engine"""
    print("\n🧪 Testing Ollama Query Engine")
    print("=" * 50)
    
    test_queries = [
        "How many employees work in IT?",
        "Show me top 5 performers",
        "Compare average performance between IT and Sales",
        "Who has the highest performance rating?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Testing: '{query}'")
        result = await ollama_query_engine.process_query(query)
        
        print(f"   🎯 Intent: {result['intent']}")
        print(f"   📊 Count: {result['count']}")
        print(f"   ⏱️ Time: {result['execution_time_ms']:.1f}ms")
        print(f"   💬 Response: {result['response'][:100]}...")
        
        if result['results']:
            print(f"   👥 Sample results:")
            for emp in result['results'][:2]:
                name = emp.get('full_name', 'N/A')
                dept = emp.get('department', 'N/A')
                print(f"       - {name} ({dept})")
        
        print("-" * 40)
    
    print(f"\n🎉 Ollama query engine testing completed!")

if __name__ == "__main__":
    asyncio.run(test_ollama_query_engine())
