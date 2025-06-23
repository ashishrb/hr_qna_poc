# import_validator.py
import sys
import os

def validate_imports():
    """Validate all required imports for the enhanced intelligent query engine"""
    print("🔍 VALIDATING ALL IMPORTS")
    print("=" * 50)
    
    missing_libraries = []
    available_libraries = []
    
    # Standard library imports
    standard_libs = [
        "asyncio", "json", "sys", "os", "typing", "enum", "dataclasses"
    ]
    
    print("\n📚 Standard Library Imports:")
    for lib in standard_libs:
        try:
            __import__(lib)
            print(f"   ✅ {lib}")
            available_libraries.append(lib)
        except ImportError as e:
            print(f"   ❌ {lib} - {e}")
            missing_libraries.append(lib)
    
    # Third-party library imports
    third_party_libs = [
        ("openai", "AzureOpenAI"),
        ("motor.motor_asyncio", "AsyncIOMotorClient"),
        ("azure.search.documents", "SearchClient"),
        ("azure.core.credentials", "AzureKeyCredential"),
        ("pandas", None),
        ("numpy", None)
    ]
    
    print("\n🌐 Third-party Library Imports:")
    for lib_info in third_party_libs:
        if isinstance(lib_info, tuple):
            lib_name, class_name = lib_info
        else:
            lib_name, class_name = lib_info, None
            
        try:
            if class_name:
                module = __import__(lib_name, fromlist=[class_name])
                getattr(module, class_name)
                print(f"   ✅ {lib_name}.{class_name}")
            else:
                __import__(lib_name)
                print(f"   ✅ {lib_name}")
            available_libraries.append(lib_name)
        except ImportError as e:
            print(f"   ❌ {lib_name} - {e}")
            missing_libraries.append(lib_name)
        except AttributeError as e:
            print(f"   ❌ {lib_name}.{class_name} - {e}")
            missing_libraries.append(f"{lib_name}.{class_name}")
    
    # Custom module imports (check if files exist)
    custom_modules = [
        "src.core.config",
        "src.database.mongodb_client", 
        "src.search.azure_search_client",
        "src.query.query_engine"
    ]
    
    print("\n🏠 Custom Module Imports:")
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    for module in custom_modules:
        try:
            # Check if file exists
            module_path = module.replace('.', '/') + '.py'
            if os.path.exists(module_path):
                print(f"   📁 {module_path} - File exists")
                
                # Try to import
                __import__(module)
                print(f"   ✅ {module} - Import successful")
                available_libraries.append(module)
            else:
                print(f"   ❌ {module_path} - File not found")
                missing_libraries.append(module)
        except ImportError as e:
            print(f"   ⚠️  {module} - Import failed: {e}")
            missing_libraries.append(module)
        except Exception as e:
            print(f"   ❌ {module} - Error: {e}")
            missing_libraries.append(module)
    
    # Summary
    print(f"\n📊 IMPORT VALIDATION SUMMARY")
    print("=" * 30)
    print(f"✅ Available: {len(available_libraries)}")
    print(f"❌ Missing: {len(missing_libraries)}")
    
    if missing_libraries:
        print(f"\n❌ MISSING LIBRARIES/MODULES:")
        for lib in missing_libraries:
            print(f"   - {lib}")
        print(f"\n💡 RECOMMENDATIONS:")
        
        if any("openai" in lib for lib in missing_libraries):
            print("   📦 Install: pip install openai")
        if any("motor" in lib for lib in missing_libraries):
            print("   📦 Install: pip install motor")
        if any("azure" in lib for lib in missing_libraries):
            print("   📦 Install: pip install azure-search-documents azure-core")
        if any("pandas" in lib for lib in missing_libraries):
            print("   📦 Install: pip install pandas")
        if any("src." in lib for lib in missing_libraries):
            print("   📁 Check: Ensure all custom modules exist in correct paths")
    else:
        print(f"\n🎉 ALL IMPORTS VALIDATED SUCCESSFULLY!")
    
    return len(missing_libraries) == 0

if __name__ == "__main__":
    validate_imports()