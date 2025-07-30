#!/usr/bin/env python3
"""
Neo4j Graph Database Loader

Loads processed data from the modular pipeline into Neo4j.
Reads from multiple files and creates relationships based on hashes.
Uses modular directory structure: data/processed/loading/
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging
from tqdm import tqdm
import hashlib
from datetime import datetime

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jGraphLoader:
    """Loads modular pipeline data into Neo4j graph database."""
    
    def __init__(self, 
                 uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "password",
                 processed_dir: str = "data/processed"):
        self.uri = uri
        self.user = user
        self.password = password
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.loading_dir = self.processed_dir / "loading"
        self.loading_dir.mkdir(parents=True, exist_ok=True)
        
        if NEO4J_AVAILABLE:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        else:
            self.driver = None
    
    def _load_chats(self) -> List[Dict]:
        """Load chats from ingestion step."""
        chats_file = self.processed_dir / "ingestion" / "chats.jsonl"
        chats = []
        if chats_file.exists():
            with jsonlines.open(chats_file) as reader:
                for chat in reader:
                    chats.append(chat)
            logger.info(f"Loaded {len(chats)} chats")
        return chats
    
    def _load_chunks(self) -> List[Dict]:
        """Load chunks from chunking step."""
        chunks_file = self.processed_dir / "chunking" / "chunks.jsonl"
        chunks = []
        if chunks_file.exists():
            with jsonlines.open(chunks_file) as reader:
                for chunk in reader:
                    chunks.append(chunk)
            logger.info(f"Loaded {len(chunks)} chunks")
        return chunks
    
    def _load_embeddings(self) -> List[Dict]:
        """Load embeddings from embedding step."""
        embeddings_file = self.processed_dir / "embedding" / "embeddings.jsonl"
        embeddings = []
        if embeddings_file.exists():
            with jsonlines.open(embeddings_file) as reader:
                for embedding in reader:
                    embeddings.append(embedding)
            logger.info(f"Loaded {len(embeddings)} embeddings")
        return embeddings
    
    def _load_clustered_embeddings(self) -> List[Dict]:
        """Load clustered embeddings from clustering step."""
        clustered_file = self.processed_dir / "clustering" / "clustered_embeddings.jsonl"
        clustered = []
        if clustered_file.exists():
            with jsonlines.open(clustered_file) as reader:
                for item in reader:
                    clustered.append(item)
            logger.info(f"Loaded {len(clustered)} clustered embeddings")
        return clustered
    
    def _load_tags(self) -> List[Dict]:
        """Load tags from tagging step."""
        tags_file = self.processed_dir / "tagging" / "tags.jsonl"
        tags = []
        if tags_file.exists():
            with jsonlines.open(tags_file) as reader:
                for tag in reader:
                    tags.append(tag)
            logger.info(f"Loaded {len(tags)} tag entries")
        return tags
    
    def _load_tagged_chunks(self) -> List[Dict]:
        """Load tagged chunks from tag propagation step."""
        tagged_file = self.processed_dir / "tagging" / "tagged_chunks.jsonl"
        tagged = []
        if tagged_file.exists():
            with jsonlines.open(tagged_file) as reader:
                for chunk in reader:
                    tagged.append(chunk)
            logger.info(f"Loaded {len(tagged)} tagged chunks")
        return tagged
    
    def _load_summaries(self) -> Dict:
        """Load cluster summaries from summarization step."""
        summaries_file = self.processed_dir / "summarization" / "cluster_summaries.json"
        summaries = {}
        if summaries_file.exists():
            with open(summaries_file, 'r') as f:
                summaries = json.load(f)
            logger.info(f"Loaded {len(summaries)} cluster summaries")
        return summaries
    
    def _load_similarities(self) -> List[Dict]:
        """Load chat similarities from similarity step."""
        similarities_file = self.processed_dir / "similarity" / "chat_similarities.jsonl"
        similarities = []
        if similarities_file.exists():
            with jsonlines.open(similarities_file) as reader:
                for similarity in reader:
                    similarities.append(similarity)
            logger.info(f"Loaded {len(similarities)} chat similarities")
        return similarities
    
    def _create_chat_nodes(self, session, chats: List[Dict]) -> Dict[str, str]:
        """Create Chat nodes and return chat_id to chat_hash mapping."""
        chat_mapping = {}
        
        for chat in tqdm(chats, desc="Creating Chat nodes"):
            chat_hash = chat.get('content_hash', '')
            chat_id = chat.get('content_hash', '')
            title = chat.get('title', 'Untitled')
            create_time = chat.get('create_time', '')
            source_file = chat.get('source_file', '')
            
            # Create Chat node
            query = """
            MERGE (c:Chat {chat_hash: $chat_hash})
            SET c.title = $title,
                c.create_time = $create_time,
                c.source_file = $source_file,
                c.loaded_at = datetime()
            RETURN c
            """
            
            result = session.run(query, {
                'chat_hash': chat_hash,
                'title': title,
                'create_time': create_time,
                'source_file': source_file
            })
            
            chat_mapping[chat_id] = chat_hash
        
        logger.info(f"Created {len(chat_mapping)} Chat nodes")
        return chat_mapping
    
    def _create_message_nodes(self, session, chats: List[Dict], chat_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Message nodes and return message_id to message_hash mapping."""
        message_mapping = {}
        
        for chat in tqdm(chats, desc="Creating Message nodes"):
            chat_hash = chat_mapping.get(chat.get('content_hash', ''), '')
            messages = chat.get('messages', [])
            
            for message in messages:
                message_id = message.get('id', '')
                content = message.get('content', '')
                role = message.get('role', '')
                timestamp = message.get('timestamp', '')
                parent_id = message.get('parent_id', '')
                
                # Generate message hash
                message_data = {
                    'content': content,
                    'chat_id': chat.get('content_hash', ''),
                    'id': message_id,
                    'role': role
                }
                message_hash = hashlib.sha256(json.dumps(message_data, sort_keys=True).encode()).hexdigest()
                
                # Create Message node
                query = """
                MERGE (m:Message {message_hash: $message_hash})
                SET m.content = $content,
                    m.role = $role,
                    m.timestamp = $timestamp,
                    m.parent_id = $parent_id,
                    m.loaded_at = datetime()
                WITH m
                MATCH (c:Chat {chat_hash: $chat_hash})
                MERGE (m)-[:BELONGS_TO]->(c)
                RETURN m
                """
                
                result = session.run(query, {
                    'message_hash': message_hash,
                    'content': content,
                    'role': role,
                    'timestamp': timestamp,
                    'parent_id': parent_id,
                    'chat_hash': chat_hash
                })
                
                message_mapping[message_id] = message_hash
        
        logger.info(f"Created {len(message_mapping)} Message nodes")
        return message_mapping
    
    def _create_chunk_nodes(self, session, chunks: List[Dict], message_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Chunk nodes and return chunk_id to chunk_hash mapping."""
        chunk_mapping = {}
        
        for chunk in tqdm(chunks, desc="Creating Chunk nodes"):
            chunk_hash = chunk.get('chunk_hash', '')
            chunk_id = chunk.get('chunk_id', '')
            content = chunk.get('content', '')
            role = chunk.get('role', '')
            token_count = chunk.get('token_count', 0)
            message_ids = chunk.get('message_ids', [])
            
            # Create Chunk node
            query = """
            MERGE (ch:Chunk {chunk_hash: $chunk_hash})
            SET ch.content = $content,
                ch.role = $role,
                ch.token_count = $token_count,
                ch.loaded_at = datetime()
            RETURN ch
            """
            
            result = session.run(query, {
                'chunk_hash': chunk_hash,
                'content': content,
                'role': role,
                'token_count': token_count
            })
            
            # Create relationships to messages
            for message_id in message_ids:
                message_hash = message_mapping.get(message_id, '')
                if message_hash:
                    rel_query = """
                    MATCH (ch:Chunk {chunk_hash: $chunk_hash})
                    MATCH (m:Message {message_hash: $message_hash})
                    MERGE (ch)-[:DERIVED_FROM]->(m)
                    """
                    session.run(rel_query, {
                        'chunk_hash': chunk_hash,
                        'message_hash': message_hash
                    })
            
            chunk_mapping[chunk_id] = chunk_hash
        
        logger.info(f"Created {len(chunk_mapping)} Chunk nodes")
        return chunk_mapping
    
    def _create_embedding_nodes(self, session, embeddings: List[Dict], chunk_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Embedding nodes and return embedding_hash mapping."""
        embedding_mapping = {}
        
        for embedding in tqdm(embeddings, desc="Creating Embedding nodes"):
            chunk_hash = embedding.get('chunk_hash', '')
            embedding_vector = embedding.get('embedding', [])
            
            # Generate embedding hash
            embedding_data = {
                'chunk_hash': chunk_hash,
                'embedding': embedding_vector
            }
            embedding_hash = hashlib.sha256(json.dumps(embedding_data, sort_keys=True).encode()).hexdigest()
            
            # Create Embedding node
            query = """
            MERGE (e:Embedding {embedding_hash: $embedding_hash})
            SET e.vector = $vector,
                e.dimension = $dimension,
                e.loaded_at = datetime()
            WITH e
            MATCH (ch:Chunk {chunk_hash: $chunk_hash})
            MERGE (e)-[:EMBEDS]->(ch)
            RETURN e
            """
            
            result = session.run(query, {
                'embedding_hash': embedding_hash,
                'vector': embedding_vector,
                'dimension': len(embedding_vector),
                'chunk_hash': chunk_hash
            })
            
            embedding_mapping[chunk_hash] = embedding_hash
        
        logger.info(f"Created {len(embedding_mapping)} Embedding nodes")
        return embedding_mapping
    
    def _create_cluster_nodes(self, session, clustered: List[Dict], embedding_mapping: Dict[str, str]) -> Dict[int, str]:
        """Create Cluster nodes and return cluster_id to cluster_hash mapping."""
        cluster_mapping = {}
        
        for item in tqdm(clustered, desc="Creating Cluster nodes"):
            chunk_hash = item.get('chunk_hash', '')
            cluster_id = item.get('cluster_id', -1)
            umap_x = item.get('umap_x', 0.0)
            umap_y = item.get('umap_y', 0.0)
            
            # Generate cluster hash
            cluster_data = {
                'cluster_id': cluster_id,
                'chunk_hash': chunk_hash,
                'umap_x': umap_x,
                'umap_y': umap_y
            }
            cluster_hash = hashlib.sha256(json.dumps(cluster_data, sort_keys=True).encode()).hexdigest()
            
            # Create Cluster node
            query = """
            MERGE (cl:Cluster {cluster_id: $cluster_id})
            SET cl.umap_x = $umap_x,
                cl.umap_y = $umap_y,
                cl.loaded_at = datetime()
            WITH cl
            MATCH (ch:Chunk {chunk_hash: $chunk_hash})
            MERGE (ch)-[:BELONGS_TO_CLUSTER]->(cl)
            RETURN cl
            """
            
            result = session.run(query, {
                'cluster_id': cluster_id,
                'umap_x': umap_x,
                'umap_y': umap_y,
                'chunk_hash': chunk_hash
            })
            
            cluster_mapping[cluster_id] = cluster_hash
        
        logger.info(f"Created {len(cluster_mapping)} Cluster nodes")
        return cluster_mapping
    
    def _create_tag_nodes(self, session, tags: List[Dict], message_mapping: Dict[str, str]) -> Dict[str, str]:
        """Create Tag nodes and return tag_hash mapping."""
        tag_mapping = {}
        
        for tag_entry in tqdm(tags, desc="Creating Tag nodes"):
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
            tag_hash = hashlib.sha256(json.dumps(tag_data, sort_keys=True).encode()).hexdigest()
            
            # Create Tag node
            query = """
            MERGE (t:Tag {tag_hash: $tag_hash})
            SET t.tags = $tags,
                t.topics = $topics,
                t.domain = $domain,
                t.complexity = $complexity,
                t.sentiment = $sentiment,
                t.intent = $intent,
                t.loaded_at = datetime()
            WITH t
            MATCH (m:Message {message_hash: $message_hash})
            MERGE (t)-[:TAGS]->(m)
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
                'message_hash': message_hash
            })
            
            tag_mapping[message_hash] = tag_hash
        
        logger.info(f"Created {len(tag_mapping)} Tag nodes")
        return tag_mapping
    
    def _create_summary_nodes(self, session, summaries: Dict, cluster_mapping: Dict[int, str]) -> Dict[int, str]:
        """Create Summary nodes and return summary_hash mapping."""
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
            summary_hash = hashlib.sha256(json.dumps(summary_hash_data, sort_keys=True).encode()).hexdigest()
            
            # Create Summary node
            query = """
            MERGE (s:Summary {summary_hash: $summary_hash})
            SET s.summary = $summary,
                s.domain = $domain,
                s.topics = $topics,
                s.complexity = $complexity,
                s.key_points = $key_points,
                s.common_tags = $common_tags,
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
                'cluster_id': cluster_id
            })
            
            summary_mapping[cluster_id] = summary_hash
        
        logger.info(f"Created {len(summary_mapping)} Summary nodes")
        return summary_mapping
    
    def _create_similarity_relationships(self, session, similarities: List[Dict]) -> None:
        """Create similarity relationships between chats."""
        for similarity in tqdm(similarities, desc="Creating similarity relationships"):
            chat_hash_1 = similarity.get('chat_hash_1', '')
            chat_hash_2 = similarity.get('chat_hash_2', '')
            similarity_score = similarity.get('similarity_score', 0.0)
            
            query = """
            MATCH (c1:Chat {chat_hash: $chat_hash_1})
            MATCH (c2:Chat {chat_hash: $chat_hash_2})
            MERGE (c1)-[r:SIMILAR_TO]->(c2)
            SET r.similarity_score = $similarity_score,
                r.loaded_at = datetime()
            """
            
            session.run(query, {
                'chat_hash_1': chat_hash_1,
                'chat_hash_2': chat_hash_2,
                'similarity_score': similarity_score
            })
        
        logger.info(f"Created {len(similarities)} similarity relationships")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save loading metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'loading',
            'stats': stats,
            'version': '1.0'
        }
        metadata_file = self.loading_dir / "metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def load_pipeline(self, force_reload: bool = False) -> Dict:
        """Load all pipeline data into Neo4j."""
        logger.info("🚀 Starting Neo4j data loading...")
        
        if not self.driver:
            logger.error("Neo4j driver not available")
            return {'status': 'neo4j_unavailable'}
        
        # Load all data
        chats = self._load_chats()
        chunks = self._load_chunks()
        embeddings = self._load_embeddings()
        clustered = self._load_clustered_embeddings()
        tags = self._load_tags()
        tagged_chunks = self._load_tagged_chunks()
        summaries = self._load_summaries()
        similarities = self._load_similarities()
        
        if not chats:
            logger.warning("No chats found")
            return {'status': 'no_chats'}
        
        # Load data into Neo4j
        with self.driver.session() as session:
            # Clear database if force reload
            if force_reload:
                session.run("MATCH (n) DETACH DELETE n")
                logger.info("Cleared existing data")
            
            # Create nodes in order
            chat_mapping = self._create_chat_nodes(session, chats)
            message_mapping = self._create_message_nodes(session, chats, chat_mapping)
            chunk_mapping = self._create_chunk_nodes(session, chunks, message_mapping)
            embedding_mapping = self._create_embedding_nodes(session, embeddings, chunk_mapping)
            cluster_mapping = self._create_cluster_nodes(session, clustered, embedding_mapping)
            tag_mapping = self._create_tag_nodes(session, tags, message_mapping)
            summary_mapping = self._create_summary_nodes(session, summaries, cluster_mapping)
            
            # Create relationships
            self._create_similarity_relationships(session, similarities)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'chats_loaded': len(chats),
            'chunks_loaded': len(chunks),
            'embeddings_loaded': len(embeddings),
            'clusters_loaded': len(clustered),
            'tags_loaded': len(tags),
            'summaries_loaded': len(summaries),
            'similarities_loaded': len(similarities)
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Neo4j loading completed!")
        logger.info(f"  Chats: {stats['chats_loaded']}")
        logger.info(f"  Chunks: {stats['chunks_loaded']}")
        logger.info(f"  Embeddings: {stats['embeddings_loaded']}")
        logger.info(f"  Clusters: {stats['clusters_loaded']}")
        logger.info(f"  Tags: {stats['tags_loaded']}")
        logger.info(f"  Summaries: {stats['summaries_loaded']}")
        logger.info(f"  Similarities: {stats['similarities_loaded']}")
        
        return stats
    
    def close(self):
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()


@click.command()
@click.option('--uri', default='bolt://localhost:7687', help='Neo4j URI')
@click.option('--user', default='neo4j', help='Neo4j username')
@click.option('--password', default='password', help='Neo4j password')
@click.option('--force', is_flag=True, help='Force reload (clear existing data)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t load')
def main(uri: str, user: str, password: str, force: bool, check_only: bool):
    """Load pipeline data into Neo4j graph database."""
    
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
    
    loader = Neo4jGraphLoader(uri=uri, user=user, password=password)
    
    try:
        result = loader.load_pipeline(force_reload=force)
        
        if result['status'] == 'success':
            logger.info("✅ Loading completed successfully!")
        else:
            logger.error(f"❌ Loading failed: {result.get('reason', 'unknown')}")
    finally:
        loader.close()


if __name__ == "__main__":
    main() 