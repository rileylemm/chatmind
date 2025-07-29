#!/usr/bin/env python3
"""
ChatMind Tagger Selection Script

Choose between different tagging approaches:
- Cloud API (OpenAI): Fast, high quality, but costs money
- Local Model (Ollama): Free, slower, good quality
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
              default='data/embeddings/chunks_with_clusters.jsonl',
              help='Input JSONL file with chunks')
@click.option('--output-file', 
              default=None,
              help='Output JSONL file for tagged chunks (auto-generated if not specified)')
@click.option('--model', 
              default=None,
              help='Model to use (auto-selected based on method)')
@click.option('--enable-validation/--disable-validation',
              default=False,
              help='Enable/disable tag validation (disabled by default for speed)')
@click.option('--enable-conversation-context/--disable-conversation-context',
              default=True,
              help='Enable/disable conversation-level context')
@click.option('--force', is_flag=True, help='Force reprocess all chunks (ignore state)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run tagging')
def main(method: str, input_file: str, output_file: str, model: str, 
         enable_validation: bool, enable_conversation_context: bool, 
         force: bool, check_only: bool):
    """
    Run ChatMind tagging with your choice of method.
    
    METHODS:
    - cloud: Use OpenAI API (fast, high quality, costs money)
    - local: Use local models via Ollama (free, slower, good quality)
    
    EXAMPLES:
    # Quick cloud tagging
    python3 chatmind/tagger/run_tagging.py --method cloud
    
    # Local tagging with specific model
    python3 chatmind/tagger/run_tagging.py --method local --model mistral:latest
    
    # Check local setup only
    python3 chatmind/tagger/run_tagging.py --method local --check-only
    """
    
    # Auto-generate output file if not specified
    if output_file is None:
        if method == 'cloud':
            output_file = 'data/processed/enhanced_tagged_chunks.jsonl'
        else:
            output_file = 'data/processed/local_enhanced_tagged_chunks.jsonl'
    
    # Auto-select model if not specified
    if model is None:
        if method == 'cloud':
            model = 'gpt-3.5-turbo'
        else:
            model = 'gemma:2b'
    
    print(f"🤖 ChatMind Tagger - {method.upper()} Method")
    print("=" * 50)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Model: {model}")
    print(f"Validation: {'enabled' if enable_validation else 'disabled'}")
    print(f"Conversation Context: {'enabled' if enable_conversation_context else 'disabled'}")
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
        return run_cloud_tagging(input_file, output_file, model, enable_validation, 
                               enable_conversation_context, force)
    else:
        return run_local_tagging(input_file, output_file, model, enable_validation, 
                               enable_conversation_context, force)


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
                     enable_validation: bool, enable_conversation_context: bool, force: bool) -> int:
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
    
    if not enable_validation:
        cmd.append("--disable-validation")
    if not enable_conversation_context:
        cmd.append("--disable-conversation-context")
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
                     enable_validation: bool, enable_conversation_context: bool, force: bool) -> int:
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
    
    if not enable_validation:
        cmd.append("--disable-validation")
    if not enable_conversation_context:
        cmd.append("--disable-conversation-context")
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