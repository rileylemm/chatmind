# ChatMind User Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker (for Neo4j)
- Ollama (for local models)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd ai_memory

# Create virtual environment
python3 -m venv chatmind_env
source chatmind_env/bin/activate

# Install dependencies
pip install -r chatmind/pipeline/requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your API keys and Neo4j credentials
```

### Local Model Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Gemma 2B model
ollama pull gemma:2b

# Start Ollama service
ollama serve
```

### Neo4j Setup
```bash
# Start Neo4j with Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_neo4j_password_here \
  neo4j:latest

# Or use the provided script
python3 scripts/start_services.py
```

---

## 🔄 Pipeline Usage

### Full Pipeline (Recommended)
```bash
# Activate environment
source chatmind_env/bin/activate

# Run full pipeline with local models (free)
python3 chatmind/pipeline/run_pipeline.py

# Run with cloud API (faster, costs money)
python3 chatmind/pipeline/run_pipeline.py --embedding-method cloud --tagging-method cloud --summarization-method cloud
```

### Individual Steps
```bash
# Run specific steps
python3 chatmind/pipeline/run_pipeline.py --steps ingestion,chunking,embedding

# Force reprocess specific step
python3 chatmind/pipeline/run_pipeline.py --steps similarity --force

# Check what needs processing
python3 chatmind/pipeline/run_pipeline.py --check-only
```

### Step-by-Step Processing
```bash
# 1. Data ingestion
python3 chatmind/pipeline/run_pipeline.py --steps ingestion

# 2. Semantic chunking
python3 chatmind/pipeline/run_pipeline.py --steps chunking

# 3. Embedding generation
python3 chatmind/pipeline/run_pipeline.py --steps embedding

# 4. Clustering
python3 chatmind/pipeline/run_pipeline.py --steps clustering

# 5. Tagging
python3 chatmind/pipeline/run_pipeline.py --steps tagging

# 6. Tag post-processing
python3 chatmind/pipeline/run_pipeline.py --steps tag_post_processing

# 7. Cluster summarization
python3 chatmind/pipeline/run_pipeline.py --steps cluster_summarization

# 8. Chat summarization
python3 chatmind/pipeline/run_pipeline.py --steps chat_summarization

# 9. Positioning (generates embeddings for reuse)
python3 chatmind/pipeline/run_pipeline.py --steps positioning

# 10. Similarity calculation (uses saved embeddings)
python3 chatmind/pipeline/run_pipeline.py --steps similarity

# 11. Neo4j loading
python3 chatmind/pipeline/run_pipeline.py --steps loading
```

---

## 📊 Current Status

### ✅ Successfully Implemented
- **Complete pipeline** with all steps working
- **Incremental processing** with hash-based tracking
- **Dual layer graph** architecture
- **Local and cloud processing** options
- **Embedding reuse optimization** for performance
- **Recent fixes applied** for data consistency

### 🔧 Recent Fixes Applied
- **Data Lake Structure**: Fixed duplicate data lake creation
- **Chat ID Consistency**: All chats now have unique IDs
- **Neo4j Authentication**: Proper credential handling
- **File References**: Correct tagged chunks file reference
- **Hash Synchronization**: Fixed similarity calculation tracking

---

## 🗂️ Data Structure

### Input Data
Place your ChatGPT exports (ZIP files) in `data/raw/`:
```
data/raw/
├── chatgpt_export_2024_01_01.zip
├── chatgpt_export_2024_01_15.zip
└── ...
```

### Processed Data
Pipeline creates organized data in `data/processed/`:
```
data/processed/
├── ingestion/chats.jsonl          # Flattened chat data
├── chunking/chunks.jsonl          # Semantic chunks
├── embedding/embeddings.jsonl     # Chunk embeddings
├── clustering/clustered_embeddings.jsonl  # Semantic clusters
├── tagging/chunk_tags.jsonl       # Tagged chunks
├── cluster_summarization/local_enhanced_cluster_summaries.json  # Cluster summaries
├── chat_summarization/local_enhanced_chat_summaries.json       # Chat summaries
├── positioning/
│   ├── chat_positions.jsonl       # Chat coordinates
│   ├── cluster_positions.jsonl    # Cluster coordinates
│   ├── chat_summary_embeddings.jsonl  # Reused for similarity
│   └── cluster_summary_embeddings.jsonl  # Reused for similarity
└── similarity/
    ├── chat_similarities.jsonl    # Chat similarity relationships
    └── cluster_similarities.jsonl # Cluster similarity relationships
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# OpenAI API (for cloud processing)
OPENAI_API_KEY=your_openai_api_key_here

# Neo4j Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Pipeline Settings
EMBEDDING_METHOD=local  # or cloud
TAGGING_METHOD=local    # or cloud
SUMMARIZATION_METHOD=local  # or cloud
```

### Local Model Configuration
```bash
# Ollama model to use
OLLAMA_MODEL=gemma:2b

# Ollama API endpoint
OLLAMA_API_URL=http://localhost:11434
```

---

## 🚀 Advanced Usage

### Incremental Processing
The pipeline uses hash-based tracking to only process new data:
```bash
# Add new ZIP files to data/raw/
# Run pipeline - only new data will be processed
python3 chatmind/pipeline/run_pipeline.py
```

### Force Reprocessing
```bash
# Force reprocess everything
python3 chatmind/pipeline/run_pipeline.py --force

# Force specific step
python3 chatmind/pipeline/run_pipeline.py --steps similarity --force
```

### Mixed Processing
```bash
# Use cloud for expensive operations, local for others
python3 chatmind/pipeline/run_pipeline.py \
  --embedding-method cloud \
  --tagging-method local \
  --summarization-method local
```

### Development Workflow
```bash
# Check what will be processed
python3 chatmind/pipeline/run_pipeline.py --check-only

# Run only specific steps for testing
python3 chatmind/pipeline/run_pipeline.py --steps ingestion,chunking

# Test individual components
python3 chatmind/pipeline/ingestion/extract_and_flatten.py
python3 chatmind/pipeline/chunking/chunker.py
```

---

## 🎯 Best Practices

### Performance Optimization
- **Embedding Reuse**: Positioning step generates embeddings reused by similarity calculation
- **Incremental Processing**: Only process new data using hash tracking
- **Local Models**: Use local models for development and testing
- **Cloud API**: Use cloud API for production when speed is critical

### Data Management
- **Backup Strategy**: Keep hash files unless you want to reprocess everything
- **File Organization**: Use consistent naming conventions
- **Error Recovery**: Use `--force` to reprocess failed steps
- **Monitoring**: Check metadata files for processing statistics

### Development Tips
- Start with small datasets for testing
- Use `--check-only` before running expensive operations
- Monitor hash files to understand incremental behavior
- Test individual steps before running full pipeline
- Keep environment variables updated

---

## 🔍 Troubleshooting

### Common Issues

#### Neo4j Connection Error
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Verify credentials in .env
cat .env | grep NEO4J

# Test connection
python3 -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'chatmind123')); driver.verify_connectivity()"
```

#### Ollama Connection Error
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

#### Missing Dependencies
```bash
# Reinstall dependencies
pip install -r chatmind/pipeline/requirements.txt

# Check Python version
python3 --version
```

#### Data Lake Issues
```bash
# Verify data directories exist
python3 scripts/verify_data_directories.py

# Check data lake structure
ls -la data/lake/
```

### Debug Mode
```bash
# Run with verbose output
python3 chatmind/pipeline/run_pipeline.py --verbose

# Check individual step logs
tail -f data/processed/*/metadata.json
```

---

## 📈 Performance Metrics

### Processing Times (Local Models)
- **Ingestion**: ~2-5 minutes for typical datasets
- **Chunking**: ~5-10 minutes for message processing
- **Embedding**: ~15-30 minutes for chunk embeddings
- **Clustering**: ~10-20 minutes for semantic clustering
- **Tagging**: ~1-3 hours for comprehensive tagging
- **Summarization**: ~30-60 minutes for summaries
- **Positioning**: ~5-10 minutes for coordinates
- **Similarity**: ~10-20 minutes for similarity calculations
- **Loading**: ~5-15 minutes for Neo4j import

### Resource Usage
- **Memory**: ~4GB peak during clustering
- **CPU**: Multi-threaded processing
- **Storage**: ~500MB for processed data
- **Network**: Local processing (no external calls)

### Cost Comparison
- **Local Models**: $0 (free processing)
- **Cloud API**: ~$57-100 for full pipeline
- **Mixed**: Varies based on method selection

---

## 🔮 Next Steps

### After Pipeline Completion
1. **Start Services**: `python3 scripts/start_services.py`
2. **Access Frontend**: Open http://localhost:3000
3. **Explore Graph**: Navigate to Graph Explorer
4. **Analyze Data**: Use Analytics dashboard

### Adding New Data
1. Add new ZIP files to `data/raw/`
2. Run pipeline: `python3 chatmind/pipeline/run_pipeline.py`
3. Only new data will be processed automatically

### Customization
- Modify tags in `data/tags_masterlist/tags_master_list.json`
- Adjust similarity thresholds in similarity scripts
- Customize prompts in local model scripts
- Extend pipeline with new steps

---

## 📚 Additional Resources

- [Pipeline Overview](PIPELINE_OVERVIEW_AND_INCREMENTAL.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Dual Layer Graph Strategy](DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)
- [Enhanced Tagging System](ENHANCED_TAGGING_SYSTEM.md)
- [Local Model Setup](LOCAL_MODEL_SETUP.md)

---

*This user guide provides everything needed to run the ChatMind pipeline successfully. The system is designed to be robust, efficient, and easy to use with both local and cloud processing options.*