# query_engine_dry_run.py
import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.query.intelligent_query_engine import IntelligentQueryEngine  # Correct import

async def test_query_engine_with_real_data():
    """Test query engine with real employee data"""
    print("🤖 Intelligent HR Query Engine - Dry Run Testing")
    print("=" * 60)
    print("Testing with REAL employee data from MongoDB")
    print("🧠 Using AI-powered query routing and execution")
    print(f"📊 Available data: 25 employees across 10 collections")
    print("=" * 60)
    
    # Initialize query engine
    try:
        query_engine = IntelligentQueryEngine()
        print("✅ Intelligent Query Engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize intelligent query engine: {e}")
        return
    
    # Test queries based on your actual data structure
    test_queries = [
        # Department-based queries (Sales, etc.)
        {
            "query": "Who are the developers in our company?",
            "expected": "Should find employees with role='Developer'",
            "type": "Employee Search"
        },
        {
            "query": "Find employees in Sales department",
            "expected": "Should find employees from Sales dept",
            "type": "Department Search"
        },
        {
            "query": "How many people work in Sales?",
            "expected": "Should count Sales employees",
            "type": "Count Query"
        },
        
        # Skill/Certification queries (GCP, etc.)
        {
            "query": "Find employees with GCP certification",
            "expected": "Should find employees with GCP skills",
            "type": "Skill Search"
        },
        {
            "query": "Who has cloud certifications?",
            "expected": "Should find GCP/AWS certified employees",
            "type": "Skill Search"
        },
        
        # Location-based queries
        {
            "query": "Find Offshore employees",
            "expected": "Should find employees in Offshore location",
            "type": "Location Search"
        },
        {
            "query": "Show me employees working in Hybrid mode",
            "expected": "Should find work_mode='Hybrid' employees",
            "type": "Work Mode Search"
        },
        
        # Performance-based queries
        {
            "query": "Find high-performing employees",
            "expected": "Should find employees with high performance ratings",
            "type": "Performance Search"
        },
        {
            "query": "Show employees with high attrition risk",
            "expected": "Should find attrition_risk_score='High' employees",
            "type": "Attrition Search"
        },
        
        # Complex queries
        {
            "query": "Find developers with GCP certification in Sales department",
            "expected": "Complex multi-filter search",
            "type": "Complex Search"
        }
    ]
    
    print(f"\n🔍 Testing {len(test_queries)} different query types...")
    print("=" * 60)
    
    success_count = 0
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {test_case['type']}")
        print(f"🔍 Query: '{test_case['query']}'")
        print(f"📋 Expected: {test_case['expected']}")
        print("-" * 50)
        
        try:
            # Process the query
            result = await query_engine.process_query(test_case['query'])
            
            # Display results
            print(f"🎯 Intent Detected: {result['intent']}")
            print(f"📊 Entities Found: {result['entities']}")
            print(f"🔍 Data Source: {result['data_source']}")
            print(f"📈 Search Results: {len(result['results'])} employees found")
            
            if result['status'] == 'success':
                print(f"✅ Status: SUCCESS")
                success_count += 1
                
                # Show found employees (top 3)
                if result['results']:
                    print(f"👥 Top Results:")
                    for j, emp in enumerate(result['results'][:3], 1):
                        print(f"   {j}. {emp.get('full_name', 'N/A')} - {emp.get('department', 'N/A')} - {emp.get('role', 'N/A')}")
                        if emp.get('certifications'):
                            print(f"      🏆 Certifications: {emp.get('certifications')}")
                
                # Show count for count queries
                if result.get('count', 0) > 0:
                    print(f"📊 Count Result: {result['count']} employees")
                
                # Show AI response
                print(f"💬 AI Response: {result['response'][:200]}...")
                
                # Show confidence and execution time
                if result.get('confidence'):
                    print(f"🎯 Confidence: {result['confidence']:.2f}")
                if result.get('execution_time_ms'):
                    print(f"⏱️  Execution Time: {result['execution_time_ms']:.1f}ms")
                
            else:
                print(f"❌ Status: FAILED")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
            
        except Exception as e:
            print(f"❌ Query failed with exception: {e}")
        
        print("=" * 60)
    
    # Summary
    print(f"\n📈 DRY RUN SUMMARY")
    print("=" * 30)
    print(f"✅ Successful queries: {success_count}/{len(test_queries)}")
    print(f"📊 Success rate: {(success_count/len(test_queries)*100):.1f}%")
    
    if success_count == len(test_queries):
        print("🎉 ALL TESTS PASSED! Query engine working perfectly with real data.")
    elif success_count > len(test_queries) * 0.7:
        print("✅ MOSTLY WORKING! Some queries need fine-tuning.")
    else:
        print("⚠️  NEEDS ATTENTION! Several queries failed - check search index.")
    
    return success_count, len(test_queries)

async def interactive_testing():
    """Interactive testing mode"""
    print("\n🎮 Interactive Query Testing")
    print("Type your questions or 'quit' to exit")
    print("=" * 40)
    
    query_engine = IntelligentQueryEngine()
    
    while True:
        try:
            user_query = input("\n💬 Enter your HR question: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_query:
                continue
            
            print(f"\n🔄 Processing: '{user_query}'")
            result = await query_engine.process_query(user_query)
            
            print(f"🎯 Intent: {result['intent']}")
            print(f"📊 Found: {len(result['results'])} employees")
            print(f"💬 Response: {result['response']}")
            
            if result['results']:
                print(f"\n👥 Employees found:")
                for emp in result['results'][:5]:
                    print(f"  - {emp.get('full_name', 'N/A')} ({emp.get('department', 'N/A')}) - {emp.get('role', 'N/A')}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Interactive testing ended")

async def main():
    """Main testing function"""
    print("🚀 Starting Query Engine Dry Run")
    
    # Run automated tests
    success, total = await test_query_engine_with_real_data()
    
    # Ask for interactive testing
    if success > 0:
        response = input(f"\n🎮 Would you like to try interactive testing? (y/n): ")
        if response.lower() == 'y':
            await interactive_testing()
    
    print(f"\n🎯 Query Engine Dry Run Complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")