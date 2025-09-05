# HR Q&A System - Ollama Edition

## 🚀 Overview

The HR Q&A System is a comprehensive employee analytics platform that provides natural language querying capabilities for HR data. This version has been completely refactored to use **Ollama** for local AI processing, replacing Azure dependencies with a fully self-contained solution.

### ✨ Key Features

- **🤖 Local AI Processing** - Uses Ollama for natural language understanding
- **🌐 Professional Web Interface** - Modern, responsive HTML/CSS/JS UI
- **📊 Advanced Analytics** - Complex queries, comparisons, and rankings
- **🔍 Intelligent Search** - MongoDB-based search with semantic capabilities
- **📱 Responsive Design** - Works on desktop, tablet, and mobile
- **🔒 Data Privacy** - All processing happens locally

## 🏗️ Architecture

### Before (Azure-based)
```
UI → FastAPI → Azure OpenAI → Azure AI Search → MongoDB
```

### After (Ollama-based)
```
Web UI → FastAPI → Ollama LLM → MongoDB Search → MongoDB
```

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | HTML/CSS/JS | Professional web interface |
| **Backend** | FastAPI | REST API server |
| **AI Engine** | Ollama (llama3.2:3b) | Natural language processing |
| **Search** | MongoDB + Local Search | Employee data retrieval |
| **Database** | MongoDB | Employee data storage |
| **Embeddings** | Ollama (nomic-embed-text) | Semantic search |

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **MongoDB** (local or Atlas)
3. **Ollama** installed from [ollama.ai](https://ollama.ai/)

### Installation

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama server
ollama serve

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Setup Ollama models
python setup_ollama.py

# 5. Configure environment
cp .env.example .env
# Edit .env with your MongoDB connection string

# 6. Load sample data
python src/processing/etl_pipeline.py

# 7. Start the application
python src/api/main.py

# 8. Open browser to http://localhost:8000
```

## 🎯 What's New

### ✅ Completed Improvements

1. **Professional Web Interface**
   - Modern, responsive design with gradient backgrounds
   - Interactive dashboard with real-time analytics
   - Advanced query interface with suggestions
   - Employee directory with filtering and pagination
   - Toast notifications and loading states

2. **Ollama Integration**
   - Replaced Azure OpenAI with local Ollama models
   - Supports llama3.2:3b for text generation
   - Uses nomic-embed-text for embeddings
   - Fallback mechanisms for reliability

3. **Enhanced Query Engine**
   - Advanced intent detection
   - Complex analytics queries (comparisons, rankings)
   - Natural language response generation
   - Error handling and fallback responses

4. **Local Search System**
   - MongoDB-based text search
   - Semantic search capabilities
   - Faceted search and suggestions
   - No external search dependencies

5. **Comprehensive Testing**
   - System connectivity tests
   - Automated demo scripts
   - Component validation
   - Performance monitoring

### 🔧 Technical Improvements

- **Removed Dependencies**: Azure OpenAI, Azure AI Search
- **Added Dependencies**: Ollama, requests
- **New Components**: Web UI, Local Search, Ollama Client
- **Enhanced**: Query Engine, Error Handling, Testing

## 📊 Sample Queries

### Basic Queries
```
"How many employees work in IT department?"
"Show me all developers"
"Find employees with AWS certification"
```

### Analytics Queries
```
"What's the average performance rating?"
"Compare salaries between IT and Sales"
"Top 5 performers in the company"
```

### Complex Queries
```
"Show me developers with more than 5 years experience"
"Who has the highest leave balance?"
"Employees who joined in the last 6 months"
"Remote employees with high performance ratings"
```

## 🧪 Testing

### System Test
```bash
python test_system.py
```

### Demo Script
```bash
# Comprehensive demo
python demo_script.py

# Quick demo
python demo_script.py --quick
```

### Individual Components
```bash
# Test Ollama
python src/ai/ollama_client.py

# Test Query Engine
python src/query/ollama_query_engine.py

# Test Search
python src/search/local_search_client.py
```

## 📁 Project Structure

```
hr_qna_poc/
├── static/                     # Web interface files
│   ├── index.html             # Main web page
│   ├── styles.css             # Styling
│   └── app.js                 # Frontend logic
├── src/
│   ├── ai/
│   │   └── ollama_client.py   # Ollama integration
│   ├── api/
│   │   └── main.py            # FastAPI server
│   ├── query/
│   │   └── ollama_query_engine.py  # Query processing
│   ├── search/
│   │   └── local_search_client.py   # Local search
│   ├── database/
│   │   └── mongodb_client.py  # Database operations
│   └── processing/
│       └── etl_pipeline.py    # Data loading
├── setup_ollama.py            # Ollama setup script
├── test_system.py             # System tests
├── demo_script.py             # Demo automation
└── requirements.txt            # Python dependencies
```

## 🔧 Configuration

### Environment Variables

```env
# MongoDB Configuration (REQUIRED)
MONGODB_CONNECTION_STRING=mongodb://localhost:27017
MONGODB_DATABASE=hr_qna_poc

# Ollama Configuration (OPTIONAL)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Model Configuration

| Model | Size | Use Case | Performance |
|-------|------|----------|-------------|
| llama3.2:3b | ~2GB | Recommended | High quality, good speed |
| llama3.2:1b | ~1GB | Fast testing | Good quality, very fast |
| gemma2:2b | ~1.5GB | Alternative | High quality, efficient |
| phi3:mini | ~2GB | Alternative | Good quality, balanced |

## 🚀 Deployment

### Local Development
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start MongoDB
mongod

# Terminal 3: Start API server
python src/api/main.py
```

### Docker Deployment
```dockerfile
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

### Production Considerations

1. **Security**
   - Secure MongoDB connection
   - Add authentication to web interface
   - Use HTTPS in production

2. **Performance**
   - Use larger Ollama models for better quality
   - Implement caching for frequent queries
   - Monitor response times

3. **Monitoring**
   - Set up health checks
   - Monitor Ollama server status
   - Track query performance

## 🔍 Troubleshooting

### Common Issues

1. **Ollama not starting**
   ```bash
   # Check installation
   ollama --version
   
   # Start server
   ollama serve
   
   # Check models
   ollama list
   ```

2. **MongoDB connection failed**
   ```bash
   # Check MongoDB status
   mongosh --eval "db.adminCommand('ping')"
   
   # For local MongoDB
   sudo systemctl start mongod
   ```

3. **Slow responses**
   - Use smaller models (llama3.2:1b)
   - Increase timeout settings
   - Check system resources

4. **Import errors**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

### Performance Optimization

1. **Model Selection**
   - Use llama3.2:1b for speed
   - Use llama3.2:3b for quality
   - Consider GPU acceleration

2. **Query Optimization**
   - Use specific queries
   - Limit result sets
   - Cache frequent queries

3. **System Resources**
   - Ensure adequate RAM (8GB+ recommended)
   - Use SSD storage
   - Monitor CPU usage

## 📈 Performance Metrics

### Expected Performance

| Query Type | Response Time | Quality |
|------------|---------------|---------|
| Simple Count | 1-3 seconds | High |
| Basic Search | 2-5 seconds | High |
| Complex Analytics | 5-15 seconds | High |
| Comparison Queries | 3-8 seconds | High |

### Resource Usage

| Component | RAM Usage | CPU Usage |
|-----------|-----------|-----------|
| Ollama (llama3.2:3b) | ~2GB | Medium |
| MongoDB | ~500MB | Low |
| FastAPI | ~100MB | Low |
| Web Browser | ~200MB | Low |

## 🎉 Success Indicators

Your system is working correctly when:

✅ Ollama server responds to health checks  
✅ Models are installed and test successfully  
✅ MongoDB connection is established  
✅ Web interface loads at http://localhost:8000  
✅ Sample queries return results  
✅ Analytics dashboard shows data  
✅ All system tests pass  

## 📚 Documentation

- **Setup Guide**: `OLLAMA_SETUP_GUIDE.md`
- **API Documentation**: http://localhost:8000/docs
- **Query Examples**: `docs/query_examples.md`
- **Troubleshooting**: `docs/troubleshooting.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for providing excellent local AI capabilities
- **MongoDB** for robust data storage
- **FastAPI** for the excellent web framework
- **The open-source community** for various libraries and tools

---

**🎯 Ready to revolutionize your HR analytics with local AI!**

For support and questions, please check the troubleshooting guide or open an issue.
