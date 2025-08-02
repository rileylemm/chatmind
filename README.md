# ChatMind - AI-Powered Conversation Memory System

> **Transform your ChatGPT conversations into a searchable, visual knowledge graph**

ChatMind processes ChatGPT exports into a comprehensive knowledge graph with semantic search, clustering, and visualization capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker (for Neo4j)
- Ollama (for local AI models)

### Installation
```bash
# Clone repository
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

### Local AI Setup
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Gemma 2B model
ollama pull gemma:2b

# Start Ollama service
ollama serve
```

### Run Pipeline
```bash
# Activate environment
source chatmind_env/bin/activate

# Run full pipeline with local models (free)
python3 chatmind/pipeline/run_pipeline.py

# Or with cloud API (faster, costs money)
python3 chatmind/pipeline/run_pipeline.py --embedding-method cloud --tagging-method cloud --summarization-method cloud
```

### Start Services
```bash
# Start Neo4j and API services
python3 scripts/start_services.py

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Neo4j: http://localhost:7474
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

### 🔧 Recent Fixes
- Data lake structure cleanup
- Chat ID consistency fixes
- Neo4j authentication improvements
- File reference corrections

---

## 🏗️ Architecture

### Modular Pipeline
The system uses a modular, incremental processing pipeline:

1. **Data Ingestion** - Extract and flatten ChatGPT exports
2. **Semantic Chunking** - Break messages into meaningful segments
3. **Embedding Generation** - Create vector representations
4. **Clustering** - Group similar content together
5. **Auto-Tagging** - Apply semantic tags to content
6. **Summarization** - Generate summaries for chats and clusters
7. **Positioning** - Create 2D coordinates for visualization
8. **Similarity Calculation** - Find related content
9. **Graph Loading** - Import into Neo4j for exploration

### Dual Layer Graph
- **Chat Layer**: Individual conversations and messages
- **Cluster Layer**: Semantic groupings and topics
- **Cross-Layer Connections**: Links between chats and clusters

### Smart Features
- **Incremental Processing**: Only processes new data
- **Embedding Reuse**: Optimizes similarity calculations
- **Hash-Based Tracking**: Ensures data integrity
- **Local/Cloud Options**: Choose processing method

---

## 🎯 Key Features

### 🔍 Intelligent Search
- **Semantic Search**: Find content by meaning, not just keywords
- **Tag-Based Filtering**: Filter by topics, categories, and themes
- **Similarity Discovery**: Find related conversations and topics
- **Cross-Layer Navigation**: Move between chats and clusters

### 📊 Advanced Analytics
- **Topic Clustering**: Automatic grouping of related content
- **Conversation Analysis**: Understand patterns in your chats
- **Tag Coverage**: See what topics you discuss most
- **Similarity Networks**: Visualize content relationships

### 🎨 Rich Visualization
- **Interactive Graph**: Explore your knowledge network
- **Dual Layer View**: Switch between chat and cluster perspectives
- **Real-Time Filtering**: Focus on specific topics or time periods
- **Responsive Design**: Works on desktop and mobile

### ⚡ Performance Optimized
- **Local AI Models**: Process data without sending to cloud
- **Incremental Updates**: Only process new data
- **Embedding Reuse**: Avoid duplicate computations
- **Smart Caching**: Dramatically improve performance

---

## 🗂️ Data Structure

### Input
Place your ChatGPT exports (ZIP files) in `data/raw/`:
```
data/raw/
├── chatgpt_export_2024_01_01.zip
├── chatgpt_export_2024_01_15.zip
└── ...
```

### Output
Pipeline creates organized data in `data/processed/`:
```
data/processed/
├── ingestion/
│   ├── chats.jsonl                # Flattened chat data
│   ├── processed_zip_hashes.pkl   # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
├── chunking/
│   ├── chunks.jsonl               # Semantic chunks
│   ├── processed_chat_hashes.pkl  # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
├── embedding/
│   ├── embeddings.jsonl           # Chunk embeddings
│   ├── processed_chunk_hashes.pkl # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
├── clustering/
│   ├── clustered_embeddings.jsonl # Semantic clusters
│   ├── processed_embedding_hashes.pkl # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
├── tagging/
│   ├── chunk_tags.jsonl           # Tagged chunks
│   ├── processed_chunk_hashes.pkl # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
├── cluster_summarization/
│   ├── local_enhanced_cluster_summaries.json # Cluster summaries
│   ├── processed_cluster_hashes.pkl # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
├── chat_summarization/
│   ├── local_enhanced_chat_summaries.json # Chat summaries
│   ├── processed_chat_hashes.pkl  # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
├── positioning/
│   ├── chat_positions.jsonl       # Chat coordinates
│   ├── cluster_positions.jsonl    # Cluster coordinates
│   ├── chat_summary_embeddings.jsonl  # Reused for similarity
│   ├── cluster_summary_embeddings.jsonl  # Reused for similarity
│   ├── processed_chat_hashes.pkl  # Hash tracking for incremental processing
│   ├── processed_cluster_hashes.pkl # Hash tracking for incremental processing
│   └── metadata.json              # Processing statistics and metadata
└── similarity/
    ├── chat_similarities.jsonl    # Chat similarity relationships
    ├── cluster_similarities.jsonl # Cluster similarity relationships
    ├── chat_similarity_hashes.pkl # Hash tracking for incremental processing
    ├── cluster_similarity_hashes.pkl # Hash tracking for incremental processing
    └── metadata.json              # Processing statistics and metadata
```

---

## 🚀 Usage Examples

### Basic Pipeline
```bash
# Run full pipeline with local models
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

### Adding New Data
```bash
# Add new ZIP files to data/raw/
cp new_export.zip data/raw/

# Run pipeline - only new data will be processed
python3 chatmind/pipeline/run_pipeline.py
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

### Cost Comparison
- **Local Models**: $0 (free processing)
- **Cloud API**: ~$57-100 for full pipeline
- **Mixed**: Varies based on method selection

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

## 🔍 Troubleshooting

### Common Issues

#### Neo4j Connection Error
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Verify credentials in .env
cat .env | grep NEO4J

# Test connection
python3 -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'your_neo4j_password_here')); driver.verify_connectivity()"
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

---

## 📚 Documentation

- **[User Guide](docs/UserGuide.md)** - Complete setup and usage instructions
- **[Pipeline Overview](docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md)** - Detailed pipeline architecture
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Backend API reference
- **[Dual Layer Graph Strategy](docs/DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)** - Graph design details
- **[Enhanced Tagging System](docs/ENHANCED_TAGGING_SYSTEM.md)** - Tagging system overview
- **[Local Model Setup](docs/LOCAL_MODEL_SETUP.md)** - Local AI model configuration

---

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd ai_memory

# Create virtual environment
python3 -m venv chatmind_env
source chatmind_env/bin/activate

# Install dependencies
pip install -r chatmind/pipeline/requirements.txt

# Set up environment
cp env.example .env
```

### Testing
```bash
# Test API endpoints
python3 scripts/test_api_endpoints.py

# Test dual layer implementation
python3 scripts/test_dual_layer.py

# Test Neo4j queries
python3 scripts/test_neo4j_queries.py
```

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for all functions
- Include type hints where appropriate

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** for GPT models and API
- **Ollama** for local model serving
- **Neo4j** for graph database
- **UMAP** and **HDBSCAN** for clustering
- **React** and **D3.js** for visualization

---

*ChatMind transforms your ChatGPT conversations into a powerful, searchable knowledge graph. Whether you're a researcher, writer, or just curious about your conversation patterns, ChatMind helps you discover insights in your AI interactions.* 