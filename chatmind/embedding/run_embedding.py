#!/usr/bin/env python3
"""
ChatMind Embedding Selection Script

Choose between different embedding approaches:
- Cloud API (OpenAI): High quality, costs money
- Local Model (Sentence Transformers): Free, good quality
"""

import click
import subprocess
import sys
import os
from pathlib import Path

@click.command()
@click.option('--method', 
              type=click.Choice(['cloud', 'local']),
              prompt='Choose embedding method',
              help='Embedding method to use')
@click.option('--chats-file', 
              default='data/processed/chats.jsonl',
              help='Input JSONL file with chat messages')
@click.option('--state-file', 
              default=None,
              help='State file for tracking processed messages (auto-generated if not specified)')
@click.option('--model', 
              default=None,
              help='Model to use (auto-selected based on method)')
@click.option('--force', is_flag=True, help='Force reprocess all messages (ignore state)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run embedding')
def main(method: str, chats_file: str, state_file: str, model: str, 
         force: bool, check_only: bool):
    """
    Run ChatMind embedding with your choice of method.
    
    METHODS:
    - cloud: Use OpenAI API (high quality, costs money)
    - local: Use local models via Sentence Transformers (free, good quality)
    
    EXAMPLES:
    # Quick local embedding
    python3 chatmind/embedding/run_embedding.py --method local
    
    # Cloud embedding with specific model
    python3 chatmind/embedding/run_embedding.py --method cloud --model text-embedding-3-large
    
    # Check local setup only
    python3 chatmind/embedding/run_embedding.py --method local --check-only
    """
    
    # Auto-generate state file if not specified
    if state_file is None:
        if method == 'cloud':
            state_file = 'data/processed/cloud_embedding_state.pkl'
        else:
            state_file = 'data/processed/direct_embedding_state.pkl'
    
    # Auto-select model if not specified
    if model is None:
        if method == 'cloud':
            model = 'text-embedding-3-small'
        else:
            model = 'all-MiniLM-L6-v2'
    
    print(f"🧠 ChatMind Embedder - {method.upper()} Method")
    print("=" * 50)
    print(f"Input: {chats_file}")
    print(f"State: {state_file}")
    print(f"Model: {model}")
    print(f"Force reprocess: {'yes' if force else 'no'}")
    print()
    
    if check_only:
        print("🔍 Checking setup only...")
        if method == 'local':
            check_local_setup()
        else:
            check_cloud_setup()
        return
    
    # Validate input file exists
    if not Path(chats_file).exists():
        print(f"❌ Input file not found: {chats_file}")
        return 1
    
    # Run the appropriate embedder
    if method == 'cloud':
        return run_cloud_embedding(chats_file, state_file, model, force)
    else:
        return run_local_embedding(chats_file, state_file, model, force)


def check_cloud_setup():
    """Check if cloud API setup is ready."""
    print("🔍 Checking Cloud API setup...")
    
    # Check if OpenAI API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-api-key'")
        return False
    
    print("✅ OpenAI API key is configured")
    print("✅ Cloud API setup is ready")
    return True


def check_local_setup():
    """Check if local model setup is ready."""
    print("🔍 Checking Local Model setup...")
    
    try:
        import sentence_transformers
        print("✅ Sentence Transformers is available")
        
        # Test loading a model
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Local model setup is ready")
        return True
    except ImportError as e:
        print(f"❌ Sentence Transformers not available: {e}")
        print("   Install with: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"❌ Local model setup failed: {e}")
        return False


def run_cloud_embedding(chats_file: str, state_file: str, model: str, force: bool) -> int:
    """Run cloud API embedding."""
    print("☁️  Running Cloud API Enhanced Embedding...")
    
    # Check cloud setup
    if not check_cloud_setup():
        return 1
    
    # Build command
    cmd = [
        sys.executable, 
        "chatmind/embedding/cloud_api/enhanced_embedder.py",
        "--chats-file", chats_file,
        "--state-file", state_file,
        "--model", model,
        "--delay", "0.1"
    ]
    
    if force:
        cmd.append("--force")
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    try:
        subprocess.run(cmd, check=True, env=env)
        print("✅ Cloud API embedding completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Cloud API embedding failed: {e}")
        return 1


def run_local_embedding(chats_file: str, state_file: str, model: str, force: bool) -> int:
    """Run local model embedding."""
    print("🏠 Running Local Model Embedding...")
    
    # Check local setup
    if not check_local_setup():
        return 1
    
    # Build command
    cmd = [
        sys.executable, 
        "chatmind/embedding/local/embed_and_cluster_direct_incremental.py",
        "--chats-file", chats_file,
        "--state-file", state_file,
        "--model", model
    ]
    
    if force:
        cmd.append("--force")
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    try:
        subprocess.run(cmd, check=True, env=env)
        print("✅ Local model embedding completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Local model embedding failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 