#!/usr/bin/env python3
"""
Direct Incremental Embedding and Clustering Pipeline

Processes NEW messages from chats.jsonl into embeddings, clusters them semantically,
and merges with existing clustering results. Skips semantic chunking entirely.
"""

import json
import jsonlines
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import click
from tqdm import tqdm
import logging
import pickle
import hashlib

# ML imports
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import HDBSCAN
    from sklearn.manifold import TSNE
    import umap
except ImportError as e:
    logger.error(f"Missing ML dependencies: {e}")
    logger.error("Install with: pip install sentence-transformers scikit-learn umap-learn")
    raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DirectIncrementalChatEmbedder:
    """Embeds and clusters NEW chat messages incrementally, skipping semantic chunking."""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 processed_dir: str = "data/processed",
                 embeddings_dir: str = "data/embeddings"):
        self.model = SentenceTransformer(model_name)
        self.processed_dir = Path(processed_dir)
        self.embeddings_dir = Path(embeddings_dir)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_message_hash(self, message: Dict) -> str:
        """Generate a hash for a message to track if it's been processed."""
        # Create a normalized version for hashing that matches existing chunk format
        normalized_message = {
            'content': message.get('content', ''),
            'chat_id': message.get('chat_id', ''),
            'message_id': message.get('message_id', ''),  # This will be constructed from chat_id + id
            'role': message.get('role', ''),
            'timestamp': message.get('timestamp')
        }
        content = json.dumps(normalized_message, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def load_processed_message_hashes(self, state_file: Path) -> Set[str]:
        """Load hashes of messages that have already been processed."""
        if state_file.exists():
            try:
                with open(state_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed message hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def save_processed_message_hashes(self, hashes: Set[str], state_file: Path) -> None:
        """Save hashes of processed messages."""
        try:
            with open(state_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed message hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def load_existing_chunks(self, chunks_file: Path) -> List[Dict]:
        """Load existing chunks with embeddings and cluster info."""
        chunks = []
        if chunks_file.exists():
            with jsonlines.open(chunks_file) as reader:
                for chunk in reader:
                    chunks.append(chunk)
            logger.info(f"Loaded {len(chunks)} existing chunks")
        return chunks
    
    def load_messages_from_chats(self, chats_file: Path) -> List[Dict]:
        """Load individual messages from chats.jsonl."""
        messages = []
        if chats_file.exists():
            with jsonlines.open(chats_file) as reader:
                for chat in reader:
                    chat_id = chat.get('content_hash', 'unknown')
                    # Extract individual messages from each chat
                    for message in chat.get('messages', []):
                        # Only process user and assistant messages with content
                        if message.get('role') in ['user', 'assistant'] and message.get('content', '').strip():
                            # Normalize message format to match existing chunks
                            message_id = f"{chat_id}_{message.get('id', 'unknown')}"
                            message_with_metadata = {
                                'message_id': message_id,
                                'chat_id': chat_id,
                                'chat_title': chat.get('title', 'Untitled'),
                                'role': message.get('role', ''),
                                'content': message.get('content', ''),
                                'timestamp': message.get('timestamp'),
                                'parent_id': message.get('parent_id'),
                                'create_time': chat.get('create_time'),
                                'source_file': chat.get('source_file', '')
                            }
                            messages.append(message_with_metadata)
            logger.info(f"Loaded {len(messages)} messages from {chats_file}")
        return messages
    
    def identify_new_messages(self, all_messages: List[Dict], processed_hashes: Set[str]) -> List[Dict]:
        """Identify messages that haven't been processed yet."""
        new_messages = []
        for message in all_messages:
            message_hash = self.generate_message_hash(message)
            if message_hash not in processed_hashes:
                new_messages.append(message)
        
        logger.info(f"Found {len(new_messages)} new messages out of {len(all_messages)} total")
        return new_messages
    
    def embed_messages(self, messages: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """Generate embeddings for messages."""
        if not messages:
            return np.array([]), []
        
        # Extract and preprocess content for embedding
        processed_messages = []
        contents = []
        
        for message in messages:
            content = message.get('content', '')
            
            # Handle long content (sentence-transformers typically handles 512 tokens)
            # For very long messages, we'll truncate to first 2000 characters
            # This is a rough approximation - actual token count may vary
            if len(content) > 2000:
                logger.warning(f"Truncating long message (length: {len(content)})")
                content = content[:2000] + "... [truncated]"
            
            # Skip empty content
            if not content.strip():
                continue
                
            processed_messages.append(message)
            contents.append(content)
        
        if not contents:
            logger.warning("No valid content found for embedding")
            return np.array([]), []
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(contents)} messages...")
        embeddings = self.model.encode(contents, show_progress_bar=True)
        
        # Add embeddings to messages
        embedded_messages = []
        for i, message in enumerate(processed_messages):
            message_with_embedding = {
                **message,
                'embedding': embeddings[i].tolist(),
                'content_length': len(message.get('content', '')),
                'content_truncated': len(message.get('content', '')) > 2000
            }
            embedded_messages.append(message_with_embedding)
        
        return embeddings, embedded_messages
    
    def cluster_embeddings_incremental(self, 
                                     new_embeddings: np.ndarray,
                                     existing_embeddings: np.ndarray,
                                     min_cluster_size: int = 5,
                                     min_samples: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Cluster embeddings incrementally, combining new and existing."""
        if len(new_embeddings) == 0:
            logger.info("No new embeddings to cluster")
            return np.array([]), np.array([])
        
        # Combine existing and new embeddings
        if len(existing_embeddings) > 0:
            combined_embeddings = np.vstack([existing_embeddings, new_embeddings])
            logger.info(f"Combined {len(existing_embeddings)} existing + {len(new_embeddings)} new embeddings")
        else:
            combined_embeddings = new_embeddings
            logger.info(f"Using {len(new_embeddings)} new embeddings only")
        
        # Perform clustering on combined data
        logger.info("Performing HDBSCAN clustering...")
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean'
        )
        cluster_labels = clusterer.fit_predict(combined_embeddings)
        
        # Perform UMAP dimensionality reduction
        logger.info("Performing UMAP dimensionality reduction...")
        umap_reducer = umap.UMAP(
            n_components=2,
            random_state=42,
            n_neighbors=15,
            min_dist=0.1
        )
        umap_embeddings = umap_reducer.fit_transform(combined_embeddings)
        
        logger.info(f"Clustering complete: {len(set(cluster_labels))} clusters found")
        return cluster_labels, umap_embeddings
    
    def merge_messages_with_clustering(self, 
                                     existing_chunks: List[Dict],
                                     new_messages: List[Dict],
                                     cluster_labels: np.ndarray,
                                     umap_embeddings: np.ndarray) -> List[Dict]:
        """Merge new messages with existing chunks and add clustering info."""
        all_chunks = []
        
        # Add existing chunks (they already have clustering info)
        all_chunks.extend(existing_chunks)
        
        # Add new messages with clustering info
        existing_count = len(existing_chunks)
        for i, message in enumerate(new_messages):
            cluster_idx = existing_count + i
            chunk_with_clustering = {
                **message,
                'cluster_id': int(cluster_labels[cluster_idx]),
                'umap_x': float(umap_embeddings[cluster_idx][0]),
                'umap_y': float(umap_embeddings[cluster_idx][1]),
                # Preserve chat continuity information
                'parent_id': message.get('parent_id'),
                'message_id': message.get('message_id'),
                'chat_id': message.get('chat_id'),
                'role': message.get('role'),
                'timestamp': message.get('timestamp')
            }
            all_chunks.append(chunk_with_clustering)
        
        logger.info(f"Merged {len(existing_chunks)} existing + {len(new_messages)} new chunks")
        return all_chunks
    
    def save_results_incremental(self, 
                               all_chunks: List[Dict],
                               cluster_labels: np.ndarray,
                               umap_embeddings: np.ndarray,
                               processed_hashes: Set[str],
                               state_file: Path) -> None:
        """Save results and update state."""
        # Save all chunks with clustering info
        chunks_file = self.embeddings_dir / "chunks_with_clusters.jsonl"
        with jsonlines.open(chunks_file, mode='w') as writer:
            for chunk in all_chunks:
                writer.write(chunk)
        
        logger.info(f"Saved {len(all_chunks)} chunks to {chunks_file}")
        
        # Save state
        self.save_processed_message_hashes(processed_hashes, state_file)
        
        # Save clustering metadata
        metadata = {
            'total_chunks': len(all_chunks),
            'total_clusters': len(set(cluster_labels)),
            'clustering_timestamp': datetime.now().isoformat(),
            'cluster_distribution': {}
        }
        
        # Count clusters
        for label in cluster_labels:
            if label not in metadata['cluster_distribution']:
                metadata['cluster_distribution'][int(label)] = 0
            metadata['cluster_distribution'][int(label)] += 1
        
        metadata_file = self.embeddings_dir / "clustering_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved clustering metadata to {metadata_file}")
    
    def process_pipeline_incremental(self, 
                                   chats_file: Path,
                                   state_file: Path,
                                   min_cluster_size: int = 5,
                                   min_samples: int = 3,
                                   force_reprocess: bool = False) -> Dict:
        """Process the incremental embedding pipeline."""
        logger.info("🚀 Starting direct incremental embedding pipeline...")
        
        # Load existing chunks
        chunks_file = self.embeddings_dir / "chunks_with_clusters.jsonl"
        existing_chunks = self.load_existing_chunks(chunks_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            # Build processed hashes from existing chunks
            for chunk in existing_chunks:
                chunk_hash = self.generate_message_hash(chunk)
                processed_hashes.add(chunk_hash)
            logger.info(f"Built {len(processed_hashes)} processed hashes from existing chunks")
            
            # Also try to load from state file if it exists
            state_hashes = self.load_processed_message_hashes(state_file)
            if state_hashes:
                processed_hashes.update(state_hashes)
                logger.info(f"Added {len(state_hashes)} hashes from state file")
        
        # Load all messages from chats
        all_messages = self.load_messages_from_chats(chats_file)
        
        if not all_messages:
            logger.warning("No messages found in chats file")
            return {'status': 'no_messages'}
        
        # Identify new messages
        new_messages = self.identify_new_messages(all_messages, processed_hashes)
        
        if not new_messages and not force_reprocess:
            logger.info("No new messages to process")
            return {'status': 'no_new_messages'}
        
        # Embed new messages
        new_embeddings, embedded_new_messages = self.embed_messages(new_messages)
        
        if len(new_embeddings) == 0:
            logger.info("No new embeddings generated")
            return {'status': 'no_embeddings'}
        
        # Extract existing embeddings
        existing_embeddings = np.array([])
        if existing_chunks:
            existing_embeddings = np.array([chunk.get('embedding', []) for chunk in existing_chunks])
        
        # Cluster embeddings
        cluster_labels, umap_embeddings = self.cluster_embeddings_incremental(
            new_embeddings, existing_embeddings, min_cluster_size, min_samples
        )
        
        # Merge results
        all_chunks = self.merge_messages_with_clustering(
            existing_chunks, embedded_new_messages, cluster_labels, umap_embeddings
        )
        
        # Update processed hashes
        for message in new_messages:
            message_hash = self.generate_message_hash(message)
            processed_hashes.add(message_hash)
        
        # Save results
        self.save_results_incremental(all_chunks, cluster_labels, umap_embeddings, processed_hashes, state_file)
        
        logger.info("✅ Direct incremental embedding pipeline completed")
        
        return {
            'status': 'success',
            'total_chunks': len(all_chunks),
            'new_chunks': len(new_messages),
            'total_clusters': len(set(cluster_labels))
        }


@click.command()
@click.option('--chats-file',
              default='data/processed/chats.jsonl',
              help='Input JSONL file with chat messages')
@click.option('--state-file',
              default='data/processed/direct_embedding_state.pkl',
              help='State file for tracking processed messages')
@click.option('--model', default='all-MiniLM-L6-v2', help='Sentence transformer model to use')
@click.option('--min-cluster-size', default=5, help='Minimum cluster size for HDBSCAN')
@click.option('--min-samples', default=3, help='Minimum samples for HDBSCAN')
@click.option('--processed-dir', default='data/processed', help='Directory with processed chats')
@click.option('--embeddings-dir', default='data/embeddings', help='Output directory for embeddings')
@click.option('--force', is_flag=True, help='Force reprocess all messages (ignore state)')
def main(chats_file: str, state_file: str, model: str, min_cluster_size: int, min_samples: int,
         processed_dir: str, embeddings_dir: str, force: bool):
    """Run direct incremental embedding and clustering pipeline."""
    
    embedder = DirectIncrementalChatEmbedder(
        model_name=model,
        processed_dir=processed_dir,
        embeddings_dir=embeddings_dir
    )
    
    result = embedder.process_pipeline_incremental(
        chats_file=Path(chats_file),
        state_file=Path(state_file),
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        force_reprocess=force
    )
    
    if result['status'] == 'success':
        logger.info(f"✅ Pipeline completed successfully!")
        logger.info(f"   Total chunks: {result['total_chunks']}")
        logger.info(f"   New chunks: {result['new_chunks']}")
        logger.info(f"   Total clusters: {result['total_clusters']}")
    else:
        logger.info(f"ℹ️ Pipeline status: {result['status']}")


if __name__ == "__main__":
    main() 