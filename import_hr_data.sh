#!/bin/bash
# MongoDB Import Script for HR Demo Data
# Run this script to import HR data into your local MongoDB

echo "🚀 Importing HR Demo Data to MongoDB..."

# Collections to import
collections=(
    "employee_personal_info"
    "employee_employment_info" 
    "employee_learning_info"
    "employee_experience_info"
    "employee_performance_info"
    "employee_engagement_info"
    "employee_compensation_info"
    "employee_attendance_info"
    "employee_attrition_info"
)

# Create temporary JSON files for each collection

# Extract employee_personal_info data
echo "📝 Creating employee_personal_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_personal_info.json', 'w') as f:
    json.dump([emp['personal_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_personal_info..."
mongoimport --db hr_qna_poc --collection employee_personal_info --file employee_personal_info.json --jsonArray

# Clean up
rm employee_personal_info.json

# Extract employee_employment_info data
echo "📝 Creating employee_employment_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_employment_info.json', 'w') as f:
    json.dump([emp['employment_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_employment_info..."
mongoimport --db hr_qna_poc --collection employee_employment_info --file employee_employment_info.json --jsonArray

# Clean up
rm employee_employment_info.json

# Extract employee_learning_info data
echo "📝 Creating employee_learning_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_learning_info.json', 'w') as f:
    json.dump([emp['learning_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_learning_info..."
mongoimport --db hr_qna_poc --collection employee_learning_info --file employee_learning_info.json --jsonArray

# Clean up
rm employee_learning_info.json

# Extract employee_experience_info data
echo "📝 Creating employee_experience_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_experience_info.json', 'w') as f:
    json.dump([emp['experience_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_experience_info..."
mongoimport --db hr_qna_poc --collection employee_experience_info --file employee_experience_info.json --jsonArray

# Clean up
rm employee_experience_info.json

# Extract employee_performance_info data
echo "📝 Creating employee_performance_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_performance_info.json', 'w') as f:
    json.dump([emp['performance_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_performance_info..."
mongoimport --db hr_qna_poc --collection employee_performance_info --file employee_performance_info.json --jsonArray

# Clean up
rm employee_performance_info.json

# Extract employee_engagement_info data
echo "📝 Creating employee_engagement_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_engagement_info.json', 'w') as f:
    json.dump([emp['engagement_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_engagement_info..."
mongoimport --db hr_qna_poc --collection employee_engagement_info --file employee_engagement_info.json --jsonArray

# Clean up
rm employee_engagement_info.json

# Extract employee_compensation_info data
echo "📝 Creating employee_compensation_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_compensation_info.json', 'w') as f:
    json.dump([emp['compensation_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_compensation_info..."
mongoimport --db hr_qna_poc --collection employee_compensation_info --file employee_compensation_info.json --jsonArray

# Clean up
rm employee_compensation_info.json

# Extract employee_attendance_info data
echo "📝 Creating employee_attendance_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_attendance_info.json', 'w') as f:
    json.dump([emp['attendance_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_attendance_info..."
mongoimport --db hr_qna_poc --collection employee_attendance_info --file employee_attendance_info.json --jsonArray

# Clean up
rm employee_attendance_info.json

# Extract employee_attrition_info data
echo "📝 Creating employee_attrition_info data..."
python3 -c "
import json
with open('hr_demo_data.json', 'r') as f:
    data = json.load(f)
with open('employee_attrition_info.json', 'w') as f:
    json.dump([emp['attrition_info'] for emp in data], f, indent=2)
"

# Import to MongoDB
echo "📥 Importing employee_attrition_info..."
mongoimport --db hr_qna_poc --collection employee_attrition_info --file employee_attrition_info.json --jsonArray

# Clean up
rm employee_attrition_info.json

echo "✅ HR Demo Data import completed!"
echo "💡 You can now test your HR Q&A system with realistic data"
