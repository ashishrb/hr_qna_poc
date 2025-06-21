# scripts/performance_test.py
"""
Performance Testing Script for HR Q&A System

Purpose:
- Benchmark query response times and system performance
- Test search accuracy and relevance scoring
- Load testing for concurrent users and high-volume queries
- Memory and resource usage monitoring
- API endpoint performance testing
- Database and search service latency testing

Usage:
    python scripts/performance_test.py --test query_speed --iterations 100
    python scripts/performance_test.py --test load_test --concurrent 10 --duration 60
    python scripts/performance_test.py --test search_accuracy --queries test_queries.json
    python scripts/performance_test.py --test full_suite
    python scripts/performance_test.py --test api_endpoints --host localhost:8000
"""

import asyncio
import aiohttp
import time
import statistics
import json
import argparse
import psutil
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.query.updated_query_engine import UpdatedHRQueryEngine
from src.search.azure_search_client import azure_search_client
from src.database.mongodb_client import mongodb_client

class PerformanceTestSuite:
    """Comprehensive performance testing for HR Q&A system"""
    
    def __init__(self):
        self.query_engine = None
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_info": self._get_system_info(),
            "tests": {}
        }
        
        # Test queries for different scenarios
        self.test_queries = {
            "simple": [
                "Who are the developers?",
                "Find employees in IT department",
                "Show me managers",
                "List employees in Operations"
            ],
            "complex": [
                "Find developers with Python certification in IT department",
                "Show me employees with PMP certification and 5+ years experience",
                "Who are the high-performing employees in Sales with AWS skills?",
                "Find remote employees with GCP certification working on Cloud projects"
            ],
            "count": [
                "How many employees work in IT?",
                "Count of developers in the company",
                "Total employees with AWS certification",
                "Number of employees in each department"
            ],
            "skill_based": [
                "Find employees with Python skills",
                "Who has AWS certification?",
                "Show me employees with machine learning experience",
                "Find people with SQL and database skills"
            ],
            "edge_cases": [
                "",  # Empty query
                "a",  # Single character
                "xyz123",  # Non-existent term
                "find me all the super senior principal architect developers with 20+ years experience in quantum computing and blockchain",  # Very long query
                "employees employees employees",  # Repeated words
                "Who is the CEO of Microsoft?",  # Out-of-scope query
            ]
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "cpu_percent": psutil.cpu_percent(),
            "python_version": sys.version,
            "platform": sys.platform
        }
    
    async def setup_test_environment(self):
        """Initialize test environment"""
        print("🔧 Setting up test environment...")
        
        try:
            # Initialize query engine
            self.query_engine = UpdatedHRQueryEngine()
            
            # Test database connection
            await mongodb_client.connect()
            
            # Test search service
            count = azure_search_client.get_document_count()
            print(f"   📊 Search index documents: {count}")
            
            # Warm up the system with a few test queries
            print("🔥 Warming up system...")
            for _ in range(3):
                await self.query_engine.process_query("find developers")
            
            print("✅ Test environment ready")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup test environment: {e}")
            return False
    
    async def test_query_speed(self, iterations: int = 100) -> Dict[str, Any]:
        """Test query processing speed and response times"""
        print(f"⚡ Testing query speed ({iterations} iterations)...")
        
        results = {
            "iterations": iterations,
            "query_types": {},
            "overall_stats": {}
        }
        
        all_times = []
        
        for query_type, queries in self.test_queries.items():
            if query_type == "edge_cases":
                continue  # Skip edge cases for speed test
            
            print(f"   📊 Testing {query_type} queries...")
            
            type_times = []
            
            for i in range(iterations // len(self.test_queries)):
                for query in queries:
                    start_time = time.time()
                    
                    try:
                        result = await self.query_engine.process_query(query)
                        end_time = time.time()
                        
                        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                        type_times.append(response_time)
                        all_times.append(response_time)
                        
                        # Log slow queries
                        if response_time > 5000:  # 5 seconds
                            print(f"      ⚠️ Slow query ({response_time:.0f}ms): {query[:50]}...")
                    
                    except Exception as e:
                        print(f"      ❌ Query failed: {query[:50]}... - {e}")
            
            # Calculate statistics for this query type
            if type_times:
                results["query_types"][query_type] = {
                    "count": len(type_times),
                    "min_ms": min(type_times),
                    "max_ms": max(type_times),
                    "avg_ms": statistics.mean(type_times),
                    "median_ms": statistics.median(type_times),
                    "std_dev": statistics.stdev(type_times) if len(type_times) > 1 else 0
                }
        
        # Calculate overall statistics
        if all_times:
            results["overall_stats"] = {
                "total_queries": len(all_times),
                "min_ms": min(all_times),
                "max_ms": max(all_times),
                "avg_ms": statistics.mean(all_times),
                "median_ms": statistics.median(all_times),
                "p95_ms": sorted(all_times)[int(len(all_times) * 0.95)],
                "p99_ms": sorted(all_times)[int(len(all_times) * 0.99)],
                "queries_per_second": len(all_times) / (sum(all_times) / 1000)
            }
        
        self.test_results["tests"]["query_speed"] = results
        return results
    
    async def test_search_accuracy(self, test_queries_file: str = None) -> Dict[str, Any]:
        """Test search accuracy and relevance"""
        print("🎯 Testing search accuracy...")
        
        results = {
            "test_queries": {},
            "accuracy_metrics": {}
        }
        
        # Use predefined test queries with expected results
        expected_results = {
            "find developers": {"should_contain": ["developer", "development", "software"]},
            "employees with AWS certification": {"should_contain": ["aws"], "min_results": 1},
            "IT department employees": {"should_contain": ["IT"], "department_filter": "IT"},
            "employees in Operations": {"should_contain": ["operations"], "department_filter": "Operations"},
            "Python developers": {"should_contain": ["python", "developer"], "min_results": 1}
        }
        
        accuracy_scores = []
        
        for query, expectations in expected_results.items():
            print(f"   🔍 Testing: {query}")
            
            try:
                result = await self.query_engine.process_query(query)
                
                search_results = result.get("search_results", [])
                response_text = result.get("response", "").lower()
                
                # Calculate accuracy score
                score = 0
                feedback = []
                
                # Check if minimum results are returned
                if "min_results" in expectations:
                    if len(search_results) >= expectations["min_results"]:
                        score += 20
                        feedback.append("✅ Minimum results found")
                    else:
                        feedback.append(f"❌ Expected {expectations['min_results']} results, got {len(search_results)}")
                
                # Check if expected terms are in response
                if "should_contain" in expectations:
                    found_terms = 0
                    for term in expectations["should_contain"]:
                        if term.lower() in response_text:
                            found_terms += 1
                    
                    term_score = (found_terms / len(expectations["should_contain"])) * 40
                    score += term_score
                    feedback.append(f"📝 Found {found_terms}/{len(expectations['should_contain'])} expected terms")
                
                # Check department filtering
                if "department_filter" in expectations:
                    correct_dept = 0
                    for emp in search_results:
                        if emp.get("department", "").lower() == expectations["department_filter"].lower():
                            correct_dept += 1
                    
                    if search_results:
                        dept_score = (correct_dept / len(search_results)) * 40
                        score += dept_score
                        feedback.append(f"🏢 {correct_dept}/{len(search_results)} employees from correct department")
                
                # Overall relevance check (based on search scores)
                if search_results:
                    avg_score = sum(emp.get("score", 0) for emp in search_results) / len(search_results)
                    if avg_score > 0.5:
                        score += 20
                        feedback.append("📊 Good search relevance scores")
                    else:
                        feedback.append("📊 Low search relevance scores")
                
                accuracy_scores.append(score)
                
                results["test_queries"][query] = {
                    "accuracy_score": score,
                    "results_count": len(search_results),
                    "response_length": len(result.get("response", "")),
                    "feedback": feedback,
                    "processing_time_ms": result.get("processing_time_ms", 0)
                }
                
            except Exception as e:
                print(f"      ❌ Query failed: {e}")
                results["test_queries"][query] = {
                    "accuracy_score": 0,
                    "error": str(e)
                }
        
        # Calculate overall accuracy metrics
        if accuracy_scores:
            results["accuracy_metrics"] = {
                "average_accuracy": statistics.mean(accuracy_scores),
                "min_accuracy": min(accuracy_scores),
                "max_accuracy": max(accuracy_scores),
                "accuracy_std_dev": statistics.stdev(accuracy_scores) if len(accuracy_scores) > 1 else 0,
                "queries_above_70": sum(1 for score in accuracy_scores if score >= 70),
                "total_queries": len(accuracy_scores)
            }
        
        self.test_results["tests"]["search_accuracy"] = results
        return results
    
    async def test_load_performance(self, concurrent_users: int = 10, duration_seconds: int = 60) -> Dict[str, Any]:
        """Test system performance under load"""
        print(f"🔥 Load testing ({concurrent_users} concurrent users, {duration_seconds}s duration)...")
        
        results = {
            "concurrent_users": concurrent_users,
            "duration_seconds": duration_seconds,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": [],
            "throughput": {}
        }
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        # Shared data structures for thread-safe operations
        request_count = {"total": 0, "success": 0, "failed": 0}
        response_times = []
        errors = []
        lock = threading.Lock()
        
        async def worker_task():
            """Individual worker task for load testing"""
            while time.time() < end_time:
                query = self.test_queries["simple"][request_count["total"] % len(self.test_queries["simple"])]
                
                task_start = time.time()
                try:
                    result = await self.query_engine.process_query(query)
                    task_end = time.time()
                    
                    with lock:
                        request_count["total"] += 1
                        request_count["success"] += 1
                        response_times.append((task_end - task_start) * 1000)
                
                except Exception as e:
                    with lock:
                        request_count["total"] += 1
                        request_count["failed"] += 1
                        errors.append(str(e))
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)
        
        # Run concurrent workers
        tasks = [worker_task() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate results
        actual_duration = time.time() - start_time
        
        results.update({
            "total_requests": request_count["total"],
            "successful_requests": request_count["success"],
            "failed_requests": request_count["failed"],
            "actual_duration": actual_duration,
            "requests_per_second": request_count["total"] / actual_duration,
            "success_rate": request_count["success"] / max(request_count["total"], 1),
            "error_rate": request_count["failed"] / max(request_count["total"], 1)
        })
        
        if response_times:
            results["response_times"] = {
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "avg_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "p95_ms": sorted(response_times)[int(len(response_times) * 0.95)],
                "p99_ms": sorted(response_times)[int(len(response_times) * 0.99)]
            }
        
        results["top_errors"] = list(set(errors))[:10]  # Top 10 unique errors
        
        self.test_results["tests"]["load_performance"] = results
        return results
    
    async def test_api_endpoints(self, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """Test API endpoint performance"""
        print(f"🌐 Testing API endpoints at {base_url}...")
        
        results = {
            "base_url": base_url,
            "endpoints": {}
        }
        
        # Define endpoints to test
        endpoints = {
            "health": {"method": "GET", "url": "/health"},
            "query": {"method": "POST", "url": "/query", "data": {"query": "find developers", "top_k": 5}},
            "search_employees": {"method": "POST", "url": "/search/employees", "data": {"query": "IT department"}},
            "count_employees": {"method": "GET", "url": "/search/employees/count?department=IT"},
            "analytics_departments": {"method": "GET", "url": "/analytics/departments"},
            "analytics_positions": {"method": "GET", "url": "/analytics/positions"}
        }
        
        async with aiohttp.ClientSession() as session:
            for endpoint_name, config in endpoints.items():
                print(f"   🔗 Testing {endpoint_name}...")
                
                times = []
                status_codes = []
                errors = []
                
                # Test each endpoint multiple times
                for i in range(10):
                    start_time = time.time()
                    
                    try:
                        if config["method"] == "GET":
                            async with session.get(f"{base_url}{config['url']}") as response:
                                await response.text()
                                status_codes.append(response.status)
                        else:
                            async with session.post(f"{base_url}{config['url']}", 
                                                  json=config.get("data", {})) as response:
                                await response.text()
                                status_codes.append(response.status)
                        
                        end_time = time.time()
                        times.append((end_time - start_time) * 1000)
                    
                    except Exception as e:
                        errors.append(str(e))
                
                # Calculate endpoint statistics
                if times:
                    results["endpoints"][endpoint_name] = {
                        "avg_response_time_ms": statistics.mean(times),
                        "min_response_time_ms": min(times),
                        "max_response_time_ms": max(times),
                        "success_rate": len([code for code in status_codes if 200 <= code < 300]) / len(status_codes),
                        "status_codes": list(set(status_codes)),
                        "error_count": len(errors),
                        "errors": errors[:5]  # First 5 errors
                    }
                else:
                    results["endpoints"][endpoint_name] = {
                        "error": "No successful requests",
                        "errors": errors
                    }
        
        self.test_results["tests"]["api_endpoints"] = results
        return results
    
    def test_resource_usage(self, duration_seconds: int = 30) -> Dict[str, Any]:
        """Monitor resource usage during testing"""
        print(f"📊 Monitoring resource usage for {duration_seconds}s...")
        
        results = {
            "duration_seconds": duration_seconds,
            "cpu_usage": [],
            "memory_usage": [],
            "disk_io": [],
            "network_io": []
        }
        
        start_time = time.time()
        
        # Initial readings
        initial_disk = psutil.disk_io_counters()
        initial_network = psutil.net_io_counters()
        
        while time.time() - start_time < duration_seconds:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            results["cpu_usage"].append(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            results["memory_usage"].append({
                "percent": memory.percent,
                "available_mb": memory.available / (1024 * 1024),
                "used_mb": memory.used / (1024 * 1024)
            })
            
            # Disk I/O
            disk = psutil.disk_io_counters()
            results["disk_io"].append({
                "read_bytes": disk.read_bytes - initial_disk.read_bytes,
                "write_bytes": disk.write_bytes - initial_disk.write_bytes
            })
            
            # Network I/O
            network = psutil.net_io_counters()
            results["network_io"].append({
                "bytes_sent": network.bytes_sent - initial_network.bytes_sent,
                "bytes_recv": network.bytes_recv - initial_network.bytes_recv
            })
        
        # Calculate averages and peaks
        results["summary"] = {
            "avg_cpu_percent": statistics.mean(results["cpu_usage"]),
            "max_cpu_percent": max(results["cpu_usage"]),
            "avg_memory_percent": statistics.mean([m["percent"] for m in results["memory_usage"]]),
            "max_memory_percent": max([m["percent"] for m in results["memory_usage"]]),
            "total_disk_read_mb": max([d["read_bytes"] for d in results["disk_io"]]) / (1024 * 1024),
            "total_disk_write_mb": max([d["write_bytes"] for d in results["disk_io"]]) / (1024 * 1024)
        }
        
        self.test_results["tests"]["resource_usage"] = results
        return results
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive performance report"""
        report_lines = []
        
        report_lines.append("🚀 HR Q&A System Performance Test Report")
        report_lines.append("=" * 60)
        report_lines.append(f"📅 Test Date: {self.test_results['timestamp']}")
        report_lines.append(f"💻 System: {self.test_results['system_info']['cpu_count']} CPU cores, "
                          f"{self.test_results['system_info']['memory_total'] // (1024**3)}GB RAM")
        report_lines.append("")
        
        # Query Speed Results
        if "query_speed" in self.test_results["tests"]:
            speed_results = self.test_results["tests"]["query_speed"]
            report_lines.append("⚡ Query Speed Performance")
            report_lines.append("-" * 30)
            
            overall = speed_results.get("overall_stats", {})
            if overall:
                report_lines.append(f"📊 Total Queries: {overall['total_queries']}")
                report_lines.append(f"⏱️  Average Response Time: {overall['avg_ms']:.1f}ms")
                report_lines.append(f"🏃 Queries per Second: {overall['queries_per_second']:.1f}")
                report_lines.append(f"📈 95th Percentile: {overall['p95_ms']:.1f}ms")
                report_lines.append(f"📈 99th Percentile: {overall['p99_ms']:.1f}ms")
            report_lines.append("")
        
        # Search Accuracy Results
        if "search_accuracy" in self.test_results["tests"]:
            accuracy_results = self.test_results["tests"]["search_accuracy"]
            report_lines.append("🎯 Search Accuracy Performance")
            report_lines.append("-" * 30)
            
            metrics = accuracy_results.get("accuracy_metrics", {})
            if metrics:
                report_lines.append(f"📊 Average Accuracy: {metrics['average_accuracy']:.1f}%")
                report_lines.append(f"✅ Queries Above 70%: {metrics['queries_above_70']}/{metrics['total_queries']}")
                report_lines.append(f"📈 Max Accuracy: {metrics['max_accuracy']:.1f}%")
                report_lines.append(f"📉 Min Accuracy: {metrics['min_accuracy']:.1f}%")
            report_lines.append("")
        
        # Load Performance Results
        if "load_performance" in self.test_results["tests"]:
            load_results = self.test_results["tests"]["load_performance"]
            report_lines.append("🔥 Load Performance")
            report_lines.append("-" * 30)
            report_lines.append(f"👥 Concurrent Users: {load_results['concurrent_users']}")
            report_lines.append(f"⏱️  Duration: {load_results['actual_duration']:.1f}s")
            report_lines.append(f"📊 Total Requests: {load_results['total_requests']}")
            report_lines.append(f"✅ Success Rate: {load_results['success_rate']:.1%}")
            report_lines.append(f"🏃 Requests/Second: {load_results['requests_per_second']:.1f}")
            
            if "response_times" in load_results:
                rt = load_results["response_times"]
                report_lines.append(f"⏱️  Avg Response Time: {rt['avg_ms']:.1f}ms")
                report_lines.append(f"📈 95th Percentile: {rt['p95_ms']:.1f}ms")
            report_lines.append("")
        
        # API Endpoints Results
        if "api_endpoints" in self.test_results["tests"]:
            api_results = self.test_results["tests"]["api_endpoints"]
            report_lines.append("🌐 API Endpoint Performance")
            report_lines.append("-" * 30)
            
            for endpoint, stats in api_results.get("endpoints", {}).items():
                if "avg_response_time_ms" in stats:
                    report_lines.append(f"🔗 {endpoint}: {stats['avg_response_time_ms']:.1f}ms "
                                      f"(Success: {stats['success_rate']:.1%})")
            report_lines.append("")
        
        # Resource Usage Results
        if "resource_usage" in self.test_results["tests"]:
            resource_results = self.test_results["tests"]["resource_usage"]
            summary = resource_results.get("summary", {})
            if summary:
                report_lines.append("📊 Resource Usage")
                report_lines.append("-" * 30)
                report_lines.append(f"💻 Average CPU: {summary['avg_cpu_percent']:.1f}%")
                report_lines.append(f"🔥 Peak CPU: {summary['max_cpu_percent']:.1f}%")
                report_lines.append(f"🧠 Average Memory: {summary['avg_memory_percent']:.1f}%")
                report_lines.append(f"🧠 Peak Memory: {summary['max_memory_percent']:.1f}%")
                report_lines.append("")
        
        # Recommendations
        report_lines.append("💡 Performance Recommendations")
        report_lines.append("-" * 30)
        
        # Add specific recommendations based on results
        if "query_speed" in self.test_results["tests"]:
            overall = self.test_results["tests"]["query_speed"].get("overall_stats", {})
            if overall.get("avg_ms", 0) > 2000:
                report_lines.append("⚠️  Consider optimizing slow queries (>2s average)")
            if overall.get("queries_per_second", 0) < 10:
                report_lines.append("⚠️  Low throughput - consider caching or indexing improvements")
        
        if "load_performance" in self.test_results["tests"]:
            load_results = self.test_results["tests"]["load_performance"]
            if load_results.get("success_rate", 1) < 0.95:
                report_lines.append("⚠️  High error rate under load - investigate error handling")
        
        report_lines.append("✅ Performance testing completed successfully")
        
        report = "\n".join(report_lines)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"📄 Report saved to {output_file}")
        
        return report
    
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run complete performance test suite"""
        print("🎯 Running Full Performance Test Suite")
        print("=" * 50)
        
        # Setup environment
        if not await self.setup_test_environment():
            return {"error": "Failed to setup test environment"}
        
        # Run all tests
        await self.test_query_speed(iterations=50)
        await self.test_search_accuracy()
        await self.test_load_performance(concurrent_users=5, duration_seconds=30)
        
        # Monitor resource usage during a test
        resource_task = asyncio.create_task(
            asyncio.to_thread(self.test_resource_usage, 30)
        )
        
        # Test API endpoints if available
        try:
            await self.test_api_endpoints()
        except Exception as e:
            print(f"⚠️ API endpoint testing skipped: {e}")
        
        await resource_task
        
        # Generate and display report
        report = self.generate_report(f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        print("\n" + report)
        
        return self.test_results

async def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="HR Q&A System Performance Testing")
    parser.add_argument("--test", required=True,
                       choices=["query_speed", "search_accuracy", "load_test", "api_endpoints", "resource_usage", "full_suite"],
                       help="Type of test to run")
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations for speed test")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent users for load test")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds for load test")
    parser.add_argument("--host", default="localhost:8000", help="API host for endpoint testing")
    parser.add_argument("--output", help="Output file for test report")
    
    args = parser.parse_args()
    
    test_suite = PerformanceTestSuite()
    
    if args.test == "query_speed":
        await test_suite.setup_test_environment()
        await test_suite.test_query_speed(args.iterations)
    elif args.test == "search_accuracy":
        await test_suite.setup_test_environment()
        await test_suite.test_search_accuracy()
    elif args.test == "load_test":
        await test_suite.setup_test_environment()
        await test_suite.test_load_performance(args.concurrent, args.duration)
    elif args.test == "api_endpoints":
        await test_suite.test_api_endpoints(f"http://{args.host}")
    elif args.test == "resource_usage":
        test_suite.test_resource_usage(args.duration)
    elif args.test == "full_suite":
        await test_suite.run_full_test_suite()
    
    # Generate report
    report = test_suite.generate_report(args.output)
    if not args.output:
        print("\n" + report)

if __name__ == "__main__":
    asyncio.run(main())