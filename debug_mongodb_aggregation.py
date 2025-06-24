# debug_mongodb_aggregation.py
# Run this to debug the MongoDB aggregation pipeline issue

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from core.config import settings
from database.mongodb_client import mongodb_client

async def debug_mongodb_aggregation():
    """Debug the MongoDB aggregation pipeline step by step"""
    print("\n🔍 DEBUG: MongoDB Aggregation Pipeline Analysis")
    print("=" * 60)
    
    try:
        await mongodb_client.connect()
        
        # Step 1: Test individual collections
        print("📊 Step 1: Individual Collection Counts")
        personal_collection = await mongodb_client.get_collection("personal_info")
        employment_collection = await mongodb_client.get_collection("employment")
        
        personal_count = await personal_collection.count_documents({})
        employment_count = await employment_collection.count_documents({})
        
        print(f"   personal_info documents: {personal_count}")
        print(f"   employment documents: {employment_count}")
        
        # Step 2: Test specific filters
        print("\n🎯 Step 2: Specific Filter Tests")
        it_employees = await employment_collection.count_documents({"department": "IT"})
        developers = await employment_collection.count_documents({"role": "Developer"})
        it_developers = await employment_collection.count_documents({
            "department": "IT", 
            "role": "Developer"
        })
        
        print(f"   IT department employees: {it_employees}")
        print(f"   Developer role employees: {developers}")
        print(f"   IT + Developer employees: {it_developers}")
        
        # Step 3: Test sample data structure
        print("\n📋 Step 3: Sample Data Structure")
        sample_personal = await personal_collection.find_one()
        sample_employment = await employment_collection.find_one()
        
        if sample_personal:
            print(f"   Sample personal_info keys: {list(sample_personal.keys())}")
            print(f"   Sample personal_info employee_id: '{sample_personal.get('employee_id')}' (type: {type(sample_personal.get('employee_id'))})")
        
        if sample_employment:
            print(f"   Sample employment keys: {list(sample_employment.keys())}")
            print(f"   Sample employment employee_id: '{sample_employment.get('employee_id')}' (type: {type(sample_employment.get('employee_id'))})")
            print(f"   Sample employment department: '{sample_employment.get('department')}'")
            print(f"   Sample employment role: '{sample_employment.get('role')}'")
        
        # Step 4: Find the specific IT Developer
        print("\n🔍 Step 4: Finding the IT Developer")
        it_dev_employment = await employment_collection.find_one({
            "department": "IT",
            "role": "Developer"
        })
        
        if it_dev_employment:
            emp_id = it_dev_employment['employee_id']
            print(f"   Found IT Developer: employee_id = '{emp_id}'")
            
            # Check if this employee exists in personal_info
            personal_match = await personal_collection.find_one({"employee_id": emp_id})
            if personal_match:
                print(f"   ✅ Found matching personal_info: '{personal_match.get('full_name')}'")
            else:
                print(f"   ❌ No matching personal_info found for employee_id: '{emp_id}'")
        else:
            print("   ❌ No IT Developer found in employment collection")
        
        # Step 5: Test aggregation pipeline step by step
        print("\n🔧 Step 5: Aggregation Pipeline Debug")
        
        # Build the exact pipeline from enhanced engine
        pipeline = [
            # Stage 1: Lookup employment
            {
                "$lookup": {
                    "from": "employment",
                    "localField": "employee_id", 
                    "foreignField": "employee_id",
                    "as": "employment"
                }
            }
        ]
        
        print(f"   Testing Stage 1: $lookup employment")
        cursor = personal_collection.aggregate(pipeline + [{"$limit": 3}])
        stage1_results = await cursor.to_list(length=3)
        print(f"   Stage 1 results: {len(stage1_results)} documents")
        
        if stage1_results:
            sample = stage1_results[0]
            employment_array = sample.get('employment', [])
            print(f"   Sample employment array length: {len(employment_array)}")
            if employment_array:
                print(f"   Sample employment data: {employment_array[0]}")
        
        # Stage 2: Unwind employment
        pipeline.append({"$unwind": {"path": "$employment", "preserveNullAndEmptyArrays": True}})
        
        print(f"\n   Testing Stage 2: $unwind employment")
        cursor = personal_collection.aggregate(pipeline + [{"$limit": 3}])
        stage2_results = await cursor.to_list(length=3)
        print(f"   Stage 2 results: {len(stage2_results)} documents")
        
        if stage2_results:
            sample = stage2_results[0]
            print(f"   Sample after unwind - employment keys: {list(sample.get('employment', {}).keys())}")
            print(f"   Sample after unwind - department: '{sample.get('employment', {}).get('department')}'")
            print(f"   Sample after unwind - role: '{sample.get('employment', {}).get('role')}'")
        
        # Stage 3: Add debug fields
        pipeline.append({
            "$addFields": {
                "debug_department": "$employment.department",
                "debug_role": "$employment.role",
                "debug_has_employment": {"$cond": [{"$ifNull": ["$employment", False]}, True, False]}
            }
        })
        
        print(f"\n   Testing Stage 3: Add debug fields")
        cursor = personal_collection.aggregate(pipeline + [{"$limit": 5}])
        stage3_results = await cursor.to_list(length=5)
        print(f"   Stage 3 results: {len(stage3_results)} documents")
        
        if stage3_results:
            for i, doc in enumerate(stage3_results):
                dept = doc.get('debug_department')
                role = doc.get('debug_role')
                has_emp = doc.get('debug_has_employment')
                print(f"     Doc {i+1}: dept='{dept}', role='{role}', has_employment={has_emp}")
        
        # Stage 4: Match IT Developers
        pipeline.append({
            "$match": {
                "employment.department": "IT",
                "employment.role": "Developer"
            }
        })
        
        print(f"\n   Testing Stage 4: Match IT Developers")
        cursor = personal_collection.aggregate(pipeline)
        stage4_results = await cursor.to_list(length=10)
        print(f"   Stage 4 results: {len(stage4_results)} documents")
        
        if stage4_results:
            for doc in stage4_results:
                name = doc.get('full_name')
                dept = doc.get('employment', {}).get('department')
                role = doc.get('employment', {}).get('role')
                print(f"     Found: {name} - {dept} - {role}")
        
        # Stage 5: Count
        count_pipeline = pipeline + [{"$count": "total"}]
        print(f"\n   Testing Stage 5: Count")
        cursor = personal_collection.aggregate(count_pipeline)
        count_results = await cursor.to_list(length=1)
        print(f"   Count results: {count_results}")
        
        # Step 6: Test alternative approaches
        print(f"\n🔄 Step 6: Alternative Approaches")
        
        # Approach A: Direct employment query
        print(f"   Approach A: Direct employment query")
        it_devs = await employment_collection.find({
            "department": "IT",
            "role": "Developer"
        }).to_list(length=None)
        print(f"   Direct query found: {len(it_devs)} IT developers")
        
        if it_devs:
            for dev in it_devs:
                emp_id = dev['employee_id']
                personal = await personal_collection.find_one({"employee_id": emp_id})
                if personal:
                    print(f"     {personal.get('full_name')} (ID: {emp_id})")
        
        # Approach B: Simple aggregation
        print(f"\n   Approach B: Simplified aggregation")
        simple_pipeline = [
            {
                "$lookup": {
                    "from": "employment",
                    "localField": "employee_id",
                    "foreignField": "employee_id", 
                    "as": "emp_data"
                }
            },
            {"$unwind": "$emp_data"},
            {
                "$match": {
                    "emp_data.department": "IT",
                    "emp_data.role": "Developer"
                }
            },
            {"$count": "total"}
        ]
        
        cursor = personal_collection.aggregate(simple_pipeline)
        simple_results = await cursor.to_list(length=1)
        print(f"   Simplified aggregation result: {simple_results}")
        
        # Step 7: Check for case sensitivity and exact matches
        print(f"\n🔍 Step 7: Case Sensitivity Check")
        
        # Get all unique departments and roles
        dept_cursor = employment_collection.aggregate([
            {"$group": {"_id": "$department"}},
            {"$sort": {"_id": 1}}
        ])
        departments = await dept_cursor.to_list(length=None)
        
        role_cursor = employment_collection.aggregate([
            {"$group": {"_id": "$role"}},
            {"$sort": {"_id": 1}}
        ])
        roles = await role_cursor.to_list(length=None)
        
        print(f"   All departments: {[d['_id'] for d in departments]}")
        print(f"   All roles: {[r['_id'] for r in roles]}")
        
        # Test exact matches
        for dept in ["IT", "it", "It"]:
            count = await employment_collection.count_documents({"department": dept})
            print(f"   Department '{dept}': {count} employees")
        
        for role in ["Developer", "developer", "Developer "]:
            count = await employment_collection.count_documents({"role": role})
            print(f"   Role '{role}': {count} employees")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function"""
    print("🚀 MongoDB Aggregation Debug")
    print("Will analyze why aggregation returns 0 when we expect 1 IT Developer")
    
    await debug_mongodb_aggregation()
    
    print("\n" + "=" * 60)
    print("🎯 Debug completed! Check the output above to see where the pipeline breaks.")

if __name__ == "__main__":
    asyncio.run(main())