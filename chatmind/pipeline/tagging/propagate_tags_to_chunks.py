#!/usr/bin/env python3
"""
Tag Propagation Script

Propagates tags from post-processed tagged messages to chunks.
Outputs only chunk hashes with tags to avoid data duplication.
Uses modular directory structure: data/processed/tagging/
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging
from tqdm import tqdm
import hashlib
import pickle
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TagPropagator:
    """Propagates tags from post-processed messages to chunks."""
    
    def __init__(self, processed_dir: str = "data/processed"):
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.tagging_dir = self.processed_dir / "tagging"
        self.tagging_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_post_processed_tags(self, processed_tags_file: Path) -> Dict[str, Dict]:
        """Load post-processed tags indexed by message_hash."""
        processed_tags = {}
        if processed_tags_file.exists():
            with jsonlines.open(processed_tags_file) as reader:
                for tag_entry in reader:
                    message_hash = tag_entry.get('message_hash', '')
                    if message_hash:
                        processed_tags[message_hash] = tag_entry
            logger.info(f"Loaded {len(processed_tags)} post-processed tag entries")
        return processed_tags
    
    def _load_chunks(self, chunks_file: Path) -> List[Dict]:
        """Load chunks from JSONL file."""
        chunks = []
        with jsonlines.open(chunks_file) as reader:
            for chunk in reader:
                chunks.append(chunk)
        
        logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
        return chunks
    
    def _propagate_tags_to_chunk(self, chunk: Dict, processed_tags: Dict[str, Dict]) -> Optional[Dict]:
        """Propagate tags from parent message to chunk. Returns only chunk hash with tags."""
        # Get the message hash directly from the chunk
        message_hash = chunk.get('message_hash', '')
        if not message_hash:
            logger.warning(f"No message_hash found in chunk {chunk.get('chunk_id', 'unknown')}")
            return None
        
        # Find the processed tag entry using the message hash
        processed_tag_entry = processed_tags.get(message_hash)
        
        if processed_tag_entry:
            # Return only chunk hash with tags (no full chunk data)
            chunk_tag_entry = {
                'chunk_hash': chunk.get('chunk_hash', ''),
                'chunk_id': chunk.get('chunk_id', ''),
                'message_id': chunk.get('message_ids', [''])[0],
                'chat_id': chunk.get('chat_id', ''),
                'tags': processed_tag_entry.get('tags', []),
                'domain': processed_tag_entry.get('domain', 'unknown'),
                'complexity': processed_tag_entry.get('complexity', 'unknown'),
                'confidence': processed_tag_entry.get('confidence', 0.0),
                'parent_message_hash': message_hash,
                'tagged_at': datetime.now().isoformat()
            }
            return chunk_tag_entry
        else:
            # No processed tag entry found
            logger.warning(f"No processed tag entry found for chunk {chunk.get('chunk_id', 'unknown')} with message_hash {message_hash[:10]}...")
            return None
    
    def _save_chunk_tags(self, chunk_tags: List[Dict]) -> None:
        """Save chunk tags to file."""
        chunk_tags_file = self.tagging_dir / "chunk_tags.jsonl"
        with jsonlines.open(chunk_tags_file, mode='w') as writer:
            for chunk_tag in chunk_tags:
                writer.write(chunk_tag)
        
        logger.info(f"Saved {len(chunk_tags)} chunk tag entries to {chunk_tags_file}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'tag_propagation',
            'stats': stats,
            'version': '1.0'
        }
        metadata_file = self.tagging_dir / "tag_propagation_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def propagate_tags(self, processed_tags_file: Path, chunks_file: Path) -> Dict:
        """Propagate tags from post-processed tag entries to chunks."""
        logger.info("🚀 Starting tag propagation...")
        
        # Load post-processed tags
        processed_tags = self._load_post_processed_tags(processed_tags_file)
        if not processed_tags:
            logger.warning("No post-processed tag entries found")
            return {'status': 'no_processed_tags'}
        
        # Load chunks
        chunks = self._load_chunks(chunks_file)
        if not chunks:
            logger.warning("No chunks found")
            return {'status': 'no_chunks'}
        
        # Propagate tags to chunks
        chunk_tags = []
        chunks_with_tags = 0
        
        for chunk in tqdm(chunks, desc="Propagating tags"):
            chunk_tag_entry = self._propagate_tags_to_chunk(chunk, processed_tags)
            if chunk_tag_entry:
                chunk_tags.append(chunk_tag_entry)
                chunks_with_tags += 1
        
        # Save chunk tags
        self._save_chunk_tags(chunk_tags)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_chunks': len(chunks),
            'chunks_with_tags': chunks_with_tags,
            'processed_tag_entries_available': len(processed_tags),
            'tag_propagation_rate': chunks_with_tags / len(chunks) if chunks else 0
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Tag propagation completed!")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Chunks with tags: {stats['chunks_with_tags']}")
        logger.info(f"  Tag propagation rate: {stats['tag_propagation_rate']:.1%}")
        
        return stats


@click.command()
@click.option('--processed-tags-file', 
              default='data/processed/tagging/processed_tags.jsonl',
              help='Input JSONL file with post-processed tag entries')
@click.option('--chunks-file', 
              default='data/processed/chunking/chunks.jsonl',
              help='Input JSONL file with chunks')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(processed_tags_file: str, chunks_file: str, check_only: bool):
    """Propagate tags from post-processed tag entries to chunks."""
    
    if check_only:
        logger.info("🔍 Checking tag propagation setup...")
        processed_tags_path = Path(processed_tags_file)
        chunks_path = Path(chunks_file)
        
        if processed_tags_path.exists():
            logger.info(f"✅ Post-processed tags file exists: {processed_tags_path}")
        else:
            logger.error(f"❌ Post-processed tags file not found: {processed_tags_path}")
        
        if chunks_path.exists():
            logger.info(f"✅ Chunks file exists: {chunks_path}")
        else:
            logger.error(f"❌ Chunks file not found: {chunks_path}")
        
        return
    
    propagator = TagPropagator()
    stats = propagator.propagate_tags(
        processed_tags_file=Path(processed_tags_file),
        chunks_file=Path(chunks_file)
    )
    
    if stats['status'] == 'success':
        logger.info("✅ Tag propagation successful!")
    else:
        logger.error(f"❌ Tag propagation failed: {stats.get('reason', 'unknown')}")


if __name__ == "__main__":
    main() 