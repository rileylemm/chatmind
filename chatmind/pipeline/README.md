# ChatMind Pipeline

A modular data processing pipeline for ChatMind with hybrid Neo4j + Qdrant architecture for optimal performance.

## 🚀 Quick Start

### 1. Activate the Pipeline Environment

```bash
# Activate the pipeline virtual environment
source chatmind/pipeline/activate_pipeline.sh

# Or on Windows:
# chatmind/pipeline/activate_pipeline.bat
```

### 2. Configure Environment Variables

The pipeline uses a hierarchical configuration system:

```bash
# Copy the example environment file
cp chatmind/pipeline/env.example chatmind/pipeline/.env

# Edit with your settings
nano chatmind/pipeline/.env
```

**Configuration Precedence:**
1. Pipeline `.env` (highest priority - for overrides)
2. Root `.env` (fallback)
3. Default values (lowest priority)

### 3. Start Databases

```bash
# Option 1: Use Docker Compose (recommended)
cd chatmind/pipeline
./manage_databases.sh start

# Option 2: Use setup script
./chatmind/pipeline/setup_hybrid.sh

# Option 3: Manual Docker commands
docker-compose -f chatmind/pipeline/docker-compose.yml up -d
```

### 4. Verify Setup

```bash
# Check database status
./chatmind/pipeline/manage_databases.sh status

# Check hybrid database setup
python chatmind/pipeline/loading/load_hybrid.py --check-only

# Check pipeline dependencies
python scripts/check_pipeline_dependencies.py
```

## 📁 Directory Structure

```
chatmind/pipeline/
├── __init__.py
├── config.py              # Environment configuration
├── requirements.txt       # Pipeline dependencies
├── run_pipeline.py       # Main orchestrator
├── env.example          # Environment template
├── .env                 # Your environment (gitignored)
├── activate_pipeline.sh # Environment activation
├── activate_pipeline.bat
├── README.md
└── pipeline_env/        # Virtual environment
```

## 🔧 Environment Configuration

### Required Variables

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Qdrant Configuration
QDRANT_URL=http://localhost:6335
QDRANT_COLLECTION=chatmind_embeddings

# Pipeline Settings
PIPELINE_DEBUG=True
PIPELINE_LOG_LEVEL=INFO
```

### Optional Variables

```bash
# OpenAI Configuration (inherited from root .env if not set)
OPENAI_API_KEY=your_openai_api_key

# Pipeline-specific overrides
PIPELINE_MODEL_NAME=gpt-4-turbo
PIPELINE_MAX_TOKENS=4000
```

## 🏗️ Pipeline Components

### Core Processing Steps

1. **Ingestion** (`ingestion/`) - Data extraction and flattening
2. **Chunking** (`chunking/`) - Semantic text chunking
3. **Embedding** (`embedding/`) - Vector embeddings generation
4. **Clustering** (`clustering/`) - Content clustering
5. **Tagging** (`tagging/`) - Content tagging and classification
6. **Chat Summarization** (`chat_summarization/`) - Chat-level summaries
7. **Cluster Summarization** (`cluster_summarization/`) - Cluster summaries
8. **Positioning** (`positioning/`) - 2D coordinates + embeddings
9. **Similarity** (`similarity/`) - Similarity calculations
10. **Loading** (`loading/`) - Hybrid Neo4j + Qdrant database loading

### Data Flow

```
Raw Data → Ingestion → Chunking → Embedding → Clustering
    ↓
Tagging → Summarization → Positioning → Similarity → Hybrid Loading
    ↓
Neo4j (Graph Relationships) + Qdrant (Vector Embeddings)
```

## 🎯 Key Features

### Optimized Processing
- **Hash-based incremental processing** - Only process new/changed data
- **Embedding reuse** - 50%+ performance improvement for similarity calculations
- **Modular architecture** - Each step is independent and reusable

### Environment Management
- **Pipeline-specific configuration** - Override root settings when needed
- **Virtual environment isolation** - Dedicated dependencies
- **Hierarchical config loading** - Flexible configuration management

### Hybrid Data Loading
- **Neo4j for graph relationships** - Chats, messages, tags, clusters, similarities
- **Qdrant for vector embeddings** - Fast semantic search and similarity
- **Cross-reference linking** - Seamless integration between databases
- **Incremental loading** - Hash-based tracking for efficiency

## 📊 Usage Examples

### Database Management
```bash
# Start databases
./manage_databases.sh start

# Check status
./manage_databases.sh status

# View logs
./manage_databases.sh logs

# Stop databases
./manage_databases.sh stop

# Create backup
./manage_databases.sh backup
```

### Run Full Pipeline
```bash
python run_pipeline.py --local
```

### Run Specific Steps
```bash
python run_pipeline.py --steps ingestion,chunking,embedding
```

### Force Reprocessing
```bash
python run_pipeline.py --force --steps similarity
```

### Load to Hybrid Databases
```bash
# Load both Neo4j and Qdrant
python loading/load_hybrid.py

# Load Neo4j only (graph relationships)
python loading/load_graph.py

# Load Qdrant only (embeddings)
python loading/load_qdrant.py
```

## 🔍 Monitoring and Debugging

### Check Pipeline Status
```bash
# Check database status
./manage_databases.sh status

# Check database health
./manage_databases.sh health

# Verify data directories
python scripts/verify_data_directories.py

# Check dependencies
python scripts/check_pipeline_dependencies.py

# Test hybrid database connections
python loading/load_hybrid.py --check-only
```

### Debug Mode
```bash
# Enable debug logging
export PIPELINE_DEBUG=True
export PIPELINE_LOG_LEVEL=DEBUG

# Run with verbose output
python run_pipeline.py --local --force
```

## 🛠️ Development

### Adding New Steps
1. Create step directory in `chatmind/pipeline/`
2. Implement step logic with hash-based tracking
3. Update `run_pipeline.py` orchestrator
4. Add to documentation

### Environment Variables
- Add new variables to `config.py`
- Update `env.example` with documentation
- Test with different configuration scenarios

## 📈 Performance

### Optimizations Implemented
- **Hybrid architecture**: Neo4j for graphs, Qdrant for vectors
- **Fast semantic search**: <1 second vs 600+ seconds previously
- **Cross-reference linking**: Seamless integration between databases
- **Hash-based tracking**: Only process changed data
- **Incremental loading**: Skip already loaded data

### Monitoring
- Processing statistics in metadata files
- Hash tracking for incremental processing
- Performance metrics in pipeline logs

## 🔐 Security

### Environment Files
- `.env` files are gitignored for security
- Use `env.example` as template
- Pipeline-specific overrides for isolation

### Best Practices
- Never commit `.env` files
- Use different credentials for testing
- Validate configuration before processing

## 📚 Documentation

- **Pipeline Overview**: `docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md`
- **User Guide**: `docs/UserGuide.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`

## 🤝 Contributing

1. Follow the modular architecture pattern
2. Implement hash-based tracking for new steps
3. Update documentation and examples
4. Test with different environment configurations 