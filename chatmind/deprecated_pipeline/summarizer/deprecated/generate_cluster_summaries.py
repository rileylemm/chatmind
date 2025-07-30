#!/usr/bin/env python3
"""
Generate Cluster Summaries for Neo4j Loading

This script generates cluster summaries from chunks_with_clusters.jsonl
to provide topic information for the Neo4j graph loader.
"""

import json
import jsonlines
from pathlib import Path
from collections import defaultdict, Counter
import logging
from typing import Dict, List, Set
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_top_words(text: str, max_words: int = 5) -> List[str]:
    """Extract top words from text (simple implementation)."""
    # Remove common punctuation and split
    import re
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Remove common stop words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'within', 'without',
        'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall'
    }
    
    # Filter and count
    word_counts = Counter(word for word in words if word not in stop_words)
    return [word for word, _ in word_counts.most_common(max_words)]


def generate_cluster_summaries(chunks_file: Path, output_file: Path) -> Dict:
    """Generate cluster summaries from chunks data."""
    logger.info(f"Generating cluster summaries from {chunks_file}")
    
    # Group chunks by cluster
    clusters = defaultdict(list)
    cluster_sizes = Counter()
    
    with jsonlines.open(chunks_file) as reader:
        for chunk in reader:
            cluster_id = chunk.get('cluster_id')
            if cluster_id is not None and cluster_id != -1:
                clusters[cluster_id].append(chunk)
                cluster_sizes[cluster_id] += 1
    
    logger.info(f"Found {len(clusters)} clusters")
    
    # Generate summaries for each cluster
    summaries = {}
    
    for cluster_id, chunks in clusters.items():
        # Collect all text content
        all_text = " ".join([chunk.get('content', '') for chunk in chunks])
        
        # Extract top words
        top_words = extract_top_words(all_text, max_words=5)
        
        # Get sample titles (first few chat titles)
        sample_titles = []
        seen_titles = set()
        for chunk in chunks:
            title = chunk.get('chat_title', '')
            if title and title not in seen_titles and len(sample_titles) < 3:
                sample_titles.append(title)
                seen_titles.add(title)
        
        # Create summary
        summaries[str(cluster_id)] = {
            'size': len(chunks),
            'top_words': top_words,
            'sample_titles': sample_titles,
            'total_messages': cluster_sizes[cluster_id]
        }
    
    # Save summaries
    with open(output_file, 'w') as f:
        json.dump(summaries, f, indent=2)
    
    logger.info(f"Generated summaries for {len(summaries)} clusters")
    logger.info(f"Saved to {output_file}")
    
    return summaries


@click.command()
@click.option('--input-file', 
              default='data/embeddings/chunks_with_clusters.jsonl',
              help='Input chunks file')
@click.option('--output-file', 
              default='data/embeddings/cluster_summaries.json',
              help='Output summaries file')
def main(input_file: str, output_file: str):
    """Generate cluster summaries for Neo4j loading."""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate summaries
    summaries = generate_cluster_summaries(input_path, output_path)
    
    # Print summary statistics
    total_clusters = len(summaries)
    total_messages = sum(s['total_messages'] for s in summaries.values())
    avg_cluster_size = total_messages / total_clusters if total_clusters > 0 else 0
    
    print(f"\n📊 Cluster Summary Statistics:")
    print(f"  - Total clusters: {total_clusters}")
    print(f"  - Total messages: {total_messages}")
    print(f"  - Average cluster size: {avg_cluster_size:.1f}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 