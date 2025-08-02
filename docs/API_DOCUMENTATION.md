# ChatMind API Documentation

**Modern REST API for exploring your rich ChatGPT semantic knowledge graph.**

The ChatMind API provides powerful endpoints for discovering insights, exploring semantic connections, and visualizing your processed ChatGPT conversations. Built with FastAPI for automatic documentation and validation, leveraging your rich Neo4j database with 168,406 nodes and sophisticated semantic relationships.

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
curl http://localhost:8000/health
```

---

## ✅ Test Coverage & Reliability
- **All endpoints are covered by automated tests.**
- **100% pass rate** as of January 2025 (see `scripts/test_api_endpoints.py`).
- All endpoints return a standard response with `data`, `message`, and `error` keys.

---

## 📋 API Overview

### Rich Semantic Knowledge Graph
Your ChatMind database contains:
- **1,714 Chats** with positioning data
- **47,575 Chunks** with embeddings
- **32,516 Tags** with semantic classification
- **1,486 Cluster Summaries**
- **1,714 Chat Summaries**
- **86,588 Chat Similarities**
- **305,013 Cluster Similarities**

### Core Features
- **Discovery & Exploration**: Find topics, patterns, and insights
- **Semantic Search**: Search by meaning, not just keywords
- **Graph Visualization**: 2D/3D positioning and relationships
- **Advanced Analytics**: Pattern analysis and recommendations
- **Interactive Exploration**: Real-time graph navigation

### Authentication
Currently, the API runs without authentication for local development. For production deployment, consider adding API key authentication.

### CORS Configuration
The API is configured to accept requests from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

---

## 📊 Data Models

### GraphNode
```json
{
  "id": "string",
  "type": "Chat|Message|Chunk|Cluster|Tag|Summary",
  "properties": {
    "title": "string",
    "content": "string",
    "tags": ["string"],
    "domain": "string",
    "sentiment": "string",
    "complexity": "string"
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
  "type": "CONTAINS|HAS_CHUNK|SUMMARIZES|TAGS|SIMILAR_TO",
  "properties": {
    "score": "number",
    "weight": "number"
  }
}
```

### DashboardStats
```json
{
  "total_chats": "number",
  "total_messages": "number", 
  "total_chunks": "number",
  "total_clusters": "number",
  "active_tags": "number",
  "total_relationships": "number",
  "total_cost": "string",
  "total_calls": "number"
}
```

### Message
```json
{
  "id": "string",
  "content": "string",
  "role": "user|assistant",
  "timestamp": "number",
  "chat_id": "string",
  "tags": ["string"],
  "domain": "string",
  "sentiment": "string"
}
```

### Chat
```json
{
  "id": "string",
  "title": "string",
  "create_time": "number",
  "message_count": "number",
  "position_x": "number",
  "position_y": "number"
}
```

### Cluster
```json
{
  "cluster_id": "number",
  "name": "string",
  "size": "number",
  "umap_x": "number",
  "umap_y": "number",
  "summary": "string",
  "key_points": ["string"],
  "common_tags": ["string"]
}
```

### Tag
```json
{
  "name": "string",
  "count": "number",
  "category": "string",
  "domain": "string"
}
```

---

## 🔗 API Endpoints

### 1. Health Check

#### GET `/health`
Check API health and connectivity.

**Response:**
```json
{
  "data": {
    "status": "healthy",
    "timestamp": "2025-01-15T10:30:00Z"
  },
  "message": "API is running",
  "error": null
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

### 2. Dashboard Statistics

#### GET `/api/stats/dashboard`
Get real-time dashboard statistics from your processed data.

**Response:**
```json
{
  "data": {
    "total_chats": 1714,
    "total_messages": 2847,
    "total_chunks": 47575,
    "total_clusters": 1486,
    "active_tags": 32516,
    "total_relationships": 391601,
    "total_cost": "$12.45",
    "total_calls": 1250
  },
  "message": "Dashboard statistics retrieved",
  "error": null
}
```

**Example:**
```bash
curl http://localhost:8000/api/stats/dashboard
```

### 3. Discovery APIs

#### GET `/api/discover/topics`
Get most discussed topics with frequency and trends.

**Query Parameters:**
- `limit` (int, optional): Maximum number of topics (default: 20)
- `min_count` (int, optional): Minimum usage count filter
- `domain` (string, optional): Filter by domain

**Response:**
```json
{
  "data": [
    {
      "topic": "python programming",
      "count": 156,
      "domain": "technology",
      "trend": "increasing",
      "related_topics": ["web development", "api design"]
    }
  ],
  "message": "Topics discovered successfully",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/api/discover/topics?limit=10&domain=technology"
```

#### GET `/api/discover/domains`
Get domain distribution and insights.

**Response:**
```json
{
  "data": [
    {
      "domain": "technology",
      "count": 892,
      "percentage": 52.0,
      "top_topics": ["python", "javascript", "api design"],
      "sentiment_distribution": {
        "positive": 65,
        "neutral": 25,
        "negative": 10
      }
    }
  ],
  "message": "Domain insights retrieved",
  "error": null
}
```

#### GET `/api/discover/clusters`
Get semantic clusters with positioning and summaries.

**Query Parameters:**
- `limit` (int, optional): Maximum number of clusters (default: 50)
- `min_size` (int, optional): Minimum cluster size
- `include_positioning` (boolean, optional): Include UMAP coordinates (default: true)

**Response:**
```json
{
  "data": [
    {
      "cluster_id": 123,
      "name": "AI Ethics Discussion",
      "size": 45,
      "umap_x": 0.234,
      "umap_y": 0.567,
      "summary": "Discussions about AI alignment and safety",
      "key_points": ["ethics", "alignment", "safety"],
      "common_tags": ["#ai", "#ethics", "#alignment"]
    }
  ],
  "message": "Clusters discovered successfully",
  "error": null
}
```

### 4. Search APIs

#### GET `/api/search/semantic`
Search by semantic similarity using embeddings.

**Query Parameters:**
- `query` (string, required): Search query
- `limit` (int, optional): Maximum results (default: 20)
- `min_similarity` (float, optional): Minimum similarity score (default: 0.7)

**Response:**
```json
{
  "data": [
    {
      "id": "msg_xyz789",
      "content": "How do I implement machine learning algorithms?",
      "role": "user",
      "similarity_score": 0.89,
      "chat_id": "chat_abc123",
      "tags": ["#machine-learning", "#python"]
    }
  ],
  "message": "Semantic search completed",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/api/search/semantic?query=machine learning&limit=10"
```

#### GET `/api/search/content`
Full-text search across messages.

**Query Parameters:**
- `query` (string, required): Search term
- `limit` (int, optional): Maximum results (default: 50)
- `role` (string, optional): Filter by role (user/assistant)

**Response:**
```json
{
  "data": [
    {
      "id": "msg_xyz789",
      "content": "I'm working on a Python FastAPI project...",
      "role": "user",
      "timestamp": 1732234567.0,
      "chat_id": "chat_abc123",
      "tags": ["#python", "#api"]
    }
  ],
  "message": "Content search completed",
  "error": null
}
```

#### GET `/api/search/tags`
Search by specific tags or tag combinations.

**Query Parameters:**
- `tags` (string, required): Comma-separated tag list
- `limit` (int, optional): Maximum results (default: 50)
- `exact_match` (boolean, optional): Require exact tag matches (default: false)

**Response:**
```json
{
  "data": [
    {
      "id": "msg_xyz789",
      "content": "Python web development with FastAPI",
      "role": "user",
      "tags": ["#python", "#web-development", "#api"],
      "chat_id": "chat_abc123"
    }
  ],
  "message": "Tag search completed",
  "error": null
}
```

#### POST `/api/search/advanced`
Advanced multi-criteria search.

**Request Body:**
```json
{
  "query": "python",
  "filters": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "domain": "technology",
    "sentiment": "positive",
    "complexity": "intermediate",
    "tags": ["#python", "#api"],
    "min_similarity": 0.8,
    "limit": 20
  }
}
```

**Response:**
```json
{
  "data": [
    {
      "id": "msg_xyz789",
      "content": "Advanced Python FastAPI implementation",
      "role": "user",
      "similarity_score": 0.92,
      "chat_id": "chat_abc123",
      "tags": ["#python", "#api", "#advanced"],
      "domain": "technology",
      "sentiment": "positive"
    }
  ],
  "message": "Advanced search completed",
  "error": null
}
```

### 5. Graph Exploration APIs

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

#### GET `/api/graph/connections`
Find connections between different conversations or topics.

**Query Parameters:**
- `source_id` (string, required): Source node ID
- `target_id` (string, optional): Target node ID
- `max_hops` (int, optional): Maximum path length (default: 3)
- `relationship_types` (string, optional): Comma-separated relationship types

**Response:**
```json
{
  "data": {
    "paths": [
      {
        "path": ["chat_abc123", "cluster_45", "chat_def456"],
        "length": 2,
        "relationships": ["SIMILAR_TO", "CONTAINS"],
        "total_score": 0.78
      }
    ],
    "summary": {
      "total_paths": 5,
      "average_score": 0.72,
      "strongest_connection": 0.89
    }
  },
  "message": "Connections found",
  "error": null
}
```

#### GET `/api/graph/neighbors`
Get semantic neighbors of a conversation or cluster.

**Query Parameters:**
- `node_id` (string, required): Node ID to explore
- `limit` (int, optional): Maximum neighbors (default: 10)
- `min_similarity` (float, optional): Minimum similarity (default: 0.7)
- `relationship_type` (string, optional): Specific relationship type

**Response:**
```json
{
  "data": {
    "node": {
      "id": "chat_abc123",
      "type": "Chat",
      "title": "Python Web Development"
    },
    "neighbors": [
      {
        "id": "chat_def456",
        "type": "Chat",
        "title": "FastAPI Tutorial",
        "similarity_score": 0.89,
        "relationship_type": "SIMILAR_TO"
      }
    ],
    "summary": {
      "total_neighbors": 8,
      "average_similarity": 0.76,
      "strongest_connection": 0.92
    }
  },
  "message": "Neighbors retrieved",
  "error": null
}
```

### 6. Analytics APIs

#### GET `/api/analytics/patterns`
Analyze conversation patterns and trends.

**Query Parameters:**
- `timeframe` (string, optional): Time period (daily, weekly, monthly)
- `domain` (string, optional): Filter by domain
- `include_sentiment` (boolean, optional): Include sentiment analysis (default: true)

**Response:**
```json
{
  "data": {
    "conversation_frequency": [
      {
        "date": "2025-01-15",
        "count": 12,
        "avg_messages": 18.5
      }
    ],
    "topic_evolution": [
      {
        "topic": "python",
        "trend": "increasing",
        "growth_rate": 0.15
      }
    ],
    "sentiment_trends": {
      "positive": 65,
      "neutral": 25,
      "negative": 10
    },
    "complexity_distribution": {
      "beginner": 20,
      "intermediate": 45,
      "advanced": 35
    }
  },
  "message": "Pattern analysis completed",
  "error": null
}
```

#### GET `/api/analytics/sentiment`
Sentiment analysis over time.

**Query Parameters:**
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)
- `group_by` (string, optional): Grouping (day, week, month, domain)

**Response:**
```json
{
  "data": {
    "overall_sentiment": {
      "positive": 65,
      "neutral": 25,
      "negative": 10
    },
    "sentiment_by_domain": [
      {
        "domain": "technology",
        "positive": 70,
        "neutral": 20,
        "negative": 10
      }
    ],
    "sentiment_timeline": [
      {
        "date": "2025-01-15",
        "positive": 8,
        "neutral": 3,
        "negative": 1
      }
    ]
  },
  "message": "Sentiment analysis completed",
  "error": null
}
```

### 7. Traditional APIs (Maintained for Compatibility)

#### GET `/api/graph`
Retrieve graph data for visualization (legacy endpoint).

#### GET `/api/chats`
Get all conversations.

#### GET `/api/chats/{chat_id}/messages`
Get messages for a specific chat.

#### GET `/api/search`
Basic content search (legacy endpoint).

#### GET `/api/tags`
Get all tags with counts.

#### GET `/api/clusters/{cluster_id}`
Get detailed cluster information.

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
# Using the startup script (recommended)
python scripts/start_services.py

# Manual start
cd chatmind/api
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables
```bash
# Required
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Optional
OPENAI_API_KEY=your_openai_key  # For future features
```

---

## 📊 Integration Examples

### Frontend Integration (JavaScript)
```javascript
// Discover topics
const topicsResponse = await fetch('http://localhost:8000/api/discover/topics?limit=10');
const topics = await topicsResponse.json();

// Semantic search
const searchResponse = await fetch('http://localhost:8000/api/search/semantic?query=machine learning&limit=10');
const searchResults = await searchResponse.json();

// Graph visualization
const graphResponse = await fetch('http://localhost:8000/api/graph/visualization?node_types=Chat,Cluster&limit=100');
const graphData = await graphResponse.json();

// Pattern analysis
const patternsResponse = await fetch('http://localhost:8000/api/analytics/patterns?timeframe=monthly');
const patterns = await patternsResponse.json();
```

### Python Integration
```python
import requests

# Discover clusters
response = requests.get('http://localhost:8000/api/discover/clusters?limit=20')
clusters = response.json()

# Advanced search
response = requests.post('http://localhost:8000/api/search/advanced', json={
    'query': 'python',
    'filters': {
        'domain': 'technology',
        'sentiment': 'positive',
        'limit': 10
    }
})
results = response.json()

# Graph connections
response = requests.get('http://localhost:8000/api/graph/connections?source_id=chat_abc123&max_hops=3')
connections = response.json()
```

---

## 🎯 Roadmap

### Phase 1: Core Discovery (Current)
- ✅ Topic discovery and visualization
- ✅ Basic semantic search
- ✅ Graph visualization data
- ✅ Conversation browsing

### Phase 2: Advanced Analytics (Next)
- 🔄 Pattern analysis and insights
- 🔄 Interactive graph exploration
- 🔄 Advanced search capabilities
- 🔄 Personal analytics dashboard

### Phase 3: Intelligence Features (Future)
- 🔮 AI-powered insights and recommendations
- 🔮 Advanced graph algorithms
- 🔮 Real-time collaboration features
- 🔮 Predictive analytics

---

**API Version**: 3.0.0  
**Last Updated**: January 2025  
**Maintainer**: ChatMind Development Team 