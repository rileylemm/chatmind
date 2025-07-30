#!/usr/bin/env python3
"""
Script to create HAS_CHUNK relationships between messages and chunks.
This addresses the missing cross-layer relationships in the dual layer graph.
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

class HasChunkRelationshipCreator:
    """Create HAS_CHUNK relationships between messages and chunks."""
    
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
    
    def create_has_chunk_relationships(self):
        """Create HAS_CHUNK relationships between messages and chunks."""
        logger.info("🎯 Creating HAS_CHUNK relationships between messages and chunks...")
        
        with self.driver.session() as session:
            # First, get all unique message IDs that have chunks
            get_message_ids_query = """
            MATCH (chunk:Chunk)
            WHERE chunk.source_message_id IS NOT NULL
            WITH DISTINCT chunk.source_message_id as source_id
            RETURN source_id
            """
            
            result = session.run(get_message_ids_query)
            source_ids = [record['source_id'] for record in result]
            
            logger.info(f"Found {len(source_ids)} unique source message IDs to process")
            
            # Process in smaller batches
            batch_size = 100
            total_relationships = 0
            
            for i in range(0, len(source_ids), batch_size):
                batch = source_ids[i:i + batch_size]
                
                # For each source_id, find the message and create relationships
                for source_id in batch:
                    try:
                        # Extract the message ID part (after the last underscore)
                        message_id = source_id.split('_')[-1]
                        
                        # Create relationships for this message
                        create_query = """
                        MATCH (m:Message {message_id: $message_id})
                        MATCH (chunk:Chunk {source_message_id: $source_id})
                        MERGE (m)-[:HAS_CHUNK]->(chunk)
                        RETURN count(*) as created
                        """
                        
                        result = session.run(create_query, message_id=message_id, source_id=source_id)
                        count = result.single()['created']
                        total_relationships += count
                        
                    except Exception as e:
                        logger.warning(f"Failed to process source_id {source_id}: {e}")
                
                if (i + batch_size) % 500 == 0:
                    logger.info(f"Processed {i + batch_size} source IDs, created {total_relationships} relationships...")
            
            logger.info(f"✅ Created {total_relationships} HAS_CHUNK relationships")
            return total_relationships

def main():
    """Main function to create HAS_CHUNK relationships."""
    creator = HasChunkRelationshipCreator()
    
    if not creator.connect():
        logger.error("Failed to connect to Neo4j")
        return
    
    try:
        # Create HAS_CHUNK relationships
        relationships_created = creator.create_has_chunk_relationships()
        logger.info(f"🎉 Successfully created {relationships_created} HAS_CHUNK relationships")
        
    except Exception as e:
        logger.error(f"❌ Error creating HAS_CHUNK relationships: {e}")
    
    finally:
        creator.close()

if __name__ == "__main__":
    main() 