#!/usr/bin/env python3
"""
ChatMind Chat Positioning

Creates 2D coordinates for chats using their summaries.
Uses chat summaries from chat_summarization step.
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
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatPositioner:
    """Creates 2D coordinates for chats using their summaries."""
    
    def __init__(self, 
                 chat_summaries_file: str = "data/processed/chat_summarization/chat_summaries.json"):
        self.chat_summaries_file = Path(chat_summaries_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/positioning")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_positioning_hash(self, chat_id: str, summary_hash: str) -> str:
        """Generate a hash for chat positioning to track if it's been processed."""
        # Create a normalized version for hashing
        normalized_positioning = {
            'chat_id': chat_id,
            'summary_hash': summary_hash
        }
        content = json.dumps(normalized_positioning, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_positioning_hashes(self) -> Set[str]:
        """Load hashes of chats that have already been positioned."""
        hash_file = self.output_dir / "chat_positioning_hashes.pkl"
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
        """Save hashes of processed chat positioning."""
        hash_file = self.output_dir / "chat_positioning_hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} positioning hashes")
        except Exception as e:
            logger.error(f"Failed to save positioning hashes: {e}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata_file = self.output_dir / "chat_positioning_metadata.json"
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'chat_positioning',
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
        """Load existing chat positions from file."""
        positions = {}
        if positions_file.exists():
            with jsonlines.open(positions_file) as reader:
                for position in reader:
                    chat_id = position.get('chat_id')
                    if chat_id:
                        positions[chat_id] = position
            logger.info(f"Loaded {len(positions)} existing chat positions")
        return positions
    
    def _load_chat_summaries(self) -> Dict:
        """Load chat summaries from file."""
        summaries = {}
        if self.chat_summaries_file.exists():
            with open(self.chat_summaries_file, 'r') as f:
                summaries = json.load(f)
            logger.info(f"Loaded {len(summaries)} chat summaries")
        return summaries
    
    def _load_chats(self) -> Dict[str, Dict]:
        """Load chats from ingestion step."""
        chats = {}
        
        # This function is no longer used as input is simplified
        # if self.chats_file.exists():
        #     with jsonlines.open(self.chats_file) as reader:
        #         for chat in reader:
        #             chat_id = chat.get('content_hash', 'unknown')
        #             chats[chat_id] = chat
            
        #     logger.info(f"Loaded {len(chats)} chats")
        # else:
        #     logger.warning("Chats file not found")
        
        return chats
    
    def _load_clustered_embeddings(self) -> Dict[str, int]:
        """Load cluster assignments for chunks."""
        cluster_assignments = {}
        
        # This function is no longer used as input is simplified
        # if self.clustered_embeddings_file.exists():
        #     with jsonlines.open(self.clustered_embeddings_file) as reader:
        #         for item in reader:
        #             chunk_hash = item.get('chunk_hash')
        #             cluster_id = item.get('cluster_id')
                    
        #             if chunk_hash and cluster_id is not None:
        #                 cluster_assignments[chunk_hash] = cluster_id
            
        #     logger.info(f"Loaded cluster assignments for {len(cluster_assignments)} chunks")
        # else:
        #     logger.warning("Clustered embeddings file not found")
        
        return cluster_assignments
    
    def _save_chat_summary_embeddings(self, chat_embeddings: Dict[str, np.ndarray]) -> None:
        """Save chat summary embeddings alongside positions."""
        embeddings_file = self.output_dir / "chat_summary_embeddings.jsonl"
        
        with jsonlines.open(embeddings_file, 'w') as writer:
            for chat_id, embedding in chat_embeddings.items():
                writer.write({
                    'chat_id': chat_id,
                    'embedding': embedding.tolist(),
                    'hash': self._generate_content_hash({
                        'chat_id': chat_id,
                        'embedding': embedding.tolist()
                    })
                })
        
        logger.info(f"💾 Saved chat summary embeddings to {embeddings_file}")
    
    def _generate_content_hash(self, data: Dict) -> str:
        """Generate a content hash for tracking."""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _compute_summary_embeddings(self, summaries: Dict) -> Tuple[Dict[str, np.ndarray], List[str]]:
        """Compute embeddings for chat summaries using TF-IDF or embedding models."""
        if not summaries:
            return {}, []
        
        chat_ids = list(summaries.keys())
        texts = []
        
        for chat_id in chat_ids:
            summary = summaries[chat_id]
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
            valid_chat_ids = []
            
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
                
                valid_chat_ids.append(chat_ids[i])
            
            # Generate embeddings
            embeddings = model.encode(processed_texts, convert_to_numpy=True)
            logger.info(f"Generated embeddings using sentence-transformers: {embeddings.shape}")
            
            # Create chat_id to embedding mapping
            chat_embeddings = {}
            for i, chat_id in enumerate(valid_chat_ids):
                chat_embeddings[chat_id] = embeddings[i]
            
            return chat_embeddings, valid_chat_ids
            
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
        chat_embeddings = {}
        for i, chat_id in enumerate(chat_ids):
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
            
            chat_embeddings[chat_id] = vector
        
        embeddings_array = np.array(list(chat_embeddings.values()))
        logger.info(f"Computed embeddings using TF-IDF: {embeddings_array.shape}")
        return chat_embeddings, chat_ids
    
    def _apply_umap_reduction(self, chat_embeddings: Dict[str, np.ndarray], chat_ids: List[str]) -> Dict[str, Tuple[float, float]]:
        """Apply UMAP dimensionality reduction to get 2D coordinates."""
        if len(chat_embeddings) == 0:
            logger.warning("No embeddings available, using random coordinates")
            return {cid: (np.random.uniform(-1, 1), np.random.uniform(-1, 1)) for cid in chat_ids}
        
        # Convert to numpy array for UMAP
        embeddings_array = np.array([chat_embeddings[chat_id] for chat_id in chat_ids])
        
        try:
            # Import UMAP
            try:
                import umap
                reducer = umap.UMAP(
                    n_components=2,
                    random_state=42,
                    n_neighbors=min(15, len(embeddings_array) - 1),
                    min_dist=0.1
                )
                coords = reducer.fit_transform(embeddings_array)
                logger.info("Applied UMAP reduction successfully")
            except ImportError:
                # Fallback to random coordinates
                coords = np.random.uniform(-1, 1, (len(embeddings_array), 2))
                logger.warning("UMAP not available, using random coordinates")
            
            # Create mapping from chat_id to coordinates
            coordinates = {}
            for i, chat_id in enumerate(chat_ids):
                coordinates[chat_id] = (float(coords[i, 0]), float(coords[i, 1]))
            
            return coordinates
            
        except Exception as e:
            logger.error(f"Dimensionality reduction failed: {e}")
            return {}
    
    def _create_positioning_data(self, 
                                summaries: Dict,
                                coordinates: Dict[str, Tuple[float, float]]) -> List[Dict]:
        """Create positioning data with proper hash connections."""
        positioning_data = []
        
        for chat_id, summary in summaries.items():
            if chat_id not in coordinates:
                continue
            
            x, y = coordinates[chat_id]
            
            # Generate summary hash for connection
            summary_content = json.dumps(summary, sort_keys=True)
            summary_hash = hashlib.sha256(summary_content.encode()).hexdigest()
            
            # Get chat data
            # chat = chats.get(chat_id, {}) # This line is no longer needed
            
            # Get cluster assignments for this chat's chunks (if available)
            # This would require mapping chat_id to chunk_hashes, which we don't have directly
            # For now, we'll skip cluster assignment
            primary_cluster = None
            
            # Generate positioning hash
            positioning_hash = self._generate_positioning_hash(chat_id, summary_hash)
            
            positioning_entry = {
                'chat_id': chat_id,
                'chat_hash': chat_id,  # chat_id IS the content_hash from original chats
                'x': x,
                'y': y,
                'umap_x': x,
                'umap_y': y,
                'primary_cluster': primary_cluster,
                'summary_hash': summary_hash,
                'positioning_hash': positioning_hash,
                'timestamp': datetime.now().isoformat()
            }
            
            positioning_data.append(positioning_entry)
        
        return positioning_data
    
    def process_chats_to_positions(self, force_reprocess: bool = False) -> Dict:
        """Process chats into 2D positions using their summaries."""
        logger.info("🚀 Starting chat positioning using summaries...")
        
        # Load existing positions
        positions_file = self.output_dir / "chat_positions.jsonl"
        existing_positions = self._load_existing_positions(positions_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_positioning_hashes()
            logger.info(f"Found {len(processed_hashes)} existing positioning hashes")
        
        # Load data
        summaries = self._load_chat_summaries()
        # chats = self._load_chats() # This line is no longer needed
        # cluster_assignments = self._load_clustered_embeddings() # This line is no longer needed
        
        if not summaries:
            logger.warning("No chat summaries found")
            return {'status': 'no_summaries'}
        
        # if not chats: # This line is no longer needed
        #     logger.warning("No chats found")
        #     return {'status': 'no_chats'}
        
        # Compute embeddings for summaries
        chat_embeddings, chat_ids = self._compute_summary_embeddings(summaries)
        
        if not chat_embeddings:
            logger.warning("No embeddings computed")
            return {'status': 'no_embeddings'}
        
        # Save embeddings
        self._save_chat_summary_embeddings(chat_embeddings)

        # Apply dimensionality reduction
        coordinates = self._apply_umap_reduction(chat_embeddings, chat_ids)
        
        if not coordinates:
            logger.warning("No coordinates computed")
            return {'status': 'no_coordinates'}
        
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
                logger.info(f"Chat {position['chat_id']} already positioned, skipping")
        
        if not new_positions and not force_reprocess:
            logger.info("No new chats to position")
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
            'total_chats': len(all_positions),
            'new_positions': len(new_positions),
            'existing_positions': len(existing_positions),
            'processed_chats': len(processed_positioning_hashes)
        }
        
        self._save_metadata(stats)
        
        logger.info(f"✅ Chat positioning complete: {len(new_positions)} new positions created")
        return stats


@click.command()
@click.option('--chat-summaries-file', 
              default='data/processed/chat_summarization/chat_summaries.json',
              help='Input chat summaries file')
# @click.option('--chats-file', 
#               default='data/processed/ingestion/chats.jsonl', # This option is no longer needed
#               help='Input chats file')
# @click.option('--clustered-embeddings-file', 
#               default='data/processed/clustering/clustered_embeddings.jsonl', # This option is no longer needed
#               help='Input clustered embeddings file')
@click.option('--force', is_flag=True, help='Force reprocess all chats')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(chat_summaries_file: str, force: bool, check_only: bool):
    """Run chat positioning using summaries."""
    if check_only:
        logger.info("🔍 Checking setup...")
        
        # Check input files
        summaries_path = Path(chat_summaries_file)
        # chats_path = Path(chats_file) # This line is no longer needed
        # clustered_path = Path(clustered_embeddings_file) # This line is no longer needed
        
        if not summaries_path.exists():
            logger.error(f"❌ Chat summaries file not found: {summaries_path}")
            return
        
        # if not chats_path.exists(): # This line is no longer needed
        #     logger.error(f"❌ Chats file not found: {chats_path}")
        #     return
        
        # if not clustered_path.exists(): # This line is no longer needed
        #     logger.warning(f"⚠️ Clustered embeddings file not found: {clustered_path}")
        
        logger.info("✅ Setup check passed")
        return
    
    # Run positioning
    positioner = ChatPositioner(chat_summaries_file)
    result = positioner.process_chats_to_positions(force)
    
    if result['status'] == 'success':
        logger.info("🎉 Chat positioning completed successfully!")
    else:
        logger.error(f"❌ Chat positioning failed: {result['status']}")


if __name__ == "__main__":
    main() 