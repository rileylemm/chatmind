#!/usr/bin/env python3
"""
Direct Incremental Chunk Embedding

Embeds chunks using local Sentence Transformers models.
Uses modular directory structure: data/processed/embedding/
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

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("Sentence Transformers not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DirectIncrementalChunkEmbedder:
    """Embeds chunks using local models."""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 processed_dir: str = "data/processed"):
        self.model = SentenceTransformer(model_name)
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.embedding_dir = self.processed_dir / "embedding"
        self.embedding_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_chunk_hash(self, chunk: Dict) -> str:
        """Generate a hash for a chunk to track if it's been processed."""
        # Create a normalized version for hashing
        normalized_chunk = {
            'content': chunk.get('content', ''),
            'chat_id': chunk.get('chat_id', ''),
            'chunk_id': chunk.get('chunk_id', ''),
            'message_ids': chunk.get('message_ids', [])
        }
        content = json.dumps(normalized_chunk, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
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
    
    def _generate_embedding_hash(self, embedding: List[float]) -> str:
        """Generate a hash for an embedding vector."""
        # Convert embedding to bytes for hashing
        embedding_bytes = json.dumps(embedding, sort_keys=True).encode()
        return hashlib.sha256(embedding_bytes).hexdigest()
    
    def _embed_chunks(self, chunks: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """Generate embeddings for chunks."""
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
        
        # Generate embeddings
        embeddings = self.model.encode(contents, show_progress_bar=True)
        
        # Add embeddings to chunks
        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_with_embedding = chunk.copy()
            embedding_vector = embeddings[i].tolist()
            chunk_with_embedding['embedding'] = embedding_vector
            chunk_with_embedding['embedding_hash'] = self._generate_embedding_hash(embedding_vector)
            embedded_chunks.append(chunk_with_embedding)
        
        logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
        return embeddings, embedded_chunks
    
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
        logger.info("🚀 Starting chunk embedding...")
        
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
        new_embeddings, embedded_new_chunks = self._embed_chunks(new_chunks)
        
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
            'embedding_dimension': len(new_embeddings[0]) if len(new_embeddings) > 0 else 0
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Chunk embedding completed!")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        logger.info(f"  New chunks: {stats['new_chunks']}")
        logger.info(f"  Embedding dimension: {stats['embedding_dimension']}")
        
        return stats


if __name__ == "__main__":
    import click
    @click.command()
    @click.option('--chunks-file',
                  default='data/processed/chunking/chunks.jsonl',
                  help='Input JSONL file with chunks')
    @click.option('--state-file',
                  default='data/processed/embedding/hashes.pkl',
                  help='State file for tracking processed chunks')
    @click.option('--model', default='all-MiniLM-L6-v2', help='Sentence transformer model to use')
    @click.option('--force', is_flag=True, help='Force reprocess all chunks (ignore state)')
    def main(chunks_file: str, state_file: str, model: str, force: bool):
        """Run chunk embedding pipeline."""
        
        embedder = DirectIncrementalChunkEmbedder(model_name=model)
        
        result = embedder.process_chunks_to_embeddings(
            chunks_file=Path(chunks_file),
            state_file=Path(state_file),
            force_reprocess=force
        )
        
        if result['status'] == 'success':
            logger.info(f"✅ Embedding completed successfully!")
            logger.info(f"   Total chunks: {result['total_chunks']}")
            logger.info(f"   New chunks: {result['new_chunks']}")
        else:
            logger.info(f"ℹ️ Embedding status: {result['status']}")

    main() 