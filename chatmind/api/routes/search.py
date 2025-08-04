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
            # Simple text search in messages
            result = session.run("""
                MATCH (m:Message)
                WHERE m.content CONTAINS $search_term
                RETURN m.content as content, m.message_id as message_id
                LIMIT $limit
            """, search_term=q, limit=limit)
            
            results = []
            for record in result:
                results.append({
                    "content": record["content"],
                    "message_id": record["message_id"]
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
            results.append({
                "chunk_id": result.payload.get("chunk_id"),
                "content": result.payload.get("content", ""),
                "message_id": result.payload.get("message_id"),
                "chat_id": result.payload.get("chat_id"),
                "similarity_score": result.score
            })
        
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
                    results.append({
                        "type": "semantic",
                        "chunk_id": result.payload.get("chunk_id"),
                        "content": result.payload.get("content", ""),
                        "message_id": result.payload.get("message_id"),
                        "chat_id": result.payload.get("chat_id"),
                        "similarity_score": result.score
                    })
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
                    result = session.run("""
                        MATCH (n)
                        RETURN 
                            count(DISTINCT n:Chat) as conversations,
                            count(DISTINCT n:Message) as messages
                    """)
                    record = result.single()
                    if record:
                        stats["total_conversations"] = record["conversations"]
                        stats["total_messages"] = record["messages"]
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
    """Search by tags endpoint - Hybrid approach"""
    try:
        results = []
        tag_list = [tag.strip() for tag in tags.split(",")]
        
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
                
                # Enrich with Neo4j tag data
                if neo4j_driver:
                    for result in search_result:
                        message_id = result.payload.get("message_id")
                        if message_id:
                            try:
                                with neo4j_driver.session() as session:
                                    # Get message and its tags from Neo4j
                                    cypher_result = session.run("""
                                        MATCH (m:Message {message_id: $message_id})<-[:TAGS]-(t:Tag)
                                        UNWIND t.tags as tag
                                        RETURN DISTINCT tag as tag_name
                                    """, message_id=message_id)
                                    
                                    message_tags = [record["tag_name"] for record in cypher_result]
                                    
                                    # Check if any search tags match message tags
                                    if any(tag.lower() in [mt.lower() for mt in message_tags] for tag in tag_list):
                                        results.append({
                                            "chunk_id": result.payload.get("chunk_id"),
                                            "content": result.payload.get("content", ""),
                                            "message_id": message_id,
                                            "chat_id": result.payload.get("chat_id"),
                                            "tags": message_tags,
                                            "similarity_score": result.score
                                        })
                                        
                                        if len(results) >= limit:
                                            break
                            except Exception as e:
                                logger.warning(f"Neo4j tag lookup failed for message {message_id}: {e}")
                                continue
                                
            except Exception as e:
                logger.warning(f"Qdrant tag search failed: {e}")
        
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
    """Get list of available tags from Neo4j"""
    try:
        tags = set()
        
        # Get tags from Neo4j
        if neo4j_driver:
            try:
                with neo4j_driver.session() as session:
                    result = session.run("""
                        MATCH (t:Tag)
                        UNWIND t.tags as tag
                        RETURN DISTINCT tag as tag_name
                        ORDER BY tag
                    """)
                    
                    for record in result:
                        tag_name = record["tag_name"]
                        if tag_name and tag_name.strip():
                            tags.add(tag_name.strip())
                            
            except Exception as e:
                logger.warning(f"Neo4j tag collection failed: {e}")
        
        return ApiResponse(
            data=list(tags),
            message=f"Found {len(tags)} available tags"
        )
        
    except Exception as e:
        logger.error(f"Available tags error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 