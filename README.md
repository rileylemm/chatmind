# ChatMind

**Organize and explore your ChatGPT conversations with AI-powered tagging and visualization.**

ChatMind automatically processes your ChatGPT export data, extracts meaningful insights, and presents them in an interactive knowledge graph. Perfect for researchers, writers, developers, and anyone who wants to make their ChatGPT conversations searchable and discoverable.

## Features

- **Smart Content Processing**: Automatically extracts and normalizes ChatGPT conversations
- **AI-Powered Tagging**: Uses GPT to intelligently tag and categorize your content
- **Interactive Visualization**: Explore your knowledge graph with Neo4j and React
- **Incremental Processing**: Only processes new data, saving time and API costs
- **Semantic Clustering**: Groups related conversations together for better insights
- **Modern Web Interface**: Clean, responsive UI for exploring your data
- **Real-time Statistics**: Dashboard shows live data from your processed content
- **RESTful API**: FastAPI backend with 25+ tested endpoints
- **Dual-Layer Graph**: Raw data + semantic layer for powerful queries
- **Flexible AI Processing**: Choose between cloud API (fast, paid) and local models (free, slower)

## Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** (for frontend)
- **Neo4j Database** (local or cloud)
- **Tagger Selection**: Choose between:
  - **Cloud API** (OpenAI): Fast, high quality, costs money (~$42-65 for 32K chunks)
  - **Local Model** (Ollama): Free, fast, excellent quality (3-4 hours for 32K chunks with Gemma-2B)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rileylemm/chatmind.git
   cd chatmind
   ```

2. **Set up Python virtual environment**
   ```bash
   # Create virtual environment
   python3 -m venv chatmind_env
   
   # Activate virtual environment
   # On macOS/Linux:
   source chatmind_env/bin/activate
   # On Windows:
   # chatmind_env\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   Edit `.env` and add your configuration:
   ```
   # Required for all setups
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   
   # Only required for Cloud API tagger
   OPENAI_API_KEY=your_openai_key_here
   ```

5. **Install frontend dependencies**
   ```bash
   cd chatmind/frontend
   npm install
   cd ../..
   ```

6. **Set up Neo4j** (if running locally)
   ```bash
   # Option 1: Docker
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   
   # Option 2: Neo4j Desktop
   # Download and install from https://neo4j.com/download/
   ```

7. **Set up your chosen tagger**
   
   **For Cloud API (OpenAI):**
   ```bash
   # Verify OpenAI API key is set
   echo $OPENAI_API_KEY
   
   # Test cloud setup
   python3 chatmind/tagger/run_tagging.py --method cloud --check-only
   ```
   
   **For Local Model (Ollama):**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama service
   ollama serve
   
   # Pull the optimized model (recommended)
   ollama pull gemma:2b
   
   # Test local setup
   python3 chatmind/tagger/run_tagging.py --method local --check-only


### Usage

1. **Add your ChatGPT export**
   ```bash
   cp your_chatgpt_export.zip data/raw/
   ```

2. **Run the processing pipeline**
   ```bash
   # Use cloud API for everything (fast, high quality, costs money)
   python run_pipeline.py --cloud
   
   # Use local models for everything (free, fast, excellent quality)
   python run_pipeline.py --local
   
   # Use default mixed approach (local embedding, cloud tagging/summarization)
   python run_pipeline.py
   
   # For development: skip expensive steps
   python run_pipeline.py --local --skip-tagging
   ```

### Pipeline Options

**Quick Start:**
- `--cloud`: Use cloud API for all AI components (embedding, tagging, summarization)
- `--local`: Use local models for all AI components (embedding, tagging, summarization)
- Default: Mixed approach (local embedding, cloud tagging/summarization)

**Development:**
- `--local --skip-tagging`: Fast iteration with local models
- `--cloud --skip-summarization`: Test cloud setup without expensive steps
- `--check-only`: Preview what will be processed
- `--force-reprocess`: Reprocess everything from scratch

3. **Start the backend API server**
   ```bash
   # Option 1: Using the startup script (recommended)
   python scripts/start_api.py
   
   # Option 2: Manual start
   cd chatmind/api
   python3 run.py
   ```

4. **Start the frontend development server**
   ```bash
   cd chatmind/frontend
   npm run dev
   ```

5. **Open the application**
   - Frontend: http://localhost:5173 (Vite dev server)
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs (Swagger UI)

## Backend API

The ChatMind API is built with **FastAPI** and provides a clean, modern REST API for accessing your knowledge graph data.

**Quick Start:**
```bash
# Start the API
python scripts/start_api.py

# Or manually
cd chatmind/api
python3 run.py
```

**Key Features:**
- **25+ Tested Endpoints** with comprehensive error handling
- **Interactive API Docs** at `/docs` (Swagger UI)
- **Real-time Statistics** and dashboard data
- **Dual-Layer Graph Support** for raw + semantic data
- **Advanced Search** and filtering capabilities

**API Documentation:** See [API Documentation](docs/API_DOCUMENTATION.md) for complete endpoint reference.

## Project Structure

```
chatmind/
├── api/                    # FastAPI backend
├── data_ingestion/         # ChatGPT export processing
├── embedding/              # Semantic clustering
├── tagger/                 # AI-powered tagging
├── neo4j_loader/          # Graph database loading
├── frontend/              # React web interface
├── scripts/               # Utility scripts and tests
└── docs/                  # Documentation
```

## Documentation

- **[User Guide](docs/UserGuide.md)** - Complete setup and usage instructions
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Enhanced Tagging System](docs/ENHANCED_TAGGING_SYSTEM.md)** - AI-powered tagging with cloud/local options
- **[Dual Layer Graph Strategy](docs/DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)** - Architecture and implementation
- **[Pipeline Overview](docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md)** - Processing pipeline details
- **[Neo4j Query Guide](docs/NEO4J_QUERY_GUIDE.md)** - Database query reference

## Testing & Quality Assurance

- **✅ API Endpoints**: 25 endpoints tested with 100% pass rate
- **✅ Dual Layer Graph**: 7 comprehensive tests covering all layers
- **✅ Neo4j Queries**: All documented queries tested and verified
- **✅ Pipeline Processing**: Incremental processing and data integrity

**Test Scripts:** See [User Guide](docs/UserGuide.md) for testing instructions.

## Current Development Status

### Completed & Production Ready

**Backend Infrastructure:**
- **FastAPI Backend**: 25+ tested endpoints with comprehensive error handling
- **Data Pipeline**: Complete ChatGPT export processing with incremental updates
- **AI-Powered Tagging**: Intelligent content categorization using GPT
- **Semantic Clustering**: Advanced embedding and clustering system
- **Neo4j Integration**: Dual-layer graph strategy with raw + semantic data
- **Cost Tracking**: Real-time API usage monitoring and cost analysis

**Frontend Foundation:**
- **Modern Tech Stack**: React 19, TypeScript, Tailwind CSS, Vite
- **Dashboard**: Real-time statistics with live API integration
- **Graph Explorer**: Interactive knowledge graph visualization
- **API Integration**: React Query for efficient data fetching
- **Responsive Layout**: Header, sidebar, and routing structure

### Currently In Development

**Frontend Features:**
- **Messages Interface**: Individual message viewing and search
- **Analytics Dashboard**: Advanced charts and data visualization
- **Tag Management**: Tag browsing, editing, and relationship exploration
- **Data Lake Explorer**: Raw data browsing and export capabilities
- **Settings Panel**: User preferences and system configuration

**Enhanced Functionality:**
- **Advanced Search**: Multi-criteria search with filters
- **Export Features**: Data export in various formats
- **User Preferences**: Customizable interface and display options

### Next Steps & Roadmap

## 1. Frontend: Complete Core Features

**Priority:** High  
**Focus:** Complete the user interface to make the powerful backend accessible and enjoyable to use.

**Key Milestones:**
- **Messages Interface**: Paginated, searchable view of all messages by chat
- **Analytics Dashboard**: Recharts showing cost trends, top tags, cluster count over time
- **Tag Explorer**: Tree-style or force-directed graph of tag relationships
- **Data Lake Interface**: Tabular/raw view of JSONL or clusters with filters
- **Graph Interactivity**: Expand-on-click, node details, semantic layer toggles
- **Responsive UI**: Refactor components to support tablets/phones
- **User Settings**: Dark mode, tag list source, cluster granularity slider

---

## 2. Enhanced Semantic Intelligence

**Priority:** Medium  
**Focus:** Leverage existing clustering and tagging to provide deeper insights.

**Features:**
- **Tag Relationship Graph**: Build tag–tag co-occurrence network for insights
- **Topic Drift Detection**: Detect when conversations veer off-topic
- **Conversation Embedding Summaries**: Represent each chat as an embedding for chat-to-chat similarity search
- **RAG Style Search**: Semantic + lexical combo search with highlight matches

---

## 3. Data Export & Portability

**Priority:** Medium  
**Focus:** Enable users to use their data in external tools and formats.

**Features:**
- **Export tagged conversations** as JSON, CSV, or markdown
- **Export graph data** (e.g., nodes.csv + edges.csv)
- **Generate static reports**: "Top 10 tags," "Cluster summaries," "Cost by chat"

---

## 4. Real-Time & Scheduled Updates

**Priority:** Medium  
**Focus:** Automate data processing for a "set it and forget it" experience.

**Tasks:**
- **Add watcher**: Auto-run pipeline when new ZIPs appear in `data/raw/`
- **Optional scheduler** (e.g. cron or APScheduler) for nightly runs
- **Frontend alert** if new data was processed

---

## 5. Active Learning & Feedback Loops

**Priority:** Lower (experimental)  
**Focus:** Make the system learn and improve from user interaction.

**Features:**
- **User tag approval/rejection**: Retrain local model or fine-tune prompts
- **Tag suggestion interface**: Allow adding to `tags_master_list.json`
- **Highlight "unknown" or "weak" clusters** for user curation

---

## 6. Developer Experience & Extensibility

**Priority:** Ongoing  
**Focus:** Keep the codebase clean and easy to contribute to.

**Tasks:**
- **Generate pyproject.toml** and move toward modern Python packaging
- **Create reusable GraphDB interface layer** (for other projects to hook into)
- **Optional plugin system** for extra graph transforms or taggers
- **Add CLI** (via typer) for key pipeline and graph tasks

---

## Stretch Goals (Long-Term)
- **Natural Language Search Interface**: "Show me chats about vector databases tagged 'AI' and 'Neo4j'"
- **Multi-Model Support**: Compare responses from different GPT versions
- **Visual History Map**: Timeline or map-style view of evolving conversations
- **User accounts + session storage** for multi-user deployments (e.g. internal team dashboards)
- **3D Graph Interface**: Immersive 3D visualization using `react-force-graph-3d` ([Plan](docs/dev_plans/3d_graph_interface_plan.md))



## Utilities

- **[Graph Utilities](chatmind/utilities/UTILITIES.md)** - Database maintenance and enhancement scripts
  - `create_has_chunk_relationships.py` - Link messages to semantic chunks
  - `create_chat_similarity.py` - Create chat similarity relationships

## Configuration

**Tag Setup:**
```bash
# Quick setup (recommended)
python scripts/setup_tags.py
```

**Processing Options:**
- **Incremental processing**: Only processes new data
- **Force reprocess**: `python run_pipeline.py --force-reprocess`
- **Skip specific steps**: `python run_pipeline.py --skip-tagging`
- **Method selection**: `--cloud` for all cloud API, `--local` for all local models
- **Development mode**: `--local --skip-tagging` for fast iteration

**Detailed Configuration:** See [User Guide](docs/UserGuide.md) for complete setup instructions.

## Understanding Your Data

**Processing Pipeline:**
1. **Data Ingestion**: Extracts conversations from ChatGPT ZIP exports
2. **Embedding & Clustering**: Groups similar messages using AI
3. **Tagging**: Automatically tags clusters with relevant categories
4. **Graph Loading**: Creates interactive knowledge graph in Neo4j

**Data Files:**
- `data/processed/chats.jsonl`: Extracted conversations
- `data/embeddings/chunks_with_clusters.jsonl`: Clustered messages
- `data/processed/tagged_chunks.jsonl`: Tagged content
- `data/tags/tags_master_list.json`: Tag definitions
- `data/cost_tracker.db`: API cost tracking database

**Dashboard Statistics:** Real-time data from your processed content including chats, messages, tags, costs, and clusters.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/rileylemm/chatmind/issues) - Report bugs, request features, or suggest improvements
- **Discussions**: [GitHub Discussions](https://github.com/rileylemm/chatmind/discussions) - Ask questions, share setups, or join community discussions
- **Documentation**: [User Guide](docs/UserGuide.md) - Complete setup and usage instructions

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Visualizations powered by [Cytoscape.js](https://cytoscape.org/)
- Frontend built with [React](https://reactjs.org/) and [TypeScript](https://www.typescriptlang.org/)
- Graph database powered by [Neo4j](https://neo4j.com/) 