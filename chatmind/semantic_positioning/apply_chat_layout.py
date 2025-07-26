#!/usr/bin/env python3
"""
Apply Semantic Positioning to Chat Nodes

This script:
1. Loads processed tagged chunks and topic coordinates
2. Aggregates chat data and computes chat-level embeddings (by averaging message embeddings)
3. Groups chats by topic and applies UMAP to generate 2D coordinates relative to each topic
4. Saves chat coordinates to data/processed/chats_with_coords.jsonl
"""

import jsonlines
import json
import logging
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import numpy as np
import click
from tqdm import tqdm

# Import for dimensionality reduction
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False
    logging.warning("UMAP not available, will use TSNE or random fallback")

try:
    from sklearn.manifold import TSNE
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available, will use random fallback")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_processed_chunks(file_path: Path) -> List[Dict]:
    """Load processed tagged chunks from JSONL file."""
    chunks = []
    try:
        with jsonlines.open(file_path) as reader:
            for chunk in reader:
                chunks.append(chunk)
        logger.info(f"Loaded {len(chunks)} processed chunks")
        return chunks
    except Exception as e:
        logger.error(f"Failed to load processed chunks: {e}")
        return []


def load_topic_coordinates(file_path: Path) -> Dict[str, Tuple[float, float]]:
    """Load topic coordinates from JSONL file."""
    topic_coords = {}
    try:
        with jsonlines.open(file_path) as reader:
            for topic in reader:
                topic_id = topic.get('topic_id')
                x = topic.get('x')
                y = topic.get('y')
                if topic_id and x is not None and y is not None:
                    topic_coords[topic_id] = (x, y)
        logger.info(f"Loaded coordinates for {len(topic_coords)} topics")
        return topic_coords
    except Exception as e:
        logger.error(f"Failed to load topic coordinates: {e}")
        return {}


def aggregate_chats_by_topic(chunks: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group chunks by chat and then by topic.
    
    Returns:
        Dict mapping topic_id to list of chat data
    """
    # First, group chunks by chat
    chats = defaultdict(lambda: {
        'chat_id': None,
        'chat_title': '',
        'messages': [],
        'embeddings': [],
        'topic_id': None
    })
    
    for chunk in chunks:
        chat_id = chunk.get('chat_id')
        if not chat_id:
            continue
            
        # Initialize chat if not seen
        if chats[chat_id]['chat_id'] is None:
            chats[chat_id]['chat_id'] = chat_id
            chats[chat_id]['chat_title'] = chunk.get('chat_title', '')
        
        # Add message content
        content = chunk.get('content', '')
        if content:
            chats[chat_id]['messages'].append(content)
        
        # Add embedding if available
        if 'embedding' in chunk:
            chats[chat_id]['embeddings'].append(chunk['embedding'])
        
        # Determine topic (use cluster_id as fallback)
        topic_id = None
        chunk_tags = chunk.get('tags', [])
        
        # Look for topic tags
        for tag in chunk_tags:
            if tag.startswith('topic:') or tag.startswith('subject:'):
                topic_id = tag
                break
        
        # Fallback to cluster_id if no topic tag found
        if not topic_id:
            topic_id = f"cluster_{chunk.get('cluster_id', 'unknown')}"
        
        chats[chat_id]['topic_id'] = topic_id
    
    # Now group chats by topic
    topics = defaultdict(list)
    for chat_data in chats.values():
        topic_id = chat_data['topic_id']
        if topic_id:
            topics[topic_id].append(chat_data)
    
    logger.info(f"Aggregated {len(chats)} chats into {len(topics)} topics")
    return dict(topics)


def compute_chat_embeddings(chats_by_topic: Dict[str, List[Dict]]) -> Dict[str, np.ndarray]:
    """
    Compute chat-level embeddings by averaging message embeddings.
    
    Returns:
        Dict mapping chat_id to chat embedding
    """
    chat_embeddings = {}
    
    for topic_id, chats in chats_by_topic.items():
        for chat in chats:
            chat_id = chat['chat_id']
            embeddings = chat.get('embeddings', [])
            
            if not embeddings:
                logger.warning(f"No embeddings found for chat {chat_id}")
                continue
            
            # Convert embeddings to numpy array and average them
            try:
                embedding_arrays = [np.array(emb) for emb in embeddings]
                chat_embedding = np.mean(embedding_arrays, axis=0)
                chat_embeddings[chat_id] = chat_embedding
            except Exception as e:
                logger.warning(f"Failed to compute embedding for chat {chat_id}: {e}")
                continue
    
    logger.info(f"Computed embeddings for {len(chat_embeddings)} chats")
    return chat_embeddings


def apply_umap_to_chats_in_topic(
    chat_embeddings: Dict[str, np.ndarray],
    chats_in_topic: List[Dict],
    topic_coords: Tuple[float, float],
    n_neighbors: int = 15,
    min_dist: float = 0.1
) -> Dict[str, Tuple[float, float]]:
    """
    Apply UMAP positioning to chats within a topic.
    
    Args:
        chat_embeddings: Dict mapping chat_id to embedding array
        chats_in_topic: List of chat data for this topic
        topic_coords: (x, y) coordinates of the topic center
        n_neighbors: UMAP parameter
        min_dist: UMAP parameter
    
    Returns:
        Dict mapping chat_id to (x, y) coordinates
    """
    if not chats_in_topic:
        return {}
    
    # Extract embeddings for chats in this topic
    chat_ids = [chat['chat_id'] for chat in chats_in_topic]
    embeddings_list = []
    valid_chat_ids = []
    
    for chat_id in chat_ids:
        if chat_id in chat_embeddings:
            embeddings_list.append(chat_embeddings[chat_id])
            valid_chat_ids.append(chat_id)
    
    if not embeddings_list:
        logger.warning(f"No valid embeddings found for topic")
        return {}
    
    embeddings_array = np.array(embeddings_list)
    
    # Handle small clusters (less than 2 points)
    if len(embeddings_array) < 2:
        logger.warning(f"Topic has only {len(embeddings_array)} chats, using random positioning")
        chat_coords = {}
        for i, chat_id in enumerate(valid_chat_ids):
            # Add small random offset around topic center
            offset_x = np.random.uniform(-0.1, 0.1)
            offset_y = np.random.uniform(-0.1, 0.1)
            chat_coords[chat_id] = (float(topic_coords[0] + offset_x), float(topic_coords[1] + offset_y))
        return chat_coords
    
    # Handle small clusters (2-4 points) with TSNE instead of UMAP
    if len(embeddings_array) <= 4:
        logger.info(f"Topic has {len(embeddings_array)} chats, using TSNE instead of UMAP")
        try:
            from sklearn.manifold import TSNE
            reducer = TSNE(n_components=2, random_state=42, perplexity=min(len(embeddings_array)-1, 2))
            coords_2d = reducer.fit_transform(embeddings_array)
        except Exception as e:
            logger.warning(f"TSNE failed for small cluster: {e}, using random positioning")
            chat_coords = {}
            for i, chat_id in enumerate(valid_chat_ids):
                offset_x = np.random.uniform(-0.1, 0.1)
                offset_y = np.random.uniform(-0.1, 0.1)
                chat_coords[chat_id] = (float(topic_coords[0] + offset_x), float(topic_coords[1] + offset_y))
            return chat_coords
    else:
        # Use UMAP for larger clusters
        try:
            # Adjust n_neighbors for small clusters
            adjusted_n_neighbors = min(n_neighbors, len(embeddings_array) - 1)
            if adjusted_n_neighbors < 2:
                adjusted_n_neighbors = 2
            
            reducer = umap.UMAP(
                n_components=2,
                n_neighbors=adjusted_n_neighbors,
                min_dist=min_dist,
                random_state=42,
                n_jobs=1  # Force single-threaded to avoid warnings
            )
            coords_2d = reducer.fit_transform(embeddings_array)
        except Exception as e:
            logger.warning(f"UMAP failed for topic: {e}, falling back to TSNE")
            try:
                from sklearn.manifold import TSNE
                reducer = TSNE(n_components=2, random_state=42, perplexity=min(len(embeddings_array)-1, 30))
                coords_2d = reducer.fit_transform(embeddings_array)
            except Exception as e2:
                logger.warning(f"TSNE also failed: {e2}, using random positioning")
                chat_coords = {}
                for i, chat_id in enumerate(valid_chat_ids):
                    offset_x = np.random.uniform(-0.1, 0.1)
                    offset_y = np.random.uniform(-0.1, 0.1)
                    chat_coords[chat_id] = (float(topic_coords[0] + offset_x), float(topic_coords[1] + offset_y))
                return chat_coords
    
    # Scale coordinates to be relative to topic center
    # Normalize to small range around topic center
    coords_2d = coords_2d * 0.1  # Scale down to small area
    
    # Create result dict
    chat_coords = {}
    for i, chat_id in enumerate(valid_chat_ids):
        x = float(topic_coords[0] + coords_2d[i, 0])  # Convert to Python float
        y = float(topic_coords[1] + coords_2d[i, 1])  # Convert to Python float
        chat_coords[chat_id] = (x, y)
    
    return chat_coords


def apply_chat_layout(
    chunks_file: Path,
    topics_coords_file: Path,
    output_file: Path
) -> bool:
    """
    Main function to apply semantic positioning to chat nodes.
    
    Args:
        chunks_file: Path to processed tagged chunks JSONL file
        topics_coords_file: Path to topics with coordinates JSONL file
        output_file: Path to save chats with coordinates
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("🎯 Starting semantic positioning for chat nodes...")
    
    # Step 1: Load processed chunks
    logger.info("📥 Step 1: Loading processed chunks...")
    chunks = load_processed_chunks(chunks_file)
    if not chunks:
        logger.error("No chunks loaded, aborting")
        return False
    
    # Step 2: Load topic coordinates
    logger.info("🗺️ Step 2: Loading topic coordinates...")
    topic_coords = load_topic_coordinates(topics_coords_file)
    if not topic_coords:
        logger.error("No topic coordinates loaded, aborting")
        return False
    
    # Step 3: Aggregate chats by topic
    logger.info("🔗 Step 3: Aggregating chats by topic...")
    chats_by_topic = aggregate_chats_by_topic(chunks)
    if not chats_by_topic:
        logger.error("No chats aggregated, aborting")
        return False
    
    # Step 4: Compute chat embeddings
    logger.info("🧠 Step 4: Computing chat embeddings...")
    chat_embeddings = compute_chat_embeddings(chats_by_topic)
    if not chat_embeddings:
        logger.error("No chat embeddings computed, aborting")
        return False
    
    # Step 5: Apply positioning for each topic
    logger.info("📍 Step 5: Applying positioning for each topic...")
    all_chat_coords = {}
    
    for topic_id, chats_in_topic in tqdm(chats_by_topic.items(), desc="Positioning chats"):
        if topic_id in topic_coords:
            topic_anchor = topic_coords[topic_id]
            chat_coords = apply_umap_to_chats_in_topic(
                chat_embeddings, chats_in_topic, topic_anchor
            )
            all_chat_coords.update(chat_coords)
        else:
            logger.warning(f"No coordinates found for topic {topic_id}")
    
    # Step 6: Save results
    logger.info("💾 Step 6: Saving chats with coordinates...")
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with jsonlines.open(output_file, mode='w') as writer:
            for chat_id, (x, y) in all_chat_coords.items():
                # Find the topic_id for this chat
                topic_id = None
                for topic_chats in chats_by_topic.values():
                    for chat in topic_chats:
                        if chat['chat_id'] == chat_id:
                            topic_id = chat['topic_id']
                            break
                    if topic_id:
                        break
                
                writer.write({
                    'chat_id': chat_id,
                    'topic_id': topic_id,
                    'x': x,
                    'y': y
                })
        
        logger.info(f"Saved coordinates for {len(all_chat_coords)} chats to {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to save chat coordinates: {e}")
        return False
    
    logger.info("✅ Chat semantic positioning completed successfully!")
    return True


@click.command()
@click.option('--chunks-file', type=click.Path(exists=True), 
              default='data/processed/processed_tagged_chunks.jsonl',
              help='Input processed tagged chunks JSONL file')
@click.option('--topics-coords-file', type=click.Path(exists=True), 
              default='data/processed/topics_with_coords.jsonl',
              help='Input topics with coordinates JSONL file')
@click.option('--output-file', type=click.Path(), 
              default='data/processed/chats_with_coords.jsonl',
              help='Output chats with coordinates JSONL file')
@click.option('--force', is_flag=True, help='Force reprocess even if output exists')
def main(chunks_file: str, topics_coords_file: str, output_file: str, force: bool):
    """Apply semantic positioning to chat nodes."""
    
    chunks_path = Path(chunks_file)
    topics_coords_path = Path(topics_coords_file)
    output_path = Path(output_file)
    
    # Check if output already exists
    if output_path.exists() and not force:
        logger.info(f"Output file {output_path} already exists. Use --force to reprocess.")
        return
    
    success = apply_chat_layout(chunks_path, topics_coords_path, output_path)
    
    if success:
        logger.info("🎉 Chat semantic positioning completed successfully!")
        logger.info(f"📁 Output saved to: {output_path}")
    else:
        logger.error("❌ Chat semantic positioning failed!")
        exit(1)


if __name__ == "__main__":
    main() 