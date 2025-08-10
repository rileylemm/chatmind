#!/usr/bin/env python3
"""
Turn Summary Embedding (Local)

Embeds turn summaries using a local Sentence Transformers model.
Outputs vectors to data/processed/turns/turn_embeddings.jsonl with incremental hashing.
"""

import json
import jsonlines
import numpy as np
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import logging
from tqdm import tqdm
import hashlib
import pickle
from datetime import datetime
import click

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence Transformers not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DirectIncrementalTurnEmbedder:
    """Embeds turn summaries using local models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", processed_dir: str = "data/processed"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError("sentence-transformers not installed")
        self.model = SentenceTransformer(model_name)
        self.processed_dir = Path(processed_dir)
        self.turns_dir = self.processed_dir / "turns"
        self.turns_dir.mkdir(parents=True, exist_ok=True)

    def _generate_turn_hash(self, turn: Dict) -> str:
        """Generate a hash for a turn to track if it needs embedding."""
        key = {
            'turn_uid': turn.get('turn_uid'),
            'summary': turn.get('summary', ''),
            'chat_id': turn.get('chat_id', ''),
            'turn_id': turn.get('turn_id', 0)
        }
        return hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()

    def _load_processed_hashes(self, state_file: Path) -> Set[str]:
        if state_file.exists():
            try:
                with open(state_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed turn hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed turn hashes: {e}")
        return set()

    def _save_processed_hashes(self, hashes: Set[str], state_file: Path) -> None:
        try:
            with open(state_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed turn hashes")
        except Exception as e:
            logger.error(f"Failed to save processed turn hashes: {e}")

    def _load_turns(self, turns_file: Path) -> List[Dict]:
        turns: List[Dict] = []
        with jsonlines.open(turns_file) as reader:
            for t in reader:
                turns.append(t)
        logger.info(f"Loaded {len(turns)} turns from {turns_file}")
        return turns

    def _identify_new_turns(self, all_turns: List[Dict], processed_hashes: Set[str]) -> List[Dict]:
        new_turns: List[Dict] = []
        for t in all_turns:
            h = self._generate_turn_hash(t)
            if h not in processed_hashes:
                new_turns.append(t)
        logger.info(f"Found {len(new_turns)} new/changed turns out of {len(all_turns)} total")
        return new_turns

    def _embed_summaries(self, turns: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        if not turns:
            return np.array([]), []
        texts: List[str] = []
        for t in turns:
            texts.append((t.get('summary') or '').strip())
        embeddings = self.model.encode(texts, show_progress_bar=True)
        embedded: List[Dict] = []
        for i, t in enumerate(turns):
            vec = embeddings[i].tolist()
            embedded.append({
                'turn_uid': t.get('turn_uid'),
                'chat_id': t.get('chat_id'),
                'turn_id': t.get('turn_id'),
                'summary': t.get('summary', ''),
                'embedding': vec,
                'embedding_hash': hashlib.sha256(json.dumps(vec).encode()).hexdigest()
            })
        logger.info(f"Generated embeddings for {len(embedded)} turns")
        return embeddings, embedded

    def _load_existing_embeddings(self, embeddings_file: Path) -> List[Dict]:
        data: List[Dict] = []
        if embeddings_file.exists():
            with jsonlines.open(embeddings_file) as reader:
                for item in reader:
                    data.append(item)
            logger.info(f"Loaded {len(data)} existing turn embeddings")
        return data

    def _save_embeddings(self, records: List[Dict], embeddings_file: Path) -> None:
        with jsonlines.open(embeddings_file, mode='w') as writer:
            for rec in records:
                writer.write(rec)
        logger.info(f"Saved {len(records)} turn embeddings to {embeddings_file}")

    def _save_metadata(self, stats: Dict) -> None:
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'turn_embedding',
            'stats': stats,
            'version': '1.0'
        }
        meta_file = self.turns_dir / 'embedding_metadata.json'
        try:
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {meta_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def process_turns_to_embeddings(self, turns_file: Path, state_file: Path, force_reprocess: bool = False) -> Dict:
        logger.info("🚀 Starting turn summary embedding...")
        embeddings_file = self.turns_dir / 'turn_embeddings.jsonl'
        existing = self._load_existing_embeddings(embeddings_file)

        processed_hashes: Set[str] = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_hashes(state_file)

        all_turns = self._load_turns(turns_file)
        if not all_turns:
            logger.warning("No turns found")
            return {'status': 'no_turns'}

        new_turns = self._identify_new_turns(all_turns, processed_hashes)
        if not new_turns and not force_reprocess:
            logger.info("No new turns to embed")
            return {'status': 'no_new_turns'}

        new_embeddings, embedded_new = self._embed_summaries(new_turns)
        if len(new_embeddings) == 0:
            logger.info("No new embeddings generated")
            return {'status': 'no_embeddings'}

        # Merge existing by turn_uid (dedupe)
        existing_by_uid = {e.get('turn_uid'): e for e in existing}
        for rec in embedded_new:
            existing_by_uid[rec.get('turn_uid')] = rec
            processed_hashes.add(self._generate_turn_hash({
                'turn_uid': rec.get('turn_uid'),
                'summary': rec.get('summary'),
                'chat_id': rec.get('chat_id'),
                'turn_id': rec.get('turn_id'),
            }))

        merged = list(existing_by_uid.values())
        self._save_embeddings(merged, embeddings_file)
        self._save_processed_hashes(processed_hashes, state_file)

        stats = {
            'status': 'success',
            'total_turn_embeddings': len(merged),
            'new_turns': len(new_turns),
            'existing_turns': len(existing),
            'embedding_dimension': len(new_embeddings[0]) if len(new_embeddings) > 0 else 0
        }
        self._save_metadata(stats)
        logger.info(f"✅ Turn embedding complete: {len(embedded_new)} new embeddings")
        return stats


@click.command()
@click.option('--processed-dir', default='data/processed', help='Processed data directory')
@click.option('--model-name', default='all-MiniLM-L6-v2', help='Sentence Transformers model')
@click.option('--force', is_flag=True, help='Force re-embed all turns')
def main(processed_dir: str, model_name: str, force: bool):
    embedder = DirectIncrementalTurnEmbedder(model_name=model_name, processed_dir=processed_dir)
    turns_file = Path(processed_dir) / 'turns' / 'turns.jsonl'
    state_file = Path(processed_dir) / 'turns' / 'turn_embedding_hashes.pkl'
    result = embedder.process_turns_to_embeddings(turns_file, state_file, force_reprocess=force)
    if result.get('status') == 'success':
        logger.info("✅ Turn embeddings generated successfully")
    else:
        logger.info(f"ℹ️ Turn embedding result: {result}")


if __name__ == '__main__':
    main() 