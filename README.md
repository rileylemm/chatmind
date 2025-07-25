# ChatMind

**Organize and explore your ChatGPT conversations with AI-powered tagging and visualization.**

ChatMind automatically processes your ChatGPT export data, extracts meaningful insights, and presents them in an interactive knowledge graph. Perfect for researchers, writers, developers, and anyone who wants to make their ChatGPT conversations searchable and discoverable.

## ✨ Features

- **🔍 Smart Content Processing**: Automatically extracts and normalizes ChatGPT conversations
- **🏷️ AI-Powered Tagging**: Uses GPT to intelligently tag and categorize your content
- **📊 Interactive Visualization**: Explore your knowledge graph with Neo4j and React
- **🔄 Incremental Processing**: Only processes new data, saving time and API costs
- **🎯 Semantic Clustering**: Groups related conversations together for better insights
- **📱 Modern Web Interface**: Clean, responsive UI for exploring your data
- **📈 Real-time Statistics**: Dashboard shows live data from your processed content
- **🔌 RESTful API**: FastAPI backend for data access and management

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+** (for frontend)
- **Neo4j Database** (local or cloud)
- **OpenAI API Key**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/chatmind.git
   cd chatmind
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
3. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   Edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

4. **Install frontend dependencies**
   ```bash
   cd chatmind/frontend
   npm install
   cd ../..
   ```

5. **Set up Neo4j** (if running locally)
   ```bash
   # Option 1: Docker
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   
   # Option 2: Neo4j Desktop
   # Download and install from https://neo4j.com/download/
   ```

### Usage

1. **Add your ChatGPT export**
   ```bash
   cp your_chatgpt_export.zip data/raw/
   ```

2. **Run the processing pipeline**
   ```bash
   python run_pipeline.py
   ```

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

## 🔧 Backend API

The ChatMind API is built with **FastAPI** and provides a clean, modern REST API for accessing your knowledge graph data.

### Features

- **Clean Architecture**: Separated concerns with dedicated service layers
- **Type Safety**: Full Pydantic model validation
- **Auto Documentation**: Interactive API docs at `/docs`
- **Error Handling**: Comprehensive error responses with proper HTTP status codes
- **CORS Support**: Configured for frontend development
- **Health Monitoring**: Built-in health checks

### Quick Start

```bash
# Start the API
python scripts/start_api.py

# Or manually
cd chatmind/api
python3 run.py
```

### API Endpoints

- **`GET /api/stats/dashboard`** - Get real-time dashboard statistics
- **`GET /api/health`** - Health check endpoint
- **`GET /`** - API root endpoint

### Real Data Sources

The backend connects to your actual processed data:

- **Chat Statistics**: Reads from `data/processed/chats.jsonl`
- **Tag Information**: Reads from `data/tags/tags_master_list.json`
- **Cost Tracking**: Reads from `data/cost_tracker.db`
- **Cluster Data**: Reads from `data/embeddings/cluster_summaries.json`

### API Development

```bash
# Start API server with auto-reload
cd chatmind/api
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test API endpoints
curl http://localhost:8000/api/stats/dashboard
curl http://localhost:8000/api/health
```

## 📁 Project Structure

```
chatmind/
├── api/                    # FastAPI backend with real data endpoints
├── data_ingestion/         # ChatGPT export processing
├── embedding/              # Semantic clustering
├── tagger/                 # AI-powered tagging
├── neo4j_loader/          # Graph database loading
├── frontend/              # React web interface
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## 🔧 Configuration

### Tag Master List

The system uses a master list of tags for consistent categorization. 

#### 🚀 **Quick Setup:**
```bash
# Option 1: Use the setup script (recommended)
python scripts/setup_tags.py

# Option 2: Manual copy
cp data/tags/tags_master_list_generic.json data/tags/tags_master_list.json
```

#### 📝 **Customization Options:**
- **Start with generic tags** - Use the provided 500-tag list as a starting point
- **Edit your personal list** - Modify `data/tags/tags_master_list.json` to match your interests
- **Let the system auto-expand** - The pipeline will suggest new tags based on your content
- **Review missing tags** - Check `data/interim/missing_tags_report.json` after processing

#### 🔒 **Privacy Note:**
Your personal tag list (`data/tags/tags_master_list.json`) is excluded from git to keep your custom tags private. The generic list is included for new users.

#### 📊 **Check Your Setup:**
```bash
# See current tag list status
python scripts/setup_tags.py --info
```

### Processing Options

- **Incremental processing**: Only processes new data
- **Force reprocess**: `python run_pipeline.py --force-reprocess`
- **Skip specific steps**: `python run_pipeline.py --skip-tagging`

## 📊 Understanding Your Data

### Processing Pipeline

1. **Data Ingestion**: Extracts conversations from ChatGPT ZIP exports
2. **Embedding & Clustering**: Groups similar messages using AI
3. **Tagging**: Automatically tags clusters with relevant categories
4. **Graph Loading**: Creates interactive knowledge graph in Neo4j

### Data Files

- `data/processed/chats.jsonl`: Extracted conversations
- `data/embeddings/chunks_with_clusters.jsonl`: Clustered messages
- `data/processed/tagged_chunks.jsonl`: Tagged content
- `data/tags/tags_master_list.json`: Tag definitions
- `data/cost_tracker.db`: API cost tracking database

### Real-time Statistics

The dashboard displays live data from your processed content:

- **Total Chats**: Number of conversations processed
- **Total Messages**: Count of all messages across all chats
- **Active Tags**: Number of tags in your master list
- **Total Cost**: Actual API costs from your usage
- **Total Clusters**: Number of semantic clusters created
- **Total Calls**: Number of API calls made during processing

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/chatmind/issues)
- **Documentation**: [User Guide](docs/UserGuide.md)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/chatmind/discussions)

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Visualizations powered by [Cytoscape.js](https://cytoscape.org/)
- Frontend built with [React](https://reactjs.org/) and [TypeScript](https://www.typescriptlang.org/)
- Graph database powered by [Neo4j](https://neo4j.com/) 