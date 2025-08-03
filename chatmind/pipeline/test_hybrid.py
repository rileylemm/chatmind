#!/usr/bin/env python3
"""
Hybrid Architecture Test Script

Tests the integration between Neo4j and Qdrant databases.
Verifies cross-references and data integrity.
"""

import json
import logging
from pathlib import Path
import sys

# Add pipeline to path
sys.path.append(str(Path(__file__).parent))

from config import get_neo4j_config

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridArchitectureTester:
    """Test the hybrid Neo4j + Qdrant architecture."""
    
    def __init__(self):
        # Load configurations
        neo4j_config = get_neo4j_config()
        self.neo4j_uri = neo4j_config['uri']
        self.neo4j_user = neo4j_config['user']
        self.neo4j_password = neo4j_config['password']
        
        # Qdrant config (from environment or defaults)
        import os
        self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6335')
        self.qdrant_collection = os.getenv('QDRANT_COLLECTION', 'chatmind_embeddings')
        
        # Initialize connections
        if NEO4J_AVAILABLE:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
        else:
            self.neo4j_driver = None
            
        if QDRANT_AVAILABLE:
            self.qdrant_client = QdrantClient(url=self.qdrant_url)
        else:
            self.qdrant_client = None
    
    def test_neo4j_connection(self) -> dict:
        """Test Neo4j connection and basic functionality."""
        logger.info("🔍 Testing Neo4j connection...")
        
        if not self.neo4j_driver:
            return {'status': 'failed', 'reason': 'neo4j_not_available'}
        
        try:
            with self.neo4j_driver.session() as session:
                # Test basic connection
                result = session.run("RETURN 1 as test")
                test_value = result.single()['test']
                
                if test_value != 1:
                    return {'status': 'failed', 'reason': 'neo4j_test_query_failed'}
                
                # Count nodes by type
                node_counts = {}
                node_types = ['Chat', 'Message', 'Chunk', 'Cluster', 'Tag', 'Summary']
                
                for node_type in node_types:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    count = result.single()['count']
                    node_counts[node_type.lower()] = count
                
                # Count relationships
                rel_counts = {}
                rel_types = ['HAS_MESSAGE', 'HAS_CHUNK', 'TAGS', 'CONTAINS_CHUNK']
                
                for rel_type in rel_types:
                    result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                    count = result.single()['count']
                    rel_counts[rel_type.lower()] = count
                
                return {
                    'status': 'success',
                    'node_counts': node_counts,
                    'relationship_counts': rel_counts
                }
                
        except Exception as e:
            return {'status': 'failed', 'reason': f'neo4j_error: {str(e)}'}
    
    def test_qdrant_connection(self) -> dict:
        """Test Qdrant connection and basic functionality."""
        logger.info("🔍 Testing Qdrant connection...")
        
        if not self.qdrant_client:
            return {'status': 'failed', 'reason': 'qdrant_not_available'}
        
        try:
            # Test basic connection
            collections = self.qdrant_client.get_collections()
            
            # Check if our collection exists
            collection_names = [col.name for col in collections.collections]
            
            if self.qdrant_collection not in collection_names:
                return {
                    'status': 'failed', 
                    'reason': f'collection_not_found: {self.qdrant_collection}',
                    'available_collections': collection_names
                }
            
            # Get collection info
            collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
            
            return {
                'status': 'success',
                'collection_name': self.qdrant_collection,
                'points_count': collection_info.points_count,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance
            }
            
        except Exception as e:
            return {'status': 'failed', 'reason': f'qdrant_error: {str(e)}'}
    
    def test_cross_references(self) -> dict:
        """Test cross-references between Neo4j and Qdrant."""
        logger.info("🔍 Testing cross-references...")
        
        if not self.neo4j_driver or not self.qdrant_client:
            return {'status': 'failed', 'reason': 'databases_not_available'}
        
        try:
            # Get sample chunk from Neo4j
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (ch:Chunk) 
                    RETURN ch.chunk_id as chunk_id, ch.content as content 
                    LIMIT 1
                """)
                neo4j_chunk = result.single()
                
                if not neo4j_chunk:
                    return {'status': 'failed', 'reason': 'no_chunks_in_neo4j'}
                
                chunk_id = neo4j_chunk['chunk_id']
                content = neo4j_chunk['content']
                
                # Try to find the same chunk in Qdrant
                try:
                    qdrant_point = self.qdrant_client.retrieve(
                        collection_name=self.qdrant_collection,
                        ids=[chunk_id]
                    )
                    
                    if not qdrant_point:
                        return {
                            'status': 'failed', 
                            'reason': f'chunk_not_found_in_qdrant: {chunk_id}'
                        }
                    
                    qdrant_content = qdrant_point[0].payload.get('content', '')
                    
                    # Verify content matches
                    if content != qdrant_content:
                        return {
                            'status': 'failed',
                            'reason': 'content_mismatch',
                            'neo4j_content': content[:50] + '...',
                            'qdrant_content': qdrant_content[:50] + '...'
                        }
                    
                    return {
                        'status': 'success',
                        'chunk_id': chunk_id,
                        'content_matches': True,
                        'neo4j_content_length': len(content),
                        'qdrant_content_length': len(qdrant_content)
                    }
                    
                except Exception as e:
                    return {
                        'status': 'failed',
                        'reason': f'qdrant_retrieve_error: {str(e)}',
                        'chunk_id': chunk_id
                    }
                    
        except Exception as e:
            return {'status': 'failed', 'reason': f'cross_reference_error: {str(e)}'}
    
    def test_semantic_search(self) -> dict:
        """Test semantic search functionality in Qdrant."""
        logger.info("🔍 Testing semantic search...")
        
        if not self.qdrant_client:
            return {'status': 'failed', 'reason': 'qdrant_not_available'}
        
        try:
            # Get collection info to check if we have points
            collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
            
            if collection_info.points_count == 0:
                return {'status': 'failed', 'reason': 'no_points_in_collection'}
            
            # Try a simple search
            search_results = self.qdrant_client.search(
                collection_name=self.qdrant_collection,
                query_vector=[0.1] * 384,  # Simple test vector
                limit=5
            )
            
            if not search_results:
                return {'status': 'failed', 'reason': 'search_returned_no_results'}
            
            return {
                'status': 'success',
                'search_results_count': len(search_results),
                'first_result_score': search_results[0].score,
                'first_result_id': search_results[0].id
            }
            
        except Exception as e:
            return {'status': 'failed', 'reason': f'semantic_search_error: {str(e)}'}
    
    def run_all_tests(self) -> dict:
        """Run all hybrid architecture tests."""
        logger.info("🚀 Running hybrid architecture tests...")
        logger.info("=" * 50)
        
        results = {
            'neo4j_test': self.test_neo4j_connection(),
            'qdrant_test': self.test_qdrant_connection(),
            'cross_reference_test': self.test_cross_references(),
            'semantic_search_test': self.test_semantic_search()
        }
        
        # Calculate overall status
        all_passed = all(result['status'] == 'success' for result in results.values())
        
        # Print results
        logger.info("\n📊 Test Results:")
        logger.info("=" * 50)
        
        for test_name, result in results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            logger.info(f"{status_icon} {test_name}: {result['status']}")
            
            if result['status'] == 'success':
                if 'node_counts' in result:
                    logger.info(f"   📊 Neo4j nodes: {sum(result['node_counts'].values())}")
                if 'points_count' in result:
                    logger.info(f"   📊 Qdrant points: {result['points_count']}")
                if 'search_results_count' in result:
                    logger.info(f"   🔍 Search results: {result['search_results_count']}")
            else:
                logger.info(f"   ❌ Reason: {result.get('reason', 'unknown')}")
        
        logger.info("\n" + "=" * 50)
        
        if all_passed:
            logger.info("🎉 All tests passed! Hybrid architecture is working correctly.")
        else:
            logger.info("⚠️  Some tests failed. Check the details above.")
        
        return {
            'overall_status': 'success' if all_passed else 'failed',
            'tests_passed': sum(1 for r in results.values() if r['status'] == 'success'),
            'total_tests': len(results),
            'results': results
        }
    
    def close(self):
        """Close database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.qdrant_client:
            self.qdrant_client.close()


def main():
    """Run the hybrid architecture tests."""
    tester = HybridArchitectureTester()
    
    try:
        results = tester.run_all_tests()
        
        if results['overall_status'] == 'success':
            logger.info("✅ Hybrid architecture test completed successfully!")
            return 0
        else:
            logger.error("❌ Hybrid architecture test failed!")
            return 1
            
    finally:
        tester.close()


if __name__ == "__main__":
    exit(main()) 