#!/usr/bin/env python3
"""
Tag Propagation Script

Propagates tags from tagged messages to chunks.
This ensures chunks inherit tags from their parent messages.
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
    """Propagates tags from messages to chunks."""
    
    def __init__(self, processed_dir: str = "data/processed"):
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.tagging_dir = self.processed_dir / "tagging"
        self.tagging_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_tagged_messages(self, tagged_messages_file: Path) -> Dict[str, Dict]:
        """Load tagged messages indexed by message_id."""
        tagged_messages = {}
        if tagged_messages_file.exists():
            with jsonlines.open(tagged_messages_file) as reader:
                for message in reader:
                    message_id = message.get('message_id', '')
                    if message_id:
                        tagged_messages[message_id] = message
            logger.info(f"Loaded {len(tagged_messages)} tagged messages")
        return tagged_messages
    
    def _load_chunks(self, chunks_file: Path) -> List[Dict]:
        """Load chunks from JSONL file."""
        chunks = []
        with jsonlines.open(chunks_file) as reader:
            for chunk in reader:
                chunks.append(chunk)
        
        logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
        return chunks
    
    def _load_tag_entries(self, tags_file: Path) -> Dict[str, Dict]:
        """Load tag entries indexed by message_hash."""
        tag_entries = {}
        if tags_file.exists():
            with jsonlines.open(tags_file) as reader:
                for tag_entry in reader:
                    message_hash = tag_entry.get('message_hash', '')
                    if message_hash:
                        tag_entries[message_hash] = tag_entry
            logger.info(f"Loaded {len(tag_entries)} tag entries")
        return tag_entries
    
    def _propagate_tags_to_chunk(self, chunk: Dict, tag_entries: Dict[str, Dict]) -> Dict:
        """Propagate tags from parent message to chunk."""
        # Get the message ID from the chunk
        message_ids = chunk.get('message_ids', [])
        if not message_ids:
            return chunk
        
        # Use the first message ID (chunks should only have one message ID now)
        message_id = message_ids[0]
        
        # Generate message hash to find the tag entry
        # We need to reconstruct the message hash from the chunk data
        message_data = {
            'content': chunk.get('content', ''),
            'chat_id': chunk.get('chat_id', ''),
            'id': message_id,
            'role': chunk.get('role', '')
        }
        message_hash = hashlib.sha256(json.dumps(message_data, sort_keys=True).encode()).hexdigest()
        
        # Find the tag entry
        tag_entry = tag_entries.get(message_hash)
        
        if tag_entry:
            # Propagate tags to chunk
            tagged_chunk = {
                **chunk,
                'tags': tag_entry.get('tags', []),
                'topics': tag_entry.get('topics', []),
                'domain': tag_entry.get('domain', 'other'),
                'complexity': tag_entry.get('complexity', 'medium'),
                'sentiment': tag_entry.get('sentiment', 'neutral'),
                'intent': tag_entry.get('intent', 'other'),
                'parent_message_hash': message_hash,
                'tagged_at': tag_entry.get('tagged_at', datetime.now().isoformat())
            }
            return tagged_chunk
        else:
            # No tag entry found, keep chunk as is
            logger.warning(f"No tag entry found for chunk {chunk.get('chunk_id', 'unknown')}")
            return chunk
    
    def _save_tagged_chunks(self, tagged_chunks: List[Dict]) -> None:
        """Save tagged chunks to file."""
        tagged_chunks_file = self.tagging_dir / "tagged_chunks.jsonl"
        with jsonlines.open(tagged_chunks_file, mode='w') as writer:
            for chunk in tagged_chunks:
                writer.write(chunk)
        
        logger.info(f"Saved {len(tagged_chunks)} tagged chunks to {tagged_chunks_file}")
    
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
    
    def propagate_tags(self, tags_file: Path, chunks_file: Path) -> Dict:
        """Propagate tags from tag entries to chunks."""
        logger.info("🚀 Starting tag propagation...")
        
        # Load tag entries
        tag_entries = self._load_tag_entries(tags_file)
        if not tag_entries:
            logger.warning("No tag entries found")
            return {'status': 'no_tag_entries'}
        
        # Load chunks
        chunks = self._load_chunks(chunks_file)
        if not chunks:
            logger.warning("No chunks found")
            return {'status': 'no_chunks'}
        
        # Propagate tags to chunks
        tagged_chunks = []
        chunks_with_tags = 0
        
        for chunk in tqdm(chunks, desc="Propagating tags"):
            tagged_chunk = self._propagate_tags_to_chunk(chunk, tag_entries)
            tagged_chunks.append(tagged_chunk)
            
            # Count chunks that got tags
            if tagged_chunk.get('tags'):
                chunks_with_tags += 1
        
        # Save tagged chunks
        self._save_tagged_chunks(tagged_chunks)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_chunks': len(tagged_chunks),
            'chunks_with_tags': chunks_with_tags,
            'tag_entries_available': len(tag_entries),
            'tag_propagation_rate': chunks_with_tags / len(tagged_chunks) if tagged_chunks else 0
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Tag propagation completed!")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  Chunks with tags: {stats['chunks_with_tags']}")
        logger.info(f"  Tag propagation rate: {stats['tag_propagation_rate']:.1%}")
        
        return stats


@click.command()
@click.option('--tags-file', 
              default='data/processed/tagging/tags.jsonl',
              help='Input JSONL file with tag entries')
@click.option('--chunks-file', 
              default='data/processed/chunking/chunks.jsonl',
              help='Input JSONL file with chunks')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(tags_file: str, chunks_file: str, check_only: bool):
    """Propagate tags from tag entries to chunks."""
    
    if check_only:
        logger.info("🔍 Checking tag propagation setup...")
        tags_path = Path(tags_file)
        chunks_path = Path(chunks_file)
        
        if tags_path.exists():
            logger.info(f"✅ Tags file exists: {tags_path}")
        else:
            logger.error(f"❌ Tags file not found: {tags_path}")
        
        if chunks_path.exists():
            logger.info(f"✅ Chunks file exists: {chunks_path}")
        else:
            logger.error(f"❌ Chunks file not found: {chunks_path}")
        
        return
    
    propagator = TagPropagator()
    stats = propagator.propagate_tags(
        tags_file=Path(tags_file),
        chunks_file=Path(chunks_file)
    )
    
    if stats['status'] == 'success':
        logger.info("✅ Tag propagation successful!")
    else:
        logger.error(f"❌ Tag propagation failed: {stats.get('reason', 'unknown')}")


if __name__ == "__main__":
    main() 