#!/usr/bin/env python3
"""
Cloud API Enhanced Embedding and Clustering Pipeline

Uses OpenAI embeddings for higher quality semantic understanding.
Processes chat messages into embeddings, clusters them semantically,
and prepares data for Neo4j graph loading.
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
import time
import openai

# ML imports
try:
    from sklearn.cluster import HDBSCAN
    from sklearn.manifold import TSNE
    import umap
except ImportError as e:
    logger.error(f"Missing ML dependencies: {e}")
    logger.error("Install with: pip install scikit-learn umap-learn")
    raise

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudEnhancedChatEmbedder:
    """Embeds and clusters chat messages using OpenAI embeddings for better quality."""
    
    def __init__(self, 
                 model_name: str = "text-embedding-3-small",
                 processed_dir: str = "data/processed",
                 embeddings_dir: str = "data/embeddings",
                 max_retries: int = 3,
                 delay_between_calls: float = 0.1):
        self.model_name = model_name
        self.processed_dir = Path(processed_dir)
        self.embeddings_dir = Path(embeddings_dir)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        self.stats = {
            'messages_processed': 0,
            'api_calls': 0,
            'errors': 0,
            'total_tokens': 0
        }
        
    def generate_message_hash(self, message: Dict) -> str:
        """Generate a hash for a message to track if it's been processed."""
        normalized_message = {
            'content': message.get('content', ''),
            'chat_id': message.get('chat_id', ''),
            'message_id': message.get('message_id', ''),
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
                    chat_title = chat.get('title', 'Untitled')
                    
                    for msg in chat.get('messages', []):
                        if msg.get('content', '').strip():
                            messages.append({
                                'message_id': f"{chat_id}_{msg['id']}",
                                'chat_id': chat_id,
                                'chat_title': chat_title,
                                'role': msg.get('role', 'unknown'),
                                'content': msg['content'],
                                'timestamp': msg.get('timestamp'),
                                'parent_id': msg.get('parent_id')
                            })
            
            logger.info(f"Loaded {len(messages)} messages from chats")
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
    
    def embed_messages_with_openai(self, messages: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """Embed messages using OpenAI API."""
        if not messages:
            return np.array([]), []
        
        embeddings = []
        embedded_messages = []
        
        # Prepare texts for embedding
        texts = [msg['content'] for msg in messages]
        
        # Process in batches to avoid rate limits
        batch_size = 100
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding messages"):
            batch_texts = texts[i:i + batch_size]
            batch_messages = messages[i:i + batch_size]
            
            for attempt in range(self.max_retries):
                try:
                    response = openai.Embedding.create(
                        model=self.model_name,
                        input=batch_texts
                    )
                    
                    self.stats['api_calls'] += 1
                    self.stats['total_tokens'] += response.usage.total_tokens
                    
                    # Extract embeddings
                    batch_embeddings = [data.embedding for data in response.data]
                    embeddings.extend(batch_embeddings)
                    embedded_messages.extend(batch_messages)
                    
                    # Add delay between calls
                    time.sleep(self.delay_between_calls)
                    break
                    
                except Exception as e:
                    logger.error(f"API call failed (attempt {attempt + 1}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay_between_calls * 2)
                        continue
                    else:
                        logger.error(f"Failed to embed batch after {self.max_retries} attempts")
                        # Add zero embeddings for failed messages
                        for _ in batch_messages:
                            embeddings.append([0.0] * 1536)  # OpenAI embedding dimension
                            embedded_messages.extend(batch_messages)
                        self.stats['errors'] += 1
        
        embeddings_array = np.array(embeddings)
        logger.info(f"Generated embeddings for {len(embedded_messages)} messages")
        return embeddings_array, embedded_messages
    
    def cluster_embeddings_incremental(self, 
                                     new_embeddings: np.ndarray,
                                     existing_embeddings: np.ndarray,
                                     min_cluster_size: int = 5,
                                     min_samples: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """Cluster embeddings incrementally, combining new and existing."""
        if len(new_embeddings) == 0:
            return np.array([]), np.array([])
        
        # Combine existing and new embeddings
        if len(existing_embeddings) > 0:
            all_embeddings = np.vstack([existing_embeddings, new_embeddings])
        else:
            all_embeddings = new_embeddings
        
        # Perform clustering
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='cosine'
        )
        cluster_labels = clusterer.fit_predict(all_embeddings)
        
        # Generate UMAP for visualization
        umap_reducer = umap.UMAP(
            n_components=2,
            metric='cosine',
            random_state=42
        )
        umap_embeddings = umap_reducer.fit_transform(all_embeddings)
        
        logger.info(f"Clustered {len(all_embeddings)} embeddings into {len(set(cluster_labels)) - 1} clusters")
        return cluster_labels, umap_embeddings
    
    def merge_messages_with_clustering(self, 
                                     existing_chunks: List[Dict],
                                     new_messages: List[Dict],
                                     cluster_labels: np.ndarray,
                                     umap_embeddings: np.ndarray) -> List[Dict]:
        """Merge new messages with existing chunks and add clustering info."""
        all_chunks = existing_chunks.copy()
        
        # Add new messages as chunks
        start_idx = len(existing_chunks)
        for i, message in enumerate(new_messages):
            chunk = {
                'content': message['content'],
                'chat_id': message['chat_id'],
                'chat_title': message['chat_title'],
                'message_id': message['message_id'],
                'role': message['role'],
                'timestamp': message['timestamp'],
                'parent_id': message.get('parent_id'),
                'cluster_id': int(cluster_labels[start_idx + i]),
                'umap_x': float(umap_embeddings[start_idx + i, 0]),
                'umap_y': float(umap_embeddings[start_idx + i, 1]),
                'embedding_model': self.model_name,
                'embedding_timestamp': int(time.time())
            }
            all_chunks.append(chunk)
        
        # Update existing chunks with new cluster info
        for i, chunk in enumerate(existing_chunks):
            chunk['cluster_id'] = int(cluster_labels[i])
            chunk['umap_x'] = float(umap_embeddings[i, 0])
            chunk['umap_y'] = float(umap_embeddings[i, 1])
        
        logger.info(f"Merged {len(new_messages)} new messages with {len(existing_chunks)} existing chunks")
        return all_chunks
    
    def save_results_incremental(self, 
                               all_chunks: List[Dict],
                               cluster_labels: np.ndarray,
                               umap_embeddings: np.ndarray,
                               processed_hashes: Set[str],
                               state_file: Path) -> None:
        """Save incremental embedding and clustering results."""
        # Save chunks with embeddings
        chunks_file = self.embeddings_dir / "chunks_with_clusters.jsonl"
        with jsonlines.open(chunks_file, 'w') as writer:
            for chunk in all_chunks:
                writer.write(chunk)
        
        # Save embeddings array
        embeddings_file = self.embeddings_dir / "embeddings.npy"
        np.save(embeddings_file, umap_embeddings)
        
        # Save cluster labels
        labels_file = self.embeddings_dir / "cluster_labels.npy"
        np.save(labels_file, cluster_labels)
        
        # Save processed hashes
        self.save_processed_message_hashes(processed_hashes, state_file)
        
        logger.info(f"Saved {len(all_chunks)} chunks with embeddings and clustering")
        logger.info(f"Embeddings saved to {embeddings_file}")
        logger.info(f"Cluster labels saved to {labels_file}")
    
    def process_pipeline_incremental(self, 
                                   chats_file: Path,
                                   state_file: Path,
                                   min_cluster_size: int = 5,
                                   min_samples: int = 3,
                                   force_reprocess: bool = False) -> Dict:
        """Process the complete incremental embedding pipeline."""
        logger.info(f"Starting incremental embedding pipeline with {self.model_name}")
        
        # Load existing state
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self.load_processed_message_hashes(state_file)
        
        # Load existing chunks
        chunks_file = self.embeddings_dir / "chunks_with_clusters.jsonl"
        existing_chunks = self.load_existing_chunks(chunks_file)
        
        # Load all messages
        all_messages = self.load_messages_from_chats(chats_file)
        if not all_messages:
            logger.warning("No messages found to process")
            return self.stats
        
        # Identify new messages
        new_messages = self.identify_new_messages(all_messages, processed_hashes)
        
        if not new_messages and not force_reprocess:
            logger.info("No new messages to process")
            return self.stats
        
        # Embed new messages
        if new_messages:
            new_embeddings, embedded_messages = self.embed_messages_with_openai(new_messages)
            
            # Load existing embeddings if available
            existing_embeddings = np.array([])
            embeddings_file = self.embeddings_dir / "embeddings.npy"
            if embeddings_file.exists() and len(existing_chunks) > 0:
                existing_embeddings = np.load(embeddings_file)
            
            # Cluster embeddings
            cluster_labels, umap_embeddings = self.cluster_embeddings_incremental(
                new_embeddings, existing_embeddings, min_cluster_size, min_samples
            )
            
            # Merge results
            all_chunks = self.merge_messages_with_clustering(
                existing_chunks, embedded_messages, cluster_labels, umap_embeddings
            )
            
            # Update processed hashes
            for message in embedded_messages:
                message_hash = self.generate_message_hash(message)
                processed_hashes.add(message_hash)
            
            # Save results
            self.save_results_incremental(
                all_chunks, cluster_labels, umap_embeddings, processed_hashes, state_file
            )
            
            self.stats['messages_processed'] = len(embedded_messages)
        
        # Print statistics
        total_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        logger.info(f"📊 Cloud API Embedding Statistics:")
        logger.info(f"  - Messages processed: {self.stats['messages_processed']}")
        logger.info(f"  - API calls made: {self.stats['api_calls']}")
        logger.info(f"  - Total tokens used: {self.stats['total_tokens']}")
        logger.info(f"  - Errors: {self.stats['errors']}")
        logger.info(f"  - Total clusters: {total_clusters}")
        logger.info(f"  - Total chunks: {len(all_chunks)}")
        
        return self.stats


@click.command()
@click.option('--chats-file',
              default='data/processed/chats.jsonl',
              help='Input JSONL file with chat messages')
@click.option('--state-file',
              default='data/processed/cloud_embedding_state.pkl',
              help='State file for tracking processed messages')
@click.option('--model', 
              default='text-embedding-3-small', 
              help='OpenAI embedding model to use')
@click.option('--min-cluster-size', 
              default=5, 
              help='Minimum cluster size for HDBSCAN')
@click.option('--min-samples', 
              default=3, 
              help='Minimum samples for HDBSCAN')
@click.option('--processed-dir', 
              default='data/processed', 
              help='Directory with processed chats')
@click.option('--embeddings-dir', 
              default='data/embeddings', 
              help='Output directory for embeddings')
@click.option('--force', 
              is_flag=True, 
              help='Force reprocess all messages (ignore state)')
@click.option('--max-retries', 
              default=3, 
              help='Maximum retries for API calls')
@click.option('--delay', 
              default=0.1, 
              help='Delay between API calls (seconds)')
def main(chats_file: str, state_file: str, model: str, min_cluster_size: int, min_samples: int,
         processed_dir: str, embeddings_dir: str, force: bool, max_retries: int, delay: float):
    """Run cloud API enhanced embedding and clustering pipeline."""
    
    # Check OpenAI API key
    if not openai.api_key:
        logger.error("OpenAI API key not set. Set OPENAI_API_KEY environment variable.")
        return 1
    
    # Initialize embedder
    embedder = CloudEnhancedChatEmbedder(
        model_name=model,
        processed_dir=processed_dir,
        embeddings_dir=embeddings_dir,
        max_retries=max_retries,
        delay_between_calls=delay
    )
    
    # Process pipeline
    try:
        stats = embedder.process_pipeline_incremental(
            chats_file=Path(chats_file),
            state_file=Path(state_file),
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            force_reprocess=force
        )
        
        logger.info("✅ Cloud API embedding pipeline completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Cloud API embedding pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main()) 