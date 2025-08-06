#!/usr/bin/env python3
"""
Updated Database Query Test Script for ChatMind Hybrid Architecture
Tests both Neo4j (graph database) and Qdrant (vector database) queries,
properly reflecting the current architecture where embeddings are only in Qdrant.
"""

import sys
import os
import json
import time
import hashlib
from pathlib import Path
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

class UpdatedHybridDatabaseTester:
    """Updated tester for hybrid architecture with embeddings only in Qdrant."""
    
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
                logger.info(f"✅ {name}: {result_count} results ({execution_time:.3f}s)")
                if result.get('data') and len(result['data']) <= 3:
                    for i, item in enumerate(result['data'][:3]):
                        logger.info(f"   Result {i+1}: {item}")
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
        
        # Test entity type distribution
        self.test_query(
            "Qdrant - Entity type distribution",
            lambda: self._get_qdrant_entity_type_distribution()
        )
    
    def test_hybrid_architecture_queries(self):
        """Test queries that validate our hybrid architecture."""
        logger.info("\n🏗️ Testing Hybrid Architecture Queries...")
        
        # Test that embeddings are only in Qdrant
        self.test_query(
            "Hybrid - Embeddings only in Qdrant",
            lambda: self._test_embeddings_only_in_qdrant()
        )
        
        # Test cross-database linking
        self.test_query(
            "Hybrid - Cross-database linking",
            lambda: self._test_cross_database_linking()
        )
        
        # Test semantic search with graph context
        self.test_query(
            "Hybrid - Semantic search with graph context",
            lambda: self._test_semantic_search_with_graph_context()
        )
        
        # Test hierarchical search (chunks, clusters, chat summaries)
        self.test_query(
            "Hybrid - Hierarchical search",
            lambda: self._test_hierarchical_search()
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
    
    def test_tag_system_queries(self):
        """Test tag system queries."""
        logger.info("\n🏷️ Testing Tag System Queries...")
        
        # Test messages with tags
        self.test_query(
            "Tags - Messages with tags",
            lambda: self._test_messages_with_tags()
        )
        
        # Test tag distribution
        self.test_query(
            "Tags - Tag distribution",
            lambda: self._test_tag_distribution()
        )
        
        # Test tag-chunk relationships
        self.test_query(
            "Tags - Tag-chunk relationships",
            lambda: self._test_tag_chunk_relationships()
        )
        
        # Test multi-tag search (AND logic)
        self.test_query(
            "Tags - Multi-tag search",
            lambda: self._test_multi_tag_search()
        )
    
    def test_cluster_system_queries(self):
        """Test cluster system queries."""
        logger.info("\n🎯 Testing Cluster System Queries...")
        
        # Test cluster data
        self.test_query(
            "Clusters - Cluster data",
            lambda: self._test_cluster_data()
        )
        
        # Test cluster-chunk relationships
        self.test_query(
            "Clusters - Cluster-chunk relationships",
            lambda: self._test_cluster_chunk_relationships()
        )
        
        # Test cluster summaries
        self.test_query(
            "Clusters - Cluster summaries",
            lambda: self._test_cluster_summaries()
        )
    
    def test_summary_system_queries(self):
        """Test summary system queries."""
        logger.info("\n📊 Testing Summary System Queries...")
        
        # Test chat summaries
        self.test_query(
            "Summaries - Chat summaries",
            lambda: self._test_chat_summaries()
        )
        
        # Test summary embeddings in Qdrant
        self.test_query(
            "Summaries - Summary embeddings in Qdrant",
            lambda: self._test_summary_embeddings_in_qdrant()
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
        
        data = []
        for point in points:
            data.append({
                "id": point.id,
                "entity_type": point.payload.get("entity_type"),
                "chunk_id": point.payload.get("chunk_id"),
                "message_id": point.payload.get("message_id"),
                "chat_id": point.payload.get("chat_id"),
                "content_preview": point.payload.get("content", "")[:100]
            })
        
        return {"count": len(data), "data": data}
    
    def _get_qdrant_entity_type_distribution(self):
        """Get distribution of entity types in Qdrant."""
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=1000,
            with_payload=True,
            with_vectors=False
        )[0]
        
        entity_types = {}
        for point in points:
            entity_type = point.payload.get("entity_type", "unknown")
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        return {"count": len(entity_types), "data": dict(list(entity_types.items())[:3])}
    
    # Hybrid Architecture Test Methods
    def _test_embeddings_only_in_qdrant(self):
        """Test that embeddings are only stored in Qdrant, not Neo4j."""
        # Check Neo4j for Embedding nodes
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (e:Embedding)
                RETURN count(e) as embedding_count
            """)
            neo4j_embedding_count = result.single()["embedding_count"]
        
        # Get Qdrant point count
        collection_info = self.qdrant_client.get_collection(self.qdrant_collection)
        qdrant_point_count = collection_info.points_count
        
        return {
            "neo4j_embedding_count": neo4j_embedding_count,
            "qdrant_point_count": qdrant_point_count,
            "embeddings_only_in_qdrant": neo4j_embedding_count == 0,
            "architecture_correct": neo4j_embedding_count == 0 and qdrant_point_count > 0
        }
    
    def _test_cross_database_linking(self):
        """Test cross-database linking via IDs."""
        # Get sample chunk IDs from Neo4j
        with self.neo4j_driver.session() as session:
            neo4j_result = session.run("""
                MATCH (ch:Chunk)
                RETURN ch.chunk_id
                LIMIT 10
            """)
            neo4j_chunk_ids = [record["ch.chunk_id"] for record in neo4j_result]
        
        # Get sample chunk IDs from Qdrant
        points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            limit=10,
            with_payload=True,
            with_vectors=False
        )[0]
        
        qdrant_chunk_ids = []
        for point in points:
            chunk_id = point.payload.get("chunk_id")
            if chunk_id:
                qdrant_chunk_ids.append(chunk_id)
        
        # Check for overlap
        neo4j_set = set(neo4j_chunk_ids)
        qdrant_set = set(qdrant_chunk_ids)
        overlap = neo4j_set.intersection(qdrant_set)
        
        return {
            "neo4j_chunk_count": len(neo4j_set),
            "qdrant_chunk_count": len(qdrant_set),
            "overlap_count": len(overlap),
            "cross_linking_works": len(overlap) > 0
        }
    
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
                    OPTIONAL MATCH (cl:Cluster)-[:CONTAINS_CHUNK]->(ch)
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
    
    def _test_hierarchical_search(self):
        """Test hierarchical search across chunks, clusters, and chat summaries."""
        # Test search for different entity types
        test_query = "machine learning"
        query_vector = self.embedding_model.encode(test_query).tolist()
        
        # Search for chunks
        chunk_results = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            query_filter={"must": [{"key": "entity_type", "match": {"value": "chunk"}}]},
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        # Search for clusters
        cluster_results = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            query_filter={"must": [{"key": "entity_type", "match": {"value": "cluster"}}]},
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        # Search for chat summaries
        chat_summary_results = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_vector,
            query_filter={"must": [{"key": "entity_type", "match": {"value": "chat_summary"}}]},
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        return {
            "chunk_results": len(chunk_results),
            "cluster_results": len(cluster_results),
            "chat_summary_results": len(chat_summary_results),
            "hierarchical_search_works": len(chunk_results) > 0 or len(cluster_results) > 0 or len(chat_summary_results) > 0
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
                "entity_type": result.payload.get("entity_type")
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
    
    # Tag System Methods
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
    
    def _test_tag_chunk_relationships(self):
        """Test tag-chunk relationships."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS_CHUNK]->(ch:Chunk)
                RETURN t.tags, ch.chunk_id, substring(ch.content, 0, 100) as content_preview
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_multi_tag_search(self):
        """Test multi-tag search with AND logic."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (t:Tag)-[:TAGS]->(m:Message)
                WHERE ALL(tag IN ['#python', '#technology'] WHERE tag IN t.tags)
                RETURN m.content, m.role, t.tags
                ORDER BY m.timestamp DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    # Cluster System Methods
    def _test_cluster_data(self):
        """Test cluster data."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster)
                RETURN cl.cluster_id, cl.x, cl.y, cl.cluster_hash
                ORDER BY cl.cluster_id
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_cluster_chunk_relationships(self):
        """Test cluster-chunk relationships."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cl:Cluster)-[:CONTAINS_CHUNK]->(ch:Chunk)
                RETURN cl.cluster_id, count(ch) as chunk_count
                ORDER BY chunk_count DESC
                LIMIT 10
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_cluster_summaries(self):
        """Test cluster summaries."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
                RETURN cl.cluster_id, s.summary, s.key_points
                ORDER BY cl.cluster_id
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    # Summary System Methods
    def _test_chat_summaries(self):
        """Test chat summaries."""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c:Chat)
                RETURN c.chat_id, c.title, cs.summary, cs.key_points
                ORDER BY c.create_time DESC
                LIMIT 5
            """)
            data = [dict(record) for record in result]
            return {"count": len(data), "data": data[:3]}
    
    def _test_summary_embeddings_in_qdrant(self):
        """Test that summary embeddings are stored in Qdrant."""
        # Check for cluster summary embeddings
        cluster_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "cluster"}}]},
            limit=5,
            with_payload=True,
            with_vectors=False
        )[0]
        
        # Check for chat summary embeddings
        chat_summary_points = self.qdrant_client.scroll(
            collection_name=self.qdrant_collection,
            scroll_filter={"must": [{"key": "entity_type", "match": {"value": "chat_summary"}}]},
            limit=5,
            with_payload=True,
            with_vectors=False
        )[0]
        
        return {
            "cluster_summary_embeddings": len(cluster_points),
            "chat_summary_embeddings": len(chat_summary_points),
            "summary_embeddings_exist": len(cluster_points) > 0 or len(chat_summary_points) > 0
        }
    
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
    
    def run_all_tests(self):
        """Run all database tests."""
        logger.info("🚀 Starting Updated Hybrid Database Query Tests...")
        
        if not self.connect_databases():
            return False
        
        try:
            # Run all test categories
            test_categories = [
                self.test_neo4j_basic_queries,
                self.test_qdrant_basic_queries,
                self.test_hybrid_architecture_queries,
                self.test_semantic_search_workflow,
                self.test_tag_system_queries,
                self.test_cluster_system_queries,
                self.test_summary_system_queries,
                self.test_performance_metrics
            ]
            
            for test_category in test_categories:
                test_category()
            
            # Print summary
            self.print_summary()
            
        finally:
            self.close_connections()
    
    def print_summary(self):
        """Print comprehensive test summary."""
        logger.info("\n📋 Updated Hybrid Database Test Summary:")
        
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
            logger.info("🎉 Excellent! Updated hybrid database queries are working correctly.")
        elif success_rate >= 80:
            logger.info("⚠️  Good, but some queries need attention.")
        else:
            logger.error("❌ Many queries are failing. Check database setup.")
    
    def export_results(self, output_file="updated_hybrid_db_test_results.json"):
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

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Updated Hybrid Database Query Tester")
    parser.add_argument("--export", type=str, help="Export results to JSON file")
    
    args = parser.parse_args()
    
    tester = UpdatedHybridDatabaseTester()
    tester.run_all_tests()
    
    if args.export:
        tester.export_results(args.export) 