#!/usr/bin/env python3
"""
Auto-Tagging Runner

Script to run auto-tagging on semantic chunks and generate
enriched chunks with hashtags and categories.
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List
import logging
from tqdm import tqdm

from chatmind.tagger.tagger import ChunkTagger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chunks(input_file: Path) -> List[Dict]:
    """Load chunks from JSONL file."""
    chunks = []
    with jsonlines.open(input_file) as reader:
        for chunk in reader:
            chunks.append(chunk)
    
    logger.info(f"Loaded {len(chunks)} chunks from {input_file}")
    return chunks


def save_tagged_chunks(tagged_chunks: List[Dict], output_file: Path) -> None:
    """Save tagged chunks to JSONL file."""
    with jsonlines.open(output_file, mode='w') as writer:
        for chunk in tagged_chunks:
            writer.write(chunk)
    
    logger.info(f"Saved {len(tagged_chunks)} tagged chunks to {output_file}")


def process_chunks_with_tagging(
    input_file: Path,
    output_file: Path,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.2,
    max_retries: int = 3,
    delay_between_calls: float = 1.0,
    style: str = "standard"
) -> None:
    """
    Process chunks using auto-tagging.
    
    Args:
        input_file: Path to input JSONL file with chunks
        output_file: Path to output JSONL file for tagged chunks
        model: GPT model to use
        temperature: Temperature for GPT generation
        max_retries: Maximum retries for failed API calls
        delay_between_calls: Delay between API calls (seconds)
        style: Prompt style ("standard", "detailed", "general")
    """
    # Load chunks
    chunks = load_chunks(input_file)
    
    if not chunks:
        logger.warning("No chunks found to process")
        return
    
    # Initialize tagger
    tagger = ChunkTagger(
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay_between_calls
    )
    
    # Process chunks
    logger.info(f"Starting auto-tagging with {model}...")
    # If chunks have been clustered, tag one representative per cluster to reduce API calls
    if chunks and 'cluster_id' in chunks[0]:
        logger.info("Detected 'cluster_id' in chunks, grouping into clusters for tagging")
        from collections import defaultdict
        import time
        # Group chunks by their cluster_id
        clusters = defaultdict(list)
        for chunk in chunks:
            clusters[chunk['cluster_id']].append(chunk)
        tagged_chunks = []
        # Tag clusters
        for cluster_id, group in tqdm(clusters.items(), desc="Tagging clusters"):
            try:
                # Tag representative chunk
                rep_chunk = group[0]
                rep_tagged = tagger.tag_chunk(rep_chunk)
                # Apply tags to all chunks in this cluster
                for chunk in group:
                    enhanced = {
                        **chunk,
                        'tags': rep_tagged.get('tags', []),
                        'category': rep_tagged.get('category', ''),
                        'tagging_model': rep_tagged.get('tagging_model', tagger.model),
                        'tagging_timestamp': rep_tagged.get('tagging_timestamp', int(time.time()))
                    }
                    tagged_chunks.append(enhanced)
                # Respect delay between API calls
                time.sleep(tagger.delay_between_calls)
            except Exception as e:
                logger.error(f"Failed to tag cluster {cluster_id}: {e}")
                # Fallback tagging for all chunks in this cluster
                for chunk in group:
                    fallback_chunk = {
                        **chunk,
                        'tags': ['#error'],
                        'category': 'Error in tagging',
                        'tagging_model': 'fallback',
                        'tagging_timestamp': int(time.time())
                    }
                    tagged_chunks.append(fallback_chunk)
    else:
        tagged_chunks = tagger.tag_multiple_chunks(chunks)
    
    # Save results
    save_tagged_chunks(tagged_chunks, output_file)
    
    # Get and print statistics
    stats = tagger.get_tagging_stats(tagged_chunks)
    
    logger.info(f"Tagging complete!")
    logger.info(f"  - Total chunks tagged: {stats['total_chunks']}")
    logger.info(f"  - Total tags applied: {stats['total_tags']}")
    logger.info(f"  - Unique tags: {stats['unique_tags']}")
    logger.info(f"  - Unique categories: {stats['unique_categories']}")
    
    if stats['top_tags']:
        logger.info(f"  - Top tags: {[tag for tag, count in stats['top_tags'][:5]]}")


@click.command()
@click.option('--input-file', 
              default='data/processed/semantic_chunks.jsonl',
              help='Input JSONL file with semantic chunks')
@click.option('--output-file', 
              default='data/processed/tagged_chunks.jsonl',
              help='Output JSONL file for tagged chunks')
@click.option('--model', 
              default='gpt-3.5-turbo',
              help='GPT model to use for tagging')
@click.option('--temperature', 
              default=0.2,
              help='Temperature for GPT generation')
@click.option('--max-retries', 
              default=3,
              help='Maximum retries for failed API calls')
@click.option('--delay', 
              default=1.0,
              help='Delay between API calls (seconds)')
@click.option('--style', 
              default='standard',
              type=click.Choice(['standard', 'detailed', 'general']),
              help='Prompt style for tagging')
def main(input_file: str, output_file: str, model: str, temperature: float,
         max_retries: int, delay: float, style: str):
    """Run auto-tagging on semantic chunks."""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    logger.info(f"Starting auto-tagging...")
    logger.info(f"  Input: {input_path}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Style: {style}")
    
    try:
        process_chunks_with_tagging(
            input_path,
            output_path,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            delay_between_calls=delay,
            style=style
        )
        logger.info("Auto-tagging completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during auto-tagging: {e}")
        raise


if __name__ == "__main__":
    main() 