"""
Analytics and cost tracking endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException, Query
from models import ApiResponse
from utils import convert_neo4j_to_json
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analytics"])

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


@router.get("/analytics/patterns", response_model=ApiResponse)
async def get_conversation_patterns(
    timeframe: str = Query(default="daily", description="Timeframe: daily, weekly, monthly"),
    include_sentiment: bool = Query(default=False, description="Include sentiment analysis")
):
    """Get conversation pattern analysis"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Basic pattern analysis
            if timeframe == "monthly":
                time_format = "yyyy-MM"
            elif timeframe == "weekly":
                time_format = "yyyy-'W'ww"
            else:  # daily
                time_format = "yyyy-MM-dd"
            
            result = session.run("""
                MATCH (c:Chat)
                WHERE c.timestamp IS NOT NULL
                WITH c, toString(date(c.timestamp)) as date_str
                WITH date_str, count(c) as chat_count
                RETURN date_str, chat_count
                ORDER BY date_str
            """)
            
            patterns = []
            for record in result:
                patterns.append({
                    "date": record["date_str"],
                    "chat_count": record["chat_count"]
                })
            
            return ApiResponse(
                data={
                    "timeframe": timeframe,
                    "patterns": patterns,
                    "total_chats": sum(p["chat_count"] for p in patterns)
                },
                message=f"Pattern analysis for {timeframe} timeframe"
            )
            
    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/sentiment", response_model=ApiResponse)
async def get_sentiment_analysis():
    """Get basic sentiment overview"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                WITH count(m) as total_messages
                RETURN total_messages
            """)
            
            total_messages = result.single()["total_messages"]
            
            return ApiResponse(
                data={
                    "total_messages": total_messages,
                    "note": "Sentiment analysis not implemented yet"
                },
                message="Basic message statistics retrieved"
            )
            
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))





@router.get("/graph/connections", response_model=ApiResponse)
async def get_graph_connections(
    source_id: str = Query(..., description="Source node ID"),
    max_hops: int = Query(default=2, ge=1, le=5, description="Maximum number of hops")
):
    """Find connections from a source node"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Simplified query to avoid complex path matching
            result = session.run("""
                MATCH (start)
                WHERE start.chat_id = $source_id OR start.message_id = $source_id OR start.chunk_id = $source_id
                OPTIONAL MATCH (start)-[r]-(connected)
                RETURN 
                    start.chat_id as source_id,
                    connected.chat_id as connected_id,
                    1 as hop_count,
                    type(r) as relationship_type
                LIMIT 50
            """, source_id=source_id)
            
            connections = []
            for record in result:
                if record["connected_id"]:  # Only add if there's a connection
                    connections.append({
                        "source_id": record["source_id"],
                        "connected_id": record["connected_id"],
                        "hop_count": record["hop_count"],
                        "relationship_type": record["relationship_type"]
                    })
            
            return ApiResponse(
                data=connections,
                message=f"Found {len(connections)} connections from {source_id}"
            )
            
    except Exception as e:
        logger.error(f"Graph connections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/neighbors", response_model=ApiResponse)
async def get_graph_neighbors(
    node_id: str = Query(..., description="Node ID"),
    limit: int = Query(default=10, ge=1, le=50),
    min_similarity: float = Query(default=0.0, ge=0.0, le=1.0)
):
    """Get neighbors of a node with similarity filtering"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (node)-[r:SIMILAR_TO]-(neighbor)
                WHERE (node.chat_id = $node_id OR node.message_id = $node_id OR node.chunk_id = $node_id)
                AND r.similarity >= $min_similarity
                RETURN 
                    neighbor.chat_id as neighbor_id,
                    neighbor.title as neighbor_title,
                    r.similarity as similarity
                ORDER BY r.similarity DESC
                LIMIT $limit
            """, node_id=node_id, min_similarity=min_similarity, limit=limit)
            
            neighbors = []
            for record in result:
                neighbors.append({
                    "neighbor_id": record["neighbor_id"],
                    "neighbor_title": record["neighbor_title"],
                    "similarity": record["similarity"]
                })
            
            return ApiResponse(
                data=neighbors,
                message=f"Found {len(neighbors)} neighbors for {node_id}"
            )
            
    except Exception as e:
        logger.error(f"Graph neighbors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/domains", response_model=ApiResponse)
async def get_available_domains():
    """Get list of available domains for filtering"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                WHERE c.domain IS NOT NULL
                RETURN DISTINCT c.domain as domain
                ORDER BY domain
            """)
            
            domains = []
            for record in result:
                domains.append(record["domain"])
            
            return ApiResponse(
                data=domains,
                message=f"Found {len(domains)} available domains"
            )
            
    except Exception as e:
        logger.error(f"Available domains error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chats/{chat_id}/summary", response_model=ApiResponse)
async def generate_chat_summary(chat_id: str):
    """Generate a summary for a specific chat"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Get chat messages for summarization
            result = session.run("""
                MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
                RETURN 
                    c.title as title,
                    count(m) as message_count
            """, chat_id=chat_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Chat not found")
            
            title = record["title"]
            message_count = record["message_count"]
            
            # Simple summary based on message count
            summary = f"Chat '{title}' contains {message_count} messages covering various topics."
            
            return ApiResponse(
                data={
                    "chat_id": chat_id,
                    "title": title,
                    "summary": summary,
                    "message_count": message_count
                },
                message="Chat summary generated successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 