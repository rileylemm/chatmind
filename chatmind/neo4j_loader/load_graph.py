#!/usr/bin/env python3
"""
Neo4j Graph Loader - Dual Layer Graph Strategy

Loads processed chat data into Neo4j with two layers:
1. Raw Layer: Chat and Message nodes with full content (no chunking)
2. Chunk Layer: Chunk nodes with embeddings and semantic processing

This enables both conversation-level analysis and semantic search capabilities.
"""

import json
import jsonlines
import pickle
import hashlib
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
    """Loads chat data into Neo4j knowledge graph with dual layer strategy."""
    
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
    
    def _generate_content_hash(self, chat_data: Dict) -> str:
        """Generate a content hash for a chat based on its content."""
        import hashlib
        import json
        
        # Create a hashable representation of the chat
        chat_content = {
            'title': chat_data.get('title', ''),
            'messages': [
                {
                    'id': msg.get('id', ''),
                    'content': msg.get('content', ''),
                    'role': msg.get('role', '')
                }
                for msg in chat_data.get('messages', [])
            ]
        }
        
        # Generate hash
        content_str = json.dumps(chat_content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def create_constraints(self):
        """Create database constraints and indexes for dual layer schema."""
        with self.driver.session() as session:
            # Raw Layer constraints
            session.run("CREATE CONSTRAINT chat_id IF NOT EXISTS FOR (c:Chat) REQUIRE c.chat_id IS UNIQUE")
            session.run("CREATE CONSTRAINT message_id IF NOT EXISTS FOR (m:Message) REQUIRE m.message_id IS UNIQUE")
            
            # Chunk Layer constraints
            session.run("CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (ch:Chunk) REQUIRE ch.chunk_id IS UNIQUE")
            
            # Semantic Layer constraints
            session.run("CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE")
            session.run("CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (tag:Tag) REQUIRE tag.name IS UNIQUE")
            
            # Create indexes for better performance
            session.run("CREATE INDEX chat_title IF NOT EXISTS FOR (c:Chat) ON (c.title)")
            session.run("CREATE INDEX message_role IF NOT EXISTS FOR (m:Message) ON (m.role)")
            session.run("CREATE INDEX message_timestamp IF NOT EXISTS FOR (m:Message) ON (m.timestamp)")
            session.run("CREATE INDEX chunk_source_message IF NOT EXISTS FOR (ch:Chunk) ON (ch.source_message_id)")
            session.run("CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)")
            session.run("CREATE INDEX tag_name IF NOT EXISTS FOR (tag:Tag) ON (tag.name)")
            
            logger.info("Created database constraints and indexes for dual layer schema")
    
    def load_raw_layer(self, chats_file: Path, chat_coords_file: Path = None) -> None:
        """Load raw layer: Chat and Message nodes from chats.jsonl."""
        logger.info("Loading raw layer (Chat and Message nodes)...")
        
        # Load chat coordinates if available
        chat_coords = {}
        if chat_coords_file and chat_coords_file.exists():
            try:
                with jsonlines.open(chat_coords_file) as reader:
                    for coord_data in reader:
                        chat_id = coord_data.get('chat_id')
                        if chat_id:
                            chat_coords[chat_id] = {
                                'x': coord_data.get('x'),
                                'y': coord_data.get('y')
                            }
                logger.info(f"Loaded coordinates for {len(chat_coords)} chats")
            except Exception as e:
                logger.warning(f"Failed to load chat coordinates: {e}")
        
        with self.driver.session() as session:
            with jsonlines.open(chats_file) as reader:
                for chat_data in tqdm(reader, desc="Loading raw layer"):
                    content_hash = self._generate_content_hash(chat_data)
                    chat_id = f"chat_{content_hash[:16]}"
                    coords = chat_coords.get(chat_id, {})
                    
                    session.run("""
                        MERGE (c:Chat {chat_id: $chat_id})
                        SET c.title = $title,
                            c.create_time = $create_time,
                            c.update_time = $update_time,
                            c.data_lake_id = $data_lake_id,
                            c.x = $x,
                            c.y = $y
                    """, {
                        'chat_id': chat_id,
                        'title': chat_data.get('title', 'Untitled'),
                        'create_time': chat_data.get('create_time'),
                        'update_time': chat_data.get('update_time'),
                        'data_lake_id': chat_id,
                        'x': coords.get('x'),
                        'y': coords.get('y')
                    })
                    
                    messages = chat_data.get('messages', [])
                    for message in messages:
                        message_id = message.get('id')
                        if not message_id:
                            continue
                            
                        session.run("""
                            MERGE (m:Message {message_id: $message_id})
                            SET m.content = $content,
                                m.role = $role,
                                m.timestamp = $timestamp,
                                m.chat_id = $chat_id
                        """, {
                            'message_id': message_id,
                            'content': message.get('content', ''),
                            'role': message.get('role', 'user'),
                            'timestamp': message.get('timestamp'),
                            'chat_id': chat_id
                        })
                        
                        session.run("""
                            MATCH (m:Message {message_id: $message_id})
                            MATCH (c:Chat {chat_id: $chat_id})
                            MERGE (c)-[:CONTAINS]->(m)
                        """, {
                            'message_id': message_id,
                            'chat_id': chat_id
                        })
                        
                        parent_id = message.get('parent_id')
                        if parent_id:
                            session.run("""
                                MATCH (m:Message {message_id: $message_id})
                                MATCH (p:Message {message_id: $parent_id})
                                MERGE (p)-[:REPLIES_TO]->(m)
                            """, {
                                'message_id': message_id,
                                'parent_id': parent_id
                            })
    
    def load_chunk_layer(self, chunks_file: Path):
        """Load Chunk nodes and link to source messages (Layer 2)."""
        with self.driver.session() as session:
            chunk_count = 0
            
            with jsonlines.open(chunks_file) as reader:
                for chunk in tqdm(reader, desc="Loading chunk layer"):
                    # Generate chunk_id from message_id and content
                    message_id = chunk['message_id']
                    content_hash = hashlib.sha256(chunk['content'].encode()).hexdigest()[:8]
                    chunk_id = f"{message_id}_{content_hash}"
                    
                    # Create Chunk node
                    session.run("""
                        MERGE (ch:Chunk {chunk_id: $chunk_id})
                        SET ch.text = $text,
                            ch.embedding = $embedding,
                            ch.source_message_id = $source_message_id,
                            ch.cluster_id = $cluster_id,
                            ch.chat_id = $chat_id
                    """, {
                        'chunk_id': chunk_id,
                        'text': chunk['content'],
                        'embedding': chunk.get('embedding'),
                        'source_message_id': message_id,
                        'cluster_id': chunk.get('cluster_id', -1),
                        'chat_id': chunk['chat_id']
                    })
                    
                    # Create relationship to source Message
                    session.run("""
                        MATCH (m:Message {message_id: $source_message_id})
                        MATCH (ch:Chunk {chunk_id: $chunk_id})
                        MERGE (m)-[:HAS_CHUNK]->(ch)
                    """, {
                        'source_message_id': message_id,
                        'chunk_id': chunk_id
                    })
                    
                    chunk_count += 1
            
            logger.info(f"Loaded {chunk_count} chunk nodes in chunk layer")
    
    def load_tags(self, chunks_file: Path):
        """Load tag nodes and relationships from tagged chunks."""
        with self.driver.session() as session:
            tag_count = 0
            relationship_count = 0
            
            with jsonlines.open(chunks_file) as reader:
                for chunk in tqdm(reader, desc="Loading tags"):
                    if not chunk.get('tags'):
                        continue
                    
                    tags = chunk['tags']
                    if isinstance(tags, str):
                        # Handle case where tags might be a string
                        tags = [tags]
                    elif not isinstance(tags, list):
                        continue
                    
                    # Generate chunk_id from message_id and content
                    message_id = chunk['message_id']
                    content_hash = hashlib.sha256(chunk['content'].encode()).hexdigest()[:8]
                    chunk_id = f"{message_id}_{content_hash}"
                    
                    for tag in tags:
                        # Clean tag name (remove # if present)
                        tag_name = tag.replace('#', '') if tag.startswith('#') else tag
                        
                        # Create Tag node
                        session.run("""
                            MERGE (tag:Tag {name: $tag_name})
                            SET tag.count = COALESCE(tag.count, 0) + 1
                        """, {
                            'tag_name': tag_name
                        })
                        
                        # Create relationship between Chunk and Tag
                        session.run("""
                            MATCH (ch:Chunk {chunk_id: $chunk_id})
                            MATCH (tag:Tag {name: $tag_name})
                            MERGE (ch)-[:TAGGED_WITH]->(tag)
                        """, {
                            'chunk_id': chunk_id,
                            'tag_name': tag_name
                        })
                        
                        relationship_count += 1
                    
                    tag_count += len(tags)
            
            logger.info(f"Loaded {tag_count} tag relationships across all chunks")
    
    def load_topics(self, chunks_file: Path, topics_with_coords_file: Path = None):
        """Load topic nodes from chunks data with optional coordinates."""
        with self.driver.session() as session:
            # Extract topics from chunks
            topics = {}
            with jsonlines.open(chunks_file) as reader:
                for chunk in reader:
                    cluster_id = chunk.get('cluster_id')
                    if cluster_id is not None and cluster_id != -1:
                        if cluster_id not in topics:
                            topics[cluster_id] = {
                                'size': 0,
                                'top_words': [],
                                'sample_titles': []
                            }
                        topics[cluster_id]['size'] += 1
            
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
            
            for topic_id, topic_data in tqdm(topics.items(), desc="Loading topics"):
                topic_name = f"Topic {topic_id}"
                
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
                            t.x = $x,
                            t.y = $y
                    """, {
                        'topic_id': int(topic_id),
                        'name': topic_name,
                        'size': topic_data['size'],
                        'x': x_coord,
                        'y': y_coord
                    })
                else:
                    session.run("""
                        MERGE (t:Topic {topic_id: $topic_id})
                        SET t.name = $name,
                            t.size = $size
                    """, {
                        'topic_id': int(topic_id),
                        'name': topic_name,
                        'size': topic_data['size']
                    })
            
            logger.info(f"Loaded {len(topics)} topic nodes")
    
    def create_topic_relationships(self, chunks_file: Path):
        """Create relationships between chunks and topics."""
        with self.driver.session() as session:
            with jsonlines.open(chunks_file) as reader:
                for chunk in tqdm(reader, desc="Creating topic relationships"):
                    cluster_id = chunk.get('cluster_id')
                    if cluster_id is not None and cluster_id != -1:
                        # Generate chunk_id from message_id and content
                        message_id = chunk['message_id']
                        content_hash = hashlib.sha256(chunk['content'].encode()).hexdigest()[:8]
                        chunk_id = f"{message_id}_{content_hash}"
                        
                        session.run("""
                            MATCH (ch:Chunk {chunk_id: $chunk_id})
                            MATCH (t:Topic {topic_id: $topic_id})
                            MERGE (t)-[:SUMMARIZES]->(ch)
                        """, {
                            'chunk_id': chunk_id,
                            'topic_id': int(cluster_id)
                        })
            
            logger.info("Created topic-chunk relationships")
    
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
    
    def create_has_chunk_relationships(self, chunks_file: Path):
        """Create HAS_CHUNK relationships between Message and Chunk nodes."""
        logger.info("Creating HAS_CHUNK relationships between messages and chunks...")
        
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
            
            # Process in batches
            batch_size = 500
            total_relationships = 0
            
            for i in range(0, len(source_ids), batch_size):
                batch = source_ids[i:i + batch_size]
                
                for source_id in batch:
                    # Extract the actual message_id from source_message_id
                    # source_message_id format: "message_id_chunk_index"
                    if '_' in source_id:
                        message_id = source_id.rsplit('_', 1)[0]
                    else:
                        message_id = source_id
                    
                    # Create the relationship
                    create_relationship_query = """
                    MATCH (m:Message {message_id: $message_id})
                    MATCH (chunk:Chunk {source_message_id: $source_id})
                    MERGE (m)-[:HAS_CHUNK]->(chunk)
                    """
                    
                    session.run(create_relationship_query, message_id=message_id, source_id=source_id)
                
                total_relationships += len(batch)
                if (i + batch_size) % 5000 == 0 or (i + batch_size) >= len(source_ids):
                    logger.info(f"Processed {total_relationships} source IDs, created {total_relationships} relationships...")
            
            logger.info(f"Created {total_relationships} HAS_CHUNK relationships")

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
    
    def load_precalculated_similarities(self, similarities_file: Path):
        """Load pre-calculated similarity relationships from file."""
        logger.info("🔗 Loading pre-calculated similarity relationships...")
        
        if not similarities_file.exists():
            logger.warning(f"Similarities file not found: {similarities_file}")
            return
        
        rel_count = 0
        with self.driver.session() as session:
            with jsonlines.open(similarities_file) as reader:
                for similarity in tqdm(reader, desc="Loading similarities"):
                    session.run("""
                        MATCH (c1:Chat {chat_id: $chat1})
                        MATCH (c2:Chat {chat_id: $chat2})
                        MERGE (c1)-[r:SIMILAR_TO]->(c2)
                        SET r.score = $sim
                    """, {
                        'chat1': similarity['chat1_id'],
                        'chat2': similarity['chat2_id'],
                        'sim': similarity['similarity']
                    })
                    rel_count += 1
        
        logger.info(f"✅ Loaded {rel_count} pre-calculated similarity relationships")
    
    def load_pipeline(self):
        """Load all data into Neo4j following the dual layer strategy."""
        logger.info("Starting dual layer graph loading pipeline...")
        
        try:
            # Connect to Neo4j
            self.connect()
            
            # Clear existing data
            self.clear_database()
            
            # Create constraints
            self.create_constraints()
            
            # Define file paths
            chats_file = Path("data/processed/chats.jsonl")
            chunks_file = Path("data/processed/processed_tagged_chunks.jsonl")
            topics_file = Path("data/processed/topics_with_coords.jsonl")
            chat_coords_file = Path("data/processed/chats_with_coords.jsonl")
            similarities_file = Path("data/processed/chat_similarities.jsonl")
            
            # Step 1: Load raw layer (Chat and Message nodes)
            if chats_file.exists():
                self.load_raw_layer(chats_file, chat_coords_file)
            else:
                logger.warning(f"Chats file not found: {chats_file}")
            
            # Step 2: Load chunk layer (Chunk nodes)
            if chunks_file.exists():
                self.load_chunk_layer(chunks_file)
            else:
                logger.warning(f"Chunks file not found: {chunks_file}")
            
            # Step 2.5: Create HAS_CHUNK relationships
            if chunks_file.exists():
                self.create_has_chunk_relationships(chunks_file)
            else:
                logger.warning(f"Chunks file not found: {chunks_file}")
            
            # Step 3: Load semantic layer (Tags and Topics)
            if chunks_file.exists():
                self.load_tags(chunks_file)
                self.load_topics(chunks_file, topics_file)
            else:
                logger.warning(f"Chunks file not found: {chunks_file}")
            
            # Step 4: Create semantic relationships
            if chunks_file.exists():
                self.create_topic_relationships(chunks_file)
                self.create_chat_topic_relationships(chunks_file)
            else:
                logger.warning(f"Chunks file not found: {chunks_file}")
            
            # Step 5: Load pre-calculated similarity relationships
            self.load_precalculated_similarities(similarities_file)
            
            logger.info("Dual layer graph loading pipeline completed!")
            
        finally:
            self.close()
    
    def get_graph_stats(self) -> Dict:
        """Get statistics about the loaded dual layer graph."""
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
    """Load processed data into Neo4j graph database with dual layer strategy."""
    
    loader = Neo4jGraphLoader(uri, user, password, embeddings_dir)
    # Configure optional chat similarity computation
    loader.chat_similarity = chat_similarity
    loader.similarity_threshold = similarity_threshold
    try:
        loader.load_pipeline()
        stats = loader.get_graph_stats()
        logger.info("Dual layer graph loading completed successfully!")
        logger.info(f"Final stats: {stats}")
    except Exception as e:
        logger.error(f"Graph loading failed: {e}")
        raise


if __name__ == "__main__":
    main() 