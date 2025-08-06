#!/usr/bin/env python3
"""
Qdrant Vector Database Loader

Loads embeddings from the modular pipeline into Qdrant.
Optimized for hybrid architecture with Neo4j for graph relationships.
Uses modular directory structure: data/processed/loading/
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import logging
from tqdm import tqdm
import hashlib
from datetime import datetime
import pickle
import numpy as np

# Import pipeline configuration
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import get_neo4j_config

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("Qdrant client not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantVectorLoader:
    """Qdrant loader for embeddings with cross-reference metadata."""
    
    def __init__(self, 
                 qdrant_url: str = "http://localhost:6335",
                 collection_name: str = "chatmind_embeddings",
                 processed_dir: str = "data/processed"):
        
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        
        # Resolve processed_dir path
        if Path(processed_dir).is_absolute():
            self.processed_dir = Path(processed_dir)
        else:
            # If relative path, find project root and resolve relative to it
            current_dir = Path(__file__).parent
            project_root = None
            
            # Walk up the directory tree to find the project root
            for parent in [current_dir] + list(current_dir.parents):
                if (parent / ".env").exists():
                    project_root = parent
                    break
            
            if project_root is None:
                # Fallback: assume we're in the pipeline directory and go up two levels
                project_root = current_dir.parent.parent
            
            self.processed_dir = project_root / processed_dir
        
        # Debug logging
        logger.info(f"Qdrant connection config:")
        logger.info(f"  URL: {self.qdrant_url}")
        logger.info(f"  Collection: {self.collection_name}")
        logger.info(f"  Processed directory: {self.processed_dir}")
        
        # Use modular directory structure
        self.loading_dir = self.processed_dir / "loading"
        self.loading_dir.mkdir(parents=True, exist_ok=True)
        
        if QDRANT_AVAILABLE:
            self.client = QdrantClient(url=self.qdrant_url)
        else:
            self.client = None
    
    def _generate_content_hash(self, data: Dict) -> str:
        """Generate a content hash for tracking."""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _get_processed_hashes(self) -> Dict[str, set]:
        """Get hashes of already processed data by type."""
        hash_file = self.loading_dir / "qdrant_loading_hashes.pkl"
        if hash_file.exists():
            with open(hash_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_processed_hashes(self, hashes: Dict[str, set]) -> None:
        """Save hashes of processed data by type."""
        hash_file = self.loading_dir / "qdrant_loading_hashes.pkl"
        with open(hash_file, 'wb') as f:
            pickle.dump(hashes, f)
    
    def _generate_data_type_hash(self, data_type: str, items: List[Dict]) -> str:
        """Generate a hash for a specific data type."""
        if not items:
            return hashlib.sha256(f"{data_type}_empty".encode()).hexdigest()
        
        # Create a combined hash for all items in this data type
        content_str = json.dumps([self._generate_content_hash(item) for item in items], sort_keys=True)
        return hashlib.sha256(f"{data_type}_{content_str}".encode()).hexdigest()
    
    def _load_data_file(self, file_path: Path, description: str) -> List[Dict]:
        """Load data from a JSONL file with error handling."""
        data = []
        if file_path.exists():
            try:
                with jsonlines.open(file_path) as reader:
                    for item in reader:
                        data.append(item)
                logger.info(f"✅ Loaded {len(data)} {description}")
            except Exception as e:
                logger.error(f"❌ Failed to load {description}: {e}")
        else:
            logger.warning(f"⚠️  {description} file not found: {file_path}")
        return data
    
    def _load_json_file(self, file_path: Path, description: str) -> Dict:
        """Load data from JSON file."""
        if not file_path.exists():
            logger.warning(f"⚠️  {description} file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"✅ Loaded {description}")
            return data
        except Exception as e:
            logger.error(f"❌ Failed to load {description}: {e}")
            return {}
    
    def _load_embeddings_data(self) -> Dict[str, any]:
        """Load embeddings and related data for Qdrant."""
        logger.info("📖 Loading embeddings data for Qdrant...")
        
        data = {
            # Chunk embeddings data
            'embeddings': self._load_data_file(
                self.processed_dir / "embedding" / "embeddings.jsonl", 
                "embeddings"
            ),
            'clustered_embeddings': self._load_data_file(
                self.processed_dir / "clustering" / "clustered_embeddings.jsonl", 
                "clustered embeddings"
            ),
            'chunks': self._load_data_file(
                self.processed_dir / "chunking" / "chunks.jsonl", 
                "chunks"
            ),
            'tagged_chunks': self._load_data_file(
                self.processed_dir / "tagging" / "chunk_tags.jsonl", 
                "tagged chunks"
            ),
            # Cluster embeddings data
            'cluster_summary_embeddings': self._load_data_file(
                self.processed_dir / "positioning" / "cluster_summary_embeddings.jsonl", 
                "cluster summary embeddings"
            ),
            'cluster_summaries': self._load_json_file(
                self.processed_dir / "cluster_summarization" / "cluster_summaries.json", 
                "cluster summaries"
            ),
            # Chat summary embeddings data
            'chat_summary_embeddings': self._load_data_file(
                self.processed_dir / "positioning" / "chat_summary_embeddings.jsonl", 
                "chat summary embeddings"
            ),
            'chat_summaries': self._load_json_file(
                self.processed_dir / "chat_summarization" / "chat_summaries.json", 
                "chat summaries"
            ),
        }
        
        return data
    
    def _create_collection(self) -> bool:
        """Create Qdrant collection with proper configuration."""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"✅ Collection '{self.collection_name}' already exists")
                return True
            
            # Create collection with proper vector configuration
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 dimension
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"✅ Created collection '{self.collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create collection: {e}")
            return False
    
    def _prepare_points(self, embeddings: List[Dict], chunks: List[Dict], tagged_chunks: List[Dict], 
                       cluster_summary_embeddings: List[Dict], cluster_summaries: Dict,
                       chat_summary_embeddings: List[Dict], chat_summaries: Dict) -> List[PointStruct]:
        """Prepare points for Qdrant with cross-reference metadata (chunks and clusters)."""
        points = []
        
        # Create lookup dictionaries for efficient data access
        chunks_lookup = {chunk['chunk_id']: chunk for chunk in chunks}
        tagged_chunks_lookup = {tagged['chunk_id']: tagged for tagged in tagged_chunks}
        cluster_summaries_lookup = {str(cluster_id): summary_data for cluster_id, summary_data in cluster_summaries.items()}
        chat_summaries_lookup = {str(chat_id): summary_data for chat_id, summary_data in chat_summaries.items()}
        
        # Process chunk embeddings
        for embedding in tqdm(embeddings, desc="Preparing chunk points"):
            chunk_id = embedding.get('chunk_id', '')
            embedding_vector = embedding.get('embedding', [])
            embedding_hash = embedding.get('embedding_hash', '')
            
            # Get chunk data
            chunk_data = chunks_lookup.get(chunk_id, {})
            content = chunk_data.get('content', '')
            role = chunk_data.get('role', '')
            chat_id = chunk_data.get('chat_id', '')
            message_id = chunk_data.get('message_id', '')
            message_hash = chunk_data.get('message_hash', '')
            
            # Get tagged chunk data
            tagged_data = tagged_chunks_lookup.get(chunk_id, {})
            tags = tagged_data.get('tags', [])
            domain = tagged_data.get('domain', 'unknown')
            complexity = tagged_data.get('complexity', 'medium')
            
            # Create integer ID from chunk_id hash for Qdrant compatibility
            point_id = int(hashlib.sha256(chunk_id.encode()).hexdigest()[:16], 16)
            
            # Create point with comprehensive metadata
            point = PointStruct(
                id=point_id,  # Use integer ID for Qdrant compatibility
                vector=embedding_vector,
                payload={
                    # Entity type
                    'entity_type': 'chunk',
                    
                    # Cross-reference IDs for Neo4j linking
                    'chunk_id': chunk_id,
                    'message_id': message_id,
                    'chat_id': chat_id,
                    'embedding_hash': embedding_hash,
                    'message_hash': message_hash,
                    
                    # Content data
                    'content': content,
                    'role': role,
                    
                    # Semantic data
                    'tags': tags,
                    'domain': domain,
                    'complexity': complexity,
                    
                    # Processing metadata
                    'loaded_at': datetime.now().isoformat(),
                    'vector_dimension': len(embedding_vector),
                    'embedding_method': 'sentence-transformers'
                }
            )
            
            points.append(point)
        
        # Process cluster embeddings
        for cluster_embedding in tqdm(cluster_summary_embeddings, desc="Preparing cluster points"):
            cluster_id = cluster_embedding.get('cluster_id', '')
            embedding_vector = cluster_embedding.get('embedding', [])
            embedding_hash = cluster_embedding.get('hash', '')
            
            # Get cluster summary data
            cluster_summary_data = cluster_summaries_lookup.get(cluster_id, {})
            summary = cluster_summary_data.get('summary', '')
            domain = cluster_summary_data.get('domain', 'unknown')
            topics = cluster_summary_data.get('topics', [])
            complexity = cluster_summary_data.get('complexity', 'medium')
            key_points = cluster_summary_data.get('key_points', [])
            common_tags = cluster_summary_data.get('common_tags', [])
            
            # Create integer ID from cluster_id hash for Qdrant compatibility
            point_id = int(hashlib.sha256(f"cluster_{cluster_id}".encode()).hexdigest()[:16], 16)
            
            # Create cluster point with comprehensive metadata
            point = PointStruct(
                id=point_id,
                vector=embedding_vector,
                payload={
                    # Entity type
                    'entity_type': 'cluster',
                    
                    # Cross-reference IDs for Neo4j linking
                    'cluster_id': cluster_id,
                    'embedding_hash': embedding_hash,
                    
                    # Content data
                    'summary': summary,
                    'key_points': key_points,
                    
                    # Semantic data
                    'topics': topics,
                    'domain': domain,
                    'complexity': complexity,
                    'common_tags': common_tags,
                    
                    # Processing metadata
                    'loaded_at': datetime.now().isoformat(),
                    'vector_dimension': len(embedding_vector),
                    'embedding_method': 'sentence-transformers'
                }
            )
            
            points.append(point)
        
        # Process chat summary embeddings
        for chat_embedding in tqdm(chat_summary_embeddings, desc="Preparing chat summary points"):
            chat_id = chat_embedding.get('chat_id', '')
            embedding_vector = chat_embedding.get('embedding', [])
            embedding_hash = chat_embedding.get('hash', '')
            
            # Get chat summary data
            chat_summary_data = chat_summaries_lookup.get(chat_id, {})
            summary = chat_summary_data.get('summary', '')
            key_points = chat_summary_data.get('key_points', [])
            topics = chat_summary_data.get('topics', [])
            domain = chat_summary_data.get('domain', 'unknown')
            complexity = chat_summary_data.get('complexity', 'medium')
            
            # Create integer ID from chat_id hash for Qdrant compatibility
            point_id = int(hashlib.sha256(f"chat_summary_{chat_id}".encode()).hexdigest()[:16], 16)
            
            # Create chat summary point with comprehensive metadata
            point = PointStruct(
                id=point_id,
                vector=embedding_vector,
                payload={
                    # Entity type
                    'entity_type': 'chat_summary',
                    
                    # Cross-reference IDs for Neo4j linking
                    'chat_id': chat_id,
                    'embedding_hash': embedding_hash,
                    
                    # Content data
                    'summary': summary,
                    'key_points': key_points,
                    
                    # Semantic data
                    'topics': topics,
                    'domain': domain,
                    'complexity': complexity,
                    
                    # Processing metadata
                    'loaded_at': datetime.now().isoformat(),
                    'vector_dimension': len(embedding_vector),
                    'embedding_method': 'sentence-transformers'
                }
            )
            
            points.append(point)
        
        return points
    
    def _upload_points(self, points: List[PointStruct], batch_size: int = 100) -> bool:
        """Upload points to Qdrant in batches."""
        try:
            total_points = len(points)
            logger.info(f"📤 Uploading {total_points} points to Qdrant...")
            
            # Upload in batches for better performance
            for i in tqdm(range(0, total_points, batch_size), desc="Uploading batches"):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            logger.info(f"✅ Successfully uploaded {total_points} points")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to upload points: {e}")
            return False
    
    def _verify_collection(self) -> Dict[str, any]:
        """Verify collection contents and statistics."""
        try:
            # Get collection info
            collection_info = self.client.get_collection(self.collection_name)
            
            # Get collection statistics
            collection_stats = self.client.get_collection(self.collection_name)
            
            # Count points
            points_count = collection_stats.points_count
            
            logger.info(f"📊 Collection Statistics:")
            logger.info(f"  Collection: {self.collection_name}")
            logger.info(f"  Points: {points_count}")
            logger.info(f"  Vector Size: {collection_info.config.params.vectors.size}")
            logger.info(f"  Distance: {collection_info.config.params.vectors.distance}")
            
            return {
                'collection_name': self.collection_name,
                'points_count': points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to verify collection: {e}")
            return {}
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save loading metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'qdrant_loading',
            'stats': stats,
            'version': '1.0',
            'method': 'hybrid_loader',
            'features': [
                'hash_based_tracking',
                'incremental_loading',
                'cross_reference_metadata',
                'neo4j_compatible',
                'batch_uploading',
                'cosine_similarity',
                'chunk_embeddings',
                'cluster_embeddings',
                'hierarchical_search'
            ]
        }
        metadata_file = self.loading_dir / "qdrant_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def load_embeddings(self, force_reload: bool = False) -> Dict:
        """Load embeddings into Qdrant with cross-reference metadata."""
        logger.info("🚀 Starting Qdrant embeddings loading...")
        
        if not self.client:
            logger.error("Qdrant client not available")
            return {'status': 'qdrant_unavailable'}
        
        # Load all data
        data = self._load_embeddings_data()
        
        # Check for minimum required data
        if not data['embeddings']:
            logger.warning("⚠️  No embeddings found - pipeline may not have been run yet")
            logger.info("💡 Run the pipeline first: python chatmind/pipeline/run_pipeline.py --local")
            return {'status': 'no_embeddings', 'reason': 'pipeline_not_run'}
        
        # Generate current hashes by data type
        current_hashes = {}
        for data_type, items in data.items():
            if isinstance(items, list):
                current_hashes[data_type] = self._generate_data_type_hash(data_type, items)
        
        # Check if already processed (unless force reload)
        if not force_reload:
            existing_hashes = self._get_processed_hashes()
            if existing_hashes:
                logger.info(f"📋 Found existing processed hashes for {len(existing_hashes)} data types")
                
                # Check which data types have changed
                changed_types = []
                for data_type, current_hash in current_hashes.items():
                    if data_type not in existing_hashes or existing_hashes[data_type] != current_hash:
                        changed_types.append(data_type)
                
                if not changed_types:
                    logger.info("✅ All data types are up to date - no changes detected")
                    logger.info("⏭️ Skipping (use --force to reload)")
                    return {'status': 'skipped', 'reason': 'no_changes'}
                else:
                    logger.info(f"🔄 Incremental loading: {', '.join(changed_types)} have changed")
        
        # Create collection
        if not self._create_collection():
            return {'status': 'failed', 'reason': 'collection_creation_failed'}
        
        # Clear collection if force reload
        if force_reload:
            try:
                self.client.delete_collection(self.collection_name)
                self._create_collection()
                logger.info("🗑️  Cleared existing collection (force reload)")
            except Exception as e:
                logger.warning(f"Could not clear collection: {e}")
        
        # Prepare points with cross-reference metadata
        points = self._prepare_points(
            data['embeddings'], 
            data['chunks'], 
            data['tagged_chunks'],
            data['cluster_summary_embeddings'],
            data['cluster_summaries'],
            data['chat_summary_embeddings'],
            data['chat_summaries']
        )
        
        # Upload points
        if not self._upload_points(points):
            return {'status': 'failed', 'reason': 'upload_failed'}
        
        # Verify collection
        verification_stats = self._verify_collection()
        
        # Calculate comprehensive statistics
        stats = {
            'status': 'success',
            'embeddings_loaded': len(data['embeddings']),
            'chunks_loaded': len(data['chunks']),
            'tagged_chunks_loaded': len(data['tagged_chunks']),
            'cluster_embeddings_loaded': len(data['cluster_summary_embeddings']),
            'cluster_summaries_loaded': len(data['cluster_summaries']),
            'chat_summary_embeddings_loaded': len(data['chat_summary_embeddings']),
            'chat_summaries_loaded': len(data['chat_summaries']),
            'points_uploaded': len(points),
            'collection_name': self.collection_name,
            'vector_dimension': 384,
            'distance_metric': 'cosine'
        }
        
        # Merge verification stats
        stats.update(verification_stats)
        
        # Save granular hashes for tracking
        self._save_processed_hashes(current_hashes)
        self._save_metadata(stats)
        
        # Enhanced user feedback
        logger.info("✅ Qdrant embeddings loading completed!")
        logger.info("📈 Loading Statistics:")
        logger.info(f"  🔢 Chunk Embeddings: {stats['embeddings_loaded']}")
        logger.info(f"  📝 Chunks: {stats['chunks_loaded']}")
        logger.info(f"  🏷️  Tagged Chunks: {stats['tagged_chunks_loaded']}")
        logger.info(f"  🎯 Cluster Embeddings: {stats['cluster_embeddings_loaded']}")
        logger.info(f"  📊 Cluster Summaries: {stats['cluster_summaries_loaded']}")
        logger.info(f"  💬 Chat Summary Embeddings: {stats['chat_summary_embeddings_loaded']}")
        logger.info(f"  📊 Chat Summaries: {stats['chat_summaries_loaded']}")
        logger.info(f"  📤 Total Points Uploaded: {stats['points_uploaded']}")
        logger.info(f"  📊 Collection: {stats['collection_name']}")
        logger.info(f"  🔢 Vector Dimension: {stats['vector_dimension']}")
        logger.info(f"  📏 Distance Metric: {stats['distance_metric']}")
        
        # Cross-reference information
        logger.info("🔗 Cross-reference metadata included:")
        logger.info("  - chunk_id → Neo4j Chunk nodes")
        logger.info("  - message_id → Neo4j Message nodes")
        logger.info("  - chat_id → Neo4j Chat nodes")
        logger.info("  - cluster_id → Neo4j Cluster nodes")
        logger.info("  - embedding_hash → Unique embedding identifier")
        logger.info("  - message_hash → Message content hash")
        
        return stats
    
    def close(self):
        """Close the Qdrant client."""
        if self.client:
            self.client.close()


@click.command()
@click.option('--qdrant-url', default="http://localhost:6335", help='Qdrant URL (default: http://localhost:6335)')
@click.option('--collection-name', default="chatmind_embeddings", help='Collection name (default: chatmind_embeddings)')
@click.option('--force', is_flag=True, help='Force reload (clear existing collection)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t load')
def main(qdrant_url: str, collection_name: str, force: bool, check_only: bool):
    """Load embeddings into Qdrant vector database with hybrid architecture."""
    
    if check_only:
        logger.info("🔍 Checking Qdrant setup...")
        try:
            client = QdrantClient(url=qdrant_url)
            collections = client.get_collections()
            logger.info("✅ Qdrant connection successful")
            logger.info(f"📊 Available collections: {[col.name for col in collections.collections]}")
            client.close()
        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
        return
    
    loader = QdrantVectorLoader(qdrant_url=qdrant_url, collection_name=collection_name)
    
    try:
        result = loader.load_embeddings(force_reload=force)
        
        if result['status'] == 'success':
            logger.info("✅ Qdrant loading completed successfully!")
        else:
            logger.error(f"❌ Qdrant loading failed: {result.get('reason', 'unknown')}")
    finally:
        loader.close()


if __name__ == "__main__":
    main() 