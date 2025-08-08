"""
Health-related endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException
from models import ApiResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["health"])

# Global database connections (imported from main)
neo4j_driver = None
qdrant_client = None
embedding_model = None


def set_global_connections(neo4j, qdrant, embedding):
    """Set global database connections"""
    global neo4j_driver, qdrant_client, embedding_model
    neo4j_driver = neo4j
    qdrant_client = qdrant
    embedding_model = embedding


@router.get("/health", response_model=ApiResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test Neo4j connection
        neo4j_status = "connected" if neo4j_driver else "disconnected"
        
        return ApiResponse(
            data={"status": "healthy", "neo4j": neo4j_status},
            message="All services operational"
        )
    except Exception as e:
        return ApiResponse(
            data={"status": "unhealthy"},
            message="Service issues detected",
            error=str(e)
        ) 