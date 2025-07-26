#!/usr/bin/env python3
"""
ChatMind API Endpoint Test Script

Tests all API endpoints documented in the API guide to ensure they're working correctly.
"""

import requests
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ChatMindAPITester:
    """Test all ChatMind API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results = []
        
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     params: Optional[Dict] = None, 
                     expected_status: int = 200,
                     description: str = "") -> Dict[str, Any]:
        """Test a single API endpoint."""
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Testing {name}...")
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=10)
            else:
                logger.error(f"Unsupported method: {method}")
                return {
                    "name": name,
                    "status": "FAILED",
                    "error": f"Unsupported method: {method}",
                    "description": description
                }
            
            # Check status code
            if response.status_code == expected_status:
                status = "PASSED"
                error = None
            else:
                status = "FAILED"
                error = f"Expected status {expected_status}, got {response.status_code}"
            
            # Try to parse JSON response
            try:
                data = response.json()
                response_size = len(json.dumps(data))
            except json.JSONDecodeError:
                data = {"raw_response": response.text[:200]}
                response_size = len(response.text)
            
            result = {
                "name": name,
                "method": method,
                "url": url,
                "status": status,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_size": response_size,
                "error": error,
                "description": description,
                "data_keys": list(data.keys()) if isinstance(data, dict) else None
            }
            
            if status == "PASSED":
                logger.info(f"✅ {name}: PASSED")
            else:
                logger.error(f"❌ {name}: FAILED - {error}")
            
            self.results.append(result)
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(f"❌ {name}: FAILED - {error_msg}")
            
            result = {
                "name": name,
                "method": method,
                "url": url,
                "status": "FAILED",
                "status_code": None,
                "expected_status": expected_status,
                "response_size": 0,
                "error": error_msg,
                "description": description,
                "data_keys": None
            }
            
            self.results.append(result)
            return result
    
    def test_health_check(self):
        """Test health check endpoint."""
        return self.test_endpoint(
            name="Health Check",
            method="GET",
            endpoint="/health",
            description="Check API health and connectivity"
        )
    
    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint."""
        return self.test_endpoint(
            name="Dashboard Statistics",
            method="GET",
            endpoint="/api/stats/dashboard",
            description="Get real-time dashboard statistics"
        )
    
    def test_graph_data(self):
        """Test graph data endpoint with various parameters."""
        tests = [
            {
                "name": "Graph Data (Default)",
                "params": {},
                "description": "Get default graph data"
            },
            {
                "name": "Graph Data (Limited)",
                "params": {"limit": 10},
                "description": "Get limited graph data"
            },
            {
                "name": "Graph Data (Topics Only)",
                "params": {"node_types": "Topic", "limit": 5},
                "description": "Get only topic nodes"
            },
            {
                "name": "Graph Data (With Positioning)",
                "params": {"use_semantic_positioning": "true"},
                "description": "Get graph data with UMAP positioning"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint="/api/graph",
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_topics(self):
        """Test topics endpoint."""
        return self.test_endpoint(
            name="Topics",
            method="GET",
            endpoint="/api/topics",
            description="Get all semantic topics/clusters"
        )
    
    def test_chats(self):
        """Test chats endpoint with various parameters."""
        tests = [
            {
                "name": "Chats (Default)",
                "params": {},
                "description": "Get default chat list"
            },
            {
                "name": "Chats (Limited)",
                "params": {"limit": 5},
                "description": "Get limited chat list"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint="/api/chats",
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_chat_messages(self):
        """Test chat messages endpoint."""
        # First get a chat ID to test with
        try:
            response = self.session.get(f"{self.base_url}/api/chats?limit=1")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    chat_id = data["data"][0]["id"]
                    
                    return self.test_endpoint(
                        name="Chat Messages",
                        method="GET",
                        endpoint=f"/api/chats/{chat_id}/messages",
                        params={"limit": 5},
                        description=f"Get messages for chat {chat_id}"
                    )
                else:
                    logger.warning("No chats available for testing messages endpoint")
                    return {
                        "name": "Chat Messages",
                        "status": "SKIPPED",
                        "error": "No chats available",
                        "description": "Skipped due to no available chats"
                    }
            else:
                logger.warning("Could not fetch chats for testing messages endpoint")
                return {
                    "name": "Chat Messages", 
                    "status": "SKIPPED",
                    "error": "Could not fetch chats",
                    "description": "Skipped due to API error"
                }
        except Exception as e:
            logger.warning(f"Error preparing chat messages test: {e}")
            return {
                "name": "Chat Messages",
                "status": "SKIPPED", 
                "error": str(e),
                "description": "Skipped due to preparation error"
            }
    
    def test_search(self):
        """Test search endpoint with various queries."""
        tests = [
            {
                "name": "Search (Python)",
                "params": {"query": "python", "limit": 5},
                "description": "Search for Python-related content"
            },
            {
                "name": "Search (AI)",
                "params": {"query": "AI", "limit": 3},
                "description": "Search for AI-related content"
            },
            {
                "name": "Search (Empty Query)",
                "params": {"query": "", "limit": 1},
                "description": "Test search with empty query"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint="/api/search",
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_cost_statistics(self):
        """Test cost statistics endpoint with various parameters."""
        tests = [
            {
                "name": "Cost Statistics (Default)",
                "params": {},
                "description": "Get all cost statistics"
            },
            {
                "name": "Cost Statistics (Date Range)",
                "params": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31"
                },
                "description": "Get cost statistics for specific date range"
            },
            {
                "name": "Cost Statistics (Operation Filter)",
                "params": {"operation": "tagging"},
                "description": "Get cost statistics for tagging operation"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint="/api/costs/statistics",
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_tags(self):
        """Test tags endpoint."""
        return self.test_endpoint(
            name="Tags",
            method="GET",
            endpoint="/api/tags",
            description="Get all tags with counts and categories"
        )
    
    def test_single_message(self):
        """Test single message endpoint."""
        # First get a message ID to test with
        try:
            # Try multiple search terms that might exist in the data
            search_terms = ["health", "medical", "cooking", "food", "symptoms", "mono"]
            
            for term in search_terms:
                response = self.session.get(f"{self.base_url}/api/search?query={term}&limit=1")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("data") and len(data["data"]) > 0:
                        message_id = data["data"][0]["id"]
                        
                        return self.test_endpoint(
                            name="Single Message",
                            method="GET",
                            endpoint=f"/api/messages/{message_id}",
                            description=f"Get message {message_id} (found via '{term}' search)"
                        )
            
            logger.warning("No messages available for testing single message endpoint")
            return {
                "name": "Single Message",
                "status": "SKIPPED",
                "error": "No messages available",
                "description": "Skipped due to no available messages"
            }
        except Exception as e:
            logger.warning(f"Error preparing single message test: {e}")
            return {
                "name": "Single Message",
                "status": "SKIPPED", 
                "error": str(e),
                "description": "Skipped due to preparation error"
            }
    
    def test_cluster_details(self):
        """Test cluster details endpoint."""
        # First get a cluster ID to test with
        try:
            response = self.session.get(f"{self.base_url}/api/topics")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    # Use the first available cluster ID (prefer topic_id, fallback to id)
                    topic = data["data"][0]
                    cluster_id = topic.get("topic_id") or topic.get("id")
                    
                    return self.test_endpoint(
                        name="Cluster Details",
                        method="GET",
                        endpoint=f"/api/clusters/{cluster_id}",
                        description=f"Get details for cluster {cluster_id}"
                    )
                else:
                    logger.warning("No clusters available for testing cluster details endpoint")
                    return {
                        "name": "Cluster Details",
                        "status": "SKIPPED",
                        "error": "No clusters available",
                        "description": "Skipped due to no available clusters"
                    }
            else:
                logger.warning("Could not fetch clusters for testing cluster details endpoint")
                return {
                    "name": "Cluster Details", 
                    "status": "SKIPPED",
                    "error": "Could not fetch clusters",
                    "description": "Skipped due to API error"
                }
        except Exception as e:
            logger.warning(f"Error preparing cluster details test: {e}")
            return {
                "name": "Cluster Details",
                "status": "SKIPPED", 
                "error": str(e),
                "description": "Skipped due to preparation error"
            }
    
    def test_node_expansion(self):
        """Test node expansion endpoint."""
        # First get a chat ID to test with
        try:
            response = self.session.get(f"{self.base_url}/api/chats?limit=1")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    chat_id = data["data"][0]["id"]
                    
                    return self.test_endpoint(
                        name="Node Expansion",
                        method="GET",
                        endpoint=f"/api/graph/expand/{chat_id}",
                        description=f"Expand node {chat_id}"
                    )
                else:
                    logger.warning("No chats available for testing node expansion endpoint")
                    return {
                        "name": "Node Expansion",
                        "status": "SKIPPED",
                        "error": "No chats available",
                        "description": "Skipped due to no available chats"
                    }
            else:
                logger.warning("Could not fetch chats for testing node expansion endpoint")
                return {
                    "name": "Node Expansion", 
                    "status": "SKIPPED",
                    "error": "Could not fetch chats",
                    "description": "Skipped due to API error"
                }
        except Exception as e:
            logger.warning(f"Error preparing node expansion test: {e}")
            return {
                "name": "Node Expansion",
                "status": "SKIPPED", 
                "error": str(e),
                "description": "Skipped due to preparation error"
            }
    
    def test_advanced_search(self):
        """Test advanced search endpoint."""
        tests = [
            {
                "name": "Advanced Search (Basic)",
                "data": {
                    "query": "python",
                    "filters": {"limit": 5}
                },
                "description": "Basic advanced search with query only"
            },
            {
                "name": "Advanced Search (With Filters)",
                "data": {
                    "query": "AI",
                    "filters": {
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31",
                        "limit": 3
                    }
                },
                "description": "Advanced search with date filters"
            }
        ]
        
        results = []
        for test in tests:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/search/advanced",
                    json=test["data"],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    status = "PASSED"
                    error = None
                else:
                    status = "FAILED"
                    error = f"Expected status 200, got {response.status_code}"
                
                try:
                    data = response.json()
                    response_size = len(json.dumps(data))
                except json.JSONDecodeError:
                    data = {"raw_response": response.text[:200]}
                    response_size = len(response.text)
                
                result = {
                    "name": test["name"],
                    "method": "POST",
                    "url": f"{self.base_url}/api/search/advanced",
                    "status": status,
                    "status_code": response.status_code,
                    "expected_status": 200,
                    "response_size": response_size,
                    "error": error,
                    "description": test["description"],
                    "data_keys": list(data.keys()) if isinstance(data, dict) else None
                }
                
                if status == "PASSED":
                    logger.info(f"✅ {test['name']}: PASSED")
                else:
                    logger.error(f"❌ {test['name']}: FAILED - {error}")
                
                self.results.append(result)
                results.append(result)
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(f"❌ {test['name']}: FAILED - {error_msg}")
                
                result = {
                    "name": test["name"],
                    "method": "POST",
                    "url": f"{self.base_url}/api/search/advanced",
                    "status": "FAILED",
                    "status_code": None,
                    "expected_status": 200,
                    "response_size": 0,
                    "error": error_msg,
                    "description": test["description"],
                    "data_keys": None
                }
                
                self.results.append(result)
                results.append(result)
        
        return results
    
    def test_custom_neo4j_query(self):
        """Test custom Neo4j query endpoint."""
        tests = [
            {
                "name": "Custom Query (Tags)",
                "data": {
                    "query": "MATCH (t:Tag) RETURN t.name, t.count ORDER BY t.count DESC LIMIT 5"
                },
                "description": "Query to get top tags"
            },
            {
                "name": "Custom Query (Topics)",
                "data": {
                    "query": "MATCH (t:Topic) RETURN t.name, t.size ORDER BY t.size DESC LIMIT 3"
                },
                "description": "Query to get top topics"
            }
        ]
        
        results = []
        for test in tests:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/query/neo4j",
                    json=test["data"],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    status = "PASSED"
                    error = None
                else:
                    status = "FAILED"
                    error = f"Expected status 200, got {response.status_code}"
                
                try:
                    data = response.json()
                    response_size = len(json.dumps(data))
                except json.JSONDecodeError:
                    data = {"raw_response": response.text[:200]}
                    response_size = len(response.text)
                
                result = {
                    "name": test["name"],
                    "method": "POST",
                    "url": f"{self.base_url}/api/query/neo4j",
                    "status": status,
                    "status_code": response.status_code,
                    "expected_status": 200,
                    "response_size": response_size,
                    "error": error,
                    "description": test["description"],
                    "data_keys": list(data.keys()) if isinstance(data, dict) else None
                }
                
                if status == "PASSED":
                    logger.info(f"✅ {test['name']}: PASSED")
                else:
                    logger.error(f"❌ {test['name']}: FAILED - {error}")
                
                self.results.append(result)
                results.append(result)
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(f"❌ {test['name']}: FAILED - {error_msg}")
                
                result = {
                    "name": test["name"],
                    "method": "POST",
                    "url": f"{self.base_url}/api/query/neo4j",
                    "status": "FAILED",
                    "status_code": None,
                    "expected_status": 200,
                    "response_size": 0,
                    "error": error_msg,
                    "description": test["description"],
                    "data_keys": None
                }
                
                self.results.append(result)
                results.append(result)
        
        return results
    
    def test_chat_summary(self):
        """Test chat summary endpoint."""
        # First get a chat ID to test with
        try:
            response = self.session.get(f"{self.base_url}/api/chats?limit=5")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    # Use the first available chat (don't check message_count)
                    chat_id = data["data"][0]["id"]
                    
                    try:
                        response = self.session.post(
                            f"{self.base_url}/api/chats/{chat_id}/summary",
                            headers={"Content-Type": "application/json"},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            status = "PASSED"
                            error = None
                        else:
                            status = "FAILED"
                            error = f"Expected status 200, got {response.status_code}"
                        
                        try:
                            data = response.json()
                            response_size = len(json.dumps(data))
                        except json.JSONDecodeError:
                            data = {"raw_response": response.text[:200]}
                            response_size = len(response.text)
                        
                        result = {
                            "name": "Chat Summary",
                            "method": "POST",
                            "url": f"{self.base_url}/api/chats/{chat_id}/summary",
                            "description": f"Generate summary for chat {chat_id}",
                            "status": status,
                            "status_code": response.status_code,
                            "expected_status": 200,
                            "response_size": response_size,
                            "error": error,
                            "data_keys": list(data.keys()) if isinstance(data, dict) else None
                        }
                        
                        if status == "PASSED":
                            logger.info(f"✅ Chat Summary: PASSED")
                        else:
                            logger.error(f"❌ Chat Summary: FAILED - {error}")
                        
                        self.results.append(result)
                        return result
                        
                    except requests.exceptions.RequestException as e:
                        error_msg = f"Request failed: {str(e)}"
                        logger.error(f"❌ Chat Summary: FAILED - {error_msg}")
                        
                        result = {
                            "name": "Chat Summary",
                            "method": "POST",
                            "url": f"{self.base_url}/api/chats/{chat_id}/summary",
                            "status": "FAILED",
                            "status_code": None,
                            "expected_status": 200,
                            "response_size": 0,
                            "error": error_msg,
                            "description": f"Generate summary for chat {chat_id}",
                            "data_keys": None
                        }
                        
                        self.results.append(result)
                        return result
                else:
                    logger.warning("No chats available for testing chat summary endpoint")
                    return {
                        "name": "Chat Summary",
                        "status": "SKIPPED",
                        "error": "No chats available",
                        "description": "Skipped due to no available chats"
                    }
            else:
                logger.warning("Could not fetch chats for testing chat summary endpoint")
                return {
                    "name": "Chat Summary", 
                    "status": "SKIPPED",
                    "error": "Could not fetch chats",
                    "description": "Skipped due to API error"
                }
        except Exception as e:
            logger.warning(f"Error preparing chat summary test: {e}")
            return {
                "name": "Chat Summary",
                "status": "SKIPPED", 
                "error": str(e),
                "description": "Skipped due to preparation error"
            }
    
    def run_all_tests(self):
        """Run all API endpoint tests."""
        logger.info("🚀 Starting ChatMind API Endpoint Tests...")
        logger.info(f"Base URL: {self.base_url}")
        logger.info("=" * 60)
        
        # Test basic connectivity first
        logger.info("\n🔍 Testing Basic Connectivity...")
        self.test_health_check()
        
        # Test core endpoints
        logger.info("\n📊 Testing Core Endpoints...")
        self.test_dashboard_stats()
        
        # Test graph data with various parameters
        logger.info("\n🌐 Testing Graph Data Endpoints...")
        self.test_graph_data()
        
        # Test topics
        logger.info("\n📚 Testing Topics Endpoint...")
        self.test_topics()
        
        # Test chats
        logger.info("\n💬 Testing Chats Endpoints...")
        self.test_chats()
        
        # Test chat messages
        logger.info("\n📝 Testing Chat Messages Endpoint...")
        self.test_chat_messages()
        
        # Test search
        logger.info("\n🔍 Testing Search Endpoints...")
        self.test_search()
        
        # Test cost statistics
        logger.info("\n💰 Testing Cost Statistics Endpoints...")
        self.test_cost_statistics()
        
        # Test new endpoints
        logger.info("\n🏷️  Testing Tags Endpoint...")
        self.test_tags()
        
        logger.info("\n📝 Testing Single Message Endpoint...")
        self.test_single_message()
        
        logger.info("\n📚 Testing Cluster Details Endpoint...")
        self.test_cluster_details()
        
        logger.info("\n🔗 Testing Node Expansion Endpoint...")
        self.test_node_expansion()
        
        logger.info("\n🔍 Testing Advanced Search Endpoint...")
        self.test_advanced_search()
        
        logger.info("\n⚡ Testing Custom Neo4j Query Endpoint...")
        self.test_custom_neo4j_query()
        
        logger.info("\n📋 Testing Chat Summary Endpoint...")
        self.test_chat_summary()
        
        # Generate summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📋 TEST SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASSED"])
        failed_tests = len([r for r in self.results if r["status"] == "FAILED"])
        skipped_tests = len([r for r in self.results if r["status"] == "SKIPPED"])
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"⏭️  Skipped: {skipped_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        # Show failed tests
        if failed_tests > 0:
            logger.info("\n❌ Failed Tests:")
            for result in self.results:
                if result["status"] == "FAILED":
                    logger.info(f"  - {result['name']}: {result['error']}")
        
        # Show skipped tests
        if skipped_tests > 0:
            logger.info("\n⏭️  Skipped Tests:")
            for result in self.results:
                if result["status"] == "SKIPPED":
                    logger.info(f"  - {result['name']}: {result['error']}")
        
        # Show response details for successful tests
        logger.info("\n📊 Response Details (Successful Tests):")
        for result in self.results:
            if result["status"] == "PASSED":
                logger.info(f"  - {result['name']}: {result['response_size']} bytes, keys: {result['data_keys']}")
    
    def save_results(self, filename: str = "api_test_results.json"):
        """Save test results to JSON file."""
        output_path = Path(filename)
        
        # Add metadata
        results_data = {
            "test_run": {
                "timestamp": time.time(),
                "base_url": self.base_url,
                "total_tests": len(self.results)
            },
            "results": self.results
        }
        
        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"📄 Test results saved to: {output_path}")
        return output_path


def main():
    """Main function to run API tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ChatMind API endpoints")
    parser.add_argument(
        "--base-url", 
        default="http://localhost:8000",
        help="Base URL for the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save test results to JSON file"
    )
    parser.add_argument(
        "--output-file",
        default="api_test_results.json",
        help="Output file for test results (default: api_test_results.json)"
    )
    
    args = parser.parse_args()
    
    # Create tester and run tests
    tester = ChatMindAPITester(args.base_url)
    
    try:
        tester.run_all_tests()
        
        if args.save_results:
            tester.save_results(args.output_file)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 