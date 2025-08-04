"""
Debug-related endpoints for ChatMind API
"""

from fastapi import APIRouter, HTTPException
from models import ApiResponse
from utils import convert_neo4j_to_json
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/debug", tags=["debug"])

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


@router.get("/schema", response_model=ApiResponse)
async def debug_schema():
    """Debug endpoint to see Neo4j schema"""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        
        schema_info = {}
        
        with neo4j_driver.session() as session:
            # Get all node labels
            result = session.run("""
                CALL db.labels() YIELD label
                RETURN collect(label) as labels
            """)
            record = result.single()
            schema_info["node_labels"] = record["labels"] if record else []
            
            # Get all relationship types
            result = session.run("""
                CALL db.relationshipTypes() YIELD relationshipType
                RETURN collect(relationshipType) as types
            """)
            record = result.single()
            schema_info["relationship_types"] = record["types"] if record else []
            
            # Count nodes by label
            node_counts = {}
            for label in schema_info["node_labels"]:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                record = result.single()
                node_counts[label] = record["count"] if record else 0
            schema_info["node_counts"] = node_counts
            
            # Get sample nodes for each label
            sample_nodes = {}
            for label in schema_info["node_labels"]:
                result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 3")
                samples = []
                for record in result:
                    node = record["n"]
                    samples.append({
                        "id": str(node.id),
                        "properties": convert_neo4j_to_json(dict(node))
                    })
                sample_nodes[label] = samples
            schema_info["sample_nodes"] = sample_nodes
        
        return ApiResponse(
            data=schema_info,
            message="Neo4j schema information"
        )
        
    except Exception as e:
        logger.error(f"Schema debug error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 