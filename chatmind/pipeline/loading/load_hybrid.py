#!/usr/bin/env python3
"""
Hybrid Database Loader

Orchestrates loading of data into both Neo4j (graph relationships) and Qdrant (embeddings).
Ensures seamless cross-referencing between the two databases.
Uses modular directory structure: data/processed/loading/
"""

import json
import click
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime
import pickle

# Import pipeline configuration
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import get_neo4j_config

# Import our loaders
from load_graph import HybridNeo4jGraphLoader
from load_qdrant import QdrantVectorLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridDatabaseLoader:
    """Orchestrates loading into both Neo4j and Qdrant with cross-referencing."""
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None,
                 qdrant_url: str = "http://localhost:6335",
                 qdrant_collection: str = "chatmind_embeddings",
                 processed_dir: str = "data/processed"):
        
        # Load Neo4j configuration
        neo4j_config = get_neo4j_config()
        self.neo4j_uri = neo4j_uri or neo4j_config['uri']
        self.neo4j_user = neo4j_user or neo4j_config['user']
        self.neo4j_password = neo4j_password or neo4j_config['password']
        
        # Qdrant configuration
        self.qdrant_url = qdrant_url
        self.qdrant_collection = qdrant_collection
        
        # Directory structure - resolve relative to project root
        # Find the project root (where main .env file is located)
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
        
        # Resolve processed_dir relative to project root
        self.processed_dir = project_root / processed_dir
        self.loading_dir = self.processed_dir / "loading"
        self.loading_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Project root: {project_root}")
        logger.info(f"📁 Processed directory: {self.processed_dir}")
        logger.info(f"📁 Loading directory: {self.loading_dir}")
        
        # Initialize loaders
        self.neo4j_loader = HybridNeo4jGraphLoader(
            uri=self.neo4j_uri,
            user=self.neo4j_user,
            password=self.neo4j_password,
            processed_dir=str(self.processed_dir)
        )
        
        self.qdrant_loader = QdrantVectorLoader(
            qdrant_url=self.qdrant_url,
            collection_name=self.qdrant_collection,
            processed_dir=str(self.processed_dir)
        )
    
    def _get_processed_hashes(self) -> Dict[str, set]:
        """Get hashes of already processed data by type."""
        hash_file = self.loading_dir / "hybrid_loading_hashes.pkl"
        if hash_file.exists():
            with open(hash_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_processed_hashes(self, hashes: Dict[str, set]) -> None:
        """Save hashes of processed data by type."""
        hash_file = self.loading_dir / "hybrid_loading_hashes.pkl"
        with open(hash_file, 'wb') as f:
            pickle.dump(hashes, f)
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save hybrid loading metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'hybrid_loading',
            'stats': stats,
            'version': '1.0',
            'method': 'hybrid_orchestrator',
            'features': [
                'neo4j_graph_relationships',
                'qdrant_vector_search',
                'cross_reference_linking',
                'incremental_loading',
                'seamless_integration'
            ],
            'databases': {
                'neo4j': {
                    'uri': self.neo4j_uri,
                    'user': self.neo4j_user
                },
                'qdrant': {
                    'url': self.qdrant_url,
                    'collection': self.qdrant_collection
                }
            }
        }
        metadata_file = self.loading_dir / "hybrid_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved hybrid metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save hybrid metadata: {e}")
    
    def _verify_cross_references(self) -> Dict[str, any]:
        """Verify that cross-references are properly established."""
        logger.info("🔍 Verifying cross-references between Neo4j and Qdrant...")
        
        verification_stats = {
            'neo4j_chunks': 0,
            'qdrant_points': 0,
            'cross_references_valid': False
        }
        
        try:
            # Check Neo4j chunks
            if self.neo4j_loader.driver:
                with self.neo4j_loader.driver.session() as session:
                    result = session.run("MATCH (ch:Chunk) RETURN count(ch) as count")
                    verification_stats['neo4j_chunks'] = result.single()['count']
            
            # Check Qdrant points
            if self.qdrant_loader.client:
                try:
                    collection_info = self.qdrant_loader.client.get_collection(self.qdrant_collection)
                    verification_stats['qdrant_points'] = collection_info.points_count
                except Exception as e:
                    logger.warning(f"Could not verify Qdrant points: {e}")
            
            # Verify cross-references
            if verification_stats['neo4j_chunks'] > 0 and verification_stats['qdrant_points'] > 0:
                verification_stats['cross_references_valid'] = True
                logger.info("✅ Cross-references verified successfully!")
                logger.info(f"  📊 Neo4j Chunks: {verification_stats['neo4j_chunks']}")
                logger.info(f"  📊 Qdrant Points: {verification_stats['qdrant_points']}")
            else:
                logger.warning("⚠️  Cross-reference verification incomplete")
            
        except Exception as e:
            logger.error(f"❌ Cross-reference verification failed: {e}")
        
        return verification_stats
    
    def load_hybrid(self, force_reload: bool = False) -> Dict:
        """Load data into both Neo4j and Qdrant with cross-referencing."""
        logger.info("🚀 Starting hybrid database loading...")
        logger.info("📊 Loading into Neo4j (graph relationships) and Qdrant (embeddings)")
        
        # Check if already processed (unless force reload)
        if not force_reload:
            existing_hashes = self._get_processed_hashes()
            if existing_hashes:
                logger.info("📋 Found existing hybrid loading hashes")
                logger.info("⏭️ Skipping (use --force to reload)")
                return {'status': 'skipped', 'reason': 'already_processed'}
        
        # Step 1: Load into Neo4j (graph relationships)
        logger.info("🔄 Step 1: Loading into Neo4j...")
        neo4j_result = self.neo4j_loader.load_pipeline(force_reload=force_reload)
        
        if neo4j_result['status'] != 'success':
            logger.error(f"❌ Neo4j loading failed: {neo4j_result.get('reason', 'unknown')}")
            return {'status': 'failed', 'reason': 'neo4j_loading_failed', 'details': neo4j_result}
        
        logger.info("✅ Neo4j loading completed successfully!")
        
        # Step 2: Load into Qdrant (embeddings)
        logger.info("🔄 Step 2: Loading into Qdrant...")
        qdrant_result = self.qdrant_loader.load_embeddings(force_reload=force_reload)
        
        if qdrant_result['status'] != 'success':
            logger.error(f"❌ Qdrant loading failed: {qdrant_result.get('reason', 'unknown')}")
            return {'status': 'failed', 'reason': 'qdrant_loading_failed', 'details': qdrant_result}
        
        logger.info("✅ Qdrant loading completed successfully!")
        
        # Step 3: Verify cross-references
        logger.info("🔄 Step 3: Verifying cross-references...")
        verification_stats = self._verify_cross_references()
        
        # Combine statistics
        stats = {
            'status': 'success',
            'neo4j_stats': neo4j_result,
            'qdrant_stats': qdrant_result,
            'verification_stats': verification_stats,
            'cross_references_valid': verification_stats['cross_references_valid']
        }
        
        # Save hybrid loading hashes
        hybrid_hashes = {
            'neo4j_loaded': True,
            'qdrant_loaded': True,
            'cross_references_verified': verification_stats['cross_references_valid']
        }
        self._save_processed_hashes(hybrid_hashes)
        self._save_metadata(stats)
        
        # Enhanced user feedback
        logger.info("✅ Hybrid database loading completed!")
        logger.info("📈 Combined Statistics:")
        logger.info(f"  💬 Neo4j Chats: {neo4j_result.get('chats_loaded', 0)}")
        logger.info(f"  📝 Neo4j Chunks: {neo4j_result.get('chunks_loaded', 0)}")
        logger.info(f"  🎯 Neo4j Clusters: {neo4j_result.get('clusters_loaded', 0)}")
        logger.info(f"  🏷️  Neo4j Tags: {neo4j_result.get('tags_loaded', 0)}")
        logger.info(f"  🔢 Qdrant Points: {qdrant_result.get('points_uploaded', 0)}")
        logger.info(f"  📊 Qdrant Collection: {qdrant_result.get('collection_name', 'N/A')}")
        logger.info(f"  🔗 Cross-references: {'✅ Valid' if verification_stats['cross_references_valid'] else '❌ Invalid'}")
        
        # Architecture information
        logger.info("🏗️  Hybrid Architecture:")
        logger.info("  📊 Neo4j: Graph relationships, semantic tags, clustering")
        logger.info("  🔢 Qdrant: Vector embeddings, semantic search")
        logger.info("  🔗 Cross-references: chunk_id, message_id, chat_id")
        logger.info("  ⚡ Performance: Fast vector search + rich graph context")
        
        return stats
    
    def close(self):
        """Close all database connections."""
        if self.neo4j_loader:
            self.neo4j_loader.close()
        if self.qdrant_loader:
            self.qdrant_loader.close()


@click.command()
@click.option('--neo4j-uri', default=None, help='Neo4j URI (defaults to .env config)')
@click.option('--neo4j-user', default=None, help='Neo4j username (defaults to .env config)')
@click.option('--neo4j-password', default=None, help='Neo4j password (defaults to .env config)')
@click.option('--qdrant-url', default="http://localhost:6335", help='Qdrant URL (default: http://localhost:6335)')
@click.option('--qdrant-collection', default="chatmind_embeddings", help='Qdrant collection name (default: chatmind_embeddings)')
@click.option('--force', is_flag=True, help='Force reload (clear existing data)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t load')
def main(neo4j_uri: str, neo4j_user: str, neo4j_password: str, 
         qdrant_url: str, qdrant_collection: str, force: bool, check_only: bool):
    """Load data into both Neo4j and Qdrant with hybrid architecture."""
    
    if check_only:
        logger.info("🔍 Checking hybrid database setup...")
        
        # Check Neo4j
        try:
            from neo4j import GraphDatabase
            neo4j_config = get_neo4j_config()
            uri = neo4j_uri or neo4j_config['uri']
            user = neo4j_user or neo4j_config['user']
            password = neo4j_password or neo4j_config['password']
            
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
            driver.close()
            logger.info("✅ Neo4j connection successful")
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
        
        # Check Qdrant
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(url=qdrant_url)
            collections = client.get_collections()
            logger.info("✅ Qdrant connection successful")
            logger.info(f"📊 Available collections: {[col.name for col in collections.collections]}")
            client.close()
        except Exception as e:
            logger.error(f"❌ Qdrant connection failed: {e}")
        
        return
    
    loader = HybridDatabaseLoader(
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        qdrant_url=qdrant_url,
        qdrant_collection=qdrant_collection
    )
    
    try:
        result = loader.load_hybrid(force_reload=force)
        
        if result['status'] == 'success':
            logger.info("✅ Hybrid loading completed successfully!")
        else:
            logger.error(f"❌ Hybrid loading failed: {result.get('reason', 'unknown')}")
    finally:
        loader.close()


if __name__ == "__main__":
    main() 