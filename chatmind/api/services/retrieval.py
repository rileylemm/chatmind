import os
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any, Set
import hashlib

# Globals (kept simple)
INDEX_DIR_NAME = "index"
INDEX_DB_NAME = "turn_summaries.db"
INDEX_HASH_NAME = "turn_index.hash"
TURNS_REL_PATH = Path("data/processed/turns/turns.jsonl")


def _find_project_root(start: Path) -> Path:
    for parent in [start] + list(start.parents):
        if (parent / ".env").exists() or (parent / ".git").exists():
            return parent
    # Fallback
    return start


def _get_paths() -> Tuple[Path, Path, Path]:
    """Return (project_root, index_db_path, turns_jsonl_path)."""
    project_root = _find_project_root(Path(__file__).resolve().parent)
    index_dir = project_root / "data" / "processed" / INDEX_DIR_NAME
    index_dir.mkdir(parents=True, exist_ok=True)
    index_db = index_dir / INDEX_DB_NAME
    turns_path = project_root / TURNS_REL_PATH
    return project_root, index_db, turns_path


def _file_fingerprint(path: Path) -> str:
    try:
        stat = path.stat()
        payload = f"{path}:{stat.st_size}:{int(stat.st_mtime)}"
        return hashlib.sha256(payload.encode()).hexdigest()
    except FileNotFoundError:
        return "missing"


def ensure_bm25_index() -> bool:
    """Create/refresh the FTS5 index over turn summaries if input changed."""
    _, index_db, turns_path = _get_paths()
    hash_file = index_db.parent / INDEX_HASH_NAME
    current_fp = _file_fingerprint(turns_path)

    prior_fp = None
    if hash_file.exists():
        prior_fp = hash_file.read_text().strip()

    if prior_fp == current_fp and index_db.exists():
        return True

    # (Re)build index
    if index_db.exists():
        index_db.unlink()

    conn = sqlite3.connect(index_db)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("CREATE VIRTUAL TABLE turns_fts USING fts5(turn_uid, chat_id, turn_id, summary);")
        # Bulk insert
        import jsonlines  # type: ignore
        rows: List[Tuple[str, str, int, str]] = []
        if not turns_path.exists():
            return False
        with jsonlines.open(turns_path) as reader:
            for t in reader:
                rows.append((t.get("turn_uid", ""), t.get("chat_id", ""), int(t.get("turn_id", 0)), (t.get("summary") or "")))
        conn.executemany("INSERT INTO turns_fts(turn_uid, chat_id, turn_id, summary) VALUES (?, ?, ?, ?)", rows)
        conn.commit()
        hash_file.write_text(current_fp)
        return True
    finally:
        conn.close()


def bm25_search(query: str, topn: int = 200) -> List[str]:
    """Return turn_uids by FTS5 rank (lower bm25() is better)."""
    _, index_db, _ = _get_paths()
    if not index_db.exists():
        return []
    conn = sqlite3.connect(index_db)
    try:
        conn.create_function("rank", 1, lambda s: s)  # placeholder if needed
        sql = "SELECT turn_uid, bm25(turns_fts) as score FROM turns_fts WHERE turns_fts MATCH ? ORDER BY score LIMIT ?"
        cur = conn.execute(sql, (query, int(topn)))
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def qdrant_search_turns(qdrant_client, embedding_model, query: str, topn: int = 200) -> List[Tuple[str, float]]:
    vec = embedding_model.encode(query).tolist()
    res = qdrant_client.search(collection_name="chatmind_turns", query_vector=vec, limit=topn, with_payload=True, with_vectors=False)
    out: List[Tuple[str, float]] = []
    for r in res:
        uid = (r.payload or {}).get("turn_uid")
        if uid:
            out.append((uid, float(r.score)))
    return out


def union_topn(lex_ids: List[str], vec_ids_scores: List[Tuple[str, float]], n: int = 300) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    # Interleave to preserve diversity
    vec_ids = [vid for vid, _ in vec_ids_scores]
    i = j = 0
    while len(out) < n and (i < len(lex_ids) or j < len(vec_ids)):
        if i < len(lex_ids):
            if lex_ids[i] not in seen:
                seen.add(lex_ids[i]); out.append(lex_ids[i])
            i += 1
        if len(out) >= n:
            break
        if j < len(vec_ids):
            if vec_ids[j] not in seen:
                seen.add(vec_ids[j]); out.append(vec_ids[j])
            j += 1
    return out


def expand_neighbors(neo4j_driver, turn_uids: List[str], hop: int = 1) -> List[str]:
    if not turn_uids:
        return []
    with neo4j_driver.session() as session:
        result = session.run(
            """
            UNWIND $uids AS uid
            MATCH (t:Turn {turn_uid: uid})
            OPTIONAL MATCH (t)-[:NEXT]->(n1:Turn)
            OPTIONAL MATCH (p1:Turn)-[:NEXT]->(t)
            RETURN uid as src,
                   collect(DISTINCT n1.turn_uid) as next_uids,
                   collect(DISTINCT p1.turn_uid) as prev_uids
            """,
            uids=turn_uids,
        )
        expanded: Set[str] = set(turn_uids)
        for rec in result:
            for u in (rec["next_uids"] or []):
                if u: expanded.add(u)
            for u in (rec["prev_uids"] or []):
                if u: expanded.add(u)
        return list(expanded)


def fetch_turns(neo4j_driver, turn_uids: List[str]) -> List[Dict[str, Any]]:
    if not turn_uids:
        return []
    with neo4j_driver.session() as session:
        result = session.run(
            """
            UNWIND $uids AS uid
            MATCH (t:Turn {turn_uid: uid})
            RETURN t.turn_uid AS turn_uid,
                   t.chat_id AS chat_id,
                   t.turn_id AS turn_id,
                   t.summary AS summary,
                   t.ts AS ts
            """,
            uids=turn_uids,
        )
        rows = [dict(rec) for rec in result]
    # Preserve requested order
    pos = {u: i for i, u in enumerate(turn_uids)}
    rows.sort(key=lambda r: pos.get(r["turn_uid"], 10**9))
    return rows


def cross_encode_rerank(cross_encoder, query: str, turns: List[Dict[str, Any]], batch_size: int = 64, topk: int = 200) -> List[Dict[str, Any]]:
    """Score (query, summary) pairs with cross-encoder and return topk turns annotated with rerank_score."""
    if not turns or cross_encoder is None:
        return turns
    pairs = [(query, t.get("summary", "")) for t in turns]
    scores: List[float] = []
    # Batched scoring
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i+batch_size]
        s = cross_encoder.predict(batch)
        scores.extend([float(x) for x in s])
    for t, sc in zip(turns, scores):
        t["rerank_score"] = sc
    turns.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    return turns[:topk] 