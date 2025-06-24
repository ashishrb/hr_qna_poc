# debug_env.py - Run this to debug .env file issues
import os
from pathlib import Path

def debug_env_file():
    """Debug .env file location and content issues"""
    print("🔍 Environment File Debug Tool")
    print("=" * 50)
    
    # 1. Show current working directory
    cwd = Path.cwd()
    print(f"📍 Current working directory: {cwd}")
    
    # 2. Show script location
    script_dir = Path(__file__).parent
    print(f"📍 Script directory: {script_dir}")
    
    # 3. List all .env files we can find
    print(f"\n📂 Searching for .env files:")
    
    search_locations = [
        cwd,
        script_dir,
        script_dir.parent,
        script_dir.parent.parent
    ]
    
    found_env_files = []
    
    for location in search_locations:
        try:
            env_file = location / ".env"
            if env_file.exists():
                found_env_files.append(env_file)
                print(f"   ✅ Found: {env_file}")
                
                # Check file size and permissions
                stat = env_file.stat()
                print(f"      📊 Size: {stat.st_size} bytes")
                print(f"      🔐 Readable: {os.access(env_file, os.R_OK)}")
        except Exception as e:
            print(f"   ❌ Error checking {location}: {e}")
    
    if not found_env_files:
        print("   ❌ No .env files found!")
        print("\n💡 Create .env file in project root with content like:")
        print("""
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=hr_qna_poc
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your_search_api_key
AZURE_SEARCH_SERVICE_NAME=your-search-service
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your_openai_api_key
        """)
        return False
    
    # 4. Check content of found .env files
    print(f"\n📝 Checking .env file contents:")
    
    for env_file in found_env_files:
        print(f"\n   📄 File: {env_file}")
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
                print(f"      📊 Total lines: {len(lines)}")
                
                valid_vars = 0
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        try:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            # Don't print actual values for security
                            print(f"      ✅ Line {line_num}: {key}={'*' * min(len(value), 10)}")
                            valid_vars += 1
                        except:
                            print(f"      ❌ Line {line_num}: Invalid format")
                    elif line.startswith('#'):
                        print(f"      💬 Line {line_num}: Comment")
                    elif not line:
                        print(f"      ⭕ Line {line_num}: Empty")
                    else:
                        print(f"      ⚠️ Line {line_num}: No '=' found")
                
                print(f"      📊 Valid variables: {valid_vars}")
                
        except Exception as e:
            print(f"      ❌ Error reading file: {e}")
    
    # 5. Test loading environment variables
    print(f"\n🧪 Testing environment variable loading:")
    
    # Try to load the first found .env file
    if found_env_files:
        env_file = found_env_files[0]
        print(f"   📂 Loading from: {env_file}")
        
        try:
            loaded_vars = {}
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        loaded_vars[key] = value
                        os.environ[key] = value
            
            print(f"   ✅ Loaded {len(loaded_vars)} variables")
            
            # Check required variables
            required_vars = [
                "MONGODB_CONNECTION_STRING",
                "AZURE_SEARCH_ENDPOINT", 
                "AZURE_SEARCH_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_API_KEY"
            ]
            
            print(f"\n   🔍 Checking required variables:")
            missing = []
            for var in required_vars:
                if var in loaded_vars and loaded_vars[var]:
                    print(f"      ✅ {var}: Set")
                else:
                    print(f"      ❌ {var}: Missing or empty")
                    missing.append(var)
            
            if missing:
                print(f"\n   ⚠️ Missing variables: {missing}")
                return False
            else:
                print(f"\n   🎉 All required variables found!")
                return True
                
        except Exception as e:
            print(f"   ❌ Error loading variables: {e}")
            return False
    
    return False

def fix_common_issues():
    """Suggest fixes for common .env issues"""
    print(f"\n🔧 Common .env Issues and Fixes:")
    print("=" * 40)
    
    print("1. 📍 Wrong Location:")
    print("   - Place .env file in project root (same level as src/ folder)")
    print("   - NOT inside src/ or any subfolder")
    
    print("\n2. 🔤 Wrong Format:")
    print("   - Use: KEY=value")
    print("   - NOT: KEY = value or KEY: value")
    print("   - No spaces around =")
    
    print("\n3. 🔗 Wrong Values:")
    print("   - Remove quotes around values")
    print("   - Use: KEY=my_value")
    print("   - NOT: KEY='my_value' or KEY=\"my_value\"")
    
    print("\n4. 📝 File Encoding:")
    print("   - Save as UTF-8 encoding")
    print("   - No BOM (Byte Order Mark)")
    
    print("\n5. 🔐 Permissions:")
    print("   - Make sure file is readable")
    print("   - Check file permissions if on Linux/Mac")

if __name__ == "__main__":
    success = debug_env_file()
    
    if not success:
        fix_common_issues()
        
    print(f"\n" + "=" * 50)
    if success:
        print("🎉 .env file looks good! You can now run your application.")
    else:
        print("❌ .env file issues found. Fix them and try again.")