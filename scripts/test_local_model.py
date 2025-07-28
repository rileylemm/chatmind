#!/usr/bin/env python3
"""
Test script for local model setup and functionality.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatmind.tagger.local.local_enhanced_tagger import LocalEnhancedChunkTagger, test_local_model

def main():
    """Test the local model setup."""
    print("🧪 Testing Local Model Setup")
    print("=" * 50)
    
    # Test 1: Check if Ollama is running
    print("\n1. Checking Ollama availability...")
    tagger = LocalEnhancedChunkTagger(model="mistral:latest")  # Use available model
    
    if tagger.check_model_availability():
        print("✅ Ollama is running and accessible")
    else:
        print("❌ Ollama is not available")
        print("\n📋 Setup Instructions:")
        print("1. Install Ollama: https://ollama.ai/")
        print("2. Start Ollama: ollama serve")
        print("3. Pull a model: ollama pull llama3.1:8b")
        print("4. Run this test again")
        return False
    
    # Test 2: Test model functionality
    print("\n2. Testing model functionality...")
    if test_local_model():
        print("✅ Local model is working correctly")
    else:
        print("❌ Local model test failed")
        return False
    
    # Test 3: Test with sample chunks
    print("\n3. Testing with sample chunks...")
    
    test_chunks = [
        {
            "content": "Let's build a React portfolio site with Tailwind CSS and animations",
            "title": "Web Development Project"
        },
        {
            "content": "The API endpoint is returning 404 errors when the database connection fails",
            "title": "API Troubleshooting"
        },
        {
            "content": "We want to showcase our adventures with retro TV effects and smooth animations",
            "title": "Creative Portfolio Design"
        }
    ]
    
    try:
        tagged_chunks = tagger.tag_conversation_chunks(test_chunks)
        
        print(f"✅ Successfully tagged {len(tagged_chunks)} chunks")
        
        for i, chunk in enumerate(tagged_chunks, 1):
            print(f"\n--- Chunk {i} ---")
            print(f"Content: {chunk['content'][:80]}...")
            print(f"Tags: {chunk.get('tags', [])}")
            print(f"Category: {chunk.get('category', '')}")
            print(f"Domain: {chunk.get('domain', '')}")
            print(f"Confidence: {chunk.get('confidence', '')}")
        
        # Get statistics
        stats = tagger.get_enhanced_tagging_stats(tagged_chunks)
        print(f"\n📊 Statistics:")
        print(f"  Total chunks: {stats['total_chunks']}")
        print(f"  Total tags: {stats['total_tags']}")
        print(f"  Unique tags: {stats['unique_tags']}")
        print(f"  Unique domains: {stats['unique_domains']}")
        
        print("\n✅ All tests passed! Local model is ready for production use.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 