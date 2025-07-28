#!/usr/bin/env python3
"""
Test script for the enhanced tagging system.
This will test the new tagging system on a small sample to verify it works correctly.
"""

import json
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatmind.tagger.enhanced_tagger import EnhancedChunkTagger

def test_enhanced_tagging():
    """Test the enhanced tagging system on a small sample."""
    
    # Create test chunks with the problematic content we found
    test_chunks = [
        {
            "chunk_id": "test_1",
            "convo_id": "test_conversation",
            "content": "Let's build a React portfolio site with Tailwind CSS and animations. We want to showcase our adventures with retro TV effects and smooth animations.",
            "title": "Web Development Project"
        },
        {
            "chunk_id": "test_2", 
            "convo_id": "test_conversation",
            "content": "The API endpoint is returning 404 errors when the database connection fails. We need to debug this issue and fix the backend.",
            "title": "API Troubleshooting"
        },
        {
            "chunk_id": "test_3",
            "convo_id": "test_conversation", 
            "content": "We want to create a beautiful portfolio that showcases our adventures and creative projects. The site should have smooth animations and a unique design.",
            "title": "Creative Portfolio Design"
        }
    ]
    
    print("🧪 Testing Enhanced Tagging System")
    print("=" * 50)
    
    # Initialize enhanced tagger
    tagger = EnhancedChunkTagger(
        model="gpt-3.5-turbo",
        temperature=0.2,
        enable_validation=True,
        enable_conversation_context=True
    )
    
    print(f"✅ Initialized tagger with validation and conversation context")
    
    # Test conversation-level analysis
    print("\n🔍 Testing conversation-level analysis...")
    conversation_context = tagger.analyze_conversation(test_chunks)
    print(f"Conversation domain: {conversation_context.get('primary_domain', 'unknown')}")
    print(f"Key topics: {conversation_context.get('key_topics', [])}")
    
    # Test individual chunk tagging
    print("\n🏷️  Testing individual chunk tagging...")
    for i, chunk in enumerate(test_chunks, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Content: {chunk['content'][:100]}...")
        
        tagged_chunk = tagger.tag_chunk(chunk, conversation_context)
        
        print(f"Tags: {tagged_chunk.get('tags', [])}")
        print(f"Category: {tagged_chunk.get('category', '')}")
        print(f"Domain: {tagged_chunk.get('domain', '')}")
        print(f"Confidence: {tagged_chunk.get('confidence', '')}")
    
    # Test conversation-level tagging
    print("\n🔄 Testing conversation-level tagging...")
    tagged_chunks = tagger.tag_conversation_chunks(test_chunks)
    
    print(f"Tagged {len(tagged_chunks)} chunks")
    
    # Get statistics
    stats = tagger.get_enhanced_tagging_stats(tagged_chunks)
    
    print("\n📊 Enhanced Tagging Statistics:")
    print(f"  Total chunks: {stats['total_chunks']}")
    print(f"  Total tags: {stats['total_tags']}")
    print(f"  Unique tags: {stats['unique_tags']}")
    print(f"  Unique domains: {stats['unique_domains']}")
    
    print("\nTop tags:")
    for tag, count in stats['top_tags']:
        print(f"  {tag}: {count}")
    
    print("\nDomain distribution:")
    for domain, count in stats['domain_counts'].items():
        print(f"  {domain}: {count}")
    
    if stats['potential_issues']:
        print("\n⚠️  Potential issues detected:")
        for issue in stats['potential_issues']:
            print(f"  - {issue}")
    else:
        print("\n✅ No potential issues detected")
    
    # Save test results
    output_file = Path("data/interim/enhanced_tagging_test_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_results = {
        "test_chunks": test_chunks,
        "tagged_chunks": tagged_chunks,
        "conversation_context": conversation_context,
        "statistics": stats
    }
    
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {output_file}")
    print("\n✅ Enhanced tagging system test completed!")

if __name__ == "__main__":
    test_enhanced_tagging() 