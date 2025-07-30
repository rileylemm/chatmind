#!/usr/bin/env python3
"""
ChatMind Summarization Selection Script

Choose between different summarization approaches:
- Cloud API (OpenAI): High quality, costs money
- Local Model (Gemma/TinyLlama): Free, good quality

Uses modular directory structure: data/processed/summarization/
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
              default='data/processed/tagging/chunk_tags.jsonl',
              help='Input JSONL file with chunk tags')
@click.option('--output-file', 
              default='data/processed/summarization/cluster_summaries.json',
              help='Output JSON file for cluster summaries')
@click.option('--model', 
              default=None,
              help='Model to use (auto-selected based on method)')
@click.option('--force', is_flag=True, help='Force reprocess all clusters (ignore state)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run summarization')
def main(method: str, input_file: str, output_file: str, model: str, 
         force: bool, check_only: bool):
    """
    Run ChatMind summarization with your choice of method.
    
    METHODS:
    - cloud: Use OpenAI API (high quality, costs money)
    - local: Use local models via Ollama (free, good quality)
    
    EXAMPLES:
    # Quick local summarization
    python3 chatmind/pipeline/summarization/run_summarization.py --method local
    
    # Cloud summarization with specific model
    python3 chatmind/pipeline/summarization/run_summarization.py --method cloud --model gpt-4
    
    # Check local setup only
    python3 chatmind/pipeline/summarization/run_summarization.py --method local --check-only
    """
    
    # Auto-select model if not specified
    if model is None:
        if method == 'cloud':
            model = 'gpt-3.5-turbo'
        else:
            model = 'gemma:2b'
    
    print(f"📝 ChatMind Summarizer - {method.upper()} Method")
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
    
    # Check if openai package is installed
    try:
        import openai
        print("✅ OpenAI package is installed")
    except ImportError:
        print("❌ OpenAI package not installed")
        print("   Install with: pip install openai")
        return False
    
    print("✅ Cloud API setup looks good!")
    return True


def check_local_setup():
    """Check if local setup is ready."""
    print("🔍 Checking Local setup...")
    
    # Check if Ollama is running
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is running")
        else:
            print("❌ Ollama is not running")
            print("   Start with: ollama serve")
            return False
    except FileNotFoundError:
        print("❌ Ollama not found")
        print("   Install from: https://ollama.ai")
        return False
    
    # Check if required models are available
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if 'gemma:2b' in result.stdout:
            print("✅ Gemma:2b model is available")
        else:
            print("⚠️ Gemma:2b model not found")
            print("   Pull with: ollama pull gemma:2b")
    except Exception as e:
        print(f"⚠️ Could not check models: {e}")
    
    print("✅ Local setup looks good!")
    return True


def run_cloud_summarization(input_file: str, output_file: str, model: str, 
                           force: bool) -> int:
    """Run cloud summarization using OpenAI API."""
    print("☁️ Running cloud summarization...")
    
    # Determine script path based on method
    if method == "cloud":
        script_path = Path("chatmind/pipeline/cluster_summarization/cloud_api/enhanced_cluster_summarizer.py")
    else:
        script_path = Path("chatmind/pipeline/cluster_summarization/local/local_enhanced_cluster_summarizer.py")
    
    if not script_path.exists():
        print(f"❌ Cloud summarization script not found: {script_path}")
        return 1
    
    command = [
        sys.executable, str(script_path),
        "--input-file", input_file,
        "--output-file", output_file,
        "--model", model
    ]
    
    if force:
        command.append("--force")
    
    try:
        result = subprocess.run(command, check=True)
        print("✅ Cloud summarization completed successfully!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Cloud summarization failed: {e}")
        return e.returncode


def run_local_summarization(input_file: str, output_file: str, model: str, 
                           force: bool) -> int:
    """Run local summarization using Ollama."""
    print("🏠 Running local summarization...")
    
    script_path = Path("chatmind/pipeline/summarization/local/local_enhanced_cluster_summarizer.py")
    
    if not script_path.exists():
        print(f"❌ Local summarization script not found: {script_path}")
        return 1
    
    command = [
        sys.executable, str(script_path),
        "--input-file", input_file,
        "--output-file", output_file,
        "--model", model
    ]
    
    if force:
        command.append("--force")
    
    try:
        result = subprocess.run(command, check=True)
        print("✅ Local summarization completed successfully!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Local summarization failed: {e}")
        return e.returncode


if __name__ == "__main__":
    main() 