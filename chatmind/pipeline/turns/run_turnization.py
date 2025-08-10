#!/usr/bin/env python3
import click
from pathlib import Path
import subprocess
import sys

@click.command()
@click.option('--processed-dir', default='data/processed', help='Processed data directory')
@click.option('--prev-window', default=3, type=int, help='Sliding window size for prev_turn_ids')
@click.option('--chunk-version', default='v2', help='Chunk/version label for turns')
@click.option('--embed-model', default='all-MiniLM-L6-v2', help='Embedding model name (metadata only)')
@click.option('--embed-version', default='1', help='Embedding version tag (metadata only)')
@click.option('--force', is_flag=True, help='Force reprocess all turns')
def main(processed_dir: str, prev_window: int, chunk_version: str, embed_model: str, embed_version: str, force: bool):
    script = Path(__file__).parent / 'turnizer.py'
    cmd = [sys.executable, str(script), '--processed-dir', processed_dir, '--prev-window', str(prev_window), '--chunk-version', chunk_version, '--embed-model', embed_model, '--embed-version', embed_version]
    if force:
        cmd.append('--force')
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main() 