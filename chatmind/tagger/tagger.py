#!/usr/bin/env python3
"""
Auto-Tagger for ChatMind

Uses GPT to automatically tag semantic chunks with relevant hashtags and categories.
"""

import openai
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import time
from tqdm import tqdm

from .prompts import tagging_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkTagger:
    """Handles automatic tagging of semantic chunks using GPT."""
    
    def __init__(self, 
                 model: str = "gpt-4",
                 temperature: float = 0.2,
                 max_retries: int = 3,
                 delay_between_calls: float = 1.0):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        
        # Initialize OpenAI client
        try:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            openai.api_key = api_key
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise
    
    def tag_chunk(self, chunk: Dict) -> Dict:
        """
        Tag a single chunk with hashtags and category.
        
        Args:
            chunk: Dictionary containing chunk information
                - 'content': The chunk text to tag
                - 'title': Chunk title (optional)
                - Other metadata
        
        Returns:
            Dictionary with tags and category added
        """
        # Prepare content for tagging
        content = chunk.get('content', '')
        title = chunk.get('title', '')
        
        # Combine title and content for better context
        full_text = f"Title: {title}\n\nContent: {content}" if title else content
        
        # Get tags from GPT
        tags_result = self._get_tags_from_gpt(full_text)
        
        # Enhance chunk with tags
        enhanced_chunk = {
            **chunk,
            'tags': tags_result.get('tags', []),
            'category': tags_result.get('category', ''),
            'tagging_model': self.model,
            'tagging_timestamp': int(time.time())
        }
        
        return enhanced_chunk
    
    def _get_tags_from_gpt(self, text: str) -> Dict:
        """Get tags from GPT with retry logic."""
        prompt = tagging_prompt(text)
        
        for attempt in range(self.max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert note classifier and tagger."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                )
                
                # Track the API call
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    
                    # Extract token usage from response
                    usage = response.get('usage', {})
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                    
                    track_api_call(
                        model=self.model,
                        operation='tagging',
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        success=True,
                        metadata={
                            'chunk_id': text[:50] + '...' if len(text) > 50 else text,
                            'attempt': attempt + 1
                        }
                    )
                except ImportError:
                    logger.debug("Cost tracker not available")
                except Exception as e:
                    logger.warning(f"Failed to track API call: {e}")
                
                # Parse response
                content = response['choices'][0]['message']['content']
                result = json.loads(content)
                
                # Validate result
                if self._validate_tagging_result(result):
                    logger.debug(f"Successfully tagged chunk with {len(result.get('tags', []))} tags")
                    return result
                else:
                    logger.warning(f"Invalid tagging result (attempt {attempt + 1}): {result}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay_between_calls)
                        continue
                    else:
                        return self._get_fallback_tags()
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse GPT response (attempt {attempt + 1}): {e}")
                
                # Track failed API call
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    track_api_call(
                        model=self.model,
                        operation='tagging',
                        input_tokens=len(prompt.split()),  # Rough estimate
                        output_tokens=0,
                        success=False,
                        error_message=f"JSON decode error: {e}",
                        metadata={'attempt': attempt + 1}
                    )
                except ImportError:
                    pass
                except Exception as tracking_error:
                    logger.warning(f"Failed to track failed API call: {tracking_error}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    logger.error("Failed to get valid tags from GPT, using fallback")
                    return self._get_fallback_tags()
                    
            except Exception as e:
                logger.error(f"Error calling GPT (attempt {attempt + 1}): {e}")
                
                # Track failed API call
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    track_api_call(
                        model=self.model,
                        operation='tagging',
                        input_tokens=len(prompt.split()),  # Rough estimate
                        output_tokens=0,
                        success=False,
                        error_message=str(e),
                        metadata={'attempt': attempt + 1}
                    )
                except ImportError:
                    pass
                except Exception as tracking_error:
                    logger.warning(f"Failed to track failed API call: {tracking_error}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    logger.error("Failed to get tags from GPT, using fallback")
                    return self._get_fallback_tags()
        
        return self._get_fallback_tags()
    
    def _validate_tagging_result(self, result: Dict) -> bool:
        """Validate that the GPT response has the expected format."""
        if not isinstance(result, dict):
            return False
        
        # Check for required fields
        if 'tags' not in result or 'category' not in result:
            return False
        
        # Validate tags
        tags = result.get('tags', [])
        if not isinstance(tags, list):
            return False
        
        # Validate category
        category = result.get('category', '')
        if not isinstance(category, str) or len(category.strip()) == 0:
            return False
        
        return True
    
    def _get_fallback_tags(self) -> Dict:
        """Get fallback tags when GPT fails."""
        return {
            'tags': ['#untagged'],
            'category': 'Uncategorized'
        }
    
    def tag_multiple_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Tag multiple chunks with progress tracking."""
        tagged_chunks = []
        
        for chunk in tqdm(chunks, desc="Tagging chunks"):
            try:
                tagged_chunk = self.tag_chunk(chunk)
                tagged_chunks.append(tagged_chunk)
                
                # Add delay between API calls
                time.sleep(self.delay_between_calls)
                
            except Exception as e:
                logger.error(f"Failed to tag chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                # Add fallback tags
                fallback_chunk = {
                    **chunk,
                    'tags': ['#error'],
                    'category': 'Error in tagging',
                    'tagging_model': 'fallback',
                    'tagging_timestamp': int(time.time())
                }
                tagged_chunks.append(fallback_chunk)
        
        logger.info(f"Tagged {len(tagged_chunks)} chunks")
        return tagged_chunks
    
    def get_tagging_stats(self, tagged_chunks: List[Dict]) -> Dict:
        """Get statistics about the tagging results."""
        all_tags = []
        categories = []
        
        for chunk in tagged_chunks:
            tags = chunk.get('tags', [])
            all_tags.extend(tags)
            categories.append(chunk.get('category', ''))
        
        # Count tag frequencies
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get most common tags
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        top_tags = sorted_tags[:10]
        
        # Count categories
        category_counts = {}
        for category in categories:
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_chunks': len(tagged_chunks),
            'total_tags': len(all_tags),
            'unique_tags': len(set(all_tags)),
            'unique_categories': len(set(categories)),
            'top_tags': top_tags,
            'category_counts': category_counts
        }


def tag_chunk(chunk: Dict, model: str = "gpt-4") -> Dict:
    """
    Convenience function for tagging a single chunk.
    
    Args:
        chunk: Dictionary containing chunk information
        model: GPT model to use
    
    Returns:
        Dictionary with tags and category added
    """
    tagger = ChunkTagger(model=model)
    return tagger.tag_chunk(chunk) 