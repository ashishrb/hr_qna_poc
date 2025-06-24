# debug_init.py - Debug the initialization issue

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_config_loading():
    """Test if config loads the OpenAI settings properly"""
    print("🔍 Testing Configuration Loading")
    print("=" * 40)
    
    try:
        from core.config import settings
        
        print("✅ Config imported successfully")
        
        # Check all OpenAI related settings
        openai_settings = {
            "azure_openai_endpoint": getattr(settings, "azure_openai_endpoint", None),
            "azure_openai_api_key": getattr(settings, "azure_openai_api_key", None),
            "azure_openai_chat_deployment": getattr(settings, "azure_openai_chat_deployment", None),
        }
        
        for key, value in openai_settings.items():
            if value:
                print(f"   ✅ {key}: Set")
                if key == "azure_openai_chat_deployment":
                    print(f"      Value: {value}")
            else:
                print(f"   ❌ {key}: Missing")
        
        return openai_settings
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return None

def test_openai_import():
    """Test OpenAI import and basic client creation"""
    print("\n🔍 Testing OpenAI Import and Client Creation")
    print("=" * 50)
    
    try:
        from openai import AzureOpenAI
        print("✅ OpenAI imported successfully")
        
        from core.config import settings
        
        # Try to create client
        client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version="2023-05-15",
            azure_endpoint=settings.azure_openai_endpoint
        )
        print("✅ OpenAI client created successfully")
        
        # Get model name
        model_name = getattr(settings, 'azure_openai_chat_deployment', 'gpt-4o-llm')
        print(f"✅ Model name: {model_name}")
        
        # Test simple call
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
            temperature=0
        )
        print("✅ Test API call successful")
        print(f"   Response: {response.choices[0].message.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

def create_fixed_init_method():
    """Create a fixed __init__ method with better error handling"""
    print("\n🔧 Creating Fixed Initialization Method")
    print("=" * 45)
    
    fixed_init = '''
def __init__(self):
    """Initialize the comprehensive query engine with better error handling"""
    print("🚀 Initializing Robust 360° HR Query Engine...")
    
    # Initialize OpenAI client with detailed error handling
    self.openai_client = None
    self.model_name = None
    self.ai_available = False
    
    try:
        # Import and test config
        from src.core.config import settings
        
        # Validate required settings
        required_settings = ['azure_openai_api_key', 'azure_openai_endpoint']
        missing_settings = []
        
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"❌ Missing OpenAI settings: {missing_settings}")
            print("🔄 Will use fallback mode without AI")
        else:
            # Try to initialize OpenAI client
            from openai import AzureOpenAI
            
            self.openai_client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version="2023-05-15",
                azure_endpoint=settings.azure_openai_endpoint
            )
            
            # Get model name
            self.model_name = getattr(settings, 'azure_openai_chat_deployment', 'gpt-4o-llm')
            print(f"✅ Model name set to: {self.model_name}")
            
            # Test the connection
            test_response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                temperature=0
            )
            
            self.ai_available = True
            print(f"✅ Azure OpenAI client initialized successfully with model: {self.model_name}")
            print("✅ OpenAI connection tested successfully")
            
    except Exception as e:
        print(f"❌ OpenAI initialization failed: {e}")
        print(f"   Error details: {type(e).__name__}: {str(e)}")
        print("🔄 Continuing in fallback mode without AI")
        self.ai_available = False
    
    # Initialize other components regardless of OpenAI status
    self.departments = ["Sales", "IT", "Operations", "HR", "Finance", "Legal", "Engineering", "Marketing", "Support"]
    self.roles = ["Developer", "Manager", "Analyst", "Director", "Lead", "Engineer", "Consultant", "Specialist"]
    self.skills = ["PMP", "GCP", "AWS", "Azure", "Python", "Java", "JavaScript", "SQL", "Docker", "Kubernetes"]
    self.locations = ["Remote", "Onshore", "Offshore", "New York", "California", "India", "Chennai", "Hyderabad"]
    
    # Collection mappings
    self.collection_fields = {
        "personal_info": ["full_name", "age", "gender", "location", "email", "contact_number"],
        "employment": ["department", "role", "work_mode", "employment_type", "joining_date", "grade_band"],
        "learning": ["certifications", "courses_completed", "learning_hours_ytd", "internal_trainings"],
        "experience": ["total_experience_years", "years_in_current_company", "known_skills_count"],
        "performance": ["performance_rating", "awards", "kpis_met_pct", "improvement_areas"],
        "engagement": ["current_project", "engagement_score", "manager_feedback", "days_on_bench"],
        "compensation": ["current_salary", "bonus", "total_ctc", "currency"],
        "attendance": ["leave_balance", "leave_days_taken", "monthly_attendance_pct", "leave_pattern"],
        "attrition": ["attrition_risk_score", "exit_intent_flag", "retention_plan"]
    }
    
    status = "with AI features" if self.ai_available else "in fallback mode"
    print(f"✅ Robust 360° HR Query Engine ready {status}!")
    '''
    
    print("📝 Fixed __init__ method created")
    print("   - Better error handling")
    print("   - Graceful fallback mode")
    print("   - Detailed error messages")
    print("   - Continues working even if OpenAI fails")
    
    return fixed_init

def main():
    """Main debug function"""
    print("🔧 HR Engine Initialization Debug")
    print("=" * 45)
    
    # Test config loading
    config_result = test_config_loading()
    
    if not config_result:
        print("\n❌ Config loading failed - this is the root cause!")
        return
    
    # Test OpenAI
    openai_result = test_openai_import()
    
    if not openai_result:
        print("\n❌ OpenAI testing failed - this is why __init__ fails!")
    
    # Create fixed version
    fixed_init = create_fixed_init_method()
    
    print("\n" + "=" * 50)
    print("🎯 SOLUTION:")
    print("Replace your __init__ method with the fixed version above.")
    print("This will:")
    print("✅ Show exactly what's failing during initialization")
    print("✅ Continue working even if OpenAI fails")
    print("✅ Give you detailed error messages")

if __name__ == "__main__":
    main()