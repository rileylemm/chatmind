#!/usr/bin/env python3
"""
Local Enhanced Auto-Tagger for ChatMind

Uses local models (Ollama, etc.) instead of OpenAI API to eliminate costs.
Maintains the same enhanced features: conversation-level context, validation, and better prompts.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import time
from tqdm import tqdm
from collections import defaultdict, Counter
import requests
import subprocess
import sys

from chatmind.tagger.cloud_api.enhanced_prompts import get_enhanced_prompt, conversation_level_prompt, validation_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalEnhancedChunkTagger:
    """Enhanced auto-tagger using local models instead of OpenAI API."""
    
    def __init__(self, 
                 model: str = "llama3.1:8b",  # Default to Llama 3.1 8B
                 temperature: float = 0.2,
                 max_retries: int = 3,
                 delay_between_calls: float = 0.5,  # Faster for local models
                 enable_validation: bool = True,
                 enable_conversation_context: bool = True,
                 ollama_url: str = "http://localhost:11434"):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        self.enable_validation = enable_validation
        self.enable_conversation_context = enable_conversation_context
        self.ollama_url = ollama_url
        
        # Statistics tracking
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'validation_failures': 0,
            'conversation_analyses': 0,
            'chunks_tagged': 0
        }
    
    def _call_local_model(self, prompt: str, system_prompt: str = "") -> str:
        """
        Call local model via Ollama API.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
        
        Returns:
            Model response as string
        """
        try:
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": False
                },
                timeout=60  # 60 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.stats['successful_calls'] += 1
                return result['message']['content']
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                self.stats['failed_calls'] += 1
                raise Exception(f"API call failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error calling local model: {e}")
            self.stats['failed_calls'] += 1
            raise
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from model response, handling various formats."""
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}')
            
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                return json.loads(json_str)
            else:
                # If no JSON found, try to parse the entire response
                return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
            logger.debug(f"Raw response: {response[:200]}...")
            raise
    
    def analyze_conversation(self, chunks: List[Dict]) -> Dict:
        """
        Analyze conversation at the conversation level using local model.
        
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
            system_prompt = "You are an expert conversation classifier."
            
            response = self._call_local_model(prompt, system_prompt)
            result = self._extract_json_from_response(response)
            
            self.stats['conversation_analyses'] += 1
            logger.info(f"Conversation analysis: {result.get('primary_domain', 'unknown')} domain")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to analyze conversation: {e}")
            return {}
    
    def validate_tags(self, chunk_text: str, proposed_tags: List[str], conversation_context: str = "") -> Tuple[bool, List[str], str]:
        """
        Validate if proposed tags are appropriate using local model.
        
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
            system_prompt = "You are a tag validation expert."
            
            response = self._call_local_model(prompt, system_prompt)
            result = self._extract_json_from_response(response)
            
            is_valid = result.get('is_valid', True)
            suggested_tags = result.get('suggested_tags', proposed_tags)
            reasoning = result.get('reasoning', 'No issues found')
            
            if not is_valid:
                self.stats['validation_failures'] += 1
            
            return is_valid, suggested_tags, reasoning
            
        except Exception as e:
            logger.warning(f"Failed to validate tags: {e}")
            return True, proposed_tags, "Validation failed"
    
    def tag_chunk(self, chunk: Dict, conversation_context: Dict = None) -> Dict:
        """
        Tag a single chunk using local model.
        
        Args:
            chunk: Dictionary containing chunk information
            conversation_context: Optional conversation context
        
        Returns:
            Dictionary with enhanced tags and metadata
        """
        # Prepare content for tagging
        content = chunk.get('content', '')
        title = chunk.get('title', '')
        
        # Combine title and content for better context
        full_text = f"Title: {title}\n\nContent: {content}" if title else content
        
        # Get conversation context string
        context_str = ""
        if conversation_context:
            domain = conversation_context.get('primary_domain', '')
            topics = conversation_context.get('key_topics', [])
            context_str = f"Domain: {domain}, Topics: {', '.join(topics[:3])}"
        
        # Get initial tags from local model
        try:
            prompt = get_enhanced_prompt(full_text, context_str, "enhanced")
            system_prompt = "You are an expert content classifier and tagger."
            
            response = self._call_local_model(prompt, system_prompt)
            result = self._extract_json_from_response(response)
            
            # Validate tags if enabled
            if self.enable_validation:
                is_valid, suggested_tags, reasoning = self.validate_tags(
                    full_text, result.get('tags', []), context_str
                )
                
                if not is_valid:
                    logger.info(f"Tag validation failed: {reasoning}")
                    result['tags'] = suggested_tags
                    result['validation_issues'] = [reasoning]
            
            # Enhance chunk with tags and metadata
            enhanced_chunk = {
                **chunk,
                'tags': result.get('tags', []),
                'category': result.get('category', ''),
                'domain': result.get('domain', ''),
                'confidence': result.get('confidence', 'medium'),
                'tagging_model': f"local-{self.model}",
                'tagging_timestamp': int(time.time()),
                'conversation_context': conversation_context,
                'local_model_stats': self.stats.copy()
            }
            
            self.stats['chunks_tagged'] += 1
            return enhanced_chunk
            
        except Exception as e:
            logger.error(f"Failed to tag chunk: {e}")
            # Return fallback tags
            return {
                **chunk,
                'tags': ['#error', '#local-model-failed'],
                'category': 'Error in local tagging',
                'domain': 'unknown',
                'confidence': 'low',
                'tagging_model': f"local-{self.model}-fallback",
                'tagging_timestamp': int(time.time()),
                'error': str(e)
            }
    
    def tag_conversation_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Tag all chunks in a conversation with context awareness.
        
        Args:
            chunks: List of chunks from the same conversation
        
        Returns:
            List of tagged chunks
        """
        if not chunks:
            return []
        
        # Get conversation ID for logging
        conv_id = chunks[0].get('convo_id') or chunks[0].get('chat_id') or 'unknown'
        logger.info(f"Processing conversation {conv_id} with {len(chunks)} chunks")
        
        # Analyze conversation context
        conversation_context = self.analyze_conversation(chunks)
        
        # Tag each chunk with conversation context
        tagged_chunks = []
        for chunk in tqdm(chunks, desc=f"Tagging chunks in {conv_id}"):
            tagged_chunk = self.tag_chunk(chunk, conversation_context)
            tagged_chunks.append(tagged_chunk)
            
            # Add delay between calls
            time.sleep(self.delay_between_calls)
        
        return tagged_chunks
    
    def get_enhanced_tagging_stats(self, tagged_chunks: List[Dict]) -> Dict:
        """
        Get comprehensive statistics about the tagging process.
        
        Args:
            tagged_chunks: List of tagged chunks
        
        Returns:
            Dictionary with tagging statistics
        """
        if not tagged_chunks:
            return {}
        
        # Collect all tags
        all_tags = []
        domains = []
        confidence_levels = []
        validation_issues = []
        
        for chunk in tagged_chunks:
            tags = chunk.get('tags', [])
            all_tags.extend(tags)
            domains.append(chunk.get('domain', 'unknown'))
            confidence_levels.append(chunk.get('confidence', 'medium'))
            
            if 'validation_issues' in chunk:
                validation_issues.extend(chunk['validation_issues'])
        
        # Calculate statistics
        tag_counts = Counter(all_tags)
        domain_counts = Counter(domains)
        confidence_counts = Counter(confidence_levels)
        
        # Identify potential issues
        potential_issues = []
        if len(validation_issues) > len(tagged_chunks) * 0.1:  # More than 10% have validation issues
            potential_issues.append(f"High validation failure rate: {len(validation_issues)} issues")
        
        if len(set(all_tags)) < len(tagged_chunks) * 0.5:  # Very low tag diversity
            potential_issues.append("Low tag diversity detected")
        
        return {
            'total_chunks': len(tagged_chunks),
            'total_tags': len(all_tags),
            'unique_tags': len(set(all_tags)),
            'unique_domains': len(set(domains)),
            'top_tags': tag_counts.most_common(20),
            'domain_counts': dict(domain_counts),
            'confidence_distribution': dict(confidence_counts),
            'validation_issues': validation_issues,
            'potential_issues': potential_issues,
            'local_model_stats': self.stats
        }
    
    def check_model_availability(self) -> bool:
        """Check if the local model is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                if self.model in available_models:
                    logger.info(f"✅ Model {self.model} is available")
                    return True
                else:
                    logger.warning(f"❌ Model {self.model} not found. Available: {available_models}")
                    return False
            else:
                logger.error(f"❌ Cannot connect to Ollama at {self.ollama_url}")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking model availability: {e}")
            return False


def test_local_model():
    """Test the local model with a simple prompt."""
    tagger = LocalEnhancedChunkTagger(model="mistral:latest")
    
    if not tagger.check_model_availability():
        logger.error("Local model not available. Please install Ollama and pull a model.")
        return False
    
    # Test with a simple prompt
    test_chunk = {
        "content": "Let's build a React portfolio site with Tailwind CSS and animations",
        "title": "Web Development Project"
    }
    
    try:
        tagged_chunk = tagger.tag_chunk(test_chunk)
        logger.info(f"✅ Test successful! Tags: {tagged_chunk.get('tags', [])}")
        return True
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the local model
    test_local_model() 