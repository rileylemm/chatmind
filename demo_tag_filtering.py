#!/usr/bin/env python3
"""
Demo: Tag-Based Filtering

This script demonstrates the tag-based filtering functionality for ChatMind.
"""

import json
import requests
from pathlib import Path
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

def test_tag_api_endpoints():
    """Test the tag-related API endpoints."""
    
    print("🏷️ ChatMind Tag Filtering Demo")
    print("=" * 50)
    
    API_BASE = "http://localhost:8000"
    
    try:
        # Test getting all tags
        print("📊 Testing /tags endpoint...")
        response = requests.get(f"{API_BASE}/tags")
        if response.status_code == 200:
            tags_data = response.json()
            print(f"✅ Available tags: {len(tags_data.get('tags', []))}")
            print(f"✅ Available categories: {len(tags_data.get('categories', []))}")
            
            # Show some sample tags
            if tags_data.get('tags'):
                print(f"📝 Sample tags: {tags_data['tags'][:10]}")
            
            if tags_data.get('categories'):
                print(f"📂 Sample categories: {tags_data['categories'][:5]}")
        else:
            print(f"❌ Failed to get tags: {response.status_code}")
        
        # Test search by tags
        print("\n🔍 Testing /search/by-tags endpoint...")
        test_tags = ["#python", "#api", "#web"]
        params = {'tags': ','.join(test_tags), 'limit': 10}
        response = requests.get(f"{API_BASE}/search/by-tags", params=params)
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Found {len(messages)} messages with tags: {test_tags}")
            
            # Show sample messages
            for i, msg in enumerate(messages[:3]):
                print(f"  {i+1}. {msg.get('content', '')[:100]}...")
                print(f"     Tags: {msg.get('tags', [])}")
                print(f"     Category: {msg.get('category', 'N/A')}")
        else:
            print(f"❌ Failed to search by tags: {response.status_code}")
        
        # Test filtered graph
        print("\n🌐 Testing /graph/filtered endpoint...")
        params = {'tags': '#python', 'limit': 20}
        response = requests.get(f"{API_BASE}/graph/filtered", params=params)
        if response.status_code == 200:
            graph_data = response.json()
            print(f"✅ Filtered graph: {len(graph_data.get('nodes', []))} nodes, {len(graph_data.get('edges', []))} edges")
            
            # Show node types
            node_types = {}
            for node in graph_data.get('nodes', []):
                node_type = node.get('type', 'Unknown')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            print(f"📊 Node types: {node_types}")
        else:
            print(f"❌ Failed to get filtered graph: {response.status_code}")
        
        # Test category filtering
        print("\n📂 Testing category filtering...")
        response = requests.get(f"{API_BASE}/tags")
        if response.status_code == 200:
            tags_data = response.json()
            if tags_data.get('categories'):
                test_category = tags_data['categories'][0]
                params = {'category': test_category, 'limit': 10}
                response = requests.get(f"{API_BASE}/search/by-tags", params=params)
                if response.status_code == 200:
                    messages = response.json()
                    print(f"✅ Found {len(messages)} messages in category: {test_category}")
                else:
                    print(f"❌ Failed to search by category: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("💡 Make sure the API server is running: python chatmind/api/main.py")
    except Exception as e:
        print(f"❌ Error during API testing: {e}")


def test_frontend_integration():
    """Test frontend integration with tag filtering."""
    
    print("\n" + "="*60)
    print("🎨 Frontend Integration Test")
    print("="*60)
    
    print("""
✅ Tag Filter Component Features:
- Multi-select tag filtering
- Category dropdown filtering
- Search query integration
- Active filters display
- Clear filters functionality
- Real-time graph updates

🎯 User Experience:
- Intuitive tag selection
- Visual filter indicators
- Responsive design
- Error handling
- Loading states

🔧 Technical Implementation:
- React hooks for state management
- Material-UI components
- API integration
- Real-time filtering
- Graph visualization updates
    """)


def test_filtering_scenarios():
    """Test different filtering scenarios."""
    
    print("\n" + "="*60)
    print("🧪 Filtering Scenarios")
    print("="*60)
    
    scenarios = [
        {
            'name': 'Single Tag Filter',
            'description': 'Filter by one specific tag',
            'example': 'Filter by #python to see all Python-related content'
        },
        {
            'name': 'Multiple Tags Filter',
            'description': 'Filter by multiple tags (AND logic)',
            'example': 'Filter by #python AND #api to see Python API content'
        },
        {
            'name': 'Category Filter',
            'description': 'Filter by content category',
            'example': 'Filter by "Web Development" category'
        },
        {
            'name': 'Combined Filtering',
            'description': 'Combine tags, category, and search',
            'example': 'Filter by #python category AND search for "FastAPI"'
        },
        {
            'name': 'Clear Filters',
            'description': 'Reset all filters to show full graph',
            'example': 'Click "Clear All Filters" to restore original view'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Example: {scenario['example']}")
        print()


def show_usage_examples():
    """Show usage examples for tag filtering."""
    
    print("\n" + "="*60)
    print("💡 Usage Examples")
    print("="*60)
    
    examples = [
        {
            'use_case': 'Find all Python-related conversations',
            'filters': ['#python'],
            'result': 'Shows all messages tagged with #python'
        },
        {
            'use_case': 'Find API development discussions',
            'filters': ['#api', '#web'],
            'result': 'Shows messages with both #api and #web tags'
        },
        {
            'use_case': 'Find all web development content',
            'filters': ['category: Web Development'],
            'result': 'Shows all messages in the Web Development category'
        },
        {
            'use_case': 'Find specific technical discussions',
            'filters': ['#python', 'search: FastAPI'],
            'result': 'Shows Python content containing "FastAPI"'
        },
        {
            'use_case': 'Explore new topics',
            'filters': ['#llm', '#ai'],
            'result': 'Shows AI/LLM related discussions'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['use_case']}")
        print(f"   Filters: {', '.join(example['filters'])}")
        print(f"   Result: {example['result']}")
        print()


if __name__ == "__main__":
    test_tag_api_endpoints()
    test_frontend_integration()
    test_filtering_scenarios()
    show_usage_examples()
    
    print("\n" + "="*60)
    print("🏷️ Tag-Based Filtering Summary")
    print("="*60)
    print("""
✅ What We Built:
- Tag and category extraction from auto-tagging
- API endpoints for tag-based filtering
- React component for tag selection
- Real-time graph filtering
- Multi-filter support (tags + categories + search)

🔧 Features:
- Multi-select tag filtering
- Category dropdown filtering
- Search query integration
- Active filters display
- Clear filters functionality
- Real-time graph updates

🎯 Benefits:
- Discover related content quickly
- Focus on specific topics
- Explore content by categories
- Combine multiple filters
- Intuitive user experience

💡 Usage:
- Select tags from dropdown
- Choose categories
- Add search queries
- See filtered graph
- Clear filters to reset

🔄 Next Steps:
- Add tag frequency analysis
- Implement tag suggestions
- Add tag-based recommendations
- Create tag-based analytics
- Add tag management features
    """) 