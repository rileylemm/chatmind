#!/usr/bin/env python3
"""
ChatMind Pipeline Runner

Orchestrates the complete modular pipeline from ingestion to Neo4j loading.
Uses the new modular directory structure with hash-based linking.
"""

import json
import click
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging
import subprocess
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates the complete ChatMind pipeline."""
    
    def __init__(self, processed_dir: str = "data/processed"):
        self.processed_dir = Path(processed_dir)
        self.pipeline_dir = Path("chatmind/pipeline")
        
        # Use the pipeline virtual environment Python executable
        self.python_executable = self.pipeline_dir / "pipeline_env" / "bin" / "python"
        if not self.python_executable.exists():
            # Fallback to system Python if venv doesn't exist
            import sys
            self.python_executable = sys.executable
        
    def _check_step_output(self, step_name: str, required_files: List[str]) -> bool:
        """Check if a pipeline step has completed by looking for output files."""
        step_dir = self.processed_dir / step_name
        
        for file_name in required_files:
            file_path = step_dir / file_name
            if not file_path.exists():
                return False
        
        return True
    
    def _run_step(self, step_name: str, command: List[str], description: str) -> bool:
        """Run a pipeline step and return success status."""
        logger.info(f"🚀 {description}")
        logger.info(f"Running: {' '.join(command)}")
        
        try:
            # Run without capturing output so progress bars are visible
            result = subprocess.run(command, check=True)
            logger.info(f"✅ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ {description} failed: {e}")
            return False
    
    def run_ingestion(self, force: bool = False) -> bool:
        """Run the ingestion step."""
        if not force and self._check_step_output("ingestion", ["chats.jsonl", "metadata.json"]):
            logger.info("ℹ️ Ingestion already completed, skipping...")
            return True
        
        command = [
            str(self.python_executable), str(self.pipeline_dir / "ingestion" / "extract_and_flatten.py"),
            "--processed-dir", str(self.processed_dir),
            "--data-lake-dir", str(Path.cwd() / "data" / "lake")
        ]
        
        if force:
            command.append("--force")
        
        return self._run_step("ingestion", command, "Running ingestion step")
    
    def run_chunking(self, force: bool = False) -> bool:
        """Run the chunking step."""
        if not force and self._check_step_output("chunking", ["chunks.jsonl", "metadata.json"]):
            logger.info("ℹ️ Chunking already completed, skipping...")
            return True
        
        command = [
            str(self.python_executable), str(self.pipeline_dir / "chunking" / "chunker.py"),
            "--input-file", str(self.processed_dir / "ingestion" / "chats.jsonl")
        ]
        
        if force:
            command.append("--force")
        
        return self._run_step("chunking", command, "Running chunking step")
    
    def run_embedding(self, method: str = "local", force: bool = False) -> bool:
        """Run the embedding step."""
        if not force and self._check_step_output("embedding", ["embeddings.jsonl", "metadata.json"]):
            logger.info("ℹ️ Embedding already completed, skipping...")
            return True
        
        # Check if cloud_api version exists for the method
        cloud_script = self.pipeline_dir / "embedding" / "cloud_api" / "enhanced_embedder.py"
        local_script = self.pipeline_dir / "embedding" / "local" / "embed_chunks.py"
        
        if method == "cloud" and cloud_script.exists():
            command = [
                str(self.python_executable), str(cloud_script),
                "--chunks-file", str(self.processed_dir / "chunking" / "chunks.jsonl"),
                "--state-file", str(self.processed_dir / "embedding" / "hashes.pkl")
            ]
        else:
            # Default to local method
            command = [
                str(self.python_executable), str(local_script),
                "--chunks-file", str(self.processed_dir / "chunking" / "chunks.jsonl"),
                "--state-file", str(self.processed_dir / "embedding" / "hashes.pkl")
            ]
        
        if force:
            command.append("--force")
        
        return self._run_step("embedding", command, f"Running embedding step ({method})")
    
    def run_clustering(self, force: bool = False) -> bool:
        """Run the clustering step."""
        if not force and self._check_step_output("clustering", ["clustered_embeddings.jsonl", "metadata.json"]):
            logger.info("ℹ️ Clustering already completed, skipping...")
            return True
        
        command = [
            str(self.python_executable), str(self.pipeline_dir / "clustering" / "clusterer.py"),
            "--input-file", str(self.processed_dir / "embedding" / "embeddings.jsonl")
        ]
        
        if force:
            command.append("--force")
        
        return self._run_step("clustering", command, "Running clustering step")
    
    def run_tagging(self, method: str = "local", force: bool = False) -> bool:
        """Run the tagging step."""
        if not force and self._check_step_output("tagging", ["tags.jsonl", "metadata.json"]):
            logger.info("ℹ️ Tagging already completed, skipping...")
            return True
        
        # Check if cloud_api version exists for the method
        cloud_script = self.pipeline_dir / "tagging" / "cloud_api" / "enhanced_tagger.py"
        local_script = self.pipeline_dir / "tagging" / "local" / "run_local_enhanced_tagging.py"
        
        if method == "cloud" and cloud_script.exists():
            command = [
                str(self.python_executable), str(cloud_script),
                "--input-file", str(self.processed_dir / "ingestion" / "chats.jsonl"),
                "--output-file", str(self.processed_dir / "tagging" / "tags.jsonl")
            ]
        else:
            # Default to local method
            command = [
                str(self.python_executable), str(local_script),
                "--input-file", str(self.processed_dir / "ingestion" / "chats.jsonl"),
                "--output-file", str(self.processed_dir / "tagging" / "tags.jsonl")
            ]
        
        if force:
            command.append("--force")
        
        return self._run_step("tagging", command, f"Running tagging step ({method})")
    
    def run_tag_post_processing(self, force: bool = False) -> bool:
        """Run the tag post-processing step."""
        if not force and self._check_step_output("tagging", ["processed_tags.jsonl"]):
            logger.info("ℹ️ Tag post-processing already completed, skipping...")
            return True
        
        command = [
            str(self.python_executable), str(self.pipeline_dir / "tagging" / "post_process_tags.py"),
            "--input-file", str(self.processed_dir / "tagging" / "tags.jsonl"),
            "--output-file", str(self.processed_dir / "tagging" / "processed_tags.jsonl")
        ]
        
        return self._run_step("tag_post_processing", command, "Running tag post-processing step")
    

    
    def run_cluster_summarization(self, method: str = "local", force: bool = False) -> bool:
        """Run the cluster summarization step."""
        if not force and self._check_step_output("cluster_summarization", ["cluster_summaries.json", "metadata.json"]):
            logger.info("ℹ️ Cluster summarization already completed, skipping...")
            return True
        
        # Check if cloud_api version exists for the method
        cloud_script = self.pipeline_dir / "cluster_summarization" / "cloud_api" / "enhanced_cluster_summarizer.py"
        local_script = self.pipeline_dir / "cluster_summarization" / "local" / "local_enhanced_cluster_summarizer.py"
        
        if method == "cloud" and cloud_script.exists():
            command = [
                str(self.python_executable), str(cloud_script),
                "--clustered-embeddings-file", str(self.processed_dir / "clustering" / "clustered_embeddings.jsonl"),
                "--chunks-file", str(self.processed_dir / "chunking" / "chunks.jsonl")
            ]
        else:
            # Default to local method
            command = [
                str(self.python_executable), str(local_script),
                "--clustered-embeddings-file", str(self.processed_dir / "clustering" / "clustered_embeddings.jsonl"),
                "--chunks-file", str(self.processed_dir / "chunking" / "chunks.jsonl")
            ]
        
        if force:
            command.append("--force")
        
        return self._run_step("cluster_summarization", command, f"Running cluster summarization step ({method})")
    
    def run_chat_summarization(self, method: str = "local", force: bool = False) -> bool:
        """Run the chat summarization step."""
        if not force and self._check_step_output("chat_summarization", ["chat_summaries.json", "metadata.json"]):
            logger.info("ℹ️ Chat summarization already completed, skipping...")
            return True
        
        # Check if cloud_api version exists for the method
        cloud_script = self.pipeline_dir / "chat_summarization" / "cloud_api" / "cloud_chat_summarizer.py"
        local_script = self.pipeline_dir / "chat_summarization" / "local" / "local_chat_summarizer.py"
        
        if method == "cloud" and cloud_script.exists():
            command = [
                str(self.python_executable), str(cloud_script),
                "--chats-file", str(self.processed_dir / "ingestion" / "chats.jsonl")
            ]
        else:
            # Default to local method
            command = [
                str(self.python_executable), str(local_script),
                "--chats-file", str(self.processed_dir / "ingestion" / "chats.jsonl")
            ]
        
        if force:
            command.append("--force")
        
        return self._run_step("chat_summarization", command, f"Running chat summarization step ({method})")
    
    def run_positioning(self, force: bool = False) -> bool:
        """Run the positioning step (both cluster and chat positioning)."""
        if not force and self._check_step_output("positioning", [
            "cluster_positions.jsonl", "chat_positions.jsonl", 
            "cluster_positioning_metadata.json", "chat_positioning_metadata.json",
            "cluster_summary_embeddings.jsonl", "chat_summary_embeddings.jsonl"
        ]):
            logger.info("ℹ️ Positioning already completed, skipping...")
            return True
        
        # Run cluster positioning
        cluster_command = [
            str(self.python_executable), str(self.pipeline_dir / "positioning" / "position_clusters.py"),
            "--cluster-summaries-file", str(self.processed_dir / "cluster_summarization" / "cluster_summaries.json")
        ]
        
        if force:
            cluster_command.append("--force")
        
        cluster_success = self._run_step("cluster_positioning", cluster_command, "Running cluster positioning step")
        
        # Run chat positioning
        chat_command = [
            str(self.python_executable), str(self.pipeline_dir / "positioning" / "position_chats.py"),
            "--chat-summaries-file", str(self.processed_dir / "chat_summarization" / "chat_summaries.json")
        ]
        
        if force:
            chat_command.append("--force")
        
        chat_success = self._run_step("chat_positioning", chat_command, "Running chat positioning step")
        
        return cluster_success and chat_success
    
    def run_similarity(self, force: bool = False) -> bool:
        """Run the similarity steps (chat and cluster)."""
        # Check if both similarity steps are already completed
        chat_similarity_complete = self._check_step_output("similarity", ["chat_similarities.jsonl", "chat_similarity_hashes.pkl"])
        cluster_similarity_complete = self._check_step_output("similarity", ["cluster_similarities.jsonl", "cluster_similarity_hashes.pkl"])
        
        if not force and chat_similarity_complete and cluster_similarity_complete:
            logger.info("ℹ️ Similarity calculations already completed, skipping...")
            return True
        
        # Run chat similarity
        chat_command = [
            str(self.python_executable), str(self.pipeline_dir / "similarity" / "calculate_chat_similarities.py"),
            "--embeddings-file", str(self.processed_dir / "positioning" / "chat_summary_embeddings.jsonl")
        ]
        
        if force:
            chat_command.append("--force")
        
        chat_success = self._run_step("similarity", chat_command, "Running chat similarity calculation")
        if not chat_success:
            return False
        
        # Run cluster similarity
        cluster_command = [
            str(self.python_executable), str(self.pipeline_dir / "similarity" / "calculate_cluster_similarities.py"),
            "--embeddings-file", str(self.processed_dir / "positioning" / "cluster_summary_embeddings.jsonl")
        ]
        
        if force:
            cluster_command.append("--force")
        
        cluster_success = self._run_step("similarity", cluster_command, "Running cluster similarity calculation")
        return cluster_success
    
    def run_loading(self, force: bool = False) -> bool:
        """Run the hybrid loading step (Neo4j + Qdrant)."""
        # Get database config from environment using config module
        from config import get_neo4j_config
        
        # Load configuration
        neo4j_config = get_neo4j_config()
        neo4j_uri = neo4j_config['uri']
        neo4j_user = neo4j_config['user']
        neo4j_password = neo4j_config['password']
        
        # Qdrant config (these might not be in config yet, so use defaults)
        import os
        qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6335')
        qdrant_collection = os.getenv('QDRANT_COLLECTION', 'chatmind_embeddings')
        
        command = [
            str(self.python_executable), str(self.pipeline_dir / "loading" / "load_hybrid.py"),
            "--neo4j-uri", neo4j_uri,
            "--neo4j-user", neo4j_user,
            "--neo4j-password", neo4j_password,
            "--qdrant-url", qdrant_url,
            "--qdrant-collection", qdrant_collection
        ]
        
        if force:
            command.append("--force")
        
        return self._run_step("loading", command, "Running hybrid loading step (Neo4j + Qdrant)")
    
    def run_pipeline(self, 
                    embedding_method: str = "local",
                    tagging_method: str = "local",
                    summarization_method: str = "local",
                    force: bool = False,
                    steps: List[str] = None) -> Dict:
        """Run the complete pipeline or specified steps."""
        logger.info("🚀 Starting ChatMind Pipeline")
        logger.info("=" * 50)
        
        # Define pipeline steps in order
        pipeline_steps = [
            ("ingestion", self.run_ingestion),
            ("chunking", self.run_chunking),
            ("embedding", lambda f: self.run_embedding(embedding_method, f)),
            ("clustering", self.run_clustering),
            ("tagging", lambda f: self.run_tagging(tagging_method, f)),
            ("tag_post_processing", self.run_tag_post_processing),
            ("cluster_summarization", lambda f: self.run_cluster_summarization(summarization_method, f)),
            ("chat_summarization", lambda f: self.run_chat_summarization(summarization_method, f)),
            ("positioning", self.run_positioning),
            ("similarity", self.run_similarity),
            ("loading", self.run_loading)
        ]
        
        # Filter steps if specified
        if steps:
            pipeline_steps = [(name, func) for name, func in pipeline_steps if name in steps]
        
        # Run steps
        results = {}
        for step_name, step_func in pipeline_steps:
            logger.info(f"\n📋 Step: {step_name.upper()}")
            success = step_func(force)
            results[step_name] = success
            
            if not success:
                logger.error(f"❌ Pipeline failed at step: {step_name}")
                return {
                    'status': 'failed',
                    'failed_step': step_name,
                    'results': results
                }
        
        # Calculate statistics
        successful_steps = sum(1 for success in results.values() if success)
        total_steps = len(results)
        
        stats = {
            'status': 'success',
            'total_steps': total_steps,
            'successful_steps': successful_steps,
            'results': results,
            'completed_at': datetime.now().isoformat()
        }
        
        logger.info("\n" + "=" * 50)
        logger.info("✅ Pipeline completed successfully!")
        logger.info(f"  Steps completed: {successful_steps}/{total_steps}")
        logger.info(f"  Completed at: {stats['completed_at']}")
        
        return stats


@click.command()
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
                               'tagging', 'tag_post_processing', 'cluster_summarization', 'chat_summarization',
                               'positioning', 'similarity', 'loading']),
              help='Specific steps to run (can specify multiple)')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t run pipeline')
def main(embedding_method: str, tagging_method: str, summarization_method: str, 
         force: bool, steps: List[str], check_only: bool):
    """
    Run the complete ChatMind pipeline.
    
    The pipeline processes data through these steps:
    1. Ingestion: Extract chats from raw exports
    2. Chunking: Create semantic chunks from messages
    3. Embedding: Convert chunks to vectors
    4. Clustering: Group similar embeddings
    5. Tagging: Tag messages with topics
    6. Tag Post-Processing: Normalize and clean tags
    7. Cluster Summarization: Create cluster summaries
    8. Chat Summarization: Create chat summaries
    9. Positioning: Add spatial coordinates
    10. Similarity: Calculate chat similarities
    11. Loading: Load into Neo4j database (creates tag-chunk relationships)
    
    EXAMPLES:
    # Run complete pipeline with local models
    python3 chatmind/pipeline/run_pipeline.py
    
    # Run with cloud embedding
    python3 chatmind/pipeline/run_pipeline.py --embedding-method cloud
    
    # Run only specific steps
    python3 chatmind/pipeline/run_pipeline.py --steps ingestion chunking embedding
    
    # Force reprocess everything
    python3 chatmind/pipeline/run_pipeline.py --force
    """
    
    if check_only:
        logger.info("🔍 Checking pipeline setup...")
        # Check if all required directories exist
        required_dirs = [
            "chatmind/pipeline/ingestion",
            "chatmind/pipeline/chunking", 
            "chatmind/pipeline/embedding",
            "chatmind/pipeline/clustering",
            "chatmind/pipeline/tagging",
            "chatmind/pipeline/cluster_summarization",
            "chatmind/pipeline/chat_summarization",
            "chatmind/pipeline/positioning",
            "chatmind/pipeline/similarity",
            "chatmind/pipeline/loading"
        ]
        
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                logger.info(f"✅ {dir_path}")
            else:
                logger.error(f"❌ {dir_path}")
        
        return
    
    runner = PipelineRunner()
    result = runner.run_pipeline(
        embedding_method=embedding_method,
        tagging_method=tagging_method,
        summarization_method=summarization_method,
        force=force,
        steps=list(steps) if steps else None
    )
    
    if result['status'] == 'success':
        logger.info("✅ Pipeline completed successfully!")
    else:
        logger.error(f"❌ Pipeline failed at step: {result.get('failed_step', 'unknown')}")


if __name__ == "__main__":
    main() 