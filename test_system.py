#!/usr/bin/env python3
"""
HR Q&A System - Comprehensive Connectivity Test
Tests all components: MongoDB, Ollama, API, and UI
"""

import asyncio
import requests
import json
import time
import sys
import os
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.mongodb_client import mongodb_client
from src.ai.ollama_client import ollama_client
from src.query.ollama_query_engine import ollama_query_engine
from src.search.local_search_client import local_search_client

class SystemTester:
    """Comprehensive system connectivity tester"""
    
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    async def test_mongodb(self) -> bool:
        """Test MongoDB connectivity"""
        print("🗄️ Testing MongoDB Connection...")
        
        try:
            # Test connection
            connected = await mongodb_client.connect()
            if not connected:
                print("❌ MongoDB connection failed")
                return False
            
            # Test database operations
            collections = await mongodb_client.get_collections()
            print(f"✅ MongoDB connected - Found {len(collections)} collections")
            
            # Test data access
            count = await mongodb_client.count_documents("personal_info")
            print(f"✅ Personal info collection has {count} documents")
            
            self.results['mongodb'] = {
                'status': 'connected',
                'collections': len(collections),
                'documents': count
            }
            
            return True
            
        except Exception as e:
            print(f"❌ MongoDB test failed: {e}")
            self.results['mongodb'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_ollama(self) -> bool:
        """Test Ollama connectivity"""
        print("🤖 Testing Ollama Connection...")
        
        try:
            # Test basic connection
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code != 200:
                print("❌ Ollama server not responding")
                return False
            
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            print(f"✅ Ollama connected - Found {len(models)} models: {model_names}")
            
            # Test text generation
            test_response = ollama_client.generate_text("Hello, how are you?", max_tokens=10)
            if test_response and len(test_response) > 0:
                print(f"✅ Text generation working: {test_response[:50]}...")
            else:
                print("❌ Text generation failed")
                return False
            
            # Test query analysis
            analysis = ollama_client.analyze_query_intent("How many employees work in IT?")
            if analysis and 'intent' in analysis:
                print(f"✅ Query analysis working: {analysis['intent']}")
            else:
                print("❌ Query analysis failed")
                return False
            
            self.results['ollama'] = {
                'status': 'connected',
                'models': len(models),
                'text_generation': True,
                'query_analysis': True
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Ollama test failed: {e}")
            self.results['ollama'] = {'status': 'failed', 'error': str(e)}
            return False
    
    async def test_query_engine(self) -> bool:
        """Test query engine functionality"""
        print("🔍 Testing Query Engine...")
        
        try:
            # Test simple query
            result = await ollama_query_engine.process_query("How many employees work in IT?")
            
            if result['status'] == 'success':
                print(f"✅ Query engine working - Intent: {result['intent']}")
                print(f"✅ Found {result['count']} results in {result['execution_time_ms']:.1f}ms")
            else:
                print(f"❌ Query engine failed: {result.get('error', 'Unknown error')}")
                return False
            
            # Test complex query
            complex_result = await ollama_query_engine.process_query("Show me top 5 performers")
            if complex_result['status'] == 'success':
                print(f"✅ Complex queries working - Found {complex_result['count']} results")
            else:
                print("⚠️ Complex queries may have issues")
            
            self.results['query_engine'] = {
                'status': 'working',
                'simple_queries': True,
                'complex_queries': complex_result['status'] == 'success',
                'response_time_ms': result['execution_time_ms']
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Query engine test failed: {e}")
            self.results['query_engine'] = {'status': 'failed', 'error': str(e)}
            return False
    
    async def test_search_client(self) -> bool:
        """Test local search client"""
        print("🔎 Testing Local Search Client...")
        
        try:
            # Test basic search
            results = await local_search_client.search("developer", top_k=3)
            print(f"✅ Search working - Found {len(results)} results")
            
            # Test document count
            count = await local_search_client.get_document_count()
            print(f"✅ Document count: {count}")
            
            # Test suggestions
            suggestions = await local_search_client.suggest("IT", top_k=3)
            print(f"✅ Suggestions working - {len(suggestions)} suggestions")
            
            self.results['search_client'] = {
                'status': 'working',
                'search_results': len(results),
                'document_count': count,
                'suggestions': len(suggestions)
            }
            
            return True
            
        except Exception as e:
            print(f"❌ Search client test failed: {e}")
            self.results['search_client'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_api_server(self) -> bool:
        """Test API server endpoints"""
        print("🌐 Testing API Server...")
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API server running - Status: {health_data['status']}")
            else:
                print(f"❌ API server health check failed: {response.status_code}")
                return False
            
            # Test query endpoint
            query_payload = {
                "query": "How many employees work in IT?",
                "top_k": 5
            }
            
            response = requests.post(
                "http://localhost:8000/query",
                json=query_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                query_data = response.json()
                print(f"✅ Query endpoint working - Found {query_data['count']} results")
            else:
                print(f"❌ Query endpoint failed: {response.status_code}")
                return False
            
            # Test analytics endpoint
            response = requests.get("http://localhost:8000/analytics/overview", timeout=10)
            if response.status_code == 200:
                analytics_data = response.json()
                print(f"✅ Analytics endpoint working - {analytics_data['total_employees']} employees")
            else:
                print("⚠️ Analytics endpoint may have issues")
            
            self.results['api_server'] = {
                'status': 'running',
                'health_check': True,
                'query_endpoint': True,
                'analytics_endpoint': response.status_code == 200
            }
            
            return True
            
        except requests.exceptions.ConnectionError:
            print("❌ API server not running - Start with: python src/api/main.py")
            self.results['api_server'] = {'status': 'not_running'}
            return False
        except Exception as e:
            print(f"❌ API server test failed: {e}")
            self.results['api_server'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def test_web_interface(self) -> bool:
        """Test web interface accessibility"""
        print("🖥️ Testing Web Interface...")
        
        try:
            # Test main page
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                print("✅ Web interface accessible")
                
                # Check if it's HTML
                if 'text/html' in response.headers.get('content-type', ''):
                    print("✅ Serving HTML content")
                else:
                    print("⚠️ Not serving HTML content")
                
                self.results['web_interface'] = {
                    'status': 'accessible',
                    'serving_html': 'text/html' in response.headers.get('content-type', '')
                }
                
                return True
            else:
                print(f"❌ Web interface failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Web interface test failed: {e}")
            self.results['web_interface'] = {'status': 'failed', 'error': str(e)}
            return False
    
    def print_summary(self):
        """Print test summary"""
        total_time = time.time() - self.start_time
        
        print("\n" + "="*60)
        print("📊 SYSTEM TEST SUMMARY")
        print("="*60)
        
        components = [
            ('MongoDB', 'mongodb'),
            ('Ollama', 'ollama'),
            ('Query Engine', 'query_engine'),
            ('Search Client', 'search_client'),
            ('API Server', 'api_server'),
            ('Web Interface', 'web_interface')
        ]
        
        passed = 0
        total = len(components)
        
        for name, key in components:
            result = self.results.get(key, {})
            status = result.get('status', 'unknown')
            
            if status in ['connected', 'working', 'running', 'accessible']:
                print(f"✅ {name}: {status.upper()}")
                passed += 1
            elif status == 'not_running':
                print(f"⚠️ {name}: NOT RUNNING")
            else:
                print(f"❌ {name}: FAILED")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
        
        print(f"\n📈 Results: {passed}/{total} components working")
        print(f"⏱️ Total test time: {total_time:.1f} seconds")
        
        if passed == total:
            print("\n🎉 ALL SYSTEMS OPERATIONAL!")
            print("🚀 Your HR Q&A System is ready for use!")
            print("🌐 Open your browser to: http://localhost:8000")
        elif passed >= total - 1:
            print("\n✅ System mostly working - minor issues detected")
        else:
            print("\n❌ System has significant issues - check the errors above")
        
        return passed == total

async def main():
    """Main test function"""
    print("🧪 HR Q&A System - Comprehensive Connectivity Test")
    print("="*60)
    
    tester = SystemTester()
    
    # Run all tests
    await tester.test_mongodb()
    tester.test_ollama()
    await tester.test_query_engine()
    await tester.test_search_client()
    tester.test_api_server()
    tester.test_web_interface()
    
    # Print summary
    success = tester.print_summary()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
