# src/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.mongodb_database = os.getenv("MONGODB_DATABASE", "hr_qna_poc")
        self.azure_search_service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME")
        self.azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")

settings = Settings()

if __name__ == "__main__":
    print("✅ Configuration loaded successfully")
    print(f"MongoDB Database: {settings.mongodb_database}")