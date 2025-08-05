# ChatMind API Documentation

**Modern REST API for exploring your rich ChatGPT semantic knowledge graph.**

The ChatMind API provides powerful endpoints for discovering insights, exploring semantic connections, and visualizing your processed ChatGPT conversations. Built with FastAPI for automatic documentation and validation, leveraging your rich Neo4j database with hybrid Qdrant vector search capabilities.

---

## 🚀 Quick Start

### Base URL
```
http://localhost:8000
```

### API Documentation
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

### Health Check
```bash
curl http://localhost:8000/api/health
```

---

## ✅ Test Coverage & Reliability
- **All endpoints are covered by automated tests.**
- **100% pass rate** as of current development (see `test_simple_api.py`).
- All endpoints return a standard response with `data`, `message`, and `error` keys.
- **15 total endpoints tested** with comprehensive coverage.

---

## 📋 API Overview

### Rich Semantic Knowledge Graph
Your ChatMind database contains:
- **Chats** with positioning data
- **Messages** with content and metadata
- **Chunks** with embeddings (using Sentence Transformers)
- **Tags** with semantic classification
- **Cluster Summaries**
- **Chat Summaries**
- **Similarity relationships** between chats and clusters
- **Total Nodes** in Neo4j database
- **Total Relationships** connecting semantic data

*Note: Actual counts depend on your processed data volume.*

### Core Features
- **Discovery & Exploration**: Find topics, patterns, and insights
- **Semantic Search**: Search by meaning, not just keywords (using embeddings and cosine similarity)
- **Graph Visualization**: 2D/3D positioning and relationships
- **Hybrid Search**: Combines Neo4j graph queries with Qdrant vector search
- **Interactive Exploration**: Real-time graph navigation
- **Vector Similarity**: Embeddings for semantic search

### Authentication
Currently, the API runs without authentication for local development. For production deployment, consider adding API key authentication.

### Error Handling & Reliability
- All endpoints include comprehensive error handling
- Neo4j connection issues are gracefully handled
- Invalid parameters return appropriate HTTP status codes
- All DateTime objects are properly serialized to ISO format strings

### CORS Configuration
The API is configured to accept requests from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

### Recent Improvements
- ✅ **Modular Architecture**: Clean separation of routes, models, and utilities
- ✅ **Test-Driven Development**: All endpoints tested and validated
- ✅ **Hybrid Database Integration**: Seamless Neo4j + Qdrant operations
- ✅ **Error Handling**: Robust error handling and graceful fallbacks
- ✅ **Performance**: Optimized database connections and queries

---

## 📊 Data Models

### ApiResponse
```json
{
  "data": "any",
  "message": "string",
  "error": "string (optional)"
}
```

### GraphNode
```json
{
  "id": "string",
  "type": "Chat|Message|Chunk|Topic|Tag",
  "properties": {
    "title": "string",
    "content": "string",
    "tags": ["string"],
    "domain": "string",
    "sentiment": "string",
    "complexity": "string",
    "create_time": "string (ISO format)",
    "timestamp": "number"
  },
  "position": {
    "x": "number",
    "y": "number"
  }
}
```

### GraphEdge
```json
{
  "source": "string",
  "target": "string", 
  "type": "CONTAINS|HAS_CHUNK|SUMMARIZES|TAGS|SIMILAR_TO|HAS_TOPIC",
  "properties": {
    "score": "number",
    "weight": "number",
    "similarity": "number"
  }
}
```

### SearchResult
```json
{
  "chunk_id": "string",
  "content": "string",
  "message_id": "string",
  "chat_id": "string",
  "similarity_score": "number (optional)"
}
```

### Conversation
```json
{
  "chat_id": "string",
  "title": "string",
  "create_time": "number",
  "message_count": "number",
  "position_x": "number",
  "position_y": "number"
}
```

### Message
```json
{
  "message_id": "string",
  "content": "string",
  "role": "user|assistant",
  "timestamp": "number",
  "chat_id": "string"
}
```

---

## 🔗 API Endpoints

### 1. Health Check

#### GET `/api/health`
Check API health and connectivity.

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "neo4j": "connected"
  },
  "message": "All services operational",
  "error": null
}
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

### 2. Search APIs

#### GET `/api/search`
Simple search endpoint using Neo4j only.

**Query Parameters:**
- `query` (string, required): Search query
- `limit` (int, optional): Maximum results (default: 10, max: 100)

**Response:**
```json
{
  "data": [
    {
      "content": "Example message content",
      "message_id": "msg_123"
    }
  ],
  "message": "Found 1 results for 'example'",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/api/search?query=python&limit=5"
```

#### GET `/api/search/semantic`
Semantic search using Qdrant vector database.

**Query Parameters:**
- `query` (string, required): Search query
- `limit` (int, optional): Maximum results (default: 10, max: 100)

**Response:**
```json
{
  "data": [
    {
      "chunk_id": "abc123_msg_0_chunk_0",
      "content": "Example content",
      "message_id": "msg_123",
      "chat_id": "chat_456",
      "similarity_score": 0.95
    }
  ],
  "message": "Found 1 semantic results for 'example'",
  "error": null
}
```

**Features:**
- **True Semantic Search**: Finds related content even when exact words don't match
- **Cosine Similarity**: Uses vector embeddings for semantic comparison
- **Contextual Understanding**: "japan" finds "Korea", "Italy", "Mexico" as related countries
- **Programming Context**: "python" finds beginner discussions and script references

**Example:**
```bash
curl "http://localhost:8000/api/search/semantic?query=machine learning&limit=5"
```

#### GET `/api/search/hybrid`
Hybrid search combining Neo4j and Qdrant.

**Query Parameters:**
- `query` (string, required): Search query
- `limit` (int, optional): Maximum results (default: 10, max: 100)

**Response:**
```json
{
  "data": [
    {
      "chunk_id": "abc123_msg_0_chunk_0",
      "content": "Example content",
      "message_id": "msg_123",
      "chat_id": "chat_456",
      "similarity_score": 0.95,
      "source": "qdrant"
    }
  ],
  "message": "Found 1 hybrid results for 'example'",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/api/search/hybrid?query=python&limit=5"
```

#### GET `/api/search/stats`
Get search statistics and database status.

**Response:**
```json
{
  "data": {
    "neo4j_connected": true,
    "qdrant_connected": true,
    "embedding_model_loaded": true,
    "total_conversations": 2,
    "total_messages": 2,
    "total_chunks": 47575
  },
  "message": "Search statistics retrieved",
  "error": null
}
```

#### GET `/api/search/tags`
Search by specific tags.

**Query Parameters:**
- `tags` (string, required): Comma-separated tag list
- `limit` (int, optional): Maximum results (default: 10, max: 100)

**Response:**
```json
{
  "data": [
    {
      "chunk_id": "abc123_msg_0_chunk_0",
      "content": "Example content",
      "message_id": "msg_123",
      "chat_id": "chat_456",
      "tags": ["#python", "#api"]
    }
  ],
  "message": "Found 0 results for tags: python",
  "error": null
}
```

#### GET `/api/search/domain/{domain}`
Search by domain.

**Path Parameters:**
- `domain` (string, required): Domain to search

**Query Parameters:**
- `limit` (int, optional): Maximum results (default: 10, max: 100)

**Response:**
```json
{
  "data": [
    {
      "chunk_id": "abc123_msg_0_chunk_0",
      "content": "Example content",
      "message_id": "msg_123",
      "chat_id": "chat_456"
    }
  ],
  "message": "Found 2 results for domain: technology",
  "error": null
}
```

#### GET `/api/search/similar/{chunk_id}`
Find similar content to a specific chunk.

**Path Parameters:**
- `chunk_id` (string, required): Chunk ID to find similar content for

**Query Parameters:**
- `limit` (int, optional): Maximum results (default: 10, max: 100)

**Response:**
```json
{
  "data": [],
  "message": "Found 0 similar results for chunk: abc123",
  "error": null
}
```

#### GET `/api/search/tags/available`
Get all available tags.

**Response:**
```json
{
  "data": [
    {
      "name": "python",
      "count": 156
    }
  ],
  "message": "Found 23989 available tags",
  "error": null
}
```

### 3. Graph Exploration APIs

#### GET `/api/graph`
Get graph data for visualization.

**Response:**
```json
{
  "data": {
    "nodes": [
      {
        "id": "chat_abc123",
        "type": "Chat",
        "properties": {
          "title": "Python Web Development",
          "domain": "technology"
        },
        "position": {
          "x": 0.234,
          "y": 0.567
        }
      }
    ],
    "edges": [
      {
        "source": "chat_abc123",
        "target": "cluster_45",
        "type": "SIMILAR_TO",
        "properties": {
          "score": 0.85
        }
      }
    ]
  },
  "message": "Graph data retrieved",
  "error": null
}
```

#### GET `/api/conversations`
Get all conversations.

**Response:**
```json
{
  "data": [
    {
      "chat_id": "chat_abc123",
      "title": "Python Web Development",
      "create_time": 1732234567.0,
      "message_count": 5,
      "position_x": 0.234,
      "position_y": 0.567
    }
  ],
  "message": "Found 3 conversations",
  "error": null
}
```

#### GET `/api/conversations/{chat_id}/messages`
Get messages for a specific conversation.

**Path Parameters:**
- `chat_id` (string, required): Chat ID

**Response:**
```json
{
  "data": [
    {
      "message_id": "msg_123",
      "content": "Example message content",
      "role": "user",
      "timestamp": 1732234567.0,
      "chat_id": "chat_abc123"
    }
  ],
  "message": "Found 1 messages for chat: chat_abc123",
  "error": null
}
```

#### GET `/api/chunks/{chunk_id}`
Get details for a specific chunk.

**Path Parameters:**
- `chunk_id` (string, required): Chunk ID

**Response:**
```json
{
  "data": {
    "chunk_id": "abc123_msg_0_chunk_0",
    "content": "Example chunk content",
    "message_id": "msg_123",
    "chat_id": "chat_456"
  },
  "message": "Chunk details retrieved",
  "error": null
}
```

#### GET `/api/graph/visualization`
Get data for 2D/3D graph visualization.

**Query Parameters:**
- `node_types` (string, optional): Comma-separated node types (Chat,Cluster,Tag)
- `limit` (int, optional): Maximum nodes (default: 100)
- `include_edges` (boolean, optional): Include relationship data (default: true)
- `filter_domain` (string, optional): Filter by domain

**Response:**
```json
{
  "data": {
    "nodes": [
      {
        "id": "chat_abc123",
        "type": "Chat",
        "properties": {
          "title": "Python Web Development",
          "domain": "technology"
        },
        "position": {
          "x": 0.234,
          "y": 0.567
        }
      }
    ],
    "edges": [
      {
        "source": "chat_abc123",
        "target": "cluster_45",
        "type": "SIMILAR_TO",
        "properties": {
          "score": 0.85
        }
      }
    ]
  },
  "message": "Visualization data retrieved",
  "error": null
}
```

### 4. Debug APIs

#### GET `/api/debug/schema`
Get database schema information.

**Response:**
```json
{
  "data": {
    "neo4j_schema": {
      "nodes": [
        {
          "type": "Chat",
          "count": 2,
          "properties": ["chat_id", "title", "create_time", "message_count", "position_x", "position_y"]
        }
      ],
      "relationships": [
        {
          "type": "CONTAINS",
          "count": 2,
          "properties": []
        }
      ]
    },
    "qdrant_schema": {
      "collection_name": "chatmind_embeddings",
      "vector_size": 384,
      "total_points": 47575
    }
  },
  "message": "Schema information retrieved",
  "error": null
}
```

---

## 🔧 Error Handling

### Standard Error Response
```json
{
  "data": null,
  "message": "Error description",
  "error": "ERROR_TYPE"
}
```

### Common HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Database connection issues

---

## 🚀 Development

### Starting the API Server
```bash
# Using the run script
python run.py

# Direct execution
python main.py

# With uvicorn
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables
```bash
# Required
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=chatmind123

# Optional
QDRANT_HOST=localhost
QDRANT_PORT=6335
QDRANT_COLLECTION=chatmind_embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
API_HOST=0.0.0.0
API_PORT=8000
```

### Running Tests
```bash
# Run comprehensive test suite
python test_simple_api.py
```

---

## 📊 Integration Examples

### Frontend Integration (JavaScript)
```javascript
// Health check
const healthResponse = await fetch('http://localhost:8000/api/health');
const health = await healthResponse.json();

// Simple search
const searchResponse = await fetch('http://localhost:8000/api/search?query=python&limit=5');
const searchResults = await searchResponse.json();

// Semantic search
const semanticResponse = await fetch('http://localhost:8000/api/search/semantic?query=machine learning&limit=5');
const semanticResults = await semanticResponse.json();

// Graph visualization
const graphResponse = await fetch('http://localhost:8000/api/graph/visualization?limit=100');
const graphData = await graphResponse.json();

// Get conversations
const conversationsResponse = await fetch('http://localhost:8000/api/conversations');
const conversations = await conversationsResponse.json();
```

### Python Integration
```python
import requests

# Health check
response = requests.get('http://localhost:8000/api/health')
health = response.json()

# Hybrid search
response = requests.get('http://localhost:8000/api/search/hybrid?query=python&limit=10')
results = response.json()

# Get graph data
response = requests.get('http://localhost:8000/api/graph')
graph_data = response.json()

# Get available tags
response = requests.get('http://localhost:8000/api/search/tags/available')
tags = response.json()
```

---

## 🎯 Architecture

### Modular Design
The API follows a clean, modular architecture:

```
api/
├── main.py                 # FastAPI app setup and startup/shutdown
├── run.py                  # Entrypoint to run the server
├── config.py               # Configuration management
├── routes/                 # Individual route files
│   ├── health.py           # Health checks
│   ├── search.py           # Search endpoints
│   ├── graph.py            # Graph exploration endpoints
│   └── debug.py            # Debug endpoints
├── models/                 # Pydantic models
│   ├── __init__.py
│   └── common.py
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── helpers.py
└── services/               # Business logic (future expansion)
    └── __init__.py
```

### Database Integration
- **Neo4j**: Handles graph relationships, metadata, and complex queries
- **Qdrant**: Handles semantic search with embeddings
- **Hybrid Queries**: Combines both databases for rich exploration
- **Error Handling**: Graceful fallbacks for all database operations

### Performance Features
- **Singleton Pattern**: Single instances of database drivers and embedding models
- **Connection Pooling**: Efficient database connection management
- **Lazy Loading**: Embedding model loaded only when needed
- **Global Connections**: Database connections passed via `set_global_connections` functions

---

**API Version**: 3.0.0  
**Last Updated**: Current Development  
**Maintainer**: ChatMind Development Team  
**Test Status**: ✅ 100% Pass Rate (15/15 endpoints) 