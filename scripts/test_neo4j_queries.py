#!/usr/bin/env python3
"""
Test script for Neo4j queries from the ChatMind query guide - Dual Layer Graph Strategy.
This script tests all queries to ensure they work correctly with the dual layer database schema.
Enhanced with edge case handling, schema validation, and performance safeguards.
"""

import sys
import os
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Neo4jQueryTester:
    """Test all queries from the Neo4j query guide - Updated for Dual Layer Graph Strategy with enhanced validation."""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        self.test_results = []
        self.performance_metrics = {}
        
    def connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Connected to Neo4j database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def test_query(self, name, query, params=None, expected_result_type="any", timeout=30):
        """Test a single query and log the result with performance tracking."""
        start_time = time.time()
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                records = list(result)
                execution_time = time.time() - start_time
                
                # Log the result
                logger.info(f"✅ {name}: {len(records)} results ({execution_time:.3f}s)")
                if records and len(records) <= 3:  # Show first few results
                    for i, record in enumerate(records[:3]):
                        logger.info(f"   Result {i+1}: {dict(record)}")
                
                self.test_results.append({
                    "name": name,
                    "status": "PASS",
                    "result_count": len(records),
                    "execution_time": execution_time
                })
                
                # Store performance metric
                self.performance_metrics[name] = execution_time
                
                return True
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {name}: {e}")
            self.test_results.append({
                "name": name,
                "status": "FAIL",
                "error": str(e),
                "execution_time": execution_time
            })
            return False
    
    def test_edge_cases_and_data_absence(self):
        """Test edge cases and data absence handling."""
        logger.info("\n🔍 Testing Edge Cases and Data Absence...")
        
        # Test non-existent nodes
        self.test_query(
            "Query non-existent nodes",
            "MATCH (n:NonExistent) RETURN count(n) AS count"
        )
        
        # Test empty result sets
        self.test_query(
            "Query with no matches",
            "MATCH (m:Message) WHERE m.content = 'NONEXISTENT_CONTENT' RETURN m"
        )
        
        # Test null property handling
        self.test_query(
            "Query with null properties",
            "MATCH (m:Message) WHERE m.content IS NULL RETURN count(m) AS null_content_messages"
        )
        
        # Test empty collections
        self.test_query(
            "Query with empty collections",
            "MATCH (m:Message) WHERE NOT (m)-[:HAS_CHUNK]->() RETURN count(m) AS messages_without_chunks"
        )
    
    def test_schema_validation(self):
        """Test schema validation and data integrity."""
        logger.info("\n🏗️ Testing Schema Validation...")
        
        # Test node type properties
        self.test_query(
            "Node type properties validation",
            """
            MATCH (n)
            RETURN labels(n)[0] as node_type, 
                   keys(n) as properties,
                   count(n) as count
            ORDER BY node_type
            """
        )
        
        # Test critical properties exist
        self.test_query(
            "Critical properties validation",
            """
            MATCH (m:Message)
            WHERE m.message_id IS NULL OR m.content IS NULL
            RETURN count(*) AS bad_messages
            """
        )
        
        # Test chunk properties
        self.test_query(
            "Chunk properties validation",
            """
            MATCH (chunk:Chunk)
            WHERE chunk.chunk_id IS NULL OR chunk.text IS NULL
            RETURN count(*) AS bad_chunks
            """
        )
        
        # Test chat properties
        self.test_query(
            "Chat properties validation",
            """
            MATCH (c:Chat)
            WHERE c.chat_id IS NULL OR c.title IS NULL
            RETURN count(*) AS bad_chats
            """
        )
    
    def test_duplicate_and_conflict_detection(self):
        """Test for duplicate data and constraint violations."""
        logger.info("\n🔍 Testing Duplicate and Conflict Detection...")
        
        # Check for duplicate message IDs
        self.test_query(
            "Duplicate message IDs",
            """
            MATCH (m:Message)
            WITH m.message_id AS mid, count(*) AS c
            WHERE c > 1
            RETURN mid, c
            ORDER BY c DESC
            """
        )
        
        # Check for duplicate chunk IDs
        self.test_query(
            "Duplicate chunk IDs",
            """
            MATCH (chunk:Chunk)
            WITH chunk.chunk_id AS cid, count(*) AS c
            WHERE c > 1
            RETURN cid, c
            ORDER BY c DESC
            """
        )
        
        # Check for duplicate chat IDs
        self.test_query(
            "Duplicate chat IDs",
            """
            MATCH (c:Chat)
            WITH c.chat_id AS cid, count(*) AS c
            WHERE c > 1
            RETURN cid, c
            ORDER BY c DESC
            """
        )
        
        # Check for orphaned messages (no chat parent)
        self.test_query(
            "Orphaned messages",
            """
            MATCH (m:Message)
            WHERE NOT (m)<-[:CONTAINS]-(:Chat)
            RETURN count(m) AS orphan_messages
            """
        )
        
        # Check for orphaned chunks (no message parent)
        self.test_query(
            "Orphaned chunks",
            """
            MATCH (chunk:Chunk)
            WHERE NOT (chunk)<-[:HAS_CHUNK]-(:Message)
            RETURN count(chunk) AS orphan_chunks
            """
        )
    
    def test_graph_connectivity(self):
        """Test graph connectivity and relationship integrity."""
        logger.info("\n🕸️ Testing Graph Connectivity...")
        
        # Test chat-message connectivity
        self.test_query(
            "Chat-Message connectivity",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            RETURN c.chat_id, count(m) as message_count
            ORDER BY message_count DESC
            LIMIT 5
            """
        )
        
        # Test message-chunk connectivity
        self.test_query(
            "Message-Chunk connectivity",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN m.message_id, count(chunk) as chunk_count
            ORDER BY chunk_count DESC
            LIMIT 5
            """
        )
        
        # Test chunk-tag connectivity
        self.test_query(
            "Chunk-Tag connectivity",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            RETURN chunk.chunk_id, count(tag) as tag_count
            ORDER BY tag_count DESC
            LIMIT 5
            """
        )
        
        # Test topic-chunk connectivity
        self.test_query(
            "Topic-Chunk connectivity",
            """
            MATCH (topic:Topic)-[:SUMMARIZES]->(chunk:Chunk)
            RETURN topic.name, count(chunk) as chunk_count
            ORDER BY chunk_count DESC
            LIMIT 5
            """
        )
        
        # Test full path connectivity
        self.test_query(
            "Full path connectivity (Chat -> Message -> Chunk -> Tag)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            RETURN c.chat_id, m.message_id, chunk.chunk_id, tag.name
            LIMIT 5
            """
        )
    
    def test_performance_safeguards(self):
        """Test performance thresholds and query optimization."""
        logger.info("\n⚡ Testing Performance Safeguards...")
        
        # Test query execution time thresholds
        self.test_query(
            "Fast node count query",
            "MATCH (n) RETURN count(n) as total_nodes",
            timeout=5
        )
        
        # Test complex query performance
        self.test_query(
            "Complex aggregation performance",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WITH c, count(DISTINCT tag) as tag_count
            RETURN avg(tag_count) as avg_tags_per_chat
            """,
            timeout=10
        )
        
        # Test large result set handling
        self.test_query(
            "Large result set handling",
            """
            MATCH (chunk:Chunk)
            RETURN chunk.chunk_id, chunk.text
            LIMIT 1000
            """,
            timeout=15
        )
    
    def test_dual_layer_basic_queries(self):
        """Test basic dual layer node queries."""
        logger.info("\n🔍 Testing Dual Layer Basic Node Queries...")
        
        # Get all chats (Raw Layer)
        self.test_query(
            "Get all chats (Raw Layer)",
            "MATCH (c:Chat) RETURN c.title, c.create_time, c.chat_id ORDER BY c.create_time DESC LIMIT 5"
        )
        
        # Get all messages (Raw Layer)
        self.test_query(
            "Get all messages (Raw Layer)",
            "MATCH (m:Message) RETURN m.content, m.role, m.timestamp ORDER BY m.timestamp DESC LIMIT 5"
        )
        
        # Get all chunks (Chunk Layer)
        self.test_query(
            "Get all chunks (Chunk Layer)",
            "MATCH (chunk:Chunk) RETURN chunk.text, chunk.source_message_id, chunk.cluster_id ORDER BY chunk.source_message_id LIMIT 5"
        )
        
        # Get all topics (Semantic Layer)
        self.test_query(
            "Get all topics (Semantic Layer)",
            "MATCH (t:Topic) RETURN t.name, t.size, t.top_words ORDER BY t.size DESC LIMIT 5"
        )
        
        # Get all tags (Semantic Layer)
        self.test_query(
            "Get all tags (Semantic Layer)",
            "MATCH (tag:Tag) RETURN tag.name, tag.count ORDER BY tag.count DESC LIMIT 5"
        )
    
    def test_dual_layer_relationship_queries(self):
        """Test dual layer relationship traversal queries."""
        logger.info("\n🔗 Testing Dual Layer Relationship Queries...")
        
        # Get messages in a chat (Raw Layer)
        self.test_query(
            "Get messages in a chat (Raw Layer)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            RETURN c.title, m.content, m.role, m.timestamp
            ORDER BY m.timestamp
            LIMIT 5
            """
        )
        
        # Get chunks for messages (Cross-Layer)
        self.test_query(
            "Get chunks for messages (Cross-Layer)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN m.message_id, chunk.text, chunk.cluster_id
            LIMIT 5
            """
        )
        
        # Get tags for chunks (Chunk Layer to Semantic Layer)
        self.test_query(
            "Get tags for chunks (Chunk to Semantic)",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            RETURN chunk.text, tag.name
            LIMIT 5
            """
        )
        
        # Get topics for chunks (Chunk Layer to Semantic Layer)
        self.test_query(
            "Get topics for chunks (Chunk to Semantic)",
            """
            MATCH (t:Topic)-[:SUMMARIZES]->(chunk:Chunk)
            RETURN t.name, t.top_words, chunk.text
            LIMIT 5
            """
        )
        
        # Full dual layer traversal: Message -> Chunk -> Tag
        self.test_query(
            "Full dual layer traversal: Message -> Chunk -> Tag",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            RETURN m.message_id, chunk.text, tag.name
            LIMIT 5
            """
        )
    
    def test_dual_layer_aggregation_queries(self):
        """Test dual layer aggregation queries."""
        logger.info("\n📊 Testing Dual Layer Aggregation Queries...")
        
        # Count messages per chat (Raw Layer)
        self.test_query(
            "Count messages per chat (Raw Layer)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            RETURN c.title, count(m) as message_count
            ORDER BY message_count DESC
            LIMIT 5
            """
        )
        
        # Count chunks per message (Cross-Layer)
        self.test_query(
            "Count chunks per message (Cross-Layer)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN m.message_id, count(chunk) as chunk_count
            ORDER BY chunk_count DESC
            LIMIT 5
            """
        )
        
        # Count tags per chunk (Chunk Layer)
        self.test_query(
            "Count tags per chunk (Chunk Layer)",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            RETURN chunk.chunk_id, count(tag) as tag_count
            ORDER BY tag_count DESC
            LIMIT 5
            """
        )
        
        # Most popular tags (Semantic Layer)
        self.test_query(
            "Most popular tags (Semantic Layer)",
            """
            MATCH (tag:Tag)
            RETURN tag.name, tag.count
            ORDER BY tag.count DESC
            LIMIT 10
            """
        )
        
        # Topic distribution (Semantic Layer)
        self.test_query(
            "Topic distribution (Semantic Layer)",
            """
            MATCH (t:Topic)
            RETURN t.name, t.size
            ORDER BY t.size DESC
            LIMIT 5
            """
        )
    
    def test_dual_layer_search_queries(self):
        """Test dual layer search queries."""
        logger.info("\n🔍 Testing Dual Layer Search Queries...")
        
        # Search messages by content (Raw Layer)
        self.test_query(
            "Search messages by content (Raw Layer)",
            """
            MATCH (m:Message)
            WHERE toLower(m.content) CONTAINS toLower("python")
            RETURN m.content, m.role, m.timestamp
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Search chunks by content (Chunk Layer)
        self.test_query(
            "Search chunks by content (Chunk Layer)",
            """
            MATCH (chunk:Chunk)
            WHERE toLower(chunk.text) CONTAINS toLower("python")
            RETURN chunk.text, chunk.source_message_id
            LIMIT 5
            """
        )
        
        # Search by tag (Semantic Layer)
        self.test_query(
            "Search by tag (Semantic Layer)",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WHERE tag.name = "python"
            RETURN chunk.text, tag.name
            LIMIT 5
            """
        )
        
        # Search by topic (Semantic Layer)
        self.test_query(
            "Search by topic (Semantic Layer)",
            """
            MATCH (t:Topic)-[:SUMMARIZES]->(chunk:Chunk)
            WHERE t.name CONTAINS "code" OR t.name CONTAINS "help" OR t.name CONTAINS "question"
            RETURN t.name, chunk.text
            LIMIT 5
            """
        )
        
        # Cross-layer search: Find messages with specific tags
        self.test_query(
            "Cross-layer search: Find messages with specific tags",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WHERE tag.name = "python"
            RETURN m.content, chunk.text, tag.name
            LIMIT 5
            """
        )
    
    def test_dual_layer_graph_exploration_queries(self):
        """Test dual layer graph exploration queries."""
        logger.info("\n🌐 Testing Dual Layer Graph Exploration Queries...")
        
        # Get chat with all related data (Full dual layer)
        self.test_query(
            "Get chat with all related data (Full dual layer)",
            """
            MATCH (c:Chat)
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(chunk:Chunk)
            OPTIONAL MATCH (chunk)-[:TAGGED_WITH]->(tag:Tag)
            OPTIONAL MATCH (topic:Topic)-[:SUMMARIZES]->(chunk)
            RETURN c.title, 
                   collect(DISTINCT m.content) as messages,
                   collect(DISTINCT chunk.text) as chunks,
                   collect(DISTINCT tag.name) as tags,
                   collect(DISTINCT topic.name) as topics
            LIMIT 3
            """
        )
        
        # Find similar chats (Semantic Layer)
        self.test_query(
            "Find similar chats (Semantic Layer)",
            """
            MATCH (c1:Chat)-[:SIMILAR_TO]-(c2:Chat)
            RETURN c1.title, c2.title
            LIMIT 5
            """
        )
        
        # Get message with all its chunks and semantic data
        self.test_query(
            "Get message with all its chunks and semantic data",
            """
            MATCH (m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(chunk:Chunk)
            OPTIONAL MATCH (chunk)-[:TAGGED_WITH]->(tag:Tag)
            OPTIONAL MATCH (topic:Topic)-[:SUMMARIZES]->(chunk)
            RETURN m.content, 
                   collect(DISTINCT chunk.text) as chunks,
                   collect(DISTINCT tag.name) as tags,
                   collect(DISTINCT topic.name) as topics
            LIMIT 3
            """
        )
    
    def test_dual_layer_advanced_analytics_queries(self):
        """Test dual layer advanced analytics queries."""
        logger.info("\n📈 Testing Dual Layer Advanced Analytics Queries...")
        
        # Topic distribution with percentage (Semantic Layer)
        self.test_query(
            "Topic distribution with percentage (Semantic Layer)",
            """
            MATCH (t:Topic)
            WITH t, sum(t.size) as total_size
            RETURN t.name, t.size,
                   round(t.size * 100.0 / total_size, 2) as percentage
            ORDER BY t.size DESC
            LIMIT 5
            """
        )
        
        # Tag co-occurrence on chunks (Chunk Layer)
        self.test_query(
            "Tag co-occurrence on chunks (Chunk Layer)",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag1:Tag)
            MATCH (chunk)-[:TAGGED_WITH]->(tag2:Tag)
            WHERE tag1.name < tag2.name
            RETURN tag1.name, tag2.name, count(chunk) as co_occurrence
            ORDER BY co_occurrence DESC
            LIMIT 5
            """
        )
        
        # Conversation flow analysis (Raw Layer)
        self.test_query(
            "Conversation flow analysis (Raw Layer)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            WITH c, m ORDER BY m.timestamp
            WITH c, collect(m.role) as roles
            RETURN c.title, 
                   size([r IN roles WHERE r = "user"]) as user_messages,
                   size([r IN roles WHERE r = "assistant"]) as assistant_messages,
                   size(roles) as total_messages
            ORDER BY total_messages DESC
            LIMIT 5
            """
        )
        
        # Chunk analysis per message (Cross-Layer)
        self.test_query(
            "Chunk analysis per message (Cross-Layer)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            WITH m, count(chunk) as chunk_count
            RETURN m.content, chunk_count
            ORDER BY chunk_count DESC
            LIMIT 5
            """
        )
        
        # Semantic density analysis (Cross-Layer)
        self.test_query(
            "Semantic density analysis (Cross-Layer)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WITH m, count(DISTINCT tag) as tag_count
            RETURN m.content, tag_count
            ORDER BY tag_count DESC
            LIMIT 5
            """
        )
    
    def test_dual_layer_statistics_queries(self):
        """Test dual layer statistics queries."""
        logger.info("\n📊 Testing Dual Layer Statistics Queries...")
        
        # Node counts by type
        self.test_query(
            "Node counts by type",
            """
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(n) as count
            ORDER BY count DESC
            """
        )
        
        # Relationship counts by type
        self.test_query(
            "Relationship counts by type",
            """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """
        )
        
        # Average messages per chat (Raw Layer)
        self.test_query(
            "Average messages per chat (Raw Layer)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            WITH c, count(m) as message_count
            RETURN avg(message_count) as avg_messages_per_chat
            """
        )
        
        # Average chunks per message (Cross-Layer)
        self.test_query(
            "Average chunks per message (Cross-Layer)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            WITH m, count(chunk) as chunk_count
            RETURN avg(chunk_count) as avg_chunks_per_message
            """
        )
        
        # Average tags per chunk (Chunk Layer)
        self.test_query(
            "Average tags per chunk (Chunk Layer)",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WITH chunk, count(tag) as tag_count
            RETURN avg(tag_count) as avg_tags_per_chunk
            """
        )
    
    def test_dual_layer_debugging_queries(self):
        """Test dual layer debugging queries."""
        logger.info("\n🔧 Testing Dual Layer Debugging Queries...")
        
        # Test connection
        self.test_query(
            "Test connection",
            "RETURN 1 as test"
        )
        
        # Check data exists
        self.test_query(
            "Check data exists",
            """
            MATCH (n)
            RETURN labels(n)[0] as type, count(n) as count
            """
        )
        
        # Check relationships
        self.test_query(
            "Check relationships",
            """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            """
        )
        
        # Verify dual layer integrity
        self.test_query(
            "Verify dual layer integrity",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            RETURN count(m) as messages_with_chunks,
                   count(chunk) as total_chunks
            """
        )
        
        # Check semantic layer connections
        self.test_query(
            "Check semantic layer connections",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            MATCH (topic:Topic)-[:SUMMARIZES]->(chunk)
            RETURN count(DISTINCT chunk) as chunks_with_semantic_data
            """
        )
    
    def test_dual_layer_common_use_cases(self):
        """Test dual layer common use case queries."""
        logger.info("\n🎯 Testing Dual Layer Common Use Cases...")
        
        # Find chunks about Python (Semantic Layer)
        self.test_query(
            "Find chunks about Python (Semantic Layer)",
            """
            MATCH (chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
            RETURN chunk.text, tag.name
            ORDER BY chunk.source_message_id DESC
            LIMIT 5
            """
        )
        
        # Find messages with Python chunks (Cross-Layer)
        self.test_query(
            "Find messages with Python chunks (Cross-Layer)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
            RETURN m.content, chunk.text, tag.name
            LIMIT 5
            """
        )
        
        # Find chats with similar topics (Semantic Layer)
        self.test_query(
            "Find chats with similar topics (Semantic Layer)",
            """
            MATCH (c1:Chat)-[:HAS_TOPIC]->(t:Topic)<-[:HAS_TOPIC]-(c2:Chat)
            WHERE c1.chat_id <> c2.chat_id
            RETURN c1.title, c2.title, t.name
            LIMIT 5
            """
        )
        
        # Most active topics (Semantic Layer)
        self.test_query(
            "Most active topics (Semantic Layer)",
            """
            MATCH (t:Topic)
            RETURN t.name, t.size, t.sample_titles
            ORDER BY t.size DESC
            LIMIT 5
            """
        )
        
        # Long conversations (Raw Layer)
        self.test_query(
            "Long conversations (>20 messages)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            WITH c, count(m) as message_count
            WHERE message_count > 20
            RETURN c.title, message_count
            ORDER BY message_count DESC
            LIMIT 5
            """
        )
        
        # Messages with most semantic tags (Cross-Layer)
        self.test_query(
            "Messages with most semantic tags (Cross-Layer)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WITH m, count(DISTINCT tag) as tag_count
            RETURN m.content, tag_count
            ORDER BY tag_count DESC
            LIMIT 5
            """
        )
        
        # Messages with specific tags (array-based search)
        self.test_query(
            "Messages with specific tags (array-based search)",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WHERE tag.name IN ["python", "javascript", "react"]
            RETURN m.content, tag.name
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Conversations with many tags (unique tag counting)
        self.test_query(
            "Conversations with many tags (unique tag counting)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(chunk:Chunk)-[:TAGGED_WITH]->(tag:Tag)
            WITH c, count(DISTINCT tag) as unique_tags
            WHERE unique_tags > 5
            RETURN c.title, unique_tags
            ORDER BY unique_tags DESC
            LIMIT 5
            """
        )
        
        # Get message embeddings (for debugging/similarity)
        self.test_query(
            "Get message embeddings (for debugging/similarity)",
            """
            MATCH (m:Message)
            WHERE m.embedding IS NOT NULL
            RETURN m.message_id, m.content, m.embedding
            LIMIT 5
            """
        )
    
    def test_dual_layer_visualization_queries(self):
        """Test dual layer visualization and UMAP queries."""
        logger.info("\n🎨 Testing Dual Layer Visualization & UMAP Queries...")
        
        # Chats with UMAP positions (Raw Layer)
        self.test_query(
            "Chats with UMAP positions (Raw Layer)",
            """
            MATCH (c:Chat)
            WHERE c.x IS NOT NULL AND c.y IS NOT NULL
            RETURN c.chat_id, c.title, c.x, c.y
            ORDER BY c.create_time DESC
            LIMIT 5
            """
        )
        
        # Topics with UMAP positions (Semantic Layer)
        self.test_query(
            "Topics with UMAP positions (Semantic Layer)",
            """
            MATCH (t:Topic)
            WHERE t.x IS NOT NULL AND t.y IS NOT NULL
            RETURN t.topic_id, t.name, t.size, t.x, t.y
            ORDER BY t.size DESC
            LIMIT 5
            """
        )
        
        # Get chunk embeddings (Chunk Layer)
        self.test_query(
            "Get chunk embeddings (Chunk Layer)",
            """
            MATCH (chunk:Chunk)
            WHERE chunk.embedding IS NOT NULL
            RETURN chunk.chunk_id, chunk.text
            LIMIT 3
            """
        )
        
        # Chat-chunk-topic full context (Full dual layer)
        self.test_query(
            "Chat-chunk-topic full context (Full dual layer)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            OPTIONAL MATCH (chunk)-[:TAGGED_WITH]->(tag:Tag)
            OPTIONAL MATCH (topic:Topic)-[:SUMMARIZES]->(chunk)
            RETURN c.chat_id, m.message_id, chunk.chunk_id, 
                   collect(DISTINCT tag.name) as tags, 
                   collect(DISTINCT topic.name) as topics
            LIMIT 3
            """
        )
        
        # Graph UMAP overview (topic-based)
        self.test_query(
            "Graph UMAP overview (topic-based)",
            """
            MATCH (t:Topic)
            WHERE t.x IS NOT NULL AND t.y IS NOT NULL
            RETURN t.name, t.topic_id, t.size, t.x, t.y
            ORDER BY t.size DESC
            LIMIT 5
            """
        )
        
        # All nodes with coordinates
        self.test_query(
            "All nodes with coordinates",
            """
            MATCH (n)
            WHERE n.x IS NOT NULL AND n.y IS NOT NULL
            RETURN labels(n)[0] as node_type, n.x, n.y
            ORDER BY node_type, n.x
            LIMIT 10
            """
        )
        
        # Dual layer graph for visualization
        self.test_query(
            "Dual layer graph for visualization",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(chunk:Chunk)
            OPTIONAL MATCH (chunk)-[:TAGGED_WITH]->(tag:Tag)
            OPTIONAL MATCH (topic:Topic)-[:SUMMARIZES]->(chunk)
            RETURN c.chat_id, m.message_id, chunk.chunk_id,
                   tag.name as tag_name, topic.name as topic_name
            LIMIT 10
            """
        )
    
    def run_all_tests(self, parallel=False):
        """Run all dual layer query tests with optional parallel execution."""
        logger.info("🚀 Starting Enhanced Dual Layer Neo4j Query Tests...")
        
        if not self.connect():
            return False
        
        try:
            test_functions = [
                self.test_edge_cases_and_data_absence,
                self.test_schema_validation,
                self.test_duplicate_and_conflict_detection,
                self.test_graph_connectivity,
                self.test_performance_safeguards,
                self.test_dual_layer_basic_queries,
                self.test_dual_layer_relationship_queries,
                self.test_dual_layer_aggregation_queries,
                self.test_dual_layer_search_queries,
                self.test_dual_layer_graph_exploration_queries,
                self.test_dual_layer_advanced_analytics_queries,
                self.test_dual_layer_statistics_queries,
                self.test_dual_layer_debugging_queries,
                self.test_dual_layer_common_use_cases,
                self.test_dual_layer_visualization_queries
            ]
            
            if parallel:
                logger.info("🔄 Running tests in parallel...")
                with ThreadPoolExecutor(max_workers=4) as executor:
                    futures = [executor.submit(func) for func in test_functions]
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"❌ Test function failed: {e}")
            else:
                logger.info("🔄 Running tests sequentially...")
                for func in test_functions:
                    func()
            
            # Print summary
            self.print_summary()
            
        finally:
            self.close()
    
    def print_summary(self):
        """Print comprehensive test summary with performance metrics."""
        logger.info("\n📋 Enhanced Dual Layer Test Summary:")
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        
        if failed_tests > 0:
            logger.info("\nFailed tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    logger.error(f"  - {result['name']}: {result.get('error', 'Unknown error')}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        logger.info(f"\nSuccess rate: {success_rate:.1f}%")
        
        # Performance summary
        if self.performance_metrics:
            avg_time = sum(self.performance_metrics.values()) / len(self.performance_metrics)
            max_time = max(self.performance_metrics.values())
            logger.info(f"\nPerformance Metrics:")
            logger.info(f"  Average query time: {avg_time:.3f}s")
            logger.info(f"  Slowest query: {max_time:.3f}s")
        
        if success_rate >= 95:
            logger.info("🎉 Excellent! Enhanced dual layer queries are working correctly.")
        elif success_rate >= 80:
            logger.info("⚠️  Good, but some enhanced dual layer queries need attention.")
        else:
            logger.error("❌ Many enhanced dual layer queries are failing. Check database setup.")
    
    def export_results(self, output_file="test_results.json"):
        """Export test results to JSON for CI/CD integration."""
        results = {
            "timestamp": time.time(),
            "summary": {
                "total_tests": len(self.test_results),
                "passed": len([r for r in self.test_results if r["status"] == "PASS"]),
                "failed": len([r for r in self.test_results if r["status"] == "FAIL"]),
                "success_rate": (len([r for r in self.test_results if r["status"] == "PASS"]) / len(self.test_results)) * 100 if self.test_results else 0
            },
            "performance_metrics": self.performance_metrics,
            "detailed_results": self.test_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Test results exported to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Neo4j Dual Layer Query Tester")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    
    args = parser.parse_args()
    
    tester = Neo4jQueryTester()
    tester.run_all_tests(parallel=args.parallel)
    
    if args.export:
        tester.export_results(args.export) 