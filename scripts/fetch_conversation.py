#!/usr/bin/env python3
"""
Fetch and display the actual conversation content for the outlier conversation.
This will show you what the conversation is about.
"""

import json
from pathlib import Path

def fetch_conversation():
    """Fetch the outlier conversation content."""
    
    input_file = "data/processed/tagged_chunks.jsonl"
    outlier_conv_id = "621402c89bb710395225f6227ce25ee76e22c8a1353a427610bdd1466e59e12d"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📄 Fetching conversation: {outlier_conv_id}")
    print("=" * 80)
    
    conversation_chunks = []
    
    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                conv_id = data.get('convo_id') or data.get('chat_id') or f"chunk_{line_num}"
                
                if conv_id == outlier_conv_id:
                    conversation_chunks.append(data)
                    
            except Exception as e:
                continue
    
    if not conversation_chunks:
        print("❌ Conversation not found!")
        return
    
    # Sort chunks by chunk_id or line number
    conversation_chunks.sort(key=lambda x: x.get('chunk_id', '0'))
    
    print(f"📊 Conversation Summary:")
    print(f"  Total chunks: {len(conversation_chunks):,}")
    print(f"  Title: {conversation_chunks[0].get('title', 'Unknown')}")
    print(f"  Category: {conversation_chunks[0].get('category', 'Unknown')}")
    
    # Calculate total content length
    total_length = sum(len(chunk.get('content', '')) for chunk in conversation_chunks)
    print(f"  Total content length: {total_length:,} characters ({total_length/1000:.1f}K)")
    
    print("\n" + "=" * 80)
    print("📝 CONVERSATION CONTENT:")
    print("=" * 80)
    
    # Display the conversation content
    for i, chunk in enumerate(conversation_chunks, 1):
        chunk_id = chunk.get('chunk_id', f'chunk_{i}')
        content = chunk.get('content', '')
        tags = chunk.get('tags', [])
        
        print(f"\n--- Chunk {i}/{len(conversation_chunks)} (ID: {chunk_id}) ---")
        print(f"Tags: {tags}")
        print(f"Length: {len(content)} characters")
        print("-" * 60)
        print(content)
        
        # Only show first 10 chunks to avoid overwhelming output
        if i >= 10:
            remaining = len(conversation_chunks) - 10
            print(f"\n... and {remaining} more chunks ({remaining:,} more characters)")
            break
    
    # Show some statistics about the conversation
    print("\n" + "=" * 80)
    print("📈 CONVERSATION STATISTICS:")
    print("=" * 80)
    
    all_tags = []
    all_content = ""
    
    for chunk in conversation_chunks:
        all_tags.extend(chunk.get('tags', []))
        all_content += chunk.get('content', '')
    
    from collections import Counter
    tag_freq = Counter(all_tags)
    
    print(f"Total unique tags: {len(tag_freq)}")
    print(f"Total tag instances: {len(all_tags)}")
    print(f"Average tags per chunk: {len(all_tags) / len(conversation_chunks):.1f}")
    
    print(f"\nTop 10 tags in this conversation:")
    for i, (tag, count) in enumerate(tag_freq.most_common(10), 1):
        percentage = (count / len(all_tags)) * 100
        print(f"  {i:2d}. {tag:<25} {count:>6,} ({percentage:5.1f}%)")
    
    # Save the full conversation to a file
    output_file = "data/interim/outlier_conversation.txt"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(f"Conversation ID: {outlier_conv_id}\n")
        f.write(f"Title: {conversation_chunks[0].get('title', 'Unknown')}\n")
        f.write(f"Category: {conversation_chunks[0].get('category', 'Unknown')}\n")
        f.write(f"Total chunks: {len(conversation_chunks):,}\n")
        f.write(f"Total length: {len(all_content):,} characters\n")
        f.write("=" * 80 + "\n\n")
        
        for i, chunk in enumerate(conversation_chunks, 1):
            chunk_id = chunk.get('chunk_id', f'chunk_{i}')
            content = chunk.get('content', '')
            tags = chunk.get('tags', [])
            
            f.write(f"\n--- Chunk {i}/{len(conversation_chunks)} (ID: {chunk_id}) ---\n")
            f.write(f"Tags: {tags}\n")
            f.write(f"Length: {len(content)} characters\n")
            f.write("-" * 60 + "\n")
            f.write(content + "\n")
    
    print(f"\n💾 Full conversation saved to: {output_file}")
    print(f"📄 You can read the complete conversation in that file")

if __name__ == "__main__":
    fetch_conversation() 