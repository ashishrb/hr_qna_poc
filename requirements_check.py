# requirements_check.py
import subprocess
import sys
import os

def check_and_install_requirements():
    """Check for required packages and provide installation instructions"""
    print("📦 CHECKING REQUIREMENTS FOR INTELLIGENT QUERY ENGINE")
    print("=" * 60)
    
    # Required packages
    required_packages = {
        'openai': 'pip install openai',
        'motor': 'pip install motor',
        'azure-search-documents': 'pip install azure-search-documents',
        'azure-core': 'pip install azure-core',
        'pandas': 'pip install pandas',
        'numpy': 'pip install numpy',
        'fastapi': 'pip install fastapi',
        'uvicorn': 'pip install uvicorn',
        'python-dotenv': 'pip install python-dotenv'
    }
    
    missing_packages = []
    installed_packages = []
    
    print("\n🔍 Checking Python packages...")
    
    for package, install_cmd in required_packages.items():
        try:
            if package == 'azure-search-documents':
                import azure.search.documents
                test_import = True
            elif package == 'azure-core':
                import azure.core
                test_import = True
            else:
                __import__(package.replace('-', '_'))
                test_import = True
            
            print(f"   ✅ {package}")
            installed_packages.append(package)
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append((package, install_cmd))
    
    # Check custom modules
    print(f"\n🏠 Checking custom modules...")
    custom_modules = [
        ('src/core/config.py', 'Configuration module'),
        ('src/database/mongodb_client.py', 'MongoDB client'),
        ('src/search/azure_search_client.py', 'Azure Search client'),
        ('src/query/query_engine.py', 'Fallback query engine')
    ]
    
    missing_modules = []
    
    for module_path, description in custom_modules:
        if os.path.exists(module_path):
            print(f"   ✅ {module_path} - {description}")
        else:
            print(f"   ❌ {module_path} - {description}")
            missing_modules.append((module_path, description))
    
    # Check environment variables
    print(f"\n🔧 Checking environment configuration...")
    required_env_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'MONGODB_CONNECTION_STRING',
        'AZURE_SEARCH_API_KEY',
        'AZURE_SEARCH_ENDPOINT'
    ]
    
    missing_env_vars = []
    
    for env_var in required_env_vars:
        if os.getenv(env_var):
            print(f"   ✅ {env_var}")
        else:
            print(f"   ❌ {env_var}")
            missing_env_vars.append(env_var)
    
    # Summary and recommendations
    print(f"\n📊 REQUIREMENTS SUMMARY")
    print("=" * 30)
    print(f"✅ Installed packages: {len(installed_packages)}")
    print(f"❌ Missing packages: {len(missing_packages)}")
    print(f"✅ Available modules: {len(custom_modules) - len(missing_modules)}")
    print(f"❌ Missing modules: {len(missing_modules)}")
    print(f"✅ Set env vars: {len(required_env_vars) - len(missing_env_vars)}")
    print(f"❌ Missing env vars: {len(missing_env_vars)}")
    
    if missing_packages or missing_modules or missing_env_vars:
        print(f"\n🔧 INSTALLATION INSTRUCTIONS")
        print("=" * 30)
        
        if missing_packages:
            print(f"\n📦 Install missing packages:")
            for package, install_cmd in missing_packages:
                print(f"   {install_cmd}")
            
            print(f"\n💡 Or install all at once:")
            print(f"   pip install openai motor azure-search-documents azure-core pandas numpy fastapi uvicorn python-dotenv")
        
        if missing_modules:
            print(f"\n📁 Missing modules:")
            for module_path, description in missing_modules:
                print(f"   ❌ {module_path} - {description}")
            print(f"   💡 Ensure all source files are in correct locations")
        
        if missing_env_vars:
            print(f"\n🔧 Missing environment variables:")
            for env_var in missing_env_vars:
                print(f"   ❌ {env_var}")
            print(f"   💡 Create .env file with all required variables")
            print(f"   💡 Example .env file:")
            print(f"""
# .env
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=https://your-openai-endpoint.openai.azure.com/
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/
AZURE_SEARCH_API_KEY=your_search_key
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
""")
        
        return False
    else:
        print(f"\n🎉 ALL REQUIREMENTS SATISFIED!")
        print(f"✅ Ready to run the Intelligent Query Engine")
        return True

def create_requirements_txt():
    """Create requirements.txt file"""
    requirements_content = """# HR Q&A System Requirements
openai>=1.0.0
motor>=3.3.0
azure-search-documents>=11.4.0
azure-core>=1.29.0
pandas>=2.0.0
numpy>=1.24.0
fastapi>=0.104.0
uvicorn>=0.24.0
python-dotenv>=1.0.0
pymongo>=4.5.0
asyncio-throttle>=1.0.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_content)
    
    print("📝 Created requirements.txt file")
    print("💡 Install with: pip install -r requirements.txt")

if __name__ == "__main__":
    print("🚀 HR Q&A System Requirements Check")
    print("=" * 50)
    
    all_good = check_and_install_requirements()
    
    if not all_good:
        create_requirements_txt()
        print(f"\n💡 NEXT STEPS:")
        print(f"1. Install missing packages: pip install -r requirements.txt")
        print(f"2. Create .env file with all environment variables")
        print(f"3. Run: python import_validator.py")
        print(f"4. Run: python enhanced_query_engine_dry_run.py")
    else:
        print(f"\n🎯 READY TO TEST!")
        print(f"Run: python enhanced_query_engine_dry_run.py")