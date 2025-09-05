#!/usr/bin/env python3
"""
Ollama Setup Script for HR Q&A System
Downloads and configures required Ollama models
"""

import subprocess
import sys
import time
import requests
import json
from typing import List, Dict, Any

class OllamaSetup:
    """Setup Ollama models for HR Q&A system"""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.required_models = [
            {
                "name": "llama3.2:3b",
                "description": "Lightweight language model for HR queries",
                "size": "~2GB"
            },
            {
                "name": "nomic-embed-text",
                "description": "Text embedding model for semantic search",
                "size": "~274MB"
            }
        ]
        
        self.alternative_models = [
            "llama3.2:1b",  # Even smaller alternative
            "gemma2:2b",    # Google's Gemma model
            "phi3:mini",    # Microsoft's Phi-3 model
        ]
    
    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed and running"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                print("✅ Ollama is installed and running")
                return True
            else:
                print(f"❌ Ollama server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            print("❌ Ollama is not running or not installed")
            print("💡 Please install Ollama from https://ollama.ai/")
            print("💡 Then run: ollama serve")
            return False
    
    def get_installed_models(self) -> List[str]:
        """Get list of installed models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except Exception as e:
            print(f"❌ Failed to get installed models: {e}")
            return []
    
    def install_model(self, model_name: str) -> bool:
        """Install a model using Ollama"""
        print(f"📥 Installing {model_name}...")
        print(f"   This may take several minutes depending on your internet connection...")
        
        try:
            # Start the pull process
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(f"   {output.strip()}")
            
            # Check if installation was successful
            if process.returncode == 0:
                print(f"✅ Successfully installed {model_name}")
                return True
            else:
                stderr = process.stderr.read()
                print(f"❌ Failed to install {model_name}: {stderr}")
                return False
                
        except FileNotFoundError:
            print("❌ Ollama command not found. Please install Ollama first.")
            return False
        except Exception as e:
            print(f"❌ Error installing {model_name}: {e}")
            return False
    
    def test_model(self, model_name: str) -> bool:
        """Test if a model is working correctly"""
        try:
            print(f"🧪 Testing {model_name}...")
            
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Hello, how are you?"}],
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'message' in result and 'content' in result['message']:
                    print(f"✅ {model_name} is working correctly")
                    print(f"   Response: {result['message']['content'][:100]}...")
                    return True
            
            print(f"❌ {model_name} test failed")
            return False
            
        except Exception as e:
            print(f"❌ Error testing {model_name}: {e}")
            return False
    
    def setup_models(self) -> bool:
        """Setup all required models"""
        print("🚀 Setting up Ollama models for HR Q&A System")
        print("=" * 60)
        
        # Check if Ollama is running
        if not self.check_ollama_installed():
            return False
        
        # Get currently installed models
        installed_models = self.get_installed_models()
        print(f"📋 Currently installed models: {installed_models}")
        
        success_count = 0
        
        # Install required models
        for model_info in self.required_models:
            model_name = model_info["name"]
            description = model_info["description"]
            size = model_info["size"]
            
            print(f"\n📦 Model: {model_name}")
            print(f"   Description: {description}")
            print(f"   Size: {size}")
            
            if model_name in installed_models:
                print(f"✅ {model_name} is already installed")
                if self.test_model(model_name):
                    success_count += 1
            else:
                if self.install_model(model_name):
                    if self.test_model(model_name):
                        success_count += 1
        
        # If no models were successfully installed, try alternatives
        if success_count == 0:
            print("\n⚠️ No required models could be installed. Trying alternatives...")
            for alt_model in self.alternative_models:
                print(f"\n🔄 Trying alternative: {alt_model}")
                if self.install_model(alt_model):
                    if self.test_model(alt_model):
                        print(f"✅ Alternative model {alt_model} is working")
                        success_count += 1
                        break
        
        print(f"\n📊 Setup Summary:")
        print(f"   Models successfully installed: {success_count}")
        
        if success_count > 0:
            print("🎉 Ollama setup completed successfully!")
            print("\n💡 Next steps:")
            print("   1. Start the HR Q&A API server: python src/api/main.py")
            print("   2. Open your browser to: http://localhost:8000")
            print("   3. Start asking questions about your employees!")
            return True
        else:
            print("❌ Ollama setup failed. Please check the errors above.")
            print("\n🔧 Troubleshooting:")
            print("   1. Make sure Ollama is installed: https://ollama.ai/")
            print("   2. Start Ollama server: ollama serve")
            print("   3. Check your internet connection")
            print("   4. Try installing models manually: ollama pull llama3.2:3b")
            return False
    
    def show_model_info(self):
        """Show information about available models"""
        print("📚 Available Ollama Models for HR Q&A System")
        print("=" * 50)
        
        print("\n🎯 Recommended Models:")
        for model in self.required_models:
            print(f"   • {model['name']}")
            print(f"     {model['description']}")
            print(f"     Size: {model['size']}")
            print()
        
        print("🔄 Alternative Models (if recommended ones fail):")
        for model in self.alternative_models:
            print(f"   • {model}")
        
        print("\n💡 Model Selection Guide:")
        print("   • llama3.2:3b - Best balance of performance and size")
        print("   • llama3.2:1b - Fastest, smallest model")
        print("   • gemma2:2b - Google's efficient model")
        print("   • phi3:mini - Microsoft's compact model")
        print("   • nomic-embed-text - Required for semantic search")

def main():
    """Main setup function"""
    setup = OllamaSetup()
    
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        setup.show_model_info()
        return
    
    success = setup.setup_models()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
