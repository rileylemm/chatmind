#!/usr/bin/env python3
"""
Debug script to check cluster IDs in both databases.
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

class ClusterIDDebugger:
    """Debug cluster ID linking between databases."""
    
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
    
    def debug_cluster_ids(self):
        """Debug cluster IDs in both databases."""
        logger.info("\n🔍 Debugging Cluster IDs...")
        
        # Get all cluster summaries from Neo4j
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
                RETURN cl.cluster_id, s.summary_hash
                ORDER BY cl.cluster_id
                LIMIT 20
            """)
            neo4j_cluster_summaries = [dict(record) for record in neo4j_result]
        
        logger.info(f"Found {len(neo4j_cluster_summaries)} cluster summaries in Neo4j")
        
        # Get all cluster embeddings from Qdrant
        cluster_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "cluster"}}]},
            limit=20,
            with_payload=True,
            with_vectors=False
        )[0]
        
        logger.info(f"Found {len(cluster_points)} cluster embeddings in Qdrant")
        
        # Check for ID matches
        neo4j_cluster_ids = {record['cl.cluster_id'] for record in neo4j_cluster_summaries}
        qdrant_cluster_ids = {point.payload.get('cluster_id') for point in cluster_points}
        
        # Find overlap
        overlap = neo4j_cluster_ids.intersection(qdrant_cluster_ids)
        
        logger.info(f"Neo4j cluster IDs (first 10): {list(neo4j_cluster_ids)[:10]}")
        logger.info(f"Qdrant cluster IDs (first 10): {list(qdrant_cluster_ids)[:10]}")
        logger.info(f"Overlap: {overlap}")
        logger.info(f"Linking success rate: {len(overlap)}/{len(neo4j_cluster_ids)} ({len(overlap)/len(neo4j_cluster_ids)*100:.1f}%)")
        
        # Check if there are any matching IDs
        if overlap:
            sample_id = list(overlap)[0]
            logger.info(f"\n✅ Found matching cluster ID: {sample_id}")
            
            # Verify the match in both databases
            with self.neo4j_driver.session() as session:
                neo4j_match = session.run("""
                    MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster {cluster_id: $cluster_id})
                    RETURN cl.cluster_id, s.summary
                """, cluster_id=sample_id).single()
            
            if neo4j_match:
                logger.info(f"Neo4j match: {dict(neo4j_match)}")
            
            # Find the matching Qdrant point
            for point in cluster_points:
                if point.payload.get('cluster_id') == sample_id:
                    logger.info(f"Qdrant match: cluster_id={point.payload.get('cluster_id')}, summary={point.payload.get('summary', 'N/A')[:100]}...")
                    break
        
        return {
            "neo4j_count": len(neo4j_cluster_summaries),
            "qdrant_count": len(cluster_points),
            "overlap_count": len(overlap),
            "linking_success_rate": len(overlap)/len(neo4j_cluster_ids)*100 if neo4j_cluster_ids else 0
        }
    
    def debug_chat_ids(self):
        """Debug chat IDs in both databases."""
        logger.info("\n🔍 Debugging Chat IDs...")
        
        # Get all chat summaries from Neo4j
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c:Chat)
                RETURN c.chat_id, cs.chat_summary_hash
                ORDER BY c.chat_id
                LIMIT 20
            """)
            neo4j_chat_summaries = [dict(record) for record in neo4j_result]
        
        logger.info(f"Found {len(neo4j_chat_summaries)} chat summaries in Neo4j")
        
        # Get all chat summary embeddings from Qdrant
        chat_summary_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "chat_summary"}}]},
            limit=20,
            with_payload=True,
            with_vectors=False
        )[0]
        
        logger.info(f"Found {len(chat_summary_points)} chat summary embeddings in Qdrant")
        
        # Check for ID matches
        neo4j_chat_ids = {record['c.chat_id'] for record in neo4j_chat_summaries}
        qdrant_chat_ids = {point.payload.get('chat_id') for point in chat_summary_points}
        
        # Find overlap
        overlap = neo4j_chat_ids.intersection(qdrant_chat_ids)
        
        logger.info(f"Neo4j chat IDs (first 5): {list(neo4j_chat_ids)[:5]}")
        logger.info(f"Qdrant chat IDs (first 5): {list(qdrant_chat_ids)[:5]}")
        logger.info(f"Overlap: {overlap}")
        logger.info(f"Linking success rate: {len(overlap)}/{len(neo4j_chat_ids)} ({len(overlap)/len(neo4j_chat_ids)*100:.1f}%)")
        
        return {
            "neo4j_count": len(neo4j_chat_summaries),
            "qdrant_count": len(chat_summary_points),
            "overlap_count": len(overlap),
            "linking_success_rate": len(overlap)/len(neo4j_chat_ids)*100 if neo4j_chat_ids else 0
        }
    
    def run_debug(self):
        """Run all debug tests."""
        logger.info("🚀 Starting Cluster ID Debug...")
        
        if not self.connect_databases():
            return False
        
        try:
            # Run debug tests
            cluster_results = self.debug_cluster_ids()
            chat_results = self.debug_chat_ids()
            
            # Print summary
            logger.info("\n📋 Debug Results:")
            logger.info(f"Cluster Summary Linking: {cluster_results['linking_success_rate']:.1f}% success")
            logger.info(f"Chat Summary Linking: {chat_results['linking_success_rate']:.1f}% success")
            
        finally:
            self.close_connections()

if __name__ == "__main__":
    debugger = ClusterIDDebugger()
    debugger.run_debug() 