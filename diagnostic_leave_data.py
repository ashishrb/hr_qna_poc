# diagnostic_leave_data.py
import asyncio
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database.mongodb_client import mongodb_client
from src.database.collections import employee_collections

async def diagnose_leave_data():
    """Diagnose leave data in the database"""
    print("🔍 Diagnosing Leave Data in Database")
    print("=" * 50)
    
    try:
        # Connect to MongoDB
        await mongodb_client.connect()
        print("✅ Connected to MongoDB")
        
        # Check if attendance collection exists
        collections = await mongodb_client.get_collections()
        print(f"📋 Available collections: {collections}")
        
        if 'attendance' in collections:
            print("\n📊 Checking Attendance Collection:")
            
            # Get sample attendance data
            sample_attendance = await mongodb_client.find_documents('attendance', {}, limit=5)
            print(f"   📄 Sample records: {len(sample_attendance)}")
            
            if sample_attendance:
                print("\n👀 Sample Attendance Records:")
                for i, record in enumerate(sample_attendance, 1):
                    print(f"   {i}. Employee ID: {record.get('employee_id', 'N/A')}")
                    print(f"      Leave Days Taken: {record.get('leave_days_taken', 'N/A')}")
                    print(f"      Leave Balance: {record.get('leave_balance', 'N/A')}")
                    print(f"      Monthly Attendance: {record.get('monthly_attendance_pct', 'N/A')}")
                    print(f"      Leave Pattern: {record.get('leave_pattern', 'N/A')}")
                    print()
                
                # Check leave days distribution
                print("📈 Leave Days Analysis:")
                all_attendance = await mongodb_client.find_documents('attendance', {})
                
                leave_days_list = []
                for record in all_attendance:
                    leave_days = record.get('leave_days_taken')
                    if leave_days is not None:
                        try:
                            leave_days_list.append(int(leave_days))
                        except (ValueError, TypeError):
                            pass
                
                if leave_days_list:
                    print(f"   📊 Total employees with leave data: {len(leave_days_list)}")
                    print(f"   📈 Max leave days taken: {max(leave_days_list)}")
                    print(f"   📉 Min leave days taken: {min(leave_days_list)}")
                    print(f"   📐 Average leave days: {sum(leave_days_list)/len(leave_days_list):.1f}")
                    
                    # Find employees with high leave usage
                    high_leave_threshold = 15  # Threshold for "high" leave
                    high_leave_employees = [days for days in leave_days_list if days >= high_leave_threshold]
                    print(f"   🔴 Employees with ≥{high_leave_threshold} days: {len(high_leave_employees)}")
                    
                    max_leave_days = max(leave_days_list)
                    max_leave_employees = [days for days in leave_days_list if days == max_leave_days]
                    print(f"   🏆 Employees with maximum leave ({max_leave_days} days): {len(max_leave_employees)}")
                else:
                    print("   ❌ No valid leave days data found")
            else:
                print("   ❌ No attendance records found")
        else:
            print("❌ Attendance collection not found")
        
        # Test the specific aggregation pipeline that the intelligent engine would use
        print("\n🧪 Testing MongoDB Aggregation Pipeline:")
        await test_aggregation_pipeline()
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await mongodb_client.disconnect()

async def test_aggregation_pipeline():
    """Test the aggregation pipeline used by intelligent query engine"""
    try:
        collection = await mongodb_client.get_collection("personal_info")
        
        # This is similar to what the intelligent engine does
        pipeline = [
            {
                "$lookup": {
                    "from": "employment",
                    "localField": "employee_id", 
                    "foreignField": "employee_id",
                    "as": "employment"
                }
            },
            {
                "$lookup": {
                    "from": "attendance",
                    "localField": "employee_id",
                    "foreignField": "employee_id",
                    "as": "attendance" 
                }
            },
            {"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}},
            {"$unwind": {"path": "$attendance", "preserveNullAndEmptyArrays": True}},
            {
                "$match": {
                    "attendance.leave_days_taken": {"$gte": 15}  # High leave threshold
                }
            },
            {"$count": "total"}
        ]
        
        print("   🔄 Running aggregation pipeline for high leave users...")
        cursor = collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        if results:
            print(f"   ✅ Pipeline result: {results[0]['total']} employees with high leave")
        else:
            print("   ❌ Pipeline returned no results")
            
        # Try simpler aggregation
        print("   🔄 Testing simpler attendance query...")
        simple_pipeline = [
            {
                "$lookup": {
                    "from": "attendance",
                    "localField": "employee_id",
                    "foreignField": "employee_id",
                    "as": "attendance" 
                }
            },
            {"$unwind": {"path": "$attendance", "preserveNullAndEmptyArrays": True}},
            {"$match": {"attendance.leave_days_taken": {"$exists": True}}},
            {"$count": "total"}
        ]
        
        cursor = collection.aggregate(simple_pipeline)
        results = await cursor.to_list(length=None)
        
        if results:
            print(f"   ✅ Employees with leave data: {results[0]['total']}")
        else:
            print("   ❌ No employees with leave data found")
            
    except Exception as e:
        print(f"   ❌ Aggregation test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main diagnostic function"""
    await diagnose_leave_data()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Diagnosis interrupted by user")
    except Exception as e:
        print(f"\n❌ Diagnosis failed: {e}")