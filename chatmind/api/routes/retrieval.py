from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

from ..services import retrieval as rsvc

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

        # Ensure BM25 index ready
        rsvc.ensure_bm25_index()

        # 1) Lexical
        cand_ids_lex = rsvc.bm25_search(req.query, topn=400)
        # 2) Vector
        cand_ids_vec = rsvc.qdrant_search_turns(qdrant_client, embedding_model, req.query, topn=200)
        # 3) Union
        ids = rsvc.union_topn(cand_ids_lex, cand_ids_vec, n=300)
        # 4) Expand NEXT +/- 1
        expanded_ids = rsvc.expand_neighbors(neo4j_driver, ids, hop=1)
        # 5) Fetch turn records (no rerank yet)
        turns = rsvc.fetch_turns(neo4j_driver, expanded_ids[: max(req.topn * 5, 50)])

        # Simple pack by chat_id preserving order
        packs: Dict[str, List[Dict[str, Any]]] = {}
        for t in turns:
            packs.setdefault(t["chat_id"], []).append(t)
        # Take top N chats by count
        sorted_chats = sorted(packs.items(), key=lambda kv: -len(kv[1]))[: req.topn]
        results = [
            {
                "chat_id": chat_id,
                "turns": chat_turns[:50],  # cap per-chat
                "score": len(chat_turns),
            }
            for chat_id, chat_turns in sorted_chats
        ]

        return {"query": req.query, "packs": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 