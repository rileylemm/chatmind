#!/usr/bin/env python3
"""
ChatMind Chat Summarization Runner

Orchestrates chat summarization using either local or cloud methods.
"""

import sys
import subprocess
from pathlib import Path
import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--method', 
              type=click.Choice(['local', 'cloud']),
              default='local',
              help='Summarization method to use')
@click.option('--chats-file', 
              default='data/processed/ingestion/chats.jsonl',
              help='Input chats file')
@click.option('--force', is_flag=True, help='Force reprocess all chats')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(method: str, chats_file: str, force: bool, check_only: bool):
    """Run chat summarization with specified method."""
    
    # Determine script path based on method
    if method == "cloud":
        script_path = Path(__file__).parent / "cloud_api" / "cloud_chat_summarizer.py"
    else:
        script_path = Path(__file__).parent / "local" / "local_chat_summarizer.py"
    
    if not script_path.exists():
        logger.error(f"❌ Script not found: {script_path}")
        return 1
    
    # Build command
    command = [
        sys.executable, str(script_path),
        "--chats-file", chats_file
    ]
    
    if force:
        command.append("--force")
    
    if check_only:
        command.append("--check-only")
    
    # Run the script
    logger.info(f"🚀 Running chat summarization ({method})")
    logger.info(f"Command: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Chat summarization failed with exit code: {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    main() 