#!/usr/bin/env python3
"""
ChatMind Unified Pipeline Runner

Smart pipeline that handles both first-time processing and incremental updates.
Automatically detects what needs to be processed and skips already completed steps.
"""

import subprocess
import sys
import os
from pathlib import Path
import click
import logging
import jsonlines
import pickle
import hashlib
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists and has content."""
    return file_path.exists() and file_path.stat().st_size > 0


def get_processed_chat_hashes() -> set:
    """Get hashes of chats that have been processed."""
    state_file = Path("data/processed/chat_processing_state.pkl")
    if state_file.exists():
        try:
            with open(state_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load chat processing state: {e}")
    return set()


def save_processed_chat_hashes(hashes: set) -> None:
    """Save hashes of processed chats."""
    state_file = Path("data/processed/chat_processing_state.pkl")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_file, 'wb') as f:
            pickle.dump(hashes, f)
        logger.info(f"Saved {len(hashes)} processed chat hashes")
    except Exception as e:
        logger.error(f"Failed to save chat processing state: {e}")


def get_processed_message_hashes() -> set:
    """Get hashes of messages that have been embedded."""
    state_file = Path("data/processed/direct_embedding_state.pkl")
    if state_file.exists():
        try:
            with open(state_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load message embedding state: {e}")
    return set()


def save_processed_message_hashes(hashes: set) -> None:
    """Save hashes of processed messages."""
    state_file = Path("data/processed/direct_embedding_state.pkl")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_file, 'wb') as f:
            pickle.dump(hashes, f)
        logger.info(f"Saved {len(hashes)} processed message hashes")
    except Exception as e:
        logger.error(f"Failed to save message embedding state: {e}")


def get_processed_chunk_hashes() -> set:
    """Get hashes of chunks that have been tagged."""
    state_file = Path("data/processed/enhanced_tagging_state.pkl")
    if state_file.exists():
        try:
            with open(state_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load enhanced chunk tagging state: {e}")
    return set()


def save_processed_chunk_hashes(hashes: set) -> None:
    """Save hashes of processed chunks."""
    state_file = Path("data/processed/enhanced_tagging_state.pkl")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_file, 'wb') as f:
            pickle.dump(hashes, f)
        logger.info(f"Saved {len(hashes)} processed chunk hashes")
    except Exception as e:
        logger.error(f"Failed to save enhanced chunk tagging state: {e}")


def check_needs_processing() -> dict:
    """Check what needs to be processed based on existing state."""
    needs_processing = {
        'ingestion': False,
        'embedding': False,
        'tagging': False,
        'summarization': False,
        'positioning': False,
        'loading': False
    }
    
    # Check if chats.jsonl exists and has content
    chats_file = Path("data/processed/chats.jsonl")
    if not check_file_exists(chats_file):
        logger.info("📥 Data ingestion needed: No chats.jsonl found")
        needs_processing['ingestion'] = True
        needs_processing['embedding'] = True
        needs_processing['tagging'] = True
        needs_processing['summarization'] = True
        needs_processing['positioning'] = True
        needs_processing['loading'] = True
        return needs_processing
    
    # Check if embeddings exist
    embeddings_file = Path("data/embeddings/chunks_with_clusters.jsonl")
    if not check_file_exists(embeddings_file):
        logger.info("🧠 Embedding needed: No chunks_with_clusters.jsonl found")
        needs_processing['embedding'] = True
        needs_processing['tagging'] = True
        needs_processing['loading'] = True
    else:
        # Check if there are new messages to embed
        try:
            processed_hashes = get_processed_message_hashes()
            total_messages = 0
            new_messages = 0
            
            with jsonlines.open(chats_file) as reader:
                for chat in reader:
                    for message in chat.get('messages', []):
                        if message.get('role') in ['user', 'assistant'] and message.get('content', '').strip():
                            total_messages += 1
                            # Create hash similar to the embedding script
                            message_hash = hashlib.sha256(
                                json.dumps({
                                    'content': message.get('content', ''),
                                    'chat_id': chat.get('content_hash', ''),
                                    'message_id': f"{chat.get('content_hash', '')}_{message.get('id', '')}",
                                    'role': message.get('role', ''),
                                    'timestamp': message.get('timestamp')
                                }, sort_keys=True).encode()
                            ).hexdigest()
                            
                            if message_hash not in processed_hashes:
                                new_messages += 1
            
            if new_messages > 0:
                logger.info(f"🧠 Embedding needed: {new_messages} new messages out of {total_messages} total")
                needs_processing['embedding'] = True
                needs_processing['tagging'] = True
                needs_processing['loading'] = True
            else:
                logger.info("✅ Embedding up to date: All messages already processed")
                
        except Exception as e:
            logger.warning(f"Could not check message state: {e}")
            needs_processing['embedding'] = True
            needs_processing['tagging'] = True
            needs_processing['loading'] = True
    
    # Check if enhanced tagging exists
    tagged_file = Path("data/processed/enhanced_tagged_chunks.jsonl")
    if not check_file_exists(tagged_file):
        logger.info("🏷️ Enhanced tagging needed: No enhanced_tagged_chunks.jsonl found")
        needs_processing['tagging'] = True
        needs_processing['loading'] = True
    else:
        # Check if there are new chunks to tag
        try:
            processed_hashes = get_processed_chunk_hashes()
            total_chunks = 0
            new_chunks = 0
            
            with jsonlines.open(embeddings_file) as reader:
                for chunk in reader:
                    total_chunks += 1
                    chunk_hash = hashlib.sha256(
                        json.dumps({
                            'content': chunk.get('content', ''),
                            'chat_id': chunk.get('chat_id', ''),
                            'message_id': chunk.get('message_id', ''),
                            'role': chunk.get('role', ''),
                            'cluster_id': chunk.get('cluster_id', '')
                        }, sort_keys=True).encode()
                    ).hexdigest()
                    
                    if chunk_hash not in processed_hashes:
                        new_chunks += 1
            
            if new_chunks > 0:
                logger.info(f"🏷️ Enhanced tagging needed: {new_chunks} new chunks out of {total_chunks} total")
                needs_processing['tagging'] = True
                needs_processing['loading'] = True
            else:
                logger.info("✅ Enhanced tagging up to date: All chunks already processed")
                
        except Exception as e:
            logger.warning(f"Could not check chunk state: {e}")
            needs_processing['tagging'] = True
            needs_processing['loading'] = True
    
    # Check if cluster summarization is needed
    cluster_summaries_file = Path("data/embeddings/enhanced_cluster_summaries.json")
    local_summaries_file = Path("data/embeddings/local_enhanced_cluster_summaries.json")
    cloud_exists = check_file_exists(cluster_summaries_file)
    local_exists = check_file_exists(local_summaries_file)
    logger.info(f"📊 Checking cluster summaries: cloud={cloud_exists}, local={local_exists}")
    if not cloud_exists and not local_exists:
        logger.info("📊 Cluster summarization needed: No cluster summaries found")
        needs_processing['summarization'] = True
    else:
        logger.info("✅ Cluster summarization up to date: Cluster summaries exist")
    
    # Check if semantic positioning is needed
    topics_with_coords_file = Path("data/processed/topics_with_coords.jsonl")
    if not check_file_exists(topics_with_coords_file):
        logger.info("🗺️ Semantic positioning needed: No topics_with_coords.jsonl found")
        needs_processing['positioning'] = True
        needs_processing['loading'] = True
    else:
        logger.info("✅ Semantic positioning up to date: Topics with coordinates exist")
    
    # Check if Neo4j needs loading
    if needs_processing['tagging'] or needs_processing['positioning'] or needs_processing['summarization']:
        logger.info("🗄️ Neo4j loading needed: New tagged data, coordinates, or summaries available")
        needs_processing['loading'] = True
    else:
        logger.info("✅ Neo4j up to date: No new data to load")
    
    return needs_processing


@click.command()
@click.option('--skip-ingestion', is_flag=True, help='Skip data ingestion step')
@click.option('--skip-embedding', is_flag=True, help='Skip embedding and clustering step')
@click.option('--skip-tagging', is_flag=True, help='Skip auto-tagging step')
@click.option('--skip-summarization', is_flag=True, help='Skip cluster summarization step')
@click.option('--skip-positioning', is_flag=True, help='Skip semantic positioning step')
@click.option('--skip-loading', is_flag=True, help='Skip Neo4j loading step')
@click.option('--cloud', is_flag=True, help='Use cloud API for all AI components (embedding, tagging, summarization)')
@click.option('--local', is_flag=True, help='Use local models for all AI components (embedding, tagging, summarization)')
@click.option('--tagger-method', 
              type=click.Choice(['cloud', 'local']), 
              default='cloud',
              help='Tagger method to use (cloud or local)')
@click.option('--embedder-method', 
              type=click.Choice(['cloud', 'local']), 
              default='local',
              help='Embedder method to use (cloud or local)')
@click.option('--summarizer-method', 
              type=click.Choice(['cloud', 'local']), 
              default='cloud',
              help='Summarizer method to use (cloud or local)')
@click.option('--clear-neo4j', is_flag=True, help='Clear existing Neo4j data before loading')
@click.option('--force-reprocess', is_flag=True, help='Force reprocess all files (ignore previous state)')
@click.option('--clear-state', is_flag=True, help='Clear all processed state and start fresh')
@click.option('--check-only', is_flag=True, help='Only check what needs processing, don\'t run pipeline')
def main(skip_ingestion: bool, skip_embedding: bool, skip_tagging: bool, skip_summarization: bool, skip_positioning: bool, skip_loading: bool, 
         cloud: bool, local: bool, embedder_method: str, tagger_method: str, summarizer_method: str, clear_neo4j: bool, force_reprocess: bool, clear_state: bool, check_only: bool):
    """Run the complete ChatMind pipeline with smart incremental processing."""
    
    # Override individual methods if cloud/local flags are used
    if cloud:
        embedder_method = 'cloud'
        tagger_method = 'cloud'
        summarizer_method = 'cloud'
        logger.info("☁️  Using cloud API for all AI components")
    elif local:
        embedder_method = 'local'
        tagger_method = 'local'
        summarizer_method = 'local'
        logger.info("🏠 Using local models for all AI components")
    
    logger.info("🚀 Starting ChatMind unified pipeline...")
    
    # Clear state if requested
    if clear_state:
        logger.info("🧹 Clearing all processing state...")
        state_files = [
            "data/processed/chat_processing_state.pkl",
            "data/processed/direct_embedding_state.pkl", 
            "data/processed/enhanced_tagging_state.pkl"
        ]
        for state_file in state_files:
            Path(state_file).unlink(missing_ok=True)
        logger.info("✅ State cleared")
    
    # Check what needs processing
    if force_reprocess:
        logger.info("🔄 Force reprocess mode: Will process everything")
        needs_processing = {
            'ingestion': not skip_ingestion,
            'embedding': not skip_embedding,
            'tagging': not skip_tagging,
            'positioning': not skip_positioning,
            'loading': not skip_loading
        }
    else:
        logger.info("🔍 Checking what needs processing...")
        needs_processing = check_needs_processing()
        
        # Apply skip flags
        if skip_ingestion:
            needs_processing['ingestion'] = False
        if skip_embedding:
            needs_processing['embedding'] = False
        if skip_tagging:
            needs_processing['tagging'] = False
        if skip_positioning:
            needs_processing['positioning'] = False
        if skip_loading:
            needs_processing['loading'] = False
    
    if check_only:
        logger.info("📋 Processing summary:")
        for step, needed in needs_processing.items():
            status = "🔄 NEEDS PROCESSING" if needed else "✅ UP TO DATE"
            logger.info(f"   {step.title()}: {status}")
        return 0
    
    # Step 1: Data Ingestion
    if needs_processing['ingestion']:
        logger.info("📥 Step 1: Extracting and flattening ChatGPT exports...")
        try:
            cmd = [sys.executable, "chatmind/data_ingestion/extract_and_flatten.py"]
            if force_reprocess:
                cmd.append("--force")
            # Set PYTHONPATH to include current directory
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            subprocess.run(cmd, check=True, env=env)
            logger.info("✅ Data ingestion completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Data ingestion failed: {e}")
            return 1
    else:
        logger.info("⏭️ Skipping data ingestion (already up to date)")
    
    # Step 2: Embedding and Clustering
    if needs_processing['embedding'] and not skip_embedding:
        logger.info(f"🧠 Step 2: Generating embeddings and clustering using {embedder_method} method...")
        try:
            # Use the new unified embedder interface
            cmd = [sys.executable, "chatmind/embedding/run_embedding.py", "--method", embedder_method]
            if force_reprocess:
                cmd.append("--force")
            # Set PYTHONPATH to include current directory
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            subprocess.run(cmd, check=True, env=env)
            logger.info("✅ Embedding and clustering completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Embedding and clustering failed: {e}")
            return 1
    elif skip_embedding:
        logger.info("⏭️ Skipping embedding and clustering (--skip-embedding flag)")
    else:
        logger.info("⏭️ Skipping embedding and clustering (already up to date)")
    
    # Step 3: Enhanced Auto-Tagging
    if needs_processing['tagging'] and not skip_tagging:
        logger.info(f"🏷️ Step 3: Enhanced auto-tagging chunks using {tagger_method} method...")
        try:
            # Use the new unified tagger interface
            cmd = [sys.executable, "chatmind/tagger/run_tagging.py", "--method", tagger_method]
            if force_reprocess:
                cmd.append("--force")
            # Set PYTHONPATH to include current directory
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            subprocess.run(cmd, check=True, env=env)
            logger.info("✅ Enhanced auto-tagging completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Enhanced auto-tagging failed: {e}")
            return 1
    elif skip_tagging:
        logger.info("⏭️ Skipping enhanced auto-tagging (--skip-tagging flag)")
    else:
        logger.info("⏭️ Skipping enhanced auto-tagging (already up to date)")
    
    # Step 3.5: Post-process tags to map to master list
    logger.info("🔧 Step 3.5: Post-processing tags...")
    try:
        cmd = [sys.executable, "chatmind/tagger/post_process_tags.py"]
        # Set PYTHONPATH to include current directory
        env = os.environ.copy()
        env['PYTHONPATH'] = '.'
        subprocess.run(cmd, check=True, env=env)
        logger.info("✅ Tag post-processing completed")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Tag post-processing failed: {e}")
        return 1
    
    # Step 3.6: Generate cluster summaries for Neo4j
    if not skip_summarization:
        logger.info(f"📊 Step 3.6: Generating cluster summaries using {summarizer_method} method...")
        try:
            # Use the new unified cluster summary interface
            cmd = [sys.executable, "chatmind/summarizer/run_cluster_summaries.py", "--method", summarizer_method]
            if force_reprocess:
                cmd.append("--force")
            # Set PYTHONPATH to include current directory
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            subprocess.run(cmd, check=True, env=env)
            logger.info("✅ Cluster summaries generated")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Cluster summary generation failed: {e}")
            return 1
    else:
        logger.info("⏭️ Skipping cluster summarization (--skip-summarization flag)")
    
    # Step 3.7: Apply semantic positioning to topic nodes
    if needs_processing['positioning']:
        logger.info("🗺️ Step 3.7: Applying semantic positioning to topic nodes...")
        try:
            cmd = [sys.executable, "chatmind/semantic_positioning/apply_topic_layout.py"]
            if force_reprocess:
                cmd.append("--force")
            # Set PYTHONPATH to include current directory
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            subprocess.run(cmd, check=True, env=env)
            logger.info("✅ Semantic positioning completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Semantic positioning failed: {e}")
            return 1
    else:
        logger.info("⏭️ Skipping semantic positioning (already up to date)")
    
    # Step 4: Neo4j Loading
    if needs_processing['loading']:
        logger.info("🗄️ Step 4: Loading data into Neo4j...")
        try:
            cmd = [sys.executable, "chatmind/neo4j_loader/load_graph.py"]
            if clear_neo4j:
                cmd.append("--clear")
            # Set PYTHONPATH to include current directory
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            subprocess.run(cmd, check=True, env=env)
            logger.info("✅ Neo4j loading completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Neo4j loading failed: {e}")
            return 1
    else:
        logger.info("⏭️ Skipping Neo4j loading (already up to date)")
    
    logger.info("🎉 Pipeline completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Start the API server: python chatmind/api/main.py")
    logger.info("2. Start the frontend: cd chatmind/frontend && npm start")
    logger.info("3. Open http://localhost:3000 in your browser")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 