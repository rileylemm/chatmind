#!/usr/bin/env python3
"""
ChatMind API - Dual Layer Graph Support

Provides REST API endpoints for querying the Neo4j knowledge graph
with support for both raw conversation data and semantic chunk data.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from fastapi import Body
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

from services import Neo4jService, StatsService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatMind API - Dual Layer Graph",
    description="Modern API for querying ChatGPT knowledge graph with raw and semantic layers",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models
# ============================================================================

class GraphNode(BaseModel):
    id: str
    type: str = Field(..., description="Node type: Topic, Chat, Message, Chunk, Tag")
    properties: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str = Field(..., description="Edge type: CONTAINS, HAS_CHUNK, SUMMARIZES, TAGGED_WITH, HAS_TOPIC, SIMILAR_TO")
    properties: Optional[Dict[str, Any]] = None

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class Message(BaseModel):
    id: str
    content: str
    role: str
    timestamp: Optional[float] = None
    chunk_count: Optional[int] = None
    chat_id: Optional[str] = None

class Chat(BaseModel):
    id: str
    title: str
    create_time: Optional[float] = None
    message_count: Optional[int] = None

class Chunk(BaseModel):
    id: int
    text: str
    source_message_id: str
    cluster_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    topic: Optional[Dict[str, Any]] = None

class Topic(BaseModel):
    id: int
    name: str
    size: int
    top_words: List[str] = Field(default_factory=list)
    sample_titles: List[str] = Field(default_factory=list)

class Tag(BaseModel):
    name: str
    count: int
    category: Optional[str] = None

class Conversation(BaseModel):
    chat_id: str
    title: str
    create_time: Optional[float] = None
    message_count: int
    messages: List[Message] = Field(default_factory=list)

class DashboardStats(BaseModel):
    total_chats: int
    total_messages: int
    total_chunks: int
    total_topics: int
    active_tags: int
    total_relationships: int
    total_cost: str
    total_calls: int

class ApiResponse(BaseModel):
    data: Any
    message: Optional[str] = None
    error: Optional[str] = None

# ============================================================================
# Dependency Injection
# ============================================================================

async def get_neo4j_service() -> Neo4jService:
    """Get Neo4j service instance"""
    # Configure Neo4j connection from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    service = Neo4jService()
    service.configure(neo4j_uri, neo4j_user, neo4j_password)
    await service.connect()
    return service

async def get_stats_service() -> StatsService:
    """Get stats service instance"""
    # Configure Neo4j connection from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    neo4j_service = Neo4jService()
    neo4j_service.configure(neo4j_uri, neo4j_user, neo4j_password)
    await neo4j_service.connect()
    return StatsService(neo4j_service)

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting ChatMind API with dual layer graph support")
    
    # Configure Neo4j connection from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    # Test Neo4j connection
    try:
        service = Neo4jService()
        service.configure(neo4j_uri, neo4j_user, neo4j_password)
        await service.connect()
        logger.info("Successfully connected to Neo4j")
        service.close()
    except Exception as e:
        logger.warning(f"Neo4j connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ChatMind API")

# ============================================================================
# Basic Endpoints
# ============================================================================

@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint"""
    return ApiResponse(
        data={
            "name": "ChatMind API",
            "version": "3.0.0",
            "description": "Dual Layer Graph API for ChatGPT data analysis",
            "endpoints": {
                "raw_layer": "/api/conversations",
                "chunk_layer": "/api/chunks",
                "semantic_search": "/api/search/semantic",
                "graph": "/api/graph",
                "topics": "/api/topics",
                "chats": "/api/chats"
            }
        },
        message="ChatMind API is running"
    )

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Configure Neo4j connection from environment
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        
        service = Neo4jService()
        service.configure(neo4j_uri, neo4j_user, neo4j_password)
        await service.connect()
        service.close()
        return ApiResponse(data={"status": "healthy"}, message="All services operational")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")

# ============================================================================
# Dashboard & Statistics
# ============================================================================

@app.get("/api/stats/dashboard", response_model=ApiResponse)
async def get_dashboard_stats(
    stats_service: StatsService = Depends(get_stats_service)
):
    """Get comprehensive dashboard statistics"""
    try:
        stats = stats_service.get_dashboard_stats()
        return ApiResponse(data=stats, message="Dashboard statistics retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {e}")

# ============================================================================
# Graph Data Endpoints
# ============================================================================

@app.get("/api/graph", response_model=ApiResponse)
async def get_graph_data(
    limit: int = 100,
    node_types: Optional[str] = None,
    parent_id: Optional[str] = None,
    use_semantic_positioning: bool = False,
    layer: str = "both",  # "raw", "chunk", or "both"
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get graph data with dual layer support"""
    try:
        # Parse node types
        types = None
        if node_types:
            types = [t.strip() for t in node_types.split(",")]
        
        data = neo4j_service.get_graph_data(
            limit=limit,
            node_types=types,
            parent_id=parent_id,
            use_semantic_positioning=use_semantic_positioning,
            layer=layer
        )
        
        return ApiResponse(data=data, message=f"Graph data retrieved (layer: {layer})")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {e}")

# ============================================================================
# Raw Layer Endpoints
# ============================================================================

@app.get("/api/conversations", response_model=ApiResponse)
async def get_raw_conversations(
    limit: int = 50,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get raw conversation data (Chat and Message nodes)"""
    try:
        conversations = neo4j_service.get_raw_conversations(limit=limit)
        return ApiResponse(data=conversations, message=f"Retrieved {len(conversations)} conversations")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversations: {e}")

@app.get("/api/chats", response_model=ApiResponse)
async def get_chats(
    limit: int = 50,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get all chats"""
    try:
        chats = neo4j_service.get_chats(limit=limit)
        return ApiResponse(data=chats, message=f"Retrieved {len(chats)} chats")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chats: {e}")

@app.get("/api/chats/{chat_id}/messages", response_model=ApiResponse)
async def get_chat_messages(
    chat_id: str,
    limit: int = 100,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get messages for a specific chat"""
    try:
        messages = neo4j_service.get_messages_for_chat(chat_id, limit=limit)
        return ApiResponse(data=messages, message=f"Retrieved {len(messages)} messages for chat {chat_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat messages: {e}")

@app.post("/api/chats/{chat_id}/summary", response_model=ApiResponse)
async def generate_chat_summary(
    chat_id: str,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Generate a summary for a specific chat"""
    try:
        # For now, return a simple summary based on chat data
        # In a real implementation, this would use an LLM to generate summaries
        messages = neo4j_service.get_messages_for_chat(chat_id, limit=100)
        if not messages:
            raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
        
        # Create a simple summary
        summary = {
            "chat_id": chat_id,
            "message_count": len(messages),
            "summary": f"Chat with {len(messages)} messages",
            "generated_at": datetime.now().isoformat()
        }
        
        return ApiResponse(data=summary, message=f"Generated summary for chat {chat_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chat summary: {e}")

@app.get("/api/messages/{message_id}", response_model=ApiResponse)
async def get_message_by_id(
    message_id: str,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get a specific message by ID with its chunks"""
    try:
        message = neo4j_service.get_message_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return ApiResponse(data=message, message="Message retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message: {e}")

# ============================================================================
# Chunk Layer Endpoints
# ============================================================================

@app.get("/api/chunks", response_model=ApiResponse)
async def get_semantic_chunks(
    limit: int = 100,
    cluster_id: Optional[int] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get semantic chunks with embeddings and tags"""
    try:
        chunks = neo4j_service.get_semantic_chunks(limit=limit, cluster_id=cluster_id)
        return ApiResponse(data=chunks, message=f"Retrieved {len(chunks)} chunks")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {e}")

@app.get("/api/messages/{message_id}/chunks", response_model=ApiResponse)
async def get_chunks_for_message(
    message_id: str,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get chunks associated with a specific message"""
    try:
        chunks = neo4j_service.get_chunks_for_message(message_id)
        return ApiResponse(data=chunks, message=f"Retrieved {len(chunks)} chunks for message {message_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chunks for message: {e}")

# ============================================================================
# Semantic Layer Endpoints
# ============================================================================

@app.get("/api/topics", response_model=ApiResponse)
async def get_topics(
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get all topics"""
    try:
        topics = neo4j_service.get_topics()
        return ApiResponse(data=topics, message=f"Retrieved {len(topics)} topics")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topics: {e}")

@app.get("/api/clusters/{cluster_id}", response_model=ApiResponse)
async def get_cluster_details(
    cluster_id: int,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get details for a specific cluster/topic"""
    try:
        cluster = neo4j_service.get_cluster_details(cluster_id)
        if not cluster:
            raise HTTPException(status_code=404, detail="Cluster not found")
        return ApiResponse(data=cluster, message="Cluster details retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cluster details: {e}")

@app.get("/api/tags", response_model=ApiResponse)
async def get_tags(
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get all tags"""
    try:
        tags = neo4j_service.get_tags()
        return ApiResponse(data=tags, message=f"Retrieved {len(tags)} tags")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {e}")

# ============================================================================
# Search Endpoints
# ============================================================================

@app.get("/api/search", response_model=ApiResponse)
async def search_messages(
    query: str,
    limit: int = 50,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Search messages by content"""
    try:
        messages = neo4j_service.search_messages(query, limit=limit)
        return ApiResponse(data=messages, message=f"Found {len(messages)} messages for query '{query}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search messages: {e}")

@app.get("/api/search/semantic", response_model=ApiResponse)
async def search_by_semantic_similarity(
    query: str,
    limit: int = 20,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Search chunks by semantic similarity"""
    try:
        chunks = neo4j_service.search_by_semantic_similarity(query, limit=limit)
        return ApiResponse(data=chunks, message=f"Found {len(chunks)} semantically similar chunks for query '{query}'")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search by semantic similarity: {e}")

@app.post("/api/search/advanced", response_model=ApiResponse)
async def advanced_search(
    query: str = Body(...),
    filters: Dict[str, Any] = Body(default_factory=dict),
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Advanced search with filters"""
    try:
        results = neo4j_service.advanced_search(query, filters)
        return ApiResponse(data=results, message=f"Found {len(results)} results for advanced search")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform advanced search: {e}")

# ============================================================================
# Graph Exploration Endpoints
# ============================================================================

@app.get("/api/graph/expand/{node_id}", response_model=ApiResponse)
async def expand_node(
    node_id: str,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Expand a node to show its relationships"""
    try:
        expansion = neo4j_service.expand_node(node_id)
        if "error" in expansion:
            raise HTTPException(status_code=404, detail=expansion["error"])
        return ApiResponse(data=expansion, message="Node expanded successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to expand node: {e}")

# ============================================================================
# Discovery APIs
# ============================================================================

@app.get("/api/discover/topics", response_model=ApiResponse)
async def discover_topics(
    limit: int = 20,
    min_count: Optional[int] = None,
    domain: Optional[str] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get most discussed topics with frequency and trends"""
    try:
        topics = neo4j_service.discover_topics(limit, min_count, domain)
        return ApiResponse(data=topics, message="Topics discovered successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover topics: {e}")

@app.get("/api/discover/domains", response_model=ApiResponse)
async def discover_domains(
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get domain distribution and insights"""
    try:
        domains = neo4j_service.discover_domains()
        return ApiResponse(data=domains, message="Domain insights retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover domains: {e}")

@app.get("/api/discover/clusters", response_model=ApiResponse)
async def discover_clusters(
    limit: int = 50,
    min_size: Optional[int] = None,
    include_positioning: bool = True,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get semantic clusters with positioning and summaries"""
    try:
        clusters = neo4j_service.discover_clusters(limit, min_size, include_positioning)
        return ApiResponse(data=clusters, message="Clusters discovered successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover clusters: {e}")

# ============================================================================
# Enhanced Search APIs
# ============================================================================

@app.get("/api/search/content", response_model=ApiResponse)
async def search_content(
    query: str,
    limit: int = 50,
    role: Optional[str] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Full-text search across messages"""
    try:
        results = neo4j_service.search_content(query, limit, role)
        return ApiResponse(data=results, message="Content search completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search content: {e}")

@app.get("/api/search/tags", response_model=ApiResponse)
async def search_by_tags(
    tags: str,
    limit: int = 50,
    exact_match: bool = False,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Search by specific tags or tag combinations"""
    try:
        tag_list = [tag.strip() for tag in tags.split(",")]
        results = neo4j_service.search_by_tags(tag_list, limit, exact_match)
        return ApiResponse(data=results, message="Tag search completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search by tags: {e}")

# ============================================================================
# Graph Exploration APIs
# ============================================================================

@app.get("/api/graph/visualization", response_model=ApiResponse)
async def get_visualization_data(
    node_types: Optional[str] = None,
    limit: int = 100,
    include_edges: bool = True,
    filter_domain: Optional[str] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get data for 2D/3D graph visualization"""
    try:
        node_type_list = [nt.strip() for nt in node_types.split(",")] if node_types else None
        data = neo4j_service.get_visualization_data(node_type_list, limit, include_edges, filter_domain)
        return ApiResponse(data=data, message="Visualization data retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get visualization data: {e}")

@app.get("/api/graph/connections", response_model=ApiResponse)
async def find_connections(
    source_id: str,
    target_id: Optional[str] = None,
    max_hops: int = 3,
    relationship_types: Optional[str] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Find connections between different conversations or topics"""
    try:
        rel_types = [rt.strip() for rt in relationship_types.split(",")] if relationship_types else None
        connections = neo4j_service.find_connections(source_id, target_id, max_hops, rel_types)
        return ApiResponse(data=connections, message="Connections found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find connections: {e}")

@app.get("/api/graph/neighbors", response_model=ApiResponse)
async def get_neighbors(
    node_id: str,
    limit: int = 10,
    min_similarity: float = 0.7,
    relationship_type: Optional[str] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get semantic neighbors of a conversation or cluster"""
    try:
        neighbors = neo4j_service.get_neighbors(node_id, limit, min_similarity, relationship_type)
        return ApiResponse(data=neighbors, message="Neighbors retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get neighbors: {e}")

# ============================================================================
# Analytics APIs
# ============================================================================

@app.get("/api/analytics/patterns", response_model=ApiResponse)
async def analyze_patterns(
    timeframe: Optional[str] = None,
    domain: Optional[str] = None,
    include_sentiment: bool = True,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Analyze conversation patterns and trends"""
    try:
        patterns = neo4j_service.analyze_patterns(timeframe, domain, include_sentiment)
        return ApiResponse(data=patterns, message="Pattern analysis completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {e}")

@app.get("/api/analytics/sentiment", response_model=ApiResponse)
async def analyze_sentiment(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: Optional[str] = None,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Sentiment analysis over time"""
    try:
        sentiment = neo4j_service.analyze_sentiment(start_date, end_date, group_by)
        return ApiResponse(data=sentiment, message="Sentiment analysis completed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze sentiment: {e}")

# ============================================================================
# Custom Query Endpoints
# ============================================================================

@app.post("/api/query/neo4j", response_model=ApiResponse)
async def custom_neo4j_query(
    query: str = Body(...),
    params: Optional[Dict[str, Any]] = Body(default=None),
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Execute custom Neo4j Cypher query"""
    try:
        if not neo4j_service.driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_service.driver.session() as session:
            if params:
                result = session.run(query, **params)
            else:
                result = session.run(query)
            
            # Convert result to list of dictionaries
            records = []
            for record in result:
                record_dict = {}
                for key, value in record.items():
                    if hasattr(value, 'id'):
                        # Handle Neo4j nodes/relationships
                        record_dict[key] = {
                            "id": value.id,
                            "type": list(value.labels)[0] if hasattr(value, 'labels') else type(value).__name__,
                            "properties": dict(value)
                        }
                    else:
                        record_dict[key] = value
                records.append(record_dict)
            
            return ApiResponse(data=records, message=f"Query executed successfully, returned {len(records)} records")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {e}")

# ============================================================================
# Cost Tracking Endpoints
# ============================================================================

@app.get("/api/costs/statistics", response_model=ApiResponse)
async def get_cost_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    operation: Optional[str] = None,
    stats_service: StatsService = Depends(get_stats_service)
):
    """Get cost tracking statistics"""
    try:
        stats = stats_service.get_cost_statistics(start_date, end_date, operation)
        return ApiResponse(data=stats, message="Cost statistics retrieved")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost statistics: {e}")

# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/api/health/neo4j", response_model=ApiResponse)
async def neo4j_health_check():
    """Check Neo4j connection health"""
    try:
        service = Neo4jService()
        await service.connect()
        
        # Test a simple query
        with service.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
        
        service.close()
        return ApiResponse(
            data={"status": "healthy", "node_count": node_count},
            message="Neo4j connection is healthy"
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Neo4j health check failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 