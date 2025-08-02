#!/usr/bin/env python3
"""
ChatMind Chunking Step

Takes chats from ingestion and creates semantic chunks.
This step is separate from embedding to allow for different chunking strategies.
Uses modular directory structure: data/processed/chunking/
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
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatChunker:
    """Creates semantic chunks from chat messages."""
    
    def __init__(self, input_file: str = "data/processed/ingestion/chats.jsonl"):
        self.input_file = Path(input_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/chunking")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_chunk_hash(self, chunk: Dict) -> str:
        """Generate a hash for a chunk to track if it's been processed."""
        content_str = json.dumps(chunk, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _generate_message_hash(self, message: Dict) -> str:
        """Generate a hash for a message that matches the tagging step's hash generation."""
        # Create a normalized version for hashing that matches the tagging step
        normalized_message = {
            'content': message.get('content', ''),
            'chat_id': message.get('chat_id', ''),
            'message_id': message.get('id', ''),
            'role': message.get('role', '')
        }
        content = json.dumps(normalized_message, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_chunk_hashes(self) -> Set[str]:
        """Load hashes of chunks that have already been processed."""
        hash_file = self.output_dir / "hashes.pkl"
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed chunk hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def _save_processed_chunk_hashes(self, hashes: Set[str]) -> None:
        """Save hashes of processed chunks."""
        hash_file = self.output_dir / "hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed chunk hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'chunking',
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
    
    def _load_existing_chunks(self, chunks_file: Path) -> List[Dict]:
        """Load existing chunks from output file."""
        chunks = []
        if chunks_file.exists():
            with jsonlines.open(chunks_file) as reader:
                for chunk in reader:
                    chunks.append(chunk)
            logger.info(f"Loaded {len(chunks)} existing chunks")
        return chunks
    
    def _load_chats(self, chats_file: Path) -> List[Dict]:
        """Load chats from JSONL file."""
        chats = []
        with jsonlines.open(chats_file) as reader:
            for chat in reader:
                chats.append(chat)
        
        logger.info(f"Loaded {len(chats)} chats from {chats_file}")
        return chats
    
    def _create_semantic_chunks(self, messages: List[Dict], chat_id: str) -> List[Dict]:
        """Create semantic chunks from messages using simple text segmentation."""
        chunks = []
        
        # Use simple character-based estimation for chunking
        # This avoids loading heavy embedding models in the chunking step
        max_chars = 2000  # Conservative character limit for chunks
        
        def count_chars(text: str) -> int:
            """Count characters in text."""
            return len(text)
        
        def split_message_into_chunks(message: Dict, message_index: int) -> List[Dict]:
            """Split a single message into chunks if it's too long."""
            content = message.get('content', '')
            
            # Skip non-user/assistant messages
            if message.get('role') not in ['user', 'assistant']:
                return []
            
            message_chars = count_chars(content)
            
            # Generate message hash that matches tagging step
            # Add chat_id to message for hash generation
            message_with_chat_id = {
                **message,
                'chat_id': chat_id
            }
            message_hash = self._generate_message_hash(message_with_chat_id)
            
            # If message fits in one chunk, return it as is
            if message_chars <= max_chars:
                chunk = {
                    'chunk_id': f"{chat_id}_msg_{message_index}_chunk_0",
                    'chat_id': chat_id,
                    'message_id': message.get('id', ''),
                    'content': content,
                    'message_ids': [message.get('id', '')],
                    'role': message.get('role'),
                    'char_count': message_chars,
                    'message_hash': message_hash,  # Add message hash
                    'chunk_hash': self._generate_chunk_hash({
                        'content': content,
                        'chat_id': chat_id,
                        'message_ids': [message.get('id', '')],
                        'role': message.get('role')
                    })
                }
                return [chunk]
            
            # If message is too long, split it into chunks
            # Simple splitting by sentences or paragraphs
            import re
            
            # Split by sentences first (more semantic)
            sentences = re.split(r'[.!?]+', content)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                # Fallback to character-based splitting
                sentences = [content[i:i+max_chars] for i in range(0, len(content), max_chars)]
            
            message_chunks = []
            current_chunk_content = ""
            current_chunk_chars = 0
            chunk_index = 0
            
            for sentence in sentences:
                sentence_chars = count_chars(sentence)
                
                # If adding this sentence would exceed the limit, start a new chunk
                if current_chunk_chars + sentence_chars > max_chars and current_chunk_content:
                    # Save current chunk
                    chunk = {
                        'chunk_id': f"{chat_id}_msg_{message_index}_chunk_{chunk_index}",
                        'chat_id': chat_id,
                        'message_id': message.get('id', ''),
                        'content': current_chunk_content.strip(),
                        'message_ids': [message.get('id', '')],
                        'role': message.get('role'),
                        'char_count': current_chunk_chars,
                        'message_hash': message_hash, # Add message hash to chunk
                        'chunk_hash': self._generate_chunk_hash({
                            'content': current_chunk_content.strip(),
                            'chat_id': chat_id,
                            'message_ids': [message.get('id', '')],
                            'role': message.get('role')
                        })
                    }
                    message_chunks.append(chunk)
                    
                    # Start new chunk
                    current_chunk_content = sentence
                    current_chunk_chars = sentence_chars
                    chunk_index += 1
                else:
                    # Add to current chunk
                    if current_chunk_content:
                        current_chunk_content += ". " + sentence
                    else:
                        current_chunk_content = sentence
                    current_chunk_chars += sentence_chars
            
            # Don't forget the last chunk
            if current_chunk_content:
                chunk = {
                    'chunk_id': f"{chat_id}_msg_{message_index}_chunk_{chunk_index}",
                    'chat_id': chat_id,
                    'message_id': message.get('id', ''),
                    'content': current_chunk_content.strip(),
                    'message_ids': [message.get('id', '')],
                    'role': message.get('role'),
                    'char_count': current_chunk_chars,
                    'message_hash': message_hash, # Add message hash to chunk
                    'chunk_hash': self._generate_chunk_hash({
                        'content': current_chunk_content.strip(),
                        'chat_id': chat_id,
                        'message_ids': [message.get('id', '')],
                        'role': message.get('role')
                    })
                }
                message_chunks.append(chunk)
            
            return message_chunks
        
        # Process each message individually
        for i, message in enumerate(messages):
            message_chunks = split_message_into_chunks(message, i)
            chunks.extend(message_chunks)
        
        return chunks
    
    def process_chats_to_chunks(self, force_reprocess: bool = False) -> Dict:
        """Process chats into semantic chunks."""
        logger.info("🚀 Starting chat chunking...")
        
        # Load existing chunks
        chunks_file = self.output_dir / "chunks.jsonl"
        existing_chunks = self._load_existing_chunks(chunks_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_chunk_hashes()
            logger.info(f"Found {len(processed_hashes)} existing processed hashes")
        
        # Load chats
        chats = self._load_chats(self.input_file)
        if not chats:
            logger.warning("No chats found")
            return {'status': 'no_chats'}
        
        # Process each chat
        all_chunks = existing_chunks.copy()
        new_chunks = []
        total_chats = len(chats)
        
        for i, chat in enumerate(tqdm(chats, desc="Processing chats")):
            chat_id = chat.get('content_hash', f"chat_{i}")
            messages = chat.get('messages', [])
            
            # Create chunks for this chat
            chat_chunks = self._create_semantic_chunks(messages, chat_id)
            
            # Check which chunks are new
            for chunk in chat_chunks:
                chunk_hash = chunk['chunk_hash']
                if chunk_hash not in processed_hashes or force_reprocess:
                    new_chunks.append(chunk)
                    processed_hashes.add(chunk_hash)
        
        if not new_chunks and not force_reprocess:
            logger.info("No new chunks to process")
            return {'status': 'no_new_chunks'}
        
        # Save new chunks
        with jsonlines.open(chunks_file, mode='w') as writer:
            for chunk in all_chunks + new_chunks:
                writer.write(chunk)
        
        # Save hashes and metadata
        self._save_processed_chunk_hashes(processed_hashes)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_chats': total_chats,
            'total_chunks': len(all_chunks + new_chunks),
            'new_chunks': len(new_chunks),
            'existing_chunks': len(existing_chunks),
            'avg_chunks_per_chat': len(all_chunks + new_chunks) / total_chats if total_chats > 0 else 0
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Chat chunking completed!")
        logger.info(f"  Total chats: {stats['total_chats']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  New chunks: {stats['new_chunks']}")
        logger.info(f"  Avg chunks per chat: {stats['avg_chunks_per_chat']:.2f}")
        
        return stats


@click.command()
@click.option('--input-file', 
              default='data/processed/ingestion/chats.jsonl',
              help='Input chats file')
@click.option('--force', is_flag=True, help='Force reprocess all chats')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(input_file: str, force: bool, check_only: bool):
    """Create semantic chunks from chats."""
    
    if check_only:
        logger.info("🔍 Checking chunking setup...")
        input_path = Path(input_file)
        if input_path.exists():
            logger.info(f"✅ Input file exists: {input_path}")
        else:
            logger.error(f"❌ Input file not found: {input_path}")
        return
    
    chunker = ChatChunker(input_file)
    stats = chunker.process_chats_to_chunks(force_reprocess=force)
    
    if stats['status'] == 'success':
        logger.info("✅ Chunking successful!")
    else:
        logger.error(f"❌ Chunking failed: {stats.get('reason', 'unknown')}")


if __name__ == "__main__":
    main() 