#!/usr/bin/env python3
"""
Enhanced Auto-Tagger for ChatMind

Improved tagging system with conversation-level context, validation, and better error handling.
"""

import openai
from openai import OpenAI
import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import time
from tqdm import tqdm
from collections import defaultdict, Counter

from chatmind.tagger.cloud_api.enhanced_prompts import get_enhanced_prompt, conversation_level_prompt, validation_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedChunkTagger:
    """Enhanced tagger with conversation-level context and validation."""
    
    def __init__(self, 
                 model: str = "gpt-3.5-turbo",
                 temperature: float = 0.2,
                 max_retries: int = 3,
                 delay_between_calls: float = 1.0,
                 enable_validation: bool = True,
                 enable_conversation_context: bool = True):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        self.enable_validation = enable_validation
        self.enable_conversation_context = enable_conversation_context
        
        # Initialize OpenAI client
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=api_key)
    
    def analyze_conversation(self, chunks: List[Dict]) -> Dict:
        """
        Analyze conversation at the conversation level to understand context.
        
        Args:
            chunks: List of chunks from the same conversation
        
        Returns:
            Conversation analysis with domain and key topics
        """
        if not self.enable_conversation_context or not chunks:
            return {}
        
        # Create a representative sample of the conversation
        total_content = ""
        for chunk in chunks[:10]:  # Sample first 10 chunks
            content = chunk.get('content', '')
            total_content += content[:500] + "\n"  # Limit each chunk
        
        if len(total_content) > 4000:  # Truncate if too long
            total_content = total_content[:4000]
        
        try:
            prompt = conversation_level_prompt(total_content)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert conversation classifier."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
            )
            
            choice = response.choices[0]
            raw = choice.message.content or ''
            json_text = raw.strip()
            
            if not json_text.startswith('{'):
                start = json_text.find('{')
                end = json_text.rfind('}')
                if start != -1 and end != -1:
                    json_text = json_text[start:end+1]
            
            result = json.loads(json_text)
            logger.info(f"Conversation analysis: {result.get('primary_domain', 'unknown')} domain")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to analyze conversation: {e}")
            return {}
    
    def validate_tags(self, chunk_text: str, proposed_tags: List[str], conversation_context: str = "") -> Tuple[bool, List[str], str]:
        """
        Validate if proposed tags are appropriate for the content.
        
        Args:
            chunk_text: The chunk text
            proposed_tags: Tags to validate
            conversation_context: Conversation context
        
        Returns:
            Tuple of (is_valid, suggested_tags, reasoning)
        """
        if not self.enable_validation:
            return True, proposed_tags, "Validation disabled"
        
        try:
            prompt = validation_prompt(chunk_text, proposed_tags, conversation_context)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a tag validation expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
            )
            
            choice = response.choices[0]
            raw = choice.message.content or ''
            json_text = raw.strip()
            
            if not json_text.startswith('{'):
                start = json_text.find('{')
                end = json_text.rfind('}')
                if start != -1 and end != -1:
                    json_text = json_text[start:end+1]
            
            result = json.loads(json_text)
            
            is_valid = result.get('is_valid', True)
            suggested_tags = result.get('suggested_tags', proposed_tags)
            reasoning = result.get('reasoning', 'No issues found')
            
            return is_valid, suggested_tags, reasoning
            
        except Exception as e:
            logger.warning(f"Failed to validate tags: {e}")
            return True, proposed_tags, "Validation failed"
    
    def tag_chunk(self, chunk: Dict, conversation_context: Dict = None) -> Dict:
        """
        Tag a single chunk with enhanced context awareness.
        
        Args:
            chunk: Dictionary containing chunk information
            conversation_context: Optional conversation analysis
        
        Returns:
            Dictionary with enhanced tags and category
        """
        content = chunk.get('content', '')
        title = chunk.get('title', '')
        
        # Prepare context information
        context_info = ""
        if conversation_context:
            domain = conversation_context.get('primary_domain', '')
            topics = conversation_context.get('key_topics', [])
            context_info = f"Domain: {domain}, Topics: {', '.join(topics[:3])}"
        
        # Combine title and content for better context
        full_text = f"Title: {title}\n\nContent: {content}" if title else content
        
        # Get initial tags from GPT
        initial_result = self._get_tags_from_gpt(full_text, context_info)
        
        # Validate tags if enabled
        if self.enable_validation:
            is_valid, suggested_tags, reasoning = self.validate_tags(
                full_text, 
                initial_result.get('tags', []), 
                context_info
            )
            
            if not is_valid:
                logger.info(f"Tag validation failed: {reasoning}")
                # Use suggested tags if validation failed
                initial_result['tags'] = suggested_tags
                initial_result['validation_issues'] = reasoning
        
        # Enhance chunk with tags and metadata
        enhanced_chunk = {
            **chunk,
            'tags': initial_result.get('tags', []),
            'category': initial_result.get('category', ''),
            'domain': initial_result.get('domain', ''),
            'confidence': initial_result.get('confidence', 'medium'),
            'tagging_model': self.model,
            'tagging_timestamp': int(time.time()),
            'conversation_context': conversation_context or {}
        }
        
        return enhanced_chunk
    
    def _get_tags_from_gpt(self, text: str, conversation_context: str = "") -> Dict:
        """Get tags from GPT with enhanced prompt and retry logic."""
        prompt = get_enhanced_prompt(text, conversation_context, "enhanced")
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert content classifier and tagger."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                )
                
                # Track API usage
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    usage = getattr(response, 'usage', None)
                    input_tokens = getattr(usage, 'prompt_tokens', 0)
                    output_tokens = getattr(usage, 'completion_tokens', 0)
                    
                    track_api_call(
                        model=self.model,
                        operation='enhanced_tagging',
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        success=True,
                        metadata={'attempt': attempt + 1}
                    )
                except ImportError:
                    logger.debug("Cost tracker not available")
                except Exception as e:
                    logger.warning(f"Failed to track API call: {e}")
                
                # Parse response
                choice = response.choices[0]
                raw = choice.message.content or ''
                json_text = raw.strip()
                
                if not json_text.startswith('{'):
                    start = json_text.find('{')
                    end = json_text.rfind('}')
                    if start != -1 and end != -1:
                        json_text = json_text[start:end+1]
                
                result = json.loads(json_text)
                
                # Validate result
                if self._validate_enhanced_result(result):
                    logger.debug(f"Successfully tagged chunk with {len(result.get('tags', []))} tags")
                    return result
                else:
                    logger.warning(f"Invalid enhanced tagging result (attempt {attempt + 1}): {result}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay_between_calls)
                        continue
                    else:
                        return self._get_enhanced_fallback_tags()
                        
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse GPT response (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    logger.error("Failed to get valid tags from GPT, using fallback")
                    return self._get_enhanced_fallback_tags()
                    
            except Exception as e:
                logger.error(f"Error calling GPT (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    logger.error("Failed to get tags from GPT, using fallback")
                    return self._get_enhanced_fallback_tags()
        
        return self._get_enhanced_fallback_tags()
    
    def _validate_enhanced_result(self, result: Dict) -> bool:
        """Validate that the enhanced GPT response has the expected format."""
        if not isinstance(result, dict):
            return False
        
        # Check for required fields
        required_fields = ['tags', 'category']
        for field in required_fields:
            if field not in result:
                return False
        
        # Validate tags
        tags = result.get('tags', [])
        if not isinstance(tags, list):
            return False
        
        # Validate category
        category = result.get('category', '')
        if not isinstance(category, str) or len(category.strip()) == 0:
            return False
        
        # Validate optional fields
        if 'domain' in result and not isinstance(result['domain'], str):
            return False
        
        if 'confidence' in result and result['confidence'] not in ['high', 'medium', 'low']:
            return False
        
        return True
    
    def _get_enhanced_fallback_tags(self) -> Dict:
        """Get enhanced fallback tags when GPT fails."""
        return {
            'tags': ['#untagged'],
            'category': 'Uncategorized',
            'domain': 'unknown',
            'confidence': 'low'
        }
    
    def tag_conversation_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Tag multiple chunks with conversation-level context awareness.
        
        Args:
            chunks: List of chunks from the same conversation
        
        Returns:
            List of enhanced tagged chunks
        """
        if not chunks:
            return []
        
        # Group chunks by conversation
        conversation_groups = defaultdict(list)
        for chunk in chunks:
            conv_id = chunk.get('convo_id') or chunk.get('chat_id') or 'unknown'
            conversation_groups[conv_id].append(chunk)
        
        all_tagged_chunks = []
        
        for conv_id, conv_chunks in conversation_groups.items():
            logger.info(f"Processing conversation {conv_id} with {len(conv_chunks)} chunks")
            
            # Analyze conversation first
            conversation_context = self.analyze_conversation(conv_chunks)
            
            # Tag chunks with conversation context
            tagged_chunks = []
            for chunk in tqdm(conv_chunks, desc=f"Tagging chunks in {conv_id}"):
                try:
                    tagged_chunk = self.tag_chunk(chunk, conversation_context)
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
                        'domain': 'unknown',
                        'confidence': 'low',
                        'tagging_model': 'fallback',
                        'tagging_timestamp': int(time.time()),
                        'conversation_context': conversation_context
                    }
                    tagged_chunks.append(fallback_chunk)
            
            all_tagged_chunks.extend(tagged_chunks)
        
        logger.info(f"Tagged {len(all_tagged_chunks)} chunks across {len(conversation_groups)} conversations")
        return all_tagged_chunks
    
    def get_enhanced_tagging_stats(self, tagged_chunks: List[Dict]) -> Dict:
        """Get enhanced statistics about the tagging results."""
        all_tags = []
        categories = []
        domains = []
        confidence_levels = []
        
        for chunk in tagged_chunks:
            tags = chunk.get('tags', [])
            all_tags.extend(tags)
            categories.append(chunk.get('category', ''))
            domains.append(chunk.get('domain', ''))
            confidence_levels.append(chunk.get('confidence', 'medium'))
        
        # Count tag frequencies
        tag_counts = Counter(all_tags)
        
        # Get most common tags
        top_tags = tag_counts.most_common(10)
        
        # Count categories and domains
        category_counts = Counter(categories)
        domain_counts = Counter(domains)
        confidence_counts = Counter(confidence_levels)
        
        # Detect potential issues
        issues = []
        if tag_counts.get('#genetic-disorder', 0) > 100:
            issues.append("High frequency of medical tags - possible systematic bias")
        if tag_counts.get('#untagged', 0) > len(tagged_chunks) * 0.1:
            issues.append("High frequency of untagged chunks - possible tagging failures")
        
        return {
            'total_chunks': len(tagged_chunks),
            'total_tags': len(all_tags),
            'unique_tags': len(set(all_tags)),
            'unique_categories': len(set(categories)),
            'unique_domains': len(set(domains)),
            'top_tags': top_tags,
            'category_counts': dict(category_counts.most_common(10)),
            'domain_counts': dict(domain_counts),
            'confidence_distribution': dict(confidence_counts),
            'potential_issues': issues
        }


def enhanced_tag_chunk(chunk: Dict, model: str = "gpt-3.5-turbo") -> Dict:
    """
    Convenience function for enhanced tagging of a single chunk.
    
    Args:
        chunk: Dictionary containing chunk information
        model: GPT model to use
    
    Returns:
        Dictionary with enhanced tags and category added
    """
    tagger = EnhancedChunkTagger(model=model)
    return tagger.tag_chunk(chunk) 