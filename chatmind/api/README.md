# ChatMind API - Hybrid Architecture

A modern FastAPI backend for querying ChatGPT knowledge graph with hybrid Neo4j + Qdrant architecture.

## Architecture

The API uses a hybrid architecture combining Neo4j graph database and Qdrant vector database:

- **Neo4j**: Stores graph relationships, metadata, and complex queries
- **Qdrant**: Stores embeddings for semantic search and similarity operations
- **Hybrid Search**: Combines both databases for rich semantic exploration

The API is organized with a clean, modular structure:

```
api/
├── main.py                 # FastAPI app setup and startup/shutdown
├── run.py                  # Entrypoint to run the server
├── config.py               # Configuration management
│
├── routes/                 # Individual route files
│   ├── health.py           # Health checks
│   ├── search.py           # Search endpoints (simple, semantic, hybrid)
│   ├── graph.py            # Graph exploration endpoints
│   └── debug.py            # Debug and schema endpoints
│
├── models/                 # Pydantic request/response models
│   ├── __init__.py         # Package initialization
│   └── common.py           # Common models (ApiResponse)
│
├── utils/                  # Utility functions
│   ├── __init__.py         # Package initialization
│   └── helpers.py          # Helper functions (convert_neo4j_to_json)
│
├── services/               # Business logic (future expansion)
│   └── __init__.py         # Package initialization
│
├── requirements.txt
└── README.md
```

## Features

- **Hybrid Architecture**: Combines Neo4j graph database and Qdrant vector database
- **Semantic Search**: Advanced search with embeddings and similarity
- **Graph Exploration**: Rich graph queries and relationship analysis
- **Hybrid Search**: Combines semantic search with graph context
- **Health Checks**: Comprehensive service health monitoring
- **Modular Design**: Clean separation of concerns with incremental development
- **Test-Driven Development**: All endpoints tested and validated

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables** (or copy `.env.example` and source it):
   ```bash
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="your_strong_password_here"
   export QDRANT_HOST="localhost"
   export QDRANT_PORT="6335"
   export QDRANT_COLLECTION="chatmind_embeddings"
   export API_HOST="0.0.0.0"
   export API_PORT="8000"
   ```

3. **Run the Server**:
   ```bash
   python run.py
   # or
   python main.py
   ```

4. **Access the API**:
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

## API Endpoints

### Health Checks
- `GET /api/health` - General health check

### Search Endpoints
- `GET /api/search` - Simple search (Neo4j only)
- `GET /api/search/semantic` - Semantic search (Qdrant only)
- `GET /api/search/hybrid` - Hybrid search (combines both)
- `GET /api/search/stats` - Search statistics
- `GET /api/search/tags` - Search by tags
- `GET /api/search/domain/{domain}` - Search by domain
- `GET /api/search/similar/{chunk_id}` - Find similar content
- `GET /api/search/tags/available` - Get available tags

### Graph Exploration
- `GET /api/graph` - Get graph data
- `GET /api/conversations` - Get conversations
- `GET /api/conversations/{chat_id}/messages` - Get messages for a chat
- `GET /api/chunks/{chunk_id}` - Get chunk details
- `GET /api/graph/visualization` - Get graph visualization data

### Debug Endpoints
- `GET /api/debug/schema` - Get database schema information

## Development

### Adding New Routes

1. Create a new route file in `routes/`:
   ```python
   # routes/new_feature.py
   from fastapi import APIRouter
   from models import ApiResponse
   
   router = APIRouter(prefix="/api", tags=["new-feature"])
   
   @router.get("/new-endpoint", response_model=ApiResponse)
   async def new_endpoint():
       return ApiResponse(
           data={"message": "New endpoint"},
           message="Success"
       )
   ```

2. Add to `main.py`:
   ```python
   from routes.new_feature import router as new_feature_router, set_global_connections as set_new_feature_connections
   
   # In startup_event():
   set_new_feature_connections(neo4j_driver, qdrant_client, embedding_model)
   
   # Include router
   app.include_router(new_feature_router)
   ```

### Adding New Models

1. Create a new model file in `models/`:
   ```python
   # models/new_models.py
   from pydantic import BaseModel
   
   class NewModel(BaseModel):
       field: str
   ```

2. Add to `models/__init__.py`:
   ```python
   from .new_models import NewModel
   __all__ = ["ApiResponse", "NewModel"]
   ```

### Adding New Utilities

1. Create a new utility file in `utils/`:
   ```python
   # utils/new_helpers.py
   def new_helper_function():
       return "helper result"
   ```

2. Add to `utils/__init__.py`:
   ```python
   from .new_helpers import new_helper_function
   __all__ = ["convert_neo4j_to_json", "get_config", "new_helper_function"]
   ```

## Configuration

The API uses environment variables for configuration:

- `NEO4J_URI`: Neo4j connection URI (default: bolt://localhost:7687)
- `NEO4J_USER`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password (no default; set via env)
- `QDRANT_HOST`: Qdrant server host (default: localhost)
- `QDRANT_PORT`: Qdrant server port (default: 6335)
- `QDRANT_COLLECTION`: Qdrant collection name (default: chatmind_embeddings)
- `EMBEDDING_MODEL`: Sentence transformer model (default: all-MiniLM-L6-v2)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `API_DEBUG`: Enable debug mode (default: false)

## Testing

Run the comprehensive test suite:

```bash
# Start the server
python run.py

# Run all tests
python test_simple_api.py
```

The test suite covers all 15 endpoints with 100% pass rate.

## Architecture Decisions

### Modular Design
- **Incremental Development**: Built piece by piece with testing at each step
- **Global Connections**: Database connections passed via `set_global_connections` functions
- **Absolute Imports**: Uses absolute imports from the `api` root for simplicity
- **Test-Driven**: All features developed with tests first

### Database Integration
- **Neo4j**: Handles graph relationships, metadata, and complex queries
- **Qdrant**: Handles semantic search with embeddings
- **Hybrid Queries**: Combines both databases for rich exploration
- **Error Handling**: Graceful fallbacks for all database operations

### Performance
- **Singleton Pattern**: Single instances of database drivers and embedding models
- **Connection Pooling**: Efficient database connection management
- **Lazy Loading**: Embedding model loaded only when needed

## Contributing

1. Follow the modular structure
2. Add proper error handling
3. Include type hints
4. Add docstrings
5. Write tests for new features
6. Update this README for new features

## Recent Improvements

- ✅ **Modular Architecture**: Clean separation of routes, models, and utilities
- ✅ **Test-Driven Development**: All endpoints tested and validated
- ✅ **Hybrid Database Integration**: Seamless Neo4j + Qdrant operations
- ✅ **Error Handling**: Robust error handling and graceful fallbacks
- ✅ **Documentation**: Comprehensive API documentation
- ✅ **Performance**: Optimized database connections and queries 