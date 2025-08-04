#!/usr/bin/env python3
"""
Simple API Test Suite - TDD Approach

Test the minimal API functionality before building complex features.
"""

import requests
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAPITester:
    """Test the minimal ChatMind API functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout
    
    def test_health_check(self) -> bool:
        """Test basic health endpoint"""
        try:
            logger.info("🧪 Testing health endpoint...")
            response = self.session.get(f"{self.base_url}/api/health")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Health check passed")
                logger.info(f"   Response: {data}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    def test_graph_data_simple(self) -> bool:
        """Test basic graph data endpoint"""
        try:
            logger.info("🧪 Testing graph data endpoint...")
            response = self.session.get(f"{self.base_url}/api/graph?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Graph data test passed")
                logger.info(f"   Found {len(data.get('data', {}).get('nodes', []))} nodes")
                return True
            else:
                logger.error(f"❌ Graph data test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Graph data test error: {e}")
            return False
    
    def test_conversations_list(self) -> bool:
        """Test conversations endpoint"""
        try:
            logger.info("🧪 Testing conversations endpoint...")
            response = self.session.get(f"{self.base_url}/api/conversations?limit=3")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Conversations test passed")
                logger.info(f"   Found {len(data.get('data', []))} conversations")
                return True
            else:
                logger.error(f"❌ Conversations test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Conversations test error: {e}")
            return False
    
    def test_simple_search(self) -> bool:
        """Test simple search endpoint (Neo4j only)"""
        try:
            logger.info("🧪 Testing simple search endpoint...")
            response = self.session.get(f"{self.base_url}/api/search?query=test&limit=5")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Simple search test passed")
                logger.info(f"   Found {len(data.get('data', []))} results")
                return True
            else:
                logger.error(f"❌ Simple search test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Simple search test error: {e}")
            return False
    
    def test_semantic_search(self) -> bool:
        """Test semantic search endpoint (Qdrant)"""
        try:
            logger.info("🧪 Testing semantic search endpoint...")
            response = self.session.get(f"{self.base_url}/api/search/semantic?query=health&limit=3")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Semantic search test passed")
                logger.info(f"   Found {len(data.get('data', []))} results")
                return True
            else:
                logger.error(f"❌ Semantic search test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Semantic search test error: {e}")
            return False
    
    def test_hybrid_search(self) -> bool:
        """Test hybrid search endpoint (Neo4j + Qdrant)"""
        try:
            logger.info("🧪 Testing hybrid search endpoint...")
            response = self.session.get(f"{self.base_url}/api/search/hybrid?query=medical&limit=3")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Hybrid search test passed")
                logger.info(f"   Found {len(data.get('data', []))} results")
                return True
            else:
                logger.error(f"❌ Hybrid search test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Hybrid search test error: {e}")
            return False
    
    def test_search_stats(self) -> bool:
        """Test search statistics endpoint"""
        try:
            logger.info("🧪 Testing search stats endpoint...")
            response = self.session.get(f"{self.base_url}/api/search/stats")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Search stats test passed")
                logger.info(f"   Stats: {data.get('data', {})}")
                return True
            else:
                logger.error(f"❌ Search stats test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Search stats test error: {e}")
            return False
    
    def test_message_details(self) -> bool:
        """Test message details endpoint"""
        try:
            logger.info("🧪 Testing message details endpoint...")
            # First get a message ID from conversations
            response = self.session.get(f"{self.base_url}/api/conversations?limit=1")
            if response.status_code != 200:
                logger.error("❌ Could not get conversations for message test")
                return False
            
            conversations = response.json().get('data', [])
            if not conversations:
                logger.error("❌ No conversations found for message test")
                return False
            
            # Get messages for the first conversation
            chat_id = conversations[0].get('chat_id')
            response = self.session.get(f"{self.base_url}/api/conversations/{chat_id}/messages?limit=1")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Message details test passed")
                logger.info(f"   Found {len(data.get('data', []))} messages")
                return True
            else:
                logger.error(f"❌ Message details test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Message details test error: {e}")
            return False
    
    def test_chunk_details(self) -> bool:
        """Test chunk details endpoint"""
        try:
            logger.info("🧪 Testing chunk details endpoint...")
            # Get a chunk ID from semantic search
            response = self.session.get(f"{self.base_url}/api/search/semantic?query=test&limit=1")
            if response.status_code != 200:
                logger.error("❌ Could not get chunks for chunk test")
                return False
            
            chunks = response.json().get('data', [])
            if not chunks:
                logger.error("❌ No chunks found for chunk test")
                return False
            
            chunk_id = chunks[0].get('chunk_id')
            response = self.session.get(f"{self.base_url}/api/chunks/{chunk_id}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Chunk details test passed")
                logger.info(f"   Chunk: {data.get('data', {}).get('chunk_id', 'unknown')}")
                return True
            else:
                logger.error(f"❌ Chunk details test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Chunk details test error: {e}")
            return False
    
    def test_graph_visualization(self) -> bool:
        """Test graph visualization endpoint"""
        try:
            logger.info("🧪 Testing graph visualization endpoint...")
            response = self.session.get(f"{self.base_url}/api/graph/visualization?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Graph visualization test passed")
                logger.info(f"   Nodes: {len(data.get('data', {}).get('nodes', []))}")
                logger.info(f"   Edges: {len(data.get('data', {}).get('edges', []))}")
                return True
            else:
                logger.error(f"❌ Graph visualization test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Graph visualization test error: {e}")
            return False
    
    def test_search_by_tags(self) -> bool:
        """Test search by tags endpoint"""
        try:
            logger.info("🧪 Testing search by tags endpoint...")
            response = self.session.get(f"{self.base_url}/api/search/tags?tags=health,medical&limit=3")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Search by tags test passed")
                logger.info(f"   Found {len(data.get('data', []))} results")
                return True
            else:
                logger.error(f"❌ Search by tags test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Search by tags test error: {e}")
            return False
    
    def test_search_by_domain(self) -> bool:
        """Test search by domain endpoint"""
        try:
            logger.info("🧪 Testing search by domain endpoint...")
            response = self.session.get(f"{self.base_url}/api/search/domain/health?limit=3")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Search by domain test passed")
                logger.info(f"   Found {len(data.get('data', []))} results")
                return True
            else:
                logger.error(f"❌ Search by domain test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Search by domain test error: {e}")
            return False
    
    def test_similar_content(self) -> bool:
        """Test similar content search endpoint"""
        try:
            logger.info("🧪 Testing similar content search endpoint...")
            # First get a chunk ID from semantic search
            response = self.session.get(f"{self.base_url}/api/search/semantic?query=health&limit=1")
            if response.status_code != 200:
                logger.error("❌ Could not get chunk for similar content test")
                return False
            
            chunks = response.json().get('data', [])
            if not chunks:
                logger.error("❌ No chunks found for similar content test")
                return False
            
            chunk_id = chunks[0].get('chunk_id')
            response = self.session.get(f"{self.base_url}/api/search/similar/{chunk_id}?limit=3")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Similar content search test passed")
                logger.info(f"   Found {len(data.get('data', []))} similar results")
                return True
            else:
                logger.error(f"❌ Similar content search test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Similar content search test error: {e}")
            return False
    
    def test_available_tags(self) -> bool:
        """Test available tags endpoint"""
        try:
            logger.info("🧪 Testing available tags endpoint...")
            response = self.session.get(f"{self.base_url}/api/search/tags/available")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Available tags test passed")
                logger.info(f"   Found {len(data.get('data', []))} tags")
                return True
            else:
                logger.error(f"❌ Available tags test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Available tags test error: {e}")
            return False
    
    def test_api_docs(self) -> bool:
        """Test that API docs are accessible"""
        try:
            logger.info("🧪 Testing API docs...")
            response = self.session.get(f"{self.base_url}/docs")
            
            if response.status_code == 200:
                logger.info("✅ API docs test passed")
                return True
            else:
                logger.error(f"❌ API docs test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ API docs test error: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        logger.info("🚀 Starting Simple API Tests...")
        logger.info(f"Base URL: {self.base_url}")
        logger.info("=" * 50)
        
        tests = {
            "health_check": self.test_health_check,
            "graph_data": self.test_graph_data_simple,
            "conversations": self.test_conversations_list,
            "simple_search": self.test_simple_search,
            "semantic_search": self.test_semantic_search,
            "hybrid_search": self.test_hybrid_search,
            "search_stats": self.test_search_stats,
            "message_details": self.test_message_details,
            "chunk_details": self.test_chunk_details,
            "graph_visualization": self.test_graph_visualization,
            "search_by_tags": self.test_search_by_tags,
            "search_by_domain": self.test_search_by_domain,
            "similar_content": self.test_similar_content,
            "available_tags": self.test_available_tags,
            "api_docs": self.test_api_docs
        }
        
        results = {}
        for test_name, test_func in tests.items():
            logger.info(f"\n📋 Running: {test_name}")
            results[test_name] = test_func()
            time.sleep(0.5)  # Small delay between tests
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 50)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {test_name}")
        
        logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! API is working correctly.")
        else:
            logger.info("⚠️  Some tests failed. API needs work.")
        
        return results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Simple ChatMind API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tester = SimpleAPITester(args.url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main() 