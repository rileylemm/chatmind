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
import os
from datetime import datetime

from chatmind.tagger.cloud_api.enhanced_prompts import get_enhanced_prompt, conversation_level_prompt, validation_prompt
from chatmind.tagger.local.local_prompts import (
    get_gemma_tagging_prompt, get_gemma_conversation_prompt, get_gemma_validation_prompt
)

# Create logs directory if it doesn't exist
log_dir = Path("chatmind/tagger/logs")
log_dir.mkdir(parents=True, exist_ok=True)

# Set up file logging
log_file = log_dir / f"local_tagger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

# Set up console logging
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"Logging to: {log_file}")


class LocalEnhancedChunkTagger:
    """Enhanced auto-tagger using local models instead of OpenAI API."""
    
    def __init__(self, 
                 model: str = "gemma:2b",  # Default to Gemma-2B for better JSON compliance
                 temperature: float = 0.2,
                 max_retries: int = 3,
                 delay_between_calls: float = 0.1,  # Fast for Gemma-2B
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
        Call local model via Ollama API with retries and better error handling.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
        
        Returns:
            Model response as string
        """
        logger.debug(f"Calling local model: {self.model}")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        logger.debug(f"System prompt: {system_prompt[:100] if system_prompt else 'None'}...")
        
        for attempt in range(self.max_retries):
            try:
                # Prepare messages
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                logger.debug(f"API call attempt {attempt + 1}/{self.max_retries}")
                logger.debug(f"Request URL: {self.ollama_url}/api/chat")
                logger.debug(f"Request payload: model={self.model}, temperature={self.temperature}")
                
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
                
                logger.debug(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get('message', {}).get('content', '')
                    
                    logger.debug(f"Response content length: {len(content)} chars")
                    logger.debug(f"Response preview: {content[:200]}...")
                    
                    if not content or content.strip() == "":
                        logger.warning(f"Empty response from model (attempt {attempt + 1}/{self.max_retries})")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.delay_between_calls * 2)  # Longer delay for empty responses
                            continue
                        else:
                            raise Exception("Model returned empty response after all retries")
                    
                    self.stats['successful_calls'] += 1
                    logger.debug(f"Successful API call (attempt {attempt + 1})")
                    return content
                else:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    self.stats['failed_calls'] += 1
                    if attempt < self.max_retries - 1:
                        time.sleep(self.delay_between_calls)
                        continue
                    else:
                        raise Exception(f"API call failed: {response.status_code}")
                        
            except Exception as e:
                logger.error(f"Error calling local model (attempt {attempt + 1}/{self.max_retries}): {e}")
                self.stats['failed_calls'] += 1
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    raise
    
    def _extract_json_from_response(self, response: str) -> Dict:
        """Extract JSON from model response, handling various formats with robust fallbacks."""
        logger.debug(f"Extracting JSON from response of length {len(response)}")
        
        if not response or response.strip() == "":
            logger.warning("Empty response from model")
            return self._get_fallback_response()
        
        # Clean the response
        cleaned_response = response.strip()
        logger.debug(f"Cleaned response length: {len(cleaned_response)}")
        logger.debug(f"Response preview: {cleaned_response[:300]}...")
        
        # Try multiple JSON extraction strategies
        strategies = [
            # Strategy 1: Find JSON between braces
            lambda: self._extract_json_between_braces(cleaned_response),
            # Strategy 2: Try to parse the entire response
            lambda: json.loads(cleaned_response),
            # Strategy 3: Look for JSON after "```json" or "```"
            lambda: self._extract_json_from_code_blocks(cleaned_response),
            # Strategy 4: Try to fix common JSON issues
            lambda: self._fix_and_parse_json(cleaned_response)
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.debug(f"Trying JSON extraction strategy {i}")
                result = strategy()
                if result:
                    logger.debug(f"JSON extraction succeeded with strategy {i}")
                    logger.debug(f"Extracted JSON keys: {list(result.keys())}")
                    return result
            except Exception as e:
                logger.debug(f"Strategy {i} failed: {e}")
                continue
        
        # All strategies failed
        logger.warning(f"All JSON extraction strategies failed for response: {cleaned_response[:200]}...")
        logger.debug(f"Full response for debugging: {cleaned_response}")
        return self._get_fallback_response()
    
    def _extract_json_between_braces(self, response: str) -> Dict:
        """Extract JSON between the first { and last }."""
        start = response.find('{')
        end = response.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            json_str = response[start:end+1]
            return json.loads(json_str)
        raise ValueError("No JSON braces found")
    
    def _extract_json_from_code_blocks(self, response: str) -> Dict:
        """Extract JSON from code blocks like ```json or ```."""
        import re
        
        # Look for ```json ... ``` or ``` ... ```
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return json.loads(matches[0].strip())
        
        raise ValueError("No code blocks found")
    
    def _fix_and_parse_json(self, response: str) -> Dict:
        """Try to fix common JSON issues and parse."""
        # Remove common prefixes/suffixes that break JSON
        cleaned = response
        prefixes = [
            'Here is the JSON:', 'JSON:', 'Response:', 'Answer:', 
            'Sure, here\'s', 'Here\'s', 'Here is', 'Sure,',
            'Your AI assistant has', 'I can help you',
            'Dear [Your Name],', 'Tag this text with',
            'Content:', 'Context:', 'Response: [No response]'
        ]
        
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove any trailing text after the JSON
        if '}' in cleaned:
            last_brace = cleaned.rfind('}')
            cleaned = cleaned[:last_brace + 1]
        
        # Try to find JSON-like structure
        start = cleaned.find('{')
        if start != -1:
            # Count braces to find proper end
            brace_count = 0
            for i, char in enumerate(cleaned[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = cleaned[start:i+1]
                        return json.loads(json_str)
        
        # If no braces found, try to construct basic JSON from content
        if 'tags' in cleaned.lower() or 'category' in cleaned.lower():
            # Try to extract tags and category from text
            import re
            tags_match = re.findall(r'#\w+', cleaned)
            if tags_match:
                return {
                    'tags': tags_match[:5],  # Limit to 5 tags
                    'category': 'Extracted from text',
                    'domain': 'unknown'
                }
        
        raise ValueError("Could not fix JSON")
    
    def _get_fallback_response(self) -> Dict:
        """Return a fallback response when JSON parsing fails."""
        return {
            'tags': ['#unprocessed', '#needs-review'],
            'category': 'Content requiring manual review',
            'domain': 'unknown',
            'confidence': 'low',
            'note': 'JSON parsing failed - needs manual tagging'
        }
    
    def analyze_conversation(self, chunks: List[Dict]) -> Dict:
        """
        Analyze conversation at the conversation level using local model.
        
        Args:
            chunks: List of chunks from the same conversation
        
        Returns:
            Conversation analysis with domain and key topics
        """
        logger.debug(f"Analyzing conversation with {len(chunks)} chunks")
        
        if not self.enable_conversation_context or not chunks:
            logger.debug("Conversation analysis disabled or no chunks")
            return {}
        
        # Create a representative sample of the conversation
        total_content = ""
        for chunk in chunks[:10]:  # Sample first 10 chunks
            content = chunk.get('content', '')
            total_content += content[:500] + "\n"  # Limit each chunk
        
        logger.debug(f"Total conversation content length: {len(total_content)}")
        
        if len(total_content) > 4000:  # Truncate if too long
            total_content = total_content[:4000]
            logger.debug(f"Truncated conversation content to 4000 chars")
        
        try:
            prompt = get_gemma_conversation_prompt(total_content)
            system_prompt = ""  # Local prompts include system prompt
            
            logger.debug(f"Conversation analysis prompt length: {len(prompt)}")
            
            response = self._call_local_model(prompt, system_prompt)
            result = self._extract_json_from_response(response)
            
            self.stats['conversation_analyses'] += 1
            logger.info(f"Conversation analysis: {result.get('primary_domain', 'unknown')} domain")
            logger.debug(f"Conversation analysis result: {result}")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to analyze conversation: {e}")
            logger.debug(f"Conversation analysis error details: {str(e)}")
            # Return a basic fallback instead of empty dict
            return {
                'primary_domain': 'general',
                'key_topics': ['general'],
                'conversation_type': 'general',
                'complexity': 'medium'
            }
    
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
            prompt = get_gemma_validation_prompt(chunk_text, proposed_tags, conversation_context)
            system_prompt = ""  # Local prompts include system prompt
            
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
        chunk_id = chunk.get('message_id', chunk.get('id', 'unknown'))
        logger.debug(f"Tagging chunk: {chunk_id}")
        
        # Prepare content for tagging
        content = chunk.get('content', '')
        title = chunk.get('title', '')
        
        logger.debug(f"Chunk content length: {len(content)}")
        logger.debug(f"Chunk title: {title}")
        
        # Combine title and content for better context
        full_text = f"Title: {title}\n\nContent: {content}" if title else content
        
        # Get conversation context string
        context_str = ""
        if conversation_context:
            domain = conversation_context.get('primary_domain', '')
            topics = conversation_context.get('key_topics', [])
            context_str = f"Domain: {domain}, Topics: {', '.join(topics[:3])}"
            logger.debug(f"Conversation context: {context_str}")
        
        # Get initial tags from local model
        try:
            # Use Gemma-optimized prompts
            prompt = get_gemma_tagging_prompt(full_text, context_str)
            system_prompt = ""
            
            logger.debug(f"Tagging prompt length: {len(prompt)}")
            logger.debug(f"Full text preview: {full_text[:200]}...")
            
            response = self._call_local_model(prompt, system_prompt)
            result = self._extract_json_from_response(response)
            
            logger.debug(f"Initial tagging result: {result}")
            
            # Validate tags if enabled
            if self.enable_validation:
                logger.debug("Running tag validation")
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
            logger.debug(f"Successfully tagged chunk {chunk_id} with {len(result.get('tags', []))} tags")
            return enhanced_chunk
            
        except Exception as e:
            logger.error(f"Failed to tag chunk {chunk_id}: {e}")
            logger.debug(f"Chunk tagging error details: {str(e)}")
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
            logger.debug("No chunks to tag")
            return []
        
        # Get conversation ID for logging
        conv_id = chunks[0].get('convo_id') or chunks[0].get('chat_id') or 'unknown'
        logger.info(f"Processing conversation {conv_id} with {len(chunks)} chunks")
        
        # Analyze conversation context
        logger.debug(f"Starting conversation analysis for {conv_id}")
        conversation_context = self.analyze_conversation(chunks)
        logger.debug(f"Conversation context for {conv_id}: {conversation_context}")
        
        # Tag each chunk with conversation context
        tagged_chunks = []
        error_count = 0
        success_count = 0
        
        for i, chunk in enumerate(tqdm(chunks, desc=f"Tagging chunks in {conv_id}")):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)} in conversation {conv_id}")
            
            try:
                tagged_chunk = self.tag_chunk(chunk, conversation_context)
                tagged_chunks.append(tagged_chunk)
                success_count += 1
                
                # Log progress every 10 chunks
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i+1}/{len(chunks)} chunks tagged in {conv_id}")
                
            except Exception as e:
                logger.error(f"Failed to tag chunk {i+1} in conversation {conv_id}: {e}")
                error_count += 1
                # Add fallback chunk
                tagged_chunks.append({
                    **chunk,
                    'tags': ['#error', '#chunk-tagging-failed'],
                    'category': 'Error in chunk tagging',
                    'domain': 'unknown',
                    'confidence': 'low',
                    'tagging_model': f"local-{self.model}-fallback",
                    'tagging_timestamp': int(time.time()),
                    'error': str(e)
                })
            
            # Add delay between calls
            time.sleep(self.delay_between_calls)
        
        logger.info(f"Completed tagging conversation {conv_id}: {success_count} success, {error_count} errors")
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