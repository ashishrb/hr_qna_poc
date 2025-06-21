# src/core/config.py - Simplified version
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # MongoDB Configuration
        self.mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "hr_qna_poc")
        
        # Azure AI Search Configuration
        self.azure_search_service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME")
        self.azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        
        # Azure OpenAI Configuration
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-llm")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        
        # Application Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.embedding_cache_ttl = int(os.getenv("EMBEDDING_CACHE_TTL", "3600"))

# Global settings instance
settings = Settings()

# Validation function
def validate_config() -> bool:
    """Validate that all required configuration is present."""
    try:
        required_fields = [
            settings.mongodb_connection_string,
            settings.azure_openai_endpoint,
            settings.azure_openai_api_key,
        ]
        
        if all(field for field in required_fields):
            print("✅ Configuration validation passed")
            return True
        else:
            print("❌ Missing required configuration")
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration...")
    print(f"MongoDB Database: {settings.mongodb_database}")
    print(f"Azure OpenAI Endpoint: {settings.azure_openai_endpoint}")
    print(f"Environment: {settings.environment}")
    validate_config()# src/core/config.py - Simplified version
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # MongoDB Configuration
        self.mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "hr_qna_poc")
        
        # Azure AI Search Configuration
        self.azure_search_service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME")
        self.azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        
        # Azure OpenAI Configuration
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        self.azure_openai_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-llm")
        self.azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        
        # Application Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.embedding_cache_ttl = int(os.getenv("EMBEDDING_CACHE_TTL", "3600"))

# Global settings instance
settings = Settings()

# Validation function
def validate_config() -> bool:
    """Validate that all required configuration is present."""
    try:
        required_fields = [
            settings.mongodb_connection_string,
            settings.azure_openai_endpoint,
            settings.azure_openai_api_key,
        ]
        
        if all(field for field in required_fields):
            print("✅ Configuration validation passed")
            return True
        else:
            print("❌ Missing required configuration")
            return False
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    # Test configuration loading
    print("Testing configuration...")
    print(f"MongoDB Database: {settings.mongodb_database}")
    print(f"Azure OpenAI Endpoint: {settings.azure_openai_endpoint}")
    print(f"Environment: {settings.environment}")
    validate_config()