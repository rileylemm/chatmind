#!/usr/bin/env python3
"""
Separate Tag Validation Runner

Runs validation on already-tagged chunks as a separate step.
This allows for faster initial tagging and independent validation retries.
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
import time
import os
from datetime import datetime

from chatmind.tagger.local.local_enhanced_tagger import LocalEnhancedChunkTagger

# Create logs directory if it doesn't exist
log_dir = Path("chatmind/tagger/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Set up file logging
log_file = log_dir / f"tag_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

# Set up console logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"Tag validation logging to: {log_file}")


def generate_chunk_hash(chunk: Dict) -> str:
    """Generate a hash for a chunk to track if it's been validated."""
    normalized_chunk = {
        'content': chunk.get('content', ''),
        'chat_id': chunk.get('chat_id', ''),
        'message_id': chunk.get('message_id', ''),
        'cluster_id': chunk.get('cluster_id', ''),
        'role': chunk.get('role', ''),
        'tags': sorted(chunk.get('tags', []))  # Include tags in hash
    }
    content = json.dumps(normalized_chunk, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def load_processed_validation_hashes(state_file: Path) -> Set[str]:
    """Load hashes of chunks that have already been validated."""
    if state_file.exists():
        try:
            with open(state_file, 'rb') as f:
                hashes = pickle.load(f)
            logger.info(f"Loaded {len(hashes)} processed validation hashes")
            return hashes
        except Exception as e:
            logger.warning(f"Failed to load validation hashes: {e}")
    return set()


def save_processed_validation_hashes(hashes: Set[str], state_file: Path) -> None:
    """Save hashes of validated chunks."""
    try:
        with open(state_file, 'wb') as f:
            pickle.dump(hashes, f)
        logger.info(f"Saved {len(hashes)} validation hashes")
    except Exception as e:
        logger.error(f"Failed to save validation hashes: {e}")


def load_tagged_chunks(input_file: Path) -> List[Dict]:
    """Load tagged chunks from JSONL file."""
    chunks = []
    with jsonlines.open(input_file) as reader:
        for chunk in reader:
            chunks.append(chunk)
    
    logger.info(f"Loaded {len(chunks)} tagged chunks from {input_file}")
    return chunks


def save_validated_chunks(chunks: List[Dict], output_file: Path) -> None:
    """Save validated chunks to JSONL file."""
    with jsonlines.open(output_file, 'w') as writer:
        for chunk in chunks:
            writer.write(chunk)
    
    logger.info(f"Saved {len(chunks)} validated chunks to {output_file}")


def validate_chunks_batch(
    chunks: List[Dict],
    model: str = "tinyllama:latest",
    temperature: float = 0.2,
    max_retries: int = 3,
    delay_between_calls: float = 0.1,
    force_reprocess: bool = False
) -> List[Dict]:
    """
    Validate a batch of tagged chunks.
    
    Args:
        chunks: List of tagged chunks to validate
        model: Local model to use for validation
        temperature: Model temperature
        max_retries: Maximum retries for failed calls
        delay_between_calls: Delay between API calls
        force_reprocess: Force reprocess all chunks
    
    Returns:
        List of validated chunks
    """
    # Initialize tagger for validation only
    tagger = LocalEnhancedChunkTagger(
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay_between_calls,
        enable_validation=True,
        enable_conversation_context=False  # No need for conversation context in validation
    )
    
    validated_chunks = []
    
    for chunk in tqdm(chunks, desc="Validating chunks"):
        try:
            # Extract current tags
            current_tags = chunk.get('tags', [])
            
            # Validate tags
            is_valid, suggested_tags, reasoning = tagger.validate_tags(
                chunk.get('content', ''),
                current_tags,
                ""
            )
            
            # Update chunk with validation results
            validated_chunk = {
                **chunk,
                'tags': suggested_tags,
                'validation_is_valid': is_valid,
                'validation_reasoning': reasoning,
                'validation_timestamp': int(time.time()),
                'validation_model': f"local-{model}"
            }
            
            # Add validation issues if tags were changed
            if not is_valid or suggested_tags != current_tags:
                validated_chunk['validation_issues'] = [reasoning]
            
            validated_chunks.append(validated_chunk)
            
        except Exception as e:
            logger.warning(f"Failed to validate chunk: {e}")
            # Keep original chunk with validation failure marker
            validated_chunk = {
                **chunk,
                'validation_is_valid': False,
                'validation_reasoning': f"Validation failed: {str(e)}",
                'validation_timestamp': int(time.time()),
                'validation_model': f"local-{model}",
                'validation_issues': [f"Validation failed: {str(e)}"]
            }
            validated_chunks.append(validated_chunk)
    
    return validated_chunks


@click.command()
@click.option('--input-file', 
              default='data/processed/local_enhanced_tagged_chunks.jsonl',
              help='Input JSONL file with tagged chunks')
@click.option('--output-file', 
              default='data/processed/local_validated_tagged_chunks.jsonl',
              help='Output JSONL file for validated chunks')
@click.option('--state-file',
              default='data/processed/local_validation_state.pkl',
              help='State file for tracking validated chunks')
@click.option('--model', 
              default='tinyllama:latest',
              help='Local model to use for validation')
@click.option('--temperature', 
              default=0.2,
              help='Temperature for model generation')
@click.option('--max-retries', 
              default=3,
              help='Maximum retries for failed calls')
@click.option('--delay', 
              default=0.5,
              help='Delay between API calls (seconds)')
@click.option('--force', is_flag=True, help='Force reprocess all chunks (ignore state)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run validation')
def main(input_file: str, output_file: str, state_file: str, model: str, temperature: float,
         max_retries: int, delay: float, force: bool, check_only: bool):
    """
    Run tag validation as a separate step.
    
    This script validates already-tagged chunks independently of the tagging process.
    This allows for faster initial tagging and independent validation retries.
    
    EXAMPLES:
    # Validate all tagged chunks
    python3 chatmind/tagger/local/run_tag_validation.py
    
    # Validate with different model
    python3 chatmind/tagger/local/run_tag_validation.py --model tinyllama:latest
    
    # Check setup only
    python3 chatmind/tagger/local/run_tag_validation.py --check-only
    """
    
    print(f"🔍 ChatMind Tag Validator - {model.upper()}")
    print("=" * 50)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Model: {model}")
    print(f"Force reprocess: {'yes' if force else 'no'}")
    print()
    
    if check_only:
        print("🔍 Checking setup only...")
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                print(f"✅ Ollama is running")
                print(f"✅ Available models: {', '.join(available_models)}")
                if model in available_models:
                    print(f"✅ Model {model} is available")
                else:
                    print(f"❌ Model {model} is not available")
                return
            else:
                print("❌ Ollama is not responding properly")
                return
        except Exception as e:
            print(f"❌ Cannot connect to Ollama: {e}")
            return
    
    # Validate input file exists
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_file}")
        print("   Run tagging first: python3 chatmind/tagger/run_tagging.py --method local")
        return 1
    
    # Load tagged chunks
    chunks = load_tagged_chunks(input_path)
    if not chunks:
        print("❌ No tagged chunks found in input file")
        return 1
    
    # Load validation state
    state_path = Path(state_file)
    processed_hashes = set()
    if not force:
        processed_hashes = load_processed_validation_hashes(state_path)
    
    # Identify chunks that need validation
    chunks_to_validate = []
    for chunk in chunks:
        chunk_hash = generate_chunk_hash(chunk)
        if force or chunk_hash not in processed_hashes:
            chunks_to_validate.append(chunk)
    
    if not chunks_to_validate:
        print("✅ All chunks already validated")
        return 0
    
    print(f"📊 Found {len(chunks_to_validate)} chunks to validate out of {len(chunks)} total")
    
    # Validate chunks
    validated_chunks = validate_chunks_batch(
        chunks_to_validate,
        model=model,
        temperature=temperature,
        max_retries=max_retries,
        delay_between_calls=delay,
        force_reprocess=force
    )
    
    # Update processed hashes
    for chunk in validated_chunks:
        chunk_hash = generate_chunk_hash(chunk)
        processed_hashes.add(chunk_hash)
    
    # Save results
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_validated_chunks(validated_chunks, output_path)
    save_processed_validation_hashes(processed_hashes, state_path)
    
    # Print statistics
    valid_count = sum(1 for chunk in validated_chunks if chunk.get('validation_is_valid', False))
    invalid_count = len(validated_chunks) - valid_count
    
    print(f"✅ Validation completed!")
    print(f"📊 Statistics:")
    print(f"   - Total chunks: {len(validated_chunks)}")
    print(f"   - Valid: {valid_count}")
    print(f"   - Invalid: {invalid_count}")
    print(f"   - Success rate: {valid_count/len(validated_chunks)*100:.1f}%")
    
    return 0


if __name__ == "__main__":
    exit(main()) 