"""
Advanced search and query endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException, Query
from models import ApiResponse
from utils import convert_neo4j_to_json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["advanced"])

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


class AdvancedSearchRequest(BaseModel):
    """Request model for advanced search"""
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class Neo4jQueryRequest(BaseModel):
    """Request model for custom Neo4j queries"""
    query: str


@router.post("/search/advanced", response_model=ApiResponse)
async def advanced_search(request: AdvancedSearchRequest):
    """Advanced search with filters"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        filters = request.filters or {}
        limit = filters.get("limit", 10)
        
        with neo4j_driver.session() as session:
            # Build dynamic query based on filters
            query_parts = ["MATCH (m:Message)"]
            params = {"limit": limit}
            
            if request.query:
                query_parts.append("WHERE m.content CONTAINS $search_term")
                params["search_term"] = request.query
            
            # Add date filters
            if "start_date" in filters:
                query_parts.append("AND m.timestamp >= $start_date")
                params["start_date"] = filters["start_date"]
            
            if "end_date" in filters:
                query_parts.append("AND m.timestamp <= $end_date")
                params["end_date"] = filters["end_date"]
            
            # Add tag filters
            if "tags" in filters:
                query_parts.append("MATCH (m)-[:HAS_TAG]->(t:Tag)")
                query_parts.append("WHERE t.name IN $tags")
                params["tags"] = filters["tags"].split(",") if isinstance(filters["tags"], str) else filters["tags"]
            
            # Add domain filters
            if "domain" in filters:
                query_parts.append("MATCH (c:Chat {chat_id: m.chat_id})")
                query_parts.append("WHERE c.domain = $domain")
                params["domain"] = filters["domain"]
            
            query_parts.extend([
                "MATCH (c:Chat {chat_id: m.chat_id})",
                "RETURN",
                "    m.content as content,",
                "    m.message_id as message_id,",
                "    m.role as role,",
                "    m.timestamp as timestamp,",
                "    c.title as conversation_title",
                "ORDER BY m.timestamp DESC",
                "LIMIT $limit"
            ])
            
            query = " ".join(query_parts)
            result = session.run(query, **params)
            
            results = []
            for record in result:
                results.append({
                    "content": record["content"],
                    "message_id": record["message_id"],
                    "role": record["role"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None,
                    "conversation_title": record["conversation_title"]
                })
            
            return ApiResponse(
                data=results,
                message=f"Found {len(results)} results with advanced search"
            )
            
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/neo4j", response_model=ApiResponse)
async def custom_neo4j_query(request: Neo4jQueryRequest):
    """Execute custom Neo4j query"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run(request.query)
            
            # Convert Neo4j records to JSON
            records = []
            for record in result:
                record_dict = {}
                for key, value in record.items():
                    record_dict[key] = convert_neo4j_to_json(value)
                records.append(record_dict)
            
            return ApiResponse(
                data=records,
                message=f"Query executed successfully, returned {len(records)} records"
            )
            
    except Exception as e:
        logger.error(f"Custom Neo4j query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover/topics", response_model=ApiResponse)
async def discover_topics(
    limit: int = Query(default=20, ge=1, le=100),
    min_count: int = Query(default=0, ge=0)
):
    """Discover most discussed topics"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster)
                OPTIONAL MATCH (cl)-[:HAS_CHUNK]->(ch:Chunk)
                WITH cl, count(ch) as chunk_count
                WHERE chunk_count >= $min_count
                RETURN 
                    cl.cluster_id as topic_id,
                    cl.name as name,
                    cl.summary as summary,
                    chunk_count as size
                ORDER BY chunk_count DESC
                LIMIT $limit
            """, limit=limit, min_count=min_count)
            
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
        logger.error(f"Discover topics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover/domains", response_model=ApiResponse)
async def discover_domains():
    """Discover domain distribution"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                WHERE c.domain IS NOT NULL
                RETURN 
                    c.domain as domain,
                    count(c) as chat_count
                ORDER BY chat_count DESC
            """)
            
            domains = []
            for record in result:
                domains.append({
                    "domain": record["domain"],
                    "chat_count": record["chat_count"]
                })
            
            return ApiResponse(
                data=domains,
                message=f"Found {len(domains)} domains"
            )
            
    except Exception as e:
        logger.error(f"Discover domains error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover/clusters", response_model=ApiResponse)
async def discover_clusters(
    limit: int = Query(default=20, ge=1, le=100),
    min_size: int = Query(default=0, ge=0),
    include_positioning: bool = Query(default=True)
):
    """Discover semantic clusters"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            if include_positioning:
                result = session.run("""
                    MATCH (cl:Cluster)
                    OPTIONAL MATCH (cl)-[:HAS_CHUNK]->(ch:Chunk)
                    WITH cl, count(ch) as chunk_count
                    WHERE chunk_count >= $min_size
                    OPTIONAL MATCH (cl)-[:HAS_POSITION]->(pos:ClusterPosition)
                    RETURN 
                        cl.cluster_id as cluster_id,
                        cl.name as name,
                        cl.summary as summary,
                        chunk_count as size,
                        pos.x as x,
                        pos.y as y
                    ORDER BY chunk_count DESC
                    LIMIT $limit
                """, limit=limit, min_size=min_size)
            else:
                result = session.run("""
                    MATCH (cl:Cluster)
                    OPTIONAL MATCH (cl)-[:HAS_CHUNK]->(ch:Chunk)
                    WITH cl, count(ch) as chunk_count
                    WHERE chunk_count >= $min_size
                    RETURN 
                        cl.cluster_id as cluster_id,
                        cl.name as name,
                        cl.summary as summary,
                        chunk_count as size
                    ORDER BY chunk_count DESC
                    LIMIT $limit
                """, limit=limit, min_size=min_size)
            
            clusters = []
            for record in result:
                cluster_data = {
                    "cluster_id": record["cluster_id"],
                    "name": record["name"],
                    "summary": record["summary"],
                    "size": record["size"]
                }
                
                if include_positioning and record["x"] is not None:
                    cluster_data.update({
                        "x": record["x"],
                        "y": record["y"]
                    })
                
                clusters.append(cluster_data)
            
            return ApiResponse(
                data=clusters,
                message=f"Found {len(clusters)} clusters"
            )
            
    except Exception as e:
        logger.error(f"Discover clusters error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{chat_id}/context", response_model=ApiResponse)
async def get_conversation_context(chat_id: str):
    """Get conversation context and related content"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Get chat info and related content
            result = session.run("""
                MATCH (c:Chat {chat_id: $chat_id})
                OPTIONAL MATCH (c)-[:HAS_MESSAGE]->(m:Message)
                OPTIONAL MATCH (m)-[:HAS_TAG]->(t:Tag)
                WITH c, collect(DISTINCT t.name) as tags
                OPTIONAL MATCH (c)-[:SIMILAR_TO]->(related:Chat)
                RETURN 
                    c.title as title,
                    c.timestamp as timestamp,
                    tags,
                    collect(DISTINCT related.chat_id) as related_chats
            """, chat_id=chat_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Chat not found")
            
            return ApiResponse(
                data={
                    "title": record["title"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None,
                    "tags": record["tags"],
                    "related_chats": record["related_chats"]
                },
                message="Conversation context retrieved successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/similar/{chunk_id}", response_model=ApiResponse)
async def search_similar_content(
    chunk_id: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """Find similar content for a chunk"""
    try:
        if not qdrant_client:
            raise HTTPException(status_code=503, detail="Qdrant not connected")
        
        # Get the chunk's embedding from Qdrant
        try:
            chunk_point = qdrant_client.retrieve(
                collection_name="chatmind_embeddings",
                ids=[chunk_id]
            )
            
            if not chunk_point:
                raise HTTPException(status_code=404, detail="Chunk not found")
            
            # Search for similar content
            search_results = qdrant_client.search(
                collection_name="chatmind_embeddings",
                query_vector=chunk_point[0].vector,
                limit=limit + 1,  # +1 to exclude the original
                with_payload=True,
                with_vectors=False
            )
            
            similar_chunks = []
            for result in search_results:
                if result.id != chunk_id:  # Exclude the original chunk
                    similar_chunks.append({
                        "chunk_id": result.id,
                        "content": result.payload.get("content", ""),
                        "similarity_score": result.score
                    })
            
            return ApiResponse(
                data=similar_chunks,
                message=f"Found {len(similar_chunks)} similar chunks"
            )
            
        except Exception as e:
            logger.error(f"Similar content search error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar content search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 