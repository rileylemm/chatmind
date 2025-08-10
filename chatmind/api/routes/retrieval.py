from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

try:
    from ..services import retrieval as rsvc
except ImportError:
    from services import retrieval as rsvc

router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])
logger = logging.getLogger(__name__)

neo4j_driver = None
qdrant_client = None
embedding_model = None
cross_encoder_model = None


def set_global_connections(neo4j, qdrant, embedding):
    global neo4j_driver, qdrant_client, embedding_model
    neo4j_driver = neo4j
    qdrant_client = qdrant
    embedding_model = embedding


class RetrieveRequest(BaseModel):
    query: str
    topn: int = 10
    window_tokens: int = 5000


def _get_cross_encoder():
    global cross_encoder_model
    if cross_encoder_model is None:
        try:
            from sentence_transformers import CrossEncoder
            # Lightweight cross-encoder for rerank; can upgrade to large later
            cross_encoder_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("✅ Cross-encoder loaded for reranking")
        except Exception as e:
            logger.warning(f"Cross-encoder unavailable: {e}")
            cross_encoder_model = None
    return cross_encoder_model


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
        # 5) Fetch turn records
        turns = rsvc.fetch_turns(neo4j_driver, expanded_ids[: max(req.topn * 5, 100)])
        # 6) Rerank with cross-encoder
        ce = _get_cross_encoder()
        reranked = rsvc.cross_encode_rerank(ce, req.query, turns, batch_size=64, topk=req.topn * 5)

        # Pack by chat_id preserving rerank order
        packs: Dict[str, List[Dict[str, Any]]] = {}
        for t in reranked:
            packs.setdefault(t["chat_id"], []).append(t)
        sorted_chats = sorted(packs.items(), key=lambda kv: -sum(x.get("rerank_score", 0.0) for x in kv[1]))[: req.topn]
        results = [
            {
                "chat_id": chat_id,
                "turns": chat_turns[:50],
                "score": sum(x.get("rerank_score", 0.0) for x in chat_turns),
            }
            for chat_id, chat_turns in sorted_chats
        ]

        return {"query": req.query, "packs": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 