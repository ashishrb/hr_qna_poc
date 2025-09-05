# src/core/config.py - Ollama-based Configuration (No Azure Dependencies)
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
        # Check if required environment variables are loaded (Ollama-based)
        required_vars = [
            "MONGODB_CONNECTION_STRING",
            "MONGODB_DATABASE"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {missing_vars}")
            print("💡 Make sure your .env file contains these variables")
        
        # MongoDB Configuration
        self.mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "hr_qna_poc")
        
        # Ollama Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text:v1.5")
        
        # Application Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.embedding_cache_ttl = int(os.getenv("EMBEDDING_CACHE_TTL", "3600"))
        
        # Server Configuration
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "true").lower() == "true"
        
        # Security Configuration
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
        self.allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        
        # Performance Configuration
        self.max_workers = int(os.getenv("MAX_WORKERS", "4"))
        self.timeout = int(os.getenv("TIMEOUT", "30"))
        
        # Print loaded configuration (without sensitive data)
        print("\n⚙️ Configuration Status:")
        print(f"   MongoDB Database: {self.mongodb_database}")
        print(f"   MongoDB Connection: {'✅ Set' if self.mongodb_connection_string else '❌ Missing'}")
        print(f"   Ollama Base URL: {self.ollama_base_url}")
        print(f"   Ollama Embedding Model: {self.ollama_embedding_model}")
        print(f"   Environment: {self.environment}")
        print(f"   Debug Mode: {self.debug}")
        print(f"   Server: {self.host}:{self.port}")

settings = Settings()

if __name__ == "__main__":
    print("✅ Configuration loaded successfully")
    print(f"MongoDB Database: {settings.mongodb_database}")
    print(f"Ollama Base URL: {settings.ollama_base_url}")
    
    # Test if we can access the configuration
    if settings.mongodb_connection_string:
        print("🎉 All required settings appear to be loaded!")
    else:
        print("❌ Some settings are missing. Check your .env file.")