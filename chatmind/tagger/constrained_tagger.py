#!/usr/bin/env python3
"""
Constrained Auto-Tagger for ChatMind

Modified version of the existing tagger that constrains tag selection
to the master tag list using OpenAI function calling.
"""

import openai
from openai import OpenAI
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import time
from tqdm import tqdm

from .prompts import tagging_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConstrainedChunkTagger:
    """Handles automatic tagging of semantic chunks using GPT with constrained tag selection."""
    
    def __init__(self, 
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.2,
                 max_retries: int = 3,
                 delay_between_calls: float = 1.0,
                 master_tags_path: str = "data/tags/tags_master_list.json"):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        
        # Load master tags
        self.master_tags = self._load_master_tags(master_tags_path)
        self.function_schema = self._create_function_schema()
        
        # Initialize OpenAI client
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
    
    def _load_master_tags(self, path: str) -> List[str]:
        """Load the master tag list."""
        try:
            with open(path, "r") as f:
                tags = json.load(f)
            logger.info(f"Loaded {len(tags)} master tags from {path}")
            return tags
        except FileNotFoundError:
            logger.error(f"Master tags file not found: {path}")
            raise
        except Exception as e:
            logger.error(f"Error loading master tags: {e}")
            raise
    
    def _create_function_schema(self) -> Dict:
        """Create the function schema for constrained tag selection."""
        return {
            "name": "select_tags",
            "description": "Select relevant tags from the master list for the given text chunk",
            "parameters": {
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": self.master_tags  # This constrains to master list
                        },
                        "description": "Tags selected from the master list (3-8 recommended)",
                        "minItems": 0,
                        "maxItems": 10
                    },
                    "category": {
                        "type": "string",
                        "description": "A short, descriptive category label"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of tag selection"
                    }
                },
                "required": ["tags", "category"]
            }
        }
    
    def tag_chunk(self, chunk: Dict) -> Dict:
        """
        Tag a single chunk with hashtags and category using constrained selection.
        
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
        
        # Get tags from GPT with constraints
        tags_result = self._get_constrained_tags_from_gpt(full_text)
        
        # Enhance chunk with tags
        enhanced_chunk = {
            **chunk,
            'tags': tags_result.get('tags', []),
            'category': tags_result.get('category', ''),
            'tagging_model': self.model,
            'tagging_timestamp': int(time.time()),
            'constrained_tagging': True  # Flag to indicate constrained tagging
        }
        
        return enhanced_chunk
    
    def _get_constrained_tags_from_gpt(self, text: str) -> Dict:
        """Get tags from GPT using function calling to constrain to master list."""
        
        # Create the constrained prompt
        prompt = self._create_constrained_prompt(text)
        
        for attempt in range(self.max_retries):
            try:
                # Call the OpenAI client with function calling
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert note classifier and tagger that selects tags from a predefined master list."},
                        {"role": "user", "content": prompt}
                    ],
                    functions=[self.function_schema],
                    function_call={"name": "select_tags"},
                    temperature=self.temperature,
                )
                
                # Track the API call usage if available
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    usage = getattr(response, 'usage', None)
                    input_tokens = getattr(usage, 'prompt_tokens', 0)
                    output_tokens = getattr(usage, 'completion_tokens', 0)
                    
                    track_api_call(
                        model=self.model,
                        operation='constrained_tagging',
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        success=True,
                        metadata={
                            'chunk_id': text[:50] + '...' if len(text) > 50 else text,
                            'attempt': attempt + 1,
                            'constrained': True
                        }
                    )
                except ImportError:
                    logger.debug("Cost tracker not available")
                except Exception as e:
                    logger.warning(f"Failed to track API call: {e}")
                
                # Extract function call result
                function_call = response.choices[0].message.function_call
                if function_call and function_call.name == "select_tags":
                    result = json.loads(function_call.arguments)
                    
                    # Validate result
                    if self._validate_constrained_result(result):
                        logger.debug(f"Successfully tagged chunk with {len(result.get('tags', []))} constrained tags")
                        return result
                    else:
                        logger.warning(f"Invalid constrained tagging result (attempt {attempt + 1}): {result}")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.delay_between_calls)
                            continue
                        else:
                            return self._get_fallback_tags()
                else:
                    logger.warning(f"No function call returned (attempt {attempt + 1})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay_between_calls)
                        continue
                    else:
                        return self._get_fallback_tags()
                        
            except Exception as e:
                logger.error(f"Error calling GPT with constraints (attempt {attempt + 1}): {e}")
                
                # Track failed API call
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    track_api_call(
                        model=self.model,
                        operation='constrained_tagging',
                        input_tokens=len(prompt.split()),  # Rough estimate
                        output_tokens=0,
                        success=False,
                        error_message=str(e),
                        metadata={'attempt': attempt + 1, 'constrained': True}
                    )
                except ImportError:
                    pass
                except Exception as tracking_error:
                    logger.warning(f"Failed to track failed API call: {tracking_error}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    logger.error("Failed to get constrained tags from GPT, using fallback")
                    return self._get_fallback_tags()
        
        return self._get_fallback_tags()
    
    def _create_constrained_prompt(self, text: str) -> str:
        """Create a prompt that instructs GPT to use the constrained tag list."""
        return f"""You are an AI assistant that analyzes text and assigns relevant semantic tags and a concise category.

TASK:
Analyze the following text and:
1. Generate 3–5 relevant hashtags from the provided master list
2. Assign a short, descriptive category label

GUIDELINES:
- You MUST select tags ONLY from the provided master list
- Tags must be specific and meaningful
- Focus on the most relevant tags for the content
- Consider both technical and conceptual aspects
- The category must be a short phrase, not a full sentence

OUTPUT FORMAT:
Use the select_tags function to return your selection.

TEXT TO TAG:
---
{text}
---

Remember: You can ONLY select tags from the master list provided to you."""
    
    def _validate_constrained_result(self, result: Dict) -> bool:
        """Validate that the constrained GPT response has the expected format."""
        if not isinstance(result, dict):
            return False
        
        # Check for required fields
        if 'tags' not in result or 'category' not in result:
            return False
        
        # Validate tags are from master list
        tags = result.get('tags', [])
        if not isinstance(tags, list):
            return False
        
        # Check that all tags are in master list
        for tag in tags:
            if tag not in self.master_tags:
                logger.warning(f"Tag '{tag}' not in master list")
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
            'category': 'Uncategorized',
            'reasoning': 'Fallback due to tagging failure'
        }
    
    def tag_multiple_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Tag multiple chunks with progress tracking."""
        tagged_chunks = []
        
        for chunk in tqdm(chunks, desc="Tagging chunks (constrained)"):
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
                    'category': 'Error in constrained tagging',
                    'tagging_model': 'fallback',
                    'tagging_timestamp': int(time.time()),
                    'constrained_tagging': True
                }
                tagged_chunks.append(fallback_chunk)
        
        logger.info(f"Tagged {len(tagged_chunks)} chunks with constrained tagging")
        return tagged_chunks
    
    def get_tagging_stats(self, tagged_chunks: List[Dict]) -> Dict:
        """Get statistics about the constrained tagging results."""
        all_tags = []
        categories = []
        constrained_count = 0
        
        for chunk in tagged_chunks:
            tags = chunk.get('tags', [])
            all_tags.extend(tags)
            categories.append(chunk.get('category', ''))
            if chunk.get('constrained_tagging', False):
                constrained_count += 1
        
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
            'constrained_chunks': constrained_count,
            'total_tags': len(all_tags),
            'unique_tags': len(set(all_tags)),
            'unique_categories': len(set(categories)),
            'top_tags': top_tags,
            'category_counts': category_counts,
            'master_list_size': len(self.master_tags)
        }


def tag_chunk_constrained(chunk: Dict, model: str = "gpt-4") -> Dict:
    """
    Convenience function for constrained tagging of a single chunk.
    
    Args:
        chunk: Dictionary containing chunk information
        model: GPT model to use
    
    Returns:
        Dictionary with constrained tags and category added
    """
    tagger = ConstrainedChunkTagger(model=model)
    return tagger.tag_chunk(chunk) 