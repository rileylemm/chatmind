# ChatMind - AI Memory System

## 🧠 Intelligent ChatGPT Conversation Analysis

ChatMind is a powerful AI memory system that transforms your ChatGPT conversations into a searchable, analyzable knowledge graph with semantic search capabilities.

### ✨ Key Features

- **🔍 Semantic Search**: Find conversations by meaning, not just keywords
- **📊 Graph Visualization**: Interactive exploration of conversation relationships
- **🏷️ Auto-Tagging**: AI-powered semantic categorization
- **📈 Analytics Dashboard**: Insights into your conversation patterns
- **🔄 Incremental Processing**: Only process new data, save time and costs
- **🏗️ Hybrid Architecture**: Neo4j (graph) + Qdrant (vectors) for optimal performance

### 🏗️ Architecture

ChatMind uses a **hybrid database architecture** combining the best of both worlds:

- **Neo4j**: Rich graph relationships, semantic tags, clustering, metadata
- **Qdrant**: Fast vector search for semantic similarity (chunks + clusters + chat summaries)
- **Cross-References**: Seamless linking between graph and vector data

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- OpenAI API key (for cloud processing)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ai_memory
cp env.example .env
# Edit .env with your configuration
```

### 2. Start Databases
```bash
# Start from repo root
docker compose up -d neo4j qdrant
# or
make up
```

### 3. Install Dependencies
```bash
# Pipeline dependencies
cd chatmind/pipeline
python -m venv pipeline_env
source pipeline_env/bin/activate
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

### 4. Setup Tag Master List
```bash
# Navigate to the tags directory
cd data/tags_masterlist/

# Rename the generic tags list to your personal master list
cp generic_tags_list.json tags_master_list.json

# Edit tags_master_list.json to add your own normalized tags
# The file contains 175 generic tags covering emotions, time, location, 
# relationships, activities, health, technology, business, education, etc.

# Optional: Use the comprehensive list for maximum coverage
# cp comprehensive_generic_tags.json tags_master_list.json
```

### 5. Process Your Data
```bash
# Add your ChatGPT exports to data/raw/
# Run the pipeline (local models)
chatmind --local
# or
cd chatmind/pipeline && source pipeline_env/bin/activate && python run_pipeline.py --local
```

### 6. Start the Application
```bash
# Start API server (from repo root)
cd chatmind/api && python main.py

# Start minimal frontend (in another terminal)
cd chatmind/frontend && npm run dev
```

## 📁 Project Structure

```
ai_memory/
├── chatmind/           # Main application
│   ├── api/           # FastAPI backend
│   ├── pipeline/      # Data processing pipeline
│   └── frontend/      # React frontend
├── data/              # Data storage
│   ├── raw/          # ChatGPT exports
│   ├── processed/    # Pipeline outputs
│   └── tags_masterlist/ # Tag master lists
│       ├── tags_master_list.json          # Your personal master list
│       ├── generic_tags_list.json         # Basic generic tags (175 tags)
│       └── comprehensive_generic_tags.json # Comprehensive generic tags (366 tags)
├── docs/             # Documentation
│   └── local/        # Project-specific docs
└── scripts/          # Utilities and tests
```

### 🏷️ Tag Master Lists

ChatMind provides three tag list options:

- **`tags_master_list.json`**: Your personal master list (3,200+ normalized tags)
- **`generic_tags_list.json`**: Basic generic tags covering common categories (175 tags)
- **`comprehensive_generic_tags.json`**: Extensive generic tags for maximum coverage (366 tags)

### 🔍 Search Capabilities

ChatMind provides hierarchical semantic search across all data levels:

- **Chunk Search**: Find specific content and messages
- **Cluster Search**: Discover related themes and topics
- **Chat Summary Search**: Find similar conversations and discussions
- **Tag Search**: Filter by semantic categories and topics

The generic lists include tags for:
- **Emotions**: #happy, #sad, #excited, #frustrated, etc.
- **Time**: #morning, #deadline, #urgent, #routine, etc.
- **Location**: #home, #office, #school, #hospital, etc.
- **Activities**: #work, #study, #exercise, #traveling, etc.
- **Technology**: #software, #hardware, #mobile, #desktop, etc.
- **Business**: #startup, #corporate, #freelance, #sales, etc.
- **And many more categories...**

## 🔄 Pipeline Overview

The ChatMind pipeline processes your ChatGPT conversations through these steps:

1. **Ingestion**: Extract and flatten conversation data
2. **Chunking**: Create semantic chunks of messages
3. **Embedding**: Generate vector representations
4. **Clustering**: Group similar content together
5. **Tagging**: Apply semantic tags and categories
6. **Tag Post-Processing**: Normalize and map tags to master list
7. **Summarization**: Generate AI summaries
8. **Positioning**: Create 2D coordinates for visualization
9. **Similarity**: Calculate relationships between content
10. **Loading**: Load into hybrid Neo4j + Qdrant architecture (creates tag-chunk relationships)

### 🏷️ Tag Optimization

After running the pipeline, you can optimize your tag master list:

```bash
# Auto-add frequently occurring tags (3+ occurrences)
cd chatmind/pipeline
python tagging/post_process_tags.py --auto-add --auto-add-threshold 3

# Or manually review missing tags
python tagging/post_process_tags.py --check-only
cat ../../data/processed/tagging/missing_tags_report.json

# Edit data/tags_masterlist/tags_master_list.json to add custom tags
# Re-run post-processing to normalize tags
```

### 🔍 Database Loading

Load your processed data into the hybrid database architecture:

```bash
# Load into both Neo4j and Qdrant with cross-references
cd chatmind/pipeline
python loading/load_hybrid.py

# Or load databases separately
python loading/load_graph.py    # Neo4j (graph relationships)
python loading/load_qdrant.py   # Qdrant (vector embeddings)
```

## 🎯 Use Cases

- **Research & Analysis**: Discover patterns in your conversations
- **Content Search**: Find specific discussions by meaning
- **Knowledge Management**: Organize and explore your AI interactions
- **Learning Insights**: Track your learning progress and topics
- **Content Creation**: Extract insights for writing and presentations

## 📚 Documentation

- **[AI Entry Point](docs/AI_ENTRY_POINT.md)** - Quick guide for AI assistants and agents
- **[User Guide](docs/UserGuide.md)** - Setup and usage instructions
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Backend API reference
- **[Pipeline Overview](docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md)** - Data processing architecture
- **[Neo4j Query Guide](docs/NEO4J_QUERY_GUIDE.md)** - Database query reference
- **[Dual Layer Strategy](docs/DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)** - Architecture details

## 🛠️ Development

### Quick Dev Setup
```bash
# (optional) Install pre-commit hooks
pipx install pre-commit || pip install pre-commit
pre-commit install

# Start services and run pipeline
make up
chatmind --local

# Run API and Frontend
make api
make frontend
```

### Local Development
```bash
# Setup development environment
cd chatmind/pipeline
source pipeline_env/bin/activate
python -m pip install -r requirements.txt

# Run tests
cd ../../scripts
python test_neo4j_queries.py
python test_api_endpoints.py
```

### Adding New Data
```bash
# Add new ChatGPT exports to data/raw/
# Run pipeline (only processes new data)
cd chatmind/pipeline
source pipeline_env/bin/activate
python run_pipeline.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details. See [NOTICE](NOTICE) for attribution. Please also review our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md).

## 🙏 Acknowledgments

- Built with [Neo4j](https://neo4j.com/) for graph database
- Powered by [Qdrant](https://qdrant.tech/) for vector search
- Frontend built with [React](https://reactjs.org/) and [D3.js](https://d3js.org/)
- Backend powered by [FastAPI](https://fastapi.tiangolo.com/)

---

**ChatMind** - Transform your ChatGPT conversations into actionable insights! 🚀

## 🗺️ Roadmap (Initial Open Source)

- Minimal CLI-inspired frontend MVP (done)
- Add ingestion for Markdown files (.md) to pipeline
- Batch processing controls for pipeline runs
- Expand data sources (Slack export, Notion export)
- Improve API ergonomics and pagination
- Iterative UI improvements on tags/search/cluster flows 