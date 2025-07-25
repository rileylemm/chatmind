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

## 🚀 Quick Usage

```bash
# Initial setup
python scripts/setup.py

# Start all services
python scripts/start_services.py

# Extract tag analysis
python scripts/extract_tags.py
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