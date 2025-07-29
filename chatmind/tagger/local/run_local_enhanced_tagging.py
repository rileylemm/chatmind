#!/usr/bin/env python3
"""
Local Enhanced Auto-Tagging Runner

Script to run enhanced auto-tagging using local models instead of OpenAI API.
This eliminates all API costs while maintaining enhanced features.
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

from chatmind.tagger.local.local_enhanced_tagger import LocalEnhancedChunkTagger

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


def process_chunks_local_enhanced_incremental(
    input_file: Path,
    output_file: Path,
    state_file: Path,
    model: str = "tinyllama:latest",
    temperature: float = 0.2,
    max_retries: int = 3,
    delay_between_calls: float = 0.1,
    enable_validation: bool = True,
    enable_conversation_context: bool = True,
    force_reprocess: bool = False,
    save_interval: int = 500  # Save every 500 chunks
) -> None:
    """
    Process chunks using local enhanced auto-tagging with incremental processing.
    
    Args:
        input_file: Path to input JSONL file with chunks
        output_file: Path to output JSONL file for tagged chunks
        state_file: Path to state file for tracking processed chunks
        model: Local model to use (e.g., "llama3.1:8b", "mistral:7b")
        temperature: Temperature for model generation
        max_retries: Maximum retries for failed calls
        delay_between_calls: Delay between API calls (seconds)
        enable_validation: Whether to enable tag validation
        enable_conversation_context: Whether to enable conversation-level context
        force_reprocess: Whether to force reprocessing of all chunks
        save_interval: How often to save progress (number of chunks)
    """
    # Load chunks
    chunks = load_chunks(input_file)
    
    if not chunks:
        logger.warning("No chunks found to process")
        return
    
    # Load existing tagged chunks
    existing_chunks = load_existing_tagged_chunks(output_file)
    
    # Load processed hashes
    processed_hashes = set()
    if not force_reprocess:
        processed_hashes = load_processed_chunk_hashes(state_file)
    
    # Identify new chunks that need processing
    new_chunks = []
    new_hashes = set()
    
    for chunk in chunks:
        chunk_hash = generate_chunk_hash(chunk)
        if chunk_hash not in processed_hashes or force_reprocess:
            new_chunks.append(chunk)
            new_hashes.add(chunk_hash)
    
    if not new_chunks:
        logger.info("No new chunks to process")
        return
    
    logger.info(f"Found {len(new_chunks)} new chunks to process out of {len(chunks)} total")
    
    # Initialize local enhanced tagger
    tagger = LocalEnhancedChunkTagger(
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay_between_calls,
        enable_validation=enable_validation,
        enable_conversation_context=enable_conversation_context
    )
    
    # Check if local model is available
    if not tagger.check_model_availability():
        logger.error(f"Local model {model} is not available. Please install Ollama and pull the model.")
        logger.info("To install Ollama: https://ollama.ai/")
        logger.info(f"To pull the model: ollama pull {model}")
        return
    
    # Process new chunks with enhanced tagging
    logger.info(f"Starting local enhanced auto-tagging with {model}...")
    logger.info(f"Validation: {'enabled' if enable_validation else 'disabled'}")
    logger.info(f"Conversation context: {'enabled' if enable_conversation_context else 'disabled'}")
    logger.info(f"Save interval: Every {save_interval} chunks")
    
    # Group new chunks by conversation for context
    from collections import defaultdict
    conversation_groups = defaultdict(list)
    for chunk in new_chunks:
        conv_id = chunk.get('convo_id') or chunk.get('chat_id') or 'unknown'
        conversation_groups[conv_id].append(chunk)
    
    all_new_tagged_chunks = []
    processed_count = 0
    total_conversations = len(conversation_groups)
    current_conversation = 0
    
    for conv_id, conv_chunks in conversation_groups.items():
        current_conversation += 1
        logger.info(f"Processing conversation {conv_id} with {len(conv_chunks)} new chunks ({current_conversation}/{total_conversations})")
        
        # Tag chunks with conversation context
        tagged_chunks = tagger.tag_conversation_chunks(conv_chunks)
        all_new_tagged_chunks.extend(tagged_chunks)
        processed_count += len(tagged_chunks)
        
        # Save incrementally every save_interval chunks
        if processed_count >= save_interval:
            logger.info(f"Saving progress: {processed_count} chunks processed so far")
            save_tagged_chunks_incremental(all_new_tagged_chunks, output_file)
            
            # Update processed hashes for the chunks we just saved
            for chunk in all_new_tagged_chunks:
                chunk_hash = generate_chunk_hash(chunk)
                processed_hashes.add(chunk_hash)
            save_processed_chunk_hashes(processed_hashes, state_file)
            
            # Reset for next batch
            all_new_tagged_chunks = []
            processed_count = 0
    
    # Save any remaining chunks
    if all_new_tagged_chunks:
        logger.info(f"Saving final batch: {len(all_new_tagged_chunks)} chunks")
        save_tagged_chunks_incremental(all_new_tagged_chunks, output_file)
        
        # Update processed hashes for remaining chunks
        for chunk in all_new_tagged_chunks:
            chunk_hash = generate_chunk_hash(chunk)
            processed_hashes.add(chunk_hash)
        save_processed_chunk_hashes(processed_hashes, state_file)
    
    # Generate and display statistics
    stats = tagger.get_enhanced_tagging_stats(all_new_tagged_chunks)
    
    logger.info("Local Enhanced Tagging Statistics (New Chunks Only):")
    logger.info(f"  Total new chunks: {stats['total_chunks']:,}")
    logger.info(f"  Total tags: {stats['total_tags']:,}")
    logger.info(f"  Unique tags: {stats['unique_tags']:,}")
    logger.info(f"  Unique domains: {stats['unique_domains']:,}")
    
    logger.info("\nTop tags in new chunks:")
    for tag, count in stats['top_tags'][:10]:
        logger.info(f"  {tag}: {count:,}")
    
    logger.info("\nDomain distribution in new chunks:")
    for domain, count in stats['domain_counts'].items():
        logger.info(f"  {domain}: {count:,}")
    
    if stats['potential_issues']:
        logger.warning("\nPotential issues detected in new chunks:")
        for issue in stats['potential_issues']:
            logger.warning(f"  - {issue}")
    
    # Local model statistics
    local_stats = stats.get('local_model_stats', {})
    logger.info("\nLocal Model Statistics:")
    logger.info(f"  Successful calls: {local_stats.get('successful_calls', 0):,}")
    logger.info(f"  Failed calls: {local_stats.get('failed_calls', 0):,}")
    logger.info(f"  Validation failures: {local_stats.get('validation_failures', 0):,}")
    logger.info(f"  Conversation analyses: {local_stats.get('conversation_analyses', 0):,}")
    
    # Save statistics to file
    stats_file = output_file.parent / f"{output_file.stem}_local_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Local enhanced statistics saved to: {stats_file}")


@click.command()
@click.option('--input-file', 
              default='data/embeddings/chunks_with_clusters.jsonl',
              help='Input JSONL file with chunks')
@click.option('--output-file', 
              default='data/processed/local_enhanced_tagged_chunks.jsonl',
              help='Output JSONL file for local enhanced tagged chunks')
@click.option('--state-file',
              default='data/processed/local_enhanced_tagging_state.pkl',
              help='State file for tracking processed chunks')
@click.option('--model', 
              default='gemma:2b',
              help='Local model to use (e.g., gemma:2b, phi:2.7b, llama3.2:latest, tinyllama:latest)')
@click.option('--temperature', 
              default=0.2,
              help='Temperature for model generation')
@click.option('--max-retries', 
              default=3,
              help='Maximum retries for failed calls')
@click.option('--delay', 
              default=0.1,
              help='Delay between API calls (seconds)')
@click.option('--enable-validation/--disable-validation',
              default=False,
              help='Enable/disable tag validation (disabled by default for speed)')
@click.option('--enable-conversation-context/--disable-conversation-context',
              default=True,
              help='Enable/disable conversation-level context')
@click.option('--force', is_flag=True, help='Force reprocess all chunks (ignore state)')
def main(input_file: str, output_file: str, state_file: str, model: str, temperature: float,
         max_retries: int, delay: float, enable_validation: bool, 
         enable_conversation_context: bool, force: bool):
    """
    Run local enhanced incremental auto-tagging on semantic chunks.
    
    This version uses local models (Ollama) instead of OpenAI API to eliminate costs.
    It maintains the same enhanced features:
    - Conversation-level context awareness
    - Tag validation to prevent systematic bias
    - Better error handling and statistics
    - Domain classification
    - Confidence scoring
    - Incremental processing to avoid reprocessing
    
    REQUIREMENTS:
    - Ollama installed: https://ollama.ai/
    - Model pulled: ollama pull llama3.1:8b
    """
    input_path = Path(input_file)
    output_path = Path(output_file)
    state_path = Path(state_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Local Enhanced Incremental Auto-Tagging Started")
    logger.info(f"  Input: {input_path}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  State: {state_path}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Validation: {'enabled' if enable_validation else 'disabled'}")
    logger.info(f"  Conversation Context: {'enabled' if enable_conversation_context else 'disabled'}")
    logger.info(f"  Force reprocess: {'yes' if force else 'no'}")
    
    try:
        process_chunks_local_enhanced_incremental(
            input_path,
            output_path,
            state_path,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            delay_between_calls=delay,
            enable_validation=enable_validation,
            enable_conversation_context=enable_conversation_context,
            force_reprocess=force,
            save_interval=500  # Save every 500 chunks
        )
        logger.info("Local enhanced incremental auto-tagging completed successfully!")
        
    except Exception as e:
        logger.error(f"Local enhanced incremental auto-tagging failed: {e}")
        raise


if __name__ == "__main__":
    main() 