#!/usr/bin/env python3
"""
FastAPI Backend for ChatMind

Provides REST API endpoints for querying the Neo4j knowledge graph
and serving data to the frontend visualization.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import date, datetime

from neo4j import GraphDatabase
from stats import get_dashboard_stats

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatMind API",
    description="API for querying ChatGPT knowledge graph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Lake Service
class DataLakeService:
    def __init__(self, data_lake_dir: str = "data/lake"):
        self.data_lake_dir = Path(data_lake_dir)
        self.chats_dir = self.data_lake_dir / "chats"
        self.messages_dir = self.data_lake_dir / "messages"
        self.urls_dir = self.data_lake_dir / "urls"
    
    def get_chat(self, chat_id: str) -> Optional[Dict]:
        """Get a specific chat from the data lake."""
        chat_file = self.chats_dir / f"{chat_id}.json"
        if not chat_file.exists():
            return None
        
        with open(chat_file, 'r') as f:
            return json.load(f)
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """Get a specific message from the data lake."""
        message_file = self.messages_dir / f"{message_id}.json"
        if not message_file.exists():
            return None
        
        with open(message_file, 'r') as f:
            return json.load(f)
    
    def get_chat_messages(self, chat_id: str) -> List[Dict]:
        """Get all messages for a specific chat."""
        messages = []
        for message_file in self.messages_dir.glob("*.json"):
            with open(message_file, 'r') as f:
                message_data = json.load(f)
            
            if message_data.get('chat_id') == chat_id:
                messages.append(message_data)
        
        # Sort by timestamp if available
        messages.sort(key=lambda x: x.get('timestamp', 0))
        return messages
    
    def get_chat_urls(self, chat_id: str) -> List[Dict]:
        """Get all ChatGPT URLs for a specific chat."""
        urls = []
        for url_file in self.urls_dir.glob("*.json"):
            with open(url_file, 'r') as f:
                url_data = json.load(f)
            
            if url_data.get('chat_id') == chat_id:
                urls.append(url_data)
        
        return urls
    
    def get_url_mapping(self, conversation_id: str) -> Optional[Dict]:
        """Get URL mapping by conversation ID."""
        url_file = self.urls_dir / f"{conversation_id}.json"
        if not url_file.exists():
            return None
        
        with open(url_file, 'r') as f:
            return json.load(f)
    
    def search_urls_by_title(self, query: str) -> List[Dict]:
        """Search URL mappings by chat title."""
        matching_urls = []
        
        for url_file in self.urls_dir.glob("*.json"):
            with open(url_file, 'r') as f:
                url_data = json.load(f)
            
            if query.lower() in url_data.get('title', '').lower():
                matching_urls.append(url_data)
        
        return matching_urls

# Neo4j connection
class Neo4jService:
    def __init__(self):
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
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def get_graph_data(self, limit: int = 100, node_types: List[str] = None, parent_id: str = None, use_semantic_positioning: bool = False) -> Dict[str, Any]:
        """Get graph data for visualization with optional filtering and semantic positioning."""
        with self.driver.session() as session:
            # Default to showing all types if none specified
            if node_types is None:
                node_types = ['Topic', 'Chat', 'Message']
            
            # Calculate limits for each node type based on total limit
            chat_limit = max(1, limit // 4)  # 25% for chats
            message_limit = max(1, limit // 2)  # 50% for messages  
            topic_limit = max(1, limit // 4)  # 25% for topics
            
            # Build the query based on what we want to show
            query_parts = []
            params = {}
            
            if 'Topic' in node_types:
                if parent_id:
                    # If we have a parent, get topics connected to that parent
                    query_parts.append("""
                        MATCH (t:Topic)-[:HAS_TOPIC]-(c:Chat {chat_id: $parent_id})
                        RETURN 'Topic' as type, t as node
                        LIMIT $topic_limit
                    """)
                    params['parent_id'] = parent_id
                else:
                                            # Get all topics with enhanced metrics
                        query_parts.append("""
                            MATCH (t:Topic)
                            OPTIONAL MATCH (t)-[:HAS_TOPIC]-(c:Chat)
                            OPTIONAL MATCH (c)-[:CONTAINS]-(m:Message)
                            WITH t, count(DISTINCT c) as chat_count, count(m) as message_count,
                                 max(c.create_time) as last_active
                            RETURN 'Topic' as type, t as node, chat_count, message_count, last_active,
                                   t.name as name, t.sample_titles as sample_titles, t.top_words as top_words,
                                   t.size as size
                            ORDER BY message_count DESC, last_active DESC
                            LIMIT $topic_limit
                        """)
                        logger.info(f"Topic query will return chat_count, message_count, last_active")
                params['topic_limit'] = topic_limit
            
            if 'Chat' in node_types:
                if parent_id:
                    # If we have a parent topic, get chats in that topic
                    query_parts.append("""
                        MATCH (c:Chat)-[:HAS_TOPIC]-(t:Topic {topic_id: $parent_id})
                        RETURN 'Chat' as type, c as node
                        LIMIT $chat_limit
                    """)
                    params['parent_id'] = int(parent_id)
                else:
                    # Get all chats
                    query_parts.append("""
                        MATCH (c:Chat)
                        RETURN 'Chat' as type, c as node
                        LIMIT $chat_limit
                    """)
                params['chat_limit'] = chat_limit
            
            if 'Message' in node_types:
                if parent_id:
                    # If we have a parent chat, get messages in that chat
                    query_parts.append("""
                        MATCH (m:Message)-[:CONTAINS]-(c:Chat {chat_id: $parent_id})
                        RETURN 'Message' as type, m as node
                        LIMIT $message_limit
                    """)
                    params['parent_id'] = parent_id
                else:
                    # Get all messages
                    query_parts.append("""
                        MATCH (m:Message)
                        RETURN 'Message' as type, m as node
                        LIMIT $message_limit
                    """)
                params['message_limit'] = message_limit
            
            nodes = []
            node_ids = set()  # Track existing node IDs
            
            # Handle Topic nodes separately since they have enhanced properties
            if 'Topic' in node_types:
                topic_query = """
                    MATCH (t:Topic)
                    OPTIONAL MATCH (t)-[:HAS_TOPIC]-(c:Chat)
                    OPTIONAL MATCH (c)-[:CONTAINS]-(m:Message)
                    WITH t, count(DISTINCT c) as chat_count, count(m) as message_count,
                         max(c.create_time) as last_active
                    RETURN 'Topic' as type, t as node, chat_count, message_count, last_active,
                           t.name as name, t.sample_titles as sample_titles, t.top_words as top_words,
                           t.size as size
                    ORDER BY message_count DESC, last_active DESC
                    LIMIT $topic_limit
                """
                logger.info("Executing topic query with enhanced properties")
                topic_result = session.run(topic_query, topic_limit=topic_limit)
                
                for record in topic_result:
                    node_data = dict(record['node'])
                    node_id = node_data.get('topic_id')
                    if node_id:
                        # Debug: print all record keys
                        logger.info(f"Topic record keys: {list(record.keys())}")
                        
                        # Add enhanced metrics to properties
                        if 'chat_count' in record:
                            node_data['chat_count'] = record['chat_count']
                            logger.info(f"Added chat_count: {record['chat_count']}")
                        if 'message_count' in record:
                            node_data['message_count'] = record['message_count']
                            logger.info(f"Added message_count: {record['message_count']}")
                        if 'last_active' in record:
                            node_data['last_active'] = record['last_active']
                            logger.info(f"Added last_active: {record['last_active']}")
                        if 'name' in record:
                            node_data['name'] = record['name']
                        if 'sample_titles' in record:
                            node_data['sample_titles'] = record['sample_titles']
                        if 'top_words' in record:
                            node_data['top_words'] = record['top_words']
                        
                        logger.info(f"Topic Node {node_id}: chat_count={record.get('chat_count', 0)}, message_count={record.get('message_count', 0)}")
                        logger.info(f"node_data after adding properties: {node_data}")
                        
                        final_node = {
                            'id': node_id,
                            'type': record['type'],
                            'properties': node_data
                        }
                        logger.info(f"Final node data: {final_node}")
                        
                        nodes.append(final_node)
                        node_ids.add(node_id)
            
            # Handle other node types with the original query
            if 'Chat' in node_types or 'Message' in node_types:
                other_query_parts = [part for part in query_parts if 'Topic' not in part]
                if other_query_parts:
                    full_query = " UNION ALL ".join(other_query_parts)
                    logger.info(f"Executing other query: {full_query}")
                    other_result = session.run(full_query, **params)
                    
                    for record in other_result:
                        node_data = dict(record['node'])
                        node_id = node_data.get('chat_id') or node_data.get('message_id')
                        if node_id:
                            # Add enhanced properties to node_data
                            if record.get('chat_count') is not None:
                                node_data['chat_count'] = record['chat_count']
                            if record.get('message_count') is not None:
                                node_data['message_count'] = record['message_count']
                            if record.get('last_active') is not None:
                                node_data['last_active'] = record['last_active']
                            
                            logger.info(f"Topic Node {node_id}: chat_count={record.get('chat_count', 0)}, message_count={record.get('message_count', 0)}")
                            
                            final_node = {
                                'id': node_id,
                                'type': record['type'],
                                'properties': node_data
                            }
                            logger.info(f"Final node data: {final_node}")
                            
                            nodes.append(final_node)
                            node_ids.add(node_id)
            
            # Get relationships only between nodes that exist
            logger.info(f"Fetching edges with limit {limit}")
            edges_result = session.run("""
                MATCH (a)-[r]->(b)
                WHERE (a.chat_id IS NOT NULL OR a.message_id IS NOT NULL OR a.topic_id IS NOT NULL)
                AND (b.chat_id IS NOT NULL OR b.message_id IS NOT NULL OR b.topic_id IS NOT NULL)
                RETURN type(r) as type, a.chat_id as from_id, b.chat_id as to_id,
                       a.message_id as from_msg, b.message_id as to_msg,
                       a.topic_id as from_topic, b.topic_id as to_topic
                LIMIT $limit
            """, limit=limit)
            
            # Process real edges first
            edges = []
            edge_count = 0
            for record in edges_result:
                from_id = record['from_id'] or record['from_msg'] or record['from_topic']
                to_id = record['to_id'] or record['to_msg'] or record['to_topic']
                
                # Only add edge if both source and target nodes exist
                if from_id and to_id and from_id in node_ids and to_id in node_ids:
                    edges.append({
                        'source': str(from_id),
                        'target': str(to_id),
                        'type': record['type']
                    })
                    edge_count += 1
            
            logger.info(f"Found {edge_count} edges between {len(nodes)} nodes")
            
            # For testing, add some dummy edges between topics if no real edges exist
            if edge_count == 0:
                logger.info("No edges found, adding dummy edges for testing")
                topic_nodes = [n for n in nodes if n['type'] == 'Topic']
                for i in range(min(5, len(topic_nodes))):
                    for j in range(i + 1, min(i + 3, len(topic_nodes))):
                        edges.append({
                            'source': str(topic_nodes[i]['id']),
                            'target': str(topic_nodes[j]['id']),
                            'type': 'SIMILAR_TO',
                            'similarity': 0.5  # Dummy similarity
                        })
            
            # Calculate semantic positioning if requested
            if use_semantic_positioning and 'Topic' in node_types and not parent_id:
                nodes = self._apply_semantic_positioning(nodes)
            
            return {
                'nodes': nodes,
                'edges': edges
            }
    
    def _apply_semantic_positioning(self, nodes: List[Dict]) -> List[Dict]:
        """Apply semantic positioning to topic nodes using UMAP (fallback to t-SNE/random)."""
        # Extract topic nodes
        topic_nodes = [n for n in nodes if n['type'] == 'Topic']
        if len(topic_nodes) < 2:
            return nodes

        # Build text representations
        topic_texts: List[str] = []
        for node in topic_nodes:
            text_parts: List[str] = []
            if node['properties'].get('name'):
                text_parts.append(node['properties']['name'])
            if node['properties'].get('sample_titles'):
                text_parts.extend(node['properties']['sample_titles'])
            if node['properties'].get('top_words'):
                text_parts.extend(node['properties']['top_words'])
            topic_texts.append(' '.join(text_parts))

        # Create TF-IDF vectors
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
        except ImportError:
            logger.warning("scikit-learn not available for vectorization, using random positioning")
            import random
            for node in topic_nodes:
                node['x'] = random.uniform(-200, 200)
                node['y'] = random.uniform(-200, 200)
            return nodes

        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(topic_texts)

        # Try UMAP for 2D positioning
        positions = None
        try:
            import umap
            reducer = umap.UMAP(n_components=2, random_state=42)
            positions = reducer.fit_transform(tfidf_matrix.toarray())
            logger.info("Applied UMAP for semantic positioning")
        except ImportError:
            # Fallback to t-SNE
            try:
                from sklearn.manifold import TSNE
                positions = TSNE(n_components=2,
                                 random_state=42,
                                 perplexity=min(30, len(topic_nodes)-1)
                                 ).fit_transform(tfidf_matrix.toarray())
                logger.info("UMAP not available, applied t-SNE for semantic positioning")
            except ImportError:
                logger.warning("Neither UMAP nor t-SNE available, using random positioning")
                import random
                for node in topic_nodes:
                    node['x'] = random.uniform(-200, 200)
                    node['y'] = random.uniform(-200, 200)
                return nodes

        # Scale positions
        positions = positions * 50

        # Update node positions
        for i, node in enumerate(topic_nodes):
            node['x'] = float(positions[i][0])
            node['y'] = float(positions[i][1])

        return nodes
    
    def get_topics(self) -> List[Dict]:
        """Get all topic nodes with their summaries."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Topic)
                RETURN t.topic_id as id, t.name as name, t.size as size,
                       t.top_words as top_words, t.sample_titles as sample_titles
                ORDER BY t.size DESC
            """)
            
            topics = []
            for record in result:
                topics.append({
                    'id': record['id'],
                    'name': record['name'],
                    'size': record['size'],
                    'top_words': record['top_words'],
                    'sample_titles': record['sample_titles']
                })
            
            return topics
    
    def get_chats(self, limit: int = 50) -> List[Dict]:
        """Get chat nodes with their metadata."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                RETURN c.chat_id as id, c.title as title, c.create_time as create_time
                ORDER BY c.create_time DESC
                LIMIT $limit
            """, limit=limit)
            
            chats = []
            for record in result:
                chats.append({
                    'id': record['id'],
                    'title': record['title'],
                    'create_time': record['create_time']
                })
            
            return chats
    
    def get_messages_for_chat(self, chat_id: str, limit: int = 100) -> List[Dict]:
        """Get messages for a specific chat."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
                RETURN m.message_id as id, m.content as content, m.role as role,
                       m.timestamp as timestamp, m.cluster_id as cluster_id
                ORDER BY m.timestamp
                LIMIT $limit
            """, chat_id=chat_id, limit=limit)
            
            messages = []
            for record in result:
                messages.append({
                    'id': record['id'],
                    'content': record['content'],
                    'role': record['role'],
                    'timestamp': record['timestamp'],
                    'cluster_id': record['cluster_id']
                })
            
            return messages
    
    def get_messages_for_topic(self, topic_id: int, limit: int = 100) -> List[Dict]:
        """Get messages for a specific topic."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Topic {topic_id: $topic_id})-[:SUMMARIZES]->(m:Message)
                RETURN m.message_id as id, m.content as content, m.role as role,
                       m.timestamp as timestamp, m.cluster_id as cluster_id
                ORDER BY m.timestamp
                LIMIT $limit
            """, topic_id=topic_id, limit=limit)
            
            messages = []
            for record in result:
                messages.append({
                    'id': record['id'],
                    'content': record['content'],
                    'role': record['role'],
                    'timestamp': record['timestamp'],
                    'cluster_id': record['cluster_id']
                })
            
            return messages
    
    def search_messages(self, query: str, limit: int = 50) -> List[Dict]:
        """Search messages by content."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                WHERE toLower(m.content) CONTAINS toLower($query)
                RETURN m.message_id as id, m.content as content, m.role as role,
                       m.timestamp as timestamp, m.cluster_id as cluster_id
                ORDER BY m.timestamp DESC
                LIMIT $limit
            """, {"query": query, "limit": limit})
            
            messages = []
            for record in result:
                messages.append({
                    'id': record['id'],
                    'content': record['content'],
                    'role': record['role'],
                    'timestamp': record['timestamp'],
                    'cluster_id': record['cluster_id']
                })
            
            return messages

# Initialize services
neo4j_service = Neo4jService()
data_lake_service = DataLakeService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    neo4j_service.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    neo4j_service.close()

# Pydantic models for API responses
class GraphData(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class Topic(BaseModel):
    id: int
    name: str
    size: int
    top_words: List[str]
    sample_titles: List[str]

class Chat(BaseModel):
    id: str
    title: str
    create_time: Optional[float]

class Message(BaseModel):
    id: str
    content: str
    role: str
    timestamp: Optional[float]
    cluster_id: Optional[int]

# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ChatMind API is running"}

@app.get("/api/stats/dashboard")
async def get_stats():
    """Get dashboard statistics from real data"""
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/debug/nodes")
async def debug_nodes():
    """Debug endpoint to see what nodes are in the database."""
    try:
        with neo4j_service.driver.session() as session:
            # Get count of each node type
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            
            node_counts = []
            for record in result:
                node_counts.append({
                    "labels": record["labels"],
                    "count": record["count"]
                })
            
            return {"node_counts": node_counts}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/chat-properties")
async def debug_chat_properties():
    """Debug endpoint to see Chat node properties."""
    try:
        with neo4j_service.driver.session() as session:
            # Get sample Chat node properties
            result = session.run("""
                MATCH (c:Chat)
                RETURN c LIMIT 3
            """)
            
            sample_chats = []
            for record in result:
                chat_node = record["c"]
                sample_chats.append({
                    "properties": dict(chat_node),
                    "labels": list(chat_node.labels)
                })
            
            return {"sample_chats": sample_chats}
    except Exception as e:
        return {"error": str(e)}

@app.get("/graph", response_model=GraphData)
async def get_graph_data(
    limit: int = 100,
    node_types: str = None,  # Comma-separated list like "Topic,Chat"
    parent_id: str = None,
    use_semantic_positioning: bool = False
):
    """Get graph data for visualization with optional filtering and semantic positioning."""
    try:
        # Parse node_types parameter
        node_types_list = None
        if node_types:
            node_types_list = [t.strip() for t in node_types.split(',')]
        
        data = neo4j_service.get_graph_data(limit, node_types_list, parent_id, use_semantic_positioning)
        return GraphData(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {e}")

@app.get("/topics", response_model=List[Topic])
async def get_topics():
    """Get all topics."""
    try:
        topics = neo4j_service.get_topics()
        return [Topic(**topic) for topic in topics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topics: {e}")

@app.get("/chats", response_model=List[Chat])
async def get_chats(limit: int = 50):
    """Get all chats."""
    try:
        chats = neo4j_service.get_chats(limit)
        return [Chat(**chat) for chat in chats]
    except Exception as e:
        logger.error(f"Error in get_chats: {e}")
        # Return empty list instead of 500 error if no chats found
        return []

@app.get("/chats/{chat_id}/messages", response_model=List[Message])
async def get_chat_messages(chat_id: str, limit: int = 100):
    """Get messages for a specific chat."""
    try:
        # Limit to maximum 500 messages to prevent resource exhaustion
        actual_limit = min(limit, 500)
        messages = neo4j_service.get_messages_for_chat(chat_id, actual_limit)
        return [Message(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat messages: {e}")

@app.get("/topics/{topic_id}/messages", response_model=List[Message])
async def get_topic_messages(topic_id: int, limit: int = 100):
    """Get messages for a specific topic."""
    try:
        # Limit to maximum 500 messages to prevent resource exhaustion
        actual_limit = min(limit, 500)
        messages = neo4j_service.get_messages_for_topic(topic_id, actual_limit)
        return [Message(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topic messages: {e}")

@app.get("/search", response_model=List[Message])
async def search_messages(query: str, limit: int = 50):
    """Search messages by content."""
    try:
        messages = neo4j_service.search_messages(query, limit)
        return [Message(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search messages: {e}")


@app.get("/tags")
async def get_all_tags():
    """Get all available tags from the knowledge graph."""
    try:
        with neo4j_service.driver.session() as session:
            # Get all unique tags from chunks
            result = session.run("""
                MATCH (c:Message)
                WHERE c.tags IS NOT NULL
                UNWIND c.tags as tag
                RETURN DISTINCT tag
                ORDER BY tag
            """)
            
            tags = [record['tag'] for record in result]
            
            # Get all unique categories
            result = session.run("""
                MATCH (c:Message)
                WHERE c.category IS NOT NULL
                RETURN DISTINCT c.category as category
                ORDER BY category
            """)
            
            categories = [record['category'] for record in result]
            
            return {
                'tags': tags,
                'categories': categories
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {e}")


@app.get("/search/by-tags")
async def search_by_tags(
    tags: str = None,
    category: str = None,
    limit: int = 50
):
    """Search messages by tags and/or category."""
    try:
        with neo4j_service.driver.session() as session:
            query = "MATCH (c:Message) WHERE 1=1"
            params = {}
            
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                query += " AND ANY(tag IN c.tags WHERE tag IN $tags)"
                params['tags'] = tag_list
            
            if category:
                query += " AND c.category = $category"
                params['category'] = category
            
            query += """
                RETURN c.id as id, c.content as content, c.role as role,
                       c.timestamp as timestamp, c.cluster_id as cluster_id,
                       c.tags as tags, c.category as category
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """
            params['limit'] = limit
            
            result = session.run(query, params)
            messages = [dict(record) for record in result]
            
            return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search by tags: {e}")


@app.get("/graph/filtered")
async def get_filtered_graph(
    tags: str = None,
    category: str = None,
    limit: int = 100
):
    """Get filtered graph data based on tags and/or category."""
    try:
        with neo4j_service.driver.session() as session:
            # Build the query based on filters
            query = """
                MATCH (c:Message)
                WHERE 1=1
            """
            params = {}
            
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                query += " AND ANY(tag IN c.tags WHERE tag IN $tags)"
                params['tags'] = tag_list
            
            if category:
                query += " AND c.category = $category"
                params['category'] = category
            
            query += """
                WITH c
                MATCH (c)-[:CONTAINS]-(chat:Chat)
                MATCH (chat)-[:SUMMARIZES]-(topic:Topic)
                
                RETURN DISTINCT
                    c.id as message_id,
                    c.content as message_content,
                    c.role as message_role,
                    c.tags as message_tags,
                    c.category as message_category,
                    chat.id as chat_id,
                    chat.title as chat_title,
                    topic.id as topic_id,
                    topic.name as topic_name
                
                LIMIT $limit
            """
            params['limit'] = limit
            
            result = session.run(query, params)
            
            # Convert to graph format
            nodes = []
            edges = []
            node_ids = set()
            
            for record in result:
                # Add message node
                message_id = f"message_{record['message_id']}"
                if message_id not in node_ids:
                    nodes.append({
                        'id': message_id,
                        'type': 'Message',
                        'properties': {
                            'id': record['message_id'],
                            'content': record['message_content'],
                            'role': record['message_role'],
                            'tags': record['message_tags'],
                            'category': record['message_category']
                        }
                    })
                    node_ids.add(message_id)
                
                # Add chat node
                chat_id = f"chat_{record['chat_id']}"
                if chat_id not in node_ids:
                    nodes.append({
                        'id': chat_id,
                        'type': 'Chat',
                        'properties': {
                            'id': record['chat_id'],
                            'title': record['chat_title']
                        }
                    })
                    node_ids.add(chat_id)
                
                # Add topic node
                topic_id = f"topic_{record['topic_id']}"
                if topic_id not in node_ids:
                    nodes.append({
                        'id': topic_id,
                        'type': 'Topic',
                        'properties': {
                            'id': record['topic_id'],
                            'name': record['topic_name']
                        }
                    })
                    node_ids.add(topic_id)
                
                # Add edges
                edges.append({
                    'source': topic_id,
                    'target': chat_id,
                    'type': 'SUMMARIZES'
                })
                edges.append({
                    'source': chat_id,
                    'target': message_id,
                    'type': 'CONTAINS'
                })
            
            return {
                'nodes': nodes,
                'edges': edges
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filtered graph: {e}")

# Data Lake endpoints
@app.get("/lake/chat/{chat_id}")
async def get_data_lake_chat(chat_id: str):
    """Get a specific chat from the data lake."""
    try:
        chat = data_lake_service.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat: {e}")

@app.get("/lake/message/{message_id}")
async def get_data_lake_message(message_id: str):
    """Get a specific message from the data lake."""
    try:
        message = data_lake_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message: {e}")

@app.get("/lake/chat/{chat_id}/messages")
async def get_data_lake_chat_messages(chat_id: str):
    """Get all messages for a specific chat from the data lake."""
    try:
        messages = data_lake_service.get_chat_messages(chat_id)
        return {"chat_id": chat_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat messages: {e}")

# ChatGPT URL endpoints
@app.get("/lake/chat/{chat_id}/urls")
async def get_chat_urls(chat_id: str):
    """Get all ChatGPT URLs for a specific chat."""
    try:
        urls = data_lake_service.get_chat_urls(chat_id)
        return {"chat_id": chat_id, "urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat URLs: {e}")

@app.get("/lake/url/{conversation_id}")
async def get_url_mapping(conversation_id: str):
    """Get URL mapping by conversation ID."""
    try:
        url_mapping = data_lake_service.get_url_mapping(conversation_id)
        if not url_mapping:
            raise HTTPException(status_code=404, detail="URL mapping not found")
        return url_mapping
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get URL mapping: {e}")

@app.get("/lake/urls/search")
async def search_urls(query: str):
    """Search URL mappings by chat title."""
    try:
        urls = data_lake_service.search_urls_by_title(query)
        return {"query": query, "urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search URLs: {e}")

@app.get("/stats")
async def get_stats():
    """Get graph statistics."""
    try:
        with neo4j_service.driver.session() as session:
            # Count nodes by type
            node_stats = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
            """)
            
            # Count relationships by type
            edge_stats = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
            """)
            
            stats = {
                'nodes': {record['type']: record['count'] for record in node_stats},
                'edges': {record['type']: record['count'] for record in edge_stats}
            }
            
            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}")


# Cost Tracking Endpoints
@app.get("/costs/statistics")
async def get_cost_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    operation: Optional[str] = None
):
    """Get cost and usage statistics."""
    try:
        from chatmind.cost_tracker.tracker import get_cost_tracker
        
        tracker = get_cost_tracker()
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
#!/usr/bin/env python3
"""
FastAPI Backend for ChatMind

Provides REST API endpoints for querying the Neo4j knowledge graph
and serving data to the frontend visualization.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging
import json
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import date, datetime

from neo4j import GraphDatabase
from stats import get_dashboard_stats

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ChatMind API",
    description="API for querying ChatGPT knowledge graph",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Lake Service
class DataLakeService:
    def __init__(self, data_lake_dir: str = "data/lake"):
        self.data_lake_dir = Path(data_lake_dir)
        self.chats_dir = self.data_lake_dir / "chats"
        self.messages_dir = self.data_lake_dir / "messages"
        self.urls_dir = self.data_lake_dir / "urls"
    
    def get_chat(self, chat_id: str) -> Optional[Dict]:
        """Get a specific chat from the data lake."""
        chat_file = self.chats_dir / f"{chat_id}.json"
        if not chat_file.exists():
            return None
        
        with open(chat_file, 'r') as f:
            return json.load(f)
    
    def get_message(self, message_id: str) -> Optional[Dict]:
        """Get a specific message from the data lake."""
        message_file = self.messages_dir / f"{message_id}.json"
        if not message_file.exists():
            return None
        
        with open(message_file, 'r') as f:
            return json.load(f)
    
    def get_chat_messages(self, chat_id: str) -> List[Dict]:
        """Get all messages for a specific chat."""
        messages = []
        for message_file in self.messages_dir.glob("*.json"):
            with open(message_file, 'r') as f:
                message_data = json.load(f)
            
            if message_data.get('chat_id') == chat_id:
                messages.append(message_data)
        
        # Sort by timestamp if available
        messages.sort(key=lambda x: x.get('timestamp', 0))
        return messages
    
    def get_chat_urls(self, chat_id: str) -> List[Dict]:
        """Get all ChatGPT URLs for a specific chat."""
        urls = []
        for url_file in self.urls_dir.glob("*.json"):
            with open(url_file, 'r') as f:
                url_data = json.load(f)
            
            if url_data.get('chat_id') == chat_id:
                urls.append(url_data)
        
        return urls
    
    def get_url_mapping(self, conversation_id: str) -> Optional[Dict]:
        """Get URL mapping by conversation ID."""
        url_file = self.urls_dir / f"{conversation_id}.json"
        if not url_file.exists():
            return None
        
        with open(url_file, 'r') as f:
            return json.load(f)
    
    def search_urls_by_title(self, query: str) -> List[Dict]:
        """Search URL mappings by chat title."""
        matching_urls = []
        
        for url_file in self.urls_dir.glob("*.json"):
            with open(url_file, 'r') as f:
                url_data = json.load(f)
            
            if query.lower() in url_data.get('title', '').lower():
                matching_urls.append(url_data)
        
        return matching_urls

# Neo4j connection
class Neo4jService:
    def __init__(self):
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
            logger.info("Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def get_graph_data(self, limit: int = 100, node_types: List[str] = None, parent_id: str = None, use_semantic_positioning: bool = False) -> Dict[str, Any]:
        """Get graph data for visualization with optional filtering and semantic positioning."""
        with self.driver.session() as session:
            # Default to showing all types if none specified
            if node_types is None:
                node_types = ['Topic', 'Chat', 'Message']
            
            # Calculate limits for each node type based on total limit
            chat_limit = max(1, limit // 4)  # 25% for chats
            message_limit = max(1, limit // 2)  # 50% for messages  
            topic_limit = max(1, limit // 4)  # 25% for topics
            
            # Build the query based on what we want to show
            query_parts = []
            params = {}
            
            if 'Topic' in node_types:
                if parent_id:
                    # If we have a parent, get topics connected to that parent
                    query_parts.append("""
                        MATCH (t:Topic)-[:HAS_TOPIC]-(c:Chat {chat_id: $parent_id})
                        RETURN 'Topic' as type, t as node
                        LIMIT $topic_limit
                    """)
                    params['parent_id'] = parent_id
                else:
                                            # Get all topics with enhanced metrics
                        query_parts.append("""
                            MATCH (t:Topic)
                            OPTIONAL MATCH (t)-[:HAS_TOPIC]-(c:Chat)
                            OPTIONAL MATCH (c)-[:CONTAINS]-(m:Message)
                            WITH t, count(DISTINCT c) as chat_count, count(m) as message_count,
                                 max(c.create_time) as last_active
                            RETURN 'Topic' as type, t as node, chat_count, message_count, last_active,
                                   t.name as name, t.sample_titles as sample_titles, t.top_words as top_words,
                                   t.size as size
                            ORDER BY message_count DESC, last_active DESC
                            LIMIT $topic_limit
                        """)
                        logger.info(f"Topic query will return chat_count, message_count, last_active")
                params['topic_limit'] = topic_limit
            
            if 'Chat' in node_types:
                if parent_id:
                    # If we have a parent topic, get chats in that topic
                    query_parts.append("""
                        MATCH (c:Chat)-[:HAS_TOPIC]-(t:Topic {topic_id: $parent_id})
                        RETURN 'Chat' as type, c as node
                        LIMIT $chat_limit
                    """)
                    params['parent_id'] = int(parent_id)
                else:
                    # Get all chats
                    query_parts.append("""
                        MATCH (c:Chat)
                        RETURN 'Chat' as type, c as node
                        LIMIT $chat_limit
                    """)
                params['chat_limit'] = chat_limit
            
            if 'Message' in node_types:
                if parent_id:
                    # If we have a parent chat, get messages in that chat
                    query_parts.append("""
                        MATCH (m:Message)-[:CONTAINS]-(c:Chat {chat_id: $parent_id})
                        RETURN 'Message' as type, m as node
                        LIMIT $message_limit
                    """)
                    params['parent_id'] = parent_id
                else:
                    # Get all messages
                    query_parts.append("""
                        MATCH (m:Message)
                        RETURN 'Message' as type, m as node
                        LIMIT $message_limit
                    """)
                params['message_limit'] = message_limit
            
            nodes = []
            node_ids = set()  # Track existing node IDs
            
            # Handle Topic nodes separately since they have enhanced properties
            if 'Topic' in node_types:
                topic_query = """
                    MATCH (t:Topic)
                    OPTIONAL MATCH (t)-[:HAS_TOPIC]-(c:Chat)
                    OPTIONAL MATCH (c)-[:CONTAINS]-(m:Message)
                    WITH t, count(DISTINCT c) as chat_count, count(m) as message_count,
                         max(c.create_time) as last_active
                    RETURN 'Topic' as type, t as node, chat_count, message_count, last_active,
                           t.name as name, t.sample_titles as sample_titles, t.top_words as top_words,
                           t.size as size
                    ORDER BY message_count DESC, last_active DESC
                    LIMIT $topic_limit
                """
                logger.info("Executing topic query with enhanced properties")
                topic_result = session.run(topic_query, topic_limit=topic_limit)
                
                for record in topic_result:
                    node_data = dict(record['node'])
                    node_id = node_data.get('topic_id')
                    if node_id:
                        # Debug: print all record keys
                        logger.info(f"Topic record keys: {list(record.keys())}")
                        
                        # Add enhanced metrics to properties
                        if 'chat_count' in record:
                            node_data['chat_count'] = record['chat_count']
                            logger.info(f"Added chat_count: {record['chat_count']}")
                        if 'message_count' in record:
                            node_data['message_count'] = record['message_count']
                            logger.info(f"Added message_count: {record['message_count']}")
                        if 'last_active' in record:
                            node_data['last_active'] = record['last_active']
                            logger.info(f"Added last_active: {record['last_active']}")
                        if 'name' in record:
                            node_data['name'] = record['name']
                        if 'sample_titles' in record:
                            node_data['sample_titles'] = record['sample_titles']
                        if 'top_words' in record:
                            node_data['top_words'] = record['top_words']
                        
                        logger.info(f"Topic Node {node_id}: chat_count={record.get('chat_count', 0)}, message_count={record.get('message_count', 0)}")
                        
                        final_node = {
                            'id': node_id,
                            'type': record['type'],
                            'properties': node_data
                        }
                        logger.info(f"Final node data: {final_node}")
                        
                        nodes.append(final_node)
                        node_ids.add(node_id)
            
            # Handle other node types with the original query
            if 'Chat' in node_types or 'Message' in node_types:
                other_query_parts = [part for part in query_parts if 'Topic' not in part]
                if other_query_parts:
                    full_query = " UNION ALL ".join(other_query_parts)
                    logger.info(f"Executing other query: {full_query}")
                    other_result = session.run(full_query, **params)
                    
                    for record in other_result:
                        node_data = dict(record['node'])
                        node_id = node_data.get('chat_id') or node_data.get('message_id')
                        if node_id:
                            # Add enhanced properties to node_data
                            if record.get('chat_count') is not None:
                                node_data['chat_count'] = record['chat_count']
                            if record.get('message_count') is not None:
                                node_data['message_count'] = record['message_count']
                            if record.get('last_active') is not None:
                                node_data['last_active'] = record['last_active']
                            
                            logger.info(f"Topic Node {node_id}: chat_count={record.get('chat_count', 0)}, message_count={record.get('message_count', 0)}")
                            
                            final_node = {
                                'id': node_id,
                                'type': record['type'],
                                'properties': node_data
                            }
                            logger.info(f"Final node data: {final_node}")
                            
                            nodes.append(final_node)
                            node_ids.add(node_id)
            
            # Get relationships only between nodes that exist
            logger.info(f"Fetching edges with limit {limit}")
            edges_result = session.run("""
                MATCH (a)-[r]->(b)
                WHERE (a.chat_id IS NOT NULL OR a.message_id IS NOT NULL OR a.topic_id IS NOT NULL)
                AND (b.chat_id IS NOT NULL OR b.message_id IS NOT NULL OR b.topic_id IS NOT NULL)
                RETURN type(r) as type, a.chat_id as from_id, b.chat_id as to_id,
                       a.message_id as from_msg, b.message_id as to_msg,
                       a.topic_id as from_topic, b.topic_id as to_topic
                LIMIT $limit
            """, limit=limit)
            
            # Process real edges first
            edges = []
            edge_count = 0
            for record in edges_result:
                from_id = record['from_id'] or record['from_msg'] or record['from_topic']
                to_id = record['to_id'] or record['to_msg'] or record['to_topic']
                
                # Only add edge if both source and target nodes exist
                if from_id and to_id and from_id in node_ids and to_id in node_ids:
                    edges.append({
                        'source': str(from_id),
                        'target': str(to_id),
                        'type': record['type']
                    })
                    edge_count += 1
            
            logger.info(f"Found {edge_count} edges between {len(nodes)} nodes")
            
            # For testing, add some dummy edges between topics if no real edges exist
            if edge_count == 0:
                logger.info("No edges found, adding dummy edges for testing")
                topic_nodes = [n for n in nodes if n['type'] == 'Topic']
                for i in range(min(5, len(topic_nodes))):
                    for j in range(i + 1, min(i + 3, len(topic_nodes))):
                        edges.append({
                            'source': str(topic_nodes[i]['id']),
                            'target': str(topic_nodes[j]['id']),
                            'type': 'SIMILAR_TO',
                            'similarity': 0.5  # Dummy similarity
                        })
            
            # Calculate semantic positioning if requested
            if use_semantic_positioning and 'Topic' in node_types and not parent_id:
                nodes = self._apply_semantic_positioning(nodes)
            
            return {
                'nodes': nodes,
                'edges': edges
            }
    
    def _apply_semantic_positioning(self, nodes: List[Dict]) -> List[Dict]:
        """Apply semantic positioning to topic nodes using UMAP (fallback to t-SNE/random)."""
        # Extract topic nodes
        topic_nodes = [n for n in nodes if n['type'] == 'Topic']
        if len(topic_nodes) < 2:
            return nodes

        # Build text representations
        topic_texts: List[str] = []
        for node in topic_nodes:
            text_parts: List[str] = []
            if node['properties'].get('name'):
                text_parts.append(node['properties']['name'])
            if node['properties'].get('sample_titles'):
                text_parts.extend(node['properties']['sample_titles'])
            if node['properties'].get('top_words'):
                text_parts.extend(node['properties']['top_words'])
            topic_texts.append(' '.join(text_parts))

        # Create TF-IDF vectors
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import numpy as np
        except ImportError:
            logger.warning("scikit-learn not available for vectorization, using random positioning")
            import random
            for node in topic_nodes:
                node['x'] = random.uniform(-200, 200)
                node['y'] = random.uniform(-200, 200)
            return nodes

        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(topic_texts)

        # Try UMAP for 2D positioning
        positions = None
        try:
            import umap
            reducer = umap.UMAP(n_components=2, random_state=42)
            positions = reducer.fit_transform(tfidf_matrix.toarray())
            logger.info("Applied UMAP for semantic positioning")
        except ImportError:
            # Fallback to t-SNE
            try:
                from sklearn.manifold import TSNE
                positions = TSNE(n_components=2,
                                 random_state=42,
                                 perplexity=min(30, len(topic_nodes)-1)
                                 ).fit_transform(tfidf_matrix.toarray())
                logger.info("UMAP not available, applied t-SNE for semantic positioning")
            except ImportError:
                logger.warning("Neither UMAP nor t-SNE available, using random positioning")
                import random
                for node in topic_nodes:
                    node['x'] = random.uniform(-200, 200)
                    node['y'] = random.uniform(-200, 200)
                return nodes

        # Scale positions
        positions = positions * 50

        # Update node positions
        for i, node in enumerate(topic_nodes):
            node['x'] = float(positions[i][0])
            node['y'] = float(positions[i][1])

        return nodes
    
    def get_topics(self) -> List[Dict]:
        """Get all topic nodes with their summaries."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Topic)
                RETURN t.topic_id as id, t.name as name, t.size as size,
                       t.top_words as top_words, t.sample_titles as sample_titles
                ORDER BY t.size DESC
            """)
            
            topics = []
            for record in result:
                topics.append({
                    'id': record['id'],
                    'name': record['name'],
                    'size': record['size'],
                    'top_words': record['top_words'],
                    'sample_titles': record['sample_titles']
                })
            
            return topics
    
    def get_chats(self, limit: int = 50) -> List[Dict]:
        """Get chat nodes with their metadata."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                RETURN c.chat_id as id, c.title as title, c.create_time as create_time
                ORDER BY c.create_time DESC
                LIMIT $limit
            """, limit=limit)
            
            chats = []
            for record in result:
                chats.append({
                    'id': record['id'],
                    'title': record['title'],
                    'create_time': record['create_time']
                })
            
            return chats
    
    def get_messages_for_chat(self, chat_id: str, limit: int = 100) -> List[Dict]:
        """Get messages for a specific chat."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
                RETURN m.message_id as id, m.content as content, m.role as role,
                       m.timestamp as timestamp, m.cluster_id as cluster_id
                ORDER BY m.timestamp
                LIMIT $limit
            """, chat_id=chat_id, limit=limit)
            
            messages = []
            for record in result:
                messages.append({
                    'id': record['id'],
                    'content': record['content'],
                    'role': record['role'],
                    'timestamp': record['timestamp'],
                    'cluster_id': record['cluster_id']
                })
            
            return messages
    
    def get_messages_for_topic(self, topic_id: int, limit: int = 100) -> List[Dict]:
        """Get messages for a specific topic."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Topic {topic_id: $topic_id})-[:SUMMARIZES]->(m:Message)
                RETURN m.message_id as id, m.content as content, m.role as role,
                       m.timestamp as timestamp, m.cluster_id as cluster_id
                ORDER BY m.timestamp
                LIMIT $limit
            """, topic_id=topic_id, limit=limit)
            
            messages = []
            for record in result:
                messages.append({
                    'id': record['id'],
                    'content': record['content'],
                    'role': record['role'],
                    'timestamp': record['timestamp'],
                    'cluster_id': record['cluster_id']
                })
            
            return messages
    
    def search_messages(self, query: str, limit: int = 50) -> List[Dict]:
        """Search messages by content."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                WHERE toLower(m.content) CONTAINS toLower($query)
                RETURN m.message_id as id, m.content as content, m.role as role,
                       m.timestamp as timestamp, m.cluster_id as cluster_id
                ORDER BY m.timestamp DESC
                LIMIT $limit
            """, {"query": query, "limit": limit})
            
            messages = []
            for record in result:
                messages.append({
                    'id': record['id'],
                    'content': record['content'],
                    'role': record['role'],
                    'timestamp': record['timestamp'],
                    'cluster_id': record['cluster_id']
                })
            
            return messages

# Initialize services
neo4j_service = Neo4jService()
data_lake_service = DataLakeService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    neo4j_service.connect()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    neo4j_service.close()

# Pydantic models for API responses
class GraphData(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class Topic(BaseModel):
    id: int
    name: str
    size: int
    top_words: List[str]
    sample_titles: List[str]

class Chat(BaseModel):
    id: str
    title: str
    create_time: Optional[float]

class Message(BaseModel):
    id: str
    content: str
    role: str
    timestamp: Optional[float]
    cluster_id: Optional[int]

# API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ChatMind API is running"}

@app.get("/api/stats/dashboard")
async def get_stats():
    """Get dashboard statistics from real data"""
    try:
        stats = get_dashboard_stats()
        return stats
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/debug/nodes")
async def debug_nodes():
    """Debug endpoint to see what nodes are in the database."""
    try:
        with neo4j_service.driver.session() as session:
            # Get count of each node type
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            
            node_counts = []
            for record in result:
                node_counts.append({
                    "labels": record["labels"],
                    "count": record["count"]
                })
            
            return {"node_counts": node_counts}
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/chat-properties")
async def debug_chat_properties():
    """Debug endpoint to see Chat node properties."""
    try:
        with neo4j_service.driver.session() as session:
            # Get sample Chat node properties
            result = session.run("""
                MATCH (c:Chat)
                RETURN c LIMIT 3
            """)
            
            sample_chats = []
            for record in result:
                chat_node = record["c"]
                sample_chats.append({
                    "properties": dict(chat_node),
                    "labels": list(chat_node.labels)
                })
            
            return {"sample_chats": sample_chats}
    except Exception as e:
        return {"error": str(e)}

@app.get("/graph", response_model=GraphData)
async def get_graph_data(
    limit: int = 100,
    node_types: str = None,  # Comma-separated list like "Topic,Chat"
    parent_id: str = None,
    use_semantic_positioning: bool = False
):
    """Get graph data for visualization with optional filtering and semantic positioning."""
    try:
        # Parse node_types parameter
        node_types_list = None
        if node_types:
            node_types_list = [t.strip() for t in node_types.split(',')]
        
        data = neo4j_service.get_graph_data(limit, node_types_list, parent_id, use_semantic_positioning)
        return GraphData(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph data: {e}")

@app.get("/topics", response_model=List[Topic])
async def get_topics():
    """Get all topics."""
    try:
        topics = neo4j_service.get_topics()
        return [Topic(**topic) for topic in topics]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topics: {e}")

@app.get("/chats", response_model=List[Chat])
async def get_chats(limit: int = 50):
    """Get all chats."""
    try:
        chats = neo4j_service.get_chats(limit)
        return [Chat(**chat) for chat in chats]
    except Exception as e:
        logger.error(f"Error in get_chats: {e}")
        # Return empty list instead of 500 error if no chats found
        return []

@app.get("/chats/{chat_id}/messages", response_model=List[Message])
async def get_chat_messages(chat_id: str, limit: int = 100):
    """Get messages for a specific chat."""
    try:
        # Limit to maximum 500 messages to prevent resource exhaustion
        actual_limit = min(limit, 500)
        messages = neo4j_service.get_messages_for_chat(chat_id, actual_limit)
        return [Message(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat messages: {e}")

@app.get("/topics/{topic_id}/messages", response_model=List[Message])
async def get_topic_messages(topic_id: int, limit: int = 100):
    """Get messages for a specific topic."""
    try:
        # Limit to maximum 500 messages to prevent resource exhaustion
        actual_limit = min(limit, 500)
        messages = neo4j_service.get_messages_for_topic(topic_id, actual_limit)
        return [Message(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topic messages: {e}")

@app.get("/search", response_model=List[Message])
async def search_messages(query: str, limit: int = 50):
    """Search messages by content."""
    try:
        messages = neo4j_service.search_messages(query, limit)
        return [Message(**msg) for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search messages: {e}")


@app.get("/tags")
async def get_all_tags():
    """Get all available tags from the knowledge graph."""
    try:
        with neo4j_service.driver.session() as session:
            # Get all unique tags from chunks
            result = session.run("""
                MATCH (c:Message)
                WHERE c.tags IS NOT NULL
                UNWIND c.tags as tag
                RETURN DISTINCT tag
                ORDER BY tag
            """)
            
            tags = [record['tag'] for record in result]
            
            # Get all unique categories
            result = session.run("""
                MATCH (c:Message)
                WHERE c.category IS NOT NULL
                RETURN DISTINCT c.category as category
                ORDER BY category
            """)
            
            categories = [record['category'] for record in result]
            
            return {
                'tags': tags,
                'categories': categories
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tags: {e}")


@app.get("/search/by-tags")
async def search_by_tags(
    tags: str = None,
    category: str = None,
    limit: int = 50
):
    """Search messages by tags and/or category."""
    try:
        with neo4j_service.driver.session() as session:
            query = "MATCH (c:Message) WHERE 1=1"
            params = {}
            
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                query += " AND ANY(tag IN c.tags WHERE tag IN $tags)"
                params['tags'] = tag_list
            
            if category:
                query += " AND c.category = $category"
                params['category'] = category
            
            query += """
                RETURN c.id as id, c.content as content, c.role as role,
                       c.timestamp as timestamp, c.cluster_id as cluster_id,
                       c.tags as tags, c.category as category
                ORDER BY c.timestamp DESC
                LIMIT $limit
            """
            params['limit'] = limit
            
            result = session.run(query, params)
            messages = [dict(record) for record in result]
            
            return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search by tags: {e}")


@app.get("/graph/filtered")
async def get_filtered_graph(
    tags: str = None,
    category: str = None,
    limit: int = 100
):
    """Get filtered graph data based on tags and/or category."""
    try:
        with neo4j_service.driver.session() as session:
            # Build the query based on filters
            query = """
                MATCH (c:Message)
                WHERE 1=1
            """
            params = {}
            
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
                query += " AND ANY(tag IN c.tags WHERE tag IN $tags)"
                params['tags'] = tag_list
            
            if category:
                query += " AND c.category = $category"
                params['category'] = category
            
            query += """
                WITH c
                MATCH (c)-[:CONTAINS]-(chat:Chat)
                MATCH (chat)-[:SUMMARIZES]-(topic:Topic)
                
                RETURN DISTINCT
                    c.id as message_id,
                    c.content as message_content,
                    c.role as message_role,
                    c.tags as message_tags,
                    c.category as message_category,
                    chat.id as chat_id,
                    chat.title as chat_title,
                    topic.id as topic_id,
                    topic.name as topic_name
                
                LIMIT $limit
            """
            params['limit'] = limit
            
            result = session.run(query, params)
            
            # Convert to graph format
            nodes = []
            edges = []
            node_ids = set()
            
            for record in result:
                # Add message node
                message_id = f"message_{record['message_id']}"
                if message_id not in node_ids:
                    nodes.append({
                        'id': message_id,
                        'type': 'Message',
                        'properties': {
                            'id': record['message_id'],
                            'content': record['message_content'],
                            'role': record['message_role'],
                            'tags': record['message_tags'],
                            'category': record['message_category']
                        }
                    })
                    node_ids.add(message_id)
                
                # Add chat node
                chat_id = f"chat_{record['chat_id']}"
                if chat_id not in node_ids:
                    nodes.append({
                        'id': chat_id,
                        'type': 'Chat',
                        'properties': {
                            'id': record['chat_id'],
                            'title': record['chat_title']
                        }
                    })
                    node_ids.add(chat_id)
                
                # Add topic node
                topic_id = f"topic_{record['topic_id']}"
                if topic_id not in node_ids:
                    nodes.append({
                        'id': topic_id,
                        'type': 'Topic',
                        'properties': {
                            'id': record['topic_id'],
                            'name': record['topic_name']
                        }
                    })
                    node_ids.add(topic_id)
                
                # Add edges
                edges.append({
                    'source': topic_id,
                    'target': chat_id,
                    'type': 'SUMMARIZES'
                })
                edges.append({
                    'source': chat_id,
                    'target': message_id,
                    'type': 'CONTAINS'
                })
            
            return {
                'nodes': nodes,
                'edges': edges
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get filtered graph: {e}")

# Data Lake endpoints
@app.get("/lake/chat/{chat_id}")
async def get_data_lake_chat(chat_id: str):
    """Get a specific chat from the data lake."""
    try:
        chat = data_lake_service.get_chat(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        return chat
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat: {e}")

@app.get("/lake/message/{message_id}")
async def get_data_lake_message(message_id: str):
    """Get a specific message from the data lake."""
    try:
        message = data_lake_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message: {e}")

@app.get("/lake/chat/{chat_id}/messages")
async def get_data_lake_chat_messages(chat_id: str):
    """Get all messages for a specific chat from the data lake."""
    try:
        messages = data_lake_service.get_chat_messages(chat_id)
        return {"chat_id": chat_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat messages: {e}")

# ChatGPT URL endpoints
@app.get("/lake/chat/{chat_id}/urls")
async def get_chat_urls(chat_id: str):
    """Get all ChatGPT URLs for a specific chat."""
    try:
        urls = data_lake_service.get_chat_urls(chat_id)
        return {"chat_id": chat_id, "urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat URLs: {e}")

@app.get("/lake/url/{conversation_id}")
async def get_url_mapping(conversation_id: str):
    """Get URL mapping by conversation ID."""
    try:
        url_mapping = data_lake_service.get_url_mapping(conversation_id)
        if not url_mapping:
            raise HTTPException(status_code=404, detail="URL mapping not found")
        return url_mapping
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get URL mapping: {e}")

@app.get("/lake/urls/search")
async def search_urls(query: str):
    """Search URL mappings by chat title."""
    try:
        urls = data_lake_service.search_urls_by_title(query)
        return {"query": query, "urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search URLs: {e}")

@app.get("/stats")
async def get_stats():
    """Get graph statistics."""
    try:
        with neo4j_service.driver.session() as session:
            # Count nodes by type
            node_stats = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
            """)
            
            # Count relationships by type
            edge_stats = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
            """)
            
            stats = {
                'nodes': {record['type']: record['count'] for record in node_stats},
                'edges': {record['type']: record['count'] for record in edge_stats}
            }
            
            return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}")


# Cost Tracking Endpoints
@app.get("/costs/statistics")
async def get_cost_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    operation: Optional[str] = None
):
    """Get cost and usage statistics."""
    try:
        from chatmind.cost_tracker.tracker import get_cost_tracker
        
        tracker = get_cost_tracker()
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = date.fromisoformat(start_date)
        if end_date:
            end_dt = date.fromisoformat(end_date)
        
        stats = tracker.get_statistics(
            start_date=start_dt,
            end_date=end_dt,
            operation=operation
        )
        
        return stats
    except ImportError:
        raise HTTPException(status_code=503, detail="Cost tracker not available")
    except Exception as e:
        logger.error(f"Error getting cost statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cost statistics")


@app.get("/costs/recent")
async def get_recent_calls(limit: int = 50):
    """Get recent API calls."""
    try:
        from chatmind.cost_tracker.tracker import get_cost_tracker
        
        tracker = get_cost_tracker()
        calls = tracker.get_recent_calls(limit=limit)
        
        return calls
    except ImportError:
        raise HTTPException(status_code=503, detail="Cost tracker not available")
    except Exception as e:
        logger.error(f"Error getting recent calls: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent calls")


@app.get("/costs/daily")
async def get_daily_costs(days: int = 30):
    """Get daily cost breakdown."""
    try:
        from chatmind.cost_tracker.tracker import get_cost_tracker
        
        tracker = get_cost_tracker()
        daily_costs = tracker.get_daily_costs(days=days)
        
        return daily_costs
    except ImportError:
        raise HTTPException(status_code=503, detail="Cost tracker not available")
    except Exception as e:
        logger.error(f"Error getting daily costs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get daily costs")


@app.post("/costs/export")
async def export_cost_data():
    """Export all cost data to JSON."""
    try:
        from chatmind.cost_tracker.tracker import get_cost_tracker
        
        tracker = get_cost_tracker()
        output_file = f"data/cost_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        tracker.export_data(output_file)
        
        return {"message": f"Cost data exported to {output_file}"}
    except ImportError:
        raise HTTPException(status_code=503, detail="Cost tracker not available")
    except Exception as e:
        logger.error(f"Error exporting cost data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export cost data")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 