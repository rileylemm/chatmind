#!/usr/bin/env python3
"""
Local Enhanced Cluster Summarizer

Generates summaries for clusters using local LLMs (Gemma/TinyLlama).
Uses modular directory structure: data/processed/summarization/
"""

import json
import jsonlines
import click
from pathlib import Path
from typing import Dict, List, Set, Optional
import logging
from tqdm import tqdm
import hashlib
import pickle
from datetime import datetime
import subprocess
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalEnhancedClusterSummarizer:
    """Generates summaries for clusters using local LLMs."""
    
    def __init__(self, 
                 model: str = "gemma:2b",
                 processed_dir: str = "data/processed"):
        self.model = model
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.summarization_dir = self.processed_dir / "summarization"
        self.summarization_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_cluster_hash(self, cluster_id: int, chunks: List[Dict]) -> str:
        """Generate a hash for a cluster to track if it's been processed."""
        # Create a normalized version for hashing
        cluster_content = {
            'cluster_id': cluster_id,
            'chunk_ids': [chunk.get('chunk_id', '') for chunk in chunks],
            'contents': [chunk.get('content', '') for chunk in chunks],
            'tags': list(set([tag for chunk in chunks for tag in chunk.get('tags', [])]))
        }
        content = json.dumps(cluster_content, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_cluster_hashes(self) -> Set[str]:
        """Load hashes of clusters that have already been summarized."""
        hash_file = self.summarization_dir / "hashes.pkl"
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
        hash_file = self.summarization_dir / "hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed cluster hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _load_existing_summaries(self, summaries_file: Path) -> Dict:
        """Load existing summaries from file."""
        summaries = {}
        if summaries_file.exists():
            with open(summaries_file, 'r') as f:
                summaries = json.load(f)
            logger.info(f"Loaded {len(summaries)} existing summaries")
        return summaries
    
    def _load_tagged_chunks(self, tagged_chunks_file: Path) -> List[Dict]:
        """Load tagged chunks from JSONL file."""
        chunks = []
        with jsonlines.open(tagged_chunks_file) as reader:
            for chunk in reader:
                chunks.append(chunk)
        
        logger.info(f"Loaded {len(chunks)} tagged chunks from {tagged_chunks_file}")
        return chunks
    
    def _group_by_cluster(self, chunks: List[Dict]) -> Dict[int, List[Dict]]:
        """Group chunks by cluster ID."""
        clusters = {}
        for chunk in chunks:
            cluster_id = chunk.get('cluster_id', -1)
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(chunk)
        
        logger.info(f"Grouped chunks into {len(clusters)} clusters")
        return clusters
    
    def _generate_summary_prompt(self, cluster_id: int, chunks: List[Dict]) -> str:
        """Generate a prompt for summarizing a cluster."""
        # Extract content and tags from chunks
        contents = [chunk.get('content', '').strip() for chunk in chunks]
        contents = [c for c in contents if c]  # Remove empty content
        
        # Collect all tags from chunks
        all_tags = []
        all_topics = []
        all_domains = []
        
        for chunk in chunks:
            all_tags.extend(chunk.get('tags', []))
            all_topics.extend(chunk.get('topics', []))
            all_domains.append(chunk.get('domain', 'other'))
        
        # Remove duplicates
        unique_tags = list(set(all_tags))
        unique_topics = list(set(all_topics))
        unique_domains = list(set(all_domains))
        
        if not contents:
            return ""
        
        # Create the prompt
        prompt = f"""You are an AI assistant that creates concise, informative summaries of conversation clusters.

Cluster ID: {cluster_id}
Number of chunks: {len(chunks)}

Conversation chunks:
{chr(10).join([f"{i+1}. {content[:500]}{'...' if len(content) > 500 else ''}" for i, content in enumerate(contents)])}

Tags from chunks: {', '.join(unique_tags[:10])}
Topics from chunks: {', '.join(unique_topics[:5])}
Domains: {', '.join(unique_domains)}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise summary of the main topics and themes discussed in this cluster",
    "domain": "The primary domain or category (e.g., 'technology', 'health', 'business', 'personal', 'education', 'entertainment')",
    "topics": ["topic1", "topic2", "topic3"],
    "complexity": "low|medium|high",
    "key_points": ["point1", "point2", "point3"],
    "common_tags": ["tag1", "tag2", "tag3"]
}}

Focus on the most important themes and avoid repetition. Keep the summary under 200 words."""

        return prompt
    
    def _call_ollama(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call Ollama API to generate summary."""
        for attempt in range(max_retries):
            try:
                # Prepare the request
                request_data = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 500
                    }
                }
                
                # Call Ollama
                result = subprocess.run(
                    ["ollama", "generate", "--json"],
                    input=json.dumps(request_data),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    response = json.loads(result.stdout)
                    return response.get('response', '').strip()
                else:
                    logger.warning(f"Ollama call failed (attempt {attempt + 1}): {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Ollama call timed out (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"Ollama call error (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from LLM response."""
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in response")
                return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
            return None
    
    def _generate_cluster_summary(self, cluster_id: int, chunks: List[Dict]) -> Optional[Dict]:
        """Generate a summary for a cluster."""
        prompt = self._generate_summary_prompt(cluster_id, chunks)
        
        if not prompt:
            logger.warning(f"Empty prompt for cluster {cluster_id}")
            return None
        
        response = self._call_ollama(prompt)
        
        if not response:
            logger.warning(f"No response for cluster {cluster_id}")
            return None
        
        summary_data = self._extract_json_from_response(response)
        
        if summary_data:
            # Add metadata
            summary_data['cluster_id'] = cluster_id
            summary_data['chunk_count'] = len(chunks)
            summary_data['generated_at'] = datetime.now().isoformat()
            return summary_data
        else:
            logger.warning(f"Failed to extract summary for cluster {cluster_id}")
            return None
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'summarization',
            'stats': stats,
            'version': '1.0'
        }
        metadata_file = self.summarization_dir / "metadata.json"
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def generate_gemma_summaries(self, tagged_chunks_file: Path, force_reprocess: bool = False) -> Dict:
        """Generate summaries for all clusters."""
        logger.info("🚀 Starting cluster summarization...")
        
        # Load existing summaries
        summaries_file = self.summarization_dir / "cluster_summaries.json"
        existing_summaries = self._load_existing_summaries(summaries_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_cluster_hashes()
            logger.info(f"Found {len(processed_hashes)} existing processed hashes")
        
        # Load tagged chunks
        chunks = self._load_tagged_chunks(tagged_chunks_file)
        if not chunks:
            logger.warning("No tagged chunks found")
            return {'status': 'no_chunks'}
        
        # Group by cluster
        clusters = self._group_by_cluster(chunks)
        
        # Generate summaries for new clusters
        new_summaries = {}
        total_clusters = len(clusters)
        
        for cluster_id, chunks in tqdm(clusters.items(), desc="Generating summaries"):
            if cluster_id == -1:  # Skip noise points
                continue
                
            cluster_hash = self._generate_cluster_hash(cluster_id, chunks)
            
            if cluster_hash not in processed_hashes or force_reprocess:
                summary = self._generate_cluster_summary(cluster_id, chunks)
                if summary:
                    new_summaries[cluster_id] = summary
                    processed_hashes.add(cluster_hash)
        
        if not new_summaries and not force_reprocess:
            logger.info("No new clusters to summarize")
            return {'status': 'no_new_clusters'}
        
        # Combine existing and new summaries
        all_summaries = {**existing_summaries, **new_summaries}
        
        # Save summaries
        with open(summaries_file, 'w') as f:
            json.dump(all_summaries, f, indent=2)
        
        # Save hashes and metadata
        self._save_processed_cluster_hashes(processed_hashes)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_clusters': len(all_summaries),
            'new_summaries': len(new_summaries),
            'existing_summaries': len(existing_summaries),
            'model_used': self.model
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Cluster summarization completed!")
        logger.info(f"  Total clusters: {stats['total_clusters']}")
        logger.info(f"  New summaries: {stats['new_summaries']}")
        logger.info(f"  Model used: {stats['model_used']}")
        
        return stats


@click.command()
@click.option('--input-file',
              default='data/processed/tagging/tagged_chunks.jsonl',
              help='Input JSONL file with tagged chunks')
@click.option('--output-file',
              default='data/processed/summarization/cluster_summaries.json',
              help='Output JSON file for cluster summaries')
@click.option('--model', default='gemma:2b', help='Ollama model to use')
@click.option('--force', is_flag=True, help='Force reprocess all clusters (ignore state)')
def main(input_file: str, output_file: str, model: str, force: bool):
    """Generate summaries for clusters using local LLMs."""
    
    summarizer = LocalEnhancedClusterSummarizer(model=model)
    
    result = summarizer.generate_gemma_summaries(
        tagged_chunks_file=Path(input_file),
        force_reprocess=force
    )
    
    if result['status'] == 'success':
        logger.info(f"✅ Summarization completed successfully!")
        logger.info(f"   Total clusters: {result['total_clusters']}")
        logger.info(f"   New summaries: {result['new_summaries']}")
    else:
        logger.info(f"ℹ️ Summarization status: {result['status']}")


if __name__ == "__main__":
    main() 