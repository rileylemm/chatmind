#!/usr/bin/env python3
"""
ChatMind Tagging Selection Script

Choose between different tagging approaches:
- Cloud API (OpenAI): High quality, costs money
- Local Model (Gemma/TinyLlama): Free, good quality

Uses modular directory structure: data/processed/tagging/
"""

import click
import subprocess
import sys
import os
from pathlib import Path

@click.command()
@click.option('--method', 
              type=click.Choice(['cloud', 'local']),
              prompt='Choose tagging method',
              help='Tagging method to use')
@click.option('--input-file', 
              default='data/processed/ingestion/chats.jsonl',
              help='Input JSONL file with chats (messages)')
@click.option('--output-file', 
              default='data/processed/tagging/tagged_messages.jsonl',
              help='Output JSONL file for tagged messages')
@click.option('--model', 
              default=None,
              help='Model to use (auto-selected based on method)')
@click.option('--force', is_flag=True, help='Force reprocess all chunks (ignore state)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run tagging')
def main(method: str, input_file: str, output_file: str, model: str, 
         force: bool, check_only: bool):
    """
    Run ChatMind tagging with your choice of method.
    
    METHODS:
    - cloud: Use OpenAI API (high quality, costs money)
    - local: Use local models via Ollama (free, good quality)
    
    EXAMPLES:
    # Quick local tagging
    python3 chatmind/pipeline/tagging/run_tagging.py --method local
    
    # Cloud tagging with specific model
    python3 chatmind/pipeline/tagging/run_tagging.py --method cloud --model gpt-4
    
    # Check local setup only
    python3 chatmind/pipeline/tagging/run_tagging.py --method local --check-only
    """
    
    # Auto-select model if not specified
    if model is None:
        if method == 'cloud':
            model = 'gpt-4'
        else:
            model = 'gemma:2b'
    
    print(f"🏷️ ChatMind Tagger - {method.upper()} Method")
    print("=" * 50)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
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
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return 1
    
    # Run the appropriate tagger
    if method == 'cloud':
        return run_cloud_tagging(input_file, output_file, model, force)
    else:
        return run_local_tagging(input_file, output_file, model, force)


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
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            available_models = [model['name'] for model in models]
            print(f"✅ Ollama is running")
            print(f"✅ Available models: {', '.join(available_models)}")
            return True
        else:
            print("❌ Ollama is not responding properly")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False


def run_cloud_tagging(input_file: str, output_file: str, model: str, 
                     force: bool) -> int:
    """Run cloud API tagging."""
    print("☁️  Running Cloud API Enhanced Tagging...")
    
    # Check cloud setup
    if not check_cloud_setup():
        return 1
    
    # Build command
    cmd = [
        sys.executable, 
        "chatmind/tagger/cloud_api/run_enhanced_tagging_incremental.py",
        "--input-file", input_file,
        "--output-file", output_file,
        "--model", model,
        "--delay", "1.0"
    ]
    
    if force:
        cmd.append("--force")
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    try:
        subprocess.run(cmd, check=True, env=env)
        print("✅ Cloud API tagging completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Cloud API tagging failed: {e}")
        return 1


def run_local_tagging(input_file: str, output_file: str, model: str, 
                     force: bool) -> int:
    """Run local model tagging."""
    print("🏠 Running Local Model Enhanced Tagging...")
    
    # Check local setup
    if not check_local_setup():
        return 1
    
    # Build command
    cmd = [
        sys.executable, 
        "chatmind/tagger/local/run_local_enhanced_tagging.py",
        "--input-file", input_file,
        "--output-file", output_file,
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
        print("✅ Local model tagging completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Local model tagging failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 