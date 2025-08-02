#!/usr/bin/env python3
"""
ChatMind Pipeline Runner (Legacy Wrapper)

This is a wrapper that calls the new modular pipeline runner.
The new pipeline is located at: chatmind/pipeline/run_pipeline.py
"""

import subprocess
import sys
import click
from pathlib import Path
from typing import List

@click.command()
@click.option('--local', is_flag=True, help='Use local models for all steps (shorthand for --embedding-method local --tagging-method local --summarization-method local)')
@click.option('--embedding-method', 
              type=click.Choice(['local', 'cloud']),
              default='local',
              help='Embedding method to use')
@click.option('--tagging-method', 
              type=click.Choice(['local', 'cloud']),
              default='local',
              help='Tagging method to use')
@click.option('--summarization-method', 
              type=click.Choice(['local', 'cloud']),
              default='local',
              help='Summarization method to use')
@click.option('--force', is_flag=True, help='Force reprocess all steps')
@click.option('--steps', 
              multiple=True,
              type=click.Choice(['ingestion', 'chunking', 'embedding', 'clustering', 
                               'tagging', 'tag_post_processing', 'tag_propagation', 'cluster_summarization', 'chat_summarization',
                               'positioning', 'similarity', 'loading']),
              help='Specific steps to run (can specify multiple)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run pipeline')
def main(local: bool, embedding_method: str, tagging_method: str, summarization_method: str, 
         force: bool, steps: List[str], check_only: bool):
    """
    Run the ChatMind pipeline.
    
    This is a wrapper for the new modular pipeline runner.
    The actual pipeline is located at: chatmind/pipeline/run_pipeline.py
    
    EXAMPLES:
    # Run complete pipeline
    python3 run_pipeline.py
    
    # Run with specific methods
    python3 run_pipeline.py --embedding-method cloud --tagging-method local
    
    # Run only specific steps
    python3 run_pipeline.py --steps ingestion chunking embedding
    
    # Run summarization steps
    python3 run_pipeline.py --steps cluster_summarization chat_summarization
    
    # Force reprocess everything
    python3 run_pipeline.py --force
    """
    
    # Call the new modular pipeline runner
    pipeline_script = Path("chatmind/pipeline/run_pipeline.py")
    
    if not pipeline_script.exists():
        print("❌ New pipeline runner not found!")
        print("Expected location: chatmind/pipeline/run_pipeline.py")
        return 1
    
    # Build command arguments
    cmd = [sys.executable, str(pipeline_script)]
    
    # If --local flag is used, override all methods to local
    if local:
        embedding_method = 'local'
        tagging_method = 'local'
        summarization_method = 'local'
    
    if embedding_method != 'local':
        cmd.extend(['--embedding-method', embedding_method])
    
    if tagging_method != 'local':
        cmd.extend(['--tagging-method', tagging_method])
    
    if summarization_method != 'local':
        cmd.extend(['--summarization-method', summarization_method])
    
    if force:
        cmd.append('--force')
    
    if steps:
        for step in steps:
            cmd.extend(['--steps', step])
    
    if check_only:
        cmd.append('--check-only')
    
    # Run the new pipeline
    print("🔄 Calling new modular pipeline runner...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline failed with exit code: {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    main() 