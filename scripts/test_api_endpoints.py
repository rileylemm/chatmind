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
    """Test all ChatMind API endpoints with hybrid Neo4j + Qdrant architecture."""
    
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
            endpoint="/api/health",
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
                "name": "Graph Data (Raw Layer)",
                "params": {"layer": "raw", "limit": 5},
                "description": "Get raw layer graph data (Chats and Messages)"
            },
            {
                "name": "Graph Data (Chunk Layer)",
                "params": {"layer": "chunk", "limit": 5},
                "description": "Get chunk layer graph data (Chunks and Clusters)"
            },
            {
                "name": "Graph Data (Both Layers)",
                "params": {"layer": "both", "limit": 10},
                "description": "Get both layers graph data"
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
                "name": "Search (Health)",
                "params": {"query": "health", "limit": 5},
                "description": "Search for health-related content"
            },
            {
                "name": "Search (Medical)",
                "params": {"query": "medical", "limit": 3},
                "description": "Search for medical-related content"
            },
            {
                "name": "Search (Technology)",
                "params": {"query": "technology", "limit": 3},
                "description": "Search for technology-related content"
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
    
    def test_discovery_endpoints(self):
        """Test discovery endpoints."""
        tests = [
            {
                "name": "Discover Topics (Default)",
                "endpoint": "/api/discover/topics",
                "params": {},
                "description": "Get most discussed topics with default parameters"
            },
            {
                "name": "Discover Topics (Limited)",
                "endpoint": "/api/discover/topics",
                "params": {"limit": 5},
                "description": "Get limited number of topics"
            },
            {
                "name": "Discover Topics (With Min Count)",
                "endpoint": "/api/discover/topics",
                "params": {"limit": 10, "min_count": 1},
                "description": "Get topics with minimum count filter"
            },
            {
                "name": "Discover Domains",
                "endpoint": "/api/discover/domains",
                "params": {},
                "description": "Get domain distribution and insights"
            },
            {
                "name": "Discover Clusters (Default)",
                "endpoint": "/api/discover/clusters",
                "params": {},
                "description": "Get semantic clusters with positioning"
            },
            {
                "name": "Discover Clusters (Limited)",
                "endpoint": "/api/discover/clusters",
                "params": {"limit": 5},
                "description": "Get limited number of clusters"
            },
            {
                "name": "Discover Clusters (With Min Size)",
                "endpoint": "/api/discover/clusters",
                "params": {"limit": 10, "min_size": 1},
                "description": "Get clusters with minimum size filter"
            },
            {
                "name": "Discover Clusters (No Positioning)",
                "endpoint": "/api/discover/clusters",
                "params": {"include_positioning": "false"},
                "description": "Get clusters without positioning data"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint=test["endpoint"],
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_hybrid_search_endpoints(self):
        """Test hybrid search endpoints."""
        tests = [
            {
                "name": "Hybrid Semantic Search (Health)",
                "endpoint": "/api/search/semantic",
                "params": {"query": "health", "limit": 5},
                "description": "Hybrid semantic search for health content"
            },
            {
                "name": "Hybrid Semantic Search (Medical)",
                "endpoint": "/api/search/semantic",
                "params": {"query": "medical", "limit": 3},
                "description": "Hybrid semantic search for medical content"
            },
            {
                "name": "Hybrid Semantic Search (Symptoms)",
                "endpoint": "/api/search/semantic",
                "params": {"query": "symptoms", "limit": 5},
                "description": "Hybrid semantic search for symptoms content"
            },
            {
                "name": "Hybrid Semantic Search (With Domain Filter)",
                "endpoint": "/api/search/semantic",
                "params": {"query": "technology", "domain": "technology", "limit": 5},
                "description": "Hybrid semantic search with domain filter"
            },
            {
                "name": "Hybrid Semantic Search (With Tags Filter)",
                "endpoint": "/api/search/semantic",
                "params": {"query": "programming", "tags": "python,technology", "limit": 5},
                "description": "Hybrid semantic search with tags filter"
            },
            {
                "name": "Search by Domain (Technology)",
                "endpoint": "/api/search/domain/technology",
                "params": {"limit": 5},
                "description": "Search by domain with graph context"
            },
            {
                "name": "Search by Domain (Health)",
                "endpoint": "/api/search/domain/health",
                "params": {"limit": 5},
                "description": "Search by health domain with graph context"
            },
            {
                "name": "Search by Tags (Python)",
                "endpoint": "/api/search/tags",
                "params": {"tags": "python", "limit": 5},
                "description": "Search by tags with graph context"
            },
            {
                "name": "Search by Tags (Multiple)",
                "endpoint": "/api/search/tags",
                "params": {"tags": "python,technology", "limit": 5},
                "description": "Search by multiple tags with graph context"
            },
            {
                "name": "Search Statistics",
                "endpoint": "/api/search/stats",
                "params": {},
                "description": "Get search statistics and database info"
            },
            {
                "name": "Available Domains",
                "endpoint": "/api/search/domains",
                "params": {},
                "description": "Get list of available domains for filtering"
            },
            {
                "name": "Available Tags",
                "endpoint": "/api/search/tags/available",
                "params": {},
                "description": "Get list of available tags for filtering"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint=test["endpoint"],
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_graph_exploration_endpoints(self):
        """Test graph exploration endpoints."""
        tests = [
            {
                "name": "Graph Visualization (Default)",
                "endpoint": "/api/graph/visualization",
                "params": {},
                "description": "Get default visualization data"
            },
            {
                "name": "Graph Visualization (Limited)",
                "endpoint": "/api/graph/visualization",
                "params": {"limit": 10},
                "description": "Get limited visualization data"
            },
            {
                "name": "Graph Visualization (Chats Only)",
                "endpoint": "/api/graph/visualization",
                "params": {"node_types": "Chat", "limit": 5},
                "description": "Get only chat nodes for visualization"
            },
            {
                "name": "Graph Visualization (No Edges)",
                "endpoint": "/api/graph/visualization",
                "params": {"include_edges": "false", "limit": 5},
                "description": "Get visualization data without edges"
            },

            {
                "name": "Graph Neighbors (Default)",
                "endpoint": "/api/graph/neighbors",
                "params": {"node_id": "test_chat", "limit": 5},
                "description": "Get neighbors of test chat"
            },
            {
                "name": "Graph Neighbors (High Similarity)",
                "endpoint": "/api/graph/neighbors",
                "params": {"node_id": "test_chat", "min_similarity": 0.8, "limit": 3},
                "description": "Get neighbors with high similarity threshold"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint=test["endpoint"],
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_conversation_context(self):
        """Test conversation context endpoint."""
        # First get a chat ID to test with
        try:
            response = self.session.get(f"{self.base_url}/api/chats?limit=1")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    chat_id = data["data"][0]["id"]
                    
                    return self.test_endpoint(
                        name="Conversation Context",
                        method="GET",
                        endpoint=f"/api/conversations/{chat_id}/context",
                        description=f"Get conversation context for chat {chat_id}"
                    )
                else:
                    logger.warning("No chats available for testing conversation context endpoint")
                    return {
                        "name": "Conversation Context",
                        "status": "SKIPPED",
                        "error": "No chats available",
                        "description": "Skipped due to no available chats"
                    }
            else:
                logger.warning("Could not fetch chats for testing conversation context endpoint")
                return {
                    "name": "Conversation Context", 
                    "status": "SKIPPED",
                    "error": "Could not fetch chats",
                    "description": "Skipped due to API error"
                }
        except Exception as e:
            logger.warning(f"Error preparing conversation context test: {e}")
            return {
                "name": "Conversation Context",
                "status": "SKIPPED", 
                "error": str(e),
                "description": "Skipped due to preparation error"
            }
    
    def test_similar_content_search(self):
        """Test similar content search endpoint."""
        # First get a chunk ID to test with
        try:
            response = self.session.get(f"{self.base_url}/api/chunks?limit=1")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    chunk_id = data["data"][0]["chunk_id"]
                    
                    return self.test_endpoint(
                        name="Similar Content Search",
                        method="GET",
                        endpoint=f"/api/search/similar/{chunk_id}",
                        params={"limit": 5},
                        description=f"Find similar content for chunk {chunk_id}"
                    )
                else:
                    logger.warning("No chunks available for testing similar content search endpoint")
                    return {
                        "name": "Similar Content Search",
                        "status": "SKIPPED",
                        "error": "No chunks available",
                        "description": "Skipped due to no available chunks"
                    }
            else:
                logger.warning("Could not fetch chunks for testing similar content search endpoint")
                return {
                    "name": "Similar Content Search", 
                    "status": "SKIPPED",
                    "error": "Could not fetch chunks",
                    "description": "Skipped due to API error"
                }
        except Exception as e:
            logger.warning(f"Error preparing similar content search test: {e}")
            return {
                "name": "Similar Content Search",
                "status": "SKIPPED", 
                "error": str(e),
                "description": "Skipped due to preparation error"
            }
    
    def test_semantic_chunks(self):
        """Test semantic chunks endpoint."""
        tests = [
            {
                "name": "Semantic Chunks (Default)",
                "params": {},
                "description": "Get default semantic chunks"
            },
            {
                "name": "Semantic Chunks (Limited)",
                "params": {"limit": 5},
                "description": "Get limited semantic chunks"
            },
            {
                "name": "Semantic Chunks (By Cluster)",
                "params": {"cluster_id": 0, "limit": 5},
                "description": "Get semantic chunks for specific cluster"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint="/api/chunks",
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_analytics_endpoints(self):
        """Test analytics endpoints."""
        tests = [
            {
                "name": "Analytics Patterns (Default)",
                "endpoint": "/api/analytics/patterns",
                "params": {},
                "description": "Get conversation pattern analysis"
            },
            {
                "name": "Analytics Patterns (Monthly)",
                "endpoint": "/api/analytics/patterns",
                "params": {"timeframe": "monthly"},
                "description": "Get monthly pattern analysis"
            },
            {
                "name": "Analytics Patterns (With Sentiment)",
                "endpoint": "/api/analytics/patterns",
                "params": {"include_sentiment": "true"},
                "description": "Get pattern analysis with sentiment"
            },
            {
                "name": "Analytics Sentiment (Default)",
                "endpoint": "/api/analytics/sentiment",
                "params": {},
                "description": "Get sentiment analysis"
            },
            {
                "name": "Analytics Sentiment (Date Range)",
                "endpoint": "/api/analytics/sentiment",
                "params": {
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31"
                },
                "description": "Get sentiment analysis for date range"
            },
            {
                "name": "Analytics Sentiment (Grouped by Domain)",
                "endpoint": "/api/analytics/sentiment",
                "params": {"group_by": "domain"},
                "description": "Get sentiment analysis grouped by domain"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint=test["endpoint"],
                params=test["params"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_api_docs(self):
        """Test that API documentation is accessible"""
        tests = [
            {
                "name": "Swagger UI Documentation",
                "endpoint": "/docs",
                "description": "Check that Swagger UI documentation is accessible"
            },
            {
                "name": "ReDoc Documentation",
                "endpoint": "/redoc",
                "description": "Check that ReDoc documentation is accessible"
            }
        ]
        
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint=test["endpoint"],
                description=test["description"]
            )
            results.append(result)
        
        return results
    
    def test_connection_discovery_endpoints(self):
        """Test connection discovery endpoints."""
        # First get some chat IDs to test with
        try:
            response = self.session.get(f"{self.base_url}/api/chats?limit=3")
            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) >= 2:
                    chat1_id = data["data"][0]["id"]
                    chat2_id = data["data"][1]["id"]
                    
                    tests = [
                        {
                            "name": "Connection Explanation",
                            "endpoint": f"/api/connections/explain",
                            "params": {"source_id": chat1_id, "target_id": chat2_id},
                            "description": f"Explain connection between chats {chat1_id} and {chat2_id}"
                        },
                        {
                            "name": "Cross-Domain Search (Health)",
                            "endpoint": "/api/search/cross-domain",
                            "params": {"query": "stress", "limit": 5},
                            "description": "Find stress across different domains"
                        },
                        {
                            "name": "Cross-Domain Search (Technology)",
                            "endpoint": "/api/search/cross-domain",
                            "params": {"query": "python", "limit": 3},
                            "description": "Find python across different domains"
                        },
                        {
                            "name": "Discovery Suggestions (Default)",
                            "endpoint": "/api/discover/suggestions",
                            "params": {"limit": 3},
                            "description": "Get discovery suggestions"
                        },
                        {
                            "name": "Discovery Suggestions (Limited)",
                            "endpoint": "/api/discover/suggestions",
                            "params": {"limit": 1},
                            "description": "Get limited discovery suggestions"
                        },
                        {
                            "name": "Timeline Semantic (Default)",
                            "endpoint": "/api/timeline/semantic",
                            "params": {},
                            "description": "Get timeline with semantic connections"
                        },
                        {
                            "name": "Timeline Semantic (Date Range)",
                            "endpoint": "/api/timeline/semantic",
                            "params": {
                                "start_date": "2025-01-01",
                                "end_date": "2025-01-31"
                            },
                            "description": "Get timeline with semantic connections for date range"
                        }
                    ]
                    
                    results = []
                    for test in tests:
                        result = self.test_endpoint(
                            name=test["name"],
                            method="GET",
                            endpoint=test["endpoint"],
                            params=test["params"],
                            description=test["description"]
                        )
                        results.append(result)
                    
                    return results
                else:
                    logger.warning("Not enough chats available for testing connection discovery endpoints")
                    return [{
                        "name": "Connection Discovery Endpoints",
                        "status": "SKIPPED",
                        "error": "Not enough chats available",
                        "description": "Skipped due to insufficient data"
                    }]
            else:
                logger.warning("Could not fetch chats for testing connection discovery endpoints")
                return [{
                    "name": "Connection Discovery Endpoints",
                    "status": "SKIPPED",
                    "error": "Could not fetch chats",
                    "description": "Skipped due to API error"
                }]
        except Exception as e:
            logger.warning(f"Error preparing connection discovery tests: {e}")
            return [{
                "name": "Connection Discovery Endpoints",
                "status": "SKIPPED",
                "error": str(e),
                "description": "Skipped due to preparation error"
            }]
    
    def test_bridges(self):
        """Test discovery bridges endpoint (serendipitous connectors)."""
        tests = [
            {
                "name": "Discover Bridges (Default)",
                "endpoint": "/api/discover/bridges",
                "params": {"limit": 5},
                "description": "Get bridge nodes connecting clusters"
            },
            {
                "name": "Discover Bridges (Domain Pair)",
                "endpoint": "/api/discover/bridges",
                "params": {"domain_a": "technology", "domain_b": "health", "limit": 5},
                "description": "Get bridges between technology and health"
            }
        ]
        results = []
        for test in tests:
            result = self.test_endpoint(
                name=test["name"],
                method="GET",
                endpoint=test["endpoint"],
                params=test["params"],
                description=test["description"],
            )
            results.append(result)
        return results

    def test_explain_path(self):
        """Test explainability endpoint between two chats."""
        try:
            # Fetch two chats to explain a path between
            resp = self.session.get(f"{self.base_url}/api/chats?limit=2", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data") and len(data["data"]) >= 2:
                    chat1 = data["data"][0]["id"]
                    chat2 = data["data"][1]["id"]
                    return self.test_endpoint(
                        name="Explain Path (Chat→Chat)",
                        method="GET",
                        endpoint=f"/api/explain/path",
                        params={"source_id": chat1, "target_id": chat2, "max_hops": 2},
                        description=f"Explain connection between chats {chat1} and {chat2}",
                    )
                else:
                    logger.warning("Not enough chats for explain path test")
                    return {"name": "Explain Path (Chat→Chat)", "status": "SKIPPED", "error": "Insufficient chats", "description": "Skipped"}
            else:
                return {"name": "Explain Path (Chat→Chat)", "status": "SKIPPED", "error": "Chats endpoint unavailable", "description": "Skipped"}
        except Exception as e:
            return {"name": "Explain Path (Chat→Chat)", "status": "SKIPPED", "error": str(e), "description": "Skipped due to prep error"}

    def test_evolution_cluster(self):
        """Test cluster evolution endpoint (timeline lens)."""
        try:
            # Fetch a cluster/topic id
            resp = self.session.get(f"{self.base_url}/api/discover/clusters?limit=1", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("data") or []
                if items:
                    cluster_id = items[0].get("cluster_id") or items[0].get("id") or items[0].get("topic_id")
                    return self.test_endpoint(
                        name="Cluster Evolution",
                        method="GET",
                        endpoint=f"/api/evolution/cluster/{cluster_id}",
                        params={"granularity": "week"},
                        description=f"Evolution timeline for cluster {cluster_id}",
                    )
                else:
                    return {"name": "Cluster Evolution", "status": "SKIPPED", "error": "No clusters available", "description": "Skipped"}
            else:
                return {"name": "Cluster Evolution", "status": "SKIPPED", "error": "Clusters endpoint unavailable", "description": "Skipped"}
        except Exception as e:
            return {"name": "Cluster Evolution", "status": "SKIPPED", "error": str(e), "description": "Skipped due to prep error"}

    def test_serendipity(self):
        """Test serendipity endpoint (novel but relevant recommendations)."""
        try:
            # Use a chat id as seed
            resp = self.session.get(f"{self.base_url}/api/chats?limit=1", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data"):
                    chat_id = data["data"][0]["id"]
                    return self.test_endpoint(
                        name="Serendipity Recommendations",
                        method="GET",
                        endpoint=f"/api/serendipity",
                        params={"seed_id": chat_id, "type": "chat", "novelty": 0.7, "limit": 5},
                        description=f"Serendipity items seeded by chat {chat_id}",
                    )
                else:
                    return {"name": "Serendipity Recommendations", "status": "SKIPPED", "error": "No chats available", "description": "Skipped"}
            else:
                return {"name": "Serendipity Recommendations", "status": "SKIPPED", "error": "Chats endpoint unavailable", "description": "Skipped"}
        except Exception as e:
            return {"name": "Serendipity Recommendations", "status": "SKIPPED", "error": str(e), "description": "Skipped due to prep error"}

    def test_compare(self):
        """Test compare endpoint (side-by-side)."""
        try:
            # Get two chats
            resp = self.session.get(f"{self.base_url}/api/chats?limit=2", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data") and len(data["data"]) >= 2:
                    ids = [data["data"][0]["id"], data["data"][1]["id"]]
                    # POST /api/compare
                    try:
                        response = self.session.post(
                            f"{self.base_url}/api/compare",
                            json={"type": "chat", "ids": ids},
                            headers={"Content-Type": "application/json"},
                            timeout=10,
                        )
                        status = "PASSED" if response.status_code == 200 else "FAILED"
                        error = None if status == "PASSED" else f"Expected 200, got {response.status_code}"
                        try:
                            data = response.json()
                            response_size = len(json.dumps(data))
                        except json.JSONDecodeError:
                            data = {"raw_response": response.text[:200]}
                            response_size = len(response.text)
                        result = {
                            "name": "Compare (Chats)",
                            "method": "POST",
                            "url": f"{self.base_url}/api/compare",
                            "status": status,
                            "status_code": response.status_code,
                            "expected_status": 200,
                            "response_size": response_size,
                            "error": error,
                            "description": f"Compare chats {ids}",
                            "data_keys": list(data.keys()) if isinstance(data, dict) else None,
                        }
                        self.results.append(result)
                        if status == "PASSED":
                            logger.info("✅ Compare (Chats): PASSED")
                        else:
                            logger.error(f"❌ Compare (Chats): FAILED - {error}")
                        return result
                    except requests.exceptions.RequestException as e:
                        err = f"Request failed: {str(e)}"
                        logger.error(f"❌ Compare (Chats): FAILED - {err}")
                        result = {
                            "name": "Compare (Chats)",
                            "method": "POST",
                            "url": f"{self.base_url}/api/compare",
                            "status": "FAILED",
                            "status_code": None,
                            "expected_status": 200,
                            "response_size": 0,
                            "error": err,
                            "description": f"Compare chats {ids}",
                            "data_keys": None,
                        }
                        self.results.append(result)
                        return result
                else:
                    return {"name": "Compare (Chats)", "status": "SKIPPED", "error": "Insufficient chats", "description": "Skipped"}
            else:
                return {"name": "Compare (Chats)", "status": "SKIPPED", "error": "Chats endpoint unavailable", "description": "Skipped"}
        except Exception as e:
            return {"name": "Compare (Chats)", "status": "SKIPPED", "error": str(e), "description": "Skipped due to prep error"}
    
    def run_all_tests(self):
        """Run all API endpoint tests."""
        logger.info("🚀 Starting ChatMind API Endpoint Tests...")
        logger.info("Architecture: Hybrid Neo4j + Qdrant")
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
        
        # Test semantic chunks
        logger.info("\n📝 Testing Semantic Chunks Endpoint...")
        self.test_semantic_chunks()
        
        # Test chats
        logger.info("\n💬 Testing Chats Endpoints...")
        self.test_chats()
        
        # Test chat messages
        logger.info("\n📝 Testing Chat Messages Endpoint...")
        self.test_chat_messages()
        
        # Test search
        logger.info("\n🔍 Testing Search Endpoints...")
        self.test_search()
        

        
        # Test new endpoints
        logger.info("\n🏷️  Testing Tags Endpoint...")
        self.test_tags()
        

        
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
        
        # Test new discovery endpoints
        logger.info("\n🔍 Testing Discovery Endpoints...")
        self.test_discovery_endpoints()
        
        # Test hybrid search endpoints
        logger.info("\n🔍 Testing Hybrid Search Endpoints...")
        self.test_hybrid_search_endpoints()
        
        # Test conversation context
        logger.info("\n💬 Testing Conversation Context Endpoint...")
        self.test_conversation_context()
        
        # Test similar content search
        logger.info("\n🔍 Testing Similar Content Search Endpoint...")
        self.test_similar_content_search()
        
        # Test new graph exploration endpoints
        logger.info("\n🌐 Testing Graph Exploration Endpoints...")
        self.test_graph_exploration_endpoints()
        
        # Test new analytics endpoints
        logger.info("\n📊 Testing Analytics Endpoints...")
        self.test_analytics_endpoints()
        
        # Test API documentation
        logger.info("\n📚 Testing API Documentation...")
        self.test_api_docs()
        
        # Test new connection discovery endpoints
        logger.info("\n🔗 Testing Connection Discovery Endpoints...")
        self.test_connection_discovery_endpoints()

        # Test new discovery/insight endpoints
        logger.info("\n🔗 Testing New Discovery/Insight Endpoints...")
        self.test_bridges()
        self.test_explain_path()
        self.test_evolution_cluster()
        self.test_serendipity()
        self.test_compare()
        
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
    
    parser = argparse.ArgumentParser(description="Test ChatMind API endpoints with hybrid architecture")
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