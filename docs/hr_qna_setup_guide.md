# HR Q&A System - Complete Setup Guide

## 🏗️ System Overview

The HR Q&A System is a comprehensive employee data management and query platform that combines:

- **MongoDB Atlas** - 10 collections for 360° employee data
- **Azure AI Search** - Semantic + Vector + Hybrid search capabilities  
- **Azure OpenAI GPT-4** - Natural language processing and response generation
- **FastAPI** - REST API with full CRUD operations
- **Rich CLI** - Command-line interface for management and testing

## 📋 Prerequisites

### 1. Required Accounts & Services

| Service | Purpose | Required Plan |
|---------|---------|---------------|
| **MongoDB Atlas** | Employee data storage | Free tier (M0) or higher |
| **Azure AI Search** | Search and indexing | Basic tier or higher |
| **Azure OpenAI** | Natural language processing | Standard deployment |
| **Python 3.8+** | Runtime environment | Any recent version |

### 2. Development Environment

```bash
# Check Python version
python --version  # Should be 3.8+

# Check pip
pip --version

# Optional: Create virtual environment
python -m venv hr_qna_env
source hr_qna_env/bin/activate  # On Windows: hr_qna_env\Scripts\activate
```

## 🛠️ Installation Steps

### Step 1: Clone and Setup Project

```bash
# Create project directory
mkdir hr_qna_system
cd hr_qna_system

# Copy all project files to this directory
# Ensure you have the complete project structure:
# ├── config/
# ├── scripts/
# ├── src/
# ├── data/input/
# └── .env (to be created)
```

### Step 2: Install Dependencies

```bash
# Install required packages
pip install fastapi uvicorn motor pandas azure-search-documents azure-identity openai click pydantic python-dotenv aiohttp psutil

# Or if you have requirements.txt:
pip install -r requirements.txt
```

### Step 3: Service Configuration

#### 3.1 MongoDB Atlas Setup

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create free account and cluster

2. **Setup Database Access**
   - Create database user with read/write permissions
   - Add your IP address to whitelist (or 0.0.0.0/0 for development)

3. **Get Connection String**
   - Click "Connect" → "Connect your application"
   - Copy connection string format: `mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority`

#### 3.2 Azure AI Search Setup

1. **Create Azure AI Search Service**
   - Log into Azure Portal
   - Create new "Azure AI Search" resource
   - Choose Basic tier or higher for semantic search

2. **Get Service Details**
   - Service name: `your-service-name`
   - Endpoint: `https://your-service-name.search.windows.net`
   - Admin API key from "Keys" section

#### 3.3 Azure OpenAI Setup

1. **Request Azure OpenAI Access**
   - Apply for access at [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
   - Wait for approval (can take several days)

2. **Create OpenAI Resource**
   - Create "Azure OpenAI" resource in Azure Portal
   - Deploy required models:
     - **GPT-4o** (for chat/responses) - deployment name: `gpt-4o-llm`
     - **text-embedding-ada-002** (for vectors) - deployment name: `text-embedding-ada-002`

3. **Get Service Details**
   - Endpoint: `https://your-resource.openai.azure.com/`
   - API key from "Keys and Endpoint" section

### Step 4: Environment Configuration

Create `.env` file in project root:

```env
# MongoDB Configuration
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=hr_qna_poc

# Azure Search Configuration
AZURE_SEARCH_SERVICE_NAME=your-search-service-name
AZURE_SEARCH_ENDPOINT=https://your-search-service-name.search.windows.net
AZURE_SEARCH_API_KEY=your-search-admin-api-key

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-llm
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2023-05-15
```

### Step 5: Verify Configuration

```bash
# Test configuration loading
python src/core/config.py

# Expected output:
# ✅ Found .env file at: /path/to/your/.env
# ✅ Configuration loaded successfully
# 🎉 All required settings appear to be loaded!
```

## 🗄️ Database Setup

### Step 1: Create Collections

```bash
# Create all 10 MongoDB collections with proper schemas
python scripts/setup_collections.py --action create_all
```

**Expected Output:**
```
✅ Created collection 'personal_info' with schema validation
✅ Created collection 'employment' with schema validation
✅ Created collection 'learning' with schema validation
... (10 collections total)
🎉 Successfully created 10/10 collections
```

### Step 2: Validate Collection Setup

```bash
# Verify all collections were created properly
python scripts/setup_collections.py --action validate_schema
```

### Step 3: Check Database Status

```bash
# Inspect MongoDB structure
python inspect_mongodb.py
```

## 📊 Data Loading (ETL Pipeline)

### Step 1: Prepare HR Data

1. **Create Excel file** with multiple sheets for different data aspects:
   - `Personal Info` - Employee basic details
   - `Employment` - Job roles, departments
   - `Learning` - Certifications, training
   - `Experience` - Years of experience, skills
   - `Performance` - Ratings, KPIs
   - `Engagement` - Projects, feedback
   - `Compensation` - Salary data (optional)
   - `Attendance` - Leave, attendance data
   - `Attrition` - Risk assessment data
   - `Project History` - Past projects

2. **Required columns** (minimum):
   - All sheets must have `employee_id` column
   - `Personal Info`: `full_name`, `email`, `location`
   - `Employment`: `department`, `role`

### Step 2: Load Data

```bash
# Place your Excel file in data/input/ directory
# Then run ETL pipeline:
python -m src.cli.interface etl run data/input/your_hr_data.xlsx

# Or use the direct ETL script:
python src/processing/etl_pipeline.py
```

**Expected Process:**
```
🚀 Starting Full ETL Pipeline
📊 Step 1: Extract and Load to MongoDB
📖 Reading Excel file: data/input/your_hr_data.xlsx
   Found 10 sheets to process
🔄 Step 2: Transform and Validate Data
🔍 Step 3: Create Search Index
🧠 Step 4: Generate Embeddings
✅ Step 5: Verify Pipeline Results
🎉 ETL Pipeline Completed Successfully!
```

### Step 3: Verify Data Load

```bash
# Check data statistics
python -m src.cli.interface data stats

# Expected output:
# 👥 Total employees: 150
# 🏢 Departments: 5
# 💼 Roles: 12
# 🔍 Indexed documents: 150
```

## 🔍 Search Index Setup

### Step 1: Create Search Index

```bash
# Create comprehensive search index
python scripts/create_search_indexes.py --action create --index hr-employees-fixed
```

### Step 2: Index Employee Data

```bash
# Index all employee data from MongoDB
python src/search/indexer.py
```

### Step 3: Generate Vector Embeddings (Optional)

```bash
# Generate embeddings for semantic search
python src/search/embeddings.py
```

### Step 4: Verify Search Index

```bash
# Validate search index
python scripts/create_search_indexes.py --action validate --index hr-employees-fixed

# Test search functionality
python -m src.cli.interface search test "developer"
```

## 🧪 Testing & Validation

### Step 1: Test Query Engine

```bash
# Run comprehensive query tests
python enhanced_query_engine_dry_run.py
```

**Expected Test Results:**
```
🔍 Test 1: Leave Analytics - Maximum
✅ SUCCESS - Found 5 employees

🔍 Test 2: Performance Analytics  
✅ SUCCESS - Found 12 employees

🔍 Test 3: Text Search - Fallback Test
✅ SUCCESS - Found 8 employees
```

### Step 2: CLI Testing

```bash
# Test predefined queries
python -m src.cli.interface query test

# Interactive testing
python -m src.cli.interface query interactive
```

**Try these test queries:**
- "How many employees work in IT?"
- "Find developers with AWS certification"
- "Show me employees in the Sales department"
- "Who are the top performers?"

### Step 3: Performance Testing

```bash
# Run performance benchmarks
python scripts/performance_test.py --test query_speed --iterations 50
```

## 🚀 API Server Setup

### Step 1: Start API Server

```bash
# Start FastAPI server
python src/api/main.py

# Or using uvicorn directly:
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Verify API

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### Step 3: Test API Endpoints

```bash
# Test query endpoint
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find developers with Python skills", "top_k": 5}'

# Test analytics endpoint
curl "http://localhost:8000/analytics/departments"
```

## 🔧 Common Issues & Troubleshooting

### Issue 1: MongoDB Connection Failed

**Symptoms:**
```
❌ MongoDB connection failed: ServerSelectionTimeoutError
```

**Solutions:**
1. Check internet connection
2. Verify MongoDB Atlas cluster is running
3. Confirm IP address is whitelisted
4. Check username/password in connection string
5. Ensure connection string format is correct

### Issue 2: Azure Search Index Creation Failed

**Symptoms:**
```
❌ Failed to create search index: AuthenticationError
```

**Solutions:**
1. Verify Azure Search service is running
2. Check API key permissions (must be admin key)
3. Confirm endpoint URL is correct
4. Ensure service tier supports semantic search

### Issue 3: OpenAI API Errors

**Symptoms:**
```
❌ OpenAI initialization failed: InvalidApiKey
```

**Solutions:**
1. Verify Azure OpenAI resource is deployed
2. Check API key is correct
3. Confirm model deployments exist
4. Ensure endpoint URL includes full path

### Issue 4: No Query Results

**Symptoms:**
```
✅ SUCCESS - Found 0 employees
```

**Solutions:**
1. Check data was loaded: `python -m src.cli.interface data stats`
2. Verify search index: `python -m src.cli.interface search status`
3. Reindex data: `python -m src.cli.interface search reindex`
4. Test with simpler queries first

### Issue 5: Import Errors

**Symptoms:**
```
ImportError: No module named 'src.query.updated_query_engine'
```

**Solutions:**
1. Use correct import: `from src.query.hr_query_engine import RobustHRQueryEngine`
2. Check file paths and project structure
3. Ensure all required files are present

## 📈 System Validation Checklist

### ✅ Pre-Flight Checklist

- [ ] All required services are created and running
- [ ] Environment variables are configured correctly
- [ ] Python dependencies are installed
- [ ] Project structure is complete

### ✅ Database Validation

- [ ] MongoDB collections created successfully (10 collections)
- [ ] Sample data loaded and verified
- [ ] Indexes created on employee_id fields
- [ ] Data validation rules applied

### ✅ Search Validation

- [ ] Azure Search index created with all fields
- [ ] Employee data indexed successfully
- [ ] Vector embeddings generated (optional)
- [ ] Search queries return results

### ✅ API Validation

- [ ] FastAPI server starts without errors
- [ ] Health check endpoint responds
- [ ] Query endpoint processes requests
- [ ] Analytics endpoints return data

### ✅ Query Engine Validation

- [ ] Natural language queries work
- [ ] Different query types supported (count, search, analytics)
- [ ] Response generation working
- [ ] Error handling functioning

## 🎯 Next Steps

Once setup is complete:

1. **Load Your Data**: Replace sample data with real HR data
2. **Customize Queries**: Modify query examples for your use case
3. **Security Setup**: Enable authentication for production use
4. **Performance Tuning**: Optimize for your data size and query patterns
5. **Integration**: Connect to existing HR systems or dashboards

## 📞 Support Resources

### Documentation
- **MongoDB Atlas**: https://docs.atlas.mongodb.com/
- **Azure AI Search**: https://docs.microsoft.com/en-us/azure/search/
- **Azure OpenAI**: https://docs.microsoft.com/en-us/azure/ai-services/openai/
- **FastAPI**: https://fastapi.tiangolo.com/

### Debug Commands
```bash
# System information
python -m src.cli.interface system-info

# Configuration validation
python -m src.cli.interface config validate

# Component status
python -m src.cli.interface config show
```

### Log Files
Check logs in:
- Console output during setup
- Application logs (if configured)
- Azure service logs in Azure Portal

---

## 🎉 Success Indicators

Your HR Q&A System is successfully set up when:

1. ✅ All CLI commands work without errors
2. ✅ API server responds to requests
3. ✅ Natural language queries return relevant results
4. ✅ Analytics endpoints provide meaningful insights
5. ✅ Performance tests show acceptable response times

**Congratulations! Your HR Q&A System is ready for use! 🚀**