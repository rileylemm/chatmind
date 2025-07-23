#!/usr/bin/env python3
"""
ChatMind Pipeline Runner

Runs the complete pipeline from ChatGPT exports to visualization.
"""

import subprocess
import sys
from pathlib import Path
import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--skip-ingestion', is_flag=True, help='Skip data ingestion step')
@click.option('--skip-embedding', is_flag=True, help='Skip embedding and clustering step')
@click.option('--skip-loading', is_flag=True, help='Skip Neo4j loading step')
@click.option('--clear-neo4j', is_flag=True, help='Clear existing Neo4j data before loading')
@click.option('--force-reprocess', is_flag=True, help='Force reprocess all files (ignore previous state)')
@click.option('--clear-state', is_flag=True, help='Clear all processed state and start fresh')
def main(skip_ingestion: bool, skip_embedding: bool, skip_loading: bool, clear_neo4j: bool, force_reprocess: bool, clear_state: bool):
    """Run the complete ChatMind pipeline."""
    
    logger.info("🚀 Starting ChatMind pipeline...")
    
    # Step 1: Data Ingestion
    if not skip_ingestion:
        logger.info("📥 Step 1: Extracting and flattening ChatGPT exports...")
        try:
            cmd = [sys.executable, "chatmind/data_ingestion/extract_and_flatten.py"]
            if force_reprocess:
                cmd.append("--force")
            if clear_state:
                cmd.append("--clear-state")
            subprocess.run(cmd, check=True)
            logger.info("✅ Data ingestion completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Data ingestion failed: {e}")
            return 1
    else:
        logger.info("⏭️ Skipping data ingestion")
    
    # Step 2: Embedding and Clustering
    if not skip_embedding:
        logger.info("🧠 Step 2: Generating embeddings and clustering...")
        try:
            subprocess.run([
                sys.executable, "chatmind/embedding/embed_and_cluster.py"
            ], check=True)
            logger.info("✅ Embedding and clustering completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Embedding and clustering failed: {e}")
            return 1
    else:
        logger.info("⏭️ Skipping embedding and clustering")
    
    # Step 3: Neo4j Loading
    if not skip_loading:
        logger.info("🗄️ Step 3: Loading data into Neo4j...")
        try:
            cmd = [sys.executable, "chatmind/neo4j_loader/load_graph.py"]
            if clear_neo4j:
                cmd.append("--clear")
            subprocess.run(cmd, check=True)
            logger.info("✅ Neo4j loading completed")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Neo4j loading failed: {e}")
            return 1
    else:
        logger.info("⏭️ Skipping Neo4j loading")
    
    logger.info("🎉 Pipeline completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Start the API server: python chatmind/api/main.py")
    logger.info("2. Start the frontend: cd chatmind/frontend && npm start")
    logger.info("3. Open http://localhost:3000 in your browser")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 