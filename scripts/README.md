# Scripts Directory

This directory contains utility scripts for ChatMind setup and management.

## 📁 Scripts

### **setup.py**
- **Purpose**: Initial project setup and dependency installation
- **Usage**: `python scripts/setup.py`
- **Features**:
  - Installs Python dependencies
  - Creates necessary directories
  - Sets up environment file from template
  - Installs frontend dependencies
  - Provides Neo4j setup instructions

### **start_services.py**
- **Purpose**: Starts the API server and frontend development server
- **Usage**: `python scripts/start_services.py`
- **Features**:
  - Starts FastAPI backend on port 8000
  - Starts React frontend on port 3000
  - Handles graceful shutdown with Ctrl+C
  - Can start services individually with flags

### **extract_tags.py**
- **Purpose**: Extract and analyze tags from processed data
- **Usage**: `python scripts/extract_tags.py`
- **Features**:
  - Extracts tags from tagged chunks
  - Generates tag frequency analysis
  - Helps with tag normalization and cleanup

### **test_gemma_final.py**
- **Purpose**: Test Gemma-2B performance and JSON compliance
- **Usage**: `python scripts/test_gemma_final.py`
- **Features**:
  - Tests Gemma-2B model functionality
  - Validates JSON compliance (100% success rate)
  - Tests optimized prompts and parsing
  - Shows tagging quality and confidence scores

### **test_api_endpoints.py**
- **Purpose**: Comprehensive API endpoint testing
- **Usage**: `python scripts/test_api_endpoints.py`
- **Features**:
  - Tests all 25+ API endpoints
  - Validates response formats
  - Ensures API functionality

### **test_dual_layer.py**
- **Purpose**: Test dual layer graph strategy
- **Usage**: `python scripts/test_dual_layer.py`
- **Features**:
  - Tests raw data layer
  - Tests semantic layer
  - Validates graph relationships

### **test_neo4j_queries.py**
- **Purpose**: Test Neo4j database queries
- **Usage**: `python scripts/test_neo4j_queries.py`
- **Features**:
  - Tests all documented Neo4j queries
  - Validates query performance
  - Ensures data integrity

## 🚀 Quick Usage

```bash
# Initial setup
python scripts/setup.py

# Start all services
python scripts/start_services.py

# Test Gemma-2B setup
python scripts/test_gemma_final.py

# Extract tag analysis
python scripts/extract_tags.py

# Test API endpoints
python scripts/test_api_endpoints.py
```

## 📋 Options

### Setup Options
```bash
python scripts/setup.py --skip-frontend  # Skip frontend setup
python scripts/setup.py --skip-neo4j     # Skip Neo4j instructions
```

### Service Options
```bash
python scripts/start_services.py --api-only      # Start only API
python scripts/start_services.py --frontend-only # Start only frontend
python scripts/start_services.py --api-port 8001 # Custom API port
```

### Testing Options
```bash
python scripts/test_gemma_final.py              # Test Gemma-2B performance
python scripts/test_api_endpoints.py            # Test all API endpoints
python scripts/test_dual_layer.py               # Test graph layers
python scripts/test_neo4j_queries.py            # Test database queries
```

## 🎯 Current Optimizations

### **Gemma-2B Integration**
- **100% JSON compliance** with optimized prompts
- **Fast 0.1s delays** between API calls
- **Robust error handling** with multiple fallbacks
- **Incremental saving** every 500 chunks

### **Cleaned Up Test Suite**
- Removed outdated test scripts
- Focused on essential functionality testing
- Optimized for current Gemma-2B setup
- Comprehensive API and database testing 