#!/usr/bin/env python3
"""
HR Q&A System - Demo Script
Automated demonstration of key features and capabilities
"""

import asyncio
import requests
import time
import json
from typing import List, Dict, Any

class HRQADemo:
    """Automated demo of HR Q&A System"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.demo_queries = [
            {
                "query": "How many employees work in IT department?",
                "description": "Basic count query",
                "expected_intent": "count_query"
            },
            {
                "query": "Show me developers with AWS certification",
                "description": "Skill-based search",
                "expected_intent": "employee_search"
            },
            {
                "query": "Top 5 performers in the company",
                "description": "Ranking query",
                "expected_intent": "ranking"
            },
            {
                "query": "Compare average performance between IT and Sales",
                "description": "Comparison analytics",
                "expected_intent": "comparison"
            },
            {
                "query": "What's the average salary across all departments?",
                "description": "Analytics query",
                "expected_intent": "analytics"
            },
            {
                "query": "Who has the highest leave balance?",
                "description": "Specific ranking",
                "expected_intent": "ranking"
            },
            {
                "query": "Find employees who joined in the last 6 months",
                "description": "Time-based filter",
                "expected_intent": "trend_analysis"
            },
            {
                "query": "Show me remote employees with high performance ratings",
                "description": "Complex multi-criteria search",
                "expected_intent": "complex_filter"
            }
        ]
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "="*60)
        print(f"🎯 {title}")
        print("="*60)
    
    def print_step(self, step: int, description: str):
        """Print formatted step"""
        print(f"\n📋 Step {step}: {description}")
        print("-" * 40)
    
    def test_api_health(self) -> bool:
        """Test API health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Status: {data['status']}")
                print(f"✅ Version: {data['version']}")
                return True
            else:
                print(f"❌ API Health Check Failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Connection Failed: {e}")
            return False
    
    def test_analytics_endpoints(self) -> bool:
        """Test analytics endpoints"""
        try:
            # Test overview analytics
            response = requests.get(f"{self.base_url}/analytics/overview", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Total Employees: {data.get('total_employees', 0)}")
                print(f"✅ Total Departments: {data.get('total_departments', 0)}")
                print(f"✅ Total Roles: {data.get('total_roles', 0)}")
            else:
                print(f"❌ Overview Analytics Failed: {response.status_code}")
                return False
            
            # Test department analytics
            response = requests.get(f"{self.base_url}/analytics/departments", timeout=10)
            if response.status_code == 200:
                data = response.json()
                departments = data.get('departments', [])
                print(f"✅ Department Analytics: {len(departments)} departments")
                for dept in departments[:3]:  # Show first 3
                    print(f"   - {dept['department']}: {dept['count']} employees")
            else:
                print(f"❌ Department Analytics Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Analytics Test Failed: {e}")
            return False
    
    def run_query_demo(self, query_info: Dict[str, Any], step: int) -> bool:
        """Run a single query demo"""
        query = query_info["query"]
        description = query_info["description"]
        expected_intent = query_info["expected_intent"]
        
        print(f"🔍 Query: \"{query}\"")
        print(f"📝 Description: {description}")
        print(f"🎯 Expected Intent: {expected_intent}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/query",
                json={"query": query, "top_k": 10},
                timeout=30
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Status: {data['status']}")
                print(f"✅ Intent: {data['intent']}")
                print(f"✅ Results Found: {data['count']}")
                print(f"✅ Response Time: {response_time:.1f}ms")
                
                # Show response preview
                response_text = data.get('response', '')
                if response_text:
                    preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
                    print(f"💬 Response: {preview}")
                
                # Show sample results if available
                results = data.get('results', [])
                if results:
                    print(f"📊 Sample Results:")
                    for i, result in enumerate(results[:3], 1):
                        if isinstance(result, dict):
                            name = result.get('full_name', 'Unknown')
                            dept = result.get('department', 'N/A')
                            role = result.get('role', 'N/A')
                            print(f"   {i}. {name} - {dept} ({role})")
                
                # Check if intent matches expectation
                if data['intent'] == expected_intent:
                    print(f"✅ Intent Detection: CORRECT")
                else:
                    print(f"⚠️ Intent Detection: Expected {expected_intent}, got {data['intent']}")
                
                return True
                
            else:
                print(f"❌ Query Failed: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Query Error: {e}")
            return False
    
    def run_comprehensive_demo(self):
        """Run comprehensive demo"""
        self.print_header("HR Q&A System - Comprehensive Demo")
        
        print("🎬 This demo will showcase the key features of the HR Q&A System:")
        print("   • Natural language query processing")
        print("   • Intent detection and analysis")
        print("   • Complex analytics and comparisons")
        print("   • Real-time response generation")
        print("   • Professional web interface")
        
        # Step 1: API Health Check
        self.print_step(1, "API Health Check")
        if not self.test_api_health():
            print("❌ Demo cannot continue - API is not accessible")
            print("💡 Make sure to start the server: python src/api/main.py")
            return False
        
        # Step 2: Analytics Overview
        self.print_step(2, "Analytics Overview")
        if not self.test_analytics_endpoints():
            print("⚠️ Analytics endpoints have issues, but continuing with demo")
        
        # Step 3: Query Demonstrations
        self.print_step(3, "Natural Language Query Demonstrations")
        
        successful_queries = 0
        total_queries = len(self.demo_queries)
        
        for i, query_info in enumerate(self.demo_queries, 1):
            print(f"\n🔍 Demo Query {i}/{total_queries}")
            if self.run_query_demo(query_info, i):
                successful_queries += 1
            
            # Small delay between queries
            if i < total_queries:
                time.sleep(1)
        
        # Step 4: Demo Summary
        self.print_step(4, "Demo Summary")
        
        print(f"📊 Demo Results:")
        print(f"   • Total Queries Tested: {total_queries}")
        print(f"   • Successful Queries: {successful_queries}")
        print(f"   • Success Rate: {(successful_queries/total_queries)*100:.1f}%")
        
        if successful_queries == total_queries:
            print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
            print("✅ All queries processed correctly")
            print("✅ System is fully operational")
        elif successful_queries >= total_queries * 0.8:
            print("\n✅ DEMO MOSTLY SUCCESSFUL!")
            print("⚠️ Some queries had issues, but system is functional")
        else:
            print("\n❌ DEMO HAD SIGNIFICANT ISSUES")
            print("🔧 Check system configuration and try again")
        
        # Step 5: Next Steps
        self.print_step(5, "Next Steps")
        print("🌐 Web Interface: http://localhost:8000")
        print("📚 Documentation: OLLAMA_SETUP_GUIDE.md")
        print("🧪 System Test: python test_system.py")
        print("🔧 Troubleshooting: Check logs and configuration")
        
        return successful_queries >= total_queries * 0.8
    
    def run_quick_demo(self):
        """Run a quick demo with essential queries"""
        self.print_header("HR Q&A System - Quick Demo")
        
        print("⚡ Quick demo with essential queries...")
        
        # Test API
        if not self.test_api_health():
            return False
        
        # Run 3 key queries
        key_queries = [
            self.demo_queries[0],  # Count query
            self.demo_queries[2],  # Ranking query
            self.demo_queries[3],  # Comparison query
        ]
        
        successful = 0
        for i, query_info in enumerate(key_queries, 1):
            print(f"\n🔍 Quick Demo {i}/3")
            if self.run_query_demo(query_info, i):
                successful += 1
        
        print(f"\n📊 Quick Demo Results: {successful}/3 successful")
        
        if successful == 3:
            print("✅ Quick demo successful - system is working!")
        else:
            print("⚠️ Quick demo had issues - check system configuration")
        
        return successful == 3

def main():
    """Main demo function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="HR Q&A System Demo")
    parser.add_argument("--quick", action="store_true", help="Run quick demo only")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    
    args = parser.parse_args()
    
    demo = HRQADemo(args.url)
    
    if args.quick:
        success = demo.run_quick_demo()
    else:
        success = demo.run_comprehensive_demo()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
