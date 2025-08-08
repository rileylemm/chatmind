"""
Search-related endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException, Query
from models import ApiResponse
from utils import convert_neo4j_to_json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])

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


@router.get("", response_model=ApiResponse)
async def simple_search(
    q: str = Query(..., description="Search query", alias="query"),
    limit: int = Query(default=10, ge=1, le=100)
):
    """Simple search endpoint (Neo4j only)"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Simple text search in messages with enrichment
            result = session.run("""
                MATCH (m:Message)
                WHERE m.content CONTAINS $search_term
                MATCH (c:Chat {chat_id: m.chat_id})
                RETURN 
                    m.content as content, 
                    m.message_id as message_id,
                    m.role as role,
                    m.timestamp as timestamp,
                    c.title as conversation_title
                LIMIT $limit
            """, search_term=q, limit=limit)
            
            results = []
            for record in result:
                results.append({
                    "content": record["content"],
                    "message_id": record["message_id"],
                    "role": record["role"] or "unknown",
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None,
                    "conversation_title": record["conversation_title"] or "Untitled Conversation"
                })
            
            return ApiResponse(
                data=results,
                message=f"Found {len(results)} results for '{q}'"
            )
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic", response_model=ApiResponse)
async def semantic_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=100)
):
    """Semantic search endpoint (Qdrant only)"""
    try:
        if not qdrant_client or not embedding_model:
            raise HTTPException(status_code=503, detail="Qdrant or embedding model not connected")
        
        # Generate embedding for query
        query_vector = embedding_model.encode(query).tolist()
        
        # Search in Qdrant
        search_result = qdrant_client.search(
            collection_name="chatmind_embeddings",
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        results = []
        for result in search_result:
            content = result.payload.get("content", "")
            
            # Calculate keyword boost
            query_lower = query.lower()
            content_lower = content.lower()
            
            # Boost score if query terms are present
            keyword_boost = 0.0
            if query_lower in content_lower:
                keyword_boost = 0.3  # Significant boost for exact keyword match
            elif any(word in content_lower for word in query_lower.split()):
                keyword_boost = 0.1  # Small boost for partial matches
            
            # Apply boost to similarity score (capped at 1.0)
            boosted_score = min(1.0, result.score + keyword_boost)
            
            # Get basic chunk info
            chunk_data = {
                "chunk_id": result.payload.get("chunk_id"),
                "content": content,
                "message_id": result.payload.get("message_id"),
                "chat_id": result.payload.get("chat_id"),
                "similarity_score": boosted_score,
                "conversation_title": "Unknown",
                "timestamp": None,
                "role": "unknown"
            }
            
            # Enrich with Neo4j data if available
            if neo4j_driver and chunk_data["message_id"]:
                try:
                    with neo4j_driver.session() as session:
                        # Get message and chat details
                        cypher_result = session.run("""
                            MATCH (m:Message {message_id: $message_id})
                            MATCH (c:Chat {chat_id: m.chat_id})
                            RETURN 
                                m.role as role,
                                m.timestamp as timestamp,
                                c.title as conversation_title
                        """, message_id=chunk_data["message_id"])
                        
                        record = cypher_result.single()
                        if record:
                            chunk_data["role"] = record["role"] or "unknown"
                            chunk_data["timestamp"] = convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None
                            chunk_data["conversation_title"] = record["conversation_title"] or "Untitled Conversation"
                except Exception as e:
                    logger.warning(f"Neo4j enrichment failed for message {chunk_data['message_id']}: {e}")
            
            results.append(chunk_data)
        
        return ApiResponse(
            data=results,
            message=f"Found {len(results)} semantic results for '{query}'"
        )
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hybrid", response_model=ApiResponse)
async def hybrid_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=100)
):
    """Hybrid search endpoint (Neo4j + Qdrant)"""
    try:
        results = []
        
        # 1. Get semantic results from Qdrant
        if qdrant_client and embedding_model:
            try:
                query_vector = embedding_model.encode(query).tolist()
                search_result = qdrant_client.search(
                    collection_name="chatmind_embeddings",
                    query_vector=query_vector,
                    limit=limit,
                    with_payload=True,
                    with_vectors=False
                )
                
                for result in search_result:
                    # Get basic chunk info
                    chunk_data = {
                        "type": "semantic",
                        "chunk_id": result.payload.get("chunk_id"),
                        "content": result.payload.get("content", ""),
                        "message_id": result.payload.get("message_id"),
                        "chat_id": result.payload.get("chat_id"),
                        "similarity_score": result.score,
                        "conversation_title": "Unknown",
                        "timestamp": None,
                        "role": "unknown"
                    }
                    
                    # Enrich with Neo4j data if available
                    if neo4j_driver and chunk_data["message_id"]:
                        try:
                            with neo4j_driver.session() as session:
                                # Get message and chat details
                                cypher_result = session.run("""
                                    MATCH (m:Message {message_id: $message_id})
                                    MATCH (c:Chat {chat_id: m.chat_id})
                                    RETURN 
                                        m.role as role,
                                        m.timestamp as timestamp,
                                        c.title as conversation_title
                                """, message_id=chunk_data["message_id"])
                                
                                record = cypher_result.single()
                                if record:
                                    chunk_data["role"] = record["role"] or "unknown"
                                    chunk_data["timestamp"] = convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None
                                    chunk_data["conversation_title"] = record["conversation_title"] or "Untitled Conversation"
                        except Exception as e:
                            logger.warning(f"Neo4j enrichment failed for message {chunk_data['message_id']}: {e}")
                    
                    results.append(chunk_data)
            except Exception as e:
                logger.warning(f"Qdrant search failed: {e}")
        
        # 2. Get text search results from Neo4j
        if neo4j_driver:
            try:
                with neo4j_driver.session() as session:
                    result = session.run("""
                        MATCH (m:Message)
                        WHERE m.content CONTAINS $search_term
                        RETURN m.content as content, m.message_id as message_id
                        LIMIT $limit
                    """, search_term=query, limit=limit)
                    
                    for record in result:
                        results.append({
                            "type": "text",
                            "content": record["content"],
                            "message_id": record["message_id"],
                            "similarity_score": 1.0  # Text match
                        })
            except Exception as e:
                logger.warning(f"Neo4j search failed: {e}")
        
        return ApiResponse(
            data=results,
            message=f"Found {len(results)} hybrid results for '{query}'"
        )
        
    except Exception as e:
        logger.error(f"Hybrid search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ApiResponse)
async def search_stats():
    """Get search statistics"""
    try:
        stats = {
            "neo4j_connected": neo4j_driver is not None,
            "qdrant_connected": qdrant_client is not None,
            "embedding_model_loaded": embedding_model is not None,
            "total_conversations": 0,
            "total_messages": 0,
            "total_chunks": 0
        }
        
        # Get Neo4j stats
        if neo4j_driver:
            try:
                with neo4j_driver.session() as session:
                    # Count conversations
                    chat_result = session.run("MATCH (c:Chat) RETURN count(c) as conversations")
                    chat_record = chat_result.single()
                    
                    # Count messages
                    message_result = session.run("MATCH (m:Message) RETURN count(m) as messages")
                    message_record = message_result.single()
                    
                    if chat_record and message_record:
                        stats["total_conversations"] = chat_record["conversations"]
                        stats["total_messages"] = message_record["messages"]
            except Exception as e:
                logger.warning(f"Neo4j stats error: {e}")
        
        # Get Qdrant stats
        if qdrant_client:
            try:
                collection_info = qdrant_client.get_collection("chatmind_embeddings")
                stats["total_chunks"] = collection_info.points_count
            except Exception as e:
                logger.warning(f"Qdrant stats error: {e}")
        
        return ApiResponse(
            data=stats,
            message="Search statistics retrieved"
        )
        
    except Exception as e:
        logger.error(f"Search stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags", response_model=ApiResponse)
async def search_by_tags(
    tags: str = Query(..., description="Comma-separated list of tags"),
    limit: int = Query(default=10, ge=1, le=100)
):
    """Search by tags endpoint - Neo4j only"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        results = []
        tag_list = [tag.strip() for tag in tags.split(",")]
        
        with neo4j_driver.session() as session:
            # Search for messages that have ALL of the specified tags (AND logic)
            cypher_result = session.run("""
                MATCH (m:Message)<-[:TAGS]-(t:Tag)
                WHERE ALL(tag IN $tag_list WHERE tag IN t.tags)
                RETURN DISTINCT 
                    m.content as content,
                    m.message_id as message_id,
                    m.chat_id as chat_id,
                    m.role as role,
                    m.timestamp as timestamp,
                    t.tags as tags
                LIMIT $limit
            """, tag_list=tag_list, limit=limit)
            
            for record in cypher_result:
                results.append({
                    "content": record["content"],
                    "message_id": record["message_id"],
                    "chat_id": record["chat_id"],
                    "role": record["role"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None,
                    "tags": record["tags"],
                    "similarity_score": 1.0  # Direct tag match
                })
        
        return ApiResponse(
            data=results,
            message=f"Found {len(results)} results for tags: {tags}"
        )
        
    except Exception as e:
        logger.error(f"Search by tags error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domain/{domain}", response_model=ApiResponse)
async def search_by_domain(
    domain: str,
    limit: int = Query(default=10, ge=1, le=100)
):
    """Search by domain endpoint - Hybrid approach"""
    try:
        results = []
        
        # Get chunks from Qdrant
        if qdrant_client:
            try:
                search_result = qdrant_client.search(
                    collection_name="chatmind_embeddings",
                    query_vector=[0.0] * 384,  # Dummy vector
                    limit=limit * 3,  # Get more to filter
                    with_payload=True,
                    with_vectors=False
                )
                
                # Enrich with Neo4j domain data
                if neo4j_driver:
                    for result in search_result:
                        message_id = result.payload.get("message_id")
                        if message_id:
                            try:
                                with neo4j_driver.session() as session:
                                    # Get message and its domain from Neo4j
                                    cypher_result = session.run("""
                                        MATCH (m:Message {message_id: $message_id})<-[:TAGS]-(t:Tag)
                                        RETURN t.domain as domain_name
                                        LIMIT 1
                                    """, message_id=message_id)
                                    
                                    record = cypher_result.single()
                                    message_domain = record["domain_name"] if record and record["domain_name"] else ""
                                    
                                    # Check if domain matches
                                    if domain.lower() in message_domain.lower():
                                        results.append({
                                            "chunk_id": result.payload.get("chunk_id"),
                                            "content": result.payload.get("content", ""),
                                            "message_id": message_id,
                                            "chat_id": result.payload.get("chat_id"),
                                            "domain": message_domain,
                                            "similarity_score": result.score
                                        })
                                        
                                        if len(results) >= limit:
                                            break
                            except Exception as e:
                                logger.warning(f"Neo4j domain lookup failed for message {message_id}: {e}")
                                continue
                                
            except Exception as e:
                logger.warning(f"Qdrant domain search failed: {e}")
        
        return ApiResponse(
            data=results,
            message=f"Found {len(results)} results for domain: {domain}"
        )
        
    except Exception as e:
        logger.error(f"Search by domain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{chunk_id}", response_model=ApiResponse)
async def search_similar_content(
    chunk_id: str,
    limit: int = Query(default=10, ge=1, le=100)
):
    """Search for similar content based on a chunk"""
    try:
        results = []
        
        # First, get the embedding for the target chunk
        if qdrant_client:
            try:
                # Search for the target chunk to get its embedding
                target_search = qdrant_client.search(
                    collection_name="chatmind_embeddings",
                    query_vector=[0.0] * 384,  # Dummy vector
                    limit=100,
                    with_payload=True,
                    with_vectors=True
                )
                
                target_embedding = None
                for result in target_search:
                    if result.payload.get("chunk_id") == chunk_id:
                        target_embedding = result.vector
                        break
                
                if target_embedding:
                    # Search for similar chunks using the target embedding
                    similar_results = qdrant_client.search(
                        collection_name="chatmind_embeddings",
                        query_vector=target_embedding,
                        limit=limit + 1,  # +1 to exclude the target itself
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    for result in similar_results:
                        if result.payload.get("chunk_id") != chunk_id:  # Exclude the target
                            results.append({
                                "chunk_id": result.payload.get("chunk_id"),
                                "content": result.payload.get("content", ""),
                                "message_id": result.payload.get("message_id"),
                                "chat_id": result.payload.get("chat_id"),
                                "similarity_score": result.score
                            })
                            
                            if len(results) >= limit:
                                break
                else:
                    logger.warning(f"Target chunk {chunk_id} not found")
                    
            except Exception as e:
                logger.warning(f"Qdrant similar search failed: {e}")
        
        return ApiResponse(
            data=results,
            message=f"Found {len(results)} similar results for chunk {chunk_id}"
        )
        
    except Exception as e:
        logger.error(f"Similar content search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags/available", response_model=ApiResponse)
async def get_available_tags():
    """Get list of available tags from Neo4j with counts"""
    try:
        tag_counts = {}
        
        # Get tags with counts from Neo4j
        if neo4j_driver:
            try:
                with neo4j_driver.session() as session:
                    result = session.run("""
                        MATCH (t:Tag)
                        UNWIND t.tags as tag
                        RETURN tag as tag_name, count(*) as tag_count
                        ORDER BY tag_count DESC, tag_name
                    """)
                    
                    for record in result:
                        tag_name = record["tag_name"]
                        tag_count = record["tag_count"]
                        if tag_name and tag_name.strip():
                            tag_counts[tag_name.strip()] = tag_count
                            
            except Exception as e:
                logger.warning(f"Neo4j tag collection failed: {e}")
        
        # Convert to list of objects
        tags = [{"name": tag, "count": count} for tag, count in tag_counts.items()]
        
        return ApiResponse(
            data=tags,
            message=f"Found {len(tags)} available tags"
        )
        
    except Exception as e:
        logger.error(f"Available tags error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 