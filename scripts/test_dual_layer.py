#!/usr/bin/env python3
"""
Test script for Dual Layer Graph Strategy implementation.

This script verifies that the dual layer graph strategy is working correctly
by testing Neo4j connections, node counts, relationships, and API endpoints.
"""

import sys
import os
import requests
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from chatmind.neo4j_loader.load_graph import Neo4jGraphLoader

def test_neo4j_connection():
    """Test basic Neo4j connection."""
    print("🔌 Testing Neo4j connection...")
    try:
        loader = Neo4jGraphLoader()
        loader.connect()
        loader.close()
        print("✅ Neo4j connection successful")
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

def test_node_counts():
    """Test that all node types exist and have reasonable counts."""
    print("\n📊 Testing node counts...")
    try:
        loader = Neo4jGraphLoader()
        loader.connect()
        
        with loader.driver.session() as session:
            # Test Chat nodes
            result = session.run("MATCH (c:Chat) RETURN count(c) as count")
            chat_count = result.single()["count"]
            print(f"✅ Raw Layer: {chat_count} chats")
            
            # Test Message nodes
            result = session.run("MATCH (m:Message) RETURN count(m) as count")
            message_count = result.single()["count"]
            print(f"✅ Raw Layer: {message_count} messages")
            
            # Test Chunk nodes
            result = session.run("MATCH (ch:Chunk) RETURN count(ch) as count")
            chunk_count = result.single()["count"]
            print(f"✅ Chunk Layer: {chunk_count} chunks")
            
            # Test Topic nodes
            result = session.run("MATCH (t:Topic) RETURN count(t) as count")
            topic_count = result.single()["count"]
            print(f"✅ Semantic Layer: {topic_count} topics")
            
            # Test Tag nodes
            result = session.run("MATCH (tag:Tag) RETURN count(tag) as count")
            tag_count = result.single()["count"]
            print(f"✅ Semantic Layer: {tag_count} tags")
            
            # Verify we have data
            if chat_count == 0:
                print("❌ Node count test failed: No Chat nodes found")
                return False
            if message_count == 0:
                print("❌ Node count test failed: No Message nodes found")
                return False
            if chunk_count == 0:
                print("❌ Node count test failed: No Chunk nodes found")
                return False
            if topic_count == 0:
                print("❌ Node count test failed: No Topic nodes found")
                return False
            if tag_count == 0:
                print("❌ Node count test failed: No Tag nodes found")
                return False
                
        loader.close()
        print("✅ Node Counts PASSED")
        return True
    except Exception as e:
        print(f"❌ Node count test failed: {e}")
        return False

def test_layer_relationships():
    """Test that dual layer relationships exist."""
    print("\n🔗 Testing layer relationships...")
    try:
        loader = Neo4jGraphLoader()
        loader.connect()
        
        with loader.driver.session() as session:
            # Test HAS_CHUNK relationships
            result = session.run("MATCH ()-[:HAS_CHUNK]->() RETURN count(*) as count")
            has_chunk_count = result.single()["count"]
            print(f"✅ HAS_CHUNK relationships: {has_chunk_count}")
            
            # Test TAGGED_WITH relationships
            result = session.run("MATCH ()-[:TAGGED_WITH]->() RETURN count(*) as count")
            tagged_with_count = result.single()["count"]
            print(f"✅ TAGGED_WITH relationships: {tagged_with_count}")
            
            # Test SUMMARIZES relationships
            result = session.run("MATCH ()-[:SUMMARIZES]->() RETURN count(*) as count")
            summarizes_count = result.single()["count"]
            print(f"✅ SUMMARIZES relationships: {summarizes_count}")
            
            # Test CONTAINS relationships
            result = session.run("MATCH ()-[:CONTAINS]->() RETURN count(*) as count")
            contains_count = result.single()["count"]
            print(f"✅ CONTAINS relationships: {contains_count}")
            
            # Verify we have relationships
            if has_chunk_count == 0:
                print("❌ Layer relationship test failed: No HAS_CHUNK relationships found")
                return False
            if tagged_with_count == 0:
                print("❌ Layer relationship test failed: No TAGGED_WITH relationships found")
                return False
            if summarizes_count == 0:
                print("❌ Layer relationship test failed: No SUMMARIZES relationships found")
                return False
            if contains_count == 0:
                print("❌ Layer relationship test failed: No CONTAINS relationships found")
                return False
                
        loader.close()
        print("✅ Layer Relationships PASSED")
        return True
    except Exception as e:
        print(f"❌ Layer relationship test failed: {e}")
        return False

def test_cross_layer_query():
    """Test cross-layer queries that join Message and Chunk nodes."""
    print("\n🔍 Testing cross-layer query...")
    try:
        loader = Neo4jGraphLoader()
        loader.connect()
        
        with loader.driver.session() as session:
            # Test cross-layer query
            result = session.run("""
                MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                RETURN m.message_id, ch.chunk_id, collect(DISTINCT tag.name) as tags
                LIMIT 5
            """)
            
            records = list(result)
            print(f"✅ Cross-layer query returned {len(records)} records")
            
            # Count messages with chunks
            result = session.run("""
                MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
                RETURN count(DISTINCT m) as message_count
            """)
            message_count = result.single()["message_count"]
            print(f"✅ Messages with chunks: {message_count}")
            
            # Count messages with tags
            result = session.run("""
                MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:TAGGED_WITH]->(tag:Tag)
                RETURN count(DISTINCT m) as message_count
            """)
            tagged_message_count = result.single()["message_count"]
            print(f"✅ Messages with tags: {tagged_message_count}")
            
            if len(records) == 0:
                print("❌ Cross-layer query test failed: No cross-layer data found")
                return False
                
        loader.close()
        print("✅ Cross-Layer Query PASSED")
        return True
    except Exception as e:
        print(f"❌ Cross-layer query test failed: {e}")
        return False

def test_semantic_layer_queries():
    """Test semantic layer queries for chunks, topics, and tags."""
    print("\n🧠 Testing semantic layer queries...")
    try:
        loader = Neo4jGraphLoader()
        loader.connect()
        
        with loader.driver.session() as session:
            # Test chunk queries
            result = session.run("""
                MATCH (ch:Chunk)
                WHERE ch.embedding IS NOT NULL
                RETURN count(ch) as chunk_count
            """)
            chunk_count = result.single()["chunk_count"]
            print(f"✅ Chunks with embeddings: {chunk_count}")
            
            # Test topic queries
            result = session.run("""
                MATCH (t:Topic)-[:SUMMARIZES]->(ch:Chunk)
                RETURN count(DISTINCT t) as topic_count, count(ch) as chunk_count
            """)
            record = result.single()
            topic_count = record["topic_count"]
            topic_chunk_count = record["chunk_count"]
            print(f"✅ Topics with chunks: {topic_count} topics, {topic_chunk_count} chunks")
            
            # Test tag queries
            result = session.run("""
                MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag:Tag)
                RETURN count(DISTINCT tag) as tag_count, count(ch) as chunk_count
            """)
            record = result.single()
            tag_count = record["tag_count"]
            tagged_chunk_count = record["chunk_count"]
            print(f"✅ Tags with chunks: {tag_count} tags, {tagged_chunk_count} chunks")
            
            if chunk_count == 0:
                print("❌ Semantic layer test failed: No chunks with embeddings found")
                return False
            if topic_count == 0:
                print("❌ Semantic layer test failed: No topics with chunks found")
                return False
            if tag_count == 0:
                print("❌ Semantic layer test failed: No tags with chunks found")
                return False
                
        loader.close()
        print("✅ Semantic Layer Queries PASSED")
        return True
    except Exception as e:
        print(f"❌ Semantic layer query test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints for dual layer functionality."""
    print("\n🌐 Testing API endpoints...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
            
        # Test raw conversations endpoint
        response = requests.get(f"{base_url}/api/conversations?limit=5")
        if response.status_code == 200:
            data = response.json()
            conversations = data.get("data", [])
            print(f"✅ Raw conversations endpoint: {len(conversations)} conversations")
        else:
            print(f"❌ Raw conversations endpoint failed: {response.status_code}")
            return False
            
        # Test chunks endpoint
        response = requests.get(f"{base_url}/api/chunks?limit=5")
        if response.status_code == 200:
            data = response.json()
            chunks = data.get("data", [])
            print(f"✅ Chunks endpoint: {len(chunks)} chunks")
        else:
            print(f"❌ Chunks endpoint failed: {response.status_code}")
            return False
            
        # Test topics endpoint
        response = requests.get(f"{base_url}/api/topics")
        if response.status_code == 200:
            data = response.json()
            topics = data.get("data", [])
            print(f"✅ Topics endpoint: {len(topics)} topics")
        else:
            print(f"❌ Topics endpoint failed: {response.status_code}")
            return False
            
        # Test graph endpoint with layer filtering
        response = requests.get(f"{base_url}/api/graph?layer=both&limit=150")
        if response.status_code == 200:
            data = response.json()
            graph_data = data.get("data", {})
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            print(f"✅ Graph endpoint: {len(nodes)} nodes, {len(edges)} edges")
        else:
            print(f"❌ Graph endpoint failed: {response.status_code}")
            return False
            
        print("✅ API Endpoints PASSED")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Start with: python3 chatmind/api/run.py")
        return False
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_advanced_dual_layer_queries():
    """Test advanced dual layer queries."""
    print("\n🔬 Testing advanced dual layer queries...")
    try:
        loader = Neo4jGraphLoader()
        loader.connect()
        
        with loader.driver.session() as session:
            # Test message with semantic analysis
            result = session.run("""
                MATCH (m:Message)
                OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
                OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
                OPTIONAL MATCH (t:Topic)-[:SUMMARIZES]->(ch)
                WITH m, count(DISTINCT ch) as chunk_count, 
                     count(DISTINCT tag) as tag_count,
                     count(DISTINCT t) as topic_count
                WHERE chunk_count > 0
                RETURN m.message_id, chunk_count, tag_count, topic_count
                LIMIT 5
            """)
            
            records = list(result)
            print(f"✅ Advanced dual layer query: {len(records)} messages with semantic data")
            
            # Test semantic similarity
            result = session.run("""
                MATCH (ch1:Chunk)-[:TAGGED_WITH]->(tag:Tag)
                MATCH (ch2:Chunk)-[:TAGGED_WITH]->(tag)
                WHERE ch1.chunk_id <> ch2.chunk_id
                RETURN count(DISTINCT tag) as shared_tags
                LIMIT 1
            """)
            
            record = result.single()
            if record:
                shared_tags = record["shared_tags"]
                print(f"✅ Semantic similarity test: {shared_tags} shared tags found")
            else:
                print("✅ Semantic similarity test: No shared tags found (expected)")
                
        loader.close()
        print("✅ Advanced Dual Layer Queries PASSED")
        return True
    except Exception as e:
        print(f"❌ Advanced dual layer query test failed: {e}")
        return False

def main():
    """Run all tests for the dual layer implementation."""
    print("🧪 Testing Dual Layer Graph Strategy Implementation")
    print("=" * 60)
    
    tests = [
        ("Neo4j Connection", test_neo4j_connection),
        ("Node Counts", test_node_counts),
        ("Layer Relationships", test_layer_relationships),
        ("Cross-Layer Query", test_cross_layer_query),
        ("Semantic Layer Queries", test_semantic_layer_queries),
        ("API Endpoints", test_api_endpoints),
        ("Advanced Dual Layer Queries", test_advanced_dual_layer_queries),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dual Layer Graph Strategy is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 