#!/usr/bin/env python3
"""
Chat Similarity Calculator

Calculates chat-level similarities using pre-computed chat summary embeddings.
Uses embeddings from positioning step to avoid duplicate computation.
Uses modular directory structure: data/processed/similarity/
"""

import json
import jsonlines
import pickle
import hashlib
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import click
from tqdm import tqdm
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatSimilarityCalculator:
    """Calculate chat similarities from pre-computed chat summary embeddings."""
    
    def __init__(self, embeddings_file: str = "data/processed/positioning/chat_summary_embeddings.jsonl"):
        self.embeddings_file = Path(embeddings_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/similarity")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_content_hash(self, data: Dict) -> str:
        """Generate a content hash for tracking."""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _get_processed_chat_hashes(self) -> set:
        """Get hashes of already processed chats."""
        hash_file = self.output_dir / "chat_similarity_hashes.pkl"
        if hash_file.exists():
            with open(hash_file, 'rb') as f:
                return pickle.load(f)
        return set()
    
    def _save_processed_chat_hashes(self, hashes: set) -> None:
        """Save hashes of processed chats."""
        hash_file = self.output_dir / "chat_similarity_hashes.pkl"
        with open(hash_file, 'wb') as f:
            pickle.dump(hashes, f)
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'similarity',
            'stats': stats,
            'version': '2.0',
            'method': 'chat_summary_embeddings',
            'source': 'positioning_step'
        }
        metadata_file = self.output_dir / "metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _load_chat_summary_embeddings(self) -> Dict[str, np.ndarray]:
        """Load pre-computed chat summary embeddings from positioning step."""
        logger.info(f"📖 Loading chat summary embeddings from {self.embeddings_file}")
        
        if not self.embeddings_file.exists():
            logger.error(f"❌ Chat summary embeddings file not found: {self.embeddings_file}")
            logger.error("Please run the positioning step first to generate embeddings")
            return {}
        
        chat_embeddings = {}
        chat_hashes = set()
        
        try:
            with jsonlines.open(self.embeddings_file) as reader:
                for item in tqdm(reader, desc="Loading embeddings"):
                    chat_id = item.get('chat_id')
                    embedding = item.get('embedding')
                    item_hash = item.get('hash', '')
                    
                    if chat_id and embedding is not None:
                        chat_embeddings[chat_id] = np.array(embedding, dtype=float)
                        chat_hashes.add(item_hash)
            
            logger.info(f"✅ Loaded {len(chat_embeddings)} chat summary embeddings")
            return chat_embeddings, chat_hashes
            
        except Exception as e:
            logger.error(f"❌ Failed to load chat summary embeddings: {e}")
            return {}, set()
    
    def calculate_similarities(self, chat_embeddings: Dict[str, np.ndarray], 
                             similarity_threshold: float = 0.8) -> List[Dict]:
        """Calculate similarities between all chat pairs."""
        logger.info(f"🔗 Calculating similarities (threshold: {similarity_threshold})...")
        
        chat_ids = list(chat_embeddings.keys())
        n = len(chat_ids)
        similarities = []
        
        # Calculate similarities for all pairs
        for i in tqdm(range(n), desc="Calculating similarities"):
            id1 = chat_ids[i]
            v1 = chat_embeddings[id1]
            norm1 = np.linalg.norm(v1)
            
            if norm1 == 0:
                continue
                
            for j in range(i + 1, n):
                id2 = chat_ids[j]
                v2 = chat_embeddings[id2]
                norm2 = np.linalg.norm(v2)
                
                if norm2 == 0:
                    continue
                    
                # Calculate cosine similarity
                sim = float(np.dot(v1, v2) / (norm1 * norm2))
                
                if sim >= similarity_threshold:
                    similarities.append({
                        'chat1_id': id1,
                        'chat2_id': id2,
                        'similarity': sim,
                        'hash': self._generate_content_hash({
                            'chat1_id': id1,
                            'chat2_id': id2,
                            'similarity': sim
                        })
                    })
        
        logger.info(f"✅ Found {len(similarities)} similarity relationships")
        return similarities
    
    def save_similarities(self, similarities: List[Dict]) -> None:
        """Save similarity relationships."""
        output_file = self.output_dir / "chat_similarities.jsonl"
        
        with jsonlines.open(output_file, 'w') as writer:
            for sim in similarities:
                writer.write(sim)
        
        logger.info(f"💾 Saved {len(similarities)} similarities to {output_file}")
    
    def process(self, similarity_threshold: float = 0.8, force_reprocess: bool = False) -> Dict:
        """Main processing function."""
        logger.info("🚀 Starting chat similarity calculation from pre-computed embeddings...")
        
        # Check if already processed
        if not force_reprocess:
            existing_hashes = self._get_processed_chat_hashes()
            if existing_hashes:
                logger.info(f"📋 Found {len(existing_hashes)} existing processed hashes")
                # Could implement incremental processing here
                logger.info("⏭️ Skipping (use --force to reprocess)")
                return {'status': 'skipped', 'reason': 'already_processed'}
        
        # Load pre-computed embeddings
        chat_embeddings, chat_hashes = self._load_chat_summary_embeddings()
        
        if not chat_embeddings:
            logger.error("❌ No chat summary embeddings found")
            return {'status': 'failed', 'reason': 'no_embeddings'}
        
        # Calculate similarities
        similarities = self.calculate_similarities(chat_embeddings, similarity_threshold)
        
        # Save results
        self.save_similarities(similarities)
        
        # Save hashes for tracking
        self._save_processed_chat_hashes(chat_hashes)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'chats_processed': len(chat_embeddings),
            'similarities_found': len(similarities),
            'similarity_threshold': similarity_threshold,
            'avg_similarity': np.mean([s['similarity'] for s in similarities]) if similarities else 0,
            'high_similarities': len([s for s in similarities if s['similarity'] > 0.9]),
            'medium_similarities': len([s for s in similarities if 0.7 <= s['similarity'] <= 0.9]),
            'low_similarities': len([s for s in similarities if s['similarity'] < 0.7]),
            'method': 'chat_summary_embeddings',
            'source': 'positioning_step'
        }
        
        # Save metadata
        self._save_metadata(stats)
        
        logger.info("🎉 Chat similarity calculation completed!")
        logger.info(f"  Chats processed: {stats['chats_processed']}")
        logger.info(f"  Similarities found: {stats['similarities_found']}")
        logger.info(f"  Average similarity: {stats['avg_similarity']:.3f}")
        
        return stats


@click.command()
@click.option('--embeddings-file', default='data/processed/positioning/chat_summary_embeddings.jsonl', 
              help='Input file with chat summary embeddings from positioning step')
@click.option('--similarity-threshold', default=0.8, show_default=True,
              help='Similarity threshold [0,1]')
@click.option('--force', is_flag=True, help='Force reprocess even if already done')
def main(embeddings_file: str, similarity_threshold: float, force: bool):
    """Calculate chat similarities from pre-computed chat summary embeddings."""
    
    calculator = ChatSimilarityCalculator(embeddings_file)
    stats = calculator.process(similarity_threshold, force)
    
    if stats['status'] == 'success':
        logger.info("✅ Chat similarity calculation successful!")
    else:
        logger.error(f"❌ Chat similarity calculation failed: {stats.get('reason', 'unknown')}")


if __name__ == "__main__":
    main() 