from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])
logger = logging.getLogger(__name__)

neo4j_driver = None
qdrant_client = None
embedding_model = None


def set_global_connections(neo4j, qdrant, embedding):
    global neo4j_driver, qdrant_client, embedding_model
    neo4j_driver = neo4j
    qdrant_client = qdrant
    embedding_model = embedding


class RetrieveRequest(BaseModel):
    query: str
    topn: int = 10
    window_tokens: int = 5000


@router.post("/retrieve")
async def retrieve(req: RetrieveRequest) -> Dict[str, Any]:
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        if not qdrant_client or not embedding_model:
            raise HTTPException(status_code=503, detail="Qdrant or embedding model not connected")

        # Placeholder minimal retrieval: vector search over turn summaries
        query_vec = embedding_model.encode(req.query).tolist()
        res = qdrant_client.search(
            collection_name="chatmind_turns",
            query_vector=query_vec,
            limit=req.topn,
            with_payload=True,
            with_vectors=False
        )
        hits = []
        for r in res:
            p = r.payload or {}
            hits.append({
                "turn_uid": p.get("turn_uid"),
                "chat_id": p.get("chat_id"),
                "turn_id": p.get("turn_id"),
                "summary": p.get("summary"),
                "score": r.score
            })
        return {"query": req.query, "results": hits}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 