# HR Q&A System - Ollama Setup Guide

## 🚀 Quick Start

This guide will help you set up the HR Q&A System with Ollama-based AI models, replacing the Azure dependencies.

### Prerequisites

1. **Python 3.8+** installed
2. **MongoDB** running (local or Atlas)
3. **Ollama** installed from [ollama.ai](https://ollama.ai/)

## 📋 Installation Steps

### Step 1: Install Ollama

**Windows:**
```bash
# Download and install from https://ollama.ai/
# Or use winget:
winget install Ollama.Ollama
```

**macOS:**
```bash
# Download and install from https://ollama.ai/
# Or use Homebrew:
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Start Ollama Server

```bash
ollama serve
```

Keep this running in a separate terminal.

### Step 3: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### Step 4: Setup Ollama Models

```bash
# Run the automated setup script
python setup_ollama.py

# Or view model information first
python setup_ollama.py info
```

This will install:
- `llama3.2:3b` (~2GB) - Main language model
- `nomic-embed-text` (~274MB) - Embedding model

### Step 5: Configure Environment

Create a `.env` file in the project root:

```env
# MongoDB Configuration (REQUIRED)
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
MONGODB_DATABASE=hr_qna_poc

# Ollama Configuration (OPTIONAL - defaults work)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# NOTE: Azure OpenAI and Azure Search settings removed
```

### Step 6: Load Sample Data

```bash
# Load the sample HR data
python src/processing/etl_pipeline.py
```

### Step 7: Start the Application

```bash
# Start the FastAPI server
python src/api/main.py
```

Open your browser to: **http://localhost:8000**

## 🎯 What's Changed

### ✅ Replaced Components

| Original | Replacement | Status |
|----------|-------------|---------|
| Azure OpenAI GPT-4 | Ollama llama3.2:3b | ✅ Complete |
| Azure AI Search | MongoDB + Local Search | ✅ Complete |
| Azure Embeddings | Ollama nomic-embed-text | ✅ Complete |
| No Web UI | Professional HTML UI | ✅ Complete |

### 🔧 New Features

1. **Professional Web Interface**
   - Modern, responsive design
   - Real-time query processing
   - Interactive analytics dashboard
   - Employee directory with filters

2. **Local AI Processing**
   - No external API dependencies
   - Faster response times
   - Complete data privacy
   - Offline capability

3. **Enhanced Query Engine**
   - Natural language processing
   - Complex analytics queries
   - Comparison and ranking
   - Recommendation queries

## 🧪 Testing the Setup

### Test Ollama Connection

```bash
python src/ai/ollama_client.py
```

### Test Query Engine

```bash
python src/query/ollama_query_engine.py
```

### Test Local Search

```bash
python src/search/local_search_client.py
```

### Test Full System

```bash
# Start the server
python src/api/main.py

# In another terminal, test the API
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "How many employees work in IT?", "top_k": 5}'
```

## 🎮 Sample Queries to Try

Once everything is running, try these queries in the web interface:

### Basic Queries
- "How many employees work in IT department?"
- "Show me all developers"
- "Find employees with AWS certification"

### Analytics Queries
- "What's the average performance rating?"
- "Compare salaries between IT and Sales"
- "Top 5 performers in the company"

### Complex Queries
- "Show me developers with more than 5 years experience"
- "Who has the highest leave balance?"
- "Employees who joined in the last 6 months"

## 🔧 Troubleshooting

### Ollama Issues

**Problem:** Ollama not starting
```bash
# Check if Ollama is installed
ollama --version

# Start Ollama server
ollama serve

# Check if models are installed
ollama list
```

**Problem:** Model download fails
```bash
# Try installing a smaller model first
ollama pull llama3.2:1b

# Or try alternative models
ollama pull gemma2:2b
ollama pull phi3:mini
```

### MongoDB Issues

**Problem:** Database connection fails
```bash
# Check MongoDB status
mongosh --eval "db.adminCommand('ping')"

# For MongoDB Atlas, check connection string
# For local MongoDB, ensure it's running:
# Windows: net start MongoDB
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

### Python Dependencies

**Problem:** Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.8+
```

## 📊 Performance Expectations

### Model Performance

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| llama3.2:3b | ~2GB | Medium | High | Recommended |
| llama3.2:1b | ~1GB | Fast | Good | Quick testing |
| gemma2:2b | ~1.5GB | Medium | High | Alternative |
| phi3:mini | ~2GB | Medium | High | Alternative |

### Response Times

- Simple queries: 1-3 seconds
- Complex analytics: 3-8 seconds
- Large result sets: 5-15 seconds

## 🔒 Security & Privacy

### Data Privacy
- All AI processing happens locally
- No data sent to external services
- Complete control over your data

### Security Considerations
- MongoDB should be secured in production
- Consider authentication for web interface
- Regular backups of employee data

## 🚀 Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.9-slim

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Start services
CMD ["python", "src/api/main.py"]
```

### Environment Variables

```env
# Production settings
MONGODB_CONNECTION_STRING=mongodb://user:pass@host:port/db
MONGODB_DATABASE=hr_production
OLLAMA_BASE_URL=http://ollama-server:11434
```

## 📈 Monitoring & Maintenance

### Health Checks

- **API Health:** `GET /health`
- **Ollama Status:** Check `http://localhost:11434/api/tags`
- **MongoDB Status:** Check connection in logs

### Regular Maintenance

1. **Update Models:** `ollama pull llama3.2:3b`
2. **Backup Data:** MongoDB dump
3. **Monitor Logs:** Check application logs
4. **Performance:** Monitor response times

## 🆘 Support

### Common Issues

1. **Slow responses:** Try smaller models or increase timeout
2. **Memory issues:** Use 1B parameter models
3. **Connection errors:** Check Ollama server status
4. **Import errors:** Verify Python dependencies

### Getting Help

1. Check the logs for error messages
2. Verify all services are running
3. Test individual components
4. Review this setup guide

## 🎉 Success Indicators

Your setup is working correctly when:

✅ Ollama server responds to health checks  
✅ Models are installed and test successfully  
✅ MongoDB connection is established  
✅ Web interface loads at http://localhost:8000  
✅ Sample queries return results  
✅ Analytics dashboard shows data  

**Congratulations! Your HR Q&A System is ready for use! 🚀**
