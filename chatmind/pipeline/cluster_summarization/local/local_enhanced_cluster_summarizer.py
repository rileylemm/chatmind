#!/usr/bin/env python3
"""
ChatMind Local Cluster Summarizer

Creates summaries for semantic clusters using local LLM.
Uses cluster_id from clustering step for proper grouping.
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List, Set, Optional, Union
import logging
from tqdm import tqdm
import hashlib
import pickle
from datetime import datetime
from collections import defaultdict
import subprocess
import sys
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalClusterSummarizer:
    """Creates cluster summaries using local LLM."""
    
    def __init__(self, clustered_embeddings_file: str = "data/processed/clustering/clustered_embeddings.jsonl",
                 chunks_file: str = "data/processed/chunking/chunks.jsonl"):
        self.clustered_embeddings_file = Path(clustered_embeddings_file)
        self.chunks_file = Path(chunks_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/cluster_summarization")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to remove problematic Unicode characters."""
        if not text:
            return text
        
        # Remove or replace problematic Unicode characters
        # Replace common problematic characters
        replacements = {
            '\u2028': '\n',  # Line separator
            '\u2029': '\n',  # Paragraph separator
            '\u200b': '',    # Zero-width space
            '\u200c': '',    # Zero-width non-joiner
            '\u200d': '',    # Zero-width joiner
            '\u2060': '',    # Word joiner
            '\u2061': '',    # Function application
            '\u2062': '',    # Invisible times
            '\u2063': '',    # Invisible separator
            '\u2064': '',    # Invisible plus
            '\u2066': '',    # Left-to-right isolate
            '\u2067': '',    # Right-to-left isolate
            '\u2068': '',    # First strong isolate
            '\u2069': '',    # Pop directional isolate
            '\u206a': '',    # Inhibit symmetric swapping
            '\u206b': '',    # Activate symmetric swapping
            '\u206c': '',    # Inhibit arabic form shaping
            '\u206d': '',    # Activate arabic form shaping
            '\u206e': '',    # National digit shapes
            '\u206f': '',    # Nominal digit shapes
        }
        
        # Apply replacements
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove other control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Normalize Unicode
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _generate_cluster_hash(self, cluster_id: int, chunk_hashes: List[str]) -> str:
        """Generate a hash for a cluster to track if it's been processed."""
        # Create a normalized version for hashing
        normalized_cluster = {
            'cluster_id': cluster_id,
            'chunk_hashes': sorted(chunk_hashes)
        }
        content = json.dumps(normalized_cluster, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_cluster_hashes(self) -> Set[str]:
        """Load hashes of clusters that have already been summarized."""
        hash_file = self.output_dir / "hashes.pkl"
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed cluster hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def _save_processed_cluster_hashes(self, hashes: Set[str]) -> None:
        """Save hashes of processed clusters."""
        hash_file = self.output_dir / "hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed cluster hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'cluster_summarization',
            'stats': stats,
            'version': '1.0'
        }
        metadata_file = self.output_dir / "metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _load_existing_summaries(self, summaries_file: Path) -> Dict:
        """Load existing summaries from output file."""
        summaries = {}
        if summaries_file.exists():
            try:
                with open(summaries_file, 'r') as f:
                    summaries = json.load(f)
                logger.info(f"Loaded {len(summaries)} existing summaries")
            except Exception as e:
                logger.warning(f"Failed to load existing summaries: {e}")
        return summaries
    
    def _load_clustered_embeddings(self) -> List[Dict]:
        """Load clustered embeddings with cluster_id."""
        embeddings = []
        if self.clustered_embeddings_file.exists():
            with jsonlines.open(self.clustered_embeddings_file) as reader:
                for embedding in reader:
                    embeddings.append(embedding)
            logger.info(f"Loaded {len(embeddings)} clustered embeddings")
        else:
            logger.warning(f"Clustered embeddings file not found: {self.clustered_embeddings_file}")
        return embeddings
    
    def _load_chunks(self) -> Dict[str, Dict]:
        """Load chunks indexed by chunk_hash."""
        chunks = {}
        if self.chunks_file.exists():
            with jsonlines.open(self.chunks_file) as reader:
                for chunk in reader:
                    chunk_hash = chunk.get('chunk_hash', '')
                    if chunk_hash:
                        chunks[chunk_hash] = chunk
            logger.info(f"Loaded {len(chunks)} chunks")
        else:
            logger.warning(f"Chunks file not found: {self.chunks_file}")
        return chunks
    
    def _group_chunks_by_cluster(self, clustered_embeddings: List[Dict], chunks: Dict[str, Dict]) -> Dict[int, List[Dict]]:
        """Group chunks by cluster_id using chunk_hash as the link."""
        clusters = defaultdict(list)
        
        for embedding in clustered_embeddings:
            chunk_hash = embedding.get('chunk_hash', '')
            cluster_id = embedding.get('cluster_id', -1)
            
            # Skip noise clusters (cluster_id = -1)
            if cluster_id == -1:
                continue
                
            # Find the corresponding chunk
            if chunk_hash in chunks:
                chunk = chunks[chunk_hash].copy()
                # Add cluster info to chunk
                chunk['cluster_id'] = cluster_id
                chunk['umap_x'] = embedding.get('umap_x', 0.0)
                chunk['umap_y'] = embedding.get('umap_y', 0.0)
                clusters[cluster_id].append(chunk)
            else:
                logger.warning(f"Chunk not found for hash: {chunk_hash}")
        
        logger.info(f"Grouped chunks into {len(clusters)} clusters")
        return dict(clusters)
    
    def _create_summary_prompt(self, cluster_chunks: List[Dict]) -> str:
        """Create a prompt for summarizing a cluster of chunks."""
        # Extract content from chunks and sanitize
        contents = []
        for chunk in cluster_chunks:
            content = chunk.get('content', '').strip()
            if content:
                sanitized_content = self._sanitize_text(content)
                if sanitized_content:
                    contents.append(sanitized_content)
        
        if not contents:
            return ""
        
        # Check if combined content exceeds token limit
        combined_content = "\n\n".join(contents)
        total_chars = len(combined_content)
        max_chars = 24000  # Conservative limit for Gemma-2B
        
        if total_chars > max_chars:
            logger.warning(f"Cluster content ({total_chars} chars) exceeds limit ({max_chars} chars), using hierarchical approach")
            return self._create_hierarchical_cluster_prompt(cluster_chunks)
        
        prompt = f"""Analyze the following content and create a comprehensive summary. The content appears to be from a conversation or discussion.

Content to summarize:
{combined_content}

Please provide a JSON response with the following structure:
{{
    "summary": "A comprehensive summary of the main topics and key points discussed",
    "domain": "The primary domain (e.g., technical, personal, medical, business, academic)",
    "key_topics": ["topic1", "topic2", "topic3"],
    "complexity": "The complexity level (beginner, intermediate, advanced)",
    "sample_questions": ["What is...?", "How does...?", "Why is...?"],
    "confidence": 0.85
}}

Focus on:
1. Main themes and topics discussed
2. Key concepts and ideas
3. The overall domain and context
4. Appropriate complexity level
5. Questions someone might ask about this content

Respond only with valid JSON."""

        return prompt
    
    def _create_hierarchical_cluster_prompt(self, cluster_chunks: List[Dict]) -> str:
        """Create hierarchical summary when cluster content is too large."""
        # Group chunks into manageable batches
        batch_size = 5  # Process 5 chunks at a time
        batches = [cluster_chunks[i:i + batch_size] for i in range(0, len(cluster_chunks), batch_size)]
        
        logger.info(f"Creating hierarchical cluster summary from {len(cluster_chunks)} chunks in {len(batches)} batches")
        
        # Create intermediate summaries for each batch
        intermediate_summaries = []
        for i, batch in enumerate(batches):
            batch_contents = []
            for chunk in batch:
                content = chunk.get('content', '').strip()
                if content:
                    sanitized_content = self._sanitize_text(content)
                    if sanitized_content:
                        batch_contents.append(sanitized_content)
            
            batch_text = "\n\n".join(batch_contents)
            
            intermediate_prompt = f"""Summarize this batch of cluster chunks ({i+1} of {len(batches)}):

{batch_text}

Respond with JSON only:
{{
    "summary": "Summary of this batch of chunks",
    "key_topics": ["topic1", "topic2"],
    "domain": "technical|personal|medical|business|academic",
    "confidence": 0.85
}}"""
            
            intermediate_summary = self._get_summary_from_llm(intermediate_prompt)
            if intermediate_summary:
                intermediate_summary['batch_index'] = i
                intermediate_summary['total_batches'] = len(batches)
                intermediate_summaries.append(intermediate_summary)
        
        # Now combine the intermediate summaries
        if len(intermediate_summaries) == 1:
            # Only one batch, use it directly
            return self._create_final_cluster_summary_from_intermediates(intermediate_summaries[0])
        else:
            # Multiple batches, combine them
            return self._create_final_cluster_summary_from_intermediates(intermediate_summaries)
    
    def _create_final_cluster_summary_from_intermediates(self, intermediate_summaries: Union[Dict, List[Dict]]) -> str:
        """Create final cluster summary from intermediate summaries."""
        if isinstance(intermediate_summaries, dict):
            # Single intermediate summary
            summary_text = intermediate_summaries.get('summary', '')
            prompt = f"""Create a comprehensive cluster summary from this summary:

{summary_text}

Respond with JSON only:
{{
    "summary": "A comprehensive summary of the main topics and key points discussed",
    "domain": "The primary domain (e.g., technical, personal, medical, business, academic)",
    "key_topics": ["topic1", "topic2", "topic3"],
    "complexity": "The complexity level (beginner, intermediate, advanced)",
    "sample_questions": ["What is...?", "How does...?", "Why is...?"],
    "confidence": 0.85
}}"""
        else:
            # Multiple intermediate summaries
            summaries_text = "\n\n".join([
                f"Batch {i+1}: {summary.get('summary', '')}"
                for i, summary in enumerate(intermediate_summaries)
            ])
            
            prompt = f"""Combine these cluster batch summaries into a comprehensive summary:

{summaries_text}

Respond with JSON only:
{{
    "summary": "A comprehensive summary of the main topics and key points discussed",
    "domain": "The primary domain (e.g., technical, personal, medical, business, academic)",
    "key_topics": ["topic1", "topic2", "topic3"],
    "complexity": "The complexity level (beginner, intermediate, advanced)",
    "sample_questions": ["What is...?", "How does...?", "Why is...?"],
    "confidence": 0.85
}}"""
        
        return prompt
    
    def _get_summary_from_llm(self, prompt: str) -> Optional[Dict]:
        """Get summary from local LLM using Ollama."""
        try:
            # Use Ollama with Gemma-2B model
            cmd = [
                "ollama", "run", "gemma:2b",
                prompt
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                
                # Try to extract JSON from response
                try:
                    # Find JSON in the response
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        summary = json.loads(json_str)
                        
                        # Validate required fields
                        required_fields = ['summary', 'domain', 'key_topics', 'complexity', 'sample_questions', 'confidence']
                        if all(field in summary for field in required_fields):
                            return summary
                        else:
                            logger.warning(f"Missing required fields in summary: {summary}")
                    else:
                        logger.warning(f"No JSON found in response: {response}")
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {e}")
                    logger.warning(f"Response: {response}")
            
            else:
                logger.error(f"Ollama command failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("Ollama command timed out")
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
        
        return None
    
    def _summarize_cluster(self, cluster_id: int, cluster_chunks: List[Dict]) -> Optional[Dict]:
        """Summarize a cluster of chunks."""
        logger.info(f"Summarizing cluster {cluster_id} with {len(cluster_chunks)} chunks")
        
        # Create prompt
        prompt = self._create_summary_prompt(cluster_chunks)
        if not prompt:
            logger.warning(f"No content to summarize for cluster {cluster_id}")
            return None
        
        # Get summary from LLM
        summary = self._get_summary_from_llm(prompt)
        
        if summary:
            # Add metadata
            summary['cluster_id'] = cluster_id
            summary['chunk_count'] = len(cluster_chunks)
            summary['chunk_hashes'] = [chunk.get('chunk_hash', '') for chunk in cluster_chunks]
            summary['timestamp'] = datetime.now().isoformat()
            summary['model'] = 'gemma:2b'
            
            # Determine processing method based on whether hierarchical was used
            total_chars = sum(len(chunk.get('content', '')) for chunk in cluster_chunks)
            if total_chars > 24000:
                summary['processing_method'] = 'hierarchical_cluster'
                logger.info(f"Used hierarchical summarization for large cluster {cluster_id}")
            else:
                summary['processing_method'] = 'single_pass'
            
            logger.info(f"Successfully summarized cluster {cluster_id}")
            return summary
        else:
            logger.warning(f"Failed to summarize cluster {cluster_id}")
            return None
    
    def process_clusters_to_summaries(self, force_reprocess: bool = False) -> Dict:
        """Process clusters into summaries."""
        logger.info("🚀 Starting cluster summarization...")
        
        # Load existing summaries
        summaries_file = self.output_dir / "cluster_summaries.json"
        existing_summaries = self._load_existing_summaries(summaries_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_cluster_hashes()
            logger.info(f"Found {len(processed_hashes)} existing processed hashes")
        
        # Load clustered embeddings and chunks
        clustered_embeddings = self._load_clustered_embeddings()
        chunks = self._load_chunks()
        
        if not clustered_embeddings:
            logger.warning("No clustered embeddings found")
            return {'status': 'no_clustered_embeddings'}
        
        if not chunks:
            logger.warning("No chunks found")
            return {'status': 'no_chunks'}
        
        # Group chunks by cluster
        clusters = self._group_chunks_by_cluster(clustered_embeddings, chunks)
        
        if not clusters:
            logger.warning("No valid clusters found")
            return {'status': 'no_clusters'}
        
        # Process each cluster
        new_summaries = {}
        processed_cluster_hashes = set()
        
        for cluster_id, cluster_chunks in clusters.items():
            # Generate cluster hash
            chunk_hashes = [chunk.get('chunk_hash', '') for chunk in cluster_chunks]
            cluster_hash = self._generate_cluster_hash(cluster_id, chunk_hashes)
            
            # Check if already processed
            if cluster_hash not in processed_hashes or force_reprocess:
                summary = self._summarize_cluster(cluster_id, cluster_chunks)
                if summary:
                    new_summaries[str(cluster_id)] = summary
                    processed_cluster_hashes.add(cluster_hash)
            else:
                logger.info(f"Cluster {cluster_id} already processed, skipping")
        
        if not new_summaries and not force_reprocess:
            logger.info("No new clusters to process")
            return {'status': 'no_new_clusters'}
        
        # Combine existing and new summaries
        all_summaries = {**existing_summaries, **new_summaries}
        
        # Save summaries
        with open(summaries_file, 'w') as f:
            json.dump(all_summaries, f, indent=2)
        
        # Save hashes and metadata
        all_processed_hashes = processed_hashes.union(processed_cluster_hashes)
        self._save_processed_cluster_hashes(all_processed_hashes)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_clusters': len(all_summaries),
            'new_summaries': len(new_summaries),
            'existing_summaries': len(existing_summaries),
            'processed_clusters': len(processed_cluster_hashes)
        }
        
        self._save_metadata(stats)
        
        logger.info(f"✅ Summarization complete: {len(new_summaries)} new summaries created")
        return stats


@click.command()
@click.option('--clustered-embeddings-file', 
              default='data/processed/clustering/clustered_embeddings.jsonl',
              help='Input clustered embeddings file')
@click.option('--chunks-file', 
              default='data/processed/chunking/chunks.jsonl',
              help='Input chunks file')
@click.option('--force', is_flag=True, help='Force reprocess all clusters')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(clustered_embeddings_file: str, chunks_file: str, force: bool, check_only: bool):
    """Run local cluster summarization."""
    if check_only:
        logger.info("🔍 Checking setup...")
        
        # Check input files
        clustered_embeddings_path = Path(clustered_embeddings_file)
        chunks_path = Path(chunks_file)
        
        if not clustered_embeddings_path.exists():
            logger.error(f"❌ Clustered embeddings file not found: {clustered_embeddings_path}")
            return 1
        
        if not chunks_path.exists():
            logger.error(f"❌ Chunks file not found: {chunks_path}")
            return 1
        
        # Check Ollama
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Ollama is available")
            else:
                logger.error("❌ Ollama not available")
                return 1
        except FileNotFoundError:
            logger.error("❌ Ollama not found in PATH")
            return 1
        
        logger.info("✅ Setup check passed")
        return 0
    
    # Run summarization
    summarizer = LocalClusterSummarizer(clustered_embeddings_file, chunks_file)
    result = summarizer.process_clusters_to_summaries(force_reprocess=force)
    
    if result.get('status') == 'success':
        logger.info("✅ Summarization completed successfully")
        return 0
    else:
        logger.error(f"❌ Summarization failed: {result.get('status')}")
        return 1


if __name__ == "__main__":
    main() 