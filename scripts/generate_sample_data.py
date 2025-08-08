#!/usr/bin/env python3
"""
Generate a tiny, deterministic sample dataset in data/processed/ that matches
loader expectations (Neo4j + Qdrant) without running heavy pipeline steps.

Usage:
  python scripts/generate_sample_data.py

This will populate data/processed/ with:
- ingestion/chats.jsonl
- chunking/chunks.jsonl
- embedding/embeddings.jsonl
- clustering/clustered_embeddings.jsonl
- tagging/processed_tags.jsonl
- cluster_summarization/cluster_summaries.json
- chat_summarization/chat_summaries.json
- positioning/chat_summary_embeddings.jsonl
- positioning/cluster_summary_embeddings.jsonl
- positioning/chat_positions.jsonl
- positioning/cluster_positions.jsonl
- similarity/chat_similarities.jsonl
- similarity/cluster_similarities.jsonl

All IDs, hashes, vectors, and positions are seeded for reproducibility.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple
import random
import math

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED = PROJECT_ROOT / "data" / "processed"

RNG_SEED = 42
VECTOR_DIM = 384  # must match Qdrant loader expectation


def ensure_dirs() -> None:
    subdirs = [
        PROCESSED / "ingestion",
        PROCESSED / "chunking",
        PROCESSED / "embedding",
        PROCESSED / "clustering",
        PROCESSED / "tagging",
        PROCESSED / "cluster_summarization",
        PROCESSED / "chat_summarization",
        PROCESSED / "positioning",
        PROCESSED / "similarity",
    ]
    for d in subdirs:
        d.mkdir(parents=True, exist_ok=True)


def sha256_json(data: Dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def seeded_vector(seed_val: str, dim: int = VECTOR_DIM) -> List[float]:
    rnd = random.Random(seed_val)
    return [rnd.uniform(-1.0, 1.0) for _ in range(dim)]


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def generate_chats() -> List[Dict]:
    # Three minimal chats with messages
    chats = []
    base_messages = [
        {
            "title": "Project Kickoff",
            "messages": [
                {"id": "m1", "role": "user", "content": "Let's plan the project scope."},
                {"id": "m2", "role": "assistant", "content": "We should define milestones and owners."},
            ],
        },
        {
            "title": "Healthy Habits",
            "messages": [
                {"id": "m3", "role": "user", "content": "Tips for consistent exercise?"},
                {"id": "m4", "role": "assistant", "content": "Start small, track progress, and stay accountable."},
            ],
        },
        {
            "title": "Tech Stack",
            "messages": [
                {"id": "m5", "role": "user", "content": "React vs Svelte for dashboards?"},
                {"id": "m6", "role": "assistant", "content": "React has broader ecosystem; choose based on team skills."},
            ],
        },
    ]

    for i, c in enumerate(base_messages, start=1):
        chat_data = {
            "title": c["title"],
            "messages": c["messages"],
        }
        content_hash = sha256_json(chat_data)
        chats.append({
            "chat_id": f"chat_{i}",
            "content_hash": content_hash,
            "title": c["title"],
            "create_time": f"2025-01-0{i}T10:00:00",
            "source_file": f"sample_{i}.json",
            "messages": c["messages"],
        })
    return chats


def generate_chunks(chats: List[Dict]) -> List[Dict]:
    chunks: List[Dict] = []
    for chat in chats:
        for msg in chat["messages"]:
            message_data = {
                "content": msg["content"],
                "chat_id": chat["content_hash"],
                "message_id": msg["id"],
                "role": msg["role"],
            }
            message_hash = sha256_json(message_data)
            # Create a single chunk per message for simplicity
            chunk_id = f"chunk_{message_hash[:12]}"
            chunks.append({
                "chunk_id": chunk_id,
                "chunk_hash": chunk_id,
                "content": msg["content"],
                "role": msg["role"],
                "token_count": len(msg["content"].split()),
                "chat_id": chat["content_hash"],
                "message_id": msg["id"],
                "message_hash": message_hash,
            })
    return chunks


def generate_chunk_embeddings(chunks: List[Dict]) -> List[Dict]:
    embeddings: List[Dict] = []
    for ch in chunks:
        vec = seeded_vector(ch["chunk_id"])
        embeddings.append({
            "chunk_id": ch["chunk_id"],
            "embedding": vec,
            "embedding_hash": sha256_json({"embedding": vec}),
        })
    return embeddings


def generate_clustered_embeddings(embeddings: List[Dict]) -> List[Dict]:
    clustered: List[Dict] = []
    # Assign clusters deterministically: first half -> 0, second half -> 1
    n = len(embeddings)
    for i, e in enumerate(embeddings):
        cluster_id = "0" if i < n / 2 else "1"
        # Simple UMAP-like layout: small circles per cluster
        angle = (i / max(1, n)) * 2 * math.pi
        radius = 0.5 if cluster_id == "0" else 0.8
        umap_x = math.cos(angle) * radius
        umap_y = math.sin(angle) * radius
        clustered.append({
            "chunk_id": e["chunk_id"],
            "cluster_id": cluster_id,
            "umap_x": float(umap_x),
            "umap_y": float(umap_y),
        })
    return clustered


def generate_processed_tags(chunks: List[Dict]) -> List[Dict]:
    # Minimal normalized tags per message_hash
    tag_pool = ["#project", "#health", "#technology"]
    out: List[Dict] = []
    for i, ch in enumerate(chunks):
        out.append({
            "message_hash": ch["message_hash"],
            "tags": [tag_pool[i % len(tag_pool)]],
            "topics": [],
            "domain": ["business", "personal", "technology"][i % 3],
            "complexity": "medium",
            "sentiment": "neutral",
            "intent": "informative",
        })
    return out


def generate_summaries(clustered: List[Dict], chats: List[Dict]) -> Tuple[Dict, Dict]:
    # Cluster summaries keyed by cluster_id (strings)
    cluster_ids = sorted({c["cluster_id"] for c in clustered})
    cluster_summaries: Dict[str, Dict] = {}
    for cid in cluster_ids:
        cluster_summaries[cid] = {
            "summary": f"Cluster {cid} overview",
            "domain": "mixed",
            "topics": ["overview"],
            "complexity": "medium",
            "key_points": [f"Key point {cid}"],
            "common_tags": ["#sample"],
        }

    chat_summaries: Dict[str, Dict] = {}
    for chat in chats:
        chat_summaries[chat["content_hash"]] = {
            "summary": f"Summary for {chat['title']}",
            "domain": "mixed",
            "topics": ["summary"],
            "complexity": "medium",
            "key_points": ["Concise"],
        }
    return cluster_summaries, chat_summaries


def generate_summary_embeddings(cluster_summaries: Dict[str, Dict], chat_summaries: Dict[str, Dict]) -> Tuple[List[Dict], List[Dict]]:
    cluster_vecs: List[Dict] = []
    for cid in cluster_summaries.keys():
        vec = seeded_vector(f"cluster_summary_{cid}")
        cluster_vecs.append({"cluster_id": cid, "embedding": vec, "hash": sha256_json({"cid": cid, "v": vec})})

    chat_vecs: List[Dict] = []
    for chat_id in chat_summaries.keys():
        vec = seeded_vector(f"chat_summary_{chat_id[:12]}")
        chat_vecs.append({"chat_id": chat_id, "embedding": vec, "hash": sha256_json({"chat": chat_id, "v": vec})})

    return cluster_vecs, chat_vecs


def generate_positions(cluster_summaries: Dict[str, Dict], chat_summaries: Dict[str, Dict]) -> Tuple[List[Dict], List[Dict]]:
    # Simple layout on a circle for chats; line for clusters
    chat_positions: List[Dict] = []
    keys = list(chat_summaries.keys())
    for i, chat_id in enumerate(keys):
        angle = (i / max(1, len(keys))) * 2 * math.pi
        x = math.cos(angle)
        y = math.sin(angle)
        entry = {
            "chat_id": chat_id,
            "chat_hash": chat_id,
            "x": float(x),
            "y": float(y),
            "umap_x": float(x),
            "umap_y": float(y),
            "summary_hash": sha256_json(chat_summaries[chat_id]),
            "positioning_hash": sha256_json({"cid": chat_id, "x": x, "y": y}),
        }
        chat_positions.append(entry)

    cluster_positions: List[Dict] = []
    for i, cid in enumerate(sorted(cluster_summaries.keys())):
        x = -0.5 + i * 1.0
        y = 0.25 if i % 2 == 0 else -0.25
        entry = {
            "cluster_id": cid,
            "cluster_hash": cid,
            "x": float(x),  # kept for cluster node creation path
            "y": float(y),
            "umap_x": float(x),  # used by position updater
            "umap_y": float(y),
            "summary_hash": sha256_json(cluster_summaries[cid]),
            "positioning_hash": sha256_json({"cid": cid, "x": x, "y": y}),
        }
        cluster_positions.append(entry)

    return chat_positions, cluster_positions


def generate_similarities(chat_vecs: List[Dict], cluster_vecs: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    chat_sims: List[Dict] = []
    for i in range(len(chat_vecs)):
        for j in range(i + 1, len(chat_vecs)):
            s = cosine(chat_vecs[i]["embedding"], chat_vecs[j]["embedding"])
            if s >= 0.5:
                chat_sims.append({
                    "chat1_id": chat_vecs[i]["chat_id"],
                    "chat2_id": chat_vecs[j]["chat_id"],
                    "similarity": float(s),
                })

    cluster_sims: List[Dict] = []
    for i in range(len(cluster_vecs)):
        for j in range(i + 1, len(cluster_vecs)):
            s = cosine(cluster_vecs[i]["embedding"], cluster_vecs[j]["embedding"])
            if s >= 0.5:
                cluster_sims.append({
                    "cluster1_id": cluster_vecs[i]["cluster_id"],
                    "cluster2_id": cluster_vecs[j]["cluster_id"],
                    "similarity": float(s),
                })
    return chat_sims, cluster_sims


def main() -> None:
    random.seed(RNG_SEED)
    ensure_dirs()

    # 1) chats and chunks
    chats = generate_chats()
    chunks = generate_chunks(chats)

    write_jsonl(PROCESSED / "ingestion" / "chats.jsonl", chats)
    write_jsonl(PROCESSED / "chunking" / "chunks.jsonl", chunks)

    # 2) chunk embeddings and clustered embeddings
    chunk_embeddings = generate_chunk_embeddings(chunks)
    write_jsonl(PROCESSED / "embedding" / "embeddings.jsonl", chunk_embeddings)

    clustered = generate_clustered_embeddings(chunk_embeddings)
    write_jsonl(PROCESSED / "clustering" / "clustered_embeddings.jsonl", clustered)

    # 3) processed tags
    processed_tags = generate_processed_tags(chunks)
    write_jsonl(PROCESSED / "tagging" / "processed_tags.jsonl", processed_tags)

    # 4) summaries
    cluster_summaries, chat_summaries = generate_summaries(clustered, chats)
    (PROCESSED / "cluster_summarization" / "cluster_summaries.json").write_text(
        json.dumps(cluster_summaries, indent=2)
    )
    (PROCESSED / "chat_summarization" / "chat_summaries.json").write_text(
        json.dumps(chat_summaries, indent=2)
    )

    # 5) summary embeddings and positions
    cluster_summary_vecs, chat_summary_vecs = generate_summary_embeddings(cluster_summaries, chat_summaries)
    write_jsonl(PROCESSED / "positioning" / "cluster_summary_embeddings.jsonl", cluster_summary_vecs)
    write_jsonl(PROCESSED / "positioning" / "chat_summary_embeddings.jsonl", chat_summary_vecs)

    chat_positions, cluster_positions = generate_positions(cluster_summaries, chat_summaries)
    write_jsonl(PROCESSED / "positioning" / "chat_positions.jsonl", chat_positions)
    write_jsonl(PROCESSED / "positioning" / "cluster_positions.jsonl", cluster_positions)

    # 6) similarities
    chat_sims, cluster_sims = generate_similarities(chat_summary_vecs, cluster_summary_vecs)
    write_jsonl(PROCESSED / "similarity" / "chat_similarities.jsonl", chat_sims)
    write_jsonl(PROCESSED / "similarity" / "cluster_similarities.jsonl", cluster_sims)

    print("✅ Sample data generated under data/processed/")


if __name__ == "__main__":
    main() 