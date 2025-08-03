"""
ChatMind API Services - Dual Layer Graph Support

Business logic layer for handling data operations and statistics
with support for both raw conversation data and semantic chunk data.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
from neo4j.graph import Relationship

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def debug_rel_inspection(rel):
    logger.warning(">>> DEBUG START")
    try:
        logger.warning(f"rel is None: {rel is None}")
        logger.warning(f"bool(rel): {bool(rel)}")
        logger.warning(f"type(rel): {type(rel)}")
        logger.warning(f"repr(rel): {repr(rel)}")
        logger.warning(f"dir(rel): {dir(rel)}")
    except Exception as e:
        logger.warning(f"Logging exploded: {e}")
    logger.warning(">>> DEBUG END")

def convert_neo4j_to_json(obj):
    """Convert Neo4j objects to JSON-serializable format"""
    if hasattr(obj, 'iso_format'):  # Neo4j DateTime objects
        return obj.iso_format()
    elif hasattr(obj, 'to_native'):  # Other Neo4j time objects
        return obj.to_native().isoformat()
    elif isinstance(obj, dict):
        return {k: convert_neo4j_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_neo4j_to_json(item) for item in obj]
    else:
        return obj

class Neo4jService:
    """Service for Neo4j database operations with dual layer support"""
    
    def __init__(self):
        self.driver = None
        self.uri = "bolt://localhost:7687"  # Will be overridden by env vars
        self.user = "neo4j"
        self.password = "password"
        
    def configure(self, uri: str, user: str, password: str):
        """Configure Neo4j connection parameters"""
        self.uri = uri
        self.user = user
        self.password = password
        
    async def connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("Successfully connected to Neo4j")
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def get_graph_data(
        self, 
        limit: int = 100, 
        node_types: Optional[List[str]] = None,
        parent_id: Optional[str] = None,
        use_semantic_positioning: bool = False,
        layer: str = "both"  # "raw", "chunk", or "both"
    ) -> Dict[str, Any]:
        """Get graph data from Neo4j with dual layer support"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                # Simplified query to get nodes and relationships
                query = """
                MATCH (n)
                WHERE (n:Chat OR n:Message OR n:Chunk OR n:Topic OR n:Tag)
                RETURN n
                LIMIT $limit
                """
                
                result = session.run(query, limit=limit)
                
                nodes = []
                edges = []
                
                for record in result:
                    node = record.get("n")
                    if node:
                        # Convert Neo4j properties to JSON-serializable format
                        properties = dict(node)
                        for key, value in properties.items():
                            if hasattr(value, 'iso_format'):  # Neo4j DateTime objects
                                properties[key] = value.iso_format()
                            elif hasattr(value, 'to_native'):  # Other Neo4j time objects
                                properties[key] = value.to_native().isoformat()
                        
                        node_data = {
                            "id": str(node.element_id),
                            "type": list(node.labels)[0] if node.labels else "Unknown",
                            "properties": properties
                        }
                        nodes.append(node_data)
                
                # Get some basic relationships
                rel_query = """
                MATCH (n)-[r]->(m)
                WHERE (n:Chat OR n:Message OR n:Chunk OR n:Topic OR n:Tag)
                AND (m:Chat OR m:Message OR m:Chunk OR m:Topic OR m:Tag)
                RETURN n, r, m
                LIMIT 50
                """
                
                rel_result = session.run(rel_query)
                
                for record in rel_result:
                    source = record.get("n")
                    target = record.get("m")
                    rel = record.get("r")
                    
                    if source and target and rel:
                        # Convert Neo4j relationship properties to JSON-serializable format
                        rel_properties = dict(rel)
                        for key, value in rel_properties.items():
                            if hasattr(value, 'iso_format'):  # Neo4j DateTime objects
                                rel_properties[key] = value.iso_format()
                            elif hasattr(value, 'to_native'):  # Other Neo4j time objects
                                rel_properties[key] = value.to_native().isoformat()
                        
                        edge_data = {
                            "source": str(source.element_id),
                            "target": str(target.element_id),
                            "type": rel.type,
                            "properties": rel_properties
                        }
                        edges.append(edge_data)
                
                logger.info(f"Found {len(nodes)} nodes and {len(edges)} edges")
                
                return {"nodes": nodes, "edges": edges}
                
        except Exception as e:
            logger.error(f"Error fetching graph data: {e}")
            return {"nodes": [], "edges": []}
    
    def get_raw_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get raw conversation data (Chat and Message nodes)"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)
                RETURN c, collect(m) as messages
                ORDER BY c.create_time DESC
                LIMIT $limit
                """
                result = session.run(query, limit=limit)
                
                conversations = []
                for record in result:
                    chat = record['c']
                    messages = record['messages']
                    
                    conversation = {
                        "chat_id": chat.get('chat_id'),
                        "title": chat.get('title'),
                        "create_time": chat.get('create_time'),
                        "message_count": len(messages),
                        "messages": [
                            {
                                "message_id": msg.get('message_id'),
                                "content": msg.get('content'),
                                "role": msg.get('role'),
                                "timestamp": msg.get('timestamp')
                            }
                            for msg in messages
                        ]
                    }
                    conversations.append(conversation)
                
                return conversations
                
        except Exception as e:
            logger.error(f"Error fetching raw conversations: {e}")
            raise RuntimeError(f"Failed to fetch raw conversations: {e}")
    
    def get_chunks_for_message(self, message_id: str) -> List[Dict[str, Any]]:
        """Get chunks associated with a specific message"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Message {message_id: $message_id})-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                RETURN ch, collect(tag) as tags
                """
                result = session.run(query, message_id=message_id)
                
                chunks = []
                for record in result:
                    chunk = record['ch']
                    tags = record['tags']
                    
                    chunk_data = {
                        "chunk_id": chunk.get('chunk_id'),
                        "text": chunk.get('text'),
                        "source_message_id": chunk.get('source_message_id'),
                        "cluster_id": chunk.get('cluster_id'),
                        "tags": [tag.get('name') for tag in tags if tag.get('name')]
                    }
                    chunks.append(chunk_data)
                
                return chunks
                
        except Exception as e:
            logger.error(f"Error fetching chunks for message: {e}")
            raise RuntimeError(f"Failed to fetch chunks: {e}")
    
    def get_semantic_chunks(self, limit: int = 100, cluster_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get semantic chunks with embeddings and tags"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (ch:Chunk)
                """
                
                if cluster_id is not None:
                    query += "WHERE ch.cluster_id = $cluster_id"
                
                query += """
                OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                OPTIONAL MATCH (ch)<-[:SUMMARIZES]-(t:Topic)
                RETURN ch, collect(tag) as tags, t
                ORDER BY ch.chunk_id
                LIMIT $limit
                """
                
                result = session.run(query, limit=limit, cluster_id=cluster_id)
                
                chunks = []
                for record in result:
                    chunk = record['ch']
                    tags = record['tags']
                    topic = record['t']
                    
                    chunk_data = {
                        "chunk_id": chunk.get('chunk_id'),
                        "text": chunk.get('text'),
                        "source_message_id": chunk.get('source_message_id'),
                        "cluster_id": chunk.get('cluster_id'),
                        "tags": [tag.get('name') for tag in tags if tag.get('name')],
                        "topic": {
                            "topic_id": topic.get('topic_id'),
                            "name": topic.get('name')
                        } if topic else None
                    }
                    chunks.append(chunk_data)
                
                return chunks
                
        except Exception as e:
            logger.error(f"Error fetching semantic chunks: {e}")
            raise RuntimeError(f"Failed to fetch semantic chunks: {e}")
    
    def search_by_semantic_similarity(self, query_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search chunks by semantic similarity using embeddings"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            # Import sentence transformers for embedding generation
            try:
                from sentence_transformers import SentenceTransformer
                import numpy as np
            except ImportError:
                logger.error("Sentence Transformers not available for semantic search")
                return []
            
            # Load the same model used in the pipeline
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Generate embedding for the query
            query_embedding = model.encode(query_text)
            
            with self.driver.session() as session:
                # Get all embeddings with their associated chunks
                query = """
                MATCH (c:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
                OPTIONAL MATCH (c)-[:BELONGS_TO]->(m:Message)
                OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
                RETURN c.chunk_id as chunk_id, 
                       c.content as content,
                       m.content as message_content,
                       m.role as role,
                       m.timestamp as timestamp,
                       e.vector as embedding_vector,
                       collect(DISTINCT t.tags) as tags
                """
                
                result = session.run(query)
                
                similarities = []
                for record in result:
                    embedding_vector = record['embedding_vector']
                    if embedding_vector:
                        # Convert to numpy array and calculate cosine similarity
                        chunk_embedding = np.array(embedding_vector)
                        similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                        
                        similarities.append({
                            'chunk_id': record['chunk_id'],
                            'content': record['content'],
                            'message_content': record['message_content'],
                            'role': record['role'],
                            'timestamp': record['timestamp'],
                            'similarity': similarity,
                            'tags': record['tags']
                        })
                
                # Sort by similarity and return top results
                similarities.sort(key=lambda x: x['similarity'], reverse=True)
                return similarities[:limit]
                
        except Exception as e:
            logger.error(f"Error searching by semantic similarity: {e}")
            raise RuntimeError(f"Failed to search by semantic similarity: {e}")
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2) if norm1 * norm2 != 0 else 0.0
    
    def get_topics(self) -> List[Dict[str, Any]]:
        """Get all topics"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (t:Topic)
                RETURN t
                ORDER BY t.size DESC
                """
                result = session.run(query)
                
                topics = []
                for record in result:
                    topic = record['t']
                    topics.append({
                        "id": topic.get('topic_id'),
                        "name": topic.get('name', ''),
                        "size": topic.get('size', 0),
                        "top_words": topic.get('top_words', []),
                        "sample_titles": topic.get('sample_titles', [])
                    })
                
                return topics
                
        except Exception as e:
            logger.error(f"Error fetching topics: {e}")
            raise RuntimeError(f"Failed to fetch topics: {e}")
    
    def get_chats(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all chats"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (c:Chat)
                OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
                WITH c, count(m) as message_count
                RETURN c, message_count
                ORDER BY c.create_time DESC
                LIMIT $limit
                """
                result = session.run(query, limit=limit)
                
                chats = []
                for record in result:
                    chat = record['c']
                    chats.append({
                        "id": chat.get('chat_id'),
                        "title": chat.get('title'),
                        "create_time": chat.get('create_time'),
                        "message_count": record['message_count']
                    })
                
                return chats
                
        except Exception as e:
            logger.error(f"Error fetching chats: {e}")
            raise RuntimeError(f"Failed to fetch chats: {e}")
    
    def get_messages_for_chat(self, chat_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages for a specific chat"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                RETURN m, count(ch) as chunk_count
                ORDER BY m.timestamp
                LIMIT $limit
                """
                result = session.run(query, chat_id=chat_id, limit=limit)
                
                messages = []
                for record in result:
                    message = record['m']
                    messages.append({
                        "id": message.get('message_id'),
                        "content": message.get('content'),
                        "role": message.get('role'),
                        "timestamp": message.get('timestamp'),
                        "chunk_count": record['chunk_count']
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Error fetching messages for chat: {e}")
            raise RuntimeError(f"Failed to fetch messages: {e}")
    
    def search_messages(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search messages by content"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Message)
                WHERE toLower(m.content) CONTAINS toLower($search_term)
                RETURN m
                ORDER BY m.timestamp DESC
                LIMIT $limit
                """
                result = session.run(query, search_term=search_term, limit=limit)
                
                messages = []
                for record in result:
                    message = record['m']
                    messages.append({
                        "id": message.get('message_id'),
                        "content": message.get('content'),
                        "role": message.get('role'),
                        "timestamp": message.get('timestamp')
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise RuntimeError(f"Failed to search messages: {e}")
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """Get all tags"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (tag:Tag)
                RETURN tag
                ORDER BY tag.count DESC
                """
                result = session.run(query)
                
                tags = []
                for record in result:
                    tag = record['tag']
                    tags.append({
                        "name": tag.get('name'),
                        "count": tag.get('count', 0)
                    })
                
                return tags
                
        except Exception as e:
            logger.error(f"Error fetching tags: {e}")
            raise RuntimeError(f"Failed to fetch tags: {e}")
    
    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific message by ID with its chunks"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Message {message_id: $message_id})
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                RETURN m, collect(DISTINCT ch) as chunks, collect(DISTINCT tag) as tags
                """
                result = session.run(query, message_id=message_id)
                record = result.single()
                
                if not record:
                    return None
                
                message = record['m']
                chunks = record['chunks']
                tags = record['tags']
                
                return {
                    "id": message.get('message_id'),
                    "content": message.get('content'),
                    "role": message.get('role'),
                    "timestamp": message.get('timestamp'),
                    "chunks": [
                        {
                            "chunk_id": chunk.get('chunk_id'),
                            "text": chunk.get('text'),
                            "cluster_id": chunk.get('cluster_id')
                        }
                        for chunk in chunks if chunk.get('chunk_id')
                    ],
                    "tags": [tag.get('name') for tag in tags if tag.get('name')]
                }
                
        except Exception as e:
            logger.error(f"Error fetching message by ID: {e}")
            raise RuntimeError(f"Failed to fetch message: {e}")
    
    def get_cluster_details(self, cluster_id: int) -> Optional[Dict[str, Any]]:
        """Get details for a specific cluster/topic"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                query = """
                MATCH (t:Topic {topic_id: $cluster_id})
                OPTIONAL MATCH (t)-[:SUMMARIZES]->(ch:Chunk)
                OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                RETURN t, ch, tag
                """
                result = session.run(query, cluster_id=cluster_id)
                records = list(result)
                
                if not records:
                    return None
                
                # Get the topic from the first record
                topic = records[0]['t']
                
                # Collect chunks and tags from all records
                chunks = []
                tags = []
                seen_chunks = set()
                seen_tags = set()
                
                for record in records:
                    if record['ch'] and record['ch'].get('chunk_id') and record['ch'].get('chunk_id') not in seen_chunks:
                        chunks.append(record['ch'])
                        seen_chunks.add(record['ch'].get('chunk_id'))
                    
                    if record['tag'] and record['tag'].get('name') and record['tag'].get('name') not in seen_tags:
                        tags.append(record['tag'])
                        seen_tags.add(record['tag'].get('name'))
                
                return {
                    "id": topic.get('topic_id'),
                    "name": topic.get('name'),
                    "size": topic.get('size'),
                    "top_words": topic.get('top_words', []),
                    "sample_titles": topic.get('sample_titles', []),
                    "chunks": [
                        {
                            "chunk_id": chunk.get('chunk_id'),
                            "text": chunk.get('text'),
                            "source_message_id": chunk.get('source_message_id')
                        }
                        for chunk in chunks if chunk.get('chunk_id')
                    ],
                    "tags": list(set([tag.get('name') for tag in tags if tag.get('name')]))
                }
                
        except Exception as e:
            logger.error(f"Error fetching cluster details: {e}")
            raise RuntimeError(f"Failed to fetch cluster details: {e}")
    
    def expand_node(self, node_id: str) -> Dict[str, Any]:
        """Expand a node to show its relationships"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                # First, determine the node type
                node_query = """
                MATCH (n)
                WHERE n.chat_id = $node_id OR n.message_id = $node_id OR n.chunk_id = $node_id OR n.topic_id = $node_id OR n.name = $node_id OR n.id = $node_id
                RETURN n
                LIMIT 1
                """
                node_result = session.run(node_query, node_id=node_id)
                node_record = node_result.single()
                
                if not node_record:
                    return {"error": "Node not found"}
                
                node = node_record['n']
                node_labels = list(node.labels)
                node_type = node_labels[0] if node_labels else "Unknown"
                
                # Build expansion query based on node type
                if node_type == "Chat":
                    expansion_query = """
                    MATCH (c:Chat {chat_id: $node_id})
                    OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
                    OPTIONAL MATCH (c)-[:HAS_TOPIC]->(t:Topic)
                    OPTIONAL MATCH (c)-[:SIMILAR_TO]->(similar:Chat)
                    RETURN c, collect(DISTINCT m) as messages, collect(DISTINCT t) as topics, collect(DISTINCT similar) as similar_chats
                    """
                elif node_type == "Message":
                    expansion_query = """
                    MATCH (m:Message {message_id: $node_id})
                    OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                    OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                    OPTIONAL MATCH (ch)<-[:SUMMARIZES]-(t:Topic)
                    RETURN m, collect(DISTINCT ch) as chunks, collect(DISTINCT tag) as tags, collect(DISTINCT t) as topics
                    """
                elif node_type == "Chunk":
                    expansion_query = """
                    MATCH (ch:Chunk {chunk_id: $node_id})
                    OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)
                    OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                    OPTIONAL MATCH (ch)<-[:SUMMARIZES]-(t:Topic)
                    RETURN ch, collect(DISTINCT m) as messages, collect(DISTINCT tag) as tags, collect(DISTINCT t) as topics
                    """
                elif node_type == "Topic":
                    expansion_query = """
                    MATCH (t:Topic {topic_id: $node_id})
                    OPTIONAL MATCH (t)-[:SUMMARIZES]->(ch:Chunk)
                    OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                    OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)
                    RETURN t, collect(DISTINCT ch) as chunks, collect(DISTINCT tag) as tags, collect(DISTINCT m) as messages
                    """
                else:
                    return {"error": f"Unsupported node type: {node_type}"}
                
                expansion_result = session.run(expansion_query, node_id=node_id)
                expansion_record = expansion_result.single()
                
                if not expansion_record:
                    return {"error": "Failed to expand node"}
                
                # Build response based on node type
                response = {
                    "node_type": node_type,
                    "node": convert_neo4j_to_json(dict(node)),
                    "relationships": {}
                }
                
                if node_type == "Chat":
                    response["relationships"] = {
                        "messages": [convert_neo4j_to_json(dict(m)) for m in expansion_record['messages'] if m.get('message_id')],
                        "topics": [convert_neo4j_to_json(dict(t)) for t in expansion_record['topics'] if t.get('topic_id')],
                        "similar_chats": [convert_neo4j_to_json(dict(c)) for c in expansion_record['similar_chats'] if c.get('chat_id')]
                    }
                elif node_type == "Message":
                    response["relationships"] = {
                        "chunks": [convert_neo4j_to_json(dict(ch)) for ch in expansion_record['chunks'] if ch.get('chunk_id')],
                        "tags": [convert_neo4j_to_json(dict(tag)) for tag in expansion_record['tags'] if tag.get('name')],
                        "topics": [convert_neo4j_to_json(dict(t)) for t in expansion_record['topics'] if t.get('topic_id')]
                    }
                elif node_type == "Chunk":
                    response["relationships"] = {
                        "messages": [convert_neo4j_to_json(dict(m)) for m in expansion_record['messages'] if m.get('message_id')],
                        "tags": [convert_neo4j_to_json(dict(tag)) for tag in expansion_record['tags'] if tag.get('name')],
                        "topics": [convert_neo4j_to_json(dict(t)) for t in expansion_record['topics'] if t.get('topic_id')]
                    }
                elif node_type == "Topic":
                    response["relationships"] = {
                        "chunks": [convert_neo4j_to_json(dict(ch)) for ch in expansion_record['chunks'] if ch.get('chunk_id')],
                        "tags": [convert_neo4j_to_json(dict(tag)) for tag in expansion_record['tags'] if tag.get('name')],
                        "messages": [convert_neo4j_to_json(dict(m)) for m in expansion_record['messages'] if m.get('message_id')]
                    }
                
                return response
                
        except Exception as e:
            logger.error(f"Error expanding node: {e}")
            return {"error": f"Failed to expand node: {e}"}
    
    def advanced_search(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Advanced search with filters"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                # Build query based on filters
                base_query = """
                MATCH (n)
                """
                
                where_conditions = []
                params = {"search_query": query}
                
                # Add filters
                if filters.get("node_type"):
                    node_type = filters["node_type"]
                    if node_type == "Message":
                        where_conditions.append("n:Message")
                    elif node_type == "Chunk":
                        where_conditions.append("n:Chunk")
                    elif node_type == "Chat":
                        where_conditions.append("n:Chat")
                    elif node_type == "Topic":
                        where_conditions.append("n:Topic")
                
                if filters.get("role"):
                    where_conditions.append("n.role = $role")
                    params["role"] = filters["role"]
                
                if filters.get("cluster_id"):
                    where_conditions.append("n.cluster_id = $cluster_id")
                    params["cluster_id"] = filters["cluster_id"]
                
                # Add text search
                if query:
                    where_conditions.append("toLower(n.content) CONTAINS toLower($search_query) OR toLower(n.text) CONTAINS toLower($search_query)")
                
                if where_conditions:
                    base_query += f" WHERE {' AND '.join(where_conditions)}"
                
                base_query += """
                RETURN n
                ORDER BY n.timestamp DESC
                LIMIT 50
                """
                
                result = session.run(base_query, **params)
                
                results = []
                for record in result:
                    node = record['n']
                    node_data = {
                        "id": node.id,
                        "type": list(node.labels)[0] if node.labels else "Unknown",
                        "properties": convert_neo4j_to_json(dict(node))
                    }
                    results.append(node_data)
                
                return results
                
        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []
    
    # ============================================================================
    # Discovery Methods
    # ============================================================================
    
    def discover_topics(self, limit: int = 20, min_count: Optional[int] = None, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get most discussed topics with frequency and trends"""
        try:
            with self.driver.session() as session:
                # Use the actual Tag nodes and their properties
                query = """
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                WHERE t.tags IS NOT NULL
                UNWIND t.tags as tag
                WITH tag, count(*) as count
                """
                
                if min_count:
                    query += f" WHERE count >= {min_count}\n"
                
                query += """
                WITH tag, count
                ORDER BY count DESC
                LIMIT $limit
                RETURN tag, count
                """
                
                result = session.run(query, limit=limit)
                topics = []
                
                for record in result:
                    topics.append({
                        "topic": record["tag"],
                        "count": record["count"],
                        "domain": "general",  # TODO: Add domain detection
                        "trend": "stable",    # TODO: Add trend analysis
                        "related_topics": []  # TODO: Add related topics
                    })
                
                return topics
                
        except Exception as e:
            logger.error(f"Error discovering topics: {e}")
            return []
    
    def discover_domains(self) -> List[Dict[str, Any]]:
        """Get domain distribution and insights"""
        try:
            with self.driver.session() as session:
                # For now, return a simple domain breakdown based on tag categories
                query = """
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                WHERE t.tags IS NOT NULL
                UNWIND t.tags as tag_name
                WITH tag_name, count(*) as count
                WITH tag_name, count,
                     CASE 
                         WHEN toLower(tag_name) CONTAINS 'ai' OR toLower(tag_name) CONTAINS 'machine' OR toLower(tag_name) CONTAINS 'learning' THEN 'AI/ML'
                         WHEN toLower(tag_name) CONTAINS 'python' OR toLower(tag_name) CONTAINS 'programming' OR toLower(tag_name) CONTAINS 'code' THEN 'Programming'
                         WHEN toLower(tag_name) CONTAINS 'health' OR toLower(tag_name) CONTAINS 'medical' OR toLower(tag_name) CONTAINS 'wellness' THEN 'Health'
                         WHEN toLower(tag_name) CONTAINS 'business' OR toLower(tag_name) CONTAINS 'finance' OR toLower(tag_name) CONTAINS 'startup' THEN 'Business'
                         ELSE 'General'
                     END as domain
                RETURN domain, sum(count) as count
                ORDER BY count DESC
                """
                
                result = session.run(query)
                domains = []
                
                for record in result:
                    domains.append({
                        "domain": record["domain"],
                        "count": record["count"],
                        "percentage": 0,  # TODO: Calculate percentage
                        "top_topics": [],  # TODO: Add top topics
                        "sentiment_distribution": {
                            "positive": 0,
                            "neutral": 0,
                            "negative": 0
                        }
                    })
                
                return domains
                
        except Exception as e:
            logger.error(f"Error discovering domains: {e}")
            return []
    
    def discover_clusters(self, limit: int = 50, min_size: Optional[int] = None, include_positioning: bool = True) -> List[Dict[str, Any]]:
        """Get semantic clusters with positioning and summaries"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (cl:Cluster)
                """
                
                if min_size:
                    query += f" WHERE cl.size >= {min_size}\n"
                
                query += """
                OPTIONAL MATCH (s:Summary)-[:SUMMARIZES]->(cl)
                RETURN cl.cluster_id, cl.umap_x, cl.umap_y, s.summary, s.key_points, s.common_tags
                ORDER BY cl.cluster_id
                LIMIT $limit
                """
                
                result = session.run(query, limit=limit)
                clusters = []
                
                for record in result:
                    cluster = {
                        "cluster_id": record["cl.cluster_id"],
                        "name": f"Cluster {record['cl.cluster_id']}",
                        "size": 0,  # TODO: Get actual size
                        "summary": record["s.summary"] or "No summary available",
                        "key_points": record["s.key_points"] or [],
                        "common_tags": record["s.common_tags"] or []
                    }
                    
                    if include_positioning and record["cl.umap_x"] is not None:
                        cluster["umap_x"] = record["cl.umap_x"]
                        cluster["umap_y"] = record["cl.umap_y"]
                    
                    clusters.append(cluster)
                
                return clusters
                
        except Exception as e:
            logger.error(f"Error discovering clusters: {e}")
            return []
    
    # ============================================================================
    # Enhanced Search Methods
    # ============================================================================
    
    def search_content(self, search_query: str, limit: int = 50, role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Full-text search across messages"""
        try:
            with self.driver.session() as session:
                cypher_query = """
                MATCH (m:Message)
                WHERE toLower(m.content) CONTAINS toLower($search_query)
                """
                
                if role:
                    cypher_query += f" AND m.role = '{role}'\n"
                
                cypher_query += """
                OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
                RETURN m, collect(DISTINCT t.tags) as tags
                ORDER BY m.timestamp DESC
                LIMIT $limit
                """
                
                result = session.run(cypher_query, search_query=search_query, limit=limit)
                messages = []
                
                for record in result:
                    message = record["m"]
                    tags = record["tags"]
                    
                    messages.append({
                        "id": message["message_id"],
                        "content": message["content"],
                        "role": message["role"],
                        "timestamp": message["timestamp"],
                        "chat_id": message["chat_id"],
                        "tags": [tag for tag_list in tags for tag in tag_list] if tags else []
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    def search_by_tags(self, tags: List[str], limit: int = 50, exact_match: bool = False) -> List[Dict[str, Any]]:
        """Search by specific tags or tag combinations"""
        try:
            with self.driver.session() as session:
                if exact_match:
                    query = """
                    MATCH (t:Tag)-[:TAGS]->(m:Message)
                    WHERE ALL(tag IN $tags WHERE tag IN t.tags)
                    RETURN m, collect(DISTINCT t.tags) as tags
                    ORDER BY m.timestamp DESC
                    LIMIT $limit
                    """
                else:
                    query = """
                    MATCH (t:Tag)-[:TAGS]->(m:Message)
                    WHERE ANY(tag IN $tags WHERE ANY(t IN t.tags WHERE t CONTAINS tag))
                    RETURN m, collect(DISTINCT t.tags) as tags
                    ORDER BY m.timestamp DESC
                    LIMIT $limit
                    """
                
                result = session.run(query, tags=tags, limit=limit)
                messages = []
                
                for record in result:
                    message = record["m"]
                    message_tags = record["tags"]
                    
                    messages.append({
                        "id": message["message_id"],
                        "content": message["content"],
                        "role": message["role"],
                        "tags": [tag for tag_list in message_tags for tag in tag_list] if message_tags else [],
                        "chat_id": message["chat_id"]
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Error searching by tags: {e}")
            return []
    
    # ============================================================================
    # Graph Exploration Methods
    # ============================================================================
    
    def get_visualization_data(self, node_types: Optional[List[str]] = None, limit: int = 100, 
                              include_edges: bool = True, filter_domain: Optional[str] = None) -> Dict[str, Any]:
        """Get data for 2D/3D graph visualization"""
        try:
            with self.driver.session() as session:
                # Build node query
                node_query = """
                MATCH (n)
                WHERE (n:Chat OR n:Message OR n:Chunk OR n:Topic OR n:Tag)
                """
                
                if node_types:
                    node_types_str = "', '".join(node_types)
                    node_query += f" AND labels(n)[0] IN ['{node_types_str}']\n"
                
                if filter_domain:
                    node_query += f" AND n.domain = '{filter_domain}'\n"
                
                node_query += """
                RETURN n
                LIMIT $limit
                """
                
                result = session.run(node_query, limit=limit)
                nodes = []
                
                for record in result:
                    node = record["n"]
                    node_data = {
                        "id": node.get("chat_id") if node.get("chat_id") else str(node.element_id),
                        "type": list(node.labels)[0],
                        "properties": convert_neo4j_to_json(dict(node))
                    }
                    
                    # Add positioning if available
                    if node.get("position_x") and node.get("position_y"):
                        node_data["position"] = {
                            "x": node["position_x"],
                            "y": node["position_y"]
                        }
                    elif node.get("umap_x") and node.get("umap_y"):
                        node_data["position"] = {
                            "x": node["umap_x"],
                            "y": node["umap_y"]
                        }
                    
                    nodes.append(node_data)
                
                edges = []
                if include_edges:
                    # Add edge query here if needed
                    pass
                
                return {
                    "nodes": nodes,
                    "edges": edges
                }
                
        except Exception as e:
            logger.error(f"Error getting visualization data: {e}")
            return {"nodes": [], "edges": []}
    
    def find_connections(self, source_id: str, target_id: Optional[str] = None, max_hops: int = 3, 
                        relationship_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find connections between different conversations or topics"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH path = (source)-[*1..$max_hops]-(target)
                WHERE source.chat_id = $source_id
                """
                
                if target_id:
                    query += " AND target.chat_id = $target_id\n"
                
                if relationship_types:
                    query += f" AND ALL(r IN relationships(path) WHERE type(r) IN {relationship_types})\n"
                
                query += """
                RETURN path, length(path) as path_length
                ORDER BY path_length
                LIMIT 10
                """
                
                result = session.run(query, source_id=source_id, target_id=target_id, max_hops=max_hops)
                paths = []
                
                for record in result:
                    path = record["path"]
                    path_length = record["path_length"]
                    
                    # Extract path information
                    path_nodes = [node["chat_id"] if "chat_id" in node else str(node.identity) for node in path.nodes]
                    path_rels = [type(rel).__name__ for rel in path.relationships]
                    
                    paths.append({
                        "path": path_nodes,
                        "length": path_length,
                        "relationships": path_rels,
                        "total_score": 0.8  # TODO: Calculate actual score
                    })
                
                return {
                    "paths": paths,
                    "summary": {
                        "total_paths": len(paths),
                        "average_score": 0.7 if paths else 0,
                        "strongest_connection": 0.9 if paths else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error finding connections: {e}")
            return {"paths": [], "summary": {"total_paths": 0, "average_score": 0, "strongest_connection": 0}}
    
    def get_neighbors(self, node_id: str, limit: int = 10, min_similarity: float = 0.7, 
                     relationship_type: Optional[str] = None) -> Dict[str, Any]:
        """Get semantic neighbors of a conversation or cluster"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (source)-[r]-(neighbor)
                WHERE source.chat_id = $node_id
                """
                
                if relationship_type:
                    query += f" AND type(r) = '{relationship_type}'\n"
                
                query += """
                RETURN neighbor, type(r) as relationship_type, r.score as similarity_score
                ORDER BY r.score DESC
                LIMIT $limit
                """
                
                result = session.run(query, node_id=node_id, limit=limit)
                neighbors = []
                
                for record in result:
                    neighbor = record["neighbor"]
                    neighbors.append({
                        "id": neighbor["chat_id"] if "chat_id" in neighbor else str(neighbor.identity),
                        "type": list(neighbor.labels)[0],
                        "title": neighbor.get("title", "Unknown"),
                        "similarity_score": record["similarity_score"] or 0.8,
                        "relationship_type": record["relationship_type"]
                    })
                
                return {
                    "node": {
                        "id": node_id,
                        "type": "Chat",
                        "title": "Source Node"
                    },
                    "neighbors": neighbors,
                    "summary": {
                        "total_neighbors": len(neighbors),
                        "average_similarity": sum(n["similarity_score"] for n in neighbors) / len(neighbors) if neighbors else 0,
                        "strongest_connection": max(n["similarity_score"] for n in neighbors) if neighbors else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting neighbors: {e}")
            return {"node": {"id": node_id, "type": "Chat", "title": "Source Node"}, "neighbors": [], "summary": {"total_neighbors": 0, "average_similarity": 0, "strongest_connection": 0}}
    
    # ============================================================================
    # Analytics Methods
    # ============================================================================
    
    def analyze_patterns(self, timeframe: Optional[str] = None, domain: Optional[str] = None, 
                        include_sentiment: bool = True) -> Dict[str, Any]:
        """Analyze conversation patterns and trends"""
        try:
            with self.driver.session() as session:
                # Basic pattern analysis
                query = """
                MATCH (c:Chat)
                RETURN count(c) as total_chats,
                       avg(c.message_count) as avg_messages
                """
                
                result = session.run(query)
                record = result.single()
                
                return {
                    "conversation_frequency": [
                        {
                            "date": "2025-01-15",
                            "count": record["total_chats"],
                            "avg_messages": record["avg_messages"]
                        }
                    ],
                    "topic_evolution": [
                        {
                            "topic": "python",
                            "trend": "increasing",
                            "growth_rate": 0.15
                        }
                    ],
                    "sentiment_trends": {
                        "positive": 65,
                        "neutral": 25,
                        "negative": 10
                    },
                    "complexity_distribution": {
                        "beginner": 20,
                        "intermediate": 45,
                        "advanced": 35
                    }
                }
                
        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")
            return {
                "conversation_frequency": [],
                "topic_evolution": [],
                "sentiment_trends": {"positive": 0, "neutral": 0, "negative": 0},
                "complexity_distribution": {"beginner": 0, "intermediate": 0, "advanced": 0}
            }
    
    def analyze_sentiment(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                         group_by: Optional[str] = None) -> Dict[str, Any]:
        """Sentiment analysis over time"""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (m:Message)-[:TAGS]->(t:Tag)
                WHERE t.sentiment IS NOT NULL
                RETURN t.sentiment as sentiment, count(*) as count
                """
                
                result = session.run(query)
                sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
                
                for record in result:
                    sentiment = record["sentiment"].lower()
                    count = record["count"]
                    if sentiment in sentiment_counts:
                        sentiment_counts[sentiment] = count
                
                return {
                    "overall_sentiment": sentiment_counts,
                    "sentiment_by_domain": [
                        {
                            "domain": "technology",
                            "positive": sentiment_counts["positive"],
                            "neutral": sentiment_counts["neutral"],
                            "negative": sentiment_counts["negative"]
                        }
                    ],
                    "sentiment_timeline": [
                        {
                            "date": "2025-01-15",
                            "positive": sentiment_counts["positive"],
                            "neutral": sentiment_counts["neutral"],
                            "negative": sentiment_counts["negative"]
                        }
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "overall_sentiment": {"positive": 0, "neutral": 0, "negative": 0},
                "sentiment_by_domain": [],
                "sentiment_timeline": []
            }

class StatsService:
    """Service for statistics and analytics"""
    
    def __init__(self, neo4j_service: Neo4jService, data_dir: str = "data"):
        self.neo4j_service = neo4j_service
        self.data_dir = Path(data_dir)
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        try:
            # Get Neo4j statistics
            with self.neo4j_service.driver.session() as session:
                # Node counts
                node_counts = {}
                result = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] as type, count(n) as count
                """)
                for record in result:
                    node_counts[f"{record['type']}_count"] = record['count']
                
                # Relationship counts
                rel_counts = {}
                result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as type, count(r) as count
                """)
                for record in result:
                    rel_counts[f"{record['type']}_count"] = record['count']
                
                # Get cost statistics
                cost_stats = self.get_cost_statistics()
                
                return {
                    "total_chats": node_counts.get("Chat_count", 0),
                    "total_messages": node_counts.get("Message_count", 0),
                    "total_chunks": node_counts.get("Chunk_count", 0),
                    "total_topics": node_counts.get("Topic_count", 0),
                    "active_tags": node_counts.get("Tag_count", 0),
                    "total_relationships": sum(rel_counts.values()),
                    "total_cost": cost_stats.get("total_cost", "$0.00"),
                    "total_calls": cost_stats.get("total_calls", 0)
                }
                
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                "total_chats": 0,
                "total_messages": 0,
                "total_chunks": 0,
                "total_topics": 0,
                "active_tags": 0,
                "total_relationships": 0,
                "total_cost": "$0.00",
                "total_calls": 0
            }
    
    def get_cost_statistics(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        operation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cost tracking statistics"""
        try:
            cost_db_path = self.data_dir / "cost_tracker.db"
            if not cost_db_path.exists():
                return {
                    "total_cost": "$0.00",
                    "total_calls": 0,
                    "operations": {},
                    "daily_costs": []
                }
            
            conn = sqlite3.connect(cost_db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT operation, SUM(cost) as total_cost, COUNT(*) as call_count FROM api_calls"
            params = []
            
            if start_date or end_date or operation:
                conditions = []
                if start_date:
                    conditions.append("date(timestamp) >= ?")
                    params.append(start_date)
                if end_date:
                    conditions.append("date(timestamp) <= ?")
                    params.append(end_date)
                if operation:
                    conditions.append("operation = ?")
                    params.append(operation)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += " GROUP BY operation"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            total_cost = 0.0
            total_calls = 0
            operations = {}
            
            for row in results:
                op, cost, calls = row
                total_cost += cost
                total_calls += calls
                operations[op] = {
                    "cost": f"${cost:.4f}",
                    "calls": calls
                }
            
            # Get daily costs
            daily_query = """
            SELECT date(timestamp) as date, SUM(cost) as daily_cost, COUNT(*) as daily_calls
            FROM api_calls
            GROUP BY date(timestamp)
            ORDER BY date DESC
            LIMIT 30
            """
            cursor.execute(daily_query)
            daily_results = cursor.fetchall()
            
            daily_costs = [
                {
                    "date": row[0],
                    "cost": f"${row[1]:.4f}",
                    "calls": row[2]
                }
                for row in daily_results
            ]
            
            conn.close()
            
            return {
                "total_cost": f"${total_cost:.4f}",
                "total_calls": total_calls,
                "operations": operations,
                "daily_costs": daily_costs
            }
            
        except Exception as e:
            logger.error(f"Error getting cost statistics: {e}")
            return {
                "total_cost": "$0.00",
                "total_calls": 0,
                "operations": {},
                "daily_costs": []
            } 