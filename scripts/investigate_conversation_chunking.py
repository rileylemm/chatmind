#!/usr/bin/env python3
"""
Investigate how one conversation could generate so many tag instances.
This will examine the chunking and tagging process for the outlier conversation.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

def investigate_conversation_chunking():
    """Investigate the chunking and tagging process for outlier conversations."""
    
    input_file = "data/processed/tagged_chunks.jsonl"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"🔍 Investigating conversation chunking from: {input_file}")
    
    # Find the outlier conversation
    conversation_tag_counts = defaultdict(int)
    conversation_chunks = defaultdict(list)
    conversation_details = defaultdict(dict)
    
    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                
                tags = data.get('tags', [])
                conv_id = data.get('convo_id') or data.get('chat_id') or f"chunk_{line_num}"
                
                # Count tags per conversation
                conversation_tag_counts[conv_id] += len(tags)
                conversation_chunks[conv_id].append(data)
                
                # Store conversation details
                if conv_id not in conversation_details:
                    conversation_details[conv_id] = {
                        'title': data.get('title', 'Unknown'),
                        'category': data.get('category', 'Unknown'),
                        'first_chunk': line_num,
                        'total_chunks': 0,
                        'total_tags': 0,
                        'unique_tags': set()
                    }
                
                conversation_details[conv_id]['total_chunks'] += 1
                conversation_details[conv_id]['total_tags'] += len(tags)
                conversation_details[conv_id]['unique_tags'].update(tags)
                
            except Exception as e:
                continue
    
    # Find the outlier conversation
    outlier_conv_id = max(conversation_tag_counts.items(), key=lambda x: x[1])[0]
    outlier_count = conversation_tag_counts[outlier_conv_id]
    
    print(f"\n🎯 Outlier Conversation Analysis:")
    print(f"  Conversation ID: {outlier_conv_id}")
    print(f"  Total tag instances: {outlier_count:,}")
    
    details = conversation_details[outlier_conv_id]
    print(f"  Title: {details['title']}")
    print(f"  Category: {details['category']}")
    print(f"  Total chunks: {details['total_chunks']:,}")
    print(f"  Unique tags: {len(details['unique_tags'])}")
    print(f"  Average tags per chunk: {details['total_tags'] / details['total_chunks']:.1f}")
    
    # Examine the chunks
    chunks = conversation_chunks[outlier_conv_id]
    print(f"\n📄 Chunk Analysis:")
    print(f"  Total chunks in conversation: {len(chunks):,}")
    
    # Show first few chunks
    print(f"\n🔍 First 5 chunks:")
    for i, chunk in enumerate(chunks[:5], 1):
        chunk_id = chunk.get('chunk_id', f'chunk_{i}')
        content_preview = chunk.get('content', '')[:100] + "..." if len(chunk.get('content', '')) > 100 else chunk.get('content', '')
        tags = chunk.get('tags', [])
        print(f"  {i}. Chunk ID: {chunk_id}")
        print(f"     Tags: {len(tags)} tags")
        print(f"     Content preview: {content_preview}")
        print(f"     Sample tags: {tags[:5]}")
        print()
    
    # Analyze tag distribution within the conversation
    all_tags_in_conversation = []
    for chunk in chunks:
        all_tags_in_conversation.extend(chunk.get('tags', []))
    
    tag_freq = Counter(all_tags_in_conversation)
    
    print(f"\n🏷️  Tag Distribution in Outlier Conversation:")
    print(f"  Total tag instances: {len(all_tags_in_conversation):,}")
    print(f"  Unique tags: {len(tag_freq):,}")
    
    print(f"\n📊 Top 20 tags in this conversation:")
    for i, (tag, count) in enumerate(tag_freq.most_common(20), 1):
        percentage = (count / len(all_tags_in_conversation)) * 100
        print(f"  {i:2d}. {tag:<30} {count:>6,} ({percentage:5.1f}%)")
    
    # Check if tags are being duplicated across chunks
    print(f"\n🔍 Tag Duplication Analysis:")
    
    # Check if the same tags appear in multiple chunks
    tag_to_chunks = defaultdict(set)
    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get('chunk_id', f'chunk_{i}')
        for tag in chunk.get('tags', []):
            tag_to_chunks[tag].add(chunk_id)
    
    tags_in_multiple_chunks = {tag: chunks for tag, chunks in tag_to_chunks.items() if len(chunks) > 1}
    
    print(f"  Tags appearing in multiple chunks: {len(tags_in_multiple_chunks)}")
    if tags_in_multiple_chunks:
        print(f"  Top tags by chunk frequency:")
        sorted_by_frequency = sorted(tags_in_multiple_chunks.items(), key=lambda x: len(x[1]), reverse=True)
        for tag, chunk_ids in sorted_by_frequency[:10]:
            print(f"    - {tag}: appears in {len(chunk_ids)} chunks")
    
    # Check chunk sizes
    chunk_sizes = [len(chunk.get('content', '')) for chunk in chunks]
    avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
    
    print(f"\n📏 Chunk Size Analysis:")
    print(f"  Average chunk size: {avg_chunk_size:.0f} characters")
    print(f"  Smallest chunk: {min(chunk_sizes) if chunk_sizes else 0} characters")
    print(f"  Largest chunk: {max(chunk_sizes) if chunk_sizes else 0} characters")
    
    # Check if this is a very long conversation
    total_content_length = sum(chunk_sizes)
    print(f"  Total conversation length: {total_content_length:,} characters")
    print(f"  Total conversation length: {total_content_length / 1000:.1f}K characters")
    
    # Compare with other conversations
    print(f"\n📈 Comparison with Other Conversations:")
    other_conversations = [(conv_id, count) for conv_id, count in conversation_tag_counts.items() 
                          if conv_id != outlier_conv_id]
    
    if other_conversations:
        avg_other_tags = sum(count for _, count in other_conversations) / len(other_conversations)
        max_other_tags = max(count for _, count in other_conversations)
        
        print(f"  Average tags per conversation (others): {avg_other_tags:.1f}")
        print(f"  Max tags in other conversations: {max_other_tags:,}")
        print(f"  Outlier is {outlier_count / avg_other_tags:.1f}x larger than average")
        print(f"  Outlier is {outlier_count / max_other_tags:.1f}x larger than next largest")

if __name__ == "__main__":
    investigate_conversation_chunking() 