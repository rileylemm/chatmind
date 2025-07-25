#!/usr/bin/env python3
"""
Demo: Data Lake Navigation

This script demonstrates how to navigate from Neo4j graph → specific chat → specific message
using the data lake structure.
"""

import requests
import json
from pathlib import Path
import jsonlines

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def main():
    print("🏊 ChatMind Data Lake Navigation Demo")
    print("=" * 50)
    
    API_BASE = "http://localhost:8000"
    
    print("💡 This demo shows how to navigate from the knowledge graph")
    print("   to specific chats and messages in your data lake.")
    print("   Make sure the API server is running first!")
    
    print("\n🔍 Step 1: Explore the Knowledge Graph")
    print("Let's start by looking at the graph structure...")
    
    try:
        # Get graph data
        response = requests.get(f"{API_BASE}/graph?limit=10")
        if response.status_code == 200:
            graph_data = response.json()
            print(f"✅ Graph has {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
            
            # Find a chat node
            chat_nodes = [node for node in graph_data['nodes'] if node['type'] == 'Chat']
            if chat_nodes:
                chat_node = chat_nodes[0]
                chat_id = chat_node['id']
                chat_title = chat_node['properties'].get('title', 'Unknown')
                print(f"📋 Found chat: {chat_title} (ID: {chat_id})")
                
                print("\n🔍 Step 2: Navigate to Specific Chat")
                print(f"Now let's get the full chat details from the data lake...")
                
                # Get chat from data lake
                chat_response = requests.get(f"{API_BASE}/lake/chat/{chat_id}")
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    print(f"✅ Retrieved chat: {chat_data['title']}")
                    print(f"📊 Chat has {chat_data['message_count']} messages")
                    
                    print("\n🔍 Step 3: Navigate to Specific Messages")
                    print("Let's get all messages for this chat...")
                    
                    # Get messages for this chat
                    messages_response = requests.get(f"{API_BASE}/lake/chat/{chat_id}/messages")
                    if messages_response.status_code == 200:
                        messages_data = messages_response.json()
                        messages = messages_data['messages']
                        print(f"✅ Retrieved {len(messages)} messages")
                        
                        # Show first few messages
                        for i, message in enumerate(messages[:3]):
                            role = message.get('role', 'unknown')
                            content = message.get('content', '')[:100]
                            print(f"  {i+1}. [{role}] {content}...")
                        
                        if len(messages) > 3:
                            print(f"  ... and {len(messages) - 3} more messages")
                        
                        print("\n🔍 Step 4: Navigate to Specific Message")
                        if messages:
                            first_message = messages[0]
                            message_id = first_message['id']
                            print(f"Let's get details for message: {message_id}")
                            
                            # Get specific message
                            message_response = requests.get(f"{API_BASE}/lake/message/{message_id}")
                            if message_response.status_code == 200:
                                message_data = message_response.json()
                                print(f"✅ Retrieved message:")
                                print(f"  Role: {message_data.get('role')}")
                                print(f"  Content: {message_data.get('content', '')[:200]}...")
                                print(f"  Timestamp: {message_data.get('timestamp')}")
                    
                else:
                    print(f"❌ Failed to get chat: {chat_response.status_code}")
            else:
                print("❌ No chat nodes found in graph")
        else:
            print(f"❌ Failed to get graph data: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("💡 Make sure the API server is running: python chatmind/api/main.py")
        return
    
    print("\n" + "="*60)
    print("🎯 Navigation Flow Summary")
    print("="*60)
    print("""
1. Neo4j Graph → Find chat nodes in knowledge graph
2. Chat Node → Get chat_id from graph properties  
3. Data Lake Chat → Retrieve full chat details from data lake
4. Chat Messages → Get all messages for the chat
5. Specific Message → Drill down to individual message details

🔗 API Endpoints:
- GET /graph → Get knowledge graph structure
- GET /lake/chat/{chat_id} → Get specific chat
- GET /lake/chat/{chat_id}/messages → Get all messages for chat
- GET /lake/message/{message_id} → Get specific message

📁 Data Lake Structure:
data/lake/
├── chats/           # Individual chat JSON files
├── messages/        # Individual message JSON files  
└── metadata/        # Indexes and metadata

🔄 Benefits:
- Hierarchical navigation from graph → chat → message
- Fast access to individual chats and messages
- Persistent storage of full conversation context
- Scalable structure for large datasets
    """)

if __name__ == "__main__":
    main() 