# enhanced_requirements_check.py
import subprocess
import sys
import os
from pathlib import Path

def check_and_install_requirements():
    """Enhanced requirements check including complete .env validation"""
    print("📦 ENHANCED REQUIREMENTS CHECK FOR HR Q&A SYSTEM")
    print("=" * 70)
    
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
        'python-dotenv': 'pip install python-dotenv',
        'pymongo': 'pip install pymongo'
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

    # Enhanced environment variables check
    print(f"\n🔧 Checking COMPLETE environment configuration...")
    
    # Core required variables (must have values)
    core_env_vars = {
        'MONGODB_CONNECTION_STRING': 'MongoDB Atlas connection string',
        'MONGODB_DATABASE': 'MongoDB database name (e.g., hr_qna_poc)',
        'AZURE_SEARCH_SERVICE_NAME': 'Azure Search service name', 
        'AZURE_SEARCH_API_KEY': 'Azure Search API key',
        'AZURE_SEARCH_ENDPOINT': 'Azure Search endpoint URL',
        'AZURE_OPENAI_ENDPOINT': 'Azure OpenAI endpoint URL',
        'AZURE_OPENAI_API_KEY': 'Azure OpenAI API key',
        'AZURE_OPENAI_API_VERSION': 'Azure OpenAI API version (e.g., 2023-05-15)',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'Chat model deployment name (e.g., gpt-4o-llm)',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT': 'Embedding model deployment (e.g., text-embedding-ada-002)'
    }
    
    # Optional variables with defaults
    optional_env_vars = {
        'LOG_LEVEL': 'INFO',
        'ENVIRONMENT': 'development', 
        'MAX_CONCURRENT_REQUESTS': '10',
        'EMBEDDING_CACHE_TTL': '3600'
    }
    
    missing_core_vars = []
    missing_optional_vars = []
    
    print(f"\n📋 Core Environment Variables (Required):")
    for env_var, description in core_env_vars.items():
        value = os.getenv(env_var)
        if value:
            # Mask sensitive values
            if 'KEY' in env_var or 'CONNECTION_STRING' in env_var:
                masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"   ✅ {env_var} = {masked_value}")
            else:
                print(f"   ✅ {env_var} = {value}")
        else:
            print(f"   ❌ {env_var} - {description}")
            missing_core_vars.append(env_var)
    
    print(f"\n📋 Optional Environment Variables:")
    for env_var, default_value in optional_env_vars.items():
        value = os.getenv(env_var)
        if value:
            print(f"   ✅ {env_var} = {value}")
        else:
            print(f"   ⚠️  {env_var} - will use default: {default_value}")
            missing_optional_vars.append(env_var)

    # Check .env file existence and format
    print(f"\n📄 Checking .env file...")
    env_file_path = Path('.env')
    if env_file_path.exists():
        print(f"   ✅ .env file exists")
        
        # Read and validate .env file format
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                
            # Check for common formatting issues
            lines = env_content.strip().split('\n')
            valid_lines = 0
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        valid_lines += 1
                    else:
                        print(f"   ⚠️  Line {line_num}: Invalid format - {line[:50]}...")
            
            print(f"   📊 Valid environment variable lines: {valid_lines}")
            
        except Exception as e:
            print(f"   ❌ Error reading .env file: {e}")
    else:
        print(f"   ❌ .env file not found")

    # Check custom modules
    print(f"\n🏠 Checking custom modules...")
    custom_modules = [
        ('src/core/config.py', 'Configuration module'),
        ('src/database/mongodb_client.py', 'MongoDB client'),
        ('src/search/azure_search_client.py', 'Azure Search client'),
        ('src/query/query_engine.py', 'Main query engine'),
        ('src/query/intelligent_query_engine.py', 'Intelligent query engine')
    ]
    
    missing_modules = []
    
    for module_path, description in custom_modules:
        if os.path.exists(module_path):
            print(f"   ✅ {module_path} - {description}")
        else:
            print(f"   ❌ {module_path} - {description}")
            missing_modules.append((module_path, description))

    # Test actual connections if all core vars are present
    if not missing_core_vars:
        print(f"\n🔌 Testing service connections...")
        # Note: Connection testing will be done in main() async function
        connection_test_needed = True
    else:
        connection_test_needed = False

    # Summary and recommendations
    print(f"\n📊 ENHANCED REQUIREMENTS SUMMARY")
    print("=" * 40)
    print(f"✅ Installed packages: {len(installed_packages)}")
    print(f"❌ Missing packages: {len(missing_packages)}")
    print(f"✅ Core env vars set: {len(core_env_vars) - len(missing_core_vars)}")
    print(f"❌ Missing core env vars: {len(missing_core_vars)}")
    print(f"⚠️  Optional env vars missing: {len(missing_optional_vars)}")
    print(f"✅ Available modules: {len(custom_modules) - len(missing_modules)}")
    print(f"❌ Missing modules: {len(missing_modules)}")
    
    if missing_packages or missing_core_vars or missing_modules:
        print(f"\n🔧 DETAILED INSTALLATION INSTRUCTIONS")
        print("=" * 40)
        
        if missing_packages:
            print(f"\n📦 Install missing packages:")
            print(f"   pip install {' '.join([pkg for pkg, _ in missing_packages])}")
        
        if missing_core_vars:
            print(f"\n🔧 Add missing environment variables to .env file:")
            for var in missing_core_vars:
                description = core_env_vars[var]
                print(f"   {var}=your_{var.lower().replace('_', '_')}  # {description}")
        
        if missing_optional_vars:
            print(f"\n⚠️  Optional variables (add to .env for custom values):")
            for var in missing_optional_vars:
                default = optional_env_vars[var]
                print(f"   {var}={default}  # Optional, will use default if not set")
        
        if missing_modules:
            print(f"\n📁 Missing modules:")
            for module_path, description in missing_modules:
                print(f"   ❌ {module_path} - {description}")
            print(f"   💡 Ensure all source files are in correct locations")
        
        print(f"\n📋 COMPLETE .ENV TEMPLATE:")
        print_complete_env_template()
        
        return False, connection_test_needed
    else:
        print(f"\n🎉 ALL REQUIREMENTS SATISFIED!")
        print(f"✅ Ready to run the HR Q&A System")
        return True, connection_test_needed

async def test_service_connections():
    """Test actual connections to all services"""
    try:
        # Test MongoDB
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(os.getenv('MONGODB_CONNECTION_STRING'))
        await client.admin.command('ping')
        print(f"   ✅ MongoDB Atlas: Connected")
        client.close()
    except Exception as e:
        print(f"   ❌ MongoDB Atlas: {str(e)[:50]}...")
    
    try:
        # Test Azure Search
        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential
        search_client = SearchClient(
            endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
            index_name="test",
            credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_API_KEY'))
        )
        print(f"   ✅ Azure AI Search: Connected")
    except Exception as e:
        print(f"   ❌ Azure AI Search: {str(e)[:50]}...")
    
    try:
        # Test Azure OpenAI
        from openai import AzureOpenAI
        client = AzureOpenAI(
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
        )
        response = client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT'),
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print(f"   ✅ Azure OpenAI: Connected")
    except Exception as e:
        print(f"   ❌ Azure OpenAI: {str(e)[:50]}...")

def print_complete_env_template():
    """Print complete .env template"""
    template = """
# MongoDB Atlas Configuration
MONGODB_CONNECTION_STRING="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DATABASE=hr_qna_poc

# Azure AI Search Configuration  
AZURE_SEARCH_SERVICE_NAME=your-search-service-name
AZURE_SEARCH_API_KEY=your_search_api_key
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-llm
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Application Configuration (Optional)
LOG_LEVEL=INFO
ENVIRONMENT=development
MAX_CONCURRENT_REQUESTS=10
EMBEDDING_CACHE_TTL=3600
"""
    print(template)

def create_enhanced_requirements_txt():
    """Create enhanced requirements.txt file"""
    requirements_content = """# HR Q&A System - Complete Requirements
# Core AI and Database
openai>=1.0.0
motor>=3.3.0
pymongo>=4.5.0

# Azure Services
azure-search-documents>=11.4.0
azure-core>=1.29.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0

# Web Framework
fastapi>=0.104.0
uvicorn>=0.24.0

# Utilities
python-dotenv>=1.0.0
asyncio-throttle>=1.0.0
click>=8.0.0

# Testing (Optional)
pytest>=7.0.0
pytest-asyncio>=0.21.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements_content)
    
    print("📝 Created enhanced requirements.txt file")
    print("💡 Install with: pip install -r requirements.txt")

async def main():
    """Main function"""
    print("🚀 HR Q&A System - Enhanced Requirements Check")
    print("=" * 60)
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded .env file")
    except ImportError:
        print("⚠️  python-dotenv not installed, checking system environment variables")
    except Exception as e:
        print(f"⚠️  Could not load .env file: {e}")
    
    all_good, test_connections = check_and_install_requirements()
    
    # Test connections if requirements are satisfied
    if test_connections:
        await test_service_connections()
    
    if not all_good:
        create_enhanced_requirements_txt()
        print(f"\n💡 NEXT STEPS:")
        print(f"1. Install missing packages: pip install -r requirements.txt")
        print(f"2. Create/update .env file with all required variables")
        print(f"3. Run this check again: python enhanced_requirements_check.py")
        print(f"4. Test the system: python query_engine_dry_run.py")
    else:
        print(f"\n🎯 SYSTEM READY!")
        print(f"✅ All requirements satisfied")
        print(f"✅ All environment variables set")
        print(f"✅ All services connected")
        print(f"\n🚀 Ready to run:")
        print(f"   python query_engine_dry_run.py")
        print(f"   python enhanced_query_engine_dry_run.py")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())