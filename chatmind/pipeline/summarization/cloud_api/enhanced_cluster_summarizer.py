#!/usr/bin/env python3
"""
Enhanced Cluster Summarizer for ChatMind

Uses OpenAI API to generate intelligent cluster summaries from chunks.
Provides better topic identification and description than simple word extraction.
"""

import json
import jsonlines
from pathlib import Path
from collections import defaultdict, Counter
import logging
from typing import Dict, List, Set, Optional
import time
import openai
import click
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedClusterSummarizer:
    """Enhanced cluster summarizer using OpenAI API."""
    
    def __init__(self, model: str = "gpt-3.5-turbo", max_retries: int = 3, 
                 delay_between_calls: float = 1.0):
        self.model = model
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        self.stats = {
            'clusters_processed': 0,
            'api_calls': 0,
            'errors': 0,
            'total_tokens': 0
        }
    
    def get_cluster_summary_prompt(self, cluster_chunks: List[Dict]) -> str:
        """Generate prompt for cluster summarization."""
        # Collect sample content from chunks
        sample_contents = []
        sample_titles = []
        
        for chunk in cluster_chunks[:10]:  # Limit to first 10 chunks
            content = chunk.get('content', '').strip()
            if content and len(content) > 50:  # Only include substantial content
                sample_contents.append(content[:200])  # Truncate for prompt
            
            title = chunk.get('chat_title', '').strip()
            if title and title not in sample_titles:
                sample_titles.append(title)
        
        # Create prompt
        prompt = f"""Analyze this cluster of related ChatGPT conversations and provide a comprehensive summary.

Cluster Information:
- Number of chunks: {len(cluster_chunks)}
- Sample titles: {sample_titles[:5]}
- Sample content excerpts:
{chr(10).join([f"- {content}" for content in sample_contents[:5]])}

Please provide a JSON response with the following structure:
{{
    "topic": "Main topic or theme of this cluster",
    "description": "Detailed description of what this cluster contains",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "domain": "technical|personal|medical|academic|creative|other",
    "complexity": "beginner|intermediate|advanced",
    "sample_questions": ["question1", "question2"],
    "tags": ["#tag1", "#tag2", "#tag3"]
}}

Focus on:
1. Identifying the main topic or theme
2. Describing the type of content and discussions
3. Extracting key concepts and terminology
4. Determining the domain and complexity level
5. Suggesting relevant tags
6. Providing sample questions that might be asked in this context

Be concise but comprehensive. The summary should help users understand what kind of content is in this cluster."""
        
        return prompt
    
    def summarize_cluster_with_api(self, cluster_chunks: List[Dict]) -> Optional[Dict]:
        """Summarize a cluster using OpenAI API."""
        prompt = self.get_cluster_summary_prompt(cluster_chunks)
        
        for attempt in range(self.max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert content analyst and summarizer. Provide clear, accurate summaries in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                self.stats['api_calls'] += 1
                self.stats['total_tokens'] += response.usage.total_tokens
                
                # Extract JSON from response
                content = response.choices[0].message.content.strip()
                
                # Try to extract JSON
                try:
                    # Find JSON in the response
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    if start != -1 and end != 0:
                        json_str = content[start:end]
                        summary = json.loads(json_str)
                        
                        # Add metadata
                        summary['cluster_size'] = len(cluster_chunks)
                        summary['sample_titles'] = list(set([
                            chunk.get('chat_title', '') for chunk in cluster_chunks[:5]
                            if chunk.get('chat_title', '')
                        ]))
                        summary['total_messages'] = len(cluster_chunks)
                        summary['summary_model'] = self.model
                        summary['summary_timestamp'] = int(time.time())
                        
                        return summary
                    else:
                        logger.warning(f"Could not find JSON in response: {content}")
                        return None
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from response: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay_between_calls)
                        continue
                    return None
                    
            except Exception as e:
                logger.error(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                return None
        
        return None
    
    def generate_enhanced_summaries(self, chunks_file: Path, output_file: Path) -> Dict:
        """Generate enhanced cluster summaries from chunks data."""
        logger.info(f"Generating enhanced cluster summaries from {chunks_file}")
        
        # Group chunks by cluster
        clusters = defaultdict(list)
        cluster_sizes = Counter()
        
        with jsonlines.open(chunks_file) as reader:
            for chunk in reader:
                cluster_id = chunk.get('cluster_id')
                if cluster_id is not None and cluster_id != -1:
                    clusters[cluster_id].append(chunk)
                    cluster_sizes[cluster_id] += 1
        
        logger.info(f"Found {len(clusters)} clusters")
        
        # Generate enhanced summaries for each cluster
        summaries = {}
        
        for cluster_id, chunks in tqdm(clusters.items(), desc="Summarizing clusters"):
            try:
                summary = self.summarize_cluster_with_api(chunks)
                
                if summary:
                    summaries[str(cluster_id)] = summary
                    self.stats['clusters_processed'] += 1
                else:
                    # Fallback to basic summary
                    logger.warning(f"API summary failed for cluster {cluster_id}, using fallback")
                    summaries[str(cluster_id)] = self._generate_fallback_summary(cluster_id, chunks)
                    self.stats['errors'] += 1
                
                # Add delay between API calls
                time.sleep(self.delay_between_calls)
                
            except Exception as e:
                logger.error(f"Failed to summarize cluster {cluster_id}: {e}")
                summaries[str(cluster_id)] = self._generate_fallback_summary(cluster_id, chunks)
                self.stats['errors'] += 1
        
        # Save summaries
        with open(output_file, 'w') as f:
            json.dump(summaries, f, indent=2)
        
        logger.info(f"Generated enhanced summaries for {len(summaries)} clusters")
        logger.info(f"Saved to {output_file}")
        
        return summaries
    
    def _generate_fallback_summary(self, cluster_id: int, chunks: List[Dict]) -> Dict:
        """Generate a basic fallback summary when API fails."""
        # Extract top words from content
        all_text = " ".join([chunk.get('content', '') for chunk in chunks])
        
        # Simple word extraction
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        word_counts = Counter(word for word in words if word not in stop_words)
        top_words = [word for word, _ in word_counts.most_common(5)]
        
        # Get sample titles
        sample_titles = list(set([
            chunk.get('chat_title', '') for chunk in chunks[:5]
            if chunk.get('chat_title', '')
        ]))
        
        return {
            'topic': f"Cluster {cluster_id}",
            'description': f"Cluster containing {len(chunks)} chunks with topics: {', '.join(top_words[:3])}",
            'key_concepts': top_words[:3],
            'domain': 'unknown',
            'complexity': 'unknown',
            'sample_questions': [],
            'tags': [f"#cluster-{cluster_id}"] + [f"#{word}" for word in top_words[:3]],
            'cluster_size': len(chunks),
            'sample_titles': sample_titles,
            'total_messages': len(chunks),
            'summary_model': 'fallback',
            'summary_timestamp': int(time.time())
        }
    
    def get_summary_stats(self) -> Dict:
        """Get statistics about the summarization process."""
        return {
            'clusters_processed': self.stats['clusters_processed'],
            'api_calls': self.stats['api_calls'],
            'errors': self.stats['errors'],
            'total_tokens': self.stats['total_tokens'],
            'success_rate': (self.stats['clusters_processed'] - self.stats['errors']) / max(self.stats['clusters_processed'], 1)
        }


@click.command()
@click.option('--input-file', 
              default='data/embeddings/chunks_with_clusters.jsonl',
              help='Input chunks file')
@click.option('--output-file', 
              default='data/embeddings/enhanced_cluster_summaries.json',
              help='Output summaries file')
@click.option('--model', 
              default='gpt-3.5-turbo',
              help='OpenAI model to use')
@click.option('--max-retries', 
              default=3,
              help='Maximum retries for API calls')
@click.option('--delay', 
              default=1.0,
              help='Delay between API calls (seconds)')
def main(input_file: str, output_file: str, model: str, max_retries: int, delay: float):
    """Generate enhanced cluster summaries using OpenAI API."""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize summarizer
    summarizer = EnhancedClusterSummarizer(
        model=model,
        max_retries=max_retries,
        delay_between_calls=delay
    )
    
    # Generate summaries
    summaries = summarizer.generate_enhanced_summaries(input_path, output_path)
    
    # Get statistics
    stats = summarizer.get_summary_stats()
    
    # Print summary statistics
    total_clusters = len(summaries)
    total_messages = sum(s['total_messages'] for s in summaries.values())
    avg_cluster_size = total_messages / total_clusters if total_clusters > 0 else 0
    
    print(f"\n📊 Enhanced Cluster Summary Statistics:")
    print(f"  - Total clusters: {total_clusters}")
    print(f"  - Total messages: {total_messages}")
    print(f"  - Average cluster size: {avg_cluster_size:.1f}")
    print(f"  - API calls made: {stats['api_calls']}")
    print(f"  - Total tokens used: {stats['total_tokens']}")
    print(f"  - Success rate: {stats['success_rate']:.1%}")
    print(f"  - Errors: {stats['errors']}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 