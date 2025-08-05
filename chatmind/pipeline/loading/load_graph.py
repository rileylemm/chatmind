#!/usr/bin/env python3
"""
Hybrid Neo4j Graph Database Loader

Loads processed data from the modular pipeline into Neo4j.
Optimized for hybrid architecture with Qdrant for embeddings.
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

# Import pipeline configuration
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import get_neo4j_config

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridNeo4jGraphLoader:
    """Hybrid loader for modular pipeline data into Neo4j (without embeddings)."""
    
    def __init__(self, 
                 uri: str = None,
                 user: str = None,
                 password: str = None,
                 processed_dir: str = "data/processed"):
        
        # Load configuration with proper precedence
        neo4j_config = get_neo4j_config()
        
        self.uri = uri or neo4j_config['uri']
        self.user = user or neo4j_config['user']
        self.password = password or neo4j_config['password']
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
        logger.info(f"Neo4j connection config:")
        logger.info(f"  URI: {self.uri}")
        logger.info(f"  User: {self.user}")
        logger.info(f"  Password: {'*' * len(self.password) if self.password else 'NOT_SET'}")
        logger.info(f"  Processed directory: {self.processed_dir}")
        
        # Use modular directory structure
        self.loading_dir = self.processed_dir / "loading"
        self.loading_dir.mkdir(parents=True, exist_ok=True)
        
        if NEO4J_AVAILABLE:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        else:
            self.driver = None
    
    def _generate_content_hash(self, data: Dict) -> str:
        """Generate a content hash for tracking."""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _get_processed_hashes(self) -> Dict[str, set]:
        """Get hashes of already processed data by type."""
        hash_file = self.loading_dir / "neo4j_loading_hashes.pkl"
        if hash_file.exists():
            with open(hash_file, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_processed_hashes(self, hashes: Dict[str, set]) -> None:
        """Save hashes of processed data by type."""
        hash_file = self.loading_dir / "neo4j_loading_hashes.pkl"
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
        """Load data from a JSON file with error handling."""
        data = {}
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"✅ Loaded {description}")
            except Exception as e:
                logger.error(f"❌ Failed to load {description}: {e}")
        else:
            logger.warning(f"⚠️  {description} file not found: {file_path}")
        return data
    
    def _load_all_pipeline_data(self) -> Dict[str, any]:
        """Load all data from the modular pipeline (excluding embeddings)."""
        logger.info("📖 Loading pipeline data for Neo4j...")
        
        data = {
            # Core data
            'chats': self._load_data_file(
                self.processed_dir / "ingestion" / "chats.jsonl", 
                "chats"
            ),
            'chunks': self._load_data_file(
                self.processed_dir / "chunking" / "chunks.jsonl", 
                "chunks"
            ),
            'cluster_positions': self._load_data_file(
                self.processed_dir / "positioning" / "cluster_positions.jsonl", 
                "cluster positions"
            ),
            
            # Tagging data (post-processed message tags)
            'processed_tags': self._load_data_file(
                self.processed_dir / "tagging" / "processed_tags.jsonl", 
                "processed tags"
            ),
            
            # Summarization data
            'cluster_summaries': self._load_json_file(
                self.processed_dir / "cluster_summarization" / "cluster_summaries.json", 
                "cluster summaries"
            ),
            'chat_summaries': self._load_json_file(
                self.processed_dir / "chat_summarization" / "chat_summaries.json", 
                "chat summaries"
            ),
            
            # Positioning data
            'chat_positions': self._load_data_file(
                self.processed_dir / "positioning" / "chat_positions.jsonl", 
                "chat positions"
            ),
            'cluster_positions': self._load_data_file(
                self.processed_dir / "positioning" / "cluster_positions.jsonl", 
                "cluster positions"
            ),
            
            # Similarity data
            'chat_similarities': self._load_data_file(
                self.processed_dir / "similarity" / "chat_similarities.jsonl", 
                "chat similarities"
            ),
            'cluster_similarities': self._load_data_file(
                self.processed_dir / "similarity" / "cluster_similarities.jsonl", 
                "cluster similarities"
            ),
        }
        
        return data
    
    def _create_chat_nodes(self, session, chats: List[Dict]) -> Dict[str, str]:
        """Create Chat nodes with enhanced properties."""
        chat_mapping = {}
        
        for chat in tqdm(chats, desc="Creating Chat nodes"):
            chat_hash = chat.get('content_hash', '')
            chat_id = chat.get('chat_id', chat_hash)  # Use chat_id if available
            title = chat.get('title', 'Untitled')
            create_time = chat.get('create_time', '')
            source_file = chat.get('source_file', '')
            message_count = len(chat.get('messages', []))
            
            # Create Chat node with enhanced properties
            query = """
            MERGE (c:Chat {chat_hash: $chat_hash})
            SET c.chat_id = $chat_id,
                c.title = $title,
                c.create_time = $create_time,
                c.source_file = $source_file,
                c.message_count = $message_count,
                c.loaded_at = datetime()
            RETURN c
            """
            
            result = session.run(query, {
                'chat_hash': chat_hash,
                'chat_id': chat_id,
                'title': title,
                'create_time': create_time,
                'source_file': source_file,
                'message_count': message_count
            })
            
            chat_mapping[chat_hash] = chat_hash
        
        logger.info(f"Created {len(chat_mapping)} Chat nodes")
        return chat_mapping
    
    def _create_message_nodes(self, session, chats: List[Dict], chat_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Message nodes with enhanced properties."""
        message_mapping = {}
        
        for chat in tqdm(chats, desc="Creating Message nodes"):
            chat_hash = chat_mapping.get(chat.get('content_hash', ''), '')
            chat_id = chat.get('chat_id', chat_hash)
            messages = chat.get('messages', [])
            
            for message in messages:
                message_id = message.get('id', '')
                content = message.get('content', '')
                role = message.get('role', '')
                timestamp = message.get('timestamp', '')
                parent_id = message.get('parent_id', '')
                
                # Generate message hash (same as chunking step)
                message_data = {
                    'content': content,
                    'chat_id': chat.get('content_hash', ''),
                    'message_id': message_id,
                    'role': role
                }
                message_hash = self._generate_content_hash(message_data)
                
                # Create Message node with enhanced properties
                query = """
                MERGE (m:Message {message_id: $message_id})
                SET m.message_hash = $message_hash,
                    m.content = $content,
                    m.role = $role,
                    m.timestamp = $timestamp,
                    m.parent_id = $parent_id,
                    m.chat_id = $chat_id,
                    m.content_length = $content_length,
                    m.loaded_at = datetime()
                WITH m
                MATCH (c:Chat {chat_hash: $chat_hash})
                MERGE (c)-[:CONTAINS]->(m)
                RETURN m
                """
                
                result = session.run(query, {
                    'message_id': message_id,
                    'message_hash': message_hash,
                    'content': content,
                    'role': role,
                    'timestamp': timestamp,
                    'parent_id': parent_id,
                    'chat_id': chat_id,
                    'content_length': len(content),
                    'chat_hash': chat_hash
                })
                
                message_mapping[message_id] = message_id  # Use message_id as key
        
        logger.info(f"Created {len(message_mapping)} Message nodes")
        return message_mapping
    
    def _create_chunk_nodes(self, session, chunks: List[Dict], message_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Chunk nodes with enhanced properties and cross-reference IDs."""
        chunk_mapping = {}
        
        for chunk in tqdm(chunks, desc="Creating Chunk nodes"):
            chunk_id = chunk.get('chunk_id', '')
            chunk_hash = chunk.get('chunk_hash', chunk_id)
            content = chunk.get('content', '')
            role = chunk.get('role', '')
            token_count = chunk.get('token_count', 0)
            message_hash = chunk.get('message_hash', '')
            chat_id = chunk.get('chat_id', '')
            message_id = chunk.get('message_id', '')
            
            # Create Chunk node with enhanced properties and cross-reference IDs
            query = """
            MERGE (ch:Chunk {chunk_id: $chunk_id})
            SET ch.chunk_hash = $chunk_hash,
                ch.content = $content,
                ch.role = $role,
                ch.token_count = $token_count,
                ch.chat_id = $chat_id,
                ch.message_id = $message_id,
                ch.message_hash = $message_hash,
                ch.content_length = $content_length,
                ch.loaded_at = datetime()
            RETURN ch
            """
            
            result = session.run(query, {
                'chunk_id': chunk_id,
                'chunk_hash': chunk_hash,
                'content': content,
                'role': role,
                'token_count': token_count,
                'chat_id': chat_id,
                'message_id': message_id,
                'message_hash': message_hash,
                'content_length': len(content)
            })
            
            # Create relationship to message using message_hash
            if message_hash:
                rel_query = """
                MATCH (ch:Chunk {chunk_id: $chunk_id})
                MATCH (m:Message {message_hash: $message_hash})
                MERGE (m)-[:HAS_CHUNK]->(ch)
                """
                session.run(rel_query, {
                    'chunk_id': chunk_id,
                    'message_hash': message_hash
                })
            
            chunk_mapping[chunk_id] = chunk_id
        
        logger.info(f"Created {len(chunk_mapping)} Chunk nodes")
        return chunk_mapping
    
    def _create_cluster_nodes(self, session, cluster_positions: List[Dict], chunk_mapping: Dict[str, str]) -> Dict[int, str]:
        """Create Cluster nodes with enhanced properties."""
        cluster_mapping = {}
        
        for item in tqdm(cluster_positions, desc="Creating Cluster nodes"):
            cluster_id = int(item.get('cluster_id', -1))
            x = item.get('x', 0.0)
            y = item.get('y', 0.0)
            cluster_hash = item.get('cluster_hash', '')
            summary_hash = item.get('summary_hash', '')
            
            # Create Cluster node with enhanced properties
            query = """
            MERGE (cl:Cluster {cluster_id: $cluster_id})
            SET cl.x = $x,
                cl.y = $y,
                cl.cluster_hash = $cluster_hash,
                cl.summary_hash = $summary_hash,
                cl.loaded_at = datetime()
            RETURN cl
            """
            
            result = session.run(query, {
                'cluster_id': cluster_id,
                'x': x,
                'y': y,
                'cluster_hash': cluster_hash,
                'summary_hash': summary_hash
            })
            
            cluster_mapping[cluster_id] = cluster_hash
        
        logger.info(f"Created {len(cluster_mapping)} Cluster nodes")
        return cluster_mapping
    
    def _create_tag_nodes(self, session, processed_tags: List[Dict], message_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Tag nodes and link them to both Messages and Chunks."""
        tag_mapping = {}
        
        for tag_entry in tqdm(processed_tags, desc="Creating Tag nodes"):
            message_hash = tag_entry.get('message_hash', '')
            tags_list = tag_entry.get('tags', [])
            topics = tag_entry.get('topics', [])
            domain = tag_entry.get('domain', 'other')
            complexity = tag_entry.get('complexity', 'medium')
            sentiment = tag_entry.get('sentiment', 'neutral')
            intent = tag_entry.get('intent', 'other')
            
            # Generate tag hash
            tag_data = {
                'message_hash': message_hash,
                'tags': tags_list,
                'topics': topics,
                'domain': domain
            }
            tag_hash = self._generate_content_hash(tag_data)
            
            # Create Tag node and link to Message
            query = """
            MERGE (t:Tag {tag_hash: $tag_hash})
            SET t.tags = $tags,
                t.topics = $topics,
                t.domain = $domain,
                t.complexity = $complexity,
                t.sentiment = $sentiment,
                t.intent = $intent,
                t.tag_count = $tag_count,
                t.loaded_at = datetime()
            WITH t
            MATCH (m:Message {message_hash: $message_hash})
            MERGE (t)-[:TAGS]->(m)
            WITH t, m
            MATCH (m)-[:CONTAINS]->(c:Chunk)
            MERGE (t)-[:TAGS_CHUNK]->(c)
            RETURN t
            """
            
            result = session.run(query, {
                'tag_hash': tag_hash,
                'tags': tags_list,
                'topics': topics,
                'domain': domain,
                'complexity': complexity,
                'sentiment': sentiment,
                'intent': intent,
                'tag_count': len(tags_list),
                'message_hash': message_hash
            })
            
            tag_mapping[message_hash] = tag_hash
        
        logger.info(f"Created {len(tag_mapping)} Tag nodes with chunk relationships")
        return tag_mapping
    
    def _create_summary_nodes(self, session, summaries: Dict, cluster_mapping: Dict[int, str]) -> Dict[int, str]:
        """Create Summary nodes with enhanced properties."""
        summary_mapping = {}
        
        for cluster_id_str, summary_data in tqdm(summaries.items(), desc="Creating Summary nodes"):
            cluster_id = int(cluster_id_str)
            summary_text = summary_data.get('summary', '')
            domain = summary_data.get('domain', 'other')
            topics = summary_data.get('topics', [])
            complexity = summary_data.get('complexity', 'medium')
            key_points = summary_data.get('key_points', [])
            common_tags = summary_data.get('common_tags', [])
            
            # Generate summary hash
            summary_hash_data = {
                'cluster_id': cluster_id,
                'summary': summary_text,
                'domain': domain
            }
            summary_hash = self._generate_content_hash(summary_hash_data)
            
            # Create Summary node with enhanced properties
            query = """
            MERGE (s:Summary {summary_hash: $summary_hash})
            SET s.summary = $summary,
                s.domain = $domain,
                s.topics = $topics,
                s.complexity = $complexity,
                s.key_points = $key_points,
                s.common_tags = $common_tags,
                s.summary_length = $summary_length,
                s.loaded_at = datetime()
            WITH s
            MATCH (cl:Cluster {cluster_id: $cluster_id})
            MERGE (s)-[:SUMMARIZES]->(cl)
            RETURN s
            """
            
            result = session.run(query, {
                'summary_hash': summary_hash,
                'summary': summary_text,
                'domain': domain,
                'topics': topics,
                'complexity': complexity,
                'key_points': key_points,
                'common_tags': common_tags,
                'summary_length': len(summary_text),
                'cluster_id': cluster_id
            })
            
            summary_mapping[cluster_id] = summary_hash
        
        logger.info(f"Created {len(summary_mapping)} Summary nodes")
        return summary_mapping
    
    def _create_chat_summary_nodes(self, session, chat_summaries: Dict, chat_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Chat Summary nodes."""
        chat_summary_mapping = {}
        
        for chat_id, summary_data in tqdm(chat_summaries.items(), desc="Creating Chat Summary nodes"):
            summary_text = summary_data.get('summary', '')
            domain = summary_data.get('domain', 'other')
            topics = summary_data.get('topics', [])
            complexity = summary_data.get('complexity', 'medium')
            key_points = summary_data.get('key_points', [])
            
            # Generate chat summary hash
            chat_summary_hash_data = {
                'chat_id': chat_id,
                'summary': summary_text,
                'domain': domain
            }
            chat_summary_hash = self._generate_content_hash(chat_summary_hash_data)
            
            # Create Chat Summary node
            query = """
            MERGE (cs:ChatSummary {chat_summary_hash: $chat_summary_hash})
            SET cs.summary = $summary,
                cs.domain = $domain,
                cs.topics = $topics,
                cs.complexity = $complexity,
                cs.key_points = $key_points,
                cs.summary_length = $summary_length,
                cs.loaded_at = datetime()
            WITH cs
            MATCH (c:Chat {chat_hash: $chat_hash})
            MERGE (cs)-[:SUMMARIZES_CHAT]->(c)
            RETURN cs
            """
            
            result = session.run(query, {
                'chat_summary_hash': chat_summary_hash,
                'summary': summary_text,
                'domain': domain,
                'topics': topics,
                'complexity': complexity,
                'key_points': key_points,
                'summary_length': len(summary_text),
                'chat_hash': chat_id
            })
            
            chat_summary_mapping[chat_id] = chat_summary_hash
        
        logger.info(f"Created {len(chat_summary_mapping)} Chat Summary nodes")
        return chat_summary_mapping
    
    def _create_positioning_nodes(self, session, chat_positions: List[Dict], cluster_positions: List[Dict]) -> None:
        """Create positioning data nodes."""
        
        # Create chat positioning nodes
        for position in tqdm(chat_positions, desc="Creating Chat Position nodes"):
            chat_id = position.get('chat_id', '')
            umap_x = position.get('umap_x', 0.0)
            umap_y = position.get('umap_y', 0.0)
            
            query = """
            MATCH (c:Chat {chat_hash: $chat_id})
            SET c.position_x = $umap_x,
                c.position_y = $umap_y
            """
            
            session.run(query, {
                'chat_id': chat_id,
                'umap_x': umap_x,
                'umap_y': umap_y
            })
        
        # Create cluster positioning nodes
        for position in tqdm(cluster_positions, desc="Creating Cluster Position nodes"):
            cluster_id = position.get('cluster_id', -1)
            umap_x = position.get('umap_x', 0.0)
            umap_y = position.get('umap_y', 0.0)
            
            query = """
            MATCH (cl:Cluster {cluster_id: $cluster_id})
            SET cl.position_x = $umap_x,
                cl.position_y = $umap_y
            """
            
            session.run(query, {
                'cluster_id': cluster_id,
                'umap_x': umap_x,
                'umap_y': umap_y
            })
        
        logger.info("Created positioning data")
    
    def _create_similarity_relationships(self, session, chat_similarities: List[Dict], cluster_similarities: List[Dict]) -> None:
        """Create similarity relationships with threshold filtering for optimal visualization."""
        
        # Filter for high-quality similarities (threshold: 0.7)
        high_threshold = 0.7
        medium_threshold = 0.5
        
        # Create chat similarity relationships
        high_similarities = 0
        medium_similarities = 0
        
        for similarity in tqdm(chat_similarities, desc="Creating Chat Similarity relationships"):
            chat1_id = similarity.get('chat1_id', '')
            chat2_id = similarity.get('chat2_id', '')
            similarity_score = similarity.get('similarity', 0.0)
            
            # Only create relationships for meaningful similarities
            if similarity_score >= medium_threshold:
                # Use different queries for different relationship types
                if similarity_score >= high_threshold:
                    query = """
                    MATCH (c1:Chat {chat_hash: $chat1_id})
                    MATCH (c2:Chat {chat_hash: $chat2_id})
                    MERGE (c1)-[r:SIMILAR_TO_CHAT_HIGH]->(c2)
                    SET r.similarity_score = $similarity_score,
                        r.threshold_level = $threshold_level,
                        r.loaded_at = datetime()
                    """
                else:
                    query = """
                    MATCH (c1:Chat {chat_hash: $chat1_id})
                    MATCH (c2:Chat {chat_hash: $chat2_id})
                    MERGE (c1)-[r:SIMILAR_TO_CHAT_MEDIUM]->(c2)
                    SET r.similarity_score = $similarity_score,
                        r.threshold_level = $threshold_level,
                        r.loaded_at = datetime()
                    """
                
                session.run(query, {
                    'chat1_id': chat1_id,
                    'chat2_id': chat2_id,
                    'similarity_score': similarity_score,
                    'threshold_level': 'high' if similarity_score >= high_threshold else 'medium'
                })
                
                if similarity_score >= high_threshold:
                    high_similarities += 1
                else:
                    medium_similarities += 1
        
        # Create cluster similarity relationships
        cluster_high_similarities = 0
        cluster_medium_similarities = 0
        
        for similarity in tqdm(cluster_similarities, desc="Creating Cluster Similarity relationships"):
            cluster1_id = similarity.get('cluster1_id', -1)
            cluster2_id = similarity.get('cluster2_id', -1)
            similarity_score = similarity.get('similarity', 0.0)
            
            # Only create relationships for meaningful similarities
            if similarity_score >= medium_threshold:
                # Use different queries for different relationship types
                if similarity_score >= high_threshold:
                    query = """
                    MATCH (cl1:Cluster {cluster_id: $cluster1_id})
                    MATCH (cl2:Cluster {cluster_id: $cluster2_id})
                    MERGE (cl1)-[r:SIMILAR_TO_CLUSTER_HIGH]->(cl2)
                    SET r.similarity_score = $similarity_score,
                        r.threshold_level = $threshold_level,
                        r.loaded_at = datetime()
                    """
                else:
                    query = """
                    MATCH (cl1:Cluster {cluster_id: $cluster1_id})
                    MATCH (cl2:Cluster {cluster_id: $cluster2_id})
                    MERGE (cl1)-[r:SIMILAR_TO_CLUSTER_MEDIUM]->(cl2)
                    SET r.similarity_score = $similarity_score,
                        r.threshold_level = $threshold_level,
                        r.loaded_at = datetime()
                    """
                
                session.run(query, {
                    'cluster1_id': cluster1_id,
                    'cluster2_id': cluster2_id,
                    'similarity_score': similarity_score,
                    'threshold_level': 'high' if similarity_score >= high_threshold else 'medium'
                })
                
                if similarity_score >= high_threshold:
                    cluster_high_similarities += 1
                else:
                    cluster_medium_similarities += 1
        
        logger.info(f"Created similarity relationships:")
        logger.info(f"  💬 Chat High Similarities: {high_similarities}")
        logger.info(f"  💬 Chat Medium Similarities: {medium_similarities}")
        logger.info(f"  🎯 Cluster High Similarities: {cluster_high_similarities}")
        logger.info(f"  🎯 Cluster Medium Similarities: {cluster_medium_similarities}")
        logger.info(f"  📊 Total relationships created: {high_similarities + medium_similarities + cluster_high_similarities + cluster_medium_similarities}")
    
    def _create_constraints(self, session) -> None:
        """Create Neo4j constraints and indexes for better performance."""
        try:
            # Create unique constraints
            constraints = [
                "CREATE CONSTRAINT chat_hash_unique IF NOT EXISTS FOR (c:Chat) REQUIRE c.chat_hash IS UNIQUE",
                "CREATE CONSTRAINT message_id_unique IF NOT EXISTS FOR (m:Message) REQUIRE m.message_id IS UNIQUE",
                "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (ch:Chunk) REQUIRE ch.chunk_id IS UNIQUE",
                "CREATE CONSTRAINT cluster_id_unique IF NOT EXISTS FOR (cl:Cluster) REQUIRE cl.cluster_id IS UNIQUE",
                "CREATE CONSTRAINT tag_hash_unique IF NOT EXISTS FOR (t:Tag) REQUIRE t.tag_hash IS UNIQUE",
                "CREATE CONSTRAINT summary_hash_unique IF NOT EXISTS FOR (s:Summary) REQUIRE s.summary_hash IS UNIQUE",
                "CREATE CONSTRAINT chat_summary_hash_unique IF NOT EXISTS FOR (cs:ChatSummary) REQUIRE cs.chat_summary_hash IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint already exists or failed: {e}")
            
            # Create indexes for better query performance
            indexes = [
                "CREATE INDEX chat_id_index IF NOT EXISTS FOR (c:Chat) ON (c.chat_id)",
                "CREATE INDEX message_chat_id_index IF NOT EXISTS FOR (m:Message) ON (m.chat_id)",
                "CREATE INDEX chunk_chat_id_index IF NOT EXISTS FOR (ch:Chunk) ON (ch.chat_id)",
                "CREATE INDEX chunk_message_id_index IF NOT EXISTS FOR (ch:Chunk) ON (ch.message_id)",
                "CREATE INDEX chunk_message_hash_index IF NOT EXISTS FOR (ch:Chunk) ON (ch.message_hash)",
                "CREATE INDEX cluster_umap_index IF NOT EXISTS FOR (cl:Cluster) ON (cl.umap_x, cl.umap_y)",
                "CREATE INDEX chat_umap_index IF NOT EXISTS FOR (c:Chat) ON (c.umap_x, c.umap_y)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.debug(f"Index already exists or failed: {e}")
            
            logger.info("✅ Created constraints and indexes")
        except Exception as e:
            logger.warning(f"Could not create constraints: {e}")
    
    def _check_neo4j_content(self, session) -> Dict[str, int]:
        """Check what's already loaded in Neo4j."""
        try:
            # Count existing nodes by type
            counts = {}
            node_types = ['Chat', 'Message', 'Chunk', 'Cluster', 'Tag', 'Summary', 'ChatSummary']
            
            for node_type in node_types:
                result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                count = result.single()['count']
                counts[node_type.lower()] = count
            
            # Count relationships
            rel_types = ['HAS_MESSAGE', 'HAS_CHUNK', 'HAS_CLUSTER', 'TAGGED_WITH', 'SIMILAR_TO_CHAT_HIGH', 'SIMILAR_TO_CLUSTER_HIGH']
            
            for rel_type in rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = result.single()['count']
                counts[f"{rel_type.lower()}_relationships"] = count
            
            return counts
        except Exception as e:
            logger.warning(f"Could not check Neo4j content: {e}")
            return {}
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save loading metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'neo4j_loading',
            'stats': stats,
            'version': '3.0',
            'method': 'hybrid_loader',
            'features': [
                'hash_based_tracking',
                'incremental_loading',
                'enhanced_properties',
                'positioning_data',
                'similarity_relationships',
                'chat_summaries',
                'cluster_summaries',
                'cross_reference_ids',
                'qdrant_compatible'
            ]
        }
        metadata_file = self.loading_dir / "neo4j_metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def load_pipeline(self, force_reload: bool = False) -> Dict:
        """Load all pipeline data into Neo4j with granular hash-based tracking."""
        logger.info("🚀 Starting hybrid Neo4j data loading...")
        
        if not self.driver:
            logger.error("Neo4j driver not available")
            return {'status': 'neo4j_unavailable'}
        
        # Load all data
        data = self._load_all_pipeline_data()
        
        # Check for minimum required data
        if not data['chats']:
            logger.warning("⚠️  No chats found - pipeline may not have been run yet")
            logger.info("💡 Run the pipeline first: python run_pipeline.py --local")
            return {'status': 'no_chats', 'reason': 'pipeline_not_run'}
        
        # Generate current hashes by data type
        current_hashes = {}
        for data_type, items in data.items():
            if isinstance(items, list):
                current_hashes[data_type] = self._generate_data_type_hash(data_type, items)
            elif isinstance(items, dict):
                # For JSON files, create hash from all items
                item_list = [{'id': k, 'data': v} for k, v in items.items()]
                current_hashes[data_type] = self._generate_data_type_hash(data_type, item_list)
        
        # Check if already processed (unless force reload)
        incremental_loading = False
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
                    incremental_loading = True
        
        # Load data into Neo4j
        with self.driver.session() as session:
            # Check what's already loaded
            existing_content = self._check_neo4j_content(session)
            if existing_content:
                logger.info("📊 Current Neo4j content:")
                for content_type, count in existing_content.items():
                    if count > 0:
                        logger.info(f"  {content_type}: {count}")
            
            # Clear database if force reload
            if force_reload:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("🗑️  Cleared existing data (force reload)")
                incremental_loading = False
            
            # Create constraints and indexes
            self._create_constraints(session)
            
            if incremental_loading:
                logger.info("📊 Incremental loading - only creating changed data...")
                # For incremental loading, we need to be more careful about dependencies
                # For now, we'll do a full reload when any upstream data changes
                # This could be optimized further in the future
                logger.info("⚠️  Incremental loading detected changes - doing full reload for data consistency")
                session.run("MATCH (n) DETACH DELETE n")
                incremental_loading = False
            
            # Create nodes in order with progress reporting
            logger.info("📊 Creating nodes and relationships...")
            
            chat_mapping = self._create_chat_nodes(session, data['chats'])
            message_mapping = self._create_message_nodes(session, data['chats'], chat_mapping)
            chunk_mapping = self._create_chunk_nodes(session, data['chunks'], message_mapping)
            cluster_mapping = self._create_cluster_nodes(session, data['cluster_positions'], chunk_mapping)
            tag_mapping = self._create_tag_nodes(session, data['processed_tags'], message_mapping)
            summary_mapping = self._create_summary_nodes(session, data['cluster_summaries'], cluster_mapping)
            chat_summary_mapping = self._create_chat_summary_nodes(session, data['chat_summaries'], chat_mapping)
            
            # Create positioning and similarity data
            self._create_positioning_nodes(session, data['chat_positions'], data['cluster_positions'])
            self._create_similarity_relationships(session, data['chat_similarities'], data['cluster_similarities'])
        
        # Calculate comprehensive statistics
        stats = {
            'status': 'success',
            'chats_loaded': len(data['chats']),
            'chunks_loaded': len(data['chunks']),
            'clusters_loaded': len(data['cluster_positions']),
            'tags_loaded': len(data['processed_tags']),
            'cluster_summaries_loaded': len(data['cluster_summaries']),
            'chat_summaries_loaded': len(data['chat_summaries']),
            'chat_similarities_loaded': len(data['chat_similarities']),
            'cluster_similarities_loaded': len(data['cluster_similarities']),
            'chat_positions_loaded': len(data['chat_positions']),
            'cluster_positions_loaded': len(data['cluster_positions'])
        }
        
        # Save granular hashes for tracking
        self._save_processed_hashes(current_hashes)
        self._save_metadata(stats)
        
        # Enhanced user feedback
        logger.info("✅ Hybrid Neo4j loading completed!")
        logger.info("📈 Loading Statistics:")
        logger.info(f"  💬 Chats: {stats['chats_loaded']}")
        logger.info(f"  📝 Chunks: {stats['chunks_loaded']}")
        logger.info(f"  🎯 Clusters: {stats['clusters_loaded']}")
        logger.info(f"  🏷️  Tags: {stats['tags_loaded']}")
        logger.info(f"  📊 Cluster Summaries: {stats['cluster_summaries_loaded']}")
        logger.info(f"  💭 Chat Summaries: {stats['chat_summaries_loaded']}")
        logger.info(f"  🔗 Chat Similarities: {stats['chat_similarities_loaded']}")
        logger.info(f"  🔗 Cluster Similarities: {stats['cluster_similarities_loaded']}")
        logger.info(f"  📍 Chat Positions: {stats['chat_positions_loaded']}")
        logger.info(f"  📍 Cluster Positions: {stats['cluster_positions_loaded']}")
        
        # Calculate total items (excluding the status string)
        numeric_values = [v for v in stats.values() if isinstance(v, (int, float))]
        total_items = sum(numeric_values)
        logger.info(f"🎉 Total items loaded: {total_items}")
        logger.info("🔗 Cross-reference IDs preserved for Qdrant linking")
        
        return stats
    
    def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()


@click.command()
@click.option('--uri', default=None, help='Neo4j URI (defaults to .env config)')
@click.option('--user', default=None, help='Neo4j username (defaults to .env config)')
@click.option('--password', default=None, help='Neo4j password (defaults to .env config)')
@click.option('--force', is_flag=True, help='Force reload (clear existing data)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t load')
def main(uri: str, user: str, password: str, force: bool, check_only: bool):
    """Load pipeline data into Neo4j graph database with hybrid architecture."""
    
    # Load configuration if not explicitly provided
    if uri is None or user is None or password is None:
        neo4j_config = get_neo4j_config()
        uri = uri or neo4j_config['uri']
        user = user or neo4j_config['user']
        password = password or neo4j_config['password']
    
    if check_only:
        logger.info("🔍 Checking Neo4j setup...")
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                logger.info("✅ Neo4j connection successful")
            driver.close()
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
        return
    
    loader = HybridNeo4jGraphLoader(uri=uri, user=user, password=password)
    
    try:
        result = loader.load_pipeline(force_reload=force)
        
        if result['status'] == 'success':
            logger.info("✅ Neo4j loading completed successfully!")
        else:
            logger.error(f"❌ Neo4j loading failed: {result.get('reason', 'unknown')}")
    finally:
        loader.close()


if __name__ == "__main__":
    main() 