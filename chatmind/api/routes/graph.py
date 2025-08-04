"""
Graph-related endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException, Query
from models import ApiResponse
from utils import convert_neo4j_to_json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["graph"])

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


@router.get("/graph", response_model=ApiResponse)
async def get_graph_data(
    limit: int = Query(default=100, ge=1, le=1000)
):
    """Get basic graph data"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Simple query to get nodes and relationships
            result = session.run("""
                MATCH (n)
                RETURN n
                LIMIT $limit
            """, limit=limit)
            
            nodes = []
            for record in result:
                node = record["n"]
                if node:
                    nodes.append({
                        "id": str(node.id),
                        "labels": list(node.labels),
                        "properties": convert_neo4j_to_json(dict(node))
                    })
            
            return ApiResponse(
                data={
                    "nodes": nodes,
                    "total": len(nodes)
                },
                message=f"Graph data retrieved ({len(nodes)} nodes)"
            )
            
    except Exception as e:
        logger.error(f"Graph data error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=ApiResponse)
async def get_conversations(
    limit: int = Query(default=50, ge=1, le=100)
):
    """Get conversations list"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                RETURN c.title as title, c.chat_id as chat_id
                LIMIT $limit
            """, limit=limit)
            
            conversations = []
            for record in result:
                conversations.append({
                    "title": record["title"],
                    "chat_id": record["chat_id"]
                })
            
            return ApiResponse(
                data=conversations,
                message=f"Found {len(conversations)} conversations"
            )
            
    except Exception as e:
        logger.error(f"Conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{chat_id}/messages", response_model=ApiResponse)
async def get_conversation_messages(
    chat_id: str,
    limit: int = Query(default=50, ge=1, le=100)
):
    """Get messages for a specific conversation"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat {chat_id: $chat_id})
                MATCH (m:Message)
                WHERE m.chat_id = $chat_id
                RETURN m.content as content, m.message_id as message_id, m.timestamp as timestamp
                ORDER BY m.timestamp
                LIMIT $limit
            """, chat_id=chat_id, limit=limit)
            
            messages = []
            for record in result:
                messages.append({
                    "content": record["content"],
                    "message_id": record["message_id"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"])
                })
            
            return ApiResponse(
                data=messages,
                message=f"Found {len(messages)} messages for conversation {chat_id}"
            )
            
    except Exception as e:
        logger.error(f"Conversation messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks/{chunk_id}", response_model=ApiResponse)
async def get_chunk_details(chunk_id: str):
    """Get details for a specific chunk"""
    try:
        # For now, return basic chunk info
        chunk_data = {
            "chunk_id": chunk_id,
            "content": f"Content for chunk {chunk_id}",
            "message_id": "sample_message_id",
            "chat_id": "sample_chat_id",
            "similarity_score": 1.0
        }
        
        return ApiResponse(
            data=chunk_data,
            message=f"Chunk details retrieved for {chunk_id}"
        )
        
    except Exception as e:
        logger.error(f"Chunk details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/visualization", response_model=ApiResponse)
async def get_graph_visualization(
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get graph data for visualization"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Get nodes and relationships for visualization
            result = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN 
                    id(n) as node_id,
                    labels(n) as node_labels,
                    properties(n) as node_props,
                    type(r) as rel_type,
                    id(m) as target_id
                LIMIT $limit
            """, limit=limit)
            
            nodes = {}
            edges = []
            
            for record in result:
                # Add source node
                node_id = record["node_id"]
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "labels": record["node_labels"],
                        "properties": convert_neo4j_to_json(record["node_props"])
                    }
                
                # Add relationship if exists
                if record["rel_type"] and record["target_id"]:
                    edges.append({
                        "source": node_id,
                        "target": record["target_id"],
                        "type": record["rel_type"]
                    })
                    
                    # Add target node
                    target_id = record["target_id"]
                    if target_id not in nodes:
                        nodes[target_id] = {
                            "id": target_id,
                            "labels": [],  # We don't have target labels in this query
                            "properties": {}
                        }
            
            return ApiResponse(
                data={
                    "nodes": list(nodes.values()),
                    "edges": edges
                },
                message=f"Graph visualization data: {len(nodes)} nodes, {len(edges)} edges"
            )
            
    except Exception as e:
        logger.error(f"Graph visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 