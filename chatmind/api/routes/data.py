"""
Data access endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException, Query
from models import ApiResponse
from utils import convert_neo4j_to_json
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["data"])

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


@router.get("/stats/dashboard", response_model=ApiResponse)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Get basic statistics
            stats_result = session.run("""
                MATCH (c:Chat)
                WITH count(c) as chat_count
                MATCH (m:Message)
                WITH chat_count, count(m) as message_count
                MATCH (ch:Chunk)
                WITH chat_count, message_count, count(ch) as chunk_count
                MATCH (t:Tag)
                WITH chat_count, message_count, chunk_count, count(t) as tag_count
                MATCH (cl:Cluster)
                WITH chat_count, message_count, chunk_count, tag_count, count(cl) as cluster_count
                RETURN chat_count, message_count, chunk_count, tag_count, cluster_count
            """)
            
            stats = stats_result.single()
            
            return ApiResponse(
                data={
                    "chats": stats["chat_count"],
                    "messages": stats["message_count"],
                    "chunks": stats["chunk_count"],
                    "tags": stats["tag_count"],
                    "clusters": stats["cluster_count"]
                },
                message="Dashboard statistics retrieved successfully"
            )
            
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/topics", response_model=ApiResponse)
async def get_topics(
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get all topics/clusters"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster)
                OPTIONAL MATCH (cl)-[:HAS_CHUNK]->(ch:Chunk)
                WITH cl, count(ch) as chunk_count
                RETURN 
                    cl.cluster_id as topic_id,
                    cl.name as name,
                    cl.summary as summary,
                    chunk_count as size
                ORDER BY chunk_count DESC
                LIMIT $limit
            """, limit=limit)
            
            topics = []
            for record in result:
                topics.append({
                    "topic_id": record["topic_id"],
                    "name": record["name"],
                    "summary": record["summary"],
                    "size": record["size"]
                })
            
            return ApiResponse(
                data=topics,
                message=f"Found {len(topics)} topics"
            )
            
    except Exception as e:
        logger.error(f"Topics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats", response_model=ApiResponse)
async def get_chats(
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get all chats"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
                WITH c, count(m) as message_count
                RETURN 
                    c.chat_id as id,
                    c.title as title,
                    c.timestamp as timestamp,
                    message_count
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, limit=limit)
            
            chats = []
            for record in result:
                chats.append({
                    "id": record["id"],
                    "title": record["title"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None,
                    "message_count": record["message_count"]
                })
            
            return ApiResponse(
                data=chats,
                message=f"Found {len(chats)} chats"
            )
            
    except Exception as e:
        logger.error(f"Chats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chats/{chat_id}/messages", response_model=ApiResponse)
async def get_chat_messages(
    chat_id: str,
    limit: int = Query(default=50, ge=1, le=200)
):
    """Get messages for a specific chat"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
                RETURN 
                    m.message_id as id,
                    m.content as content,
                    m.role as role,
                    m.timestamp as timestamp
                ORDER BY m.timestamp
                LIMIT $limit
            """, chat_id=chat_id, limit=limit)
            
            messages = []
            for record in result:
                messages.append({
                    "id": record["id"],
                    "content": record["content"],
                    "role": record["role"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None
                })
            
            return ApiResponse(
                data=messages,
                message=f"Found {len(messages)} messages for chat {chat_id}"
            )
            
    except Exception as e:
        logger.error(f"Chat messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks", response_model=ApiResponse)
async def get_chunks(
    limit: int = Query(default=50, ge=1, le=200),
    cluster_id: Optional[str] = Query(default=None, description="Filter by cluster ID")
):
    """Get semantic chunks"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            if cluster_id:
                # Filter by cluster
                query = """
                    MATCH (cl:Cluster {cluster_id: $cluster_id})-[:HAS_CHUNK]->(ch:Chunk)
                    RETURN 
                        ch.chunk_id as chunk_id,
                        ch.content as content,
                        ch.embedding_hash as embedding_hash,
                        cl.cluster_id as cluster_id,
                        cl.name as cluster_name
                    ORDER BY ch.chunk_id
                    LIMIT $limit
                """
                params = {"cluster_id": cluster_id, "limit": limit}
            else:
                # Get all chunks
                query = """
                    MATCH (ch:Chunk)
                    OPTIONAL MATCH (cl:Cluster)-[:HAS_CHUNK]->(ch)
                    RETURN 
                        ch.chunk_id as chunk_id,
                        ch.content as content,
                        ch.embedding_hash as embedding_hash,
                        cl.cluster_id as cluster_id,
                        cl.name as cluster_name
                    ORDER BY ch.chunk_id
                    LIMIT $limit
                """
                params = {"limit": limit}
            
            result = session.run(query, **params)
            
            chunks = []
            for record in result:
                chunks.append({
                    "chunk_id": record["chunk_id"],
                    "content": record["content"],
                    "embedding_hash": record["embedding_hash"],
                    "cluster_id": record["cluster_id"],
                    "cluster_name": record["cluster_name"]
                })
            
            return ApiResponse(
                data=chunks,
                message=f"Found {len(chunks)} chunks"
            )
            
    except Exception as e:
        logger.error(f"Chunks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags", response_model=ApiResponse)
async def get_tags():
    """Get all tags with counts"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)
                RETURN 
                    t.name as name,
                    t.count as count,
                    t.category as category
                ORDER BY t.count DESC
            """)
            
            tags = []
            for record in result:
                tags.append({
                    "name": record["name"],
                    "count": record["count"],
                    "category": record["category"]
                })
            
            return ApiResponse(
                data=tags,
                message=f"Found {len(tags)} tags"
            )
            
    except Exception as e:
        logger.error(f"Tags error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages/{message_id}", response_model=ApiResponse)
async def get_message(message_id: str):
    """Get a single message by ID"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message {message_id: $message_id})
                OPTIONAL MATCH (c:Chat {chat_id: m.chat_id})
                OPTIONAL MATCH (m)-[:HAS_TAG]->(t:Tag)
                RETURN 
                    m.message_id as id,
                    m.content as content,
                    m.role as role,
                    m.timestamp as timestamp,
                    c.title as chat_title,
                    collect(t.name) as tags
            """, message_id=message_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Message not found")
            
            return ApiResponse(
                data={
                    "id": record["id"],
                    "content": record["content"],
                    "role": record["role"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None,
                    "chat_title": record["chat_title"],
                    "tags": record["tags"]
                },
                message="Message retrieved successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/{cluster_id}", response_model=ApiResponse)
async def get_cluster_details(cluster_id: str):
    """Get details for a specific cluster"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster {cluster_id: $cluster_id})
                OPTIONAL MATCH (cl)-[:HAS_CHUNK]->(ch:Chunk)
                WITH cl, collect(ch) as chunks
                RETURN 
                    cl.cluster_id as cluster_id,
                    cl.name as name,
                    cl.summary as summary,
                    cl.size as size,
                    [ch in chunks | ch.content] as chunk_contents
            """, cluster_id=cluster_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Cluster not found")
            
            return ApiResponse(
                data={
                    "cluster_id": record["cluster_id"],
                    "name": record["name"],
                    "summary": record["summary"],
                    "size": record["size"],
                    "chunk_contents": record["chunk_contents"]
                },
                message="Cluster details retrieved successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cluster details error: {e}")
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
                MATCH (c:Chat {chat_id: $chat_id})
                OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
                RETURN 
                    c.title as title,
                    count(m) as message_count
            """, chat_id=chat_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Chat not found")
            
            # For now, return a simple summary
            # In a real implementation, you'd use an AI model to generate the summary
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