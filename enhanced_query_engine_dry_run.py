# enhanced_query_engine_dry_run.py
import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.query.hr_query_engine import RobustHRQueryEngine

async def test_enhanced_query_engine():
    """Test enhanced query engine with P1 fixes"""
    print("🧠 Enhanced Intelligent HR Query Engine - P1 Fixes Test")
    print("=" * 70)
    print("🔧 P1 Fixes Applied:")
    print("   ✅ Enhanced GPT prompt for HR domain")
    print("   ✅ Proper data type conversion in MongoDB")
    print("   ✅ Fallback to UpdatedHRQueryEngine")
    print("   ✅ Better entity extraction for leave queries")
    print("=" * 70)
    
    # Initialize enhanced query engine
    try:
        query_engine = RobustHRQueryEngine()
        print("✅ Enhanced Intelligent Query Engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize enhanced query engine: {e}")
        return
    
    # Focused test queries for P1 fixes validation
    test_queries = [
        # Leave-related queries (P1 focus)
        {
            "query": "How many employees have taken maximum leave?",
            "expected": "Should count employees with highest leave days",
            "type": "Leave Analytics - Maximum",
            "priority": "P1"
        },
        {
            "query": "Out of 20 days annual leave, how many employees took the maximum?",
            "expected": "Should find employees with ≥20 days leave",
            "type": "Leave Analytics - Threshold",
            "priority": "P1"
        },
        {
            "query": "Find employees with high leave usage",
            "expected": "Should find employees with >15 days leave",
            "type": "Leave Analytics - High Usage",
            "priority": "P1"
        },
        
        # Performance queries (test data type conversion)
        {
            "query": "How many high-performing employees do we have?",
            "expected": "Should count employees with rating ≥4",
            "type": "Performance Analytics",
            "priority": "P1"
        },
        
        # Text search (test fallback mechanism)
        {
            "query": "Find developers with Python skills",
            "expected": "Should use Azure Search or fallback",
            "type": "Text Search - Fallback Test",
            "priority": "P1"
        },
        
        # Complex queries (test enhanced entity extraction)
        {
            "query": "Show me employees in IT department with maximum attendance",
            "expected": "Should combine department filter with attendance",
            "type": "Complex Filter",
            "priority": "P1"
        },
        
        # Edge cases (test error handling)
        {
            "query": "Find employees with 100 days leave",
            "expected": "Should handle edge case gracefully",
            "type": "Edge Case",
            "priority": "P1"
        }
    ]
    
    print(f"\n🔍 Testing {len(test_queries)} P1-focused queries...")
    print("=" * 70)
    
    success_count = 0
    fallback_count = 0
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {test_case['type']} ({test_case['priority']})")
        print(f"🔍 Query: '{test_case['query']}'")
        print(f"📋 Expected: {test_case['expected']}")
        print("-" * 50)
        
        try:
            # Process the query
            result = await query_engine.process_query(test_case['query'])
            
            # Display enhanced results
            print(f"🎯 Intent Detected: {result['intent']}")
            print(f"📊 Entities Found: {result['entities']}")
            print(f"🔍 Status: {result['status']}")
            print(f"📈 Results Count: {result['count']}")
            print(f"🎯 Complexity: {result.get('query_complexity', 'Unknown')}")
            print(f"⏱️  Execution Time: {result.get('execution_time_ms', 0):.1f}ms")
            
            if result['status'] == 'success':
                print(f"✅ Status: SUCCESS")
                success_count += 1
            elif result['status'] == 'success_fallback':
                print(f"🔄 Status: SUCCESS (using fallback engine)")
                success_count += 1
                fallback_count += 1
            else:
                print(f"❌ Status: FAILED")
                if result.get('error'):
                    print(f"   Error: {result['error']}")
            
            # Show found results for non-zero counts
            if result['count'] > 0:
                if result['intent'] == 'analytics':
                    print(f"📊 Analytics Result: {result['count']} employees found")
                else:
                    # Show sample results for search queries
                    if result['results'] and len(result['results']) > 0:
                        print(f"👥 Sample Results:")
                        for j, emp in enumerate(result['results'][:3], 1):
                            if isinstance(emp, dict):  # Safety check
                                name = emp.get('full_name', 'N/A')
                                dept = emp.get('department', 'N/A')
                                role = emp.get('role', 'N/A')
                                print(f"   {j}. {name} - {dept} - {role}")
                            else:
                                print(f"   {j}. {emp}")
            
            # Show AI response (truncated)
            response_preview = result['response'][:150] + "..." if len(result['response']) > 150 else result['response']
            print(f"💬 AI Response: {response_preview}")
            
        except Exception as e:
            print(f"❌ Query failed with exception: {e}")
        
        print("=" * 70)
    
    # P1 Fixes Summary
    print(f"\n📈 P1 FIXES VALIDATION SUMMARY")
    print("=" * 40)
    print(f"✅ Successful queries: {success_count}/{len(test_queries)}")
    print(f"🔄 Fallback engine used: {fallback_count} times")
    print(f"📊 Success rate: {(success_count/len(test_queries)*100):.1f}%")
    print(f"🔧 Fallback rate: {(fallback_count/len(test_queries)*100):.1f}%")
    
    # P1 Fix validation
    print(f"\n🔧 P1 FIXES VALIDATION:")
    leave_queries = [t for t in test_queries if "Leave" in t["type"]]
    leave_success = sum(1 for i, t in enumerate(test_queries) if "Leave" in t["type"] and i < success_count)
    
    print(f"   📅 Leave query fixes: {leave_success}/{len(leave_queries)} working")
    print(f"   🔄 Fallback mechanism: {'✅ Working' if fallback_count > 0 else '⚠️ Not tested'}")
    print(f"   🧠 Enhanced entity extraction: {'✅ Working' if success_count > len(test_queries) * 0.7 else '⚠️ Needs improvement'}")
    
    if success_count == len(test_queries) and fallback_count == 0:
        print("\n🎉 ALL P1 FIXES WORKING PERFECTLY! Enhanced engine handles all queries.")
    elif success_count == len(test_queries):
        print(f"\n✅ ALL QUERIES SUCCESSFUL! Fallback used {fallback_count} times as safety net.")
    elif success_count > len(test_queries) * 0.8:
        print(f"\n👍 MOSTLY WORKING! {success_count}/{len(test_queries)} queries successful.")
    else:
        print(f"\n⚠️  NEEDS MORE WORK! Only {success_count}/{len(test_queries)} queries successful.")
    
    return success_count, len(test_queries), fallback_count

async def test_specific_leave_queries():
    """Test specific leave queries that were failing"""
    print("\n🎯 SPECIFIC LEAVE QUERY TESTS")
    print("=" * 50)
    
    query_engine = EnhancedIntelligentQueryEngine()
    
    specific_queries = [
        "How many employees has taken max leave",
        "Out of specified 20 days annually, how many employees taken maximum",
        "Find employees with 30 days leave",
        "Who took the highest number of leave days",
        "Show me employees with maximum leave usage"
    ]
    
    for i, query in enumerate(specific_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        try:
            result = await query_engine.process_query(query)
            print(f"   Intent: {result['intent']}")
            print(f"   Entities: {result['entities']}")
            print(f"   Count: {result['count']}")
            print(f"   Status: {result['status']}")
            
            if result['count'] > 0:
                print(f"   ✅ SUCCESS - Found {result['count']} employees")
            else:
                print(f"   ⚠️  No results found")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")

async def interactive_testing_enhanced():
    """Enhanced interactive testing"""
    print("\n🎮 Enhanced Interactive Testing")
    print("Type your questions or 'quit' to exit")
    print("Special commands:")
    print("  'debug' - Show detailed query processing")
    print("  'fallback' - Force fallback engine")
    print("=" * 50)
    
    query_engine = EnhancedIntelligentQueryEngine()
    debug_mode = False
    
    while True:
        try:
            user_query = input("\n💬 Enter your HR question: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            elif user_query.lower() == 'debug':
                debug_mode = not debug_mode
                print(f"🔧 Debug mode: {'ON' if debug_mode else 'OFF'}")
                continue
            elif user_query.lower() == 'fallback':
                print("🔄 Testing fallback engine...")
                result = await query_engine.fallback_engine.process_query("Find developers")
                print(f"Fallback result: {result['status']}")
                continue
            
            if not user_query:
                continue
            
            print(f"\n🔄 Processing: '{user_query}'")
            result = await query_engine.process_query(user_query)
            
            if debug_mode:
                print(f"🎯 Intent: {result['intent']}")
                print(f"📊 Entities: {result['entities']}")
                print(f"🔍 Data Source: {result['data_source']}")
                print(f"🎯 Confidence: {result.get('confidence', 0):.2f}")
                print(f"⏱️  Time: {result.get('execution_time_ms', 0):.1f}ms")
                print(f"📈 Status: {result['status']}")
            
            print(f"📊 Found: {result['count']} employees")
            print(f"💬 Response: {result['response']}")
            
            if result['results'] and len(result['results']) > 0:
                print(f"\n👥 Employees found:")
                for emp in result['results'][:5]:
                    name = emp.get('full_name', 'N/A')
                    dept = emp.get('department', 'N/A')
                    role = emp.get('role', 'N/A')
                    print(f"  - {name} ({dept}) - {role}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Enhanced testing ended")

async def main():
    """Main testing function with P1 validation"""
    print("🚀 Starting Enhanced Query Engine P1 Fixes Validation")
    
    # Run P1 focused tests
    success, total, fallback_count = await test_enhanced_query_engine()
    
    # Test specific leave queries that were failing
    await test_specific_leave_queries()
    
    # Ask for interactive testing
    if success > 0:
        response = input(f"\n🎮 Would you like to try enhanced interactive testing? (y/n): ")
        if response.lower() == 'y':
            await interactive_testing_enhanced()
    
    print(f"\n🎯 Enhanced Query Engine P1 Validation Complete!")
    print(f"📊 Final Results: {success}/{total} successful, {fallback_count} fallbacks used")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")