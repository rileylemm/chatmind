# ChatMind API Documentation

**Modern REST API for querying and visualizing your ChatGPT knowledge graph.**

The ChatMind API provides a clean, type-safe interface for accessing your processed ChatGPT conversations, semantic clusters, and knowledge graph data. Built with FastAPI for automatic documentation and validation.

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

## 📋 API Overview

### Core Features
- **Graph Data Access**: Query Neo4j knowledge graph
- **Real-time Statistics**: Dashboard metrics and cost tracking
- **Search Capabilities**: Semantic search across messages
- **Topic Analysis**: Access semantic clusters and topics
- **Chat Management**: Browse conversations and messages

### Authentication
Currently, the API runs without authentication for local development. For production deployment, consider adding API key authentication.

### CORS Configuration
The API is configured to accept requests from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:5173`
- `http://127.0.0.1:5173`

## 📊 Data Models

### GraphNode
```json
{
  "id": "string",
  "type": "Topic|Chat|Message|Tag",
  "properties": {
    "name": "string",
    "title": "string",
    "content": "string",
    "size": "number",
    "count": "number"
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
  "type": "CONTAINS|SUMMARIZES|HAS_TOPIC|TAGGED_WITH",
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
  "active_tags": "number",
  "total_cost": "string",
  "total_clusters": "number",
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
  "cluster_id": "number",
  "chat_id": "string"
}
```

### Chat
```json
{
  "id": "string",
  "title": "string",
  "create_time": "number",
  "message_count": "number"
}
```

### Topic
```json
{
  "id": "number",
  "name": "string",
  "size": "number",
  "top_words": ["string"],
  "sample_titles": ["string"]
}
```

### Tag
```json
{
  "name": "string",
  "count": "number",
  "category": "string"
}
```

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
    "total_chats": 150,
    "total_messages": 2847,
    "active_tags": 234,
    "total_cost": "$12.45",
    "total_clusters": 89,
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

### 3. Graph Data

#### GET `/graph`
Retrieve graph data for visualization.

**Query Parameters:**
- `limit` (int, optional): Maximum number of nodes to return (default: 100)
- `node_types` (string, optional): Comma-separated list of node types to include
- `parent_id` (string, optional): Filter to nodes connected to specific parent
- `use_semantic_positioning` (boolean, optional): Include UMAP coordinates (default: false)

**Response:**
```json
{
  "data": {
    "nodes": [
      {
        "id": "topic_123",
        "type": "Topic",
        "properties": {
          "name": "AI Ethics Discussion",
          "size": 45,
          "top_words": ["ethics", "ai", "alignment"]
        },
        "position": {
          "x": 0.234,
          "y": 0.567
        }
      }
    ],
    "edges": [
      {
        "source": "chat_456",
        "target": "topic_123",
        "type": "HAS_TOPIC",
        "properties": {
          "weight": 0.85
        }
      }
    ]
  },
  "message": "Graph data retrieved",
  "error": null
}
```

**Examples:**
```bash
# Get all graph data
curl http://localhost:8000/graph

# Get only topics and chats
curl "http://localhost:8000/graph?node_types=Topic,Chat&limit=50"

# Get nodes with semantic positioning
curl "http://localhost:8000/graph?use_semantic_positioning=true"
```

### 4. Topics

#### GET `/topics`
Get all semantic topics/clusters.

**Response:**
```json
{
  "data": [
    {
      "id": 123,
      "name": "AI Ethics Discussion",
      "size": 45,
      "top_words": ["ethics", "ai", "alignment", "safety"],
      "sample_titles": [
        "Discussion about AI alignment",
        "Ethics in machine learning"
      ]
    }
  ],
  "message": "Topics retrieved successfully",
  "error": null
}
```

**Example:**
```bash
curl http://localhost:8000/topics
```

### 5. Chats

#### GET `/chats`
Get all conversations.

**Query Parameters:**
- `limit` (int, optional): Maximum number of chats to return (default: 50)

**Response:**
```json
{
  "data": [
    {
      "id": "chat_abc123",
      "title": "Python Web Development",
      "create_time": 1732234567.0,
      "message_count": 23
    }
  ],
  "message": "Chats retrieved successfully",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/chats?limit=100"
```

### 6. Chat Messages

#### GET `/chats/{chat_id}/messages`
Get all messages for a specific chat.

**Path Parameters:**
- `chat_id` (string, required): The chat identifier

**Query Parameters:**
- `limit` (int, optional): Maximum number of messages to return (default: 100)

**Response:**
```json
{
  "data": [
    {
      "id": "msg_xyz789",
      "content": "How do I set up a FastAPI project?",
      "role": "user",
      "timestamp": 1732234567.0,
      "cluster_id": 45,
      "chat_id": "chat_abc123"
    }
  ],
  "message": "Messages retrieved successfully",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/chats/chat_abc123/messages?limit=50"
```

### 7. Search

#### GET `/search`
Search messages by content.

**Query Parameters:**
- `query` (string, required): Search term
- `limit` (int, optional): Maximum number of results (default: 50)

**Response:**
```json
{
  "data": [
    {
      "id": "msg_xyz789",
      "content": "I'm working on a FastAPI project...",
      "role": "user",
      "timestamp": 1732234567.0,
      "cluster_id": 45,
      "chat_id": "chat_abc123"
    }
  ],
  "message": "Search completed",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/search?query=FastAPI&limit=20"
```

### 8. Cost Statistics

#### GET `/costs/statistics`
Get API cost tracking statistics.

**Query Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `operation` (string, optional): Filter by operation type

**Response:**
```json
{
  "data": {
    "total_cost": "$12.45",
    "total_calls": 1250,
    "cost_by_operation": {
      "tagging": "$8.20",
      "embedding": "$4.25"
    },
    "cost_by_date": [
      {
        "date": "2025-01-15",
        "cost": "$2.10",
        "calls": 210
      }
    ]
  },
  "message": "Cost statistics retrieved",
  "error": null
}
```

**Examples:**
```bash
# Get all cost statistics
curl http://localhost:8000/costs/statistics

# Get costs for specific date range
curl "http://localhost:8000/costs/statistics?start_date=2025-01-01&end_date=2025-01-31"

# Get costs for specific operation
curl "http://localhost:8000/costs/statistics?operation=tagging"
```

### 9. Tags

#### GET `/tags`
Get all tags with their counts and categories.

**Response:**
```json
{
  "data": [
    {
      "name": "#python",
      "count": 45,
      "category": "programming"
    },
    {
      "name": "#ai",
      "count": 32,
      "category": "technology"
    }
  ],
  "message": "Tags retrieved successfully",
  "error": null
}
```

**Example:**
```bash
curl http://localhost:8000/tags
```

### 10. Single Message

#### GET `/messages/{message_id}`
Get detailed information about a specific message.

**Path Parameters:**
- `message_id` (string, required): The message identifier

**Response:**
```json
{
  "data": {
    "id": "msg_xyz789",
    "content": "How do I set up a FastAPI project?",
    "role": "user",
    "timestamp": 1732234567.0,
    "cluster_id": 45,
    "chat_id": "chat_abc123",
    "tags": ["#python", "#api"],
    "topics": ["Web Development"]
  },
  "message": "Message retrieved successfully",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/messages/msg_xyz789"
```

### 11. Cluster Details

#### GET `/clusters/{cluster_id}`
Get detailed information about a specific cluster/topic.

**Path Parameters:**
- `cluster_id` (integer, required): The cluster identifier

**Response:**
```json
{
  "data": {
    "cluster_id": 123,
    "name": "AI Ethics Discussion",
    "size": 45,
    "top_words": ["ethics", "ai", "alignment", "safety"],
    "sample_titles": [
      "Discussion about AI alignment",
      "Ethics in machine learning"
    ],
    "messages": [
      {
        "id": "msg_abc123",
        "content": "What are the ethical implications of AI?",
        "role": "user",
        "timestamp": 1732234567.0,
        "chat_id": "chat_xyz789",
        "tags": ["#ai", "#ethics"]
      }
    ],
    "common_tags": ["#ai", "#ethics", "#alignment"]
  },
  "message": "Cluster details retrieved successfully",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/clusters/123"
```

### 12. Node Expansion

#### GET `/graph/expand/{node_id}`
Get nodes and edges immediately connected to a given node.

**Path Parameters:**
- `node_id` (string, required): The node identifier (chat_id, message_id, topic_id, or tag name)

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
          "create_time": 1732234567.0
        }
      },
      {
        "id": "msg_xyz789",
        "type": "Message",
        "properties": {
          "content": "How do I set up a FastAPI project?",
          "role": "user"
        }
      }
    ],
    "edges": [
      {
        "source": "chat_abc123",
        "target": "msg_xyz789",
        "type": "CONTAINS",
        "properties": {}
      }
    ]
  },
  "message": "Node expansion retrieved successfully",
  "error": null
}
```

**Example:**
```bash
curl "http://localhost:8000/graph/expand/chat_abc123"
```

### 13. Advanced Search

#### POST `/search/advanced`
Advanced search with filters.

**Request Body:**
```json
{
  "query": "python",
  "filters": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "cluster_id": 123,
    "tags": ["#python", "#api"],
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
      "content": "I'm working on a Python FastAPI project...",
      "role": "user",
      "timestamp": 1732234567.0,
      "cluster_id": 45,
      "chat_id": "chat_abc123",
      "tags": ["#python", "#api"]
    }
  ],
  "message": "Advanced search completed successfully",
  "error": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "python",
    "filters": {
      "start_date": "2025-01-01",
      "end_date": "2025-01-31",
      "tags": ["#python"],
      "limit": 10
    }
  }'
```

### 14. Custom Neo4j Query

#### POST `/query/neo4j`
Execute a custom Cypher query (admin only, read-only).

**Request Body:**
```json
{
  "query": "MATCH (t:Tag) RETURN t.name, t.count ORDER BY t.count DESC LIMIT 10",
  "params": {}
}
```

**Response:**
```json
{
  "data": [
    {
      "t.name": "#python",
      "t.count": 45
    },
    {
      "t.name": "#ai",
      "t.count": 32
    }
  ],
  "message": "Custom query executed successfully",
  "error": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/query/neo4j" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (t:Tag) RETURN t.name, t.count ORDER BY t.count DESC LIMIT 5"
  }'
```

### 15. Chat Summary

#### POST `/chats/{chat_id}/summary`
Generate a summary for a specific chat (placeholder for future AI implementation).

**Path Parameters:**
- `chat_id` (string, required): The chat identifier

**Response:**
```json
{
  "data": {
    "chat_id": "chat_abc123",
    "message_count": 23,
    "user_messages": 12,
    "assistant_messages": 11,
    "summary": "Chat with 23 messages (12 user, 11 assistant)",
    "note": "This is a placeholder. Future versions will include AI-generated summaries."
  },
  "message": "Chat summary generated successfully",
  "error": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/chats/chat_abc123/summary"
```

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

### Error Types
- `DATABASE_ERROR`: Neo4j connection or query issues
- `VALIDATION_ERROR`: Invalid request parameters
- `NOT_FOUND`: Requested resource doesn't exist
- `CONFIGURATION_ERROR`: Missing environment variables

## 🚀 Development

### Starting the API Server
```bash
# Using the startup script (recommended)
python scripts/start_api.py

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

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Dashboard stats
curl http://localhost:8000/api/stats/dashboard

# Graph data
curl "http://localhost:8000/graph?limit=10"

# Search
curl "http://localhost:8000/search?query=python"
```

## 📊 Integration Examples

### Frontend Integration (JavaScript)
```javascript
// Get dashboard statistics
const response = await fetch('http://localhost:8000/api/stats/dashboard');
const stats = await response.json();

// Get graph data for visualization
const graphResponse = await fetch('http://localhost:8000/graph?limit=100');
const graphData = await graphResponse.json();

// Search messages
const searchResponse = await fetch('http://localhost:8000/search?query=AI&limit=20');
const searchResults = await searchResponse.json();
```

### Python Integration
```python
import requests

# Get dashboard stats
response = requests.get('http://localhost:8000/api/stats/dashboard')
stats = response.json()

# Get topics
response = requests.get('http://localhost:8000/topics')
topics = response.json()

# Search messages
response = requests.get('http://localhost:8000/search', params={
    'query': 'machine learning',
    'limit': 10
})
results = response.json()
```

## 🔒 Security Considerations

### Current Setup (Development)
- No authentication required
- CORS configured for local development
- Database credentials in environment variables

### Production Recommendations
1. **Add API Key Authentication**
2. **Implement Rate Limiting**
3. **Use HTTPS**
4. **Add Request Validation**
5. **Implement Logging and Monitoring**

## 📈 Performance Tips

### Query Optimization
- Use `limit` parameter to control result size
- Filter by `node_types` to reduce data transfer
- Use `parent_id` for focused graph queries

### Caching
- Consider caching dashboard statistics
- Cache frequently accessed graph data
- Implement client-side caching for static data

### Database Connection
- Connection pooling is handled by Neo4j driver
- Monitor connection health with `/health` endpoint
- Implement retry logic for transient failures

## 🤝 Contributing

### Adding New Endpoints
1. Define Pydantic models in `main.py`
2. Add service methods in `services.py`
3. Create endpoint in `main.py`
4. Update this documentation
5. Add tests

### Code Style
- Follow FastAPI best practices
- Use type hints throughout
- Add comprehensive docstrings
- Include error handling

## 📚 Related Documentation

- [Neo4j Query Guide](NEO4J_QUERY_GUIDE.md) - Database query patterns
- [Pipeline Overview](PIPELINE_OVERVIEW.md) - Data processing pipeline
- [User Guide](UserGuide.md) - Complete system guide

---

**API Version**: 2.0.0  
**Last Updated**: January 2025  
**Maintainer**: ChatMind Development Team 