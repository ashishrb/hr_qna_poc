# check_duplicate_fields.py
# Quick script to help identify duplicate fields in your indexer

def check_for_duplicates_in_fields():
    """Helper to identify which fields might be duplicated"""
    
    # Fields that were likely in your original index
    original_fields = [
        "id", "employee_id", "full_name", "email", "department", "role", 
        "location", "certifications", "current_project", "improvement_areas",
        "manager_feedback", "total_experience_years", "performance_rating", 
        "engagement_score", "combined_text", "content_vector", "created_at", "updated_at"
    ]
    
    # Fields I suggested adding
    new_fields = [
        "work_mode", "employment_type", "grade_band", "performance_rating",
        "kpis_met_pct", "awards", "improvement_areas", "attrition_risk_score",
        "exit_intent_flag", "retention_plan", "multiple_project_allocations",
        "peer_review_score", "days_on_bench", "allocation_percentage",
        "monthly_attendance_pct", "leave_days_taken", "leave_balance",
        "leave_pattern", "courses_completed", "internal_trainings",
        "learning_hours_ytd", "years_in_current_company", "years_in_current_skillset",
        "known_skills_count", "previous_companies_resigned", "age", "gender",
        "marital_status", "current_salary", "total_ctc", "currency"
    ]
    
    # Find duplicates
    duplicates = set(original_fields) & set(new_fields)
    
    print("🔍 DUPLICATE FIELDS FOUND:")
    for field in sorted(duplicates):
        print(f"   ❌ {field} (appears in both lists)")
    
    print(f"\n✅ ONLY ADD THESE NEW FIELDS:")
    only_new = set(new_fields) - set(original_fields)
    for field in sorted(only_new):
        print(f"   ✅ {field}")
    
    return duplicates, only_new

if __name__ == "__main__":
    duplicates, only_new = check_for_duplicates_in_fields()
    
    print(f"\n🔧 TO FIX:")
    print("1. Remove duplicate field definitions from your fields list")
    print("2. Only add the fields marked with ✅ above")
    print("3. Keep your existing definitions for fields marked with ❌")