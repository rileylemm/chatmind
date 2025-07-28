#!/usr/bin/env python3
"""
Analyze tag distribution across all conversations in ChatMind.
This script will show the actual diversity and frequency of tags.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

def analyze_tag_distribution():
    """Analyze tag distribution from processed data."""
    
    # Paths to check
    possible_files = [
        "data/processed/tagged_chunks.jsonl",
        "data/embeddings/chunks_tagged.jsonl",
        "data/processed/processed_tagged_chunks.jsonl"
    ]
    
    # Find the actual file
    input_file = None
    for file_path in possible_files:
        if Path(file_path).exists():
            input_file = file_path
            break
    
    if not input_file:
        print("❌ No tagged chunks file found. Checked:")
        for path in possible_files:
            print(f"  - {path}")
        return
    
    print(f"📊 Analyzing tag distribution from: {input_file}")
    
    # Collect all tags
    all_tags = Counter()
    conversation_tags = defaultdict(set)
    tag_categories = Counter()
    
    total_chunks = 0
    total_conversations = 0
    
    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                total_chunks += 1
                
                # Extract tags
                tags = data.get('tags', [])
                if not tags:
                    continue
                
                # Normalize tags
                normalized_tags = []
                for tag in tags:
                    if isinstance(tag, str):
                        norm_tag = tag.lower().replace('_', '-')
                        normalized_tags.append(norm_tag)
                        all_tags[norm_tag] += 1
                
                # Track by conversation
                conv_id = data.get('convo_id') or data.get('chat_id') or f"chunk_{line_num}"
                conversation_tags[conv_id].update(normalized_tags)
                
                # Track categories
                category = data.get('category', 'Unknown')
                tag_categories[category] += 1
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"⚠️  Unexpected error on line {line_num}: {e}")
                continue
    
    total_conversations = len(conversation_tags)
    
    print(f"\n📈 Summary:")
    print(f"  Total chunks processed: {total_chunks:,}")
    print(f"  Total conversations: {total_conversations:,}")
    print(f"  Unique tags found: {len(all_tags):,}")
    print(f"  Total tag instances: {sum(all_tags.values()):,}")
    
    # Show top tags
    print(f"\n🏆 Top 50 Tags by Frequency:")
    print("-" * 60)
    for i, (tag, count) in enumerate(all_tags.most_common(50), 1):
        percentage = (count / sum(all_tags.values())) * 100
        print(f"{i:2d}. {tag:<30} {count:>6,} ({percentage:5.1f}%)")
    
    # Show tag categories
    print(f"\n📂 Top 20 Categories:")
    print("-" * 60)
    for i, (category, count) in enumerate(tag_categories.most_common(20), 1):
        percentage = (count / total_chunks) * 100
        print(f"{i:2d}. {category:<40} {count:>6,} ({percentage:5.1f}%)")
    
    # Analyze conversation diversity
    print(f"\n🎯 Conversation Tag Diversity:")
    print("-" * 60)
    
    tags_per_conversation = [len(tags) for tags in conversation_tags.values()]
    if tags_per_conversation:
        avg_tags = sum(tags_per_conversation) / len(tags_per_conversation)
        max_tags = max(tags_per_conversation)
        min_tags = min(tags_per_conversation)
        
        print(f"  Average tags per conversation: {avg_tags:.1f}")
        print(f"  Most tags in a conversation: {max_tags}")
        print(f"  Least tags in a conversation: {min_tags}")
    
    # Show most diverse conversations
    print(f"\n🌟 Most Tag-Diverse Conversations:")
    print("-" * 60)
    sorted_conversations = sorted(conversation_tags.items(), 
                                key=lambda x: len(x[1]), reverse=True)
    
    for i, (conv_id, tags) in enumerate(sorted_conversations[:10], 1):
        print(f"{i:2d}. {conv_id[:30]:<30} {len(tags):>3} tags")
        if i <= 3:  # Show top 3 tag lists
            tag_list = ', '.join(sorted(tags)[:10])
            print(f"    Tags: {tag_list}")
            if len(tags) > 10:
                print(f"    ... and {len(tags) - 10} more")
    
    # Check for potential issues
    print(f"\n🔍 Potential Issues:")
    print("-" * 60)
    
    # Check for generic tags
    generic_tags = [tag for tag in all_tags if any(word in tag for word in 
                   ['general', 'misc', 'other', 'unknown', 'untagged'])]
    if generic_tags:
        print(f"⚠️  Found {len(generic_tags)} potentially generic tags:")
        for tag in generic_tags[:10]:
            print(f"    - {tag} ({all_tags[tag]} times)")
    
    # Check for very frequent tags (potential over-tagging)
    total_instances = sum(all_tags.values())
    over_tagged = [(tag, count) for tag, count in all_tags.items() 
                   if count > total_instances * 0.1]  # More than 10% of all tags
    
    if over_tagged:
        print(f"⚠️  Found {len(over_tagged)} potentially over-tagged terms:")
        for tag, count in over_tagged:
            percentage = (count / total_instances) * 100
            print(f"    - {tag}: {count:,} times ({percentage:.1f}%)")
    
    # Save detailed analysis
    output_file = "data/interim/tag_analysis.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    analysis = {
        "summary": {
            "total_chunks": total_chunks,
            "total_conversations": total_conversations,
            "unique_tags": len(all_tags),
            "total_tag_instances": sum(all_tags.values())
        },
        "top_tags": dict(all_tags.most_common(100)),
        "top_categories": dict(tag_categories.most_common(50)),
        "conversation_diversity": {
            "avg_tags_per_conversation": avg_tags if tags_per_conversation else 0,
            "max_tags_in_conversation": max_tags if tags_per_conversation else 0,
            "min_tags_in_conversation": min_tags if tags_per_conversation else 0
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    analyze_tag_distribution() 