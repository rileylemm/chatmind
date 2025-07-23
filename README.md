# ChatMind - AI Memory Pipeline

A modular pipeline that transforms ChatGPT exports into a semantic knowledge graph with interactive visualization.

## 🧭 Overview

This project ingests ChatGPT exports, processes them through semantic embedding and clustering, loads relationships into Neo4j, and provides a mindmap-style frontend for exploration.

## 🏗️ Architecture

```
ChatGPT Exports → Data Ingestion → Embedding & Clustering → Neo4j Graph → Interactive Frontend
```

## 📁 Project Structure

```
chatmind/
├── data_ingestion/          # Extract and flatten chat data
│   ├── extract_and_flatten.py
│   ├── data_lake_storage.py # Data lake storage system
│   └── chatgpt_url_mapper.py # ChatGPT URL mapping
├── embedding/               # Semantic embedding and clustering
│   └── embed_and_cluster.py
            ├── semantic_chunker/        # GPT-driven semantic chunking
            │   ├── chunker.py          # Main chunking logic
            │   ├── prompts.py          # Prompt templates
            │   ├── run_chunking.py     # Script entry point
            │   └── test_sample.json    # Sample for testing
            ├── tagger/                  # GPT-driven auto-tagging
            │   ├── tagger.py           # Main tagging logic
            │   ├── prompts.py          # Tagging prompt templates
            │   ├── run_tagging.py      # Script entry point
            │   └── test_chunks.jsonl   # Sample chunks for testing
            ├── cost_tracker/            # OpenAI API cost tracking
            │   └── tracker.py          # Cost tracking logic
            ├── neo4j_loader/           # Load data into Neo4j graph
            │   └── load_graph.py
            ├── api/                    # FastAPI backend
            │   └── main.py
            ├── frontend/               # React + Cytoscape visualization
            │   ├── src/
            │   │   ├── App.tsx        # Main visualization component
            │   │   ├── components/    # React components
            │   │   │   ├── TagFilter.tsx    # Tag filtering component
            │   │   │   └── CostTracker.tsx  # Cost tracking component
            │   │   └── index.tsx      # React entry point
            │   └── package.json
├── data/                   # Data storage
│   ├── raw/               # ChatGPT export ZIP files
│   ├── processed/         # Flattened JSONL data
│   ├── embeddings/        # Embeddings and clusters
│   └── lake/              # Data lake storage
│       ├── chats/         # Individual chat JSON files
│       ├── messages/      # Individual message JSON files
│       ├── urls/          # ChatGPT URL mappings
│       └── metadata/      # Indexes and metadata
├── run_pipeline.py        # Complete pipeline runner
├── start_services.py      # Service starter
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

1. **Setup Environment**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Copy and configure environment variables
   cp env.example .env
   # Edit .env with your Neo4j and OpenAI credentials
   ```

2. **Setup Neo4j** (if running locally)
   ```bash
   # Install Neo4j Desktop or use Docker
   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

3. **Process Data**
   ```bash
   # Place ChatGPT export ZIP files in data/raw/
   python run_pipeline.py
   ```

4. **Start Services**
   ```bash
   # Start API and frontend together
   python start_services.py
   
   # Or start individually:
   # API only: python chatmind/api/main.py
   # Frontend only: cd chatmind/frontend && npm start
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## 🔧 Configuration

Copy `env.example` to `.env` and configure:

### Required Environment Variables
- `NEO4J_URI` - Neo4j connection string (default: bolt://localhost:7687)
- `NEO4J_USER` - Neo4j username (default: neo4j)
- `NEO4J_PASSWORD` - Neo4j password (default: password)

### Optional Environment Variables
- `OPENAI_API_KEY` - For enhanced embeddings/summaries (optional)
- `DEBUG` - Enable debug logging (default: True)
- `LOG_LEVEL` - Logging level (default: INFO)

## 📊 Data Flow

1. **Ingestion**: ZIP files → content-based deduplication → JSONL
2. **Chunking**: Conversations → semantic chunks (GPT-driven or simple)
3. **Embedding**: Text chunks → semantic vectors
4. **Clustering**: Vectors → topic clusters
5. **Graph**: Clusters → Neo4j knowledge graph
6. **Visualization**: Graph → Interactive mindmap

## 🔄 Re-ingestion & Deduplication

ChatMind handles overlapping ChatGPT exports intelligently:

- **Content-Based Deduplication**: Uses SHA256 hashes of normalized chat content
- **Smart Normalization**: Excludes timestamps and metadata that change between exports
- **Persistent State**: Remembers all processed content between runs
- **Overlap Handling**: Processes all ZIP files but only adds unique conversations

**Example Workflow:**
```bash
# First export (50 conversations)
cp chat_export_1.zip data/raw/
python run_pipeline.py
# Result: 50 new conversations added

# Second export (same 50 + 10 new conversations)
cp chat_export_2.zip data/raw/
python run_pipeline.py
# Result: Only 10 new conversations added, 50 duplicates skipped
```

## 🏊 Data Lake Architecture

ChatMind implements a hierarchical data lake for deep navigation:

### **📁 Data Lake Structure**
```
data/lake/
├── chats/           # Individual chat JSON files (chat_<hash>.json)
├── messages/        # Individual message JSON files (msg_<hash>.json)
├── urls/            # ChatGPT URL mappings (conversation_id.json)
└── metadata/        # Indexes and metadata
```

### **🔗 Navigation Flow**
```
Neo4j Graph → Chat Node → Data Lake Chat → Individual Messages
```

### **🎯 API Endpoints**
- `GET /lake/chat/{chat_id}` - Get specific chat details
- `GET /lake/chat/{chat_id}/messages` - Get all messages for chat
- `GET /lake/message/{message_id}` - Get specific message details
- `GET /lake/chat/{chat_id}/urls` - Get ChatGPT URLs for chat
- `GET /lake/url/{conversation_id}` - Get URL mapping by conversation ID
- `GET /lake/urls/search?query={title}` - Search URLs by chat title

### **💡 Benefits**
- **Hierarchical Navigation**: Drill down from graph → chat → message
- **Fast Access**: Direct file-based retrieval for individual items
- **Full Context**: Complete conversation history preserved
- **Scalable**: Efficient storage for large datasets
- **Direct ChatGPT Links**: One-click access to original conversations

## 🧠 Semantic Chunking

ChatMind supports both simple and GPT-driven semantic chunking:

### **🔍 Chunking Methods**
- **Simple Chunking**: Sentence-based splitting (default)
- **Semantic Chunking**: GPT-driven intelligent splitting
- **Fallback Safety**: Automatic fallback if GPT fails

### **🎯 Semantic Chunking Benefits**
- **Better Coherence**: Chunks focus on specific topics/themes
- **Context Preservation**: Maintains conversation flow
- **Meaningful Titles**: GPT-generated descriptive titles
- **Improved Clustering**: Better semantic grouping
- **Flexible Prompts**: Multiple styles (standard, detailed, technical)

### **💡 Usage Examples**
```bash
# Use semantic chunking in pipeline
python chatmind/embedding/embed_and_cluster.py --semantic-chunking

# Standalone semantic chunking
python chatmind/semantic_chunker/run_chunking.py

# Test with sample data
python demo_semantic_chunking.py
```

### **🔄 Prompt Styles**
- **Standard**: General conversation chunking
- **Detailed**: Complex technical discussions
- **Technical**: Code-heavy conversations

## 🏷️ Auto-Tagging

ChatMind supports automatic tagging of semantic chunks using GPT:

### **🔍 Tagging Features**
- **Automatic Hashtags**: GPT-generated relevant hashtags
- **Semantic Categories**: Intelligent categorization
- **Multiple Styles**: Standard, detailed, and general prompts
- **Fallback Safety**: Automatic fallback if GPT fails
- **Rich Metadata**: Tagging model, timestamps, statistics

### **🎯 Tagging Benefits**
- **Better Organization**: Automatic content categorization
- **Improved Search**: Hashtag-based filtering and discovery
- **Semantic Understanding**: GPT-driven content analysis
- **Flexible Prompts**: Multiple tagging styles for different content
- **Statistics**: Tag frequency analysis and insights

### **💡 Usage Examples**
```bash
# Use auto-tagging in pipeline
python chatmind/embedding/embed_and_cluster.py --auto-tagging

# Standalone auto-tagging
python chatmind/tagger/run_tagging.py

# Test with sample data
python demo_auto_tagging.py
```

### **🔄 Tagging Styles**
- **Standard**: General content tagging
- **Detailed**: Technical content with comprehensive tags
- **General**: Non-technical conversation tagging

            ### **📊 Output Format**
            ```json
            {
              "chat_id": "abc123",
              "chunk_id": "abc123_semantic_0",
              "title": "Introduction to FastAPI",
              "content": "USER: I want to build a web API...",
              "tags": ["#python", "#fastapi", "#web-api", "#tutorial"],
              "category": "Web API Development",
              "tagging_model": "gpt-4",
              "tagging_timestamp": 1703123456
            }
            ```

            ## 🏷️ Tag-Based Filtering

            ChatMind supports powerful tag-based filtering for discovering and exploring content:

            ### **🔍 Filtering Features**
            - **Multi-Tag Selection**: Filter by multiple hashtags simultaneously
            - **Category Filtering**: Filter by semantic categories
            - **Search Integration**: Combine tags with text search
            - **Real-Time Updates**: Graph updates instantly when filters change
            - **Active Filter Display**: Visual indicators of current filters
            - **Clear Filters**: Easy reset to show full graph

            ### **🎯 Filtering Benefits**
            - **Content Discovery**: Find related conversations quickly
            - **Topic Focus**: Zoom in on specific areas of interest
            - **Cross-Reference**: See connections between different topics
            - **Efficient Navigation**: Skip to relevant content directly
            - **Visual Clarity**: Reduced graph complexity with focused views

            ### **💡 Usage Examples**
            ```bash
            # Filter by single tag
            Select "#python" to see all Python-related content

            # Filter by multiple tags
            Select "#python" AND "#api" to see Python API discussions

            # Filter by category
            Select "Web Development" category

            # Combined filtering
            Filter by "#python" category AND search for "FastAPI"
            ```

            ### **🔄 API Endpoints**
            - `GET /tags` - Get all available tags and categories
            - `GET /search/by-tags` - Search messages by tags/category
            - `GET /graph/filtered` - Get filtered graph data

            ### **🎨 Frontend Component**
            - **TagFilter.tsx**: React component for tag selection
            - **Multi-select dropdown**: Choose multiple tags
            - **Category dropdown**: Filter by semantic categories
            - **Search integration**: Combine with text search
            - **Active filters display**: Visual filter indicators
            - **Clear filters button**: Reset to full graph

            ## 💰 Cost Tracking

            ChatMind includes comprehensive cost tracking for OpenAI API usage:

            ### **📊 Cost Tracking Features**
            - **Real-Time Monitoring**: Track all API calls automatically
            - **Cost Calculation**: Automatic pricing based on OpenAI rates
            - **Usage Statistics**: Success rates, token usage, model breakdowns
            - **Daily Trends**: Cost trends over time
            - **Export Functionality**: JSON export for analysis
            - **API Endpoints**: REST API for frontend integration

            ### **🎯 Cost Tracking Benefits**
            - **Budget Management**: Monitor and control API costs
            - **Usage Analytics**: Understand usage patterns
            - **Performance Tracking**: Monitor success/failure rates
            - **Cost Optimization**: Identify expensive operations
            - **Usage Insights**: Token usage and model performance

            ### **💡 Usage Examples**
            ```bash
            # View cost statistics
            GET /costs/statistics

            # Get recent API calls
            GET /costs/recent?limit=20

            # View daily costs
            GET /costs/daily?days=30

            # Export cost data
            POST /costs/export
            ```

            ### **🎨 Frontend Dashboard**
            - **CostTracker.tsx**: React component for cost display
            - **Cost overview**: Total cost, calls, success rate
            - **Model breakdown**: Cost by model (GPT-4, GPT-3.5, etc.)
            - **Operation analysis**: Cost by operation (chunking, tagging)
            - **Recent activity**: Latest API calls with status
            - **Daily trends**: Cost trends over time
            - **Filtering**: Date ranges and operation filters

## 🔗 ChatGPT URL Mapping

ChatMind automatically extracts and maps ChatGPT conversation URLs:

### **🔍 URL Extraction**
- **Automatic Detection**: Scans chat content for ChatGPT URLs
- **Pattern Matching**: Supports multiple URL formats:
  - `https://chat.openai.com/c/{conversation_id}`
  - `https://chat.openai.com/share/{conversation_id}`
  - `https://chat.openai.com/chat/{conversation_id}`
- **Persistent Storage**: URLs stored in data lake for fast access

### **🎯 Navigation Flow**
```
Neo4j Graph → Chat Node → Get URLs → Open in ChatGPT
```

### **💡 Usage Examples**
```bash
# Get URLs for a specific chat
curl http://localhost:8000/lake/chat/chat_abc123/urls

# Search URLs by title
curl http://localhost:8000/lake/urls/search?query=python

# Get URL mapping details
curl http://localhost:8000/lake/url/conversation_id_123
```

### **🔄 Benefits**
- **Direct Access**: One-click links to original ChatGPT conversations
- **Search Integration**: Find conversations by title or content
- **Batch Export**: Get all URLs for a specific chat
- **Frontend Integration**: Easy to add "Open in ChatGPT" buttons

## 🛠️ Tech Stack

### Backend
- **Python 3.8+**: Core language
- **FastAPI**: Modern, fast web framework
- **Neo4j**: Graph database for knowledge storage
- **sentence-transformers**: Local embedding generation
- **HDBSCAN**: Density-based clustering
- **UMAP**: Dimensionality reduction

### Frontend
- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Material-UI**: Beautiful, accessible components
- **Cytoscape.js**: Interactive graph visualization
- **Axios**: HTTP client for API communication

### Data Processing
- **JSONL**: Efficient data storage format
- **Embeddings**: 384-dimensional semantic vectors
- **Graph Relationships**: Topic → Chat → Message hierarchy

## 📁 Project Structure

```
chatmind/
├── data_ingestion/          # Extract and flatten chat data
│   ├── extract_and_flatten.py
│   ├── data_lake_storage.py # Data lake storage system
│   └── chatgpt_url_mapper.py # ChatGPT URL mapping
├── embedding/               # Semantic embedding and clustering
│   └── embed_and_cluster.py
├── semantic_chunker/        # GPT-driven semantic chunking
│   ├── chunker.py          # Main chunking logic
│   ├── prompts.py          # Prompt templates
│   ├── run_chunking.py     # Script entry point
│   └── test_sample.json    # Sample for testing
├── neo4j_loader/           # Load data into Neo4j graph
│   └── load_graph.py
├── api/                    # FastAPI backend
│   └── main.py
├── frontend/               # React + Cytoscape visualization
│   ├── src/
│   │   ├── App.tsx        # Main visualization component
│   │   └── index.tsx      # React entry point
│   └── package.json
├── data/                   # Data storage
│   ├── raw/               # ChatGPT export ZIP files
│   ├── processed/         # Flattened JSONL data
│   ├── embeddings/        # Embeddings and clusters
│   └── lake/              # Data lake storage
│       ├── chats/         # Individual chat JSON files
│       ├── messages/      # Individual message JSON files
│       └── metadata/      # Indexes and metadata
├── run_pipeline.py        # Complete pipeline runner
├── start_services.py      # Service starter
└── requirements.txt       # Python dependencies
``` 