#!/usr/bin/env python3
"""
ChatMind Cluster Summary Selection Script

Choose between different cluster summarization approaches:
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
              prompt='Choose summarization method',
              help='Summarization method to use')
@click.option('--input-file', 
              default='data/embeddings/chunks_with_clusters.jsonl',
              help='Input JSONL file with chunks')
@click.option('--output-file', 
              default=None,
              help='Output JSON file for cluster summaries (auto-generated if not specified)')
@click.option('--model', 
              default=None,
              help='Model to use (auto-selected based on method)')
@click.option('--force', is_flag=True, help='Force reprocess all clusters (ignore state)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run summarization')
def main(method: str, input_file: str, output_file: str, model: str, 
         force: bool, check_only: bool):
    """
    Run ChatMind cluster summarization with your choice of method.
    
    METHODS:
    - cloud: Use OpenAI API (fast, high quality, costs money)
    - local: Use local models via Ollama (free, slower, good quality)
    
    EXAMPLES:
    # Quick cloud summarization
    python3 chatmind/embedding/run_cluster_summaries.py --method cloud
    
    # Local summarization with specific model
    python3 chatmind/embedding/run_cluster_summaries.py --method local --model mistral:latest
    
    # Check local setup only
    python3 chatmind/embedding/run_cluster_summaries.py --method local --check-only
    """
    
    # Auto-generate output file if not specified
    if output_file is None:
        if method == 'cloud':
            output_file = 'data/embeddings/enhanced_cluster_summaries.json'
        else:
            output_file = 'data/embeddings/local_enhanced_cluster_summaries.json'
    
    # Auto-select model if not specified
    if model is None:
        if method == 'cloud':
            model = 'gpt-3.5-turbo'
        else:
            model = 'mistral:latest'
    
    print(f"📊 ChatMind Cluster Summarizer - {method.upper()} Method")
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
    
    # Run the appropriate summarizer
    if method == 'cloud':
        return run_cloud_summarization(input_file, output_file, model, force)
    else:
        return run_local_summarization(input_file, output_file, model, force)


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


def run_cloud_summarization(input_file: str, output_file: str, model: str, force: bool) -> int:
    """Run cloud API summarization."""
    print("☁️  Running Cloud API Enhanced Cluster Summarization...")
    
    # Check cloud setup
    if not check_cloud_setup():
        return 1
    
    # Build command
    cmd = [
        sys.executable, 
        "chatmind/summarizer/cloud_api/enhanced_cluster_summarizer.py",
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
        print("✅ Cloud API cluster summarization completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Cloud API cluster summarization failed: {e}")
        return 1


def run_local_summarization(input_file: str, output_file: str, model: str, force: bool) -> int:
    """Run local model summarization."""
    print("🏠 Running Local Model Enhanced Cluster Summarization...")
    
    # Check local setup
    if not check_local_setup():
        return 1
    
    # Build command
    cmd = [
        sys.executable, 
        "chatmind/summarizer/local/local_enhanced_cluster_summarizer.py",
        "--input-file", input_file,
        "--output-file", output_file,
        "--model", model,
        "--delay", "0.5"
    ]
    
    if force:
        cmd.append("--force")
    
    # Set environment
    env = os.environ.copy()
    env['PYTHONPATH'] = '.'
    
    try:
        subprocess.run(cmd, check=True, env=env)
        print("✅ Local model cluster summarization completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Local model cluster summarization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 