#!/usr/bin/env python3
"""
ChatMind Clustering Step

Takes embeddings and creates semantic clusters.
This step is separate from embedding to allow for different clustering strategies.
Uses modular directory structure: data/processed/clustering/
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
import numpy as np

try:
    import umap
    from sklearn.cluster import HDBSCAN
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logging.warning("UMAP/HDBSCAN not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingClusterer:
    """Creates semantic clusters from embeddings."""
    
    def __init__(self, input_file: str = "data/processed/embedding/embeddings.jsonl"):
        self.input_file = Path(input_file)
        
        # Use modular directory structure
        self.output_dir = Path("../../data/processed/clustering")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_embedding_hash(self, embedding: Dict) -> str:
        """Generate a hash for an embedding to track if it's been processed."""
        # Create a normalized version for hashing
        normalized_embedding = {
            'chunk_id': embedding.get('chunk_id', ''),
            'chat_id': embedding.get('chat_id', ''),
            'content': embedding.get('content', ''),
            'embedding': embedding.get('embedding', [])
        }
        content = json.dumps(normalized_embedding, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_embedding_hashes(self) -> Set[str]:
        """Load hashes of embeddings that have already been clustered."""
        hash_file = self.output_dir / "hashes.pkl"
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed embedding hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def _save_processed_embedding_hashes(self, hashes: Set[str]) -> None:
        """Save hashes of processed embeddings."""
        hash_file = self.output_dir / "hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed embedding hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'clustering',
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
    
    def _load_existing_clusters(self, clusters_file: Path) -> List[Dict]:
        """Load existing clusters from output file."""
        clusters = []
        if clusters_file.exists():
            with jsonlines.open(clusters_file) as reader:
                for cluster in reader:
                    clusters.append(cluster)
            logger.info(f"Loaded {len(clusters)} existing clusters")
        return clusters
    
    def _load_embeddings(self, embeddings_file: Path) -> List[Dict]:
        """Load embeddings from JSONL file."""
        embeddings = []
        with jsonlines.open(embeddings_file) as reader:
            for embedding in reader:
                embeddings.append(embedding)
        
        logger.info(f"Loaded {len(embeddings)} embeddings from {embeddings_file}")
        return embeddings
    
    def _cluster_embeddings(self, embeddings: List[Dict], min_cluster_size: int = 5, min_samples: int = 3) -> List[Dict]:
        """Cluster embeddings using HDBSCAN and UMAP."""
        if not embeddings:
            logger.warning("No embeddings to cluster")
            return []
        
        # Extract embedding vectors
        embedding_vectors = np.array([emb.get('embedding', []) for emb in embeddings])
        
        if len(embedding_vectors) == 0:
            logger.warning("No valid embedding vectors found")
            return []
        
        # Perform clustering
        logger.info("Performing HDBSCAN clustering...")
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean'
        )
        cluster_labels = clusterer.fit_predict(embedding_vectors)
        
        # Perform UMAP dimensionality reduction
        logger.info("Performing UMAP dimensionality reduction...")
        umap_reducer = umap.UMAP(
            n_components=2,
            random_state=42,
            n_neighbors=15,
            min_dist=0.1
        )
        umap_embeddings = umap_reducer.fit_transform(embedding_vectors)
        
        # Add clustering info to embeddings
        clustered_embeddings = []
        for i, embedding in enumerate(embeddings):
            clustered_embedding = embedding.copy()
            clustered_embedding['cluster_id'] = str(cluster_labels[i])  # Use string cluster IDs for consistency
            clustered_embedding['umap_x'] = float(umap_embeddings[i][0])
            clustered_embedding['umap_y'] = float(umap_embeddings[i][1])
            clustered_embeddings.append(clustered_embedding)
        
        logger.info(f"Clustering complete: {len(set(cluster_labels))} clusters found")
        return clustered_embeddings
    
    def process_embeddings_to_clusters(self, min_cluster_size: int = 5, min_samples: int = 3, force_reprocess: bool = False) -> Dict:
        """Process embeddings into clusters."""
        logger.info("🚀 Starting embedding clustering...")
        
        # Load existing clusters
        clusters_file = self.output_dir / "clustered_embeddings.jsonl"
        existing_clusters = [] if force_reprocess else self._load_existing_clusters(clusters_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_embedding_hashes()
            logger.info(f"Found {len(processed_hashes)} existing processed hashes")
        else:
            logger.info("Force reprocess: clearing existing processed hashes")
        
        # Load embeddings
        embeddings = self._load_embeddings(self.input_file)
        if not embeddings:
            logger.warning("No embeddings found")
            return {'status': 'no_embeddings'}
        
        # Identify new embeddings
        new_embeddings = []
        for embedding in embeddings:
            embedding_hash = self._generate_embedding_hash(embedding)
            if embedding_hash not in processed_hashes or force_reprocess:
                new_embeddings.append(embedding)
                processed_hashes.add(embedding_hash)
        
        if not new_embeddings and not force_reprocess:
            logger.info("No new embeddings to process")
            return {'status': 'no_new_embeddings'}
        
        # Cluster all embeddings (existing + new)
        all_embeddings = existing_clusters + new_embeddings
        clustered_embeddings = self._cluster_embeddings(all_embeddings, min_cluster_size, min_samples)
        
        if not clustered_embeddings:
            logger.warning("No clusters created")
            return {'status': 'no_clusters'}
        
        # Save clustered embeddings
        with jsonlines.open(clusters_file, mode='w') as writer:
            for embedding in clustered_embeddings:
                writer.write(embedding)
        
        # Save hashes and metadata
        self._save_processed_embedding_hashes(processed_hashes)
        
        # Calculate statistics
        cluster_ids = [emb.get('cluster_id', -1) for emb in clustered_embeddings]
        unique_clusters = set(cluster_ids)
        noise_count = cluster_ids.count(-1)
        
        stats = {
            'status': 'success',
            'total_embeddings': len(clustered_embeddings),
            'new_embeddings': len(new_embeddings),
            'existing_embeddings': len(existing_clusters),
            'total_clusters': len(unique_clusters) - (1 if -1 in unique_clusters else 0),
            'noise_points': noise_count,
            'avg_cluster_size': (len(clustered_embeddings) - noise_count) / max(1, len(unique_clusters) - (1 if -1 in unique_clusters else 0))
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Embedding clustering completed!")
        logger.info(f"  Total embeddings: {stats['total_embeddings']}")
        logger.info(f"  New embeddings: {stats['new_embeddings']}")
        logger.info(f"  Total clusters: {stats['total_clusters']}")
        logger.info(f"  Noise points: {stats['noise_points']}")
        logger.info(f"  Avg cluster size: {stats['avg_cluster_size']:.2f}")
        
        return stats


@click.command()
@click.option('--input-file', 
              default='data/processed/embedding/embeddings.jsonl',
              help='Input embeddings file')
@click.option('--min-cluster-size', default=5, help='Minimum cluster size for HDBSCAN')
@click.option('--min-samples', default=3, help='Minimum samples for HDBSCAN')
@click.option('--force', is_flag=True, help='Force reprocess all embeddings')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(input_file: str, min_cluster_size: int, min_samples: int, force: bool, check_only: bool):
    """Create semantic clusters from embeddings."""
    
    if check_only:
        logger.info("🔍 Checking clustering setup...")
        input_path = Path(input_file)
        if input_path.exists():
            logger.info(f"✅ Input file exists: {input_path}")
        else:
            logger.error(f"❌ Input file not found: {input_path}")
        return
    
    clusterer = EmbeddingClusterer(input_file)
    stats = clusterer.process_embeddings_to_clusters(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        force_reprocess=force
    )
    
    if stats['status'] == 'success':
        logger.info("✅ Clustering successful!")
    else:
        logger.error(f"❌ Clustering failed: {stats.get('reason', 'unknown')}")


if __name__ == "__main__":
    main() 