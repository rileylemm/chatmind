#!/usr/bin/env python3
"""
Analyze tag distribution with outlier filtering to show representative diversity.
This removes conversations that dominate the statistics.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

def analyze_representative_tags():
    """Analyze tag distribution excluding outlier conversations."""
    
    input_file = "data/processed/tagged_chunks.jsonl"
    
    if not Path(input_file).exists():
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📊 Analyzing representative tag distribution from: {input_file}")
    
    # Collect data
    conversation_tag_counts = defaultdict(int)
    all_tags = Counter()
    conversation_tags = defaultdict(set)
    tag_categories = Counter()
    
    total_chunks = 0
    
    # First pass: count tags per conversation
    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                total_chunks += 1
                
                tags = data.get('tags', [])
                if not tags:
                    continue
                
                # Normalize tags
                normalized_tags = []
                for tag in tags:
                    if isinstance(tag, str):
                        norm_tag = tag.lower().replace('_', '-')
                        normalized_tags.append(norm_tag)
                
                # Track by conversation
                conv_id = data.get('convo_id') or data.get('chat_id') or f"chunk_{line_num}"
                conversation_tag_counts[conv_id] += len(normalized_tags)
                conversation_tags[conv_id].update(normalized_tags)
                
            except Exception as e:
                continue
    
    # Find outlier conversations (those with >1000 tag instances)
    outlier_threshold = 1000
    outlier_conversations = {conv_id for conv_id, count in conversation_tag_counts.items() 
                           if count > outlier_threshold}
    
    print(f"\n🔍 Outlier Detection:")
    print(f"  Conversations with >{outlier_threshold} tag instances: {len(outlier_conversations)}")
    
    if outlier_conversations:
        print(f"  Outlier conversations:")
        for conv_id in list(outlier_conversations)[:5]:
            count = conversation_tag_counts[conv_id]
            print(f"    - {conv_id}: {count:,} tag instances")
    
    # Second pass: collect representative data (excluding outliers)
    representative_tags = Counter()
    representative_categories = Counter()
    representative_chunks = 0
    representative_conversations = set()
    
    with open(input_file, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                
                conv_id = data.get('convo_id') or data.get('chat_id') or "unknown"
                
                # Skip outlier conversations
                if conv_id in outlier_conversations:
                    continue
                
                representative_chunks += 1
                representative_conversations.add(conv_id)
                
                tags = data.get('tags', [])
                if not tags:
                    continue
                
                # Normalize and count tags
                for tag in tags:
                    if isinstance(tag, str):
                        norm_tag = tag.lower().replace('_', '-')
                        representative_tags[norm_tag] += 1
                
                # Track categories
                category = data.get('category', 'Unknown')
                representative_categories[category] += 1
                
            except Exception as e:
                continue
    
    print(f"\n📈 Representative Summary (excluding outliers):")
    print(f"  Representative chunks: {representative_chunks:,}")
    print(f"  Representative conversations: {len(representative_conversations):,}")
    print(f"  Representative unique tags: {len(representative_tags):,}")
    print(f"  Representative tag instances: {sum(representative_tags.values()):,}")
    
    # Show representative top tags
    print(f"\n🏆 Top 50 Representative Tags:")
    print("-" * 60)
    for i, (tag, count) in enumerate(representative_tags.most_common(50), 1):
        percentage = (count / sum(representative_tags.values())) * 100
        print(f"{i:2d}. {tag:<30} {count:>6,} ({percentage:5.1f}%)")
    
    # Show representative categories
    print(f"\n📂 Top 20 Representative Categories:")
    print("-" * 60)
    for i, (category, count) in enumerate(representative_categories.most_common(20), 1):
        percentage = (count / representative_chunks) * 100
        print(f"{i:2d}. {category:<40} {count:>6,} ({percentage:5.1f}%)")
    
    # Save representative analysis
    output_file = "data/interim/representative_tag_analysis.json"
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    analysis = {
        "outliers_removed": {
            "outlier_conversations": len(outlier_conversations),
            "outlier_threshold": outlier_threshold
        },
        "representative_summary": {
            "chunks": representative_chunks,
            "conversations": len(representative_conversations),
            "unique_tags": len(representative_tags),
            "total_tag_instances": sum(representative_tags.values())
        },
        "top_representative_tags": dict(representative_tags.most_common(100)),
        "top_representative_categories": dict(representative_categories.most_common(50))
    }
    
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Representative analysis saved to: {output_file}")
    
    # Show the improvement
    if representative_tags:
        most_common_tag = representative_tags.most_common(1)[0]
        percentage = (most_common_tag[1] / sum(representative_tags.values())) * 100
        print(f"\n✅ Improvement:")
        print(f"  Most common tag now: {most_common_tag[0]} ({percentage:.1f}%)")
        print(f"  vs. previous: #genetic-disorder (19.3%)")

if __name__ == "__main__":
    analyze_representative_tags() 