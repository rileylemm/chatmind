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
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Query to get chunk details - message_id and chat_id are properties of the chunk
            result = session.run("""
                MATCH (c:Chunk {chunk_id: $chunk_id})
                RETURN 
                    c.chunk_id as chunk_id,
                    c.content as content,
                    c.message_id as message_id,
                    c.chat_id as chat_id,
                    c.embedding_vector as embedding_vector
            """, chunk_id=chunk_id)
            
            record = result.single()
            if not record:
                # If chunk not found in Neo4j, try to get basic info from Qdrant
                if qdrant_client:
                    try:
                        # Search for the chunk in Qdrant
                        search_result = qdrant_client.search(
                            collection_name=get_config()["qdrant"]["collection_name"],
                            query_vector=[0.0] * 384,  # Dummy vector
                            limit=1,
                            query_filter={
                                "must": [
                                    {"key": "chunk_id", "match": {"value": chunk_id}}
                                ]
                            }
                        )
                        
                        if search_result:
                            payload = search_result[0].payload
                            chunk_data = {
                                "chunk_id": chunk_id,
                                "content": payload.get("content", f"Content for chunk {chunk_id}"),
                                "message_id": payload.get("message_id", "unknown"),
                                "chat_id": payload.get("chat_id", "unknown"),
                                "similarity_score": 1.0
                            }
                        else:
                            chunk_data = {
                                "chunk_id": chunk_id,
                                "content": f"Content for chunk {chunk_id}",
                                "message_id": "not_found",
                                "chat_id": "not_found",
                                "similarity_score": 1.0
                            }
                    except Exception as qdrant_error:
                        logger.warning(f"Qdrant lookup failed: {qdrant_error}")
                        chunk_data = {
                            "chunk_id": chunk_id,
                            "content": f"Content for chunk {chunk_id}",
                            "message_id": "error",
                            "chat_id": "error",
                            "similarity_score": 1.0
                        }
                else:
                    chunk_data = {
                        "chunk_id": chunk_id,
                        "content": f"Content for chunk {chunk_id}",
                        "message_id": "no_qdrant",
                        "chat_id": "no_qdrant",
                        "similarity_score": 1.0
                    }
            else:
                # Found in Neo4j
                chunk_data = {
                    "chunk_id": record["chunk_id"],
                    "content": record["content"],
                    "message_id": record["message_id"] or "unknown",
                    "chat_id": record["chat_id"] or "unknown",
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


@router.get("/graph/expand/{node_id}", response_model=ApiResponse)
async def expand_node(node_id: str):
    """Expand a node to show its connections"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Get node and its immediate neighbors
            result = session.run("""
                MATCH (node)
                WHERE node.chat_id = $node_id OR node.message_id = $node_id OR node.chunk_id = $node_id
                OPTIONAL MATCH (node)-[r]-(neighbor)
                RETURN 
                    node.chat_id as node_chat_id,
                    node.message_id as node_message_id,
                    node.chunk_id as node_chunk_id,
                    labels(node) as node_labels,
                    properties(node) as node_props,
                    type(r) as rel_type,
                    labels(neighbor) as neighbor_labels,
                    properties(neighbor) as neighbor_props
                LIMIT 50
            """, node_id=node_id)
            
            node_data = None
            connections = []
            
            for record in result:
                if not node_data:
                    # First record contains the node data
                    node_data = {
                        "id": node_id,
                        "chat_id": record["node_chat_id"],
                        "message_id": record["node_message_id"],
                        "chunk_id": record["node_chunk_id"],
                        "labels": record["node_labels"],
                        "properties": convert_neo4j_to_json(record["node_props"])
                    }
                
                # Add connection if relationship exists
                if record["rel_type"]:
                    connections.append({
                        "relationship_type": record["rel_type"],
                        "neighbor_labels": record["neighbor_labels"],
                        "neighbor_properties": convert_neo4j_to_json(record["neighbor_props"])
                    })
            
            if not node_data:
                raise HTTPException(status_code=404, detail="Node not found")
            
            return ApiResponse(
                data={
                    "node": node_data,
                    "connections": connections
                },
                message=f"Node expansion: {len(connections)} connections found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Node expansion error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 