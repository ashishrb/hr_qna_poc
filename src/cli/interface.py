# src/cli/interface.py
import asyncio
import click
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.processing.etl_pipeline import etl_pipeline
from src.query.updated_query_engine import UpdatedHRQueryEngine
from src.database.collections import employee_collections
from src.search.azure_search_client import azure_search_client
from src.core.config import settings

# Initialize components
query_engine = UpdatedHRQueryEngine()

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """HR Q&A System Command Line Interface
    
    A powerful CLI for managing the HR Q&A system, running ETL pipelines,
    testing queries, and analyzing employee data.
    """
    pass

# =============================================================================
# ETL COMMANDS
# =============================================================================

@cli.group()
def etl():
    """ETL pipeline management commands"""
    pass

@etl.command()
@click.argument('excel_file', type=click.Path(exists=True))
@click.option('--skip-indexing', is_flag=True, help='Skip search index creation')
@click.option('--skip-embeddings', is_flag=True, help='Skip embeddings generation')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def run(excel_file, skip_indexing, skip_embeddings, verbose):
    """Run the complete ETL pipeline from Excel to searchable index
    
    EXCEL_FILE: Path to the Excel file containing HR data
    """
    click.echo("🚀 Starting HR Data ETL Pipeline")
    click.echo("=" * 50)
    
    if verbose:
        click.echo(f"📁 Input file: {excel_file}")
        click.echo(f"🔍 Skip indexing: {skip_indexing}")
        click.echo(f"🧠 Skip embeddings: {skip_embeddings}")
    
    try:
        # Run ETL pipeline
        result = asyncio.run(etl_pipeline.run_full_pipeline(
            excel_file_path=excel_file,
            skip_indexing=skip_indexing,
            skip_embeddings=skip_embeddings
        ))
        
        if result["status"] == "success":
            click.echo("✅ ETL Pipeline completed successfully!")
            if verbose:
                click.echo("\n📊 Pipeline Statistics:")
                for key, value in result["stats"].items():
                    if key not in ["errors", "start_time", "end_time"]:
                        click.echo(f"   {key}: {value}")
        else:
            click.echo("❌ ETL Pipeline failed!")
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        click.echo(f"❌ Pipeline execution failed: {e}")
        sys.exit(1)

@etl.command()
def status():
    """Get ETL pipeline status and statistics"""
    try:
        click.echo("📊 ETL Pipeline Status")
        click.echo("=" * 30)
        
        stats = etl_pipeline.stats
        if stats["start_time"]:
            click.echo(f"🕐 Last run: {stats['start_time']}")
            click.echo(f"📊 Records processed: {stats['total_records_processed']}")
            click.echo(f"✅ Successful: {stats['successful_records']}")
            click.echo(f"❌ Failed: {stats['failed_records']}")
            click.echo(f"🗂️  Collections: {stats['collections_created']}")
        else:
            click.echo("⏸️  No pipeline runs recorded")
            
    except Exception as e:
        click.echo(f"❌ Failed to get status: {e}")

# =============================================================================
# QUERY COMMANDS
# =============================================================================

@cli.group()
def query():
    """Query processing and testing commands"""
    pass

@query.command()
@click.argument('query_text')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with metadata')
def ask(query_text, json_output, verbose):
    """Ask a question to the HR Q&A system
    
    QUERY_TEXT: The question to ask (use quotes for multi-word queries)
    """
    try:
        if not json_output:
            click.echo(f"🤖 Processing query: '{query_text}'")
            click.echo("-" * 50)
        
        # Process query
        result = asyncio.run(query_engine.process_query(query_text))
        
        if json_output:
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            # Display human-readable output
            click.echo(f"🎯 Intent: {result['intent']}")
            click.echo(f"📋 Entities: {result['entities']}")
            click.echo(f"📊 Results found: {len(result['search_results'])}")
            
            if verbose and result['search_results']:
                click.echo("\n👥 Employees found:")
                for emp in result['search_results'][:3]:
                    click.echo(f"   - {emp['full_name']} ({emp['department']}) - {emp['role']}")
            
            click.echo(f"\n💬 Response:")
            click.echo(result['response'])
            
    except Exception as e:
        click.echo(f"❌ Query failed: {e}")
        sys.exit(1)

@query.command()
def interactive():
    """Start interactive query session"""
    click.echo("🎮 Interactive HR Q&A Session")
    click.echo("Type 'quit', 'exit', or 'q' to exit")
    click.echo("=" * 50)
    
    try:
        while True:
            query_text = click.prompt("\n💬 Enter your query", type=str)
            
            if query_text.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query_text.strip():
                continue
            
            try:
                result = asyncio.run(query_engine.process_query(query_text))
                
                click.echo(f"🤖 {result['response']}")
                
                if result['search_results']:
                    click.echo(f"📊 Found {len(result['search_results'])} employees")
                    
            except Exception as e:
                click.echo(f"❌ Error: {e}")
        
        click.echo("\n👋 Goodbye!")
        
    except KeyboardInterrupt:
        click.echo("\n👋 Session ended by user")

@query.command()
def test():
    """Run predefined test queries"""
    test_queries = [
        "Who are the developers in our company?",
        "Find employees with PMP certification",
        "How many people work in the Operations department?",
        "Show me directors",
        "Tell me about employees with GCP certification",
        "Who works in the IT department?"
    ]
    
    click.echo("🧪 Running Test Queries")
    click.echo("=" * 30)
    
    success_count = 0
    
    for i, query in enumerate(test_queries, 1):
        click.echo(f"\n{i}. {query}")
        
        try:
            result = asyncio.run(query_engine.process_query(query))
            
            if result['status'] == 'success':
                click.echo(f"   ✅ Success - Found {len(result['search_results'])} results")
                success_count += 1
            else:
                click.echo(f"   ❌ Failed - {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            click.echo(f"   ❌ Error - {e}")
    
    click.echo(f"\n📊 Test Results: {success_count}/{len(test_queries)} passed")

# =============================================================================
# DATA COMMANDS
# =============================================================================

@cli.group()
def data():
    """Data exploration and management commands"""
    pass

@data.command()
@click.option('--limit', '-l', default=10, help='Number of employees to show')
def employees(limit):
    """List employees in the system"""
    try:
        click.echo("👥 Employee List")
        click.echo("=" * 20)
        
        async def get_employees():
            employee_ids = await employee_collections.get_all_employee_ids()
            
            if not employee_ids:
                click.echo("No employees found in the system")
                return
            
            click.echo(f"Found {len(employee_ids)} total employees")
            click.echo(f"Showing first {min(limit, len(employee_ids))}:")
            click.echo("")
            
            for i, emp_id in enumerate(employee_ids[:limit], 1):
                profile = await employee_collections.get_complete_employee_profile(emp_id)
                name = profile.get('full_name', 'Unknown')
                dept = profile.get('department', 'Unknown')
                role = profile.get('role', 'Unknown')
                
                click.echo(f"{i:2d}. {name} - {dept} - {role}")
        
        asyncio.run(get_employees())
        
    except Exception as e:
        click.echo(f"❌ Failed to list employees: {e}")

@data.command()
def stats():
    """Show data statistics"""
    try:
        click.echo("📊 Data Statistics")
        click.echo("=" * 20)
        
        async def get_stats():
            # Get employee count
            employee_ids = await employee_collections.get_all_employee_ids()
            click.echo(f"👥 Total employees: {len(employee_ids)}")
            
            # Get department stats
            dept_stats = await employee_collections.get_department_statistics()
            click.echo(f"🏢 Departments: {len(dept_stats)}")
            for dept, count in list(dept_stats.items())[:5]:
                click.echo(f"   - {dept}: {count}")
            
            # Get role stats
            role_stats = await employee_collections.get_role_statistics()
            click.echo(f"💼 Roles: {len(role_stats)}")
            for role, count in list(role_stats.items())[:5]:
                click.echo(f"   - {role}: {count}")
            
            # Get search index stats
            try:
                indexed_count = azure_search_client.get_document_count()
                click.echo(f"🔍 Indexed documents: {indexed_count}")
            except:
                click.echo(f"🔍 Search index: Not available")
        
        asyncio.run(get_stats())
        
    except Exception as e:
        click.echo(f"❌ Failed to get statistics: {e}")

@data.command()
@click.argument('employee_id')
@click.option('--json-output', '-j', is_flag=True, help='Output as JSON')
def profile(employee_id, json_output):
    """Get complete employee profile
    
    EMPLOYEE_ID: The employee ID to lookup
    """
    try:
        async def get_profile():
            profile_data = await employee_collections.get_complete_employee_profile(employee_id)
            
            if not profile_data or not profile_data.get('full_name'):
                click.echo(f"❌ Employee {employee_id} not found")
                return
            
            if json_output:
                click.echo(json.dumps(profile_data, indent=2, default=str))
            else:
                click.echo(f"👤 Employee Profile: {employee_id}")
                click.echo("=" * 40)
                click.echo(f"Name: {profile_data.get('full_name', 'N/A')}")
                click.echo(f"Email: {profile_data.get('email', 'N/A')}")
                click.echo(f"Department: {profile_data.get('department', 'N/A')}")
                click.echo(f"Role: {profile_data.get('role', 'N/A')}")
                click.echo(f"Location: {profile_data.get('location', 'N/A')}")
                click.echo(f"Certifications: {profile_data.get('certifications', 'N/A')}")
                click.echo(f"Experience: {profile_data.get('total_experience_years', 'N/A')} years")
        
        asyncio.run(get_profile())
        
    except Exception as e:
        click.echo(f"❌ Failed to get profile: {e}")

# =============================================================================
# SEARCH COMMANDS
# =============================================================================

@cli.group()
def search():
    """Search system management commands"""
    pass

@search.command()
def status():
    """Check search system status"""
    try:
        click.echo("🔍 Search System Status")
        click.echo("=" * 25)
        
        # Check search index
        try:
            count = azure_search_client.get_document_count()
            click.echo(f"✅ Search index: {count} documents")
        except Exception as e:
            click.echo(f"❌ Search index: Error - {e}")
        
        # Check facets
        try:
            facets = azure_search_client.get_facets(["department", "role"])
            dept_count = len(facets.get("department", []))
            role_count = len(facets.get("role", []))
            click.echo(f"📊 Facets: {dept_count} departments, {role_count} roles")
        except Exception as e:
            click.echo(f"❌ Facets: Error - {e}")
            
    except Exception as e:
        click.echo(f"❌ Search status check failed: {e}")

@search.command()
@click.argument('query_text')
@click.option('--limit', '-l', default=5, help='Number of results to show')
def test_search(query_text, limit):
    """Test search functionality directly
    
    QUERY_TEXT: The search query to test
    """
    try:
        click.echo(f"🔍 Testing search: '{query_text}'")
        click.echo("-" * 40)
        
        # Test direct search
        results = azure_search_client.search(query_text, top_k=limit)
        
        if results:
            click.echo(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                name = result.get('full_name', 'Unknown')
                dept = result.get('department', 'Unknown')
                role = result.get('role', 'Unknown')
                score = result.get('@search.score', 0)
                click.echo(f"   {i}. {name} ({dept}) - {role} [Score: {score:.3f}]")
        else:
            click.echo("❌ No results found")
            
    except Exception as e:
        click.echo(f"❌ Search test failed: {e}")

@search.command()
def reindex():
    """Rebuild search index"""
    try:
        click.echo("🔄 Rebuilding search index...")
        
        async def rebuild_index():
            from src.search.fixed_indexer import FixedAzureSearchIndexer
            indexer = FixedAzureSearchIndexer()
            
            try:
                await indexer.connect_to_mongodb()
                
                click.echo("📝 Creating search index...")
                await indexer.create_or_update_index()
                
                click.echo("📊 Indexing employee data...")
                await indexer.index_all_employees()
                
                click.echo("🔍 Verifying index...")
                await indexer.verify_index()
                
                click.echo("✅ Search index rebuilt successfully!")
                
            finally:
                await indexer.close_connections()
        
        asyncio.run(rebuild_index())
        
    except Exception as e:
        click.echo(f"❌ Reindex failed: {e}")

# =============================================================================
# CONFIG COMMANDS
# =============================================================================

@cli.group()
def config():
    """Configuration management commands"""
    pass

@config.command()
def show():
    """Show current configuration (sanitized)"""
    click.echo("⚙️  Current Configuration")
    click.echo("=" * 25)
    
    # Show sanitized config
    click.echo(f"Database: {settings.mongodb_database}")
    click.echo(f"Search Service: {settings.azure_search_service_name}")
    click.echo(f"Search Endpoint: {settings.azure_search_endpoint}")
    click.echo(f"OpenAI Endpoint: {settings.azure_openai_endpoint}")
    
    # Test connections
    click.echo("\n🔌 Connection Tests:")
    
    # Test MongoDB
    try:
        async def test_mongo():
            await employee_collections.mongodb_client.connect()
            return True
        
        if asyncio.run(test_mongo()):
            click.echo("   ✅ MongoDB: Connected")
        else:
            click.echo("   ❌ MongoDB: Failed")
    except:
        click.echo("   ❌ MongoDB: Failed")
    
    # Test Search
    try:
        count = azure_search_client.get_document_count()
        click.echo(f"   ✅ Azure Search: Connected ({count} docs)")
    except:
        click.echo("   ❌ Azure Search: Failed")

@config.command()
def validate():
    """Validate configuration and dependencies"""
    click.echo("✅ Validating Configuration")
    click.echo("=" * 30)
    
    errors = []
    warnings = []
    
    # Check required settings
    required_settings = [
        'mongodb_connection_string',
        'mongodb_database',
        'azure_search_endpoint',
        'azure_search_api_key',
        'azure_openai_endpoint',
        'azure_openai_api_key'
    ]
    
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if not value:
            errors.append(f"Missing required setting: {setting}")
        else:
            click.echo(f"   ✅ {setting}: Set")
    
    # Check file dependencies
    try:
        import pandas as pd
        click.echo("   ✅ pandas: Available")
    except ImportError:
        errors.append("pandas not installed")
    
    try:
        import motor
        click.echo("   ✅ motor: Available")
    except ImportError:
        errors.append("motor not installed")
    
    try:
        from azure.search.documents import SearchClient
        click.echo("   ✅ azure-search-documents: Available")
    except ImportError:
        errors.append("azure-search-documents not installed")
    
    try:
        from openai import AzureOpenAI
        click.echo("   ✅ openai: Available")
    except ImportError:
        errors.append("openai not installed")
    
    # Summary
    if errors:
        click.echo(f"\n❌ Validation failed with {len(errors)} errors:")
        for error in errors:
            click.echo(f"   - {error}")
        sys.exit(1)
    elif warnings:
        click.echo(f"\n⚠️  Validation completed with {len(warnings)} warnings:")
        for warning in warnings:
            click.echo(f"   - {warning}")
    else:
        click.echo("\n🎉 Configuration validation passed!")

# =============================================================================
# UTILITY COMMANDS
# =============================================================================

@cli.command()
def version():
    """Show version information"""
    click.echo("HR Q&A System v1.0.0")
    click.echo("Built with:")
    click.echo("  - FastAPI for REST API")
    click.echo("  - Azure OpenAI for AI responses")
    click.echo("  - Azure AI Search for indexing")
    click.echo("  - MongoDB Atlas for data storage")

@cli.command()
def docs():
    """Show documentation and help"""
    click.echo("📚 HR Q&A System Documentation")
    click.echo("=" * 35)
    click.echo("")
    click.echo("🚀 Quick Start:")
    click.echo("  1. hrqa etl run data/input/hr_data.xlsx")
    click.echo("  2. hrqa query ask 'Who are the developers?'")
    click.echo("")
    click.echo("🔧 Management:")
    click.echo("  hrqa data stats              # Show data statistics")
    click.echo("  hrqa search status           # Check search system")
    click.echo("  hrqa config validate         # Validate configuration")
    click.echo("")
    click.echo("💬 Query Examples:")
    click.echo("  'Find employees with AWS certification'")
    click.echo("  'How many people work in IT?'")
    click.echo("  'Show me all managers'")
    click.echo("  'Who works in the Sales department?'")
    click.echo("")
    click.echo("📖 For more help: hrqa --help")

@cli.command()
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='Output format')
def system_info(output_format):
    """Show comprehensive system information"""
    
    async def get_system_info():
        info = {
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "type": "MongoDB Atlas",
                "status": "unknown",
                "collections": 0,
                "total_employees": 0
            },
            "search": {
                "type": "Azure AI Search",
                "status": "unknown", 
                "indexed_documents": 0
            },
            "ai": {
                "type": "Azure OpenAI",
                "model": "GPT-4",
                "embedding_model": "text-embedding-ada-002"
            }
        }
        
        # Test database
        try:
            await employee_collections.mongodb_client.connect()
            collections = await employee_collections.mongodb_client.get_collections()
            employee_ids = await employee_collections.get_all_employee_ids()
            
            info["database"]["status"] = "connected"
            info["database"]["collections"] = len(collections)
            info["database"]["total_employees"] = len(employee_ids)
        except:
            info["database"]["status"] = "error"
        
        # Test search
        try:
            count = azure_search_client.get_document_count()
            info["search"]["status"] = "connected"
            info["search"]["indexed_documents"] = count
        except:
            info["search"]["status"] = "error"
        
        return info
    
    try:
        info = asyncio.run(get_system_info())
        
        if output_format == 'json':
            click.echo(json.dumps(info, indent=2))
        else:
            click.echo("🖥️  System Information")
            click.echo("=" * 25)
            click.echo(f"Version: {info['version']}")
            click.echo(f"Timestamp: {info['timestamp']}")
            click.echo("")
            click.echo("💾 Database:")
            click.echo(f"   Type: {info['database']['type']}")
            click.echo(f"   Status: {info['database']['status']}")
            click.echo(f"   Collections: {info['database']['collections']}")
            click.echo(f"   Employees: {info['database']['total_employees']}")
            click.echo("")
            click.echo("🔍 Search:")
            click.echo(f"   Type: {info['search']['type']}")
            click.echo(f"   Status: {info['search']['status']}")
            click.echo(f"   Documents: {info['search']['indexed_documents']}")
            click.echo("")
            click.echo("🤖 AI:")
            click.echo(f"   Type: {info['ai']['type']}")
            click.echo(f"   Model: {info['ai']['model']}")
            click.echo(f"   Embeddings: {info['ai']['embedding_model']}")
            
    except Exception as e:
        click.echo(f"❌ Failed to get system info: {e}")

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\n❌ Unexpected error: {e}")
        sys.exit(1)