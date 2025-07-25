#!/usr/bin/env python3
"""
ChatMind API - Clean, Modern FastAPI Backend

Provides REST API endpoints for querying the Neo4j knowledge graph
and serving data to the frontend visualization.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
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
    title="ChatMind API",
    description="Modern API for querying ChatGPT knowledge graph",
    version="2.0.0",
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
    type: str = Field(..., description="Node type: Topic, Chat, Message, Tag")
    properties: Dict[str, Any] = Field(default_factory=dict)
    position: Optional[Dict[str, float]] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str = Field(..., description="Edge type: CONTAINS, SUMMARIZES, HAS_TOPIC, RELATED_TO")
    properties: Optional[Dict[str, Any]] = None

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class Message(BaseModel):
    id: str
    content: str
    role: str
    timestamp: Optional[float] = None
    cluster_id: Optional[int] = None
    chat_id: Optional[str] = None

class Chat(BaseModel):
    id: str
    title: str
    create_time: Optional[float] = None
    message_count: Optional[int] = None

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

class DashboardStats(BaseModel):
    total_chats: int
    total_messages: int
    active_tags: int
    total_cost: str
    total_clusters: int
    total_calls: int

class ApiResponse(BaseModel):
    data: Any
    message: Optional[str] = None
    error: Optional[str] = None

# ============================================================================
# Service Instances
# ============================================================================

neo4j_service = Neo4jService()
stats_service = StatsService()

# ============================================================================
# Dependencies
# ============================================================================

async def get_neo4j_service() -> Neo4jService:
    return neo4j_service

async def get_stats_service() -> StatsService:
    return stats_service

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting ChatMind API...")
    
    # Configure Neo4j service
    neo4j_service.configure(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password")
    )
    
    # Connect to Neo4j
    try:
        await neo4j_service.connect()
        logger.info("Successfully connected to Neo4j")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        # Don't fail startup, but log the error

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ChatMind API...")
    neo4j_service.close()

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=ApiResponse)
async def root():
    """Root endpoint"""
    return ApiResponse(
        data={"message": "ChatMind API v2.0.0"},
        message="Welcome to ChatMind API"
    )

@app.get("/health", response_model=ApiResponse)
async def health_check():
    """Health check endpoint"""
    return ApiResponse(
        data={"status": "healthy", "timestamp": datetime.now().isoformat()},
        message="API is healthy"
    )

@app.get("/api/stats/dashboard", response_model=ApiResponse)
async def get_dashboard_stats(
    stats_service: StatsService = Depends(get_stats_service)
):
    """Get dashboard statistics"""
    try:
        stats = stats_service.get_dashboard_stats()
        return ApiResponse(data=stats, message="Dashboard stats retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

@app.get("/graph", response_model=ApiResponse)
async def get_graph_data(
    limit: int = 100,
    node_types: Optional[str] = None,
    parent_id: Optional[str] = None,
    use_semantic_positioning: bool = False,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get graph data with optional filtering"""
    try:
        # Parse node_types from comma-separated string
        node_types_list = None
        if node_types:
            node_types_list = [t.strip() for t in node_types.split(",")]
        
        graph_data = neo4j_service.get_graph_data(
            limit=limit,
            node_types=node_types_list,
            parent_id=parent_id,
            use_semantic_positioning=use_semantic_positioning
        )
        
        return ApiResponse(data=graph_data, message="Graph data retrieved successfully")
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Error getting graph data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get graph data")

@app.get("/topics", response_model=ApiResponse)
async def get_topics(
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get all topics"""
    try:
        topics = neo4j_service.get_topics()
        return ApiResponse(data=topics, message="Topics retrieved successfully")
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get topics")

@app.get("/chats", response_model=ApiResponse)
async def get_chats(
    limit: int = 50,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get all chats"""
    try:
        chats = neo4j_service.get_chats(limit=limit)
        return ApiResponse(data=chats, message="Chats retrieved successfully")
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Error getting chats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chats")

@app.get("/chats/{chat_id}/messages", response_model=ApiResponse)
async def get_chat_messages(
    chat_id: str,
    limit: int = 100,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Get messages for a specific chat"""
    try:
        messages = neo4j_service.get_messages_for_chat(chat_id, limit=limit)
        return ApiResponse(data=messages, message="Chat messages retrieved successfully")
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat messages")

@app.get("/search", response_model=ApiResponse)
async def search_messages(
    query: str,
    limit: int = 50,
    neo4j_service: Neo4jService = Depends(get_neo4j_service)
):
    """Search messages by content"""
    try:
        messages = neo4j_service.search_messages(query, limit=limit)
        return ApiResponse(data=messages, message="Search results retrieved successfully")
    except ConnectionError as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to search messages")

@app.get("/costs/statistics", response_model=ApiResponse)
async def get_cost_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    operation: Optional[str] = None,
    stats_service: StatsService = Depends(get_stats_service)
):
    """Get detailed cost statistics"""
    try:
        stats = stats_service.get_cost_statistics(
            start_date=start_date,
            end_date=end_date,
            operation=operation
        )
        return ApiResponse(data=stats, message="Cost statistics retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting cost statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cost statistics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 