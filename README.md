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
- **Qdrant**: Fast vector search for semantic similarity
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
cd chatmind/pipeline
docker-compose up -d
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

### 4. Process Your Data
```bash
# Add your ChatGPT exports to data/raw/
# Run the pipeline
cd chatmind/pipeline
source pipeline_env/bin/activate
python run_pipeline.py
```

### 5. Start the Application
```bash
# Start API server
cd chatmind/api
python main.py

# Start frontend (in another terminal)
cd chatmind/frontend
npm run dev
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
│   └── processed/    # Pipeline outputs
├── docs/             # Documentation
│   └── local/        # Project-specific docs
└── scripts/          # Utilities and tests
```

## 🔄 Pipeline Overview

The ChatMind pipeline processes your ChatGPT conversations through these steps:

1. **Ingestion**: Extract and flatten conversation data
2. **Chunking**: Create semantic chunks of messages
3. **Embedding**: Generate vector representations
4. **Clustering**: Group similar content together
5. **Tagging**: Apply semantic tags and categories
6. **Summarization**: Generate AI summaries
7. **Positioning**: Create 2D coordinates for visualization
8. **Similarity**: Calculate relationships between content
9. **Loading**: Load into hybrid Neo4j + Qdrant architecture

## 🎯 Use Cases

- **Research & Analysis**: Discover patterns in your conversations
- **Content Search**: Find specific discussions by meaning
- **Knowledge Management**: Organize and explore your AI interactions
- **Learning Insights**: Track your learning progress and topics
- **Content Creation**: Extract insights for writing and presentations

## 📚 Documentation

- **[User Guide](docs/UserGuide.md)** - Setup and usage instructions
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Backend API reference
- **[Pipeline Overview](docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md)** - Data processing architecture
- **[Neo4j Query Guide](docs/NEO4J_QUERY_GUIDE.md)** - Database query reference
- **[Dual Layer Strategy](docs/DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)** - Architecture details

## 🛠️ Development

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Neo4j](https://neo4j.com/) for graph database
- Powered by [Qdrant](https://qdrant.tech/) for vector search
- Frontend built with [React](https://reactjs.org/) and [D3.js](https://d3js.org/)
- Backend powered by [FastAPI](https://fastapi.tiangolo.com/)

---

**ChatMind** - Transform your ChatGPT conversations into actionable insights! 🚀 