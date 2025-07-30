#!/usr/bin/env python3
"""
Semantic Chunking Runner

Script to run semantic chunking on processed chat data and generate
semantic chunks for the embedding pipeline.
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List
import logging
from tqdm import tqdm

from .chunker import SemanticChunker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chats(input_file: Path) -> List[Dict]:
    """Load chats from JSONL file."""
    chats = []
    with jsonlines.open(input_file) as reader:
        for chat in reader:
            chats.append(chat)
    
    logger.info(f"Loaded {len(chats)} chats from {input_file}")
    return chats


def save_chunks(chunks: List[Dict], output_file: Path) -> None:
    """Save chunks to JSONL file."""
    with jsonlines.open(output_file, mode='w') as writer:
        for chunk in chunks:
            writer.write(chunk)
    
    logger.info(f"Saved {len(chunks)} chunks to {output_file}")


def process_chats_with_semantic_chunking(
    input_file: Path,
    output_file: Path,
    model: str = "gpt-4",
    temperature: float = 0.3,
    max_retries: int = 3,
    delay_between_calls: float = 1.0,
    style: str = "standard"
) -> None:
    """
    Process chats using semantic chunking.
    
    Args:
        input_file: Path to input JSONL file with chats
        output_file: Path to output JSONL file for chunks
        model: GPT model to use
        temperature: Temperature for GPT generation
        max_retries: Maximum retries for failed API calls
        delay_between_calls: Delay between API calls (seconds)
        style: Prompt style ("standard", "detailed", "technical")
    """
    # Load chats
    chats = load_chats(input_file)
    
    if not chats:
        logger.warning("No chats found to process")
        return
    
    # Initialize chunker
    chunker = SemanticChunker(
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay_between_calls
    )
    
    # Process chats
    logger.info(f"Starting semantic chunking with {model}...")
    all_chunks = chunker.chunk_multiple_chats(chats)
    
    # Save results
    save_chunks(all_chunks, output_file)
    
    # Print statistics
    semantic_chunks = [c for c in all_chunks if c.get('chunk_type') == 'semantic']
    fallback_chunks = [c for c in all_chunks if c.get('chunk_type') == 'fallback']
    
    logger.info(f"Chunking complete!")
    logger.info(f"  - Total chunks: {len(all_chunks)}")
    logger.info(f"  - Semantic chunks: {len(semantic_chunks)}")
    logger.info(f"  - Fallback chunks: {len(fallback_chunks)}")
    logger.info(f"  - Average chunks per chat: {len(all_chunks) / len(chats):.1f}")


@click.command()
@click.option('--input-file', 
              default='data/processed/chats.jsonl',
              help='Input JSONL file with processed chats')
@click.option('--output-file', 
              default='data/processed/semantic_chunks.jsonl',
              help='Output JSONL file for semantic chunks')
@click.option('--model', 
              default='gpt-4',
              help='GPT model to use for chunking')
@click.option('--temperature', 
              default=0.3,
              help='Temperature for GPT generation')
@click.option('--max-retries', 
              default=3,
              help='Maximum retries for failed API calls')
@click.option('--delay', 
              default=1.0,
              help='Delay between API calls (seconds)')
@click.option('--style', 
              default='standard',
              type=click.Choice(['standard', 'detailed', 'technical']),
              help='Prompt style for chunking')
def main(input_file: str, output_file: str, model: str, temperature: float,
         max_retries: int, delay: float, style: str):
    """Run semantic chunking on processed chat data."""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    logger.info(f"Starting semantic chunking...")
    logger.info(f"  Input: {input_path}")
    logger.info(f"  Output: {output_path}")
    logger.info(f"  Model: {model}")
    logger.info(f"  Style: {style}")
    
    try:
        process_chats_with_semantic_chunking(
            input_path,
            output_path,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            delay_between_calls=delay,
            style=style
        )
        logger.info("Semantic chunking completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during semantic chunking: {e}")
        raise


if __name__ == "__main__":
    main() 