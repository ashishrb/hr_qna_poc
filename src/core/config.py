# src/core/config.py - FIXED VERSION
import os
from pathlib import Path

def load_env_file():
    """Load .env file with multiple path attempts"""
    
    # Define possible .env file locations
    possible_paths = [
        # Current directory
        ".env",
        # Parent directory (if running from src/)
        "../.env",
        # Two levels up (if running from src/core/)
        "../../.env",
        # Root of project (absolute path approach)
        Path(__file__).parent.parent.parent / ".env",
        # Current working directory
        Path.cwd() / ".env"
    ]
    
    print("🔍 Searching for .env file...")
    
    for env_path in possible_paths:
        env_path = Path(env_path).resolve()
        print(f"   Checking: {env_path}")
        
        if env_path.exists():
            print(f"✅ Found .env file at: {env_path}")
            try:
                with open(env_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            try:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip('"').strip("'")
                                os.environ[key] = value
                                print(f"   ✅ Loaded: {key}")
                            except ValueError:
                                print(f"   ⚠️ Skipped invalid line {line_num}: {line}")
                
                print(f"✅ Successfully loaded .env from: {env_path}")
                return True
                
            except Exception as e:
                print(f"❌ Error reading .env file: {e}")
                continue
    
    print("❌ .env file not found in any expected location")
    print("📍 Current working directory:", Path.cwd())
    print("📍 Script location:", Path(__file__).parent)
    
    # List files in current directory for debugging
    print("\n📂 Files in current directory:")
    try:
        for item in Path.cwd().iterdir():
            if item.name.startswith('.env'):
                print(f"   Found: {item.name}")
    except:
        pass
    
    return False

# Load environment variables
env_loaded = load_env_file()

class Settings:
    def __init__(self):
        # Check if required environment variables are loaded
        required_vars = [
            "MONGODB_CONNECTION_STRING",
            "AZURE_SEARCH_ENDPOINT", 
            "AZURE_SEARCH_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            print("💡 Make sure your .env file contains these variables")
        
        # Load settings with defaults
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")

        self.mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "hr_qna_poc")
        self.azure_search_service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME")
        self.azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        
        # Print loaded configuration (without sensitive data)
        print("\n⚙️ Configuration Status:")
        print(f"   MongoDB Database: {self.mongodb_database}")
        print(f"   MongoDB Connection: {'✅ Set' if self.mongodb_connection_string else '❌ Missing'}")
        print(f"   Azure Search Endpoint: {'✅ Set' if self.azure_search_endpoint else '❌ Missing'}")
        print(f"   Azure Search API Key: {'✅ Set' if self.azure_search_api_key else '❌ Missing'}")
        print(f"   Azure OpenAI Endpoint: {'✅ Set' if self.azure_openai_endpoint else '❌ Missing'}")
        print(f"   Azure OpenAI API Key: {'✅ Set' if self.azure_openai_api_key else '❌ Missing'}")

settings = Settings()

if __name__ == "__main__":
    print("✅ Configuration loaded successfully")
    print(f"MongoDB Database: {settings.mongodb_database}")
    
    # Test if we can access the configuration
    if settings.mongodb_connection_string:
        print("🎉 All required settings appear to be loaded!")
    else:
        print("❌ Some settings are missing. Check your .env file.")