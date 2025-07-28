#!/usr/bin/env python3
"""
Small test run for the enhanced tagging system.
This tests the system on a few chunks from the actual problematic conversation.
"""

import json
from pathlib import Path
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatmind.tagger.enhanced_tagger import EnhancedChunkTagger

def test_enhanced_tagging_small():
    """Test the enhanced tagging system on a small sample from the problematic conversation."""
    
    # Create test chunks from the actual problematic conversation
    test_chunks = [
        {
            "chunk_id": "test_1",
            "convo_id": "621402c89bb710395225f6227ce25ee76e22c8a1353a427610bdd1466e59e12d",
            "content": "Okay I am building a pretty simple reacrt site for my partner and I to showcase some of our adventure stuff, just kind of a personal/personal portfolio site. We are going to host on vercel, build it with react. I know you are python gpt, but you fuck wit react hard and smash it pretty good. I want to chat a bit about everything I want in the site then we will discuss how we make it a reality, then we will build it.",
            "title": "Web Development Project"
        },
        {
            "chunk_id": "test_2", 
            "convo_id": "621402c89bb710395225f6227ce25ee76e22c8a1353a427610bdd1466e59e12d",
            "content": "Hell yeah! I'm super pumped to help you bring this project to life—it sounds like an absolute blast, and I can already tell you have a solid vision. React + Vercel is such a killer combo for speed, simplicity, and getting that clean, responsive site vibe you're going for. Plus, we can really go nuts making this thing feel super personalized and stylish, with all the steez you want.",
            "title": "Web Development Planning"
        },
        {
            "chunk_id": "test_3",
            "convo_id": "621402c89bb710395225f6227ce25ee76e22c8a1353a427610bdd1466e59e12d", 
            "content": "I don't think we need a server at this point in time. We will only have some pictures, and emebedded videos and things like that mostly. As far as content goes, we are looking at having a landing page, with kind of a highlight reel looping on it. It would be cool to have some gifs looping inside old retro televisions or something like that.",
            "title": "Portfolio Design Discussion"
        },
        {
            "chunk_id": "test_4",
            "convo_id": "621402c89bb710395225f6227ce25ee76e22c8a1353a427610bdd1466e59e12d",
            "content": "The other pages will be about, portfolio, future plans, and a contact. I like the interactive map idea as well. We have been all over the world. It would be cool to kind of map both our lives with a line on a world map, and it would be cool to see when we connect and what happened with our lives since then as well.",
            "title": "Portfolio Features Planning"
        },
        {
            "chunk_id": "test_5",
            "convo_id": "621402c89bb710395225f6227ce25ee76e22c8a1353a427610bdd1466e59e12d",
            "content": "as far as functionality goes, smooth is the name of the game. smooth. sleek. I don't want any abruptness anywhere, just absolute smoothness. we definitely want some animations. My partner can make some basic animations, and I know she is thirsting to make some more, so if we put a good plan infront of her, she will go to town on that.",
            "title": "Animation and UX Planning"
        }
    ]
    
    print("🧪 Small Test Run - Enhanced Tagging System")
    print("=" * 60)
    print("Testing with chunks from the problematic conversation...")
    print()
    
    # Initialize enhanced tagger
    tagger = EnhancedChunkTagger(
        model="gpt-3.5-turbo",
        temperature=0.2,
        enable_validation=True,
        enable_conversation_context=True
    )
    
    print(f"✅ Initialized tagger with validation and conversation context")
    
    # Test conversation-level analysis
    print("\n🔍 Step 1: Conversation-level analysis...")
    conversation_context = tagger.analyze_conversation(test_chunks)
    print(f"Conversation domain: {conversation_context.get('primary_domain', 'unknown')}")
    print(f"Key topics: {conversation_context.get('key_topics', [])}")
    print(f"Primary category: {conversation_context.get('primary_category', 'unknown')}")
    print(f"Confidence: {conversation_context.get('confidence', 'unknown')}")
    
    # Test individual chunk tagging
    print("\n🏷️  Step 2: Individual chunk tagging...")
    print("-" * 60)
    
    for i, chunk in enumerate(test_chunks, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Content preview: {chunk['content'][:80]}...")
        
        tagged_chunk = tagger.tag_chunk(chunk, conversation_context)
        
        print(f"Tags: {tagged_chunk.get('tags', [])}")
        print(f"Category: {tagged_chunk.get('category', '')}")
        print(f"Domain: {tagged_chunk.get('domain', '')}")
        print(f"Confidence: {tagged_chunk.get('confidence', '')}")
        
        # Check for validation issues
        if 'validation_issues' in tagged_chunk:
            print(f"⚠️  Validation issues: {tagged_chunk['validation_issues']}")
    
    # Test conversation-level tagging
    print("\n🔄 Step 3: Conversation-level tagging...")
    tagged_chunks = tagger.tag_conversation_chunks(test_chunks)
    
    print(f"✅ Tagged {len(tagged_chunks)} chunks")
    
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
    
    print("\nConfidence distribution:")
    for confidence, count in stats['confidence_distribution'].items():
        print(f"  {confidence}: {count}")
    
    if stats['potential_issues']:
        print("\n⚠️  Potential issues detected:")
        for issue in stats['potential_issues']:
            print(f"  - {issue}")
    else:
        print("\n✅ No potential issues detected")
    
    # Check for the problematic tags
    all_tags = []
    for chunk in tagged_chunks:
        all_tags.extend(chunk.get('tags', []))
    
    medical_tags = [tag for tag in all_tags if any(word in tag.lower() for word in 
                   ['genetic', 'symptom', 'family-health', 'medical', 'health'])]
    
    if medical_tags:
        print(f"\n⚠️  WARNING: Found medical tags in web development content:")
        for tag in medical_tags:
            print(f"  - {tag}")
    else:
        print(f"\n✅ SUCCESS: No medical tags found in web development content!")
    
    # Save test results
    output_file = Path("data/interim/enhanced_tagging_small_test.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_results = {
        "test_chunks": test_chunks,
        "tagged_chunks": tagged_chunks,
        "conversation_context": conversation_context,
        "statistics": stats,
        "medical_tags_found": medical_tags
    }
    
    with open(output_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Test results saved to: {output_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY:")
    print("=" * 60)
    
    if medical_tags:
        print("❌ FAILED: Medical tags still being applied to web development content")
        print("   The enhanced system needs further tuning")
    else:
        print("✅ PASSED: No medical tags found in web development content")
        print("   The enhanced system is working correctly")
    
    print(f"\nDomain identified: {conversation_context.get('primary_domain', 'unknown')}")
    print(f"Top tags: {[tag for tag, _ in stats['top_tags'][:5]]}")
    print(f"Confidence levels: {dict(stats['confidence_distribution'])}")
    
    print("\n✅ Small test run completed!")

if __name__ == "__main__":
    test_enhanced_tagging_small() 