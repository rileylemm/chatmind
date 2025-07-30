#!/usr/bin/env python3
"""
Apply Semantic Positioning to Topic Nodes

This script:
1. Loads tagged chunks from data/processed/tagging/tagged_chunks.jsonl
2. Aggregates topics by combining related text
3. Computes TF-IDF or embeddings for each topic
4. Applies UMAP to generate 2D coordinates
5. Attaches x/y coordinates to topic nodes
6. Saves updated data to data/processed/positioning/topics_with_coords.jsonl

Uses modular directory structure: data/processed/positioning/
"""

import jsonlines
import json
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import numpy as np
import click
from datetime import datetime

# Import for TF-IDF and dimensionality reduction
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.manifold import TSNE
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, will use fallback methods")

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logging.warning("UMAP not available, will use TSNE or random fallback")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_metadata(stats: Dict, metadata_file: Path) -> None:
    """Save processing metadata."""
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'step': 'positioning',
        'stats': stats,
        'version': '1.0'
    }
    try:
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_file}")
    except Exception as e:
        logger.error(f"Failed to save metadata: {e}")


def load_tagged_chunks(file_path: Path) -> List[Dict]:
    """Load tagged chunks from JSONL file."""
    chunks = []
    try:
        with jsonlines.open(file_path) as reader:
            for chunk in reader:
                chunks.append(chunk)
        logger.info(f"Loaded {len(chunks)} tagged chunks")
        return chunks
    except Exception as e:
        logger.error(f"Failed to load tagged chunks: {e}")
        return []


def aggregate_topics(chunks: List[Dict]) -> Dict[str, Dict]:
    """
    Aggregate chunks by topic, combining text content.
    
    Returns:
        Dict mapping topic_id to topic data with combined text
    """
    topics = defaultdict(lambda: {
        'topic_id': None,
        'combined_text': [],
        'chunk_count': 0,
        'tags': set(),
        'cluster_id': None
    })
    
    for chunk in chunks:
        # Get topic from tags or use cluster_id as fallback
        topic_id = None
        chunk_tags = chunk.get('tags', [])
        
        # Look for topic tags (you might need to adjust this based on your tag structure)
        for tag in chunk_tags:
            if tag.startswith('topic:') or tag.startswith('subject:'):
                topic_id = tag
                break
        
        # Fallback to cluster_id if no topic tag found
        if not topic_id:
            topic_id = f"cluster_{chunk.get('cluster_id', 'unknown')}"
        
        # Aggregate data
        topics[topic_id]['topic_id'] = topic_id
        topics[topic_id]['combined_text'].append(chunk.get('content', ''))
        topics[topic_id]['chunk_count'] += 1
        topics[topic_id]['tags'].update(chunk_tags)
        topics[topic_id]['cluster_id'] = chunk.get('cluster_id')
    
    # Convert sets to lists for JSON serialization
    for topic in topics.values():
        topic['tags'] = list(topic['tags'])
        topic['combined_text'] = ' '.join(topic['combined_text'])
    
    logger.info(f"Aggregated {len(topics)} topics")
    return dict(topics)


def compute_tfidf_embeddings(topics: Dict[str, Dict]) -> Tuple[np.ndarray, List[str]]:
    """
    Compute TF-IDF embeddings for topic texts.
    
    Returns:
        Tuple of (tfidf_matrix, topic_ids)
    """
    if not SKLEARN_AVAILABLE:
        logger.error("scikit-learn not available for TF-IDF computation")
        return np.array([]), []
    
    topic_ids = list(topics.keys())
    texts = [topics[tid]['combined_text'] for tid in topic_ids]
    
    # Compute TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        min_df=2,
        max_df=0.95
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(texts)
        logger.info(f"Computed TF-IDF matrix: {tfidf_matrix.shape}")
        return tfidf_matrix.toarray(), topic_ids
    except Exception as e:
        logger.error(f"TF-IDF computation failed: {e}")
        return np.array([]), []


def apply_umap_reduction(embeddings: np.ndarray, topic_ids: List[str]) -> Dict[str, Tuple[float, float]]:
    """
    Apply UMAP dimensionality reduction to get 2D coordinates.
    
    Returns:
        Dict mapping topic_id to (x, y) coordinates
    """
    if len(embeddings) == 0:
        logger.warning("No embeddings available, using random coordinates")
        return {tid: (np.random.uniform(-1, 1), np.random.uniform(-1, 1)) for tid in topic_ids}
    
    try:
        if UMAP_AVAILABLE:
            # Use UMAP for dimensionality reduction
            reducer = umap.UMAP(
                n_components=2,
                random_state=42,
                n_neighbors=min(15, len(embeddings) - 1),
                min_dist=0.1
            )
            coords = reducer.fit_transform(embeddings)
            logger.info("Applied UMAP reduction successfully")
        elif SKLEARN_AVAILABLE:
            # Fallback to TSNE
            reducer = TSNE(n_components=2, random_state=42, perplexity=min(30, len(embeddings) - 1))
            coords = reducer.fit_transform(embeddings)
            logger.info("Applied TSNE reduction (UMAP fallback)")
        else:
            # Final fallback: random coordinates
            coords = np.random.uniform(-1, 1, (len(embeddings), 2))
            logger.info("Used random coordinates (no dimensionality reduction available)")
        
        # Create mapping of topic_id to coordinates
        topic_coords = {}
        for i, topic_id in enumerate(topic_ids):
            topic_coords[topic_id] = (float(coords[i, 0]), float(coords[i, 1]))
        
        return topic_coords
        
    except Exception as e:
        logger.error(f"Dimensionality reduction failed: {e}")
        # Fallback to random coordinates
        return {tid: (np.random.uniform(-1, 1), np.random.uniform(-1, 1)) for tid in topic_ids}


def attach_coordinates_to_topics(topics: Dict[str, Dict], coordinates: Dict[str, Tuple[float, float]]) -> Dict[str, Dict]:
    """
    Attach x/y coordinates to topic data.
    
    Returns:
        Updated topics dict with coordinates
    """
    for topic_id, topic_data in topics.items():
        if topic_id in coordinates:
            x, y = coordinates[topic_id]
            topic_data['x'] = x
            topic_data['y'] = y
        else:
            # Fallback coordinates
            topic_data['x'] = 0.0
            topic_data['y'] = 0.0
    
    return topics


def save_topics_with_coords(topics: Dict[str, Dict], output_path: Path) -> None:
    """Save topics with coordinates to JSONL file."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with jsonlines.open(output_path, mode='w') as writer:
            for topic_data in topics.values():
                writer.write(topic_data)
        
        logger.info(f"Saved {len(topics)} topics with coordinates to {output_path}")
        
        # Save metadata
        stats = {
            'total_topics': len(topics),
            'topics_with_coordinates': sum(1 for t in topics.values() if 'x' in t and 'y' in t),
            'average_chunk_count': sum(t.get('chunk_count', 0) for t in topics.values()) / len(topics) if topics else 0,
            'total_tags': sum(len(t.get('tags', [])) for t in topics.values())
        }
        
        metadata_file = output_path.parent / "metadata.json"
        save_metadata(stats, metadata_file)
        
    except Exception as e:
        logger.error(f"Failed to save topics with coordinates: {e}")


def apply_topic_layout(input_file: Path = None, output_file: Path = None) -> bool:
    """
    Main function to apply semantic positioning to topic nodes.
    
    Args:
        input_file: Path to tagged chunks JSONL file
        output_file: Path to save topics with coordinates
        
    Returns:
        True if successful, False otherwise
    """
    if input_file is None:
        input_file = Path("data/processed/tagging/tagged_chunks.jsonl")
    
    if output_file is None:
        output_file = Path("data/processed/positioning/topics_with_coords.jsonl")
    
    logger.info("🎯 Starting semantic positioning for topic nodes...")
    
    # Step 1: Load tagged chunks
    logger.info("📥 Step 1: Loading tagged chunks...")
    chunks = load_tagged_chunks(input_file)
    if not chunks:
        logger.error("No chunks loaded, aborting")
        return False
    
    # Step 2: Aggregate topics
    logger.info("🔗 Step 2: Aggregating topics...")
    topics = aggregate_topics(chunks)
    if not topics:
        logger.error("No topics aggregated, aborting")
        return False
    
    # Step 3: Compute embeddings
    logger.info("🧠 Step 3: Computing TF-IDF embeddings...")
    embeddings, topic_ids = compute_tfidf_embeddings(topics)
    
    # Step 4: Apply UMAP reduction
    logger.info("🗺️ Step 4: Applying UMAP dimensionality reduction...")
    coordinates = apply_umap_reduction(embeddings, topic_ids)
    
    # Step 5: Attach coordinates to topics
    logger.info("📍 Step 5: Attaching coordinates to topics...")
    topics_with_coords = attach_coordinates_to_topics(topics, coordinates)
    
    # Step 6: Save results
    logger.info("💾 Step 6: Saving topics with coordinates...")
    save_topics_with_coords(topics_with_coords, output_file)
    
    logger.info("✅ Semantic positioning completed successfully!")
    return True


@click.command()
@click.option('--input', 'input_file', type=click.Path(exists=True), 
              default='data/processed/tagging/processed_tagged_chunks.jsonl',
              help='Input processed tagged chunks JSONL file')
@click.option('--output', 'output_file', type=click.Path(), 
              default='data/processed/positioning/topics_with_coords.jsonl',
              help='Output topics with coordinates JSONL file')
@click.option('--force', is_flag=True, help='Force reprocess even if output exists')
def main(input_file: str, output_file: str, force: bool):
    """Apply semantic positioning to topic nodes."""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # Check if output already exists
    if output_path.exists() and not force:
        logger.info(f"Output file {output_path} already exists. Use --force to reprocess.")
        return
    
    success = apply_topic_layout(input_path, output_path)
    
    if success:
        logger.info("🎉 Semantic positioning completed successfully!")
        logger.info(f"📁 Output saved to: {output_path}")
    else:
        logger.error("❌ Semantic positioning failed!")
        exit(1)


if __name__ == "__main__":
    main() 