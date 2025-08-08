#!/usr/bin/env python3
"""
Comprehensive Database Query Test Script for ChatMind Hybrid Architecture
Tests both Neo4j (graph database) and Qdrant (vector database) queries,
including cross-database connections and semantic search functionality.
"""

import sys
import os
import json
import time
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HybridDatabaseTester:
    """Comprehensive tester for both Neo4j and Qdrant databases with cross-database connections."""
    
    def __init__(self):
        # Neo4j configuration
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "chatmind123")
        self.neo4j_driver = None
        
        # Qdrant configuration
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6335")
        self.qdrant_collection = os.getenv("QDRANT_COLLECTION", "chatmind_embeddings")
        self.qdrant_client = None
        
        # Test results
        self.test_results = []
        self.performance_metrics = {}
        
        # Sentence transformer for semantic search
        self.embedding_model = None
        
    def connect_databases(self):
        """Connect to both Neo4j and Qdrant databases."""
        logger.info("🔌 Connecting to databases...")
        
        # Connect to Neo4j
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.neo4j_uri, 
                auth=(self.neo4j_user, self.neo4j_password)
            )
            with self.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("✅ Connected to Neo4j database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False
        
        # Connect to Qdrant
        try:
            self.qdrant_client = QdrantClient(self.qdrant_url)
            # Test connection
            collections = self.qdrant_client.get_collections()
            logger.info("✅ Connected to Qdrant database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            return False
        
        # Initialize embedding model for semantic search
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Initialized embedding model for semantic search")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embedding model: {e}")
            return False
        
        return True
    
    def close_connections(self):
        """Close all database connections."""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.qdrant_client:
            self.qdrant_client.close()
    
    def test_query(self, name, query_func, timeout=30):
        """Test a single query function and log the result with performance tracking."""
        start_time = time.time()
        try:
            result = query_func()
            execution_time = time.time() - start_time
            
            # Log the result
            if isinstance(result, dict):
                result_count = result.get('count', 0)
                # Prefer informative keys if present
                if 'qdrant_present' in result:
                    logger.info(f"✅ {name}: qdrant_present={result['qdrant_present']} of neo4j_count={result.get('neo4j_count', 0)} ({execution_time:.3f}s)")
                elif 'intersection_count' in result and result_count == 0:
                    logger.info(f"✅ {name}: intersection_count={result['intersection_count']} ({execution_time:.3f}s)")
                else:
                    counts_summary = self._summarize_counts(result)
                    logger.info(f"✅ {name}: {counts_summary} ({execution_time:.3f}s)")
                if result.get('data') and len(result['data']) <= 3:
                    for i, item in enumerate(result['data'][:3]):
                        logger.info(f"   Result {i+1}: {item}")
                # Also wrap dict into a one-item list for downstream summary consistency if needed
                self.test_results.append({
                    "name": name,
                    "status": "PASS",
                    "result": result,
                    "execution_time": execution_time
                })
                self.performance_metrics[name] = execution_time
                return True
            elif isinstance(result, (list, tuple)):
                result_count = len(result)
                logger.info(f"✅ {name}: {result_count} results ({execution_time:.3f}s)")
                if result and len(result) <= 3:
                    for i, item in enumerate(result[:3]):
                        logger.info(f"   Result {i+1}: {item}")
            else:
                # Handle other types (strings, numbers, etc.)
                logger.info(f"✅ {name}: {result} ({execution_time:.3f}s)")
            
            self.test_results.append({
                "name": name,
                "status": "PASS",
                "result": result,
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
    
    def test_neo4j_basic_queries(self):
        """Test basic Neo4j queries."""
        logger.info("\n🗄️ Testing Neo4j Basic Queries...")
        
        # Test node counts
        self.test_query(
            "Neo4j - Node counts",
            lambda: self._get_neo4j_node_counts()
        )
        
        # Test relationship counts
        self.test_query(
            "Neo4j - Relationship counts",
            lambda: self._get_neo4j_relationship_counts()
        )
        
        # Test chat data
        self.test_query(
            "Neo4j - Chat data",
            lambda: self._get_neo4j_chat_data()
        )
        
        # Test message data
        self.test_query(
            "Neo4j - Message data",
            lambda: self._get_neo4j_message_data()
        )
        
        # Test chunk data
        self.test_query(
            "Neo4j - Chunk data",
            lambda: self._get_neo4j_chunk_data()
        )
    
    def test_qdrant_basic_queries(self):
        """Test basic Qdrant queries."""
        logger.info("\n🔍 Testing Qdrant Basic Queries...")
        
        # Test collection info
        self.test_query(
            "Qdrant - Collection info",
            lambda: self._get_qdrant_collection_info()
        )
        
        # Test point count
        self.test_query(
            "Qdrant - Point count",
            lambda: self._get_qdrant_point_count()
        )
        
        # Test sample points
        self.test_query(
            "Qdrant - Sample points",
            lambda: self._get_qdrant_sample_points()
        )
    
    def test_cross_database_connections(self):
        """Test cross-database connections and data consistency."""
        logger.info("\n🔗 Testing Cross-Database Connections...")
        
        # Test chunk ID consistency
        self.test_query(
            "Cross-DB - Chunk ID consistency",
            lambda: self._test_chunk_id_consistency()
        )
        
        # Test message ID consistency
        self.test_query(
            "Cross-DB - Message ID consistency",
            lambda: self._test_message_id_consistency()
        )
        
        # Test chat ID consistency
        self.test_query(
            "Cross-DB - Chat ID consistency",
            lambda: self._test_chat_id_consistency()
        )
        
        # Test embedding hash consistency
        self.test_query(
            "Cross-DB - Embedding hash consistency",
            lambda: self._test_embedding_hash_consistency()
        )
        
        # Test content verification between databases
        self.test_query(
            "Cross-DB - Content verification",
            lambda: self._test_content_verification()
        )
        
        # Test basic semantic search functionality
        self.test_query(
            "Cross-DB - Basic semantic search",
            lambda: self._test_basic_semantic_search()
        )
    
    def test_semantic_search_workflow(self):
        """Test semantic search workflow using Qdrant and Neo4j."""
        logger.info("\n🧠 Testing Semantic Search Workflow...")
        
        # Test semantic search in Qdrant
        self.test_query(
            "Semantic Search - Qdrant search",
            lambda: self._test_qdrant_semantic_search()
        )
        
        # Test cross-reference lookup
        self.test_query(
            "Semantic Search - Cross-reference lookup",
            lambda: self._test_cross_reference_lookup()
        )
        
        # Test full semantic search workflow
        self.test_query(
            "Semantic Search - Full workflow",
            lambda: self._test_full_semantic_search_workflow()
        )
    
    def test_hybrid_queries(self):
        """Test hybrid queries that combine both databases."""
        logger.info("\n🏗️ Testing Hybrid Queries...")
        
        # Test semantic search with graph context
        self.test_query(
            "Hybrid - Semantic search with graph context",
            lambda: self._test_semantic_search_with_graph_context()
        )
        
        # Test graph query with vector similarity
        self.test_query(
            "Hybrid - Graph query with vector similarity",
            lambda: self._test_graph_query_with_vector_similarity()
        )
        
        # Test content discovery workflow
        self.test_query(
            "Hybrid - Content discovery workflow",
            lambda: self._test_content_discovery_workflow()
        )
    
    def test_performance_metrics(self):
        """Test performance metrics for both databases."""
        logger.info("\n⚡ Testing Performance Metrics...")
        
        # Test Neo4j query performance
        self.test_query(
            "Performance - Neo4j query speed",
            lambda: self._test_neo4j_query_performance()
        )
        
        # Test Qdrant search performance
        self.test_query(
            "Performance - Qdrant search speed",
            lambda: self._test_qdrant_search_performance()
        )
        
        # Test cross-database lookup performance
        self.test_query(
            "Performance - Cross-database lookup speed",
            lambda: self._test_cross_database_lookup_performance()
        )
    
    def test_semantic_analysis_queries(self):
        """Test semantic analysis queries from the Neo4j guide."""
        logger.info("\n🏷️ Testing Semantic Analysis Queries...")
        
        # Test messages with tags
        self.test_query(
            "Semantic - Messages with tags",
            lambda: self._test_messages_with_tags()
        )
        
        # Test messages by domain
        self.test_query(
            "Semantic - Messages by domain",
            lambda: self._test_messages_by_domain()
        )
        
        # Test messages by sentiment
        self.test_query(
            "Semantic - Messages by sentiment",
            lambda: self._test_messages_by_sentiment()
        )
        
        # Test tag distribution
        self.test_query(
            "Semantic - Tag distribution",
            lambda: self._test_tag_distribution()
        )
        
        # Test domain distribution
        self.test_query(
            "Semantic - Domain distribution",
            lambda: self._test_domain_distribution()
        )
    
    def test_similarity_queries(self):
        """Test similarity queries from the Neo4j guide."""
        logger.info("\n🔗 Testing Similarity Queries...")
        
        # Test similar chats
        self.test_query(
            "Similarity - Similar chats",
            lambda: self._test_similar_chats()
        )
        
        # Test similar clusters
        self.test_query(
            "Similarity - Similar clusters",
            lambda: self._test_similar_clusters()
        )
        
        # Test chat similarity statistics
        self.test_query(
            "Similarity - Chat similarity stats",
            lambda: self._test_chat_similarity_stats()
        )
    
    def test_content_discovery_queries(self):
        """Test content discovery queries from the Neo4j guide."""
        logger.info("\n🔍 Testing Content Discovery Queries...")
        
        # Test search by content
        self.test_query(
            "Discovery - Search by content",
            lambda: self._test_search_by_content()
        )
        
        # Test search by tags
        self.test_query(
            "Discovery - Search by tags",
            lambda: self._test_search_by_tags()
        )
        
        # Test search by domain
        self.test_query(
            "Discovery - Search by domain",
            lambda: self._test_search_by_domain()
        )
        
        # Test complex content discovery
        self.test_query(
            "Discovery - Complex content discovery",
            lambda: self._test_complex_content_discovery()
        )
    
    def test_advanced_analysis_queries(self):
        """Test advanced analysis queries from the Neo4j guide."""
        logger.info("\n📊 Testing Advanced Analysis Queries...")
        
        # Test complete message context
        self.test_query(
            "Analysis - Complete message context",
            lambda: self._test_complete_message_context()
        )
        
        # Test chat with full analysis
        self.test_query(
            "Analysis - Chat with full analysis",
            lambda: self._test_chat_with_full_analysis()
        )
        
        # Test cluster analysis
        self.test_query(
            "Analysis - Cluster analysis",
            lambda: self._test_cluster_analysis()
        )
        
        # Test summary queries
        self.test_query(
            "Analysis - Summary queries",
            lambda: self._test_summary_queries()
        )
    
    def test_statistics_analytics_queries(self):
        """Test statistics and analytics queries from the Neo4j guide."""
        logger.info("\n📈 Testing Statistics & Analytics Queries...")
        
        # Test node counts by type
        self.test_query(
            "Stats - Node counts by type",
            lambda: self._test_node_counts_by_type()
        )
        
        # Test relationship counts by type
        self.test_query(
            "Stats - Relationship counts by type",
            lambda: self._test_relationship_counts_by_type()
        )
        
        # Test average chunks per message
        self.test_query(
            "Stats - Average chunks per message",
            lambda: self._test_avg_chunks_per_message()
        )
        
        # Test tag usage statistics
        self.test_query(
            "Stats - Tag usage statistics",
            lambda: self._test_tag_usage_statistics()
        )
        
        # Test domain distribution stats
        self.test_query(
            "Stats - Domain distribution stats",
            lambda: self._test_domain_distribution_stats()
        )
    
    def test_graph_exploration_queries(self):
        """Test graph exploration queries from the Neo4j guide."""
        logger.info("\n🌐 Testing Graph Exploration Queries...")
        
        # Test chat-message connectivity
        self.test_query(
            "Graph - Chat-message connectivity",
            lambda: self._test_chat_message_connectivity()
        )
        
        # Test message-chunk connectivity
        self.test_query(
            "Graph - Message-chunk connectivity",
            lambda: self._test_message_chunk_connectivity()
        )
        
        # Test message-tag connectivity
        self.test_query(
            "Graph - Message-tag connectivity",
            lambda: self._test_message_tag_connectivity()
        )
        
        # Test cluster-chunk connectivity
        self.test_query(
            "Graph - Cluster-chunk connectivity",
            lambda: self._test_cluster_chunk_connectivity()
        )
        
        # Test complete semantic path
        self.test_query(
            "Graph - Complete semantic path",
            lambda: self._test_complete_semantic_path()
        )
    
    def test_quality_analysis_queries(self):
        """Test quality analysis queries from the Neo4j guide."""
        logger.info("\n🔍 Testing Quality Analysis Queries...")
        
        # Test orphaned messages
        self.test_query(
            "Quality - Orphaned messages",
            lambda: self._test_orphaned_messages()
        )
        
        # Test orphaned chunks
        self.test_query(
            "Quality - Orphaned chunks",
            lambda: self._test_orphaned_chunks()
        )
        
        # Test duplicate detection
        self.test_query(
            "Quality - Duplicate detection",
            lambda: self._test_duplicate_detection()
        )
        
        # Test data completeness
        self.test_query(
            "Quality - Data completeness",
            lambda: self._test_data_completeness()
        )
        
        # Test rich semantic content
        self.test_query(
            "Quality - Rich semantic content",
            lambda: self._test_rich_semantic_content()
        )
    
    def test_visualization_queries(self):
        """Test visualization and positioning queries from the Neo4j guide."""
        logger.info("\n🎨 Testing Visualization Queries...")
        
        # Test chats with positions
        self.test_query(
            "Viz - Chats with positions",
            lambda: self._test_chats_with_positions()
        )
        
        # Test clusters with positions
        self.test_query(
            "Viz - Clusters with positions",
            lambda: self._test_clusters_with_positions()
        )
        
        # Test embeddings for visualization
        self.test_query(
            "Viz - Embeddings for visualization",
            lambda: self._test_embeddings_for_visualization()
        )
        
        # Test graph overview data
        self.test_query(
            "Viz - Graph overview data",
            lambda: self._test_graph_overview_data()
        )
    
    def test_api_readiness_queries(self):
        """Test queries that validate API readiness and data integrity."""
        logger.info("\n🔧 Testing API Readiness Queries...")
        
        # Test ID coverage and missing foreign keys
        self.test_query(
            "API - ID coverage report",
            lambda: self._test_id_coverage_report()
        )
        
        # Test multi-hop semantic context
        self.test_query(
            "API - Multi-hop semantic context",
            lambda: self._test_multi_hop_semantic_context()
        )
        
        # Test embedding drift detection
        self.test_query(
            "API - Embedding drift test",
            lambda: self._test_embedding_drift()
        )
        
        # Test combined endpoint shape
        self.test_query(
            "API - Combined endpoint shape",
            lambda: self._test_combined_endpoint_shape()
        )
        
        # Test fresh data embedding
        self.test_query(
            "API - Fresh data embedding test",
            lambda: self._test_fresh_data_embedding()
        )
        
        # Test Neo4j to Qdrant sync drift
        self.test_query(
            "API - Neo4j to Qdrant sync drift",
            lambda: self._test_neo4j_qdrant_sync_drift()
        )
    
    def test_schema_snapshot_queries(self):
        """Test queries that generate schema snapshots for API documentation."""
        logger.info("\n📋 Testing Schema Snapshot Queries...")
        
        # Test semantic search response schema
        self.test_query(
            "Schema - Semantic search response",
            lambda: self._test_semantic_search_response_schema()
        )
        
        # Test graph exploration response schema
        self.test_query(
            "Schema - Graph exploration response",
            lambda: self._test_graph_exploration_response_schema()
        )
        
        # Test content discovery response schema
        self.test_query(
            "Schema - Content discovery response",
            lambda: self._test_content_discovery_response_schema()
        )
    
    def test_timestamp_validation_queries(self):
        """Test timestamp validation and functionality across both databases."""
        logger.info("\n⏰ Testing Timestamp Validation Queries...")
        
        # Test Neo4j timestamp formats and ranges
        self.test_query(
            "Timestamps - Neo4j timestamp formats",
            lambda: self._test_neo4j_timestamp_formats()
        )
        
        # Test Qdrant timestamp payloads
        self.test_query(
            "Timestamps - Qdrant timestamp payloads",
            lambda: self._test_qdrant_timestamp_payloads()
        )
        
        # Test timestamp consistency between databases
        self.test_query(
            "Timestamps - Cross-database consistency",
            lambda: self._test_timestamp_cross_database_consistency()
        )
        
        # Test timestamp-based queries
        self.test_query(
            "Timestamps - Time-based queries",
            lambda: self._test_timestamp_based_queries()
        )
        
        # Test timestamp ranges and ordering
        self.test_query(
            "Timestamps - Range and ordering",
            lambda: self._test_timestamp_ranges_and_ordering()
        )
        
        # Test timestamp data quality
        self.test_query(
            "Timestamps - Data quality validation",
            lambda: self._test_timestamp_data_quality()
        )
    
    # Neo4j Query Methods
    def _get_neo4j_node_counts(self):
        """Get node counts from Neo4j."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as node_type, count(n) as count
                ORDER BY count DESC
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _get_neo4j_relationship_counts(self):
        """Get relationship counts from Neo4j."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _get_neo4j_chat_data(self):
        """Get sample chat data from Neo4j."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                RETURN c.chat_id, c.title, c.create_time
                ORDER BY c.create_time DESC
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _get_neo4j_message_data(self):
        """Get sample message data from Neo4j."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                RETURN m.message_id, m.role, substring(m.content, 0, 100) as content_preview
                ORDER BY m.timestamp DESC
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _get_neo4j_chunk_data(self):
        """Get sample chunk data from Neo4j."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (ch:Chunk)
                RETURN ch.chunk_id, substring(ch.content, 0, 100) as content_preview, ch.token_count
                ORDER BY ch.token_count DESC
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    # Qdrant Query Methods
    def _get_qdrant_collection_info(self):
        """Get collection information from Qdrant."""
        collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
        return {
            "collection_name": self.qdrant_collection,
            "vector_size": collection_info.config.params.vectors.size,
            "distance": collection_info.config.params.vectors.distance,
            "points_count": collection_info.points_count
        }
    
    def _get_qdrant_point_count(self):
        """Get point count from Qdrant."""
        collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
        return {"count": collection_info.points_count}
    
    def _get_qdrant_sample_points(self):
        """Get sample points from Qdrant."""
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=5,
            with_payload=True,
            with_vectors=False
        )[0]
        
        # Debug: Log the first point's payload structure
        if points:
            logger.info(f"Debug - Sample point payload keys: {list(points[0].payload.keys())}")
            logger.info(f"Debug - Sample point payload: {points[0].payload}")
        
        data = []
        for point in points:
            data.append({
                "id": point.id,
                "payload": {
                    "chunk_id": point.payload.get("chunk_id"),
                    "message_id": point.payload.get("message_id"),
                    "chat_id": point.payload.get("chat_id"),
                    "content_preview": point.payload.get("content", "")[:100]
                }
            })
        
        return {"count": len(data), "data": data}
    
    # Cross-Database Connection Methods
    def _test_chunk_id_consistency(self):
        """Test chunk ID consistency between Neo4j and Qdrant."""
        # Get a deterministic sample of chunk IDs from Neo4j then verify each in Qdrant
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (ch:Chunk)
                RETURN ch.chunk_id AS chunk_id
                ORDER BY ch.chunk_id
                LIMIT 20
            """)
            neo4j_chunk_ids = [record["chunk_id"] for record in neo4j_result]

        if not neo4j_chunk_ids:
            return {"neo4j_count": 0, "qdrant_present": 0, "consistent": False}

        qdrant_present = 0
        for cid in neo4j_chunk_ids:
            points = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter={"must": [{"key": "chunk_id", "match": {"value": cid}}]},
                limit=1,
                with_payload=False
            )[0]
            if points:
                qdrant_present += 1

        return {
            "neo4j_count": len(neo4j_chunk_ids),
            "qdrant_present": qdrant_present,
            "intersection_count": qdrant_present,
            "consistent": qdrant_present > 0 and qdrant_present == len(neo4j_chunk_ids)
        }
    
    def _test_message_id_consistency(self):
        """Test message ID consistency between Neo4j and Qdrant."""
        # Get a deterministic sample of message IDs from Neo4j then verify in Qdrant
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (m:Message)
                RETURN m.message_id AS message_id
                ORDER BY m.message_id
                LIMIT 20
            """)
            neo4j_message_ids = [record["message_id"] for record in neo4j_result]

        if not neo4j_message_ids:
            return {"neo4j_count": 0, "qdrant_present": 0, "consistent": False}

        qdrant_present = 0
        for mid in neo4j_message_ids:
            points = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter={"must": [{"key": "message_id", "match": {"value": mid}}]},
                limit=1,
                with_payload=False
            )[0]
            if points:
                qdrant_present += 1

        return {
            "neo4j_count": len(neo4j_message_ids),
            "qdrant_present": qdrant_present,
            "intersection_count": qdrant_present,
            "consistent": qdrant_present > 0 and qdrant_present == len(neo4j_message_ids)
        }
    
    def _test_chat_id_consistency(self):
        """Test chat ID consistency between Neo4j and Qdrant."""
        # Get a deterministic sample of chat IDs from Neo4j then verify in Qdrant
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (c:Chat)
                RETURN c.chat_id AS chat_id
                ORDER BY c.chat_id
                LIMIT 20
            """)
            neo4j_chat_ids = [record["chat_id"] for record in neo4j_result]

        if not neo4j_chat_ids:
            return {"neo4j_count": 0, "qdrant_present": 0, "consistent": False}

        qdrant_present = 0
        for cid in neo4j_chat_ids:
            points = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter={"must": [{"key": "chat_id", "match": {"value": cid}}]},
                limit=1,
                with_payload=False
            )[0]
            if points:
                qdrant_present += 1

        return {
            "neo4j_count": len(neo4j_chat_ids),
            "qdrant_present": qdrant_present,
            "intersection_count": qdrant_present,
            "consistent": qdrant_present > 0 and qdrant_present == len(neo4j_chat_ids)
        }
    
    def _test_embedding_hash_consistency(self):
        """Test embedding hash consistency between Neo4j and Qdrant."""
        # Get embedding hashes from Neo4j - check if Embedding nodes exist
        with self.neo4j_driver.session() as session:
            # First check if Embedding nodes exist
            check_result = session.run("""
                MATCH (e:Embedding)
                RETURN count(e) as embedding_count
            """)
            embedding_count = check_result.single()["embedding_count"]
            
            if embedding_count == 0:
                return {
                    "neo4j_count": 0,
                    "qdrant_count": 0,
                    "intersection_count": 0,
                    "consistent": True,
                    "note": "No Embedding nodes in Neo4j (expected in hybrid architecture)"
                }
            
            neo4j_result = session.run("""
                MATCH (e:Embedding)
                RETURN e.embedding_hash
                LIMIT 10
            """)
            neo4j_embedding_hashes = [record["embedding_hash"] for record in neo4j_result]
        
        # Get embedding hashes from Qdrant
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=10,
            with_payload=True,
            with_vectors=False
        )[0]
        
        qdrant_embedding_hashes = []
        for point in points:
            embedding_hash = point.payload.get("embedding_hash")
            if embedding_hash:
                qdrant_embedding_hashes.append(embedding_hash)
        
        # Check consistency
        neo4j_set = set(neo4j_embedding_hashes)
        qdrant_set = set(qdrant_embedding_hashes)
        
        return {
            "neo4j_count": len(neo4j_set),
            "qdrant_count": len(qdrant_set),
            "intersection_count": len(neo4j_set.intersection(qdrant_set)),
            "consistent": len(neo4j_set.intersection(qdrant_set)) > 0
        }
    
    # Semantic Search Methods
    def _test_qdrant_semantic_search(self):
        """Test semantic search in Qdrant."""
        # Create a test query
        test_query = "python programming"
        query_vector = self.embedding_model.encode(test_query).tolist()
        
        # Search in Qdrant
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            limit=5,
            with_payload=True,
            with_vectors=False
        )
        
        data = []
        for result in search_result:
            data.append({
                "score": result.score,
                "chunk_id": result.payload.get("chunk_id"),
                "content": result.payload.get("content", "")[:100],
                "tags": result.payload.get("tags", [])
            })
        
        return {"count": len(data), "data": data}
    
    def _test_cross_reference_lookup(self):
        """Test cross-reference lookup from Qdrant to Neo4j."""
        # Get a sample point from Qdrant
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=1,
            with_payload=True,
            with_vectors=False
        )[0]
        
        if not points:
            return {"error": "No points found in Qdrant"}
        
        point = points[0]
        chunk_id = point.payload.get("chunk_id")
        
        # Look up the chunk in Neo4j
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (ch:Chunk {chunk_id: $chunk_id})
                OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)
                OPTIONAL MATCH (m)<-[:CONTAINS]-(c:Chat)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                RETURN ch.content as chunk_content,
                       m.content as message_content,
                       c.title as chat_title,
                       collect(DISTINCT t.tags) as tags
            """, chunk_id=chunk_id)
            
            data = [dict(record) for record in result]
        
        return {"count": len(data), "data": data}
    
    def _test_full_semantic_search_workflow(self):
        """Test full semantic search workflow."""
        # 1. Semantic search in Qdrant
        test_query = "machine learning"
        query_vector = self.embedding_model.encode(test_query).tolist()
        
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        # 2. Cross-reference to Neo4j for rich context
        results = []
        for result in search_result:
            chunk_id = result.payload.get("chunk_id")
            
            # Get rich context from Neo4j
            with self.neo4j_driver.session() as session:
                neo4j_result = session.run("""
                    MATCH (ch:Chunk {chunk_id: $chunk_id})
                    OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)
                    OPTIONAL MATCH (m)<-[:CONTAINS]-(c:Chat)
                    OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                    RETURN ch.content as chunk_content,
                           m.content as message_content,
                           c.title as chat_title,
                           collect(DISTINCT t.tags) as tags,
                           $similarity_score as similarity_score
                """, chunk_id=chunk_id, similarity_score=result.score)
                
                neo4j_data = [dict(record) for record in neo4j_result]
                if neo4j_data:
                    results.extend(neo4j_data)
        
        return {"count": len(results), "data": results}
    
    # Hybrid Query Methods
    def _test_semantic_search_with_graph_context(self):
        """Test semantic search with graph context."""
        # 1. Find semantically similar content in Qdrant
        test_query = "artificial intelligence"
        query_vector = self.embedding_model.encode(test_query).tolist()
        
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            limit=5,
            with_payload=True,
            with_vectors=False
        )
        
        # 2. Get graph context for each result
        results = []
        for result in search_result:
            chunk_id = result.payload.get("chunk_id")
            
            # Get graph context
            with self.neo4j_driver.session() as session:
                graph_result = session.run("""
                    MATCH (ch:Chunk {chunk_id: $chunk_id})
                    OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)
                    OPTIONAL MATCH (m)<-[:CONTAINS]-(c:Chat)
                    OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                    OPTIONAL MATCH (cl:Cluster)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch)
                    RETURN ch.content as chunk_content,
                           m.content as message_content,
                           c.title as chat_title,
                           cl.cluster_id as cluster_id,
                           collect(DISTINCT t.tags) as tags,
                           $similarity_score as similarity_score
                """, chunk_id=chunk_id, similarity_score=result.score)
                
                graph_data = [dict(record) for record in graph_result]
                results.extend(graph_data)
        
        return {"count": len(results), "data": results}
    
    def _test_graph_query_with_vector_similarity(self):
        """Test graph query with vector similarity."""
        # 1. Find a cluster in Neo4j - check what properties are available
        with self.neo4j_driver.session() as session:
            # First check what properties clusters have
            check_result = session.run("""
                MATCH (cl:Cluster)
                RETURN keys(cl) as properties
                LIMIT 1
            """)
            properties = check_result.single()
            if properties:
                properties = properties["properties"]
                logger.info(f"Cluster properties: {properties}")
            
            # Use available properties for ordering
            if properties and "size" in properties:
                cluster_result = session.run("""
                    MATCH (cl:Cluster)
                    RETURN cl.cluster_id, cl.size
                    ORDER BY cl.size DESC
                    LIMIT 1
                """)
            else:
                # Fallback to just getting any cluster
                cluster_result = session.run("""
                    MATCH (cl:Cluster)
                    RETURN cl.cluster_id
                    LIMIT 1
                """)
            
            cluster_data = [dict(record) for record in cluster_result]
        
        if not cluster_data:
            return {"error": "No clusters found"}
        
        cluster_id = cluster_data[0].get("cluster_id")
        if not cluster_id:
            return {"error": "No cluster_id found in cluster data"}
        
        # 2. Get chunks in this cluster
        with self.neo4j_driver.session() as session:
            chunks_result = session.run("""
                MATCH (cl:Cluster {cluster_id: $cluster_id})-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch:Chunk)
                RETURN ch.chunk_id, ch.content
                LIMIT 5
            """, cluster_id=cluster_id)
            chunks_data = [dict(record) for record in chunks_result]
        
        if not chunks_data:
            return {"error": f"No chunks found for cluster {cluster_id}"}
        
        # 3. Find similar content in Qdrant
        results = []
        for chunk in chunks_data:
            chunk_content = chunk["content"]
            chunk_vector = self.embedding_model.encode(chunk_content).tolist()
            
            # Search for similar content
            similar_result = self.qdrant_client.search(
                collection_name=self.qdrant_collection,
                query_vector=chunk_vector,
                limit=3,
                with_payload=True,
                with_vectors=False
            )
            
            for similar in similar_result:
                results.append({
                    "original_chunk": chunk["content"][:100],
                    "similar_chunk": similar.payload.get("content", "")[:100],
                    "similarity_score": similar.score,
                    "cluster_id": cluster_id
                })
        
        return {"count": len(results), "data": results}
    
    def _test_content_discovery_workflow(self):
        """Test content discovery workflow."""
        # 1. Start with a semantic search
        test_query = "data science"
        query_vector = self.embedding_model.encode(test_query).tolist()
        
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        # 2. Get graph relationships for discovered content
        results = []
        for result in search_result:
            chunk_id = result.payload.get("chunk_id")
            
            # Get related content through graph
            with self.neo4j_driver.session() as session:
                related_result = session.run("""
                    MATCH (ch:Chunk {chunk_id: $chunk_id})
                    OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)
                    OPTIONAL MATCH (m)<-[:CONTAINS]-(c:Chat)
                    OPTIONAL MATCH (c)-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
                    OPTIONAL MATCH (c2)-[:CONTAINS]->(m2:Message)-[:HAS_CHUNK]->(ch2:Chunk)
                    RETURN ch.content as original_chunk,
                           c.title as original_chat,
                           c2.title as related_chat,
                           ch2.content as related_chunk,
                           $similarity_score as similarity_score
                    LIMIT 3
                """, chunk_id=chunk_id, similarity_score=result.score)
                
                related_data = [dict(record) for record in related_result]
                results.extend(related_data)
        
        return {"count": len(results), "data": results}
    
    # Performance Test Methods
    def _test_neo4j_query_performance(self):
        """Test Neo4j query performance."""
        start_time = time.time()
        
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)
                RETURN count(DISTINCT c) as chat_count,
                       count(DISTINCT m) as message_count,
                       count(DISTINCT ch) as chunk_count
            """)
            data = [dict(record) for record in result]
        
        execution_time = time.time() - start_time
        
        return {
            "execution_time": execution_time,
            "data": data
        }
    
    def _test_qdrant_search_performance(self):
        """Test Qdrant search performance."""
        start_time = time.time()
        
        test_query = "test query"
        query_vector = self.embedding_model.encode(test_query).tolist()
        
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            limit=10,
            with_payload=True,
            with_vectors=False
        )
        
        execution_time = time.time() - start_time
        
        return {
            "execution_time": execution_time,
            "result_count": len(search_result)
        }
    
    def _test_cross_database_lookup_performance(self):
        """Test cross-database lookup performance."""
        start_time = time.time()
        
        # Get a sample point from Qdrant
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=1,
            with_payload=True,
            with_vectors=False
        )[0]
        
        if points:
            chunk_id = points[0].payload.get("chunk_id")
            
            # Look up in Neo4j
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (ch:Chunk {chunk_id: $chunk_id})
                    RETURN ch.content
                """, chunk_id=chunk_id)
                data = [dict(record) for record in result]
        
        execution_time = time.time() - start_time
        
        return {
            "execution_time": execution_time,
            "data": data if 'data' in locals() else []
        }
    
    # Semantic Analysis Query Methods
    def _test_messages_with_tags(self):
        """Test messages with semantic tags."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                RETURN m.content, m.role, t.tags, t.domain, t.sentiment
                ORDER BY m.timestamp DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_messages_by_domain(self):
        """Test messages by domain classification."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                WHERE t.domain = "technology"
                RETURN m.content, m.role, t.domain
                ORDER BY m.timestamp DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_messages_by_sentiment(self):
        """Test messages by sentiment classification."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                WHERE t.sentiment = "positive"
                RETURN m.content, m.role, t.sentiment
                ORDER BY m.timestamp DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_tag_distribution(self):
        """Test tag distribution statistics."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                UNWIND t.tags as tag
                RETURN tag, count(*) as usage_count
                ORDER BY usage_count DESC
                LIMIT 20
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:5]}
    
    def _test_domain_distribution(self):
        """Test domain distribution statistics."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                RETURN t.domain, count(*) as message_count
                ORDER BY message_count DESC
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    # Similarity Query Methods
    def _test_similar_chats(self):
        """Test similar chats query."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
                WHERE c1.chat_id <> c2.chat_id
                RETURN c1.title as chat1_title, c2.title as chat2_title
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_similar_clusters(self):
        """Test similar clusters query."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl1:Cluster)-[:SIMILAR_TO_CLUSTER_HIGH]->(cl2:Cluster)
                WHERE cl1.cluster_id <> cl2.cluster_id
                RETURN cl1.cluster_id, cl2.cluster_id
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_chat_similarity_stats(self):
        """Test chat similarity statistics."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)-[:SIMILAR_TO_CHAT_HIGH]->(other:Chat)
                RETURN c.chat_id, count(other) as similar_count
                ORDER BY similar_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    # Content Discovery Query Methods
    def _test_search_by_content(self):
        """Test search by content."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                WHERE toLower(m.content) CONTAINS toLower("python")
                RETURN m.content, m.role, m.timestamp
                ORDER BY m.timestamp DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_search_by_tags(self):
        """Test search by tags."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
                RETURN m.content, m.role, t.tags
                ORDER BY m.timestamp DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_search_by_domain(self):
        """Test search by domain."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                WHERE t.domain = "technology"
                RETURN m.content, m.role, t.domain
                ORDER BY m.timestamp DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_complex_content_discovery(self):
        """Test complex content discovery."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                WITH c, count(DISTINCT m) as message_count, 
                     count(DISTINCT ch) as chunk_count, 
                     count(DISTINCT t) as tag_count
                WHERE chunk_count > 5 AND tag_count > 2
                RETURN c.title, message_count, chunk_count, tag_count
                ORDER BY tag_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    # Advanced Analysis Query Methods
    def _test_complete_message_context(self):
        """Test complete message context."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
                RETURN m.content as message_content,
                       m.role as message_role,
                       c.title as chat_title,
                       count(DISTINCT ch) as chunk_count,
                       count(DISTINCT t) as tag_count
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_chat_with_full_analysis(self):
        """Test chat with full analysis."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
                RETURN c.title,
                       count(DISTINCT m) as message_count,
                       count(DISTINCT ch) as chunk_count,
                       collect(DISTINCT t.domain) as domains,
                       cs.summary as chat_summary
                LIMIT 3
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_cluster_analysis(self):
        """Test cluster analysis."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster)
                OPTIONAL MATCH (cl)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (s:Summary)-[:SUMMARIZES]->(cl)
                RETURN cl.cluster_id,
                       count(ch) as chunk_count,
                       s.summary as cluster_summary
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_summary_queries(self):
        """Test summary queries."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
                RETURN cl.cluster_id, s.summary, s.key_points, s.common_tags
                ORDER BY cl.cluster_id
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    # Statistics & Analytics Query Methods
    def _test_node_counts_by_type(self):
        """Test node counts by type."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as node_type, count(n) as count
                ORDER BY count DESC
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_relationship_counts_by_type(self):
        """Test relationship counts by type."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_avg_chunks_per_message(self):
        """Test average chunks per message."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                WITH count(m) as message_count, count(ch) as chunk_count
                RETURN round(chunk_count * 100.0 / message_count, 2) as avg_chunks_per_message
            """)
            data = result.single()
            return {"avg_chunks_per_message": data["avg_chunks_per_message"] if data else 0}
    
    def _test_tag_usage_statistics(self):
        """Test tag usage statistics."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                UNWIND t.tags as tag
                RETURN tag, count(*) as usage_count
                ORDER BY usage_count DESC
                LIMIT 20
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:5]}
    
    def _test_domain_distribution_stats(self):
        """Test domain distribution statistics."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                RETURN t.domain, count(*) as message_count
                ORDER BY message_count DESC
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    # Graph Exploration Query Methods
    def _test_chat_message_connectivity(self):
        """Test chat-message connectivity."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)
                RETURN c.chat_id, count(m) as message_count
                ORDER BY message_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_message_chunk_connectivity(self):
        """Test message-chunk connectivity."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
                RETURN m.message_id, count(ch) as chunk_count
                ORDER BY chunk_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_message_tag_connectivity(self):
        """Test message-tag connectivity."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                RETURN m.message_id, count(t) as tag_count
                ORDER BY tag_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_cluster_chunk_connectivity(self):
        """Test cluster-chunk connectivity."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch:Chunk)
                RETURN cl.cluster_id, count(ch) as chunk_count
                ORDER BY chunk_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_complete_semantic_path(self):
        """Test complete semantic path from chat to embedding."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
                RETURN c.chat_id, m.message_id, ch.chunk_id, e.embedding_hash
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    # Quality Analysis Query Methods
    def _test_orphaned_messages(self):
        """Test for orphaned messages (no chat parent)."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                WHERE NOT (m)<-[:CONTAINS]-(:Chat)
                RETURN count(m) as orphan_messages
            """)
            data = result.single()
            return {"orphan_messages": data["orphan_messages"] if data else 0}
    
    def _test_orphaned_chunks(self):
        """Test for orphaned chunks (no message parent)."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (ch:Chunk)
                WHERE NOT (ch)<-[:HAS_CHUNK]-(:Message)
                RETURN count(ch) as orphan_chunks
            """)
            data = result.single()
            return {"orphan_chunks": data["orphan_chunks"] if data else 0}
    
    def _test_duplicate_detection(self):
        """Test for duplicate messages."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                WITH m.message_id AS mid, count(*) AS c
                WHERE c > 1
                RETURN mid, c
                ORDER BY c DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_data_completeness(self):
        """Test data completeness metrics."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (m:Message)
                WHERE m.content IS NULL OR m.message_id IS NULL
                RETURN count(*) AS incomplete_messages
            """)
            data = result.single()
            return {"incomplete_messages": data["incomplete_messages"] if data else 0}
    
    def _test_rich_semantic_content(self):
        """Test for conversations with rich semantic content."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                WITH c, count(DISTINCT m) as message_count, count(DISTINCT ch) as chunk_count, count(DISTINCT t) as tag_count
                WHERE chunk_count > 10 AND tag_count > 5
                RETURN c.title, message_count, chunk_count, tag_count
                ORDER BY tag_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    # Visualization Query Methods
    def _test_chats_with_positions(self):
        """Test chats with positioning data."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                WHERE c.position_x IS NOT NULL AND c.position_y IS NOT NULL
                RETURN c.chat_id, c.title, c.position_x, c.position_y
                ORDER BY c.create_time DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_clusters_with_positions(self):
        """Test clusters with positioning data."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster)
                WHERE cl.umap_x IS NOT NULL AND cl.umap_y IS NOT NULL
                RETURN cl.cluster_id, cl.umap_x, cl.umap_y
                ORDER BY cl.cluster_id
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data}
    
    def _test_embeddings_for_visualization(self):
        """Test embeddings for visualization."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (e:Embedding)
                RETURN e.chunk_id, e.vector, e.dimension
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_graph_overview_data(self):
        """Test graph overview data."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (c:Chat)
                OPTIONAL MATCH (cl:Cluster)
                OPTIONAL MATCH (e:Embedding)
                RETURN count(c) as chat_count, count(cl) as cluster_count, count(e) as embedding_count
            """)
            data = result.single()
            return {"chat_count": data["chat_count"] if data else 0,
                    "cluster_count": data["cluster_count"] if data else 0,
                    "embedding_count": data["embedding_count"] if data else 0}
    
    # API Readiness Test Methods
    def _test_id_coverage_report(self):
        """Test for missing IDs and foreign keys that could break APIs."""
        with self.neo4j_driver.session() as session:
            # Check for messages without message_id
            null_message_id_result = session.run("""
                MATCH (m:Message) 
                WHERE m.message_id IS NULL 
                RETURN count(m) as null_message_ids
            """)
            null_message_ids = null_message_id_result.single()["null_message_ids"]
            
            # Check for chunks without chunk_id
            null_chunk_id_result = session.run("""
                MATCH (ch:Chunk) 
                WHERE ch.chunk_id IS NULL 
                RETURN count(ch) as null_chunk_ids
            """)
            null_chunk_ids = null_chunk_id_result.single()["null_chunk_ids"]
            
            # Check for chats without chat_id
            null_chat_id_result = session.run("""
                MATCH (c:Chat) 
                WHERE c.chat_id IS NULL 
                RETURN count(c) as null_chat_ids
            """)
            null_chat_ids = null_chat_id_result.single()["null_chat_ids"]
            
            # Check for orphaned chunks (chunks without message)
            orphaned_chunks_result = session.run("""
                MATCH (ch:Chunk)
                WHERE NOT (ch)<-[:HAS_CHUNK]-(:Message)
                RETURN count(ch) as orphaned_chunks
            """)
            orphaned_chunks = orphaned_chunks_result.single()["orphaned_chunks"]
            
            return {
                "null_message_ids": null_message_ids,
                "null_chunk_ids": null_chunk_ids,
                "null_chat_ids": null_chat_ids,
                "orphaned_chunks": orphaned_chunks,
                "total_issues": null_message_ids + null_chunk_ids + null_chat_ids + orphaned_chunks,
                "api_ready": (null_message_ids + null_chunk_ids + null_chat_ids + orphaned_chunks) == 0
            }
    
    def _test_multi_hop_semantic_context(self):
        """Test multi-hop semantic exploration (related chunks in neighboring chats)."""
        with self.neo4j_driver.session() as session:
            # Find a chunk to use as starting point
            start_chunk_result = session.run("""
                MATCH (ch:Chunk)
                RETURN ch.chunk_id, ch.content
                LIMIT 1
            """)
            start_chunk = start_chunk_result.single()
            
            if not start_chunk:
                return {"error": "No chunks found for multi-hop test"}
            
            chunk_id = start_chunk["ch.chunk_id"]
            
            # Multi-hop query: chunk -> cluster -> similar cluster -> related chunks
            multi_hop_result = session.run("""
                MATCH (ch:Chunk {chunk_id: $chunk_id})
                OPTIONAL MATCH (cl:Cluster)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch)
                OPTIONAL MATCH (cl)-[:SIMILAR_TO_CLUSTER_HIGH]->(cl2:Cluster)
                OPTIONAL MATCH (cl2)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch2:Chunk)
                WHERE ch2.chunk_id <> $chunk_id
                RETURN ch2.chunk_id, ch2.content, cl2.cluster_id
                LIMIT 5
            """, chunk_id=chunk_id)
            
            related_chunks = []
            for record in multi_hop_result:
                content = record["ch2.content"]
                if content:
                    content_preview = content[:100] + "..." if len(content) > 100 else content
                else:
                    content_preview = "No content"
                
                related_chunks.append({
                    "chunk_id": record["ch2.chunk_id"],
                    "content": content_preview,
                    "cluster_id": record["cl2.cluster_id"]
                })
            
            return {
                "starting_chunk_id": chunk_id,
                "related_chunks_count": len(related_chunks),
                "related_chunks": related_chunks,
                "multi_hop_available": len(related_chunks) > 0
            }
    
    def _test_embedding_drift(self):
        """Test for embedding drift - same content should have same embeddings."""
        import hashlib
        
        # Get embeddings from Qdrant
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=1000,
            with_payload=True,
            with_vectors=True
        )[0]
        
        # Group by content and check for drift
        content_embeddings = {}
        drift_detected = []
        
        for point in points:
            content = point.payload.get("content", "")
            if not content:
                continue
                
            # Create hash of vector
            vector_hash = hashlib.md5(str(point.vector).encode()).hexdigest()
            
            if content in content_embeddings:
                if content_embeddings[content] != vector_hash:
                    drift_detected.append({
                        "content": content[:50] + "..." if len(content) > 50 else content,
                        "original_hash": content_embeddings[content][:8],
                        "new_hash": vector_hash[:8]
                    })
            else:
                content_embeddings[content] = vector_hash
        
        return {
            "total_content_samples": len(content_embeddings),
            "drift_detected_count": len(drift_detected),
            "drift_detected": drift_detected,
            "embedding_consistent": len(drift_detected) == 0
        }
    
    def _test_combined_endpoint_shape(self):
        """Test the combined endpoint response structure for semantic search."""
        # Simulate a semantic search response
        search_query = "python programming"
        
        # Get embedding for query
        query_embedding = self.embedding_model.encode(search_query).tolist()
        
        # Search in Qdrant
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_embedding,
            limit=3,
            with_payload=True
        )
        
        # Build combined response structure
        combined_responses = []
        
        for result in search_result:
            chunk_id = result.payload.get("chunk_id")
            
            # Get additional context from Neo4j
            with self.neo4j_driver.session() as session:
                context_result = session.run("""
                    MATCH (ch:Chunk {chunk_id: $chunk_id})
                    OPTIONAL MATCH (m:Message)-[:HAS_CHUNK]->(ch)
                    OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
                    OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                    OPTIONAL MATCH (cl:Cluster)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch)
                    RETURN m.message_id, c.title as chat_title, 
                           collect(DISTINCT t.tags) as tags,
                           cl.cluster_id
                """, chunk_id=chunk_id)
                
                context = context_result.single()
                
                if context:
                    combined_response = {
                        "chunk_id": chunk_id,
                        "content": result.payload.get("content", "")[:200] + "..." if len(result.payload.get("content", "")) > 200 else result.payload.get("content", ""),
                        "similarity": result.score,
                        "message_id": context["m.message_id"],
                        "chat_title": context["chat_title"],
                        "tags": context["tags"] if context["tags"] else [],
                        "cluster_id": context["cl.cluster_id"]
                    }
                    combined_responses.append(combined_response)
        
        return {
            "query": search_query,
            "results_count": len(combined_responses),
            "sample_response": combined_responses[0] if combined_responses else None,
            "response_structure_valid": len(combined_responses) > 0
        }
    
    def _test_fresh_data_embedding(self):
        """Test embedding fresh data and adding to both databases."""
        import uuid
        
        # Create test data
        test_content = "What is vector search and how does it work?"
        test_message_id = str(uuid.uuid4())
        test_chunk_id = f"test_chunk_{uuid.uuid4().hex}"
        
        try:
            # Generate embedding
            test_embedding = self.embedding_model.encode(test_content).tolist()
            
            # Add to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.qdrant_collection,
                points=[{
                    "id": test_chunk_id,
                    "vector": test_embedding,
                    "payload": {
                        "chunk_id": test_chunk_id,
                        "message_id": test_message_id,
                        "content": test_content,
                        "role": "user",
                        "test_data": True
                    }
                }]
            )
            
            # Add to Neo4j
            with self.neo4j_driver.session() as session:
                session.run("""
                    CREATE (m:Message {
                        message_id: $message_id,
                        content: $content,
                        role: 'user',
                        test_data: true
                    })
                    CREATE (ch:Chunk {
                        chunk_id: $chunk_id,
                        content: $content,
                        test_data: true
                    })
                    CREATE (m)-[:HAS_CHUNK]->(ch)
                """, message_id=test_message_id, chunk_id=test_chunk_id, content=test_content)
            
            # Verify data was added
            qdrant_verify = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter={"must": [{"key": "chunk_id", "match": {"value": test_chunk_id}}]},
                limit=1
            )[0]
            
            neo4j_verify = session.run("""
                MATCH (m:Message {message_id: $message_id})
                RETURN count(m) as message_count
            """, message_id=test_message_id).single()
            
            return {
                "test_content": test_content,
                "test_message_id": test_message_id,
                "test_chunk_id": test_chunk_id,
                "qdrant_added": len(qdrant_verify) > 0,
                "neo4j_added": neo4j_verify["message_count"] > 0,
                "fresh_data_embedding_works": len(qdrant_verify) > 0 and neo4j_verify["message_count"] > 0
            }
            
        except Exception as e:
            return {
                "error": f"Fresh data embedding test failed: {str(e)}",
                "fresh_data_embedding_works": False
            }
    
    def _test_neo4j_qdrant_sync_drift(self):
        """Test for sync drift between Neo4j and Qdrant."""
        # Get all message IDs from Neo4j
        with self.neo4j_driver.session() as session:
            neo4j_messages_result = session.run("""
                MATCH (m:Message)
                RETURN m.message_id
                LIMIT 100
            """)
            neo4j_message_ids = set([record["m.message_id"] for record in neo4j_messages_result])
        
        # Get all message IDs from Qdrant
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )[0]
        
        qdrant_message_ids = set()
        for point in points:
            message_id = point.payload.get("message_id")
            if message_id:
                qdrant_message_ids.add(message_id)
        
        # Calculate drift
        neo4j_only = neo4j_message_ids - qdrant_message_ids
        qdrant_only = qdrant_message_ids - neo4j_message_ids
        common = neo4j_message_ids & qdrant_message_ids
        
        return {
            "neo4j_message_count": len(neo4j_message_ids),
            "qdrant_message_count": len(qdrant_message_ids),
            "common_messages": len(common),
            "neo4j_only": len(neo4j_only),
            "qdrant_only": len(qdrant_only),
            "sync_drift_percentage": ((len(neo4j_only) + len(qdrant_only)) / len(neo4j_message_ids)) * 100 if neo4j_message_ids else 0,
            "databases_synced": len(neo4j_only) == 0 and len(qdrant_only) == 0
        }
    
    # Schema Snapshot Test Methods
    def _test_semantic_search_response_schema(self):
        """Generate semantic search response schema for API documentation."""
        # Run a semantic search and capture the response structure
        search_query = "machine learning"
        query_embedding = self.embedding_model.encode(search_query).tolist()
        
        search_result = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_embedding,
            limit=2,
            with_payload=True
        )
        
        schema_examples = []
        for result in search_result:
            chunk_id = result.payload.get("chunk_id")
            
            # Get context from Neo4j
            with self.neo4j_driver.session() as session:
                context_result = session.run("""
                    MATCH (ch:Chunk {chunk_id: $chunk_id})
                    OPTIONAL MATCH (m:Message)-[:HAS_CHUNK]->(ch)
                    OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
                    OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                    RETURN m.message_id, c.title as chat_title, 
                           collect(DISTINCT t.tags) as tags,
                           ch.cluster_id
                """, chunk_id=chunk_id)
                
                context = context_result.single()
                
                if context:
                    schema_example = {
                        "chunk_id": chunk_id,
                        "content": result.payload.get("content", "")[:100] + "..." if len(result.payload.get("content", "")) > 100 else result.payload.get("content", ""),
                        "similarity_score": result.score,
                        "message_id": context["m.message_id"],
                        "chat_title": context["chat_title"],
                        "tags": context["tags"] if context["tags"] else [],
                        "cluster_id": context["ch.cluster_id"],
                        "metadata": {
                            "role": result.payload.get("role"),
                            "domain": result.payload.get("domain"),
                            "complexity": result.payload.get("complexity")
                        }
                    }
                    schema_examples.append(schema_example)
        
        return {
            "query": search_query,
            "response_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "chunk_id": {"type": "string"},
                                "content": {"type": "string"},
                                "similarity_score": {"type": "number"},
                                "message_id": {"type": "string"},
                                "chat_title": {"type": "string"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "cluster_id": {"type": "number"},
                                "metadata": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "example_responses": schema_examples
        }
    
    def _test_graph_exploration_response_schema(self):
        """Generate graph exploration response schema for API documentation."""
        with self.neo4j_driver.session() as session:
            # Get sample graph data
            graph_result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                RETURN c.chat_id, c.title, m.message_id, ch.chunk_id,
                       collect(DISTINCT t.tags) as tags
                LIMIT 3
            """)
            
            graph_examples = []
            for record in graph_result:
                graph_example = {
                    "chat_id": record["c.chat_id"],
                    "chat_title": record["c.title"],
                    "message_id": record["m.message_id"],
                    "chunk_id": record["ch.chunk_id"],
                    "tags": record["tags"] if record["tags"] else [],
                    "relationships": {
                        "chat_to_message": "CONTAINS",
                        "message_to_chunk": "HAS_CHUNK",
                        "tag_to_message": "TAGS"
                    }
                }
                graph_examples.append(graph_example)
        
        return {
            "response_schema": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "type": {"type": "string"},
                                "properties": {"type": "object"}
                            }
                        }
                    },
                    "edges": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "target": {"type": "string"},
                                "type": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "example_responses": graph_examples
        }
    
    def _test_content_discovery_response_schema(self):
        """Generate content discovery response schema for API documentation."""
        with self.neo4j_driver.session() as session:
            # Get sample content discovery data
            discovery_result = session.run("""
                MATCH (c:Chat)-[:CONTAINS]->(m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                RETURN c.chat_id, c.title, count(DISTINCT m) as message_count,
                       count(DISTINCT ch) as chunk_count,
                       collect(DISTINCT t.tags) as all_tags
                LIMIT 3
            """)
            
            discovery_examples = []
            for record in discovery_result:
                discovery_example = {
                    "chat_id": record["c.chat_id"],
                    "chat_title": record["c.title"],
                    "message_count": record["message_count"],
                    "chunk_count": record["chunk_count"],
                    "tags": record["all_tags"] if record["all_tags"] else [],
                    "discovery_metrics": {
                        "content_density": record["chunk_count"] / record["message_count"] if record["message_count"] > 0 else 0,
                        "tag_diversity": len(set([tag for tags in record["all_tags"] for tag in tags])) if record["all_tags"] else 0
                    }
                }
                discovery_examples.append(discovery_example)
        
        return {
            "response_schema": {
                "type": "object",
                "properties": {
                    "discoveries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "chat_id": {"type": "string"},
                                "chat_title": {"type": "string"},
                                "message_count": {"type": "number"},
                                "chunk_count": {"type": "number"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                                "discovery_metrics": {"type": "object"}
                            }
                        }
                    }
                }
            },
            "example_responses": discovery_examples
        }
    
    # Timestamp Validation Methods
    def _test_neo4j_timestamp_formats(self):
        """Test Neo4j timestamp formats and data types."""
        with self.neo4j_driver.session() as session:
            # Test chat timestamps
            chat_timestamps_result = session.run("""
                MATCH (c:Chat)
                RETURN c.chat_id, c.create_time, c.update_time
                ORDER BY c.create_time DESC
                LIMIT 5
            """)
            chat_timestamps = [dict(record) for record in chat_timestamps_result]
            
            # Test message timestamps
            message_timestamps_result = session.run("""
                MATCH (m:Message)
                RETURN m.message_id, m.timestamp, m.role
                ORDER BY m.timestamp DESC
                LIMIT 5
            """)
            message_timestamps = [dict(record) for record in message_timestamps_result]
            
            # Test chunk timestamps (if they exist)
            chunk_timestamps_result = session.run("""
                MATCH (ch:Chunk)
                RETURN ch.chunk_id, ch.timestamp
                ORDER BY ch.timestamp DESC
                LIMIT 5
            """)
            chunk_timestamps = [dict(record) for record in chunk_timestamps_result]
            
            # Analyze timestamp formats
            timestamp_analysis = {
                "chat_timestamps": len(chat_timestamps),
                "message_timestamps": len(message_timestamps),
                "chunk_timestamps": len(chunk_timestamps),
                "sample_chat_timestamp": chat_timestamps[0] if chat_timestamps else None,
                "sample_message_timestamp": message_timestamps[0] if message_timestamps else None,
                "timestamp_types": {
                    "chat_create_time_type": type(chat_timestamps[0]["c.create_time"]).__name__ if chat_timestamps else None,
                    "message_timestamp_type": type(message_timestamps[0]["m.timestamp"]).__name__ if message_timestamps else None
                }
            }
            
            return timestamp_analysis
    
    def _test_qdrant_timestamp_payloads(self):
        """Test Qdrant timestamp payloads and formats."""
        try:
            # Get sample points with timestamps
            points = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                limit=10,
                with_payload=True,
                with_vectors=False
            )[0]
            
            timestamp_analysis = {
                "total_points_checked": len(points),
                "timestamp_fields_found": [],
                "sample_timestamps": []
            }
            
            for point in points:
                payload = point.payload
                
                # Check for timestamp fields
                timestamp_fields = []
                for key, value in payload.items():
                    if 'timestamp' in key.lower() or 'time' in key.lower():
                        timestamp_fields.append(key)
                
                if timestamp_fields:
                    timestamp_analysis["timestamp_fields_found"].extend(timestamp_fields)
                    timestamp_analysis["sample_timestamps"].append({
                        "point_id": point.id,
                        "timestamp_fields": timestamp_fields,
                        "sample_values": {field: payload.get(field) for field in timestamp_fields[:3]}
                    })
            
            # Remove duplicates
            timestamp_analysis["timestamp_fields_found"] = list(set(timestamp_analysis["timestamp_fields_found"]))
            
            return timestamp_analysis
            
        except Exception as e:
            return {"error": f"Qdrant timestamp test failed: {str(e)}"}
    
    def _test_timestamp_cross_database_consistency(self):
        """Test timestamp consistency between Neo4j and Qdrant."""
        try:
            # Get sample message from Neo4j
            with self.neo4j_driver.session() as session:
                neo4j_message_result = session.run("""
                    MATCH (m:Message)
                    WHERE m.timestamp IS NOT NULL
                    RETURN m.message_id, m.timestamp AS ts, m.content
                    ORDER BY m.timestamp DESC
                    LIMIT 1
                """)
                neo4j_message = neo4j_message_result.single()
            
            if not neo4j_message:
                return {"error": "No messages found in Neo4j"}
            
            message_id = neo4j_message["message_id"]
            neo4j_timestamp = neo4j_message["ts"]
            
            # Normalize Neo4j timestamp to seconds (float)
            if isinstance(neo4j_timestamp, (int, float)):
                neo4j_ts_sec = float(neo4j_timestamp)
            else:
                # Fallback: try to parse if string-like
                try:
                    neo4j_ts_sec = float(neo4j_timestamp)
                except Exception:
                    neo4j_ts_sec = None
            
            # Find corresponding point in Qdrant
            points = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter={"must": [{"key": "message_id", "match": {"value": message_id}}]},
                limit=1,
                with_payload=True,
                with_vectors=False
            )[0]
            
            if not points:
                return {
                    "error": f"Message {message_id} not found in Qdrant",
                    "neo4j_timestamp": neo4j_timestamp
                }
            
            qdrant_point = points[0]
            qdrant_timestamp = qdrant_point.payload.get("original_timestamp")
            
            # Normalize Qdrant timestamp: support int/float seconds, or ISO strings
            qdrant_ts_sec = None
            if isinstance(qdrant_timestamp, (int, float)):
                qdrant_ts_sec = float(qdrant_timestamp)
            elif isinstance(qdrant_timestamp, str):
                # Try parse ISO8601
                try:
                    from datetime import datetime
                    qdrant_ts_sec = datetime.fromisoformat(qdrant_timestamp.replace("Z", "+00:00")).timestamp()
                except Exception:
                    # Try cast
                    try:
                        qdrant_ts_sec = float(qdrant_timestamp)
                    except Exception:
                        qdrant_ts_sec = None
            
            # Compare timestamps
            if neo4j_ts_sec is not None and qdrant_ts_sec is not None:
                diff = abs(neo4j_ts_sec - qdrant_ts_sec)
            else:
                diff = None

            timestamp_consistency = {
                "message_id": message_id,
                "neo4j_timestamp": neo4j_timestamp,
                "qdrant_timestamp": qdrant_timestamp,
                "timestamps_match": (diff is not None and diff < 1.0),
                "timestamp_difference_seconds": diff
            }
            
            return timestamp_consistency
            
        except Exception as e:
            return {"error": f"Cross-database timestamp test failed: {str(e)}"}
    
    def _test_timestamp_based_queries(self):
        """Test timestamp-based queries and filtering."""
        try:
            # Get current time for reference
            current_time = time.time()
            
            # Test Neo4j time-based queries
            with self.neo4j_driver.session() as session:
                # Recent messages (last 30 days)
                recent_messages_result = session.run("""
                    MATCH (m:Message)
                    WHERE m.timestamp > $cutoff_time
                    RETURN count(m) as recent_message_count
                """, cutoff_time=current_time - (30 * 24 * 3600))
                recent_count = recent_messages_result.single()["recent_message_count"]
                
                # Old messages (older than 90 days)
                old_messages_result = session.run("""
                    MATCH (m:Message)
                    WHERE m.timestamp < $cutoff_time
                    RETURN count(m) as old_message_count
                """, cutoff_time=current_time - (90 * 24 * 3600))
                old_count = old_messages_result.single()["old_message_count"]
                
                # Messages by time range
                time_range_result = session.run("""
                    MATCH (m:Message)
                    WHERE m.timestamp > $start_time AND m.timestamp < $end_time
                    RETURN count(m) as range_message_count
                """, start_time=current_time - (60 * 24 * 3600), end_time=current_time - (30 * 24 * 3600))
                range_count = time_range_result.single()["range_message_count"]
            
            # Test Qdrant time-based filtering
            # Try numeric seconds range
            qdrant_recent_points = self.qdrant_client.scroll(
                collection_name=self.qdrant_collection,
                scroll_filter={"must": [{"key": "original_timestamp", "range": {"gte": current_time - (30 * 24 * 3600)}}]},
                limit=10,
                with_payload=False
            )[0]
            # If zero, try ISO date string range (very coarse: last 30 days via iso prefix)
            if len(qdrant_recent_points) == 0:
                try:
                    from datetime import datetime, timedelta
                    iso_cutoff = (datetime.utcfromtimestamp(current_time) - timedelta(days=30)).isoformat()
                    qdrant_recent_points = self.qdrant_client.scroll(
                        collection_name=self.qdrant_collection,
                        scroll_filter={"must": [{"key": "original_timestamp", "match": {"value": iso_cutoff[:10]}}]},
                        limit=10,
                        with_payload=False
                    )[0]
                except Exception:
                    pass
            
            timestamp_query_results = {
                "neo4j_recent_messages": recent_count,
                "neo4j_old_messages": old_count,
                "neo4j_range_messages": range_count,
                "qdrant_recent_points": len(qdrant_recent_points),
                "current_time_reference": current_time
            }
            
            return timestamp_query_results
            
        except Exception as e:
            return {"error": f"Timestamp-based query test failed: {str(e)}"}
    
    def _test_timestamp_ranges_and_ordering(self):
        """Test timestamp ranges and ordering functionality."""
        with self.neo4j_driver.session() as session:
            # Test chronological ordering
            chronological_result = session.run("""
                MATCH (m:Message)
                RETURN m.message_id, m.timestamp, m.role
                ORDER BY m.timestamp ASC
                LIMIT 5
            """)
            chronological_messages = [dict(record) for record in chronological_result]
            
            # Test reverse chronological ordering
            reverse_chronological_result = session.run("""
                MATCH (m:Message)
                RETURN m.message_id, m.timestamp, m.role
                ORDER BY m.timestamp DESC
                LIMIT 5
            """)
            reverse_chronological_messages = [dict(record) for record in reverse_chronological_result]
            
            # Test chat creation time ordering
            chat_ordering_result = session.run("""
                MATCH (c:Chat)
                RETURN c.chat_id, c.create_time, c.title
                ORDER BY c.create_time DESC
                LIMIT 5
            """)
            chat_ordering = [dict(record) for record in chat_ordering_result]
            
            # Verify ordering is correct
            chronological_ordered = True
            if len(chronological_messages) > 1:
                for i in range(1, len(chronological_messages)):
                    if chronological_messages[i]["m.timestamp"] < chronological_messages[i-1]["m.timestamp"]:
                        chronological_ordered = False
                        break
            
            reverse_ordered = True
            if len(reverse_chronological_messages) > 1:
                for i in range(1, len(reverse_chronological_messages)):
                    if reverse_chronological_messages[i]["m.timestamp"] > reverse_chronological_messages[i-1]["m.timestamp"]:
                        reverse_ordered = False
                        break
            
            return {
                "chronological_messages": len(chronological_messages),
                "reverse_chronological_messages": len(reverse_chronological_messages),
                "chat_ordering": len(chat_ordering),
                "chronological_ordering_correct": chronological_ordered,
                "reverse_ordering_correct": reverse_ordered,
                "sample_chronological": chronological_messages[0] if chronological_messages else None,
                "sample_reverse": reverse_chronological_messages[0] if reverse_chronological_messages else None
            }
    
    def _test_timestamp_data_quality(self):
        """Test timestamp data quality and validation."""
        with self.neo4j_driver.session() as session:
            # Check for null timestamps
            null_timestamp_result = session.run("""
                MATCH (m:Message)
                WHERE m.timestamp IS NULL
                RETURN count(m) as null_timestamp_count
            """)
            null_timestamp_count = null_timestamp_result.single()["null_timestamp_count"]
            
            # Check for invalid timestamps (negative or future)
            current_time = time.time()
            invalid_timestamp_result = session.run("""
                MATCH (m:Message)
                WHERE m.timestamp < 0 OR m.timestamp > $future_threshold
                RETURN count(m) as invalid_timestamp_count
            """, future_threshold=current_time + (365 * 24 * 3600))  # 1 year in future
            invalid_timestamp_count = invalid_timestamp_result.single()["invalid_timestamp_count"]
            
            # Check timestamp range
            timestamp_range_result = session.run("""
                MATCH (m:Message)
                RETURN min(m.timestamp) as min_timestamp, 
                       max(m.timestamp) as max_timestamp,
                       count(m) as total_messages
            """)
            timestamp_range = timestamp_range_result.single()
            
            # Check for duplicate timestamps (same exact time)
            duplicate_timestamp_result = session.run("""
                MATCH (m:Message)
                WITH m.timestamp as ts, count(*) as count
                WHERE count > 1
                RETURN count(ts) as duplicate_timestamp_groups
            """)
            duplicate_timestamp_groups = duplicate_timestamp_result.single()["duplicate_timestamp_groups"]
            
            data_quality_report = {
                "null_timestamps": null_timestamp_count,
                "invalid_timestamps": invalid_timestamp_count,
                "total_messages": timestamp_range["total_messages"],
                "timestamp_range": {
                    "min": timestamp_range["min_timestamp"],
                    "max": timestamp_range["max_timestamp"],
                    "span_days": (timestamp_range["max_timestamp"] - timestamp_range["min_timestamp"]) / (24 * 3600) if timestamp_range["min_timestamp"] and timestamp_range["max_timestamp"] else None
                },
                "duplicate_timestamp_groups": duplicate_timestamp_groups,
                "data_quality_score": {
                    "null_percentage": (null_timestamp_count / timestamp_range["total_messages"]) * 100 if timestamp_range["total_messages"] > 0 else 0,
                    "invalid_percentage": (invalid_timestamp_count / timestamp_range["total_messages"]) * 100 if timestamp_range["total_messages"] > 0 else 0,
                    "quality_score": 100 - ((null_timestamp_count + invalid_timestamp_count) / timestamp_range["total_messages"]) * 100 if timestamp_range["total_messages"] > 0 else 0
                }
            }
            
            return data_quality_report

    def run_all_tests(self):
        """Run all database tests."""
        logger.info("🚀 Starting Comprehensive Database Query Tests...")
        
        if not self.connect_databases():
            return False
        
        try:
            # Run all test categories
            test_categories = [
                self.test_neo4j_basic_queries,
                self.test_qdrant_basic_queries,
                self.test_cross_database_connections,
                self.test_semantic_search_workflow,
                self.test_hybrid_queries,
                self.test_performance_metrics,
                self.test_semantic_analysis_queries,
                self.test_similarity_queries,
                self.test_content_discovery_queries,
                self.test_advanced_analysis_queries,
                self.test_statistics_analytics_queries,
                self.test_graph_exploration_queries,
                self.test_quality_analysis_queries,
                self.test_visualization_queries,
                self.test_api_readiness_queries,
                self.test_schema_snapshot_queries,
                self.test_timestamp_validation_queries
            ]
            
            for test_category in test_categories:
                test_category()
            
            # Print summary
            self.print_summary()
            
        finally:
            self.close_connections()
    
    def print_summary(self):
        """Print comprehensive test summary."""
        logger.info("\n📋 Comprehensive Database Test Summary:")
        
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
            logger.info("🎉 Excellent! Hybrid database queries are working correctly.")
        elif success_rate >= 80:
            logger.info("⚠️  Good, but some queries need attention.")
        else:
            logger.error("❌ Many queries are failing. Check database setup.")
    
    def _test_content_verification(self):
        """Test content verification between Neo4j and Qdrant."""
        # Get sample chunk from Neo4j
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (ch:Chunk) 
                RETURN ch.chunk_id as chunk_id, ch.content as content 
                LIMIT 1
            """)
            neo4j_chunk = result.single()
            
            if not neo4j_chunk:
                return {'status': 'failed', 'reason': 'no_chunks_in_neo4j'}
            
            chunk_id = neo4j_chunk['chunk_id']
            content = neo4j_chunk['content']
            
            # Try to find the same chunk in Qdrant
            try:
                qdrant_point = self.qdrant_client.retrieve(
                    collection_name=self.qdrant_collection,
                    ids=[chunk_id]
                )
                
                if not qdrant_point:
                    return {
                        'status': 'failed', 
                        'reason': f'chunk_not_found_in_qdrant: {chunk_id}'
                    }
                
                qdrant_content = qdrant_point[0].payload.get('content', '')
                
                # Verify content matches
                if content != qdrant_content:
                    return {
                        'status': 'failed',
                        'reason': 'content_mismatch',
                        'neo4j_content': content[:50] + '...',
                        'qdrant_content': qdrant_content[:50] + '...'
                    }
                
                return {
                    'status': 'success',
                    'chunk_id': chunk_id,
                    'content_matches': True,
                    'neo4j_content_length': len(content),
                    'qdrant_content_length': len(qdrant_content)
                }
                
            except Exception as e:
                return {
                    'status': 'failed',
                    'reason': f'qdrant_retrieve_error: {str(e)}',
                    'chunk_id': chunk_id
                }
    
    def _test_basic_semantic_search(self):
        """Test basic semantic search functionality in Qdrant."""
        try:
            # Get collection info to check if we have points
            collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
            
            if collection_info.points_count == 0:
                return {'status': 'failed', 'reason': 'no_points_in_collection'}
            
            # Try a simple search with a test vector
            search_results = self.qdrant_client.search(
                collection_name=self.qdrant_collection,
                query_vector=[0.1] * 384,  # Simple test vector
                limit=5
            )
            
            if not search_results:
                return {'status': 'failed', 'reason': 'search_returned_no_results'}
            
            return {
                'status': 'success',
                'search_results_count': len(search_results),
                'first_result_score': search_results[0].score,
                'first_result_id': search_results[0].id,
                'collection_points': collection_info.points_count
            }
            
        except Exception as e:
            return {'status': 'failed', 'reason': f'semantic_search_error: {str(e)}'}
    
    def export_results(self, output_file="hybrid_db_test_results.json"):
        """Export test results to JSON."""
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

    def _summarize_counts(self, result: dict) -> str:
        """Build a concise counts summary from a result dict.
        Picks common *_count keys and known numeric indicators.
        """
        if not isinstance(result, dict):
            return ""
        # Known keys to surface
        preferred_keys = [
            'count', 'results_count', 'neo4j_count', 'qdrant_count', 'qdrant_present',
            'intersection_count', 'chat_count', 'cluster_count', 'embedding_count',
            'recent_message_count', 'old_message_count', 'range_message_count',
            'qdrant_recent_points', 'avg_chunks_per_message'
        ]
        # Auto-detect *_count keys
        items = []
        for key, val in result.items():
            if isinstance(val, (int, float)) and (key in preferred_keys or key.endswith('_count')):
                items.append((key, val))
        # Ensure preferred keys order first
        keyed = {k: v for k, v in items}
        ordered = []
        for k in preferred_keys:
            if k in keyed:
                ordered.append((k, keyed[k]))
        # Add the rest deterministically
        for k, v in sorted(items):
            if (k, v) not in ordered:
                ordered.append((k, v))
        if not ordered:
            return "no-counts"
        return ", ".join(f"{k}={v}" for k, v in ordered)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Hybrid Database Query Tester")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    
    args = parser.parse_args()
    
    tester = HybridDatabaseTester()
    tester.run_all_tests()
    
    if args.export:
        tester.export_results(args.export) 