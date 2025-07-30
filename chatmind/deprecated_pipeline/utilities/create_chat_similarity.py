#!/usr/bin/env python3
"""
Script to create SIMILAR_TO relationships between chats based on shared topics.
This addresses the missing chat similarity relationships in the dual layer graph.
"""

import sys
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ChatSimilarityCreator:
    """Create SIMILAR_TO relationships between chats based on shared topics."""
    
    def __init__(self):
        """Initialize the Neo4j connection."""
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
    
    def connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Successfully connected to Neo4j")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def create_chat_similarity_relationships(self, similarity_threshold=0.3):
        """Create SIMILAR_TO relationships between chats based on shared topics."""
        logger.info(f"🎯 Creating chat similarity relationships (threshold: {similarity_threshold})...")
        
        with self.driver.session() as session:
            # Find chats that share topics and create similarity relationships
            query = """
            MATCH (c1:Chat)-[:CONTAINS]->(m1:Message)-[:HAS_CHUNK]->(chunk1:Chunk)<-[:SUMMARIZES]-(topic:Topic)
            MATCH (c2:Chat)-[:CONTAINS]->(m2:Message)-[:HAS_CHUNK]->(chunk2:Chunk)<-[:SUMMARIZES]-(topic)
            WHERE c1.chat_id < c2.chat_id
            WITH c1, c2, count(DISTINCT topic) as shared_topics
            MATCH (c1)-[:CONTAINS]->(m1:Message)-[:HAS_CHUNK]->(chunk1:Chunk)<-[:SUMMARIZES]-(topic1:Topic)
            WITH c1, c2, shared_topics, count(DISTINCT topic1) as c1_topics
            MATCH (c2)-[:CONTAINS]->(m2:Message)-[:HAS_CHUNK]->(chunk2:Chunk)<-[:SUMMARIZES]-(topic2:Topic)
            WITH c1, c2, shared_topics, c1_topics, count(DISTINCT topic2) as c2_topics
            WITH c1, c2, shared_topics, c1_topics, c2_topics,
                 shared_topics * 1.0 / (c1_topics + c2_topics - shared_topics) as similarity
            WHERE similarity >= $threshold
            MERGE (c1)-[:SIMILAR_TO {similarity: similarity, shared_topics: shared_topics}]-(c2)
            RETURN c1.chat_id, c2.chat_id, similarity, shared_topics
            """
            
            result = session.run(query, threshold=similarity_threshold)
            relationships_created = 0
            
            for record in result:
                relationships_created += 1
                if relationships_created <= 5:  # Log first 5 for verification
                    logger.info(f"  Created: {record['c1.chat_id']} ↔ {record['c2.chat_id']} (similarity: {record['similarity']:.3f})")
            
            logger.info(f"✅ Created {relationships_created} chat similarity relationships")
            return relationships_created

def main():
    """Main function to create chat similarity relationships."""
    creator = ChatSimilarityCreator()
    
    if not creator.connect():
        logger.error("Failed to connect to Neo4j")
        return
    
    try:
        # Create similarity relationships with a reasonable threshold
        relationships_created = creator.create_chat_similarity_relationships(similarity_threshold=0.1)
        logger.info(f"🎉 Successfully created {relationships_created} chat similarity relationships")
        
    except Exception as e:
        logger.error(f"❌ Error creating chat similarity relationships: {e}")
    
    finally:
        creator.close()

if __name__ == "__main__":
    main() 