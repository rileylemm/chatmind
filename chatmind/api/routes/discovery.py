"""
Discovery endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException, Query
from models import ApiResponse
from utils import convert_neo4j_to_json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["discovery"])

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


@router.get("/connections/explain", response_model=ApiResponse)
async def explain_connection(
    source_id: str = Query(..., description="Source chat ID"),
    target_id: str = Query(..., description="Target chat ID")
):
    """Explain why two conversations are connected"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Get both chats and their tags
            result = session.run("""
                MATCH (source:Chat {chat_id: $source_id})
                MATCH (target:Chat {chat_id: $target_id})
                OPTIONAL MATCH (source)-[:CONTAINS]->(sm:Message)-[:HAS_TAG]->(st:Tag)
                OPTIONAL MATCH (target)-[:CONTAINS]->(tm:Message)-[:HAS_TAG]->(tt:Tag)
                WITH source, target, 
                     collect(DISTINCT st.name) as source_tags,
                     collect(DISTINCT tt.name) as target_tags
                RETURN 
                    source.title as source_title,
                    target.title as target_title,
                    source_tags,
                    target_tags
            """, source_id=source_id, target_id=target_id)
            
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="One or both chats not found")
            
            # Find shared tags
            source_tags = set(record["source_tags"] or [])
            target_tags = set(record["target_tags"] or [])
            shared_tags = list(source_tags.intersection(target_tags))
            
            # Calculate connection strength based on shared tags
            total_unique_tags = len(source_tags.union(target_tags))
            connection_strength = len(shared_tags) / total_unique_tags if total_unique_tags > 0 else 0
            
            # Determine strength category
            if connection_strength >= 0.5:
                strength_category = "strong"
            elif connection_strength >= 0.2:
                strength_category = "moderate"
            else:
                strength_category = "weak"
            
            # Generate explanation
            if shared_tags:
                explanation = f"Both conversations share themes: {', '.join(shared_tags[:3])}"
            else:
                explanation = "Conversations may be connected through semantic similarity rather than explicit tags"
            
            return ApiResponse(
                data={
                    "source_chat": {
                        "id": source_id,
                        "title": record["source_title"]
                    },
                    "target_chat": {
                        "id": target_id,
                        "title": record["target_title"]
                    },
                    "shared_tags": shared_tags,
                    "shared_themes": shared_tags,  # For now, use tags as themes
                    "connection_strength": connection_strength,
                    "strength_category": strength_category,
                    "explanation": explanation
                },
                message="Connection explanation generated successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Connection explanation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/cross-domain", response_model=ApiResponse)
async def cross_domain_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=5, ge=1, le=20, description="Maximum results per domain")
):
    """Find how a topic appears across different domains"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Get available domains
            domains_result = session.run("""
                MATCH (c:Chat)
                WHERE c.domain IS NOT NULL
                RETURN DISTINCT c.domain as domain
                ORDER BY domain
            """)
            
            domains = [record["domain"] for record in domains_result]
            
            cross_domain_results = {}
            
            # Search in each domain
            for domain in domains:
                result = session.run("""
                    MATCH (c:Chat {domain: $domain})-[:CONTAINS]->(m:Message)
                    WHERE m.content CONTAINS $query
                    RETURN 
                        c.chat_id as chat_id,
                        c.title as chat_title,
                        m.content as content,
                        m.message_id as message_id,
                        m.role as role
                    ORDER BY m.timestamp DESC
                    LIMIT $limit
                """, domain=domain, query=query, limit=limit)
                
                domain_results = []
                for record in result:
                    domain_results.append({
                        "chat_id": record["chat_id"],
                        "chat_title": record["chat_title"],
                        "content": record["content"],
                        "message_id": record["message_id"],
                        "role": record["role"],
                        "similarity": 0.8  # Placeholder similarity score
                    })
                
                if domain_results:
                    cross_domain_results[domain] = domain_results
            
            return ApiResponse(
                data={
                    "query": query,
                    "cross_domain_results": cross_domain_results,
                    "domains_searched": domains,
                    "total_results": sum(len(results) for results in cross_domain_results.values())
                },
                message=f"Found cross-domain results for '{query}'"
            )
            
    except Exception as e:
        logger.error(f"Cross-domain search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/discover/suggestions", response_model=ApiResponse)
async def get_discovery_suggestions(
    limit: int = Query(default=5, ge=1, le=20, description="Maximum suggestions")
):
    """Suggest interesting connections to explore"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Find chats with similar tags across different domains
            result = session.run("""
                MATCH (c1:Chat)-[:CONTAINS]->(m1:Message)-[:HAS_TAG]->(t:Tag)
                MATCH (c2:Chat)-[:CONTAINS]->(m2:Message)-[:HAS_TAG]->(t)
                WHERE c1.domain <> c2.domain AND c1.chat_id < c2.chat_id
                WITH c1, c2, t, count(t) as shared_tag_count
                WHERE shared_tag_count >= 1
                RETURN 
                    c1.chat_id as chat1_id,
                    c1.title as chat1_title,
                    c1.domain as domain1,
                    c2.chat_id as chat2_id,
                    c2.title as chat2_title,
                    c2.domain as domain2,
                    collect(DISTINCT t.name) as shared_tags,
                    shared_tag_count
                ORDER BY shared_tag_count DESC
                LIMIT $limit
            """, limit=limit)
            
            suggestions = []
            for record in result:
                suggestions.append({
                    "suggestion": f"You discussed '{', '.join(record['shared_tags'][:3])}' in {record['domain1']} and {record['domain2']} contexts",
                    "source_domain": record["domain1"],
                    "target_domain": record["domain2"],
                    "connection_strength": min(record["shared_tag_count"] / 5.0, 1.0),  # Normalize to 0-1
                    "exploration_path": [record["domain1"], ", ".join(record["shared_tags"][:2]), record["domain2"]],
                    "chat1": {
                        "id": record["chat1_id"],
                        "title": record["chat1_title"]
                    },
                    "chat2": {
                        "id": record["chat2_id"],
                        "title": record["chat2_title"]
                    }
                })
            
            return ApiResponse(
                data=suggestions,
                message=f"Found {len(suggestions)} discovery suggestions"
            )
            
    except Exception as e:
        logger.error(f"Discovery suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline/semantic", response_model=ApiResponse)
async def get_timeline_semantic(
    start_date: Optional[str] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(default=None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum conversations per day")
):
    """Get chronological data with semantic connections"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        with neo4j_driver.session() as session:
            # Build date filter
            date_filter = ""
            params = {"limit": limit}
            
            if start_date:
                date_filter += " AND c.timestamp >= $start_date"
                params["start_date"] = start_date
            
            if end_date:
                date_filter += " AND c.timestamp <= $end_date"
                params["end_date"] = end_date
            
            # Get conversations with semantic connections
            result = session.run(f"""
                MATCH (c:Chat)
                WHERE c.timestamp IS NOT NULL {date_filter}
                OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)-[:HAS_TAG]->(t:Tag)
                WITH c, collect(DISTINCT t.name) as tags
                OPTIONAL MATCH (c)-[:SIMILAR_TO]->(related:Chat)
                WITH c, tags, collect(DISTINCT related.chat_id) as related_chats
                RETURN 
                    c.chat_id as chat_id,
                    c.title as title,
                    c.timestamp as timestamp,
                    c.domain as domain,
                    tags,
                    related_chats
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """, **params)
            
            # Group by date
            timeline_data = {}
            for record in result:
                timestamp = record["timestamp"]
                if timestamp:
                    date_str = timestamp.strftime("%Y-%m-%d") if hasattr(timestamp, 'strftime') else str(timestamp)[:10]
                else:
                    date_str = "unknown"
                
                if date_str not in timeline_data:
                    timeline_data[date_str] = []
                
                timeline_data[date_str].append({
                    "chat_id": record["chat_id"],
                    "title": record["title"],
                    "timestamp": convert_neo4j_to_json(record["timestamp"]) if record["timestamp"] else None,
                    "domain": record["domain"],
                    "tags": record["tags"] or [],
                    "semantic_connections": [
                        {
                            "related_chat": chat_id,
                            "connection": "similar content",
                            "similarity": 0.8  # Placeholder similarity
                        }
                        for chat_id in record["related_chats"]
                    ]
                })
            
            # Convert to sorted list
            timeline_list = [
                {
                    "date": date,
                    "conversations": conversations
                }
                for date, conversations in sorted(timeline_data.items(), reverse=True)
            ]
            
            return ApiResponse(
                data=timeline_list,
                message=f"Found timeline data for {len(timeline_list)} days"
            )
            
    except Exception as e:
        logger.error(f"Timeline semantic error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 