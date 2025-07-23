#!/usr/bin/env python3
"""
Semantic Embedding and Clustering Pipeline

Processes chat messages into embeddings, clusters them semantically,
and prepares data for Neo4j graph loading.
"""

import json
import jsonlines
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import click
from tqdm import tqdm
import logging
import pickle

# ML imports
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
from sklearn.manifold import TSNE
import umap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatEmbedder:
    """Embeds and clusters chat messages semantically."""
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 processed_dir: str = "data/processed",
                 embeddings_dir: str = "data/embeddings"):
        self.model = SentenceTransformer(model_name)
        self.processed_dir = Path(processed_dir)
        self.embeddings_dir = Path(embeddings_dir)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
    def load_chats(self) -> List[Dict]:
        """Load processed chat data."""
        chats_file = self.processed_dir / "chats.jsonl"
        if not chats_file.exists():
            raise FileNotFoundError(f"No processed chats found at {chats_file}")
        
        chats = []
        with jsonlines.open(chats_file) as reader:
            for chat in reader:
                chats.append(chat)
        
        logger.info(f"Loaded {len(chats)} chats")
        return chats
    
    def extract_messages(self, chats: List[Dict]) -> List[Dict]:
        """Extract individual messages from chats with metadata."""
        messages = []
        
        for chat in chats:
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
        
        logger.info(f"Extracted {len(messages)} messages")
        return messages
    
    def chunk_messages(self, messages: List[Dict], max_length: int = 512, use_semantic_chunking: bool = False) -> List[Dict]:
        """Split messages into chunks using either simple or semantic chunking."""
        if use_semantic_chunking:
            return self._semantic_chunk_messages(messages)
        else:
            return self._simple_chunk_messages(messages, max_length)
    
    def _simple_chunk_messages(self, messages: List[Dict], max_length: int = 512) -> List[Dict]:
        """Split long messages into chunks for better embedding (simple method)."""
        chunks = []
        
        for msg in messages:
            content = msg['content']
            
            # Simple chunking by sentences/paragraphs
            if len(content) <= max_length:
                chunks.append(msg)
            else:
                # Split by sentences or paragraphs
                sentences = content.split('. ')
                current_chunk = ""
                chunk_id = 0
                
                for sentence in sentences:
                    if len(current_chunk + sentence) > max_length and current_chunk:
                        chunks.append({
                            **msg,
                            'content': current_chunk.strip(),
                            'chunk_id': chunk_id
                        })
                        current_chunk = sentence
                        chunk_id += 1
                    else:
                        current_chunk += sentence + ". "
                
                if current_chunk.strip():
                    chunks.append({
                        **msg,
                        'content': current_chunk.strip(),
                        'chunk_id': chunk_id
                    })
        
        logger.info(f"Created {len(chunks)} simple chunks from {len(messages)} messages")
        return chunks
    
    def _semantic_chunk_messages(self, messages: List[Dict]) -> List[Dict]:
        """Use semantic chunking for messages."""
        try:
            from chatmind.semantic_chunker import SemanticChunker
            
            # Group messages by chat_id
            chats = {}
            for msg in messages:
                chat_id = msg['chat_id']
                if chat_id not in chats:
                    chats[chat_id] = {
                        'content_hash': chat_id,
                        'title': msg['chat_title'],
                        'messages': []
                    }
                chats[chat_id]['messages'].append({
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg.get('timestamp'),
                    'parent_id': msg.get('parent_id')
                })
            
            # Use semantic chunker
            chunker = SemanticChunker()
            all_chunks = []
            
            for chat_data in chats.values():
                semantic_chunks = chunker.chunk_chat(chat_data)
                all_chunks.extend(semantic_chunks)
            
            logger.info(f"Created {len(all_chunks)} semantic chunks from {len(messages)} messages")
            return all_chunks
            
        except ImportError:
            logger.warning("Semantic chunker not available, falling back to simple chunking")
            return self._simple_chunk_messages(messages)
        except Exception as e:
            logger.error(f"Error in semantic chunking: {e}, falling back to simple chunking")
            return self._simple_chunk_messages(messages)
    
    def _auto_tag_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Auto-tag chunks using GPT."""
        try:
            from chatmind.tagger import ChunkTagger
            
            logger.info("Starting auto-tagging of chunks...")
            tagger = ChunkTagger()
            tagged_chunks = tagger.tag_multiple_chunks(chunks)
            
            # Get tagging statistics
            stats = tagger.get_tagging_stats(tagged_chunks)
            logger.info(f"Auto-tagging complete: {stats['total_chunks']} chunks tagged")
            logger.info(f"Applied {stats['total_tags']} tags, {stats['unique_tags']} unique")
            
            return tagged_chunks
            
        except ImportError:
            logger.warning("Auto-tagger not available, skipping tagging")
            return chunks
        except Exception as e:
            logger.error(f"Error in auto-tagging: {e}, skipping tagging")
            return chunks
    
    def embed_chunks(self, chunks: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        """Generate embeddings for message chunks."""
        texts = [chunk['content'] for chunk in chunks]
        
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()
        
        return embeddings, chunks
    
    def cluster_embeddings(self, 
                          embeddings: np.ndarray, 
                          min_cluster_size: int = 5,
                          min_samples: int = 3) -> Tuple[np.ndarray, List[Dict]]:
        """Cluster embeddings using HDBSCAN."""
        logger.info("Clustering embeddings...")
        
        # Reduce dimensionality with UMAP for better clustering
        umap_reducer = umap.UMAP(
            n_neighbors=15,
            n_components=50,
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )
        
        umap_embeddings = umap_reducer.fit_transform(embeddings)
        
        # Cluster with HDBSCAN
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean',
            cluster_selection_method='eom'
        )
        
        cluster_labels = clusterer.fit_predict(umap_embeddings)
        
        # Get cluster statistics
        unique_clusters = set(cluster_labels)
        noise_points = sum(1 for label in cluster_labels if label == -1)
        
        logger.info(f"Found {len(unique_clusters) - 1} clusters")
        logger.info(f"Noise points: {noise_points}")
        
        return cluster_labels, umap_embeddings
    
    def generate_cluster_summaries(self, chunks: List[Dict], cluster_labels: np.ndarray) -> Dict:
        """Generate summaries for each cluster."""
        cluster_data = {}
        
        for i, label in enumerate(cluster_labels):
            if label not in cluster_data:
                cluster_data[label] = []
            cluster_data[label].append(chunks[i])
        
        summaries = {}
        for cluster_id, cluster_chunks in cluster_data.items():
            if cluster_id == -1:  # Noise cluster
                continue
                
            # Simple summary: most common words + sample titles
            all_text = " ".join([chunk['content'] for chunk in cluster_chunks])
            words = all_text.lower().split()
            
            # Get most common words (excluding common stop words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            
            word_counts = {}
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # Get top words
            top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Get sample chat titles
            chat_titles = list(set([chunk['chat_title'] for chunk in cluster_chunks]))[:5]
            
            summaries[int(cluster_id)] = {
                'size': len(cluster_chunks),
                'top_words': [word for word, count in top_words],
                'sample_titles': chat_titles,
                'chunk_ids': [chunk['message_id'] for chunk in cluster_chunks]
            }
        
        return summaries
    
    def save_results(self, 
                    chunks: List[Dict], 
                    cluster_labels: np.ndarray,
                    umap_embeddings: np.ndarray,
                    cluster_summaries: Dict) -> None:
        """Save processed data and results."""
        
        # Save chunks with cluster labels
        for i, chunk in enumerate(chunks):
            chunk['cluster_id'] = int(cluster_labels[i])
        
        chunks_file = self.embeddings_dir / "chunks_with_clusters.jsonl"
        with jsonlines.open(chunks_file, mode='w') as writer:
            for chunk in chunks:
                writer.write(chunk)
        
        # Save cluster summaries
        summaries_file = self.embeddings_dir / "cluster_summaries.json"
        with open(summaries_file, 'w') as f:
            json.dump(cluster_summaries, f, indent=2)
        
        # Save UMAP embeddings for visualization
        umap_file = self.embeddings_dir / "umap_embeddings.pkl"
        with open(umap_file, 'wb') as f:
            pickle.dump(umap_embeddings, f)
        
        # Save cluster labels
        labels_file = self.embeddings_dir / "cluster_labels.pkl"
        with open(labels_file, 'wb') as f:
            pickle.dump(cluster_labels, f)
        
        logger.info(f"Saved results to {self.embeddings_dir}")
    
    def process_pipeline(self, 
                        max_chunk_length: int = 512,
                        min_cluster_size: int = 5,
                        min_samples: int = 3,
                        use_semantic_chunking: bool = False,
                        use_auto_tagging: bool = False) -> Dict:
        """Run the complete embedding and clustering pipeline."""
        
        # Load chats
        chats = self.load_chats()
        
        # Extract messages
        messages = self.extract_messages(chats)
        
        # Chunk messages
        chunks = self.chunk_messages(messages, max_chunk_length, use_semantic_chunking)
        
        # Auto-tag chunks if enabled
        if use_auto_tagging:
            chunks = self._auto_tag_chunks(chunks)
        
        # Generate embeddings
        embeddings, chunks_with_embeddings = self.embed_chunks(chunks)
        
        # Cluster embeddings
        cluster_labels, umap_embeddings = self.cluster_embeddings(
            embeddings, min_cluster_size, min_samples
        )
        
        # Generate summaries
        cluster_summaries = self.generate_cluster_summaries(chunks_with_embeddings, cluster_labels)
        
        # Save results
        self.save_results(chunks_with_embeddings, cluster_labels, umap_embeddings, cluster_summaries)
        
        return {
            'total_chunks': len(chunks_with_embeddings),
            'total_clusters': len(cluster_summaries),
            'noise_points': sum(1 for label in cluster_labels if label == -1)
        }


@click.command()
@click.option('--model', default='all-MiniLM-L6-v2', help='Sentence transformer model to use')
@click.option('--max-length', default=512, help='Maximum chunk length')
@click.option('--min-cluster-size', default=5, help='Minimum cluster size for HDBSCAN')
@click.option('--min-samples', default=3, help='Minimum samples for HDBSCAN')
@click.option('--processed-dir', default='data/processed', help='Directory with processed chats')
@click.option('--embeddings-dir', default='data/embeddings', help='Output directory for embeddings')
@click.option('--semantic-chunking', is_flag=True, help='Use GPT-driven semantic chunking')
@click.option('--auto-tagging', is_flag=True, help='Use GPT-driven auto-tagging')
def main(model: str, max_length: int, min_cluster_size: int, min_samples: int, 
         processed_dir: str, embeddings_dir: str, semantic_chunking: bool, auto_tagging: bool):
    """Run the embedding and clustering pipeline."""
    
    embedder = ChatEmbedder(model, processed_dir, embeddings_dir)
    
    try:
        results = embedder.process_pipeline(
            max_chunk_length=max_length, 
            min_cluster_size=min_cluster_size, 
            min_samples=min_samples,
            use_semantic_chunking=semantic_chunking,
            use_auto_tagging=auto_tagging
        )
        logger.info(f"Pipeline completed successfully!")
        logger.info(f"Results: {results}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main() 