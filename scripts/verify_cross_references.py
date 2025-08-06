#!/usr/bin/env python3
"""
Comprehensive cross-reference verification between Qdrant and Neo4j.
Tests chunk, cluster, and chat summary linking across both databases.
"""

import sys
import os
from pathlib import Path
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import logging
from typing import Dict, List, Set, Tuple
import json

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CrossReferenceVerifier:
    """Verify cross-references between Qdrant and Neo4j databases."""
    
    def __init__(self):
        # Neo4j configuration
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))

        # Qdrant configuration
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6335))  # Docker maps 6333->6335
        self.qdrant_grpc_port = int(os.getenv("QDRANT_GRPC_PORT", 6336))  # Docker maps 6334->6336
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "chatmind_embeddings")
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port, grpc_port=self.qdrant_grpc_port)

    def verify_chunk_cross_references(self) -> Dict:
        """Verify chunk cross-references between Qdrant and Neo4j."""
        logger.info("🔍 Verifying chunk cross-references...")
        
        # Get chunks from Qdrant
        chunk_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "chunk"}}]},
            limit=100
        )[0]
        
        logger.info(f"Found {len(chunk_points)} chunk embeddings in Qdrant")
        
        successful_matches = 0
        failed_matches = 0
        sample_matches = []
        
        for point in chunk_points[:20]:  # Test first 20 chunks
            chunk_id = point.payload.get('chunk_id')
            message_id = point.payload.get('message_id')
            
            if not chunk_id:
                failed_matches += 1
                continue
                
            # Look up in Neo4j
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (ch:Chunk {chunk_id: $chunk_id})
                    OPTIONAL MATCH (ch)-[:BELONGS_TO]->(m:Message)
                    RETURN ch.chunk_id, ch.content, m.message_id
                    LIMIT 1
                """, chunk_id=chunk_id)
                
                record = result.single()
                if record:
                    successful_matches += 1
                    sample_matches.append({
                        'qdrant_chunk_id': chunk_id,
                        'qdrant_message_id': message_id,
                        'neo4j_chunk_id': record['ch.chunk_id'],
                        'neo4j_message_id': record['m.message_id'],
                        'content_preview': record['ch.content'][:100] if record['ch.content'] else None
                    })
                else:
                    failed_matches += 1
        
        success_rate = (successful_matches / (successful_matches + failed_matches)) * 100 if (successful_matches + failed_matches) > 0 else 0
        
        return {
            'total_tested': successful_matches + failed_matches,
            'successful_matches': successful_matches,
            'failed_matches': failed_matches,
            'success_rate': success_rate,
            'sample_matches': sample_matches[:5]  # Show first 5 matches
        }

    def verify_cluster_cross_references(self) -> Dict:
        """Verify cluster cross-references between Qdrant and Neo4j."""
        logger.info("🔍 Verifying cluster cross-references...")
        
        # Get cluster embeddings from Qdrant
        cluster_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "cluster"}}]},
            limit=100
        )[0]
        
        logger.info(f"Found {len(cluster_points)} cluster embeddings in Qdrant")
        
        successful_matches = 0
        failed_matches = 0
        sample_matches = []
        
        for point in cluster_points[:20]:  # Test first 20 clusters
            cluster_id = point.payload.get('cluster_id')
            
            if not cluster_id:
                failed_matches += 1
                continue
                
            # Look up in Neo4j
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (cl:Cluster {cluster_id: $cluster_id})
                    OPTIONAL MATCH (cl)-[:HAS_SUMMARY]->(s:Summary)
                    RETURN cl.cluster_id, cl.x, cl.y, s.summary
                    LIMIT 1
                """, cluster_id=cluster_id)
                
                record = result.single()
                if record:
                    successful_matches += 1
                    sample_matches.append({
                        'qdrant_cluster_id': cluster_id,
                        'neo4j_cluster_id': record['cl.cluster_id'],
                        'position': (record['cl.x'], record['cl.y']),
                        'summary_preview': record['s.summary'][:100] if record['s.summary'] else None
                    })
                else:
                    failed_matches += 1
        
        success_rate = (successful_matches / (successful_matches + failed_matches)) * 100 if (successful_matches + failed_matches) > 0 else 0
        
        return {
            'total_tested': successful_matches + failed_matches,
            'successful_matches': successful_matches,
            'failed_matches': failed_matches,
            'success_rate': success_rate,
            'sample_matches': sample_matches[:5]  # Show first 5 matches
        }

    def verify_chat_summary_cross_references(self) -> Dict:
        """Verify chat summary cross-references between Qdrant and Neo4j."""
        logger.info("🔍 Verifying chat summary cross-references...")
        
        # Get chat summary embeddings from Qdrant
        chat_summary_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "chat_summary"}}]},
            limit=100
        )[0]
        
        logger.info(f"Found {len(chat_summary_points)} chat summary embeddings in Qdrant")
        
        successful_matches = 0
        failed_matches = 0
        sample_matches = []
        
        for point in chat_summary_points[:20]:  # Test first 20 chat summaries
            chat_id = point.payload.get('chat_id')
            
            if not chat_id:
                failed_matches += 1
                continue
                
            # Look up in Neo4j
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (c:Chat {chat_id: $chat_id})
                    OPTIONAL MATCH (c)-[:HAS_SUMMARY]->(cs:ChatSummary)
                    RETURN c.chat_id, c.title, cs.summary
                    LIMIT 1
                """, chat_id=chat_id)
                
                record = result.single()
                if record:
                    successful_matches += 1
                    sample_matches.append({
                        'qdrant_chat_id': chat_id,
                        'neo4j_chat_id': record['c.chat_id'],
                        'title': record['c.title'],
                        'summary_preview': record['cs.summary'][:100] if record['cs.summary'] else None
                    })
                else:
                    failed_matches += 1
        
        success_rate = (successful_matches / (successful_matches + failed_matches)) * 100 if (successful_matches + failed_matches) > 0 else 0
        
        return {
            'total_tested': successful_matches + failed_matches,
            'successful_matches': successful_matches,
            'failed_matches': failed_matches,
            'success_rate': success_rate,
            'sample_matches': sample_matches[:5]  # Show first 5 matches
        }

    def get_entity_distribution(self) -> Dict:
        """Get entity type distribution in Qdrant."""
        logger.info("📊 Getting entity type distribution...")
        
        all_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=1000
        )[0]
        
        entity_counts = {}
        for point in all_points:
            entity_type = point.payload.get('entity_type', 'unknown')
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        return entity_counts

    def run_comprehensive_verification(self):
        """Run comprehensive cross-reference verification."""
        logger.info("🚀 Starting comprehensive cross-reference verification...")
        
        try:
            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                logger.info("✅ Connected to Neo4j database")
            
            # Test Qdrant connection
            collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
            logger.info("✅ Connected to Qdrant database")
            
            # Get entity distribution
            entity_distribution = self.get_entity_distribution()
            logger.info(f"📊 Entity distribution in Qdrant: {entity_distribution}")
            
            # Run cross-reference tests
            chunk_results = self.verify_chunk_cross_references()
            cluster_results = self.verify_cluster_cross_references()
            chat_summary_results = self.verify_chat_summary_cross_references()
            
            # Print results
            logger.info("\n📋 Cross-Reference Verification Results:")
            logger.info("=" * 50)
            
            logger.info(f"🔍 Chunk Cross-References:")
            logger.info(f"   Total tested: {chunk_results['total_tested']}")
            logger.info(f"   Successful matches: {chunk_results['successful_matches']}")
            logger.info(f"   Failed matches: {chunk_results['failed_matches']}")
            logger.info(f"   Success rate: {chunk_results['success_rate']:.1f}%")
            
            if chunk_results['sample_matches']:
                logger.info("   Sample matches:")
                for match in chunk_results['sample_matches']:
                    logger.info(f"     Qdrant chunk_id: {match['qdrant_chunk_id']} → Neo4j chunk_id: {match['neo4j_chunk_id']}")
            
            logger.info(f"\n🎯 Cluster Cross-References:")
            logger.info(f"   Total tested: {cluster_results['total_tested']}")
            logger.info(f"   Successful matches: {cluster_results['successful_matches']}")
            logger.info(f"   Failed matches: {cluster_results['failed_matches']}")
            logger.info(f"   Success rate: {cluster_results['success_rate']:.1f}%")
            
            if cluster_results['sample_matches']:
                logger.info("   Sample matches:")
                for match in cluster_results['sample_matches']:
                    logger.info(f"     Qdrant cluster_id: {match['qdrant_cluster_id']} → Neo4j cluster_id: {match['neo4j_cluster_id']}")
            
            logger.info(f"\n💭 Chat Summary Cross-References:")
            logger.info(f"   Total tested: {chat_summary_results['total_tested']}")
            logger.info(f"   Successful matches: {chat_summary_results['successful_matches']}")
            logger.info(f"   Failed matches: {chat_summary_results['failed_matches']}")
            logger.info(f"   Success rate: {chat_summary_results['success_rate']:.1f}%")
            
            if chat_summary_results['sample_matches']:
                logger.info("   Sample matches:")
                for match in chat_summary_results['sample_matches']:
                    logger.info(f"     Qdrant chat_id: {match['qdrant_chat_id'][:20]}... → Neo4j chat_id: {match['neo4j_chat_id'][:20]}...")
            
            # Overall assessment
            total_tests = chunk_results['total_tested'] + cluster_results['total_tested'] + chat_summary_results['total_tested']
            total_successes = chunk_results['successful_matches'] + cluster_results['successful_matches'] + chat_summary_results['successful_matches']
            overall_success_rate = (total_successes / total_tests) * 100 if total_tests > 0 else 0
            
            logger.info("\n" + "=" * 50)
            logger.info(f"🎯 Overall Cross-Reference Success Rate: {overall_success_rate:.1f}%")
            
            if overall_success_rate >= 95:
                logger.info("✅ Excellent! Cross-references are working correctly.")
            elif overall_success_rate >= 80:
                logger.info("⚠️  Good, but some cross-references may need attention.")
            else:
                logger.info("❌ Significant issues with cross-references detected.")
                
        except Exception as e:
            logger.error(f"❌ Error during verification: {e}")
            raise

    def close(self):
        """Close database connections."""
        self.neo4j_driver.close()

def main():
    """Main function."""
    verifier = CrossReferenceVerifier()
    try:
        verifier.run_comprehensive_verification()
    finally:
        verifier.close()

if __name__ == "__main__":
    main() 