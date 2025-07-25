#!/usr/bin/env python3
"""
Incremental Auto-Tagging Runner

Script to run auto-tagging on NEW chunks only,
avoiding reprocessing of already tagged chunks.
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List, Set
import logging
from tqdm import tqdm
import hashlib
import pickle

from chatmind.tagger.tagger import ChunkTagger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_chunk_hash(chunk: Dict) -> str:
    """Generate a hash for a chunk to track if it's been processed."""
    # Create a normalized version for hashing
    normalized_chunk = {
        'content': chunk.get('content', ''),
        'chat_id': chunk.get('chat_id', ''),
        'message_id': chunk.get('message_id', ''),
        'cluster_id': chunk.get('cluster_id', ''),
        'role': chunk.get('role', '')
    }
    content = json.dumps(normalized_chunk, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def load_processed_chunk_hashes(state_file: Path) -> Set[str]:
    """Load hashes of chunks that have already been tagged."""
    if state_file.exists():
        try:
            with open(state_file, 'rb') as f:
                hashes = pickle.load(f)
            logger.info(f"Loaded {len(hashes)} processed chunk hashes")
            return hashes
        except Exception as e:
            logger.warning(f"Failed to load processed hashes: {e}")
    return set()


def save_processed_chunk_hashes(hashes: Set[str], state_file: Path) -> None:
    """Save hashes of processed chunks."""
    try:
        with open(state_file, 'wb') as f:
            pickle.dump(hashes, f)
        logger.info(f"Saved {len(hashes)} processed chunk hashes")
    except Exception as e:
        logger.error(f"Failed to save processed hashes: {e}")


def load_existing_tagged_chunks(output_file: Path) -> List[Dict]:
    """Load existing tagged chunks from output file."""
    chunks = []
    if output_file.exists():
        with jsonlines.open(output_file) as reader:
            for chunk in reader:
                chunks.append(chunk)
        logger.info(f"Loaded {len(chunks)} existing tagged chunks")
    return chunks


def load_chunks(input_file: Path) -> List[Dict]:
    """Load chunks from JSONL file."""
    chunks = []
    with jsonlines.open(input_file) as reader:
        for chunk in reader:
            chunks.append(chunk)
    
    logger.info(f"Loaded {len(chunks)} chunks from {input_file}")
    return chunks


def save_tagged_chunks_incremental(new_tagged_chunks: List[Dict], output_file: Path) -> None:
    """Save new tagged chunks by appending to existing file."""
    with jsonlines.open(output_file, mode='a') as writer:
        for chunk in new_tagged_chunks:
            writer.write(chunk)
    
    logger.info(f"Appended {len(new_tagged_chunks)} new tagged chunks to {output_file}")


def process_chunks_incremental(
    input_file: Path,
    output_file: Path,
    state_file: Path,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.2,
    max_retries: int = 3,
    delay_between_calls: float = 1.0,
    style: str = "standard",
    force_reprocess: bool = False
) -> None:
    """
    Process NEW chunks using auto-tagging (incremental).
    
    Args:
        input_file: Path to input JSONL file with chunks
        output_file: Path to output JSONL file for tagged chunks
        state_file: Path to state file for tracking processed chunks
        model: GPT model to use
        temperature: Temperature for GPT generation
        max_retries: Maximum retries for failed API calls
        delay_between_calls: Delay between API calls (seconds)
        style: Prompt style ("standard", "detailed", "general")
        force_reprocess: Force reprocess all chunks (ignore state)
    """
    # Load existing state
    processed_hashes = set()
    if not force_reprocess:
        processed_hashes = load_processed_chunk_hashes(state_file)
    
    # Load all chunks
    all_chunks = load_chunks(input_file)
    
    if not all_chunks:
        logger.warning("No chunks found to process")
        return
    
    # Identify new chunks
    new_chunks = []
    for chunk in all_chunks:
        chunk_hash = generate_chunk_hash(chunk)
        if force_reprocess or chunk_hash not in processed_hashes:
            new_chunks.append(chunk)
            processed_hashes.add(chunk_hash)
    
    if not new_chunks:
        logger.info("No new chunks to process")
        return
    
    logger.info(f"Found {len(new_chunks)} new chunks to tag")
    
    # Initialize tagger
    tagger = ChunkTagger(
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay_between_calls
    )
    
    # Process new chunks
    logger.info(f"Starting incremental auto-tagging with {model}...")
    
    # If chunks have been clustered, tag one representative per cluster to reduce API calls
    if new_chunks and 'cluster_id' in new_chunks[0]:
        logger.info("Detected 'cluster_id' in chunks, grouping into clusters for tagging")
        from collections import defaultdict
        
        # Group chunks by their cluster_id
        clusters = defaultdict(list)
        for chunk in new_chunks:
            clusters[chunk['cluster_id']].append(chunk)
        
        new_tagged_chunks = []
        
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
                        'tagging_model': rep_tagged.get('tagging_model', model),
                        'tagging_timestamp': rep_tagged.get('tagging_timestamp', '')
                    }
                    new_tagged_chunks.append(enhanced)
                    
            except Exception as e:
                logger.warning(f"Failed to tag cluster {cluster_id}: {e}")
                # Add chunks without tags
                for chunk in group:
                    enhanced = {
                        **chunk,
                        'tags': [],
                        'category': 'untagged',
                        'tagging_model': model,
                        'tagging_timestamp': ''
                    }
                    new_tagged_chunks.append(enhanced)
    else:
        # Tag each chunk individually
        new_tagged_chunks = tagger.tag_multiple_chunks(new_chunks)
    
    # Save new tagged chunks (append mode)
    save_tagged_chunks_incremental(new_tagged_chunks, output_file)
    
    # Save updated state
    save_processed_chunk_hashes(processed_hashes, state_file)
    
    # Print statistics
    total_tags = sum(len(chunk.get('tags', [])) for chunk in new_tagged_chunks)
    unique_tags = set()
    for chunk in new_tagged_chunks:
        unique_tags.update(chunk.get('tags', []))
    
    logger.info(f"Incremental tagging complete!")
    logger.info(f"  - New chunks tagged: {len(new_tagged_chunks)}")
    logger.info(f"  - Total tags applied: {total_tags}")
    logger.info(f"  - Unique tags used: {len(unique_tags)}")
    logger.info(f"  - Total processed chunks: {len(processed_hashes)}")


@click.command()
@click.option('--input-file', 
              default='data/embeddings/chunks_with_clusters.jsonl',
              help='Input JSONL file with chunks')
@click.option('--output-file', 
              default='data/processed/tagged_chunks.jsonl',
              help='Output JSONL file for tagged chunks')
@click.option('--state-file',
              default='data/processed/tagging_state.pkl',
              help='State file for tracking processed chunks')
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
@click.option('--force', is_flag=True, help='Force reprocess all chunks (ignore state)')
def main(input_file: str, output_file: str, state_file: str, model: str, temperature: float,
         max_retries: int, delay: float, style: str, force: bool):
    """Run incremental auto-tagging on chunks."""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    state_path = Path(state_file)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    try:
        process_chunks_incremental(
            input_path,
            output_path,
            state_path,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            delay_between_calls=delay,
            style=style,
            force_reprocess=force
        )
    except Exception as e:
        logger.error(f"Error during incremental tagging: {e}")
        raise


if __name__ == "__main__":
    main() 