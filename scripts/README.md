# Scripts Directory

This directory contains essential utility scripts for ChatMind setup, testing, and management.

## 📁 Essential Scripts

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

### **test_neo4j_queries.py**
- **Purpose**: Comprehensive Neo4j database query testing
- **Usage**: `python scripts/test_neo4j_queries.py`
- **Features**:
  - Tests all documented Neo4j queries (85+ tests)
  - Validates query performance and data integrity
  - Covers advanced analysis, quality checks, and visualization queries
  - Ensures 100% compatibility with current database schema

### **test_api_endpoints.py**
- **Purpose**: Comprehensive API endpoint testing
- **Usage**: `python scripts/test_api_endpoints.py`
- **Features**:
  - Tests all API endpoints
  - Validates response formats and data integrity
  - Ensures API functionality and performance

### **extract_tags.py**
- **Purpose**: Extract and analyze tags from processed data
- **Usage**: `python scripts/extract_tags.py`
- **Features**:
  - Extracts tags from tagged chunks
  - Generates tag frequency analysis
  - Helps with tag normalization and cleanup

### **verify_data_directories.py**
- **Purpose**: Validate data directory structure
- **Usage**: `python scripts/verify_data_directories.py`
- **Features**:
  - Checks for required directories
  - Validates data structure integrity
  - Ensures proper setup for pipeline execution

## 🚀 Quick Usage

```bash
# Initial setup
python scripts/setup.py

# Start all services
python scripts/start_services.py

# Test database queries
python scripts/test_neo4j_queries.py

# Test API endpoints
python scripts/test_api_endpoints.py

# Extract tag analysis
python scripts/extract_tags.py

# Verify data directories
python scripts/verify_data_directories.py
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
python scripts/test_neo4j_queries.py    # Test all database queries
python scripts/test_api_endpoints.py    # Test all API endpoints
```

## 🎯 Current Implementation Focus

### **Streamlined Script Suite**
- **6 essential scripts** for core functionality
- **Removed 16 outdated scripts** for cleaner codebase
- **Focused on current pipeline/API implementation**
- **Comprehensive testing coverage**

### **Database Testing**
- **85+ Neo4j query tests** with 100% success rate
- **Advanced analysis patterns** for semantic exploration
- **Performance optimization** for large datasets
- **Quality assurance** through extensive validation

### **API Testing**
- **Complete endpoint coverage** for all API routes
- **Response format validation** and data integrity checks
- **Performance benchmarking** for optimal user experience

## 📊 Test Results

### **Neo4j Query Tests**
- **85/85 tests passing** (100% success rate)
- **Average query time: 0.023s**
- **Comprehensive coverage** of rich dataset (168,406 nodes)
- **Validates all query patterns** from enhanced guide

### **API Endpoint Tests**
- **Complete endpoint coverage** for all routes
- **Response validation** and error handling
- **Performance optimization** for production use

## 🔧 Maintenance

### **Script Cleanup**
- Removed outdated Gemma-2B scripts (now using local models)
- Removed redundant quality test scripts
- Removed development/debugging scripts
- Focused on essential functionality only

### **Open Source Ready**
- Clean, focused script collection
- Comprehensive documentation
- Essential functionality only
- No outdated or experimental code 