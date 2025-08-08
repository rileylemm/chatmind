"""
Insights endpoints for advanced discovery and explainability
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any, Tuple, Set
import logging
import math
import os
from models import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["insights"])

# Global connections
neo4j_driver = None
qdrant_client = None
embedding_model = None

QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "chatmind_embeddings")


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
    """Return chats that structurally bridge multiple clusters (proxy for serendipity).

    Heuristic: count distinct clusters connected via (Chat)-[:CONTAINS]->(Message)-[:HAS_CHUNK]->(Chunk)
    and (Cluster)-[:HAS_CHUNK]->(Chunk). Higher distinct cluster count → stronger bridge.
    Optionally filter by Tag.domain pairs.
    """
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")

        with neo4j_driver.session() as session:
            domain_filter = ""
            params: Dict[str, Any] = {"limit": limit}
            if domain_a or domain_b:
                # Restrict chats that have messages tagged with requested domains
                domains = [d for d in [domain_a, domain_b] if d]
                domain_filter = """
                OPTIONAL MATCH (c)-[:CONTAINS]->(m2:Message)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m2)
                WITH c, clusters, cluster_count, collect(DISTINCT t.domain) as domains
                WHERE ANY(d IN $domains WHERE d IN domains)
                """
                params["domains"] = domains
            else:
                domain_filter = "WITH c, clusters, cluster_count"

            result = session.run(
                f"""
                MATCH (c:Chat)-[:CONTAINS]->(:Message)-[:HAS_CHUNK]->(:Chunk)<-[:HAS_CHUNK]-(cl:Cluster)
                WITH c, collect(DISTINCT cl.cluster_id) as clusters, size(collect(DISTINCT cl.cluster_id)) as cluster_count
                {domain_filter}
                RETURN c.chat_id as chat_id,
                       c.title as title,
                       cluster_count,
                       clusters[0..5] as sample_clusters
                ORDER BY cluster_count DESC
                LIMIT $limit
                """,
                **params,
            )
            items = []
            for rec in result:
                items.append(
                    {
                        "chat_id": rec["chat_id"],
                        "title": rec["title"],
                        "bridge_score": rec["cluster_count"],
                        "clusters": rec["sample_clusters"],
                    }
                )
        data = {"filters": {"domain_a": domain_a, "domain_b": domain_b}, "items": items, "count": len(items), "limit": limit}
        return ApiResponse(data=data, message=f"Found {len(items)} bridges")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"discover_bridges error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explain/path", response_model=ApiResponse)
async def explain_path(
    source_id: str = Query(..., description="Source chat ID"),
    target_id: str = Query(..., description="Target chat ID"),
    max_hops: int = Query(default=2, ge=1, le=4),
):
    """Explain connection between two chats using short patterns and evidence.

    We consider:
    - Direct similarity edge (SIMILAR_TO_*).
    - Shared cluster via chunk membership.
    - Shared tags.
    """
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")

        with neo4j_driver.session() as session:
            # Direct similarity
            sim = session.run(
                """
                MATCH (a:Chat {chat_id:$a})-[:SIMILAR_TO_CHAT_HIGH|:SIMILAR_TO_CHAT_MEDIUM]->(b:Chat {chat_id:$b})
                RETURN a.chat_id as a, b.chat_id as b
                """,
                a=source_id,
                b=target_id,
            ).single()

            path_type = None
            path: List[Dict[str, Any]] = []
            evidence: List[Dict[str, Any]] = []

            if sim:
                path_type = "direct_similarity"
                path = [
                    {"type": "Chat", "id": source_id},
                    {"type": "SIMILAR_TO", "weight": "high_or_medium"},
                    {"type": "Chat", "id": target_id},
                ]

            if not path_type:
                # Shared cluster
                rec = session.run(
                    """
                    MATCH (a:Chat {chat_id:$a})-[:CONTAINS]->(:Message)-[:HAS_CHUNK]->(ch1:Chunk)
                    MATCH (b:Chat {chat_id:$b})-[:CONTAINS]->(:Message)-[:HAS_CHUNK]->(ch2:Chunk)
                    MATCH (cl:Cluster)-[:HAS_CHUNK]->(ch1)
                    MATCH (cl)-[:HAS_CHUNK]->(ch2)
                    RETURN cl.cluster_id as cluster_id
                    LIMIT 1
                    """,
                    a=source_id,
                    b=target_id,
                ).single()
                if rec:
                    path_type = "shared_cluster"
                    cluster_id = rec["cluster_id"]
                    path = [
                        {"type": "Chat", "id": source_id},
                        {"type": "CONTAINS"},
                        {"type": "Message"},
                        {"type": "HAS_CHUNK"},
                        {"type": "Chunk"},
                        {"type": "IN_CLUSTER", "cluster_id": cluster_id},
                        {"type": "Chunk"},
                        {"type": "HAS_CHUNK"},
                        {"type": "Message"},
                        {"type": "CONTAINS"},
                        {"type": "Chat", "id": target_id},
                    ]

            # Evidence via shared tags
            tag_rec = session.run(
                """
                MATCH (a:Chat {chat_id:$a})-[:CONTAINS]->(m1:Message)
                OPTIONAL MATCH (t1:Tag)-[:TAGS]->(m1)
                WITH a, collect(DISTINCT t1.tags) as a_tags
                MATCH (b:Chat {chat_id:$b})-[:CONTAINS]->(m2:Message)
                OPTIONAL MATCH (t2:Tag)-[:TAGS]->(m2)
                WITH a_tags, collect(DISTINCT t2.tags) as b_tags
                RETURN a_tags, b_tags
                """,
                a=source_id,
                b=target_id,
            ).single()
            shared_tags: List[str] = []
            if tag_rec:
                # Flatten tag lists of lists
                a_tags = {t for tl in (tag_rec["a_tags"] or []) for t in (tl or [])}
                b_tags = {t for tl in (tag_rec["b_tags"] or []) for t in (tl or [])}
                shared_tags = sorted(list(a_tags & b_tags))[:10]
                if shared_tags:
                    evidence.append({"type": "shared_tags", "tags": shared_tags})

            if not path_type:
                path_type = "no_short_path"

        data = {
            "source_id": source_id,
            "target_id": target_id,
            "max_hops": max_hops,
            "path_type": path_type,
            "path": path,
            "evidence": evidence,
        }
        return ApiResponse(data=data, message="Explain path computed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"explain_path error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _bucket_ts(ts: float, granularity: str) -> int:
    if ts is None:
        return 0
    if granularity == "day":
        return int(ts // 86400 * 86400)
    if granularity == "week":
        return int(ts // (7 * 86400) * (7 * 86400))
    return int(ts // (30 * 86400) * (30 * 86400))


@router.get("/evolution/cluster/{cluster_id}", response_model=ApiResponse)
async def evolution_cluster(
    cluster_id: str,
    granularity: str = Query(default="week", regex="^(day|week|month)$"),
    start_time: Optional[float] = Query(default=None),
    end_time: Optional[float] = Query(default=None),
):
    """Return time-bucketed evolution metrics for a cluster using message timestamps."""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")

        with neo4j_driver.session() as session:
            recs = session.run(
                """
                MATCH (cl:Cluster {cluster_id:$cluster_id})-[:HAS_CHUNK]->(ch:Chunk)
                MATCH (m:Message)-[:HAS_CHUNK]->(ch)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                RETURN m.timestamp as ts,
                       collect(DISTINCT t.tags) as tag_lists
                """,
                cluster_id=cluster_id,
            )
            buckets: Dict[int, Dict[str, Any]] = {}
            for r in recs:
                ts = r["ts"]
                if ts is None:
                    continue
                if start_time and ts < start_time:
                    continue
                if end_time and ts > end_time:
                    continue
                bucket = _bucket_ts(float(ts), granularity)
                if bucket not in buckets:
                    buckets[bucket] = {"count_messages": 0, "top_tags": {}, "bucket_start": bucket}
                buckets[bucket]["count_messages"] += 1
                # Flatten tag list
                tags = [tag for tl in (r["tag_lists"] or []) for tag in (tl or [])]
                for tag in tags:
                    buckets[bucket]["top_tags"][tag] = buckets[bucket]["top_tags"].get(tag, 0) + 1

            points = []
            for b in sorted(buckets.keys()):
                top_tags = sorted(buckets[b]["top_tags"].items(), key=lambda x: x[1], reverse=True)[:10]
                points.append({
                    "bucket_start": b,
                    "count_messages": buckets[b]["count_messages"],
                    "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
                })

        data = {
            "cluster_id": cluster_id,
            "granularity": granularity,
            "start_time": start_time,
            "end_time": end_time,
            "points": points,
        }
        return ApiResponse(data=data, message=f"Evolution with {len(points)} buckets")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"evolution_cluster error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _get_chat_tags(session, chat_id: str) -> Set[str]:
    rec = session.run(
        """
        MATCH (c:Chat {chat_id:$chat_id})-[:CONTAINS]->(m:Message)
        OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
        RETURN collect(DISTINCT t.tags) as tag_lists
        """,
        chat_id=chat_id,
    ).single()
    if not rec:
        return set()
    return {t for tl in (rec["tag_lists"] or []) for t in (tl or [])}


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@router.get("/serendipity", response_model=ApiResponse)
async def serendipity(
    seed_id: str = Query(..., description="Seed chat or chunk id"),
    type: str = Query(default="chat", regex="^(chat|chunk)$"),
    novelty: float = Query(default=0.7, ge=0, le=1),
    limit: int = Query(default=5, ge=1, le=50),
):
    """Return novel-but-relevant recommendations using Qdrant + tag-based novelty.

    For chat seed: encode chat title (or last user message) → Qdrant search → enrich with Neo4j →
    compute novelty = 1 - Jaccard(tags_seed, tags_candidate). Rank by novelty * similarity.
    """
    try:
        if not (neo4j_driver and qdrant_client and embedding_model):
            raise HTTPException(status_code=503, detail="Service dependencies not ready")

        with neo4j_driver.session() as session:
            seed_text = None
            seed_tags: Set[str] = set()
            if type == "chat":
                rec = session.run(
                    """
                    MATCH (c:Chat {chat_id:$cid})
                    OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
                    WITH c, m
                    ORDER BY m.timestamp DESC
                    RETURN c.title as title, m.content as last_content
                    LIMIT 1
                    """,
                    cid=seed_id,
                ).single()
                if not rec:
                    raise HTTPException(status_code=404, detail="Seed chat not found")
                seed_text = rec["last_content"] or rec["title"] or ""
                seed_tags = _get_chat_tags(session, seed_id)
            else:
                # chunk seed: get chunk content from Neo4j
                rec = session.run(
                    """
                    MATCH (ch:Chunk {chunk_id:$chunk_id})
                    RETURN ch.content as content
                    """,
                    chunk_id=seed_id,
                ).single()
                if not rec:
                    raise HTTPException(status_code=404, detail="Seed chunk not found")
                seed_text = rec["content"] or ""

        if not seed_text:
            raise HTTPException(status_code=400, detail="No text found to seed recommendations")

        # Embed and search Qdrant
        vector = embedding_model.encode(seed_text).tolist()
        results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=vector,
            limit=limit * 4,
            with_payload=True,
        )

        # Enrich with Neo4j and compute novelty
        recs: List[Dict[str, Any]] = []
        with neo4j_driver.session() as session:
            for res in results:
                payload = res.payload or {}
                cand_chat_id = payload.get("chat_id")
                if type == "chat" and cand_chat_id == seed_id:
                    continue
                cand_tags = _get_chat_tags(session, cand_chat_id) if cand_chat_id else set()
                j = _jaccard(seed_tags, cand_tags)
                novelty_score = 1.0 - j
                combined = novelty * novelty_score + (1 - novelty) * float(res.score or 0.0)
                recs.append(
                    {
                        "chunk_id": payload.get("chunk_id"),
                        "chat_id": cand_chat_id,
                        "message_id": payload.get("message_id"),
                        "content": payload.get("content"),
                        "similarity": float(res.score or 0.0),
                        "novelty": novelty_score,
                        "combined": combined,
                        "tags": list(cand_tags)[:10],
                    }
                )
        # Rank and trim
        recs.sort(key=lambda x: x["combined"], reverse=True)
        items = recs[:limit]
        data = {
            "seed_id": seed_id,
            "type": type,
            "novelty": novelty,
            "items": items,
            "count": len(items),
            "limit": limit,
        }
        return ApiResponse(data=data, message=f"Serendipity generated {len(items)} items")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"serendipity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=ApiResponse)
async def compare(
    payload: Dict[str, Any] = Body(..., example={"type": "chat", "ids": ["a", "b"]}),
):
    """Compare entities side-by-side using tag and cluster overlap (chat support)."""
    try:
        if not neo4j_driver:
            raise HTTPException(status_code=503, detail="Database not connected")
        compare_type = payload.get("type", "chat")
        ids: List[str] = payload.get("ids", [])
        if compare_type != "chat" or len(ids) < 2:
            raise HTTPException(status_code=400, detail="Provide type='chat' and at least 2 ids")

        with neo4j_driver.session() as session:
            # Tags
            tag_sets = [(_get_chat_tags(session, cid)) for cid in ids]
            all_tags = list(sorted(set().union(*tag_sets)))
            # Clusters per chat
            cluster_sets: List[Set[str]] = []
            for cid in ids:
                rec = session.run(
                    """
                    MATCH (c:Chat {chat_id:$cid})-[:CONTAINS]->(:Message)-[:HAS_CHUNK]->(ch:Chunk)
                    MATCH (cl:Cluster)-[:HAS_CHUNK]->(ch)
                    RETURN collect(DISTINCT cl.cluster_id) as clusters
                    """,
                    cid=cid,
                ).single()
                clusters = set((rec and rec["clusters"]) or [])
                cluster_sets.append(set(map(str, clusters)))

        # Overlap scores (pairwise for first two)
        a_tags, b_tags = tag_sets[0], tag_sets[1]
        tags_overlap = _jaccard(a_tags, b_tags)
        a_clusters, b_clusters = cluster_sets[0], cluster_sets[1]
        clusters_overlap = _jaccard(a_clusters, b_clusters)

        data = {
            "type": compare_type,
            "ids": ids,
            "summary": {
                "overlap_score": round((tags_overlap + clusters_overlap) / 2.0, 4),
                "tags_overlap": round(tags_overlap, 4),
                "clusters_overlap": round(clusters_overlap, 4),
                "shared_tags": sorted(list(a_tags & b_tags))[:20],
                "divergent_tags": {
                    ids[0]: sorted(list(a_tags - b_tags))[:20],
                    ids[1]: sorted(list(b_tags - a_tags))[:20],
                },
                "shared_clusters": sorted(list(a_clusters & b_clusters))[:20],
            },
        }
        return ApiResponse(data=data, message="Compare computed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 