# ChatMind API

A clean, modern FastAPI backend for the ChatMind knowledge graph visualization system.

## Features

- **Clean Architecture**: Separated concerns with dedicated service layers
- **Modern FastAPI**: Type-safe endpoints with automatic documentation
- **Comprehensive Error Handling**: Proper HTTP status codes and error messages
- **CORS Support**: Configured for frontend development
- **Health Checks**: Built-in health monitoring
- **Async Support**: Non-blocking database operations

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (optional):
   ```bash
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="password"
   export API_HOST="0.0.0.0"
   export API_PORT="8000"
   ```

3. **Start the server**:
   ```bash
   python run.py
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with API info
- `GET /health` - Health check
- `GET /api/stats/dashboard` - Dashboard statistics
- `GET /graph` - Graph data with filtering
- `GET /topics` - All topics
- `GET /chats` - All chats
- `GET /chats/{chat_id}/messages` - Messages for a specific chat
- `GET /search` - Search messages by content
- `GET /costs/statistics` - Cost statistics

### Query Parameters

#### Graph Data (`/graph`)
- `limit` (int): Maximum number of nodes to return (default: 100)
- `node_types` (str): Comma-separated list of node types to include
- `parent_id` (str): Filter by parent node ID
- `use_semantic_positioning` (bool): Apply semantic positioning

#### Search (`/search`)
- `query` (str): Search term (required)
- `limit` (int): Maximum results (default: 50)

#### Cost Statistics (`/costs/statistics`)
- `start_date` (str): Start date filter
- `end_date` (str): End date filter
- `operation` (str): Filter by operation type

## Response Format

All endpoints return a consistent response format:

```json
{
  "data": <actual_data>,
  "message": "Success message",
  "error": null
}
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable (database connection issues)

## Development

### Running in Development Mode

```bash
export API_RELOAD=true
python run.py
```

### Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test dashboard stats
curl http://localhost:8000/api/stats/dashboard

# Test graph data
curl "http://localhost:8000/graph?limit=10&node_types=Topic"
```

## Architecture

### Services

- **Neo4jService**: Handles all database operations
- **StatsService**: Calculates statistics from various data sources

### Models

- **GraphNode/GraphEdge**: Graph data structures
- **Message/Chat/Topic**: Domain models
- **ApiResponse**: Standardized response wrapper

### Dependencies

- FastAPI for the web framework
- Neo4j driver for database access
- Pydantic for data validation
- Uvicorn for ASGI server

## Configuration

The API can be configured via environment variables:

- `NEO4J_URI`: Neo4j connection URI
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `API_RELOAD`: Enable auto-reload (default: false) 