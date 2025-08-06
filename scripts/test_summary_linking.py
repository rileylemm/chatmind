#!/usr/bin/env python3
"""
Test script to check cluster summary and chat summary ID linking between Neo4j and Qdrant.
"""

import sys
import os
from pathlib import Path
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import logging

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SummaryLinkingTester:
    """Test cluster summary and chat summary ID linking between databases."""
    
    def __init__(self):
        # Neo4j configuration
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "chatmind123")
        self.neo4j_driver = None
        
        # Qdrant configuration
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6335")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "chatmind_embeddings")
        self.qdrant_client = None
        
    def connect_databases(self):
        """Connect to both Neo4j and Qdrant databases."""
        logger.info("🔌 Connecting to databases...")
        
        # Connect to Neo4j
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Connected to Neo4j database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False
        
        # Connect to Qdrant
        try:
            self.qdrant_client = QdrantClient(self.qdrant_url)
            # Test connection
            collections = self.qdrant_client.get_collections()
            logger.info("✅ Connected to Qdrant database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False
        
        return True
    
    def close_connections(self):
        """Close all database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.qdrant_client:
            self.qdrant_client.close()
    
    def test_cluster_summary_linking(self):
        """Test cluster summary ID linking between Neo4j and Qdrant."""
        logger.info("\n🎯 Testing Cluster Summary ID Linking...")
        
        # Get cluster summaries from Neo4j
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
                RETURN cl.cluster_id, s.summary_hash, s.summary
                ORDER BY cl.cluster_id
                LIMIT 10
            """)
            neo4j_cluster_summaries = [dict(record) for record in neo4j_result]
        
        logger.info(f"Found {len(neo4j_cluster_summaries)} cluster summaries in Neo4j")
        
        # Get cluster embeddings from Qdrant
        cluster_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "cluster"}}]},
            limit=10,
            with_payload=True,
            with_vectors=False
        )[0]
        
        logger.info(f"Found {len(cluster_points)} cluster embeddings in Qdrant")
        
        # Check for ID matches
        neo4j_cluster_ids = {record['cl.cluster_id'] for record in neo4j_cluster_summaries}
        qdrant_cluster_ids = {point.payload.get('cluster_id') for point in cluster_points}
        
        # Find overlap
        overlap = neo4j_cluster_ids.intersection(qdrant_cluster_ids)
        
        logger.info(f"Neo4j cluster IDs: {neo4j_cluster_ids}")
        logger.info(f"Qdrant cluster IDs: {qdrant_cluster_ids}")
        logger.info(f"Overlap: {overlap}")
        logger.info(f"Linking success rate: {len(overlap)}/{len(neo4j_cluster_ids)} ({len(overlap)/len(neo4j_cluster_ids)*100:.1f}%)")
        
        return {
            "neo4j_count": len(neo4j_cluster_summaries),
            "qdrant_count": len(cluster_points),
            "overlap_count": len(overlap),
            "linking_success_rate": len(overlap)/len(neo4j_cluster_ids)*100 if neo4j_cluster_ids else 0
        }
    
    def test_chat_summary_linking(self):
        """Test chat summary ID linking between Neo4j and Qdrant."""
        logger.info("\n📊 Testing Chat Summary ID Linking...")
        
        # Get chat summaries from Neo4j
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c:Chat)
                RETURN c.chat_id, cs.chat_summary_hash, cs.summary
                ORDER BY c.chat_id
                LIMIT 10
            """)
            neo4j_chat_summaries = [dict(record) for record in neo4j_result]
        
        logger.info(f"Found {len(neo4j_chat_summaries)} chat summaries in Neo4j")
        
        # Get chat summary embeddings from Qdrant
        chat_summary_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "chat_summary"}}]},
            limit=10,
            with_payload=True,
            with_vectors=False
        )[0]
        
        logger.info(f"Found {len(chat_summary_points)} chat summary embeddings in Qdrant")
        
        # Check for ID matches
        neo4j_chat_ids = {record['c.chat_id'] for record in neo4j_chat_summaries}
        qdrant_chat_ids = {point.payload.get('chat_id') for point in chat_summary_points}
        
        # Find overlap
        overlap = neo4j_chat_ids.intersection(qdrant_chat_ids)
        
        logger.info(f"Neo4j chat IDs: {neo4j_chat_ids}")
        logger.info(f"Qdrant chat IDs: {qdrant_chat_ids}")
        logger.info(f"Overlap: {overlap}")
        logger.info(f"Linking success rate: {len(overlap)}/{len(neo4j_chat_ids)} ({len(overlap)/len(neo4j_chat_ids)*100:.1f}%)")
        
        return {
            "neo4j_count": len(neo4j_chat_summaries),
            "qdrant_count": len(chat_summary_points),
            "overlap_count": len(overlap),
            "linking_success_rate": len(overlap)/len(neo4j_chat_ids)*100 if neo4j_chat_ids else 0
        }
    
    def test_cross_reference_lookup(self):
        """Test cross-reference lookup for summaries."""
        logger.info("\n🔍 Testing Cross-Reference Lookup...")
        
        # Get a sample cluster summary from Qdrant
        cluster_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "cluster"}}]},
            limit=1,
            with_payload=True,
            with_vectors=False
        )[0]
        
        if cluster_points:
            cluster_id = cluster_points[0].payload.get('cluster_id')
            logger.info(f"Sample cluster ID from Qdrant: {cluster_id}")
            
            # Look up in Neo4j
            with self.neo4j_driver.session() as session:
                neo4j_result = session.run("""
                    MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster {cluster_id: $cluster_id})
                    RETURN cl.cluster_id, s.summary, s.domain, s.complexity
                """, cluster_id=cluster_id)
                neo4j_data = [dict(record) for record in neo4j_result]
            
            if neo4j_data:
                logger.info(f"✅ Found matching cluster summary in Neo4j: {neo4j_data[0]}")
                return {"cross_reference_works": True, "sample_data": neo4j_data[0]}
            else:
                logger.warning(f"❌ No matching cluster summary found in Neo4j for cluster_id: {cluster_id}")
                return {"cross_reference_works": False}
        
        return {"cross_reference_works": False}
    
    def test_summary_entity_distribution(self):
        """Test the distribution of summary entity types in Qdrant."""
        logger.info("\n📈 Testing Summary Entity Distribution...")
        
        # Get all points from Qdrant
        all_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )[0]
        
        # Count entity types
        entity_types = {}
        for point in all_points:
            entity_type = point.payload.get('entity_type', 'unknown')
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        logger.info(f"Entity type distribution in Qdrant: {entity_types}")
        
        # Check for summary-related entity types
        summary_entities = {k: v for k, v in entity_types.items() if 'summary' in k or k == 'cluster'}
        
        return {
            "total_points": len(all_points),
            "entity_types": entity_types,
            "summary_entities": summary_entities
        }
    
    def run_all_tests(self):
        """Run all summary linking tests."""
        logger.info("🚀 Starting Summary ID Linking Tests...")
        
        if not self.connect_databases():
            return False
        
        try:
            # Run all tests
            cluster_results = self.test_cluster_summary_linking()
            chat_results = self.test_chat_summary_linking()
            cross_ref_results = self.test_cross_reference_lookup()
            distribution_results = self.test_summary_entity_distribution()
            
            # Print summary
            logger.info("\n📋 Summary ID Linking Test Results:")
            logger.info(f"Cluster Summary Linking: {cluster_results['linking_success_rate']:.1f}% success")
            logger.info(f"Chat Summary Linking: {chat_results['linking_success_rate']:.1f}% success")
            logger.info(f"Cross-Reference Lookup: {'✅ Working' if cross_ref_results['cross_reference_works'] else '❌ Failed'}")
            logger.info(f"Entity Distribution: {distribution_results['summary_entities']}")
            
        finally:
            self.close_connections()

if __name__ == "__main__":
    tester = SummaryLinkingTester()
    tester.run_all_tests() 