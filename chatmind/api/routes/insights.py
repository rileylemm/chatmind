"""
Insights endpoints for advanced discovery and explainability (TDD stubs)
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any
import logging
from models import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["insights"])

# Global connections
neo4j_driver = None
qdrant_client = None
embedding_model = None


def set_global_connections(neo4j, qdrant, embedding):
    global neo4j_driver, qdrant_client, embedding_model
    neo4j_driver = neo4j
    qdrant_client = qdrant
    embedding_model = embedding


@router.get("/discover/bridges", response_model=ApiResponse)
async def discover_bridges(
    domain_a: Optional[str] = Query(default=None),
    domain_b: Optional[str] = Query(default=None),
    limit: int = Query(default=5, ge=1, le=50),
):
    """Return bridge nodes that likely connect distant areas (stub)."""
    try:
        data = {
            "filters": {"domain_a": domain_a, "domain_b": domain_b},
            "items": [],
            "count": 0,
            "limit": limit,
        }
        return ApiResponse(data=data, message="Bridges (stub)")
    except Exception as e:
        logger.error(f"discover_bridges error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain/path", response_model=ApiResponse)
async def explain_path(
    source_id: str = Query(..., description="Source chat ID"),
    target_id: str = Query(..., description="Target chat ID"),
    max_hops: int = Query(default=2, ge=1, le=4),
):
    """Explain connection between two nodes with a path and evidence (stub)."""
    try:
        data = {
            "source_id": source_id,
            "target_id": target_id,
            "max_hops": max_hops,
            "path": [],
            "evidence": [],
        }
        return ApiResponse(data=data, message="Explain path (stub)")
    except Exception as e:
        logger.error(f"explain_path error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution/cluster/{cluster_id}", response_model=ApiResponse)
async def evolution_cluster(
    cluster_id: str,
    granularity: str = Query(default="week", regex="^(day|week|month)$"),
    start_time: Optional[float] = Query(default=None),
    end_time: Optional[float] = Query(default=None),
):
    """Return time-bucketed evolution metrics for a cluster (stub)."""
    try:
        data = {
            "cluster_id": cluster_id,
            "granularity": granularity,
            "start_time": start_time,
            "end_time": end_time,
            "points": [],
        }
        return ApiResponse(data=data, message="Cluster evolution (stub)")
    except Exception as e:
        logger.error(f"evolution_cluster error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/serendipity", response_model=ApiResponse)
async def serendipity(
    seed_id: str = Query(..., description="Seed chat or chunk id"),
    type: str = Query(default="chat", regex="^(chat|chunk)$"),
    novelty: float = Query(default=0.7, ge=0, le=1),
    limit: int = Query(default=5, ge=1, le=50),
):
    """Return novel-but-relevant recommendations (stub)."""
    try:
        data = {
            "seed_id": seed_id,
            "type": type,
            "novelty": novelty,
            "items": [],
            "count": 0,
            "limit": limit,
        }
        return ApiResponse(data=data, message="Serendipity (stub)")
    except Exception as e:
        logger.error(f"serendipity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=ApiResponse)
async def compare(
    payload: Dict[str, Any] = Body(..., example={"type": "chat", "ids": ["a", "b"]}),
):
    """Compare entities side-by-side (stub)."""
    try:
        compare_type = payload.get("type", "chat")
        ids = payload.get("ids", [])
        data = {
            "type": compare_type,
            "ids": ids,
            "summary": {
                "overlap_score": 0.0,
                "shared_tags": [],
                "divergent_tags": [],
            },
        }
        return ApiResponse(data=data, message="Compare (stub)")
    except Exception as e:
        logger.error(f"compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 