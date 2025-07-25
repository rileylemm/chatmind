"""
ChatMind API Services

Business logic layer for handling data operations and statistics.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

logger = logging.getLogger(__name__)

class Neo4jService:
    """Service for Neo4j database operations"""
    
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
        use_semantic_positioning: bool = False
    ) -> Dict[str, Any]:
        """Get graph data from Neo4j"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                # Build query based on parameters
                query = """
                MATCH (n)
                """
                
                if node_types:
                    type_conditions = []
                    for t in node_types:
                        if t == "Topic":
                            type_conditions.append("n:Topic")
                        else:
                            type_conditions.append(f"n:{t}")
                    query += f" WHERE {' OR '.join(type_conditions)}"
                
                if parent_id:
                    query += f"""
                    MATCH (parent)-[:CONTAINS*]->(n)
                    WHERE parent.id = $parent_id
                    """
                
                query += """
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                LIMIT $limit
                """
                
                result = session.run(query, limit=limit, parent_id=parent_id)
                
                nodes = []
                edges = []
                node_ids = set()
                
                for record in result:
                    # Process nodes
                    for node_key in ['n', 'm']:
                        if record[node_key] and record[node_key].id not in node_ids:
                            node = record[node_key]
                            node_data = {
                                "id": node.id,
                                "type": list(node.labels)[0] if node.labels else "Unknown",
                                "properties": dict(node)
                            }
                            nodes.append(node_data)
                            node_ids.add(node.id)
                    
                    # Process edges
                    if record['r']:
                        edge = record['r']
                        edge_data = {
                            "source": edge.start_node.id,
                            "target": edge.end_node.id,
                            "type": edge.type,
                            "properties": dict(edge)
                        }
                        edges.append(edge_data)
                
                return {"nodes": nodes, "edges": edges}
                
        except Exception as e:
            logger.error(f"Error fetching graph data: {e}")
            raise RuntimeError(f"Failed to fetch graph data: {e}")
    
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
                        "id": topic.id,
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
                RETURN c
                ORDER BY c.create_time DESC
                LIMIT $limit
                """
                result = session.run(query, limit=limit)
                
                chats = []
                for record in result:
                    chat = record['c']
                    chats.append({
                        "id": chat.id,
                        "title": chat.get('title', ''),
                        "create_time": chat.get('create_time'),
                        "message_count": chat.get('message_count', 0)
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
                MATCH (c:Chat {id: $chat_id})-[:CONTAINS]->(m:Message)
                RETURN m
                ORDER BY m.timestamp
                LIMIT $limit
                """
                result = session.run(query, chat_id=chat_id, limit=limit)
                
                messages = []
                for record in result:
                    message = record['m']
                    messages.append({
                        "id": message.id,
                        "content": message.get('content', ''),
                        "role": message.get('role', ''),
                        "timestamp": message.get('timestamp'),
                        "cluster_id": message.get('cluster_id')
                    })
                
                return messages
                
        except Exception as e:
            logger.error(f"Error fetching messages for chat {chat_id}: {e}")
            raise RuntimeError(f"Failed to fetch messages: {e}")
    
    def search_messages(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search messages by content"""
        if not self.driver:
            raise ConnectionError("Database not connected")
        
        try:
            with self.driver.session() as session:
                # Get all messages to search through (no limit for comprehensive search)
                search_query = """
                MATCH (m:Message)
                RETURN m
                ORDER BY m.timestamp DESC
                """
                result = session.run(search_query)
                
                messages = []
                for record in result:
                    message = record['m']
                    # Filter by content in Python instead of Neo4j
                    content = message.get('content', '')
                    if search_term.lower() in content.lower():
                        messages.append({
                            "id": message.id,
                            "content": content,
                            "role": message.get('role', ''),
                            "timestamp": message.get('timestamp'),
                            "cluster_id": message.get('cluster_id')
                        })
                
                # Apply the limit after finding all matches
                messages = messages[:limit]
                
                logger.info(f"Search found {len(messages)} messages for query '{search_term}'")
                return messages
                
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise RuntimeError(f"Failed to search messages: {e}")


class StatsService:
    """Service for calculating statistics"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        try:
            # Get chat stats
            chats_file = self.data_dir / "processed" / "chats.jsonl"
            total_chats = 0
            total_messages = 0
            
            if chats_file.exists():
                with open(chats_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            chat = json.loads(line)
                            total_chats += 1
                            total_messages += len(chat.get('messages', []))
            
            # Get tag stats
            tags_file = self.data_dir / "tags" / "tags_master_list_generic.json"
            active_tags = 0
            if tags_file.exists():
                with open(tags_file, 'r') as f:
                    tags = json.load(f)
                    active_tags = len(tags)
            
            # Get cost stats
            cost_db = self.data_dir / "cost_tracker.db"
            total_cost = 0.0
            total_calls = 0
            
            if cost_db.exists():
                conn = sqlite3.connect(cost_db)
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(cost_usd) FROM api_calls WHERE success = 1")
                total_cost = cursor.fetchone()[0] or 0.0
                cursor.execute("SELECT COUNT(*) FROM api_calls")
                total_calls = cursor.fetchone()[0] or 0
                conn.close()
            
            # Get cluster stats
            cluster_file = self.data_dir / "embeddings" / "cluster_summaries.json"
            total_clusters = 0
            if cluster_file.exists():
                with open(cluster_file, 'r') as f:
                    clusters = json.load(f)
                    total_clusters = len(clusters)
            
            return {
                "total_chats": total_chats,
                "total_messages": total_messages,
                "active_tags": active_tags,
                "total_cost": f"${total_cost:.2f}",
                "total_clusters": total_clusters,
                "total_calls": total_calls
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                "total_chats": 0,
                "total_messages": 0,
                "active_tags": 0,
                "total_cost": "$0.00",
                "total_clusters": 0,
                "total_calls": 0
            }
    
    def get_cost_statistics(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None,
        operation: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed cost statistics"""
        try:
            cost_db = self.data_dir / "cost_tracker.db"
            if not cost_db.exists():
                return {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "success_rate": 0.0,
                    "total_cost_usd": 0.0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "model_statistics": {},
                    "operation_statistics": {},
                    "date_range": {"start_date": start_date, "end_date": end_date}
                }
            
            conn = sqlite3.connect(cost_db)
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_conditions = []
            params = {}
            
            if start_date:
                where_conditions.append("timestamp >= $start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_conditions.append("timestamp <= $end_date")
                params['end_date'] = end_date
            
            if operation:
                where_conditions.append("operation = $operation")
                params['operation'] = operation
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Get basic stats
            cursor.execute(f"SELECT COUNT(*) FROM api_calls WHERE {where_clause}", params)
            total_calls = cursor.fetchone()[0] or 0
            
            cursor.execute(f"SELECT COUNT(*) FROM api_calls WHERE success = 1 AND {where_clause}", params)
            successful_calls = cursor.fetchone()[0] or 0
            
            cursor.execute(f"SELECT COUNT(*) FROM api_calls WHERE success = 0 AND {where_clause}", params)
            failed_calls = cursor.fetchone()[0] or 0
            
            cursor.execute(f"SELECT SUM(cost_usd) FROM api_calls WHERE success = 1 AND {where_clause}", params)
            total_cost = cursor.fetchone()[0] or 0.0
            
            cursor.execute(f"SELECT SUM(input_tokens) FROM api_calls WHERE {where_clause}", params)
            total_input_tokens = cursor.fetchone()[0] or 0
            
            cursor.execute(f"SELECT SUM(output_tokens) FROM api_calls WHERE {where_clause}", params)
            total_output_tokens = cursor.fetchone()[0] or 0
            
            # Get model statistics
            cursor.execute(f"""
                SELECT model, COUNT(*), SUM(cost_usd), AVG(cost_usd)
                FROM api_calls 
                WHERE {where_clause}
                GROUP BY model
            """, params)
            model_stats = {}
            for row in cursor.fetchall():
                model_stats[row[0]] = {
                    "count": row[1],
                    "total_cost": row[2] or 0.0,
                    "avg_cost": row[3] or 0.0
                }
            
            # Get operation statistics
            cursor.execute(f"""
                SELECT operation, COUNT(*), SUM(cost_usd), AVG(cost_usd)
                FROM api_calls 
                WHERE {where_clause}
                GROUP BY operation
            """, params)
            operation_stats = {}
            for row in cursor.fetchall():
                operation_stats[row[0]] = {
                    "count": row[1],
                    "total_cost": row[2] or 0.0,
                    "avg_cost": row[3] or 0.0
                }
            
            conn.close()
            
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0.0
            
            return {
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": round(success_rate, 2),
                "total_cost_usd": round(total_cost, 2),
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "model_statistics": model_stats,
                "operation_statistics": operation_stats,
                "date_range": {"start_date": start_date, "end_date": end_date}
            }
            
        except Exception as e:
            logger.error(f"Error getting cost statistics: {e}")
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "success_rate": 0.0,
                "total_cost_usd": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "model_statistics": {},
                "operation_statistics": {},
                "date_range": {"start_date": start_date, "end_date": end_date}
            } 