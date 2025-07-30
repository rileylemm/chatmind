# ChatMind User Guide

This comprehensive guide covers installation, configuration, usage, and advanced features of ChatMind.

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Setup & Installation](#2-setup--installation)
   - [Tagger Setup](#21-tagger-setup)
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
4. **AI Component Selection**: Choose your processing approach:
   - **Cloud API (OpenAI)**: Fast, high quality, costs money (~$57-100 for 32K messages)
   - **Local Model (Ollama)**: Free, excellent quality, optimized for Gemma-2B

## 2. Setup & Installation

### 2.1 Full Application Setup (Recommended for Most Users)
```bash
# Clone repository
git clone <your-repo-url>
cd <your-repo>

# Python dependencies
pip install -r requirements.txt

# Pipeline-specific dependencies (optional - for pipeline-only installations)
pip install -r chatmind/pipeline/requirements.txt

# Copy and configure environment variables
cp env.example .env
```

### 2.2 Pipeline-Only Setup (For Pipeline Development/Deployment)
```bash
# Clone repository
git clone <your-repo-url>
cd <your-repo>

# Set up pipeline-specific virtual environment
python3 scripts/setup_pipeline_venv.py

# Activate pipeline virtual environment
# On macOS/Linux:
source chatmind/pipeline/activate_pipeline.sh
# On Windows:
# chatmind\pipeline\activate_pipeline.bat

# Copy and configure environment variables
cp env.example .env
```

### 2.3 Verification
```bash
# Verify data directory structure
python3 scripts/verify_data_directories.py

# Check pipeline dependencies
python3 scripts/check_pipeline_dependencies.py
```

### 2.4 Environment Configuration
```bash
# Edit .env with your configuration:
# Required for all setups:
# NEO4J_URI=bolt://localhost:7687
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=your_password
#
# Only required for Cloud API components:
# OPENAI_API_KEY=your_openai_key_here

# Frontend dependencies (only for full application setup)
cd chatmind/frontend
npm install
cd ../..
```

## 2.1 Tagger Setup

### Cloud API Setup (OpenAI)
```bash
# Verify OpenAI API key is set
echo $OPENAI_API_KEY

# Test cloud setup
python3 chatmind/pipeline/tagging/run_tagging.py --method cloud --check-only
```

### Local Model Setup (Ollama)
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull the optimized model (recommended: gemma:2b)
ollama pull gemma:2b

# Test local setup
python3 chatmind/pipeline/tagging/run_tagging.py --method local --check-only
```

### AI Component Comparison

| Feature | Cloud API | Local Model |
|---------|-----------|-------------|
| **Cost** | $57-100 for 32K messages | $0 |
| **Speed** | Fast | Fast (optimized for Gemma-2B) |
| **Quality** | Excellent | Excellent (100% JSON compliance) |
| **Privacy** | Data sent to OpenAI | Fully local |
| **Setup** | API key | Ollama + Gemma-2B model |

## 3. Data Processing Pipeline
The unified smart pipeline automatically handles both first-time processing and incremental updates with embedding reuse optimization.

### 3.1 Smart Pipeline (Recommended)
```bash
# Use cloud API for everything (fast, high quality, costs money)
python run_pipeline.py --embedding-method cloud --tagging-method cloud --summarization-method cloud

# Use local models for everything (free, excellent quality)
python run_pipeline.py --embedding-method local --tagging-method local --summarization-method local

# Use default mixed approach (local embedding, cloud tagging/summarization)
python run_pipeline.py

# Check what needs processing
python run_pipeline.py --check-only

# Force reprocess everything
python run_pipeline.py --force

# Run specific steps (uses embedding reuse optimization)
python run_pipeline.py --steps positioning similarity
```

### 3.2 Individual Steps (Advanced)
```bash
# Data ingestion
python chatmind/pipeline/ingestion/extract_and_flatten.py

# Semantic chunking
python chatmind/pipeline/chunking/chunker.py

# Enhanced embedding (choose method)
python chatmind/pipeline/embedding/run_embedding.py --method cloud
python chatmind/pipeline/embedding/run_embedding.py --method local

# Clustering
python chatmind/pipeline/clustering/clusterer.py

# Enhanced auto-tagging (choose method)
python chatmind/pipeline/tagging/run_tagging.py --method cloud
python chatmind/pipeline/tagging/run_tagging.py --method local

# Tag post-processing
python chatmind/pipeline/tagging/post_process_tags.py

# Cluster summarization (choose method)
python chatmind/pipeline/cluster_summarization/run_summarization.py --method cloud
python chatmind/pipeline/cluster_summarization/run_summarization.py --method local

# Chat summarization (choose method)
python chatmind/pipeline/chat_summarization/run_chat_summarization.py --method cloud
python chatmind/pipeline/chat_summarization/run_chat_summarization.py --method local

# Positioning (generates embeddings for reuse)
python chatmind/pipeline/positioning/position_chats.py
python chatmind/pipeline/positioning/position_clusters.py

# Similarity calculation (uses saved embeddings)
python chatmind/pipeline/similarity/calculate_chat_similarities.py
python chatmind/pipeline/similarity/calculate_cluster_similarities.py

# Neo4j loading
python chatmind/pipeline/loading/load_graph.py
```

### 3.3 Pipeline Optimization Features
- **Embedding Reuse**: Positioning step generates embeddings that are reused in similarity calculations
- **Hash-Based Tracking**: All steps use hash tracking for incremental processing
- **Separate Processing**: Chat and cluster processing are optimized separately
- **Consistent Naming**: All files follow consistent naming conventions

### 3.4 Pipeline Options
```bash
# Run only positioning and similarity (uses embedding reuse optimization)
python run_pipeline.py --steps positioning similarity

# Run only chat-related steps
python run_pipeline.py --steps chat_summarization positioning similarity

# Run only cluster-related steps
python run_pipeline.py --steps cluster_summarization positioning similarity

# Use local models for fast development
python run_pipeline.py --embedding-method local --tagging-method local

# Check setup before running expensive operations
python run_pipeline.py --check-only
```

### 3.5 Complete Pipeline Flags Reference

**Method Selection:**
```bash
# Choose embedding method (local/cloud)
--embedding-method local    # Use local models for embeddings (default)
--embedding-method cloud    # Use OpenAI API for embeddings

# Choose tagging method (local/cloud)
--tagging-method local      # Use local models for tagging (default)
--tagging-method cloud      # Use OpenAI API for tagging

# Choose summarization method (local/cloud)
--summarization-method local    # Use local models for summarization (default)
--summarization-method cloud    # Use OpenAI API for summarization
```

**Step Selection:**
```bash
# Run specific steps (can specify multiple)
--steps ingestion              # Data extraction from ChatGPT exports
--steps chunking               # Semantic chunking
--steps embedding              # Embedding generation
--steps clustering             # Clustering of embeddings
--steps tagging                # AI-powered tagging
--steps tag_propagation        # Tag post-processing
--steps cluster_summarization  # Cluster summarization
--steps chat_summarization     # Chat summarization
--steps positioning            # 2D positioning with embedding reuse
--steps similarity             # Similarity calculations
--steps loading                # Neo4j graph loading

# Examples:
--steps ingestion chunking embedding    # Run first three steps
--steps positioning similarity          # Run positioning and similarity
--steps chat_summarization positioning similarity  # Chat-focused workflow
```

**Processing Control:**
```bash
--force                        # Force reprocess all steps (ignore hash tracking)
--check-only                   # Only check setup, don't run pipeline
```

**Complete Examples:**
```bash
# Full pipeline with cloud API (fast, costs money)
python run_pipeline.py --embedding-method cloud --tagging-method cloud --summarization-method cloud

# Full pipeline with local models (free, excellent quality)
python run_pipeline.py --embedding-method local --tagging-method local --summarization-method local

# Default mixed approach (local embedding, cloud tagging/summarization)
python run_pipeline.py

# Development workflow - local models, specific steps
python run_pipeline.py --embedding-method local --tagging-method local --steps positioning similarity

# Force reprocess everything from scratch
python run_pipeline.py --force

# Check what needs processing without running
python run_pipeline.py --check-only

# Run only the expensive AI steps with cloud API
python run_pipeline.py --embedding-method cloud --tagging-method cloud --summarization-method cloud --steps embedding tagging cluster_summarization chat_summarization

# Run only the optimization steps (positioning + similarity)
python run_pipeline.py --steps positioning similarity

# Chat-focused workflow
python run_pipeline.py --steps chat_summarization positioning similarity

# Cluster-focused workflow
python run_pipeline.py --steps cluster_summarization positioning similarity
```

**Quick Reference Table:**

| Flag | Options | Description | Default |
|------|---------|-------------|---------|
| `--embedding-method` | `local`, `cloud` | Embedding generation method | `local` |
| `--tagging-method` | `local`, `cloud` | Tagging method | `local` |
| `--summarization-method` | `local`, `cloud` | Summarization method | `local` |
| `--steps` | `ingestion`, `chunking`, `embedding`, `clustering`, `tagging`, `tag_propagation`, `cluster_summarization`, `chat_summarization`, `positioning`, `similarity`, `loading` | Specific steps to run | All steps |
| `--force` | Flag | Force reprocess all steps | False |
| `--check-only` | Flag | Check setup without running | False |

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
- **Chat Statistics**: Reads from `data/processed/ingestion/chats.jsonl`
- **Tag Information**: Reads from `data/tags_masterlist/tags_master_list.json`
- **Cost Tracking**: Reads from `data/cost_tracker.db`
- **Cluster Data**: Reads from `data/processed/cluster_summarization/cluster_summaries.json`
- **Chat Summaries**: Reads from `data/processed/chat_summarization/chat_summaries.json`
- **Positioning Data**: Reads from `data/processed/positioning/chat_positions.jsonl` and `data/processed/positioning/cluster_positions.jsonl`
- **Similarity Data**: Reads from `data/processed/similarity/chat_similarities.jsonl` and `data/processed/similarity/cluster_similarities.jsonl`

## 6. Configuration

### Tag Master List Setup

The system uses a master list of tags for consistent categorization.

#### Quick Setup:
```bash
# Option 1: Use the setup script (recommended)
python scripts/setup_tags.py

# Option 2: Manual copy
cp data/tags_masterlist/tags_master_list_generic.json data/tags_masterlist/tags_master_list.json
```

#### Customization Options:
- **Start with generic tags** - Use the provided 500-tag list as a starting point
- **Edit your personal list** - Modify `data/tags_masterlist/tags_master_list.json` to match your interests
- **Let the system auto-expand** - The pipeline will suggest new tags based on your content
- **Review missing tags** - Check `data/processed/tagging/missing_tags_report.json` after processing

#### Privacy Note:
Your personal tag list (`data/tags_masterlist/tags_master_list.json`) is excluded from git to keep your custom tags private. The generic list is included for new users.

#### Check Your Setup:
```bash
# See current tag list status
python scripts/setup_tags.py --info
```

### Processing Options
- **Incremental processing**: Only processes new data using hash-based tracking
- **Force reprocess**: `python run_pipeline.py --force`
- **Run specific steps**: `python run_pipeline.py --steps positioning similarity`
- **Embedding reuse**: Positioning step generates embeddings reused in similarity calculations

### AI Component Configuration
- **Method selection**: Choose between `cloud` and `local` methods for each component
- **Model selection**: 
  - Cloud: `gpt-3.5-turbo` (default), `gpt-4` (better quality)
  - Local: `gemma:2b` (optimized), `mistral:latest` (alternative)
- **Pipeline optimization**: 
  - Hash-based tracking for incremental processing
  - Embedding reuse between positioning and similarity
  - Separate chat and cluster processing
  - Consistent file naming conventions

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
- **No tags?** Ensure your chosen tagger is properly set up:
  - Cloud: Check `OPENAI_API_KEY` is set
  - Local: Ensure Ollama is running and model is pulled
- **Processing everything?** Check if state files exist: `ls data/processed/*.pkl`
- **Force reprocess:** Use `--force-reprocess` flag

### **Tagger Issues:**
- **Cloud API errors?** Check OpenAI API key and billing
- **Local model errors?** Ensure Ollama is running: `ollama serve`
- **Slow local processing?** Try smaller models like `llama3.2:latest`
- **Quality issues?** Enable validation and conversation context

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