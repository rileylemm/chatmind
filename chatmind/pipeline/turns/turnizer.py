#!/usr/bin/env python3
"""
Turnization step

Reads chats from data/processed/ingestion/chats.jsonl and produces turn-level atoms
with optional micro-summaries and sliding-window prev_turn_ids.
"""

import json
import jsonlines
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Turn:
    turn_uid: str
    chat_id: str
    turn_id: int
    ts: Optional[float]
    roles: List[str]
    text_user: str
    text_assistant: str
    summary: str
    prev_turn_ids: List[int]
    chunk_version: str
    embed_model: str
    embed_version: str


def _hash_turn(chat_id: str, turn_id: int, text_user: str, text_assistant: str) -> str:
    payload = {
        "chat_id": chat_id,
        "turn_id": turn_id,
        "text_user": text_user,
        "text_assistant": text_assistant,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _micro_summarize(text_user: str, text_assistant: str, max_len: int = 180) -> str:
    # Simple fallback micro-summarizer; replace with LLM later
    joined = (text_user or "")
    if text_assistant:
        if joined:
            joined += " → "
        joined += text_assistant
    joined = joined.strip().replace("\n", " ")
    if len(joined) <= max_len:
        return joined
    return joined[: max_len - 1] + "…"


def _pair_messages_to_turns(messages: List[Dict], chat_id: str, prev_window: int,
                             chunk_version: str, embed_model: str, embed_version: str) -> List[Turn]:
    # Filter or normalize roles
    seq: List[Tuple[str, Dict]] = []
    for msg in messages:
        role = msg.get("role", "unknown")
        seq.append((role, msg))

    turns: List[Turn] = []
    turn_id = 0
    i = 0
    while i < len(seq):
        role, msg = seq[i]
        user_text = ""
        assistant_text = ""
        ts = msg.get("timestamp")

        if role == "user":
            user_text = msg.get("content", "")
            # Pair with the next assistant if available
            if i + 1 < len(seq) and seq[i + 1][0] == "assistant":
                assistant_msg = seq[i + 1][1]
                assistant_text = assistant_msg.get("content", "")
                ts = assistant_msg.get("timestamp", ts)
                i += 2
            else:
                i += 1
        elif role == "assistant":
            assistant_text = msg.get("content", "")
            i += 1
        else:
            # Unknown/system/other; attach to previous assistant if exists else create single-sided
            user_text = msg.get("content", "")
            i += 1

        turn_id += 1
        turn_uid = f"{chat_id}:{turn_id}"
        summary = _micro_summarize(user_text, assistant_text)
        prev_ids = list(range(max(1, turn_id - prev_window), turn_id))

        turns.append(Turn(
            turn_uid=turn_uid,
            chat_id=chat_id,
            turn_id=turn_id,
            ts=ts,
            roles=["user", "assistant"],
            text_user=user_text,
            text_assistant=assistant_text,
            summary=summary,
            prev_turn_ids=prev_ids,
            chunk_version=chunk_version,
            embed_model=embed_model,
            embed_version=embed_version,
        ))

    return turns


@click.command()
@click.option('--processed-dir', default='data/processed', help='Processed data directory')
@click.option('--prev-window', default=3, type=int, help='Sliding window size for prev_turn_ids')
@click.option('--chunk-version', default='v2', help='Chunk/version label for turns')
@click.option('--embed-model', default='all-MiniLM-L6-v2', help='Embedding model name (metadata only)')
@click.option('--embed-version', default='1', help='Embedding version tag (metadata only)')
@click.option('--force', is_flag=True, help='Force reprocess all turns')
def main(processed_dir: str, prev_window: int, chunk_version: str, embed_model: str, embed_version: str, force: bool):
    processed = Path(processed_dir)
    ingestion_file = processed / 'ingestion' / 'chats.jsonl'
    turns_dir = processed / 'turns'
    turns_dir.mkdir(parents=True, exist_ok=True)
    turns_file = turns_dir / 'turns.jsonl'
    hashes_file = turns_dir / 'turn_hashes.json'
    metadata_file = turns_dir / 'metadata.json'

    if not ingestion_file.exists():
        logger.error(f"Ingestion file not found: {ingestion_file}")
        raise SystemExit(1)

    # Load prior hashes
    prior_hashes: Dict[str, str] = {}
    if hashes_file.exists() and not force:
        try:
            prior_hashes = json.loads(hashes_file.read_text())
        except Exception:
            prior_hashes = {}

    total_turns = 0
    new_turns = 0

    # We will write fresh file; rebuild incrementally at turn granularity is okay because ids are stable per chat
    writer = jsonlines.open(turns_file, mode='w')
    try:
        with jsonlines.open(ingestion_file) as reader:
            for chat in reader:
                chat_id = chat.get('content_hash', chat.get('chat_id', 'unknown'))
                messages = chat.get('messages', [])
                turns = _pair_messages_to_turns(messages, chat_id, prev_window, chunk_version, embed_model, embed_version)
                for t in turns:
                    total_turns += 1
                    h = _hash_turn(t.chat_id, t.turn_id, t.text_user, t.text_assistant)
                    if force or prior_hashes.get(t.turn_uid) != h:
                        new_turns += 1
                    writer.write(asdict(t))
                    prior_hashes[t.turn_uid] = h
    finally:
        writer.close()

    # Save hashes and metadata
    hashes_file.write_text(json.dumps(prior_hashes, indent=2))
    meta = {
        'timestamp': datetime.now().isoformat(),
        'step': 'turnization',
        'stats': {
            'total_turns': total_turns,
            'new_or_changed_turns': new_turns,
        },
        'version': '1.0'
    }
    metadata_file.write_text(json.dumps(meta, indent=2))

    logger.info(f"Turnization complete. Total turns: {total_turns}, new/changed: {new_turns}")


if __name__ == '__main__':
    main() 