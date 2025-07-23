#!/usr/bin/env python3
"""
Demo: ChatGPT URL Mapping

This script demonstrates how to map conversation IDs to ChatGPT URLs
and create direct links back to the original conversations.
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
    print("🔗 ChatMind URL Mapping Demo")
    print("=" * 40)
    
    API_BASE = "http://localhost:8000"
    
    print("\n🔍 Step 1: Explore Chat with URLs")
    print("Let's find a chat that has ChatGPT URLs...")
    
    try:
        # Get graph data to find a chat
        response = requests.get(f"{API_BASE}/graph?limit=20")
        if response.status_code == 200:
            graph_data = response.json()
            
            # Find a chat node
            chat_nodes = [node for node in graph_data['nodes'] if node['type'] == 'Chat']
            if chat_nodes:
                chat_node = chat_nodes[0]
                chat_id = chat_node['id']
                chat_title = chat_node['properties'].get('title', 'Unknown')
                print(f"📋 Found chat: {chat_title} (ID: {chat_id})")
                
                print("\n🔍 Step 2: Get ChatGPT URLs for this Chat")
                print("Now let's see if this chat has any ChatGPT URLs...")
                
                # Get URLs for this chat
                urls_response = requests.get(f"{API_BASE}/lake/chat/{chat_id}/urls")
                if urls_response.status_code == 200:
                    urls_data = urls_response.json()
                    urls = urls_data.get('urls', [])
                    
                    if urls:
                        print(f"✅ Found {len(urls)} ChatGPT URLs for this chat:")
                        
                        for i, url_info in enumerate(urls):
                            conversation_id = url_info.get('conversation_id')
                            url = url_info.get('url')
                            title = url_info.get('title', 'Unknown')
                            
                            print(f"  {i+1}. {title}")
                            print(f"     Conversation ID: {conversation_id}")
                            print(f"     URL: {url}")
                            print(f"     Direct Link: 🔗 {url}")
                        
                        print("\n🔍 Step 3: Test Direct Link")
                        if urls:
                            first_url = urls[0]
                            conversation_id = first_url.get('conversation_id')
                            url = first_url.get('url')
                            
                            print(f"Testing direct link to ChatGPT conversation...")
                            print(f"🔗 Click here to open in ChatGPT: {url}")
                            
                            # Test URL mapping endpoint
                            print(f"\n🔍 Step 4: Get URL Mapping Details")
                            mapping_response = requests.get(f"{API_BASE}/lake/url/{conversation_id}")
                            if mapping_response.status_code == 200:
                                mapping_data = mapping_response.json()
                                print(f"✅ URL Mapping Details:")
                                print(f"  Conversation ID: {mapping_data.get('conversation_id')}")
                                print(f"  Chat ID: {mapping_data.get('chat_id')}")
                                print(f"  Title: {mapping_data.get('title')}")
                                print(f"  URL: {mapping_data.get('url')}")
                                print(f"  Source File: {mapping_data.get('source_file')}")
                    else:
                        print("❌ No ChatGPT URLs found for this chat")
                        print("💡 This might be because:")
                        print("   - The chat doesn't contain any ChatGPT URLs")
                        print("   - URLs haven't been extracted yet")
                        print("   - The chat is from a different source")
                
                print("\n🔍 Step 5: Search for URLs by Title")
                print("Let's search for URLs by chat title...")
                
                search_response = requests.get(f"{API_BASE}/lake/urls/search?query={chat_title[:20]}")
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    found_urls = search_data.get('urls', [])
                    
                    if found_urls:
                        print(f"✅ Found {len(found_urls)} URLs matching '{chat_title[:20]}':")
                        for url_info in found_urls:
                            print(f"  - {url_info.get('title')} -> {url_info.get('url')}")
                    else:
                        print(f"❌ No URLs found matching '{chat_title[:20]}'")
                
            else:
                print("❌ No chat nodes found in graph")
        else:
            print(f"❌ Failed to get graph data: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("💡 Make sure the API server is running: python chatmind/api/main.py")
        return
    
    print("\n" + "="*60)
    print("🎯 URL Mapping Flow Summary")
    print("="*60)
    print("""
1. Extract Conversation IDs → Parse ChatGPT URLs from chat content
2. Store URL Mappings → Map conversation_id → chat_id → full URL
3. API Access → Get URLs for specific chats
4. Direct Linking → Click to open original ChatGPT conversation

🔗 URL Patterns Supported:
- https://chat.openai.com/c/{conversation_id}
- https://chat.openai.com/share/{conversation_id}  
- https://chat.openai.com/chat/{conversation_id}

📁 Data Lake Structure:
data/lake/
├── chats/           # Chat JSON files
├── messages/        # Message JSON files
├── urls/            # URL mapping files (conversation_id.json)
└── metadata/        # Indexes

🔄 Benefits:
- Direct links back to original ChatGPT conversations
- Search URLs by chat title
- Map multiple URLs to single chat
- Persistent URL storage in data lake
- API access for frontend integration

💡 Usage Examples:
- Click chat node in graph → Get URLs → Open in ChatGPT
- Search for specific conversations by title
- Batch export all URLs for a chat
- Integrate with frontend for one-click access
    """)

if __name__ == "__main__":
    main() 