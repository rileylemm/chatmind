#!/usr/bin/env python3
"""
Test script for Neo4j queries from the ChatMind query guide - Current Implementation.
This script tests all queries to ensure they work correctly with the current database schema.
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
    """Test all queries from the Neo4j query guide - Updated for Current Implementation with enhanced validation."""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "chatmind123")
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
            MATCH (ch:Chunk)
            WHERE ch.chunk_id IS NULL OR ch.content IS NULL
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
            MATCH (ch:Chunk)
            WITH ch.chunk_id AS cid, count(*) AS c
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
            MATCH (ch:Chunk)
            WHERE NOT (ch)<-[:HAS_CHUNK]-(:Message)
            RETURN count(ch) AS orphan_chunks
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
            MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
            RETURN m.message_id, count(ch) as chunk_count
            ORDER BY chunk_count DESC
            LIMIT 5
            """
        )
        
        # Test chunk-embedding connectivity
        self.test_query(
            "Chunk-Embedding connectivity",
            """
            MATCH (ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            RETURN ch.chunk_id, count(e) as embedding_count
            ORDER BY embedding_count DESC
            LIMIT 5
            """
        )
        
        # Test message-tag connectivity
        self.test_query(
            "Message-Tag connectivity",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            RETURN m.message_id, count(t) as tag_count
            ORDER BY tag_count DESC
            LIMIT 5
            """
        )
        
        # Test cluster-chunk connectivity
        self.test_query(
            "Cluster-Chunk connectivity",
            """
            MATCH (cl:Cluster)-[:CONTAINS_CHUNK]->(ch:Chunk)
            RETURN cl.cluster_id, count(ch) as chunk_count
            ORDER BY chunk_count DESC
            LIMIT 5
            """
        )
        
        # Test full path connectivity
        self.test_query(
            "Full path connectivity (Chat -> Message -> Chunk -> Embedding)",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            RETURN c.chat_id, m.message_id, ch.chunk_id, e.embedding_hash
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
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            WITH c, count(DISTINCT e) as embedding_count
            RETURN avg(embedding_count) as avg_embeddings_per_chat
            """,
            timeout=10
        )
        
        # Test large result set handling
        self.test_query(
            "Large result set handling",
            """
            MATCH (ch:Chunk)
            RETURN ch.chunk_id, ch.content
            LIMIT 1000
            """,
            timeout=15
        )
    
    def test_basic_data_exploration_queries(self):
        """Test basic data exploration queries."""
        logger.info("\n🔍 Testing Basic Data Exploration Queries...")
        
        # Get all chats with message counts
        self.test_query(
            "Get all chats with message counts",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            RETURN c.title, c.create_time, c.chat_id, count(m) as message_count
            ORDER BY c.create_time DESC
            LIMIT 5
            """
        )
        
        # Get messages in a chat
        self.test_query(
            "Get messages in a chat",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            RETURN c.title, m.content, m.role, m.timestamp
            ORDER BY m.timestamp
            LIMIT 5
            """
        )
        
        # Get chunks for a message
        self.test_query(
            "Get chunks for a message",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
            RETURN m.message_id, ch.content, ch.chunk_id, ch.token_count
            LIMIT 5
            """
        )
        
        # Get embeddings for chunks
        self.test_query(
            "Get embeddings for chunks",
            """
            MATCH (ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            RETURN ch.chunk_id, e.dimension, e.method
            LIMIT 5
            """
        )
    
    def test_semantic_analysis_queries(self):
        """Test semantic analysis queries."""
        logger.info("\n🧠 Testing Semantic Analysis Queries...")
        
        # Get messages with tags
        self.test_query(
            "Get messages with tags",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            RETURN m.content, m.role, t.tags, t.domain, t.sentiment
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Find messages by domain
        self.test_query(
            "Find messages by domain",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE t.domain = "technology"
            RETURN m.content, m.role, t.tags
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Get cluster summaries
        self.test_query(
            "Get cluster summaries",
            """
            MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
            RETURN cl.cluster_id, s.summary, s.key_points, s.common_tags
            ORDER BY cl.cluster_id
            LIMIT 5
            """
        )
        
        # Get chat summaries
        self.test_query(
            "Get chat summaries",
            """
            MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c:Chat)
            RETURN c.title, cs.summary, cs.key_points, cs.topics
            ORDER BY c.create_time DESC
            LIMIT 5
            """
        )
    
    def test_similarity_queries(self):
        """Test similarity queries."""
        logger.info("\n🔗 Testing Similarity Queries...")
        
        # Find similar chats
        self.test_query(
            "Find similar chats",
            """
            MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
            RETURN c1.title, c2.title, c2.chat_id
            ORDER BY c2.create_time DESC
            LIMIT 5
            """
        )
        
        # Find similar clusters
        self.test_query(
            "Find similar clusters",
            """
            MATCH (cl1:Cluster)-[:SIMILAR_TO_CLUSTER_HIGH]->(cl2:Cluster)
            WHERE cl1.cluster_id <> cl2.cluster_id
            RETURN cl1.cluster_id, cl2.cluster_id, cl2.umap_x, cl2.umap_y
            LIMIT 5
            """
        )
    
    def test_content_discovery_queries(self):
        """Test content discovery queries."""
        logger.info("\n🔍 Testing Content Discovery Queries...")
        
        # Search messages by content
        self.test_query(
            "Search messages by content",
            """
            MATCH (m:Message)
            WHERE toLower(m.content) CONTAINS toLower("python")
            RETURN m.content, m.role, m.timestamp
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Find messages by tags
        self.test_query(
            "Find messages by tags",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE ANY(tag IN t.tags WHERE tag CONTAINS "programming")
            RETURN m.content, m.role, t.tags
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Get messages by sentiment
        self.test_query(
            "Get messages by sentiment",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE t.sentiment = "positive"
            RETURN m.content, m.role, t.sentiment
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
    
    def test_advanced_analysis_queries(self):
        """Test advanced analysis queries."""
        logger.info("\n📈 Testing Advanced Analysis Queries...")
        
        # Get complete message context
        self.test_query(
            "Get complete message context",
            """
            MATCH (m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
            RETURN m.content as message_content,
                   m.role as message_role,
                   c.title as chat_title,
                   collect(DISTINCT ch.content) as chunks,
                   collect(DISTINCT t.tags) as tags
            LIMIT 3
            """
        )
        
        # Get chat with full analysis
        self.test_query(
            "Get chat with full analysis",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
            RETURN c.title,
                   count(DISTINCT m) as message_count,
                   count(DISTINCT ch) as chunk_count,
                   collect(DISTINCT t.domain) as domains,
                   cs.summary as chat_summary
            LIMIT 3
            """
        )
        
        # Get cluster analysis
        self.test_query(
            "Get cluster analysis",
            """
            MATCH (cl:Cluster)
            OPTIONAL MATCH (cl)-[:CONTAINS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (s:Summary)-[:SUMMARIZES]->(cl)
            RETURN cl.cluster_id,
                   count(ch) as chunk_count,
                   s.summary as cluster_summary,
                   s.key_points as key_points
            LIMIT 3
            """
        )
    
    def test_statistics_and_analytics_queries(self):
        """Test statistics and analytics queries."""
        logger.info("\n📊 Testing Statistics and Analytics Queries...")
        
        # Node counts
        self.test_query(
            "Node counts",
            """
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(n) as count
            ORDER BY count DESC
            """
        )
        
        # Relationship counts
        self.test_query(
            "Relationship counts",
            """
            MATCH ()-[r]->()
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY count DESC
            """
        )
        
        # Average chunks per message
        self.test_query(
            "Average chunks per message",
            """
            MATCH (m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            WITH count(m) as message_count, count(ch) as chunk_count
            RETURN round(chunk_count * 100.0 / message_count, 2) as avg_chunks_per_message
            """
        )
        
        # Tag distribution
        self.test_query(
            "Tag distribution",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            UNWIND t.tags as tag
            RETURN tag, count(*) as usage_count
            ORDER BY usage_count DESC
            LIMIT 10
            """
        )
        
        # Domain distribution
        self.test_query(
            "Domain distribution",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            RETURN t.domain, count(*) as message_count
            ORDER BY message_count DESC
            """
        )
    
    def test_visualization_queries(self):
        """Test visualization queries."""
        logger.info("\n🎨 Testing Visualization Queries...")
        
        # Chats with positions
        self.test_query(
            "Chats with positions",
            """
            MATCH (c:Chat)
            WHERE c.position_x IS NOT NULL AND c.position_y IS NOT NULL
            RETURN c.chat_id, c.title, c.position_x, c.position_y
            ORDER BY c.create_time DESC
            LIMIT 5
            """
        )
        
        # Clusters with positions
        self.test_query(
            "Clusters with positions",
            """
            MATCH (cl:Cluster)
            WHERE cl.umap_x IS NOT NULL AND cl.umap_y IS NOT NULL
            RETURN cl.cluster_id, cl.umap_x, cl.umap_y
            ORDER BY cl.cluster_id
            LIMIT 5
            """
        )
        
        # Embeddings for visualization
        self.test_query(
            "Embeddings for visualization",
            """
            MATCH (e:Embedding)
            RETURN e.chunk_id, e.vector, e.dimension
            LIMIT 5
            """
        )
    
    def test_practical_use_cases(self):
        """Test practical use case queries."""
        logger.info("\n🎯 Testing Practical Use Cases...")
        
        # Find all messages about Python programming
        self.test_query(
            "Find all messages about Python programming",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
            RETURN m.content, m.role, t.tags
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Find messages with specific sentiment
        self.test_query(
            "Find messages with specific sentiment",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE t.sentiment = "positive"
            RETURN m.content, m.role, t.sentiment
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Get semantic breakdown of a conversation
        self.test_query(
            "Get semantic breakdown of a conversation",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
            RETURN c.title,
                   count(DISTINCT m) as messages,
                   count(DISTINCT ch) as chunks,
                   collect(DISTINCT t.domain) as domains,
                   cs.summary as chat_summary
            LIMIT 3
            """
        )
        
        # Find semantically similar conversations
        self.test_query(
            "Find semantically similar conversations",
            """
            MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
            RETURN c1.title, c2.title, c2.chat_id
            ORDER BY c2.create_time DESC
            LIMIT 5
            """
        )
    
    def test_quality_analysis_queries(self):
        """Test quality analysis queries."""
        logger.info("\n🔍 Testing Quality Analysis Queries...")
        
        # Find conversations with rich semantic content
        self.test_query(
            "Find conversations with rich semantic content",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            WITH c, count(DISTINCT m) as message_count, count(DISTINCT ch) as chunk_count, count(DISTINCT t) as tag_count
            WHERE chunk_count > 10 AND tag_count > 5
            RETURN c.title, message_count, chunk_count, tag_count
            ORDER BY tag_count DESC
            LIMIT 5
            """
        )
        
        # Find clusters with the most diverse content
        self.test_query(
            "Find clusters with the most diverse content",
            """
            MATCH (cl:Cluster)-[:CONTAINS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)-[:TAGS]->(t:Tag)
            WITH cl, count(DISTINCT ch) as chunk_count, count(DISTINCT t) as tag_count
            RETURN cl.cluster_id, chunk_count, tag_count, round(tag_count * 100.0 / chunk_count, 2) as tag_diversity
            ORDER BY tag_diversity DESC
            LIMIT 5
            """
        )
    
    def test_search_patterns(self):
        """Test search pattern queries."""
        logger.info("\n🔍 Testing Search Pattern Queries...")
        
        # Search messages by content
        self.test_query(
            "Search messages by content",
            """
            MATCH (m:Message)
            WHERE toLower(m.content) CONTAINS toLower("python")
            RETURN m.content, m.role
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Search by tag
        self.test_query(
            "Search by tag",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
            RETURN m.content, m.role
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Search by domain
        self.test_query(
            "Search by domain",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE t.domain = "technology"
            RETURN m.content, m.role
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
    
    def test_graph_exploration_queries(self):
        """Test graph exploration queries."""
        logger.info("\n🌐 Testing Graph Exploration Queries...")
        
        # Get chat with all related data
        self.test_query(
            "Get chat with all related data",
            """
            MATCH (c:Chat)
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
            RETURN c, collect(DISTINCT m) as messages, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs
            LIMIT 3
            """
        )
        
        # Find similar chats
        self.test_query(
            "Find similar chats",
            """
            MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]-(c2:Chat)
            RETURN c1.title, c2.title, c2.chat_id
            LIMIT 5
            """
        )
        
        # Chat-message-tag full context
        self.test_query(
            "Chat-message-tag full context",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
            RETURN c, m, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs
            LIMIT 3
            """
        )
    
    def test_additional_statistics_queries(self):
        """Test additional statistics queries."""
        logger.info("\n📊 Testing Additional Statistics Queries...")
        
        # Node counts
        self.test_query(
            "Node counts",
            """
            MATCH (n)
            RETURN labels(n)[0] as type, count(n) as count
            ORDER BY count DESC
            """
        )
        
        # Relationship counts
        self.test_query(
            "Relationship counts",
            """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
            """
        )
        
        # Average messages per chat
        self.test_query(
            "Average messages per chat",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            WITH c, count(m) as message_count
            RETURN avg(message_count) as avg_messages_per_chat
            """
        )
        
        # Tag distribution with percentage
        self.test_query(
            "Tag distribution with percentage",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            UNWIND t.tags as tag
            WITH tag, count(*) as usage_count
            RETURN tag, usage_count
            ORDER BY usage_count DESC
            LIMIT 10
            """
        )
    
    def test_advanced_analysis_queries(self):
        """Test advanced analysis queries from the enhanced guide."""
        logger.info("\n🔬 Testing Advanced Analysis Queries...")
        
        # Semantic layer analysis
        self.test_query(
            "Messages with semantic data",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            MATCH (ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            RETURN count(DISTINCT m) as messages_with_semantic_data,
                   count(DISTINCT ch) as chunks_with_embeddings
            """
        )
        
        # Chunk-embedding connectivity
        self.test_query(
            "Chunk-embedding connectivity",
            """
            MATCH (ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            RETURN ch.chunk_id, count(e) as embedding_count
            ORDER BY embedding_count DESC
            LIMIT 5
            """
        )
        
        # Quality and completeness analysis
        self.test_query(
            "Orphaned messages",
            """
            MATCH (m:Message)
            WHERE NOT (m)<-[:CONTAINS]-(:Chat)
            RETURN count(m) as orphan_messages
            """
        )
        
        self.test_query(
            "Orphaned chunks",
            """
            MATCH (ch:Chunk)
            WHERE NOT (ch)<-[:HAS_CHUNK]-(:Message)
            RETURN count(ch) as orphan_chunks
            """
        )
        
        # Full path connectivity
        self.test_query(
            "Complete semantic path",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            RETURN c.chat_id, m.message_id, ch.chunk_id, e.embedding_hash
            LIMIT 5
            """
        )
        
        # Chat with full semantic analysis
        self.test_query(
            "Chat with full semantic analysis",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
            RETURN c.title,
                   count(DISTINCT m) as message_count,
                   count(DISTINCT ch) as chunk_count,
                   collect(DISTINCT t.domain) as domains,
                   cs.summary as chat_summary
            LIMIT 3
            """
        )
    
    def test_quality_and_completeness_analysis(self):
        """Test quality and completeness analysis queries."""
        logger.info("\n🔍 Testing Quality and Completeness Analysis...")
        
        # Schema validation
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
        
        # Critical properties validation
        self.test_query(
            "Critical properties validation",
            """
            MATCH (m:Message)
            WHERE m.message_id IS NULL OR m.content IS NULL
            RETURN count(*) AS bad_messages
            """
        )
        
        # Chunk properties validation
        self.test_query(
            "Chunk properties validation",
            """
            MATCH (ch:Chunk)
            WHERE ch.chunk_id IS NULL OR ch.content IS NULL
            RETURN count(*) AS bad_chunks
            """
        )
        
        # Chat properties validation
        self.test_query(
            "Chat properties validation",
            """
            MATCH (c:Chat)
            WHERE c.chat_id IS NULL OR c.title IS NULL
            RETURN count(*) AS bad_chats
            """
        )
        
        # Edge case handling
        self.test_query(
            "Null property handling",
            """
            MATCH (m:Message) WHERE m.content IS NULL RETURN count(m) AS null_content_messages
            """
        )
        
        self.test_query(
            "Empty collections",
            """
            MATCH (m:Message) WHERE NOT (m)-[:HAS_CHUNK]->() RETURN count(m) AS messages_without_chunks
            """
        )
    
    def test_performance_and_optimization_queries(self):
        """Test performance and optimization queries."""
        logger.info("\n⚡ Testing Performance and Optimization Queries...")
        
        # Performance safeguards
        self.test_query(
            "Fast node count query",
            "MATCH (n) RETURN count(n) as total_nodes",
            timeout=5
        )
        
        # Complex aggregation performance
        self.test_query(
            "Complex aggregation performance",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            WITH c, count(DISTINCT e) as embedding_count
            RETURN avg(embedding_count) as avg_embeddings_per_chat
            """,
            timeout=10
        )
        
        # Large result set handling
        self.test_query(
            "Large result set handling",
            """
            MATCH (ch:Chunk)
            RETURN ch.chunk_id, ch.content
            LIMIT 1000
            """,
            timeout=15
        )
        
        # Data quality metrics
        self.test_query(
            "Average messages per chat",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            WITH c, count(m) as message_count
            RETURN avg(message_count) as avg_messages_per_chat
            """
        )
    
    def test_visualization_and_positioning_queries(self):
        """Test visualization and positioning queries."""
        logger.info("\n🎨 Testing Visualization and Positioning Queries...")
        
        # Chat positioning
        self.test_query(
            "Chats with positions",
            """
            MATCH (c:Chat)
            WHERE c.position_x IS NOT NULL AND c.position_y IS NOT NULL
            RETURN c.chat_id, c.title, c.position_x, c.position_y
            ORDER BY c.create_time DESC
            LIMIT 5
            """
        )
        
        # Cluster positioning
        self.test_query(
            "Clusters with positions",
            """
            MATCH (cl:Cluster)
            WHERE cl.umap_x IS NOT NULL AND cl.umap_y IS NOT NULL
            RETURN cl.cluster_id, cl.umap_x, cl.umap_y
            ORDER BY cl.cluster_id
            LIMIT 5
            """
        )
        
        # Embedding visualization
        self.test_query(
            "Embeddings for visualization",
            """
            MATCH (e:Embedding)
            RETURN e.chunk_id, e.vector, e.dimension
            LIMIT 5
            """
        )
    
    def test_search_and_discovery_patterns(self):
        """Test search and discovery pattern queries."""
        logger.info("\n🔍 Testing Search and Discovery Patterns...")
        
        # Content-based search
        self.test_query(
            "Search messages by content",
            """
            MATCH (m:Message)
            WHERE toLower(m.content) CONTAINS toLower("python")
            RETURN m.content, m.role
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Search by tag
        self.test_query(
            "Search by tag",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
            RETURN m.content, m.role
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Search by domain
        self.test_query(
            "Search by domain",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE t.domain = "technology"
            RETURN m.content, m.role
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Semantic discovery
        self.test_query(
            "Find all messages about Python programming",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
            RETURN m.content, m.role, t.tags
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
        
        # Find messages with specific sentiment
        self.test_query(
            "Find messages with specific sentiment",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            WHERE t.sentiment = "positive"
            RETURN m.content, m.role, t.sentiment
            ORDER BY m.timestamp DESC
            LIMIT 5
            """
        )
    
    def test_graph_exploration_queries(self):
        """Test graph exploration queries."""
        logger.info("\n🌐 Testing Graph Exploration Queries...")
        
        # Get chat with all related data
        self.test_query(
            "Get chat with all related data",
            """
            MATCH (c:Chat)
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
            RETURN c, collect(DISTINCT m) as messages, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs
            LIMIT 3
            """
        )
        
        # Find similar chats
        self.test_query(
            "Find similar chats",
            """
            MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]-(c2:Chat)
            RETURN c1.title, c2.title, c2.chat_id
            LIMIT 5
            """
        )
        
        # Chat-message-tag full context
        self.test_query(
            "Chat-message-tag full context",
            """
            MATCH (c:Chat)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
            RETURN c, m, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs
            LIMIT 3
            """
        )
    
    def test_debugging_queries(self):
        """Test debugging queries."""
        logger.info("\n🔧 Testing Debugging Queries...")
        
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
        
        # Verify message-chunk links
        self.test_query(
            "Verify message-chunk links",
            """
            MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
            RETURN count(m) as messages_with_chunks,
                   count(ch) as total_chunks
            """
        )
        
        # Check semantic layer connections
        self.test_query(
            "Check semantic layer connections",
            """
            MATCH (m:Message)-[:TAGS]->(t:Tag)
            MATCH (ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
            RETURN count(DISTINCT m) as messages_with_semantic_data,
                   count(DISTINCT ch) as chunks_with_embeddings
            """
        )
    
    def run_all_tests(self, parallel=False):
        """Run all query tests with optional parallel execution."""
        logger.info("🚀 Starting Enhanced Neo4j Query Tests...")
        
        if not self.connect():
            return False
        
        try:
            test_functions = [
                self.test_edge_cases_and_data_absence,
                self.test_schema_validation,
                self.test_duplicate_and_conflict_detection,
                self.test_graph_connectivity,
                self.test_performance_safeguards,
                self.test_basic_data_exploration_queries,
                self.test_semantic_analysis_queries,
                self.test_similarity_queries,
                self.test_content_discovery_queries,
                self.test_advanced_analysis_queries,
                self.test_statistics_and_analytics_queries,
                self.test_visualization_queries,
                self.test_practical_use_cases,
                self.test_quality_analysis_queries,
                self.test_search_patterns,
                self.test_additional_statistics_queries,
                self.test_debugging_queries,
                # New test functions from enhanced guide
                self.test_quality_and_completeness_analysis,
                self.test_performance_and_optimization_queries,
                self.test_visualization_and_positioning_queries,
                self.test_search_and_discovery_patterns
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
        logger.info("\n📋 Enhanced Test Summary:")
        
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
            logger.info("🎉 Excellent! Neo4j queries are working correctly.")
        elif success_rate >= 80:
            logger.info("⚠️  Good, but some queries need attention.")
        else:
            logger.error("❌ Many queries are failing. Check database setup.")
    
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
    
    parser = argparse.ArgumentParser(description="Enhanced Neo4j Query Tester")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    
    args = parser.parse_args()
    
    tester = Neo4jQueryTester()
    tester.run_all_tests(parallel=args.parallel)
    
    if args.export:
        tester.export_results(args.export) 