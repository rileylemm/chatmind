#!/usr/bin/env python3
"""
Chat Similarity Calculator

Calculates chat-level similarities by aggregating chunk embeddings and computing
cosine similarity between all chat pairs. Saves only essential data with hash tracking.
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
    """Calculate chat similarities from chunk embeddings."""
    
    def __init__(self, input_file: str = "data/processed/tagging/tagged_chunks.jsonl"):
        self.input_file = Path(input_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/similarity")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_content_hash(self, data: Dict) -> str:
        """Generate a content hash for tracking."""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _get_processed_chat_hashes(self) -> set:
        """Get hashes of already processed chats."""
        hash_file = self.output_dir / "hashes.pkl"
        if hash_file.exists():
            with open(hash_file, 'rb') as f:
                return pickle.load(f)
        return set()
    
    def _save_processed_chat_hashes(self, hashes: set) -> None:
        """Save hashes of processed chats."""
        hash_file = self.output_dir / "hashes.pkl"
        with open(hash_file, 'wb') as f:
            pickle.dump(hashes, f)
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'similarity',
            'stats': stats,
            'version': '1.0'
        }
        metadata_file = self.output_dir / "metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def aggregate_chat_embeddings(self) -> Dict[str, np.ndarray]:
        """Aggregate chunk embeddings per chat."""
        logger.info("📊 Aggregating embeddings per chat...")
        
        chat_sums = {}
        chat_counts = {}
        chat_hashes = set()
        
        with jsonlines.open(self.input_file) as reader:
            for chunk in tqdm(reader, desc="Processing chunks"):
                emb = chunk.get('embedding')
                if emb is None:
                    continue
                    
                chat_id = chunk['chat_id']
                vec = np.array(emb, dtype=float)
                
                if chat_id in chat_sums:
                    chat_sums[chat_id] += vec
                    chat_counts[chat_id] += 1
                else:
                    chat_sums[chat_id] = vec.copy()
                    chat_counts[chat_id] = 1
                
                # Generate hash for this chunk
                chunk_hash = self._generate_content_hash({
                    'chat_id': chat_id,
                    'embedding': emb,
                    'chunk_id': chunk.get('chunk_id', '')
                })
                chat_hashes.add(chunk_hash)
        
        # Compute averages
        chat_embeddings = {}
        for chat_id in chat_sums:
            if chat_counts[chat_id] > 0:
                chat_embeddings[chat_id] = chat_sums[chat_id] / chat_counts[chat_id]
        
        logger.info(f"✅ Aggregated embeddings for {len(chat_embeddings)} chats")
        return chat_embeddings, chat_hashes
    
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
    
    def save_chat_embeddings(self, chat_embeddings: Dict[str, np.ndarray]) -> None:
        """Save aggregated chat embeddings."""
        output_file = self.output_dir / "chat_embeddings.jsonl"
        
        with jsonlines.open(output_file, 'w') as writer:
            for chat_id, embedding in chat_embeddings.items():
                writer.write({
                    'chat_id': chat_id,
                    'embedding': embedding.tolist(),
                    'hash': self._generate_content_hash({
                        'chat_id': chat_id,
                        'embedding': embedding.tolist()
                    })
                })
        
        logger.info(f"💾 Saved chat embeddings to {output_file}")
    
    def save_similarities(self, similarities: List[Dict]) -> None:
        """Save similarity relationships."""
        output_file = self.output_dir / "chat_similarities.jsonl"
        
        with jsonlines.open(output_file, 'w') as writer:
            for sim in similarities:
                writer.write(sim)
        
        logger.info(f"💾 Saved {len(similarities)} similarities to {output_file}")
    
    def process(self, similarity_threshold: float = 0.8, force_reprocess: bool = False) -> Dict:
        """Main processing function."""
        logger.info("🚀 Starting chat similarity calculation...")
        
        # Check if already processed
        if not force_reprocess:
            existing_hashes = self._get_processed_chat_hashes()
            if existing_hashes:
                logger.info(f"📋 Found {len(existing_hashes)} existing processed hashes")
                # Could implement incremental processing here
                logger.info("⏭️ Skipping (use --force to reprocess)")
                return {'status': 'skipped', 'reason': 'already_processed'}
        
        # Aggregate embeddings
        chat_embeddings, chat_hashes = self.aggregate_chat_embeddings()
        
        if not chat_embeddings:
            logger.warning("❌ No valid embeddings found")
            return {'status': 'failed', 'reason': 'no_embeddings'}
        
        # Calculate similarities
        similarities = self.calculate_similarities(chat_embeddings, similarity_threshold)
        
        # Save results
        self.save_chat_embeddings(chat_embeddings)
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
            'low_similarities': len([s for s in similarities if s['similarity'] < 0.7])
        }
        
        # Save metadata
        self._save_metadata(stats)
        
        logger.info("🎉 Chat similarity calculation completed!")
        logger.info(f"  Chats processed: {stats['chats_processed']}")
        logger.info(f"  Similarities found: {stats['similarities_found']}")
        logger.info(f"  Average similarity: {stats['avg_similarity']:.3f}")
        
        return stats


@click.command()
@click.option('--input-file', default='data/processed/tagging/tagged_chunks.jsonl', 
              help='Input file with tagged chunks')
@click.option('--similarity-threshold', default=0.8, show_default=True,
              help='Similarity threshold [0,1]')
@click.option('--force', is_flag=True, help='Force reprocess even if already done')
def main(input_file: str, similarity_threshold: float, force: bool):
    """Calculate chat similarities from chunk embeddings."""
    
    calculator = ChatSimilarityCalculator(input_file)
    stats = calculator.process(similarity_threshold, force)
    
    if stats['status'] == 'success':
        logger.info("✅ Chat similarity calculation successful!")
    else:
        logger.error(f"❌ Chat similarity calculation failed: {stats.get('reason', 'unknown')}")


if __name__ == "__main__":
    main() 