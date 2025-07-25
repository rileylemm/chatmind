#!/usr/bin/env python3
"""
Constrained Auto-Tagging Runner

Script to run constrained auto-tagging on semantic chunks using the master tag list.
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List
import logging
from tqdm import tqdm

from chatmind.tagger.constrained_tagger import ConstrainedChunkTagger

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
    
    logger.info(f"Saved {len(tagged_chunks)} constrained tagged chunks to {output_file}")


def process_chunks_with_constrained_tagging(
    input_file: Path,
    output_file: Path,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.2,
    max_retries: int = 3,
    delay_between_calls: float = 1.0,
    master_tags_path: str = "data/tags/tags_master_list.json"
) -> None:
    """
    Process chunks using constrained auto-tagging.
    
    Args:
        input_file: Path to input JSONL file with chunks
        output_file: Path to output JSONL file for tagged chunks
        model: GPT model to use
        temperature: Temperature for GPT generation
        max_retries: Maximum retries for failed API calls
        delay_between_calls: Delay between API calls (seconds)
        master_tags_path: Path to master tags file
    """
    # Load chunks
    chunks = load_chunks(input_file)
    
    if not chunks:
        logger.warning("No chunks found to process")
        return
    
    # Initialize constrained tagger
    tagger = ConstrainedChunkTagger(
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay_between_calls,
        master_tags_path=master_tags_path
    )
    
    # Process chunks
    logger.info(f"Starting constrained auto-tagging with {model}...")
    logger.info(f"Using master list with {len(tagger.master_tags)} tags")
    
    # If chunks have been clustered, tag one representative per cluster to reduce API calls
    if chunks and 'cluster_id' in chunks[0]:
        logger.info("Detected 'cluster_id' in chunks, grouping into clusters for constrained tagging")
        from collections import defaultdict
        import time
        # Group chunks by their cluster_id
        clusters = defaultdict(list)
        for chunk in chunks:
            clusters[chunk['cluster_id']].append(chunk)
        tagged_chunks = []
        # Tag clusters
        for cluster_id, group in tqdm(clusters.items(), desc="Tagging clusters (constrained)"):
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
                        'tagging_timestamp': rep_tagged.get('tagging_timestamp', int(time.time())),
                        'constrained_tagging': True
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
                        'category': 'Error in constrained tagging',
                        'tagging_model': 'fallback',
                        'tagging_timestamp': int(time.time()),
                        'constrained_tagging': True
                    }
                    tagged_chunks.append(fallback_chunk)
    else:
        tagged_chunks = tagger.tag_multiple_chunks(chunks)
    
    # Save results
    save_tagged_chunks(tagged_chunks, output_file)
    
    # Get and print statistics
    stats = tagger.get_tagging_stats(tagged_chunks)
    
    logger.info(f"Constrained tagging complete!")
    logger.info(f"  - Total chunks tagged: {stats['total_chunks']}")
    logger.info(f"  - Constrained chunks: {stats['constrained_chunks']}")
    logger.info(f"  - Total tags applied: {stats['total_tags']}")
    logger.info(f"  - Unique tags: {stats['unique_tags']}")
    logger.info(f"  - Unique categories: {stats['unique_categories']}")
    logger.info(f"  - Master list size: {stats['master_list_size']}")
    
    if stats['top_tags']:
        logger.info(f"  - Top tags: {[tag for tag, count in stats['top_tags'][:5]]}")


@click.command()
@click.option('--input-file', 
              default='data/processed/semantic_chunks.jsonl',
              help='Input JSONL file with semantic chunks')
@click.option('--output-file', 
              default='data/processed/constrained_tagged_chunks.jsonl',
              help='Output JSONL file for constrained tagged chunks')
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
@click.option('--master-tags-path', 
              default='data/tags/tags_master_list.json',
              help='Path to master tags file')
def main(input_file: str, output_file: str, model: str, temperature: float,
         max_retries: int, delay: float, master_tags_path: str):
    """Run constrained auto-tagging on semantic chunks."""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    master_tags_path = Path(master_tags_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    if not master_tags_path.exists():
        logger.error(f"Master tags file not found: {master_tags_path}")
        return
    
    logger.info(f"Starting constrained auto-tagging...")
    logger.info(f"  Input: {input_path}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Master tags: {master_tags_path}")
    
    try:
        process_chunks_with_constrained_tagging(
            input_path,
            output_path,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            delay_between_calls=delay,
            master_tags_path=str(master_tags_path)
        )
        logger.info("Constrained auto-tagging completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during constrained auto-tagging: {e}")
        raise


if __name__ == "__main__":
    main() 