# ChatMind User Guide

This comprehensive guide covers installation, configuration, usage, and advanced features of ChatMind.

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Setup & Installation](#2-setup--installation)
3. [Data Processing Pipeline](#3-data-processing-pipeline)
4. [Starting Services](#4-starting-services)
5. [API Usage](#5-api-usage)
6. [Configuration](#6-configuration)
7. [Testing](#7-testing)
8. [Advanced Features](#8-advanced-features)
9. [Troubleshooting](#9-troubleshooting)

## 1. Prerequisites
1. Python 3.8 or higher
2. Node.js & npm (for frontend)
3. Neo4j (Desktop or Docker)
4. OpenAI API key (optional, for auto-tagging)

## 2. Setup & Installation
```bash
# Clone repository
git clone <your-repo-url>
cd <your-repo>

# Python dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp env.example .env  # edit: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY

# Frontend dependencies
cd chatmind/frontend
npm install
cd ../..
```

## 3. Data Processing Pipeline
The unified pipeline automatically handles both first-time processing and incremental updates.

### 3.1 Smart Pipeline (Recommended)
```bash
# Run complete pipeline (automatically handles incremental)
python run_pipeline.py

# Check what needs processing
python run_pipeline.py --check-only

# Force reprocess everything
python run_pipeline.py --force-reprocess
```

### 3.2 Individual Steps (Advanced)
```bash
# Data ingestion (already incremental)
python chatmind/data_ingestion/extract_and_flatten.py \
  --raw-dir data/raw \
  --processed-dir data/processed

# Embedding & clustering (incremental)
python chatmind/embedding/embed_and_cluster_direct_incremental.py

# Auto-tagging (incremental)
python chatmind/tagger/run_tagging_incremental.py

# Neo4j loading
python chatmind/neo4j_loader/load_graph.py \
  --clear \
  --chat-similarity \
  --similarity-threshold 0.8
```

### 3.3 Pipeline Options
```bash
# Skip expensive steps during development
python run_pipeline.py --skip-tagging --skip-embedding

# Clear all state and start fresh
python run_pipeline.py --clear-state

# Only check what needs processing
python run_pipeline.py --check-only
```

## 4. Starting Services
```bash
# All-in-one
python scripts/start_services.py

# Or separately
python chatmind/api/main.py       # API at http://localhost:8000
cd chatmind/frontend && npm start # UI at http://localhost:3000
```

## 5. API Usage

### Core Endpoints
- **`GET /api/health`** - Health check endpoint
- **`GET /api/stats/dashboard`** - Real-time dashboard statistics
- **`GET /api/graph`** - Knowledge graph data (multiple variants)
- **`GET /api/topics`** - Semantic topic clusters
- **`GET /api/chats`** - Chat listings with filtering
- **`GET /api/search`** - Content search across all data

### Advanced Endpoints
- **`GET /api/tags`** - Tag management and categorization
- **`GET /api/messages/{message_id}`** - Individual message details
- **`GET /api/clusters/{cluster_id}`** - Cluster-specific data
- **`GET /api/graph/expand/{node_id}`** - Expand graph nodes
- **`POST /api/search/advanced`** - Advanced search with filters
- **`POST /api/query/neo4j`** - Direct Neo4j query execution
- **`POST /api/chats/{chat_id}/summary`** - Generate chat summaries

### API Development
```bash
# Start API server with auto-reload
cd chatmind/api
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test API endpoints
python3 scripts/test_api_endpoints.py
```

### Real Data Sources
The backend connects to your actual processed data:
- **Chat Statistics**: Reads from `data/processed/chats.jsonl`
- **Tag Information**: Reads from `data/tags/tags_master_list.json`
- **Cost Tracking**: Reads from `data/cost_tracker.db`
- **Cluster Data**: Reads from `data/embeddings/cluster_summaries.json`

## 6. Configuration

### Tag Master List Setup

The system uses a master list of tags for consistent categorization.

#### Quick Setup:
```bash
# Option 1: Use the setup script (recommended)
python scripts/setup_tags.py

# Option 2: Manual copy
cp data/tags/tags_master_list_generic.json data/tags/tags_master_list.json
```

#### Customization Options:
- **Start with generic tags** - Use the provided 500-tag list as a starting point
- **Edit your personal list** - Modify `data/tags/tags_master_list.json` to match your interests
- **Let the system auto-expand** - The pipeline will suggest new tags based on your content
- **Review missing tags** - Check `data/interim/missing_tags_report.json` after processing

#### Privacy Note:
Your personal tag list (`data/tags/tags_master_list.json`) is excluded from git to keep your custom tags private. The generic list is included for new users.

#### Check Your Setup:
```bash
# See current tag list status
python scripts/setup_tags.py --info
```

### Processing Options
- **Incremental processing**: Only processes new data
- **Force reprocess**: `python run_pipeline.py --force-reprocess`
- **Skip specific steps**: `python run_pipeline.py --skip-tagging`

## 7. Testing

### Test Coverage
- **✅ API Endpoints**: 25 endpoints tested with 100% pass rate
- **✅ Dual Layer Graph**: 7 comprehensive tests covering all layers
- **✅ Neo4j Queries**: All documented queries tested and verified
- **✅ Pipeline Processing**: Incremental processing and data integrity

### Test Scripts
- **[API Endpoint Tests](scripts/test_api_endpoints.py)** - Test all API endpoints from the documentation
- **[Dual Layer Tests](scripts/test_dual_layer.py)** - Test dual layer graph strategy implementation
- **[Neo4j Query Tests](scripts/test_neo4j_queries.py)** - Test all Neo4j queries from the guide

### Running Tests
```bash
# Test API endpoints
python3 scripts/test_api_endpoints.py

# Test dual layer implementation
python3 scripts/test_dual_layer.py

# Test Neo4j queries
python3 scripts/test_neo4j_queries.py
```

## 8. Advanced Features

### Real-time Statistics
The dashboard displays live data from your processed content:
- **Total Chats**: Number of conversations processed
- **Total Messages**: Count of all messages across all chats
- **Active Tags**: Number of tags in your master list
- **Total Cost**: Actual API costs from your usage
- **Total Clusters**: Number of semantic clusters created
- **Total Calls**: Number of API calls made during processing

### Iterative Development
The unified pipeline makes development much easier:

```bash
# Add new ZIP files
cp new_export.zip data/raw/

# Run pipeline (automatically processes only new data)
python run_pipeline.py

# Check what was processed
python run_pipeline.py --check-only
```

## 7. Inspecting Data
```bash
# View tagged chunks
jq -c '{chat_id, message_id, tags, category}' data/processed/tagged_chunks.jsonl | head -n 10

# View embeddings
jq -c '{chat_id, content, cluster_id}' data/embeddings/chunks_with_clusters.jsonl | head -n 10

# Check state files
ls -la data/processed/*.pkl
```

## 8. Troubleshooting

### **Pipeline Issues:**
- **No tags?** Ensure `OPENAI_API_KEY` is set
- **Processing everything?** Check if state files exist: `ls data/processed/*.pkl`
- **Force reprocess:** Use `--force-reprocess` flag

### **Neo4j Issues:**
- **Connection errors?** Verify `.env` and Neo4j status
- **Clear database:** Use `--clear` flag with loader

### **Frontend Issues:**
- **CORS errors?** Check FastAPI CORS settings for `localhost:3000`
- **Build errors?** Run `npm install` in `chatmind/frontend/`

### **State Management:**
```bash
# Clear specific state
rm data/processed/message_embedding_state.pkl  # Clear embedding state
rm data/processed/chunk_tagging_state.pkl     # Clear tagging state

# Clear all state
python run_pipeline.py --clear-state
```

## 9. Advanced Usage

### **Development Workflow:**
```bash
# Quick iteration (skip expensive steps)
python run_pipeline.py --skip-tagging --skip-embedding

# Test specific step
python chatmind/tagger/run_tagging_incremental.py --force

# Check processing status
python run_pipeline.py --check-only
```

### **Production Workflow:**
```bash
# Add new data
cp new_export.zip data/raw/

# Run full pipeline (smart incremental)
python run_pipeline.py

# Start services
python scripts/start_services.py
```

---

**🎉 Your pipeline is now unified and smart - one command handles everything!**