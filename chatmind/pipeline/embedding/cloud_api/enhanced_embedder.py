#!/usr/bin/env python3
"""
Cloud API Embedding

Uses OpenAI embeddings for higher quality semantic understanding.
Processes chunks into embeddings only (clustering is separate step).
Uses modular directory structure: data/processed/embedding/
"""

import json
import jsonlines
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import click
from tqdm import tqdm
import logging
import pickle
import hashlib
import time
import os
from openai import OpenAI

# Import pipeline configuration
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import get_openai_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudChunkEmbedder:
    """Embeds chunks using OpenAI embeddings."""
    
    def __init__(self, 
                 model_name: str = "text-embedding-3-small",
                 processed_dir: str = "data/processed",
                 max_retries: int = 3,
                 delay_between_calls: float = 0.1):
        self.model_name = model_name
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.embedding_dir = self.processed_dir / "embedding"
        self.embedding_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        self.stats = {
            'chunks_processed': 0,
            'api_calls': 0,
            'errors': 0,
            'total_tokens': 0
        }
        
        # Initialize OpenAI client (reads OPENAI_API_KEY from environment)
        self.client = OpenAI()
        
    def _generate_chunk_hash(self, chunk: Dict) -> str:
        """Generate a hash for a chunk to track if it's been processed."""
        normalized_chunk = {
            'content': chunk.get('content', ''),
            'chat_id': chunk.get('chat_id', ''),
            'chunk_id': chunk.get('chunk_id', ''),
            'message_ids': chunk.get('message_ids', [])
        }
        content = json.dumps(normalized_chunk, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _generate_embedding_hash(self, embedding: List[float]) -> str:
        """Generate a hash for an embedding vector."""
        embedding_bytes = json.dumps(embedding, sort_keys=True).encode()
        return hashlib.sha256(embedding_bytes).hexdigest()
    
    def _load_processed_chunk_hashes(self, state_file: Path) -> Set[str]:
        """Load hashes of chunks that have already been embedded."""
        if state_file.exists():
            try:
                with open(state_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed chunk hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def _save_processed_chunk_hashes(self, hashes: Set[str], state_file: Path) -> None:
        """Save hashes of processed chunks."""
        try:
            with open(state_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed chunk hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _load_existing_embeddings(self, embeddings_file: Path) -> List[Dict]:
        """Load existing embeddings from file."""
        embeddings = []
        if embeddings_file.exists():
            with jsonlines.open(embeddings_file) as reader:
                for embedding in reader:
                    embeddings.append(embedding)
            logger.info(f"Loaded {len(embeddings)} existing embeddings")
        return embeddings
    
    def _load_chunks(self, chunks_file: Path) -> List[Dict]:
        """Load chunks from JSONL file."""
        chunks = []
        with jsonlines.open(chunks_file) as reader:
            for chunk in reader:
                chunks.append(chunk)
        
        logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
        return chunks
    
    def _identify_new_chunks(self, all_chunks: List[Dict], processed_hashes: Set[str]) -> List[Dict]:
        """Identify chunks that haven't been embedded yet."""
        new_chunks = []
        for chunk in all_chunks:
            chunk_hash = self._generate_chunk_hash(chunk)
            if chunk_hash not in processed_hashes:
                new_chunks.append(chunk)
        
        logger.info(f"Found {len(new_chunks)} new chunks out of {len(all_chunks)} total")
        return new_chunks
    
    def _embed_chunks_with_openai(self, chunks: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """Generate embeddings for chunks using OpenAI API."""
        if not chunks:
            return np.array([]), []
        
        # Extract content for embedding
        contents = []
        for chunk in chunks:
            content = chunk.get('content', '').strip()
            if content:
                contents.append(content)
            else:
                contents.append("")  # Empty content for chunks without text
        
        # Generate embeddings with retry logic
        embeddings = []
        embedded_chunks = []
        
        for i, chunk in enumerate(tqdm(chunks, desc="Embedding chunks")):
            content = contents[i]
            
            # Skip empty content
            if not content.strip():
                # Create zero embedding for empty content
                embedding_vector = [0.0] * 1536  # OpenAI embedding dimension
                chunk_with_embedding = chunk.copy()
                chunk_with_embedding['embedding'] = embedding_vector
                chunk_with_embedding['embedding_hash'] = self._generate_embedding_hash(embedding_vector)
                embedded_chunks.append(chunk_with_embedding)
                embeddings.append(embedding_vector)
                continue
            
            # Retry logic for API calls
            for attempt in range(self.max_retries):
                try:
                    response = self.client.embeddings.create(
                        input=content,
                        model=self.model_name
                    )
                    
                    embedding_vector = response.data[0].embedding
                    chunk_with_embedding = chunk.copy()
                    chunk_with_embedding['embedding'] = embedding_vector
                    chunk_with_embedding['embedding_hash'] = self._generate_embedding_hash(embedding_vector)
                    
                    embedded_chunks.append(chunk_with_embedding)
                    embeddings.append(embedding_vector)
                    
                    self.stats['api_calls'] += 1
                    # Embeddings responses may omit usage; handle safely
                    try:
                        self.stats['total_tokens'] += getattr(response, 'usage', {}).get('total_tokens', 0)  # type: ignore
                    except Exception:
                        pass
                    
                    # Add delay between calls
                    time.sleep(self.delay_between_calls)
                    break
                    
                except Exception as e:
                    logger.warning(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                    if attempt == self.max_retries - 1:
                        logger.error(f"Failed to embed chunk {chunk.get('chunk_id', 'unknown')} after {self.max_retries} attempts")
                        self.stats['errors'] += 1
                        # Create zero embedding for failed chunk
                        embedding_vector = [0.0] * 1536
                        chunk_with_embedding = chunk.copy()
                        chunk_with_embedding['embedding'] = embedding_vector
                        chunk_with_embedding['embedding_hash'] = self._generate_embedding_hash(embedding_vector)
                        embedded_chunks.append(chunk_with_embedding)
                        embeddings.append(embedding_vector)
                    else:
                        time.sleep(self.delay_between_calls * (attempt + 1))  # Exponential backoff
        
        logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
        return np.array(embeddings), embedded_chunks
    
    def _save_embeddings(self, chunks: List[Dict]) -> None:
        """Save embeddings to file."""
        embeddings_file = self.embedding_dir / "embeddings.jsonl"
        with jsonlines.open(embeddings_file, mode='w') as writer:
            for chunk in chunks:
                writer.write(chunk)
        
        logger.info(f"Saved {len(chunks)} embeddings to {embeddings_file}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'embedding',
            'stats': stats,
            'version': '1.0'
        }
        metadata_file = self.embedding_dir / "metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def process_chunks_to_embeddings(self, chunks_file: Path, state_file: Path, force_reprocess: bool = False) -> Dict:
        """Process chunks into embeddings."""
        logger.info("🚀 Starting cloud chunk embedding...")
        
        # Load existing embeddings
        embeddings_file = self.embedding_dir / "embeddings.jsonl"
        existing_embeddings = self._load_existing_embeddings(embeddings_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_chunk_hashes(state_file)
            logger.info(f"Found {len(processed_hashes)} existing processed hashes")
        
        # Load chunks
        all_chunks = self._load_chunks(chunks_file)
        if not all_chunks:
            logger.warning("No chunks found")
            return {'status': 'no_chunks'}
        
        # Identify new chunks
        new_chunks = self._identify_new_chunks(all_chunks, processed_hashes)
        
        if not new_chunks and not force_reprocess:
            logger.info("No new chunks to process")
            return {'status': 'no_new_chunks'}
        
        # Embed new chunks
        new_embeddings, embedded_new_chunks = self._embed_chunks_with_openai(new_chunks)
        
        if len(new_embeddings) == 0:
            logger.info("No new embeddings generated")
            return {'status': 'no_embeddings'}
        
        # Combine existing and new embeddings
        all_embedded_chunks = existing_embeddings + embedded_new_chunks
        
        # Update processed hashes
        for chunk in new_chunks:
            chunk_hash = self._generate_chunk_hash(chunk)
            processed_hashes.add(chunk_hash)
        
        # Save results
        self._save_embeddings(all_embedded_chunks)
        self._save_processed_chunk_hashes(processed_hashes, state_file)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_chunks': len(all_embedded_chunks),
            'new_chunks': len(new_chunks),
            'existing_chunks': len(existing_embeddings),
            'embedding_dimension': len(new_embeddings[0]) if len(new_embeddings) > 0 else 0,
            'api_calls': self.stats['api_calls'],
            'errors': self.stats['errors'],
            'total_tokens': self.stats['total_tokens']
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Cloud chunk embedding completed!")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  New chunks: {stats['new_chunks']}")
        
        return stats


@click.command()
@click.option('--chunks-file', required=True, help='Path to chunks JSONL file')
@click.option('--state-file', required=True, help='Path to state file for tracking progress')
@click.option('--force', is_flag=True, help='Force reprocess all chunks')
@click.option('--model', default='text-embedding-3-small', help='OpenAI embedding model to use')
def main(chunks_file: str, state_file: str, force: bool, model: str):
    """Run cloud embedding on chunks."""
    # Load OpenAI config
    openai_config = get_openai_config()
    if not openai_config['api_key']:
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        return
    
    # Set environment variable so OpenAI client can pick it up
    os.environ['OPENAI_API_KEY'] = openai_config['api_key']
    
    # Initialize embedder
    embedder = CloudChunkEmbedder(model_name=model)
    
    # Process chunks
    result = embedder.process_chunks_to_embeddings(
        chunks_file=Path(chunks_file),
        state_file=Path(state_file),
        force_reprocess=force
    )
    
    if result['status'] == 'success':
        logger.info("✅ Cloud embedding completed successfully!")
    else:
        logger.info(f"ℹ️ Cloud embedding status: {result['status']}")


if __name__ == "__main__":
    main() 