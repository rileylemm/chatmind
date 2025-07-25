#!/usr/bin/env python3
"""
Neo4j Graph Loader

Loads processed chat data, embeddings, and clusters into Neo4j
as a knowledge graph for visualization and querying.
"""

import json
import jsonlines
import pickle
from pathlib import Path
from typing import Dict, List, Optional
import click
from tqdm import tqdm
import logging
from datetime import datetime

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jGraphLoader:
    """Loads chat data into Neo4j knowledge graph."""
    
    def __init__(self, 
                 uri: str = None,
                 user: str = None,
                 password: str = None,
                 embeddings_dir: str = "data/embeddings"):
        
        # Get credentials from environment or parameters
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        self.embeddings_dir = Path(embeddings_dir)
        self.driver = None
        
    def connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Clear existing data from the database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared existing data from database")
    
    def create_constraints(self):
        """Create database constraints and indexes."""
        with self.driver.session() as session:
            # Create constraints for unique properties
            session.run("CREATE CONSTRAINT chat_id IF NOT EXISTS FOR (c:Chat) REQUIRE c.chat_id IS UNIQUE")
            session.run("CREATE CONSTRAINT message_id IF NOT EXISTS FOR (m:Message) REQUIRE m.message_id IS UNIQUE")
            session.run("CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE")
            
            # Create indexes for better performance
            session.run("CREATE INDEX chat_title IF NOT EXISTS FOR (c:Chat) ON (c.title)")
            session.run("CREATE INDEX message_role IF NOT EXISTS FOR (m:Message) ON (m.role)")
            session.run("CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)")
            
            logger.info("Created database constraints and indexes")
    
    def load_chats(self, chunks_file: Path):
        """Load chat nodes from processed data."""
        with self.driver.session() as session:
            chat_ids = set()
            
            with jsonlines.open(chunks_file) as reader:
                for chunk in tqdm(reader, desc="Loading chats"):
                    chat_id = chunk['chat_id']
                    if chat_id not in chat_ids:
                        chat_ids.add(chat_id)
                        
                        # Create Chat node
                        session.run("""
                            MERGE (c:Chat {chat_id: $chat_id})
                            SET c.title = $title,
                                c.create_time = $create_time,
                                c.update_time = $update_time,
                                c.data_lake_id = $data_lake_id
                        """, {
                            'chat_id': chat_id,
                            'title': chunk['chat_title'],
                            'create_time': chunk.get('timestamp'),
                            'update_time': chunk.get('timestamp'),
                            'data_lake_id': f"chat_{chunk['chat_id'][:16]}" if len(chunk['chat_id']) > 16 else chunk['chat_id']
                        })
            
            logger.info(f"Loaded {len(chat_ids)} chat nodes")
    
    def load_messages(self, chunks_file: Path):
        """Load message nodes and relationships."""
        with self.driver.session() as session:
            with jsonlines.open(chunks_file) as reader:
                for chunk in tqdm(reader, desc="Loading messages"):
                    # Create Message node
                    session.run("""
                        MERGE (m:Message {message_id: $message_id})
                        SET m.content = $content,
                            m.role = $role,
                            m.timestamp = $timestamp,
                            m.chunk_id = $chunk_id,
                            m.cluster_id = $cluster_id
                    """, {
                        'message_id': chunk['message_id'],
                        'content': chunk['content'],
                        'role': chunk['role'],
                        'timestamp': chunk.get('timestamp'),
                        'chunk_id': chunk.get('chunk_id', 0),
                        'cluster_id': chunk.get('cluster_id', -1)
                    })
                    
                    # Create relationship to Chat
                    session.run("""
                        MATCH (m:Message {message_id: $message_id})
                        MATCH (c:Chat {chat_id: $chat_id})
                        MERGE (c)-[:CONTAINS]->(m)
                    """, {
                        'message_id': chunk['message_id'],
                        'chat_id': chunk['chat_id']
                    })
                    
                    # Create parent relationship if exists
                    if chunk.get('parent_id'):
                        session.run("""
                            MATCH (m:Message {message_id: $message_id})
                            MATCH (p:Message {message_id: $parent_id})
                            MERGE (p)-[:REPLIES_TO]->(m)
                        """, {
                            'message_id': chunk['message_id'],
                            'parent_id': chunk['parent_id']
                        })
            
            logger.info("Loaded message nodes and relationships")
    
    def load_topics(self, summaries_file: Path, topics_with_coords_file: Path = None):
        """Load topic nodes from cluster summaries with optional coordinates."""
        with self.driver.session() as session:
            with open(summaries_file, 'r') as f:
                summaries = json.load(f)
            
            # Load coordinates if available
            coordinates = {}
            if topics_with_coords_file and topics_with_coords_file.exists():
                try:
                    with jsonlines.open(topics_with_coords_file) as reader:
                        for topic_data in reader:
                            topic_id = topic_data.get('topic_id')
                            if topic_id and 'x' in topic_data and 'y' in topic_data:
                                coordinates[topic_id] = (topic_data['x'], topic_data['y'])
                    logger.info(f"Loaded coordinates for {len(coordinates)} topics")
                except Exception as e:
                    logger.warning(f"Failed to load coordinates: {e}")
            
            for topic_id, summary in tqdm(summaries.items(), desc="Loading topics"):
                topic_name = f"Topic {topic_id}"
                if summary.get('top_words'):
                    topic_name = " ".join(summary['top_words'][:3])
                
                # Get coordinates if available
                x_coord = None
                y_coord = None
                if topic_id in coordinates:
                    x_coord, y_coord = coordinates[topic_id]
                
                # Create Topic node with optional coordinates
                if x_coord is not None and y_coord is not None:
                    session.run("""
                        MERGE (t:Topic {topic_id: $topic_id})
                        SET t.name = $name,
                            t.size = $size,
                            t.top_words = $top_words,
                            t.sample_titles = $sample_titles,
                            t.x = $x,
                            t.y = $y
                    """, {
                        'topic_id': int(topic_id),
                        'name': topic_name,
                        'size': summary['size'],
                        'top_words': summary['top_words'],
                        'sample_titles': summary['sample_titles'],
                        'x': x_coord,
                        'y': y_coord
                    })
                else:
                    session.run("""
                        MERGE (t:Topic {topic_id: $topic_id})
                        SET t.name = $name,
                            t.size = $size,
                            t.top_words = $top_words,
                            t.sample_titles = $sample_titles
                    """, {
                        'topic_id': int(topic_id),
                        'name': topic_name,
                        'size': summary['size'],
                        'top_words': summary['top_words'],
                        'sample_titles': summary['sample_titles']
                    })
            
            logger.info(f"Loaded {len(summaries)} topic nodes")
    
    def create_topic_relationships(self, chunks_file: Path):
        """Create relationships between messages and topics."""
        with self.driver.session() as session:
            with jsonlines.open(chunks_file) as reader:
                for chunk in tqdm(reader, desc="Creating topic relationships"):
                    cluster_id = chunk.get('cluster_id')
                    if cluster_id is not None and cluster_id != -1:
                        session.run("""
                            MATCH (m:Message {message_id: $message_id})
                            MATCH (t:Topic {topic_id: $topic_id})
                            MERGE (t)-[:SUMMARIZES]->(m)
                        """, {
                            'message_id': chunk['message_id'],
                            'topic_id': int(cluster_id)
                        })
            
            logger.info("Created topic-message relationships")
    
    def create_chat_topic_relationships(self, chunks_file: Path):
        """Create direct Chat→Topic relationships for each chat and its clusters."""
        with self.driver.session() as session:
            pairs = set()
            # Gather unique (chat_id, topic_id) pairs
            with jsonlines.open(chunks_file) as reader:
                for chunk in reader:
                    cid = chunk.get('cluster_id')
                    if cid is not None and cid != -1:
                        pairs.add((chunk['chat_id'], int(cid)))
            # Create relationships
            for chat_id, topic_id in pairs:
                session.run("""
                    MATCH (c:Chat {chat_id: $chat_id})
                    MATCH (t:Topic {topic_id: $topic_id})
                    MERGE (c)-[:HAS_TOPIC]->(t)
                """, {'chat_id': chat_id, 'topic_id': topic_id})
            logger.info(f"Created {len(pairs)} Chat→Topic relationships")
    
    def create_chat_similarity_relationships(self, chunks_file: Path, similarity_threshold: float = 0.8):
        """Compute per-chat embeddings and create Chat→Chat similarity edges above threshold."""
        # Aggregate embeddings per chat
        chat_sums = {}
        counts = {}
        with jsonlines.open(chunks_file) as reader:
            for chunk in reader:
                emb = chunk.get('embedding')
                if emb is None:
                    continue
                cid = chunk['chat_id']
                vec = np.array(emb, dtype=float)
                if cid in chat_sums:
                    chat_sums[cid] += vec
                    counts[cid] += 1
                else:
                    chat_sums[cid] = vec.copy()
                    counts[cid] = 1
        # Compute averages
        chat_vecs = {cid: chat_sums[cid] / counts[cid] for cid in chat_sums}
        chat_ids = list(chat_vecs.keys())
        n = len(chat_ids)
        rel_count = 0
        # Create similarity relationships for pairs above threshold
        with self.driver.session() as session:
            for i in range(n):
                id1 = chat_ids[i]
                v1 = chat_vecs[id1]
                norm1 = np.linalg.norm(v1)
                if norm1 == 0:
                    continue
                for j in range(i+1, n):
                    id2 = chat_ids[j]
                    v2 = chat_vecs[id2]
                    norm2 = np.linalg.norm(v2)
                    if norm2 == 0:
                        continue
                    sim = float(np.dot(v1, v2) / (norm1 * norm2))
                    if sim >= similarity_threshold:
                        session.run("""
                            MATCH (c1:Chat {chat_id: $chat1})
                            MATCH (c2:Chat {chat_id: $chat2})
                            MERGE (c1)-[r:SIMILAR_TO]->(c2)
                            SET r.score = $sim
                        """, {'chat1': id1, 'chat2': id2, 'sim': sim})
                        rel_count += 1
        logger.info(f"Created {rel_count} Chat↔Chat similarity relationships (threshold={similarity_threshold})")
    
    def create_similarity_relationships(self, similarity_threshold: float = 0.8):
        """Create similarity relationships between messages based on embeddings."""
        # This would require loading embeddings and computing similarities
        # For now, we'll skip this to keep it simple
        logger.info("Skipping similarity relationships (not implemented)")
    
    def load_pipeline(self, clear_existing: bool = True):
        """Run the complete loading pipeline."""
        try:
            # Connect to Neo4j
            self.connect()
            
            # Clear existing data if requested
            if clear_existing:
                self.clear_database()
            
            # Create constraints
            self.create_constraints()
            
            # Load data files
            chunks_file = self.embeddings_dir / "chunks_with_clusters.jsonl"
            summaries_file = self.embeddings_dir / "cluster_summaries.json"
            topics_with_coords_file = Path("data/processed/topics_with_coords.jsonl")
            
            if not chunks_file.exists():
                raise FileNotFoundError(f"No chunks file found at {chunks_file}")
            
            if not summaries_file.exists():
                raise FileNotFoundError(f"No summaries file found at {summaries_file}")
            
            # Load data into Neo4j
            self.load_chats(chunks_file)
            self.load_messages(chunks_file)
            self.load_topics(summaries_file, topics_with_coords_file)
            self.create_topic_relationships(chunks_file)
            # Create direct Chat→Topic edges
            self.create_chat_topic_relationships(chunks_file)
            # Optionally create Chat↔Chat similarity edges if configured
            if getattr(self, 'chat_similarity', False):
                thresh = getattr(self, 'similarity_threshold', 0.8)
                self.create_chat_similarity_relationships(chunks_file, thresh)
            
            logger.info("Successfully loaded data into Neo4j")
            
            # Get statistics
            stats = self.get_graph_stats()
            logger.info(f"Graph statistics: {stats}")
            
            return stats
            
        finally:
            self.close()
    
    def get_graph_stats(self) -> Dict:
        """Get statistics about the loaded graph."""
        with self.driver.session() as session:
            stats = {}
            
            # Count nodes by type
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
            """)
            
            for record in result:
                stats[f"{record['type']}_count"] = record['count']
            
            # Count relationships by type
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
            """)
            
            for record in result:
                stats[f"{record['type']}_count"] = record['count']
            
            return stats


@click.command()
@click.option('--uri', help='Neo4j URI')
@click.option('--user', help='Neo4j username')
@click.option('--password', help='Neo4j password')
@click.option('--embeddings-dir', default='data/embeddings', help='Directory with embeddings data')
@click.option('--clear', is_flag=True, help='Clear existing data before loading')
@click.option('--chat-similarity', is_flag=True, help='Compute Chat↔Chat similarity edges')
@click.option('--similarity-threshold', default=0.8, show_default=True, help='Threshold for chat similarity [0,1]')
def main(uri: str, user: str, password: str, embeddings_dir: str, clear: bool,
         chat_similarity: bool, similarity_threshold: float):
    """Load processed data into Neo4j graph database."""
    
    loader = Neo4jGraphLoader(uri, user, password, embeddings_dir)
    # Configure optional chat similarity computation
    loader.chat_similarity = chat_similarity
    loader.similarity_threshold = similarity_threshold
    try:
        stats = loader.load_pipeline(clear_existing=clear)
        logger.info("Graph loading completed successfully!")
        logger.info(f"Final stats: {stats}")
    except Exception as e:
        logger.error(f"Graph loading failed: {e}")
        raise


if __name__ == "__main__":
    main() 