#!/usr/bin/env python3
"""
Enhanced Auto-Tagging Runner

Script to run enhanced auto-tagging with conversation-level context,
validation, and better error handling.
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List
import logging
from tqdm import tqdm

from chatmind.tagger.enhanced_tagger import EnhancedChunkTagger

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


def process_chunks_with_enhanced_tagging(
    input_file: Path,
    output_file: Path,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.2,
    max_retries: int = 3,
    delay_between_calls: float = 1.0,
    enable_validation: bool = True,
    enable_conversation_context: bool = True
) -> None:
    """
    Process chunks using enhanced auto-tagging.
    
    Args:
        input_file: Path to input JSONL file with chunks
        output_file: Path to output JSONL file for tagged chunks
        model: GPT model to use
        temperature: Temperature for GPT generation
        max_retries: Maximum retries for failed API calls
        delay_between_calls: Delay between API calls (seconds)
        enable_validation: Whether to enable tag validation
        enable_conversation_context: Whether to enable conversation-level context
    """
    # Load chunks
    chunks = load_chunks(input_file)
    
    if not chunks:
        logger.warning("No chunks found to process")
        return
    
    # Initialize enhanced tagger
    tagger = EnhancedChunkTagger(
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay_between_calls,
        enable_validation=enable_validation,
        enable_conversation_context=enable_conversation_context
    )
    
    # Process chunks with conversation-level context
    logger.info(f"Starting enhanced auto-tagging with {model}...")
    logger.info(f"Validation: {'enabled' if enable_validation else 'disabled'}")
    logger.info(f"Conversation context: {'enabled' if enable_conversation_context else 'disabled'}")
    
    tagged_chunks = tagger.tag_conversation_chunks(chunks)
    
    # Save results
    save_tagged_chunks(tagged_chunks, output_file)
    
    # Generate and display statistics
    stats = tagger.get_enhanced_tagging_stats(tagged_chunks)
    
    logger.info("Enhanced Tagging Statistics:")
    logger.info(f"  Total chunks: {stats['total_chunks']:,}")
    logger.info(f"  Total tags: {stats['total_tags']:,}")
    logger.info(f"  Unique tags: {stats['unique_tags']:,}")
    logger.info(f"  Unique categories: {stats['unique_categories']:,}")
    logger.info(f"  Unique domains: {stats['unique_domains']:,}")
    
    logger.info("\nTop 10 tags:")
    for tag, count in stats['top_tags']:
        logger.info(f"  {tag}: {count:,}")
    
    logger.info("\nDomain distribution:")
    for domain, count in stats['domain_counts'].items():
        logger.info(f"  {domain}: {count:,}")
    
    logger.info("\nConfidence distribution:")
    for confidence, count in stats['confidence_distribution'].items():
        logger.info(f"  {confidence}: {count:,}")
    
    if stats['potential_issues']:
        logger.warning("\nPotential issues detected:")
        for issue in stats['potential_issues']:
            logger.warning(f"  - {issue}")
    
    # Save statistics to file
    stats_file = output_file.parent / f"{output_file.stem}_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Statistics saved to: {stats_file}")


@click.command()
@click.option('--input-file', 
              default='data/processed/semantic_chunks.jsonl',
              help='Input JSONL file with semantic chunks')
@click.option('--output-file', 
              default='data/processed/enhanced_tagged_chunks.jsonl',
              help='Output JSONL file for enhanced tagged chunks')
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
@click.option('--enable-validation/--disable-validation',
              default=True,
              help='Enable/disable tag validation')
@click.option('--enable-conversation-context/--disable-conversation-context',
              default=True,
              help='Enable/disable conversation-level context')
def main(input_file: str, output_file: str, model: str, temperature: float,
         max_retries: int, delay: float, enable_validation: bool, 
         enable_conversation_context: bool):
    """
    Run enhanced auto-tagging on semantic chunks.
    
    This enhanced version includes:
    - Conversation-level context awareness
    - Tag validation to prevent systematic bias
    - Better error handling and statistics
    - Domain classification
    - Confidence scoring
    """
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Enhanced Auto-Tagging Started")
    logger.info(f"  Input: {input_path}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Validation: {'enabled' if enable_validation else 'disabled'}")
    logger.info(f"  Conversation Context: {'enabled' if enable_conversation_context else 'disabled'}")
    
    try:
        process_chunks_with_enhanced_tagging(
            input_file=input_path,
            output_file=output_path,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            delay_between_calls=delay,
            enable_validation=enable_validation,
            enable_conversation_context=enable_conversation_context
        )
        logger.info("Enhanced auto-tagging completed successfully!")
        
    except Exception as e:
        logger.error(f"Enhanced auto-tagging failed: {e}")
        raise


if __name__ == "__main__":
    main() 