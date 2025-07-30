#!/usr/bin/env python3
"""
ChatMind Cluster Positioning

Creates 2D coordinates for clusters using their summaries.
Uses cluster summaries from cluster_summarization step.
Outputs to data/processed/positioning/ with proper hash connections.
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import logging
from tqdm import tqdm
import hashlib
import pickle
from datetime import datetime
import numpy as np

# Import for dimensionality reduction
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logging.warning("UMAP not available, will use random fallback")

try:
    from sklearn.manifold import TSNE
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, will use random fallback")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClusterPositioner:
    """Creates 2D coordinates for clusters using their summaries."""
    
    def __init__(self, cluster_summaries_file: str = "data/processed/cluster_summarization/cluster_summaries.json"):
        self.cluster_summaries_file = Path(cluster_summaries_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/positioning")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_positioning_hash(self, cluster_id: str, summary_hash: str) -> str:
        """Generate a hash for cluster positioning to track if it's been processed."""
        # Create a normalized version for hashing
        normalized_positioning = {
            'cluster_id': cluster_id,
            'summary_hash': summary_hash
        }
        content = json.dumps(normalized_positioning, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_positioning_hashes(self) -> Set[str]:
        """Load hashes of clusters that have already been positioned."""
        hash_file = self.output_dir / "cluster_positioning_hashes.pkl"
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} existing positioning hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load positioning hashes: {e}")
        return set()
    
    def _save_processed_positioning_hashes(self, hashes: Set[str]) -> None:
        """Save hashes of processed cluster positioning."""
        hash_file = self.output_dir / "cluster_positioning_hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} positioning hashes")
        except Exception as e:
            logger.error(f"Failed to save positioning hashes: {e}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata_file = self.output_dir / "cluster_positioning_metadata.json"
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'cluster_positioning',
            'stats': stats,
            'version': '1.0'
        }
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _load_existing_positions(self, positions_file: Path) -> Dict:
        """Load existing cluster positions from file."""
        positions = {}
        if positions_file.exists():
            with jsonlines.open(positions_file) as reader:
                for position in reader:
                    cluster_id = position.get('cluster_id')
                    if cluster_id:
                        positions[cluster_id] = position
            logger.info(f"Loaded {len(positions)} existing cluster positions")
        return positions
    
    def _load_cluster_summaries(self) -> Dict:
        """Load cluster summaries from file."""
        summaries = {}
        if self.cluster_summaries_file.exists():
            with open(self.cluster_summaries_file, 'r') as f:
                summaries = json.load(f)
            logger.info(f"Loaded {len(summaries)} cluster summaries")
        return summaries
    
    def _save_cluster_summary_embeddings(self, cluster_embeddings: Dict[str, np.ndarray]) -> None:
        """Save cluster summary embeddings alongside positions."""
        embeddings_file = self.output_dir / "cluster_summary_embeddings.jsonl"
        
        with jsonlines.open(embeddings_file, 'w') as writer:
            for cluster_id, embedding in cluster_embeddings.items():
                writer.write({
                    'cluster_id': cluster_id,
                    'embedding': embedding.tolist(),
                    'hash': self._generate_content_hash({
                        'cluster_id': cluster_id,
                        'embedding': embedding.tolist()
                    })
                })
        
        logger.info(f"💾 Saved cluster summary embeddings to {embeddings_file}")
    
    def _generate_content_hash(self, data: Dict) -> str:
        """Generate a content hash for tracking."""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _compute_summary_embeddings(self, summaries: Dict) -> Tuple[Dict[str, np.ndarray], List[str]]:
        """Compute embeddings for cluster summaries using TF-IDF or embedding models."""
        if not summaries:
            return {}, []
        
        cluster_ids = list(summaries.keys())
        texts = []
        
        for cluster_id in cluster_ids:
            summary = summaries[cluster_id]
            if isinstance(summary, dict):
                # Extract summary text from the summary object
                summary_text = summary.get('summary', '')
                if not summary_text:
                    # Fallback to other fields
                    summary_text = summary.get('key_topics', '') or summary.get('domain', '') or ''
            else:
                summary_text = str(summary)
            
            texts.append(summary_text)
        
        # Try embedding models first, fallback to TF-IDF
        try:
            # Check if sentence-transformers is available
            import sentence_transformers
            from sentence_transformers import SentenceTransformer
            
            # Load model
            model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions, fast
            
            # Check token limits and truncate if needed
            MAX_TOKENS = 512  # Conservative limit for sentence-transformers
            processed_texts = []
            valid_cluster_ids = []
            
            for i, text in enumerate(texts):
                # Simple token estimation (rough approximation)
                estimated_tokens = len(text.split()) * 1.3  # Rough estimate
                
                if estimated_tokens > MAX_TOKENS:
                    # Truncate text to fit within token limit
                    words = text.split()
                    truncated_words = words[:int(MAX_TOKENS / 1.3)]
                    truncated_text = ' '.join(truncated_words)
                    logger.warning(f"Truncated summary from {estimated_tokens:.0f} to ~{MAX_TOKENS} tokens")
                    processed_texts.append(truncated_text)
                else:
                    processed_texts.append(text)
                
                valid_cluster_ids.append(cluster_ids[i])
            
            # Generate embeddings
            embeddings = model.encode(processed_texts, convert_to_numpy=True)
            logger.info(f"Generated embeddings using sentence-transformers: {embeddings.shape}")
            
            # Create cluster_id to embedding mapping
            cluster_embeddings = {}
            for i, cluster_id in enumerate(valid_cluster_ids):
                cluster_embeddings[cluster_id] = embeddings[i]
            
            return cluster_embeddings, valid_cluster_ids
            
        except ImportError:
            logger.info("sentence-transformers not available, using TF-IDF fallback")
        except Exception as e:
            logger.warning(f"Embedding model failed: {e}, using TF-IDF fallback")
        
        # TF-IDF fallback (no token limits)
        from collections import Counter
        import re
        
        # Create vocabulary from all texts
        all_words = set()
        for text in texts:
            words = re.findall(r'\b\w+\b', text.lower())
            all_words.update(words)
        
        word_to_idx = {word: idx for idx, word in enumerate(sorted(all_words))}
        
        # Create feature vectors
        cluster_embeddings = {}
        for i, cluster_id in enumerate(cluster_ids):
            text = texts[i]
            words = re.findall(r'\b\w+\b', text.lower())
            word_counts = Counter(words)
            
            # Create feature vector
            vector = np.zeros(len(word_to_idx))
            for word, count in word_counts.items():
                if word in word_to_idx:
                    vector[word_to_idx[word]] = count
            
            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            cluster_embeddings[cluster_id] = vector
        
        embeddings_array = np.array(list(cluster_embeddings.values()))
        logger.info(f"Computed embeddings using TF-IDF: {embeddings_array.shape}")
        return cluster_embeddings, cluster_ids
    
    def _apply_umap_reduction(self, cluster_embeddings: Dict[str, np.ndarray], cluster_ids: List[str]) -> Dict[str, Tuple[float, float]]:
        """Apply UMAP dimensionality reduction to get 2D coordinates."""
        if len(cluster_embeddings) == 0:
            logger.warning("No embeddings available, using random coordinates")
            return {cid: (np.random.uniform(-1, 1), np.random.uniform(-1, 1)) for cid in cluster_ids}
        
        # Convert to numpy array for UMAP
        embeddings_array = np.array([cluster_embeddings[cluster_id] for cluster_id in cluster_ids])
        
        try:
            if UMAP_AVAILABLE:
                # Use UMAP for dimensionality reduction
                reducer = umap.UMAP(
                    n_components=2,
                    random_state=42,
                    n_neighbors=min(15, len(embeddings_array) - 1),
                    min_dist=0.1
                )
                coords = reducer.fit_transform(embeddings_array)
                logger.info("Applied UMAP reduction successfully")
            elif SKLEARN_AVAILABLE:
                # Use TSNE as fallback
                reducer = TSNE(n_components=2, random_state=42)
                coords = reducer.fit_transform(embeddings_array)
                logger.info("Applied TSNE reduction successfully")
            else:
                # Random fallback
                coords = np.random.uniform(-1, 1, (len(embeddings_array), 2))
                logger.warning("Using random coordinates as fallback")
            
            # Create mapping from cluster_id to coordinates
            coordinates = {}
            for i, cluster_id in enumerate(cluster_ids):
                coordinates[cluster_id] = (float(coords[i, 0]), float(coords[i, 1]))
            
            return coordinates
            
        except Exception as e:
            logger.error(f"Dimensionality reduction failed: {e}")
            # Fallback to random coordinates
            return {cid: (np.random.uniform(-1, 1), np.random.uniform(-1, 1)) for cid in cluster_ids}
    
    def _create_positioning_data(self, summaries: Dict, coordinates: Dict[str, Tuple[float, float]]) -> List[Dict]:
        """Create positioning data with proper hash connections."""
        positioning_data = []
        
        for cluster_id, summary in summaries.items():
            if cluster_id not in coordinates:
                continue
            
            x, y = coordinates[cluster_id]
            
            # Generate summary hash for connection
            summary_content = json.dumps(summary, sort_keys=True)
            summary_hash = hashlib.sha256(summary_content.encode()).hexdigest()
            
            # Generate positioning hash
            positioning_hash = self._generate_positioning_hash(cluster_id, summary_hash)
            
            positioning_entry = {
                'cluster_id': cluster_id,
                'cluster_hash': cluster_id,  # cluster_id serves as the cluster hash
                'x': x,
                'y': y,
                'summary_hash': summary_hash,
                'positioning_hash': positioning_hash,
                'timestamp': datetime.now().isoformat()
            }
            
            positioning_data.append(positioning_entry)
        
        return positioning_data
    
    def process_clusters_to_positions(self, force_reprocess: bool = False) -> Dict:
        """Process clusters into 2D positions."""
        logger.info("🚀 Starting cluster positioning...")
        
        # Load existing positions
        positions_file = self.output_dir / "cluster_positions.jsonl"
        existing_positions = self._load_existing_positions(positions_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_positioning_hashes()
            logger.info(f"Found {len(processed_hashes)} existing positioning hashes")
        
        # Load cluster summaries
        summaries = self._load_cluster_summaries()
        
        if not summaries:
            logger.warning("No cluster summaries found")
            return {'status': 'no_summaries'}
        
        # Compute embeddings for summaries
        cluster_embeddings, cluster_ids = self._compute_summary_embeddings(summaries)
        
        if len(cluster_embeddings) == 0:
            logger.warning("No embeddings computed")
            return {'status': 'no_embeddings'}
        
        # Apply dimensionality reduction
        coordinates = self._apply_umap_reduction(cluster_embeddings, cluster_ids)
        
        # Save embeddings
        self._save_cluster_summary_embeddings(cluster_embeddings)

        # Create positioning data
        positioning_data = self._create_positioning_data(summaries, coordinates)
        
        # Filter for new positions
        new_positions = []
        processed_positioning_hashes = set()
        
        for position in positioning_data:
            positioning_hash = position['positioning_hash']
            
            if positioning_hash not in processed_hashes or force_reprocess:
                new_positions.append(position)
                processed_positioning_hashes.add(positioning_hash)
            else:
                logger.info(f"Cluster {position['cluster_id']} already positioned, skipping")
        
        if not new_positions and not force_reprocess:
            logger.info("No new clusters to position")
            return {'status': 'no_new_positions'}
        
        # Combine existing and new positions
        all_positions = list(existing_positions.values()) + new_positions
        
        # Save positions
        with jsonlines.open(positions_file, mode='w') as writer:
            for position in all_positions:
                writer.write(position)
        
        # Save hashes and metadata
        all_processed_hashes = processed_hashes.union(processed_positioning_hashes)
        self._save_processed_positioning_hashes(all_processed_hashes)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_clusters': len(all_positions),
            'new_positions': len(new_positions),
            'existing_positions': len(existing_positions),
            'processed_clusters': len(processed_positioning_hashes)
        }
        
        self._save_metadata(stats)
        
        logger.info(f"✅ Cluster positioning complete: {len(new_positions)} new positions created")
        return stats


@click.command()
@click.option('--cluster-summaries-file', 
              default='data/processed/cluster_summarization/cluster_summaries.json',
              help='Input cluster summaries file')
@click.option('--force', is_flag=True, help='Force reprocess all clusters')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(cluster_summaries_file: str, force: bool, check_only: bool):
    """Run cluster positioning."""
    if check_only:
        logger.info("🔍 Checking setup...")
        
        # Check input files
        summaries_file = Path(cluster_summaries_file)
        if not summaries_file.exists():
            logger.error(f"❌ Cluster summaries file not found: {summaries_file}")
            return
        
        logger.info("✅ Setup check passed")
        return
    
    # Run positioning
    positioner = ClusterPositioner(cluster_summaries_file)
    result = positioner.process_clusters_to_positions(force)
    
    if result['status'] == 'success':
        logger.info("🎉 Cluster positioning completed successfully!")
    else:
        logger.error(f"❌ Cluster positioning failed: {result['status']}")


if __name__ == "__main__":
    main() 