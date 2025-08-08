#!/usr/bin/env python3
"""
ChatMind Local Chat Summarizer

Creates summaries for entire conversations using local LLM.
Takes full chat conversations and generates comprehensive summaries.
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
import subprocess
import sys
import re
import unicodedata
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalChatSummarizer:
    """Creates chat summaries using local LLM."""
    
    def __init__(self, chats_file: str = "data/processed/ingestion/chats.jsonl"):
        self.chats_file = Path(chats_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/chat_summarization")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_chat_hash(self, chat_id: str, messages: List[Dict]) -> str:
        """Generate a hash for a chat to track if it's been processed."""
        # Create a normalized version for hashing
        normalized_chat = {
            'chat_id': chat_id,
            'message_count': len(messages),
            'message_hashes': [msg.get('id', '') for msg in messages]
        }
        content = json.dumps(normalized_chat, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_chat_hashes(self) -> Set[str]:
        """Load hashes of chats that have already been summarized."""
        hash_file = self.output_dir / "hashes.pkl"
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed chat hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def _save_processed_chat_hashes(self, hashes: Set[str]) -> None:
        """Save hashes of processed chats."""
        hash_file = self.output_dir / "hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed chat hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _save_metadata(self, stats: Dict) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'chat_summarization',
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
    
    def _load_chats(self) -> List[Dict]:
        """Load chats from JSONL file."""
        chats = []
        if self.chats_file.exists():
            with jsonlines.open(self.chats_file) as reader:
                for chat in reader:
                    chats.append(chat)
            logger.info(f"Loaded {len(chats)} chats")
        else:
            logger.warning(f"Chats file not found: {self.chats_file}")
        return chats
    
    def _create_summary_prompt(self, chat: Dict) -> str:
        """Create a prompt for summarizing an entire chat conversation."""
        # Extract conversation content
        messages = chat.get('messages', [])
        if not messages:
            return ""
        
        # Format conversation (limit to avoid token limits)
        conversation_lines = []
        total_chars = 0
        max_chars = 24000  # Increased for Gemma-2B (8k tokens ≈ 24k chars)
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '').strip()
            if content:
                sanitized_content = self._sanitize_text(content)
                line = f"{role.upper()}: {sanitized_content}"
                if total_chars + len(line) > max_chars:
                    # Add truncation indicator
                    conversation_lines.append("... (conversation truncated)")
                    break
                conversation_lines.append(line)
                total_chars += len(line)
        
        if not conversation_lines:
            return ""
        
        conversation_text = "\n\n".join(conversation_lines)
        
        prompt = f"""You are a conversation summarizer. Analyze this conversation and provide a JSON summary.

CONVERSATION:
{conversation_text}

INSTRUCTIONS:
- Provide a comprehensive summary in JSON format
- Use simple, clear language
- Avoid trailing commas in arrays
- Ensure all JSON syntax is correct
- Be specific about topics and outcomes

JSON FORMAT (use exactly these field names):
{{
    "summary": "Brief comprehensive summary of the conversation",
    "key_topics": ["topic1", "topic2", "topic3"],
    "participants": ["user", "assistant"],
    "conversation_type": "technical_discussion|casual_chat|problem_solving|tutorial|brainstorming|other",
    "key_decisions": ["decision1", "decision2"],
    "outcomes": "What was accomplished or learned",
    "complexity": "beginner|intermediate|advanced",
    "domain": "technical|personal|business|academic|creative|other",
    "confidence": 0.85
}}

IMPORTANT: Use exactly the field names shown above. Do not change them.
RESPOND WITH JSON ONLY:"""

        return prompt
    
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
        text = unicodedata.normalize('NFKC', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _get_summary_from_llm(self, prompt: str) -> Optional[Dict]:
        """Get summary from local LLM using Ollama HTTP API with retry logic."""
        import requests
        
        # Try different prompt variations if the first attempt fails
        prompt_variations = [
            prompt,  # Original prompt
            self._create_simplified_prompt(prompt),  # Simplified version
            self._create_structured_prompt(prompt)   # More structured version
        ]
        
        for attempt, current_prompt in enumerate(prompt_variations, 1):
            try:
                logger.debug(f"🔄 Attempt {attempt}/{len(prompt_variations)} with prompt variation")
                
                # Use Ollama HTTP API with Gemma-2B model
                url = "http://localhost:11434/api/chat"
                
                # Adjust temperature based on attempt
                temperature = 0.3 if attempt == 1 else 0.1  # Lower temperature for retries
                
                # Prepare request for modern Ollama API
                request_data = {
                    "model": "gemma:2b",
                    "messages": [
                        {"role": "user", "content": current_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "num_predict": 500,
                        "stop": ["```", "```json", "```\n"]  # Stop at code blocks
                    }
                }
                
                response = requests.post(url, json=request_data, timeout=180)
                response.raise_for_status()
                
                response_json = response.json()
                
                # Extract content from the response
                if 'message' in response_json and 'content' in response_json['message']:
                    response_text = response_json['message']['content'].strip()
                else:
                    logger.error(f"Unexpected response format: {response_json}")
                    continue
                
                # Try to extract and parse JSON from response
                summary = self._extract_and_parse_json(response_text)
                
                if summary:
                    logger.debug(f"✅ Successfully generated summary on attempt {attempt}")
                    return summary
                else:
                    logger.warning(f"❌ Failed to extract valid JSON on attempt {attempt}")
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Ollama API request failed on attempt {attempt}: {e}")
            except Exception as e:
                logger.error(f"Error calling Ollama API on attempt {attempt}: {e}")
        
        # All attempts failed
        logger.warning("All prompt variations failed, creating fallback summary")
        return self._create_fallback_summary({})
    
    def _create_simplified_prompt(self, original_prompt: str) -> str:
        """Create a simplified prompt for retry attempts."""
        # Extract conversation text from original prompt
        conversation_start = original_prompt.find("CONVERSATION:")
        conversation_end = original_prompt.find("INSTRUCTIONS:")
        
        if conversation_start != -1 and conversation_end != -1:
            conversation_text = original_prompt[conversation_start:conversation_end].strip()
            
            simplified_prompt = f"""Analyze this conversation and create a JSON summary.

{conversation_text}

Create a JSON object with these fields:
- summary: brief description of the conversation
- key_topics: list of main topics discussed
- participants: list of people in the conversation
- conversation_type: type of conversation
- key_decisions: list of decisions made
- outcomes: what was accomplished
- complexity: difficulty level
- domain: subject area
- confidence: how confident you are (0-1)

JSON:"""
            return simplified_prompt
        
        return original_prompt
    
    def _create_structured_prompt(self, original_prompt: str) -> str:
        """Create a more structured prompt for final retry attempt."""
        # Extract conversation text from original prompt
        conversation_start = original_prompt.find("CONVERSATION:")
        conversation_end = original_prompt.find("INSTRUCTIONS:")
        
        if conversation_start != -1 and conversation_end != -1:
            conversation_text = original_prompt[conversation_start:conversation_end].strip()
            
            structured_prompt = f"""Summarize this conversation in JSON format.

{conversation_text}

Provide a JSON object with these fields:
summary: brief description of the conversation
key_topics: list of main topics
participants: list of people involved
conversation_type: type of conversation
key_decisions: list of decisions
outcomes: what was accomplished
complexity: difficulty level
domain: subject area
confidence: confidence level (0-1)

JSON:"""
            return structured_prompt
        
        return original_prompt
    
    def _extract_and_parse_json(self, response_text: str) -> Optional[Dict]:
        """Extract and parse JSON from response with multiple fallback methods."""
        # Method 1: Standard JSON extraction
        json_str = self._extract_json_brackets(response_text)
        if json_str:
            result = self._parse_json_string(json_str)
            if result:
                return result
        
        # Method 2: Try to find JSON-like structure without brackets
        json_str = self._extract_json_like_structure(response_text)
        if json_str:
            result = self._parse_json_string(json_str)
            if result:
                return result
        
        # Method 3: Try to construct JSON from key-value pairs
        json_str = self._construct_json_from_pairs(response_text)
        if json_str:
            result = self._parse_json_string(json_str)
            if result:
                return result
        
        logger.warning("All JSON extraction methods failed")
        return None
    
    def _extract_json_brackets(self, response_text: str) -> Optional[str]:
        """Extract JSON between curly brackets."""
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx <= start_idx:
            return None
        
        json_str = response_text[start_idx:end_idx]
        return self._clean_json_string(json_str)
    
    def _extract_json_like_structure(self, response_text: str) -> Optional[str]:
        """Extract JSON-like structure that might be missing brackets."""
        # Look for patterns like "key: value" or "key": "value"
        lines = response_text.split('\n')
        json_parts = []
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                # Try to extract key-value pairs
                if '"' in line:
                    # Already has quotes, might be JSON
                    json_parts.append(line)
                else:
                    # Try to add quotes
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        if not key.startswith('"'):
                            key = f'"{key}"'
                        if not value.startswith('"') and not value.isdigit() and value not in ['true', 'false', 'null']:
                            value = f'"{value}"'
                        json_parts.append(f'{key}: {value}')
        
        if json_parts:
            json_str = '{\n' + ',\n'.join(json_parts) + '\n}'
            return self._clean_json_string(json_str)
        
        return None
    
    def _construct_json_from_pairs(self, response_text: str) -> Optional[str]:
        """Try to construct JSON from detected key-value patterns."""
        # Look for common summary patterns
        patterns = {
            'summary': r'summary[:\s]+(.+?)(?=\n|$)',
            'key_topics': r'topics?[:\s]+(.+?)(?=\n|$)',
            'participants': r'participants?[:\s]+(.+?)(?=\n|$)',
            'conversation_type': r'type[:\s]+(.+?)(?=\n|$)',
            'key_decisions': r'decisions?[:\s]+(.+?)(?=\n|$)',
            'outcomes': r'outcomes?[:\s]+(.+?)(?=\n|$)',
            'complexity': r'complexity[:\s]+(.+?)(?=\n|$)',
            'domain': r'domain[:\s]+(.+?)(?=\n|$)',
            'confidence': r'confidence[:\s]+(.+?)(?=\n|$)'
        }
        
        extracted = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if field == 'key_topics':
                    # Try to extract as array
                    topics = re.findall(r'["\']([^"\']+)["\']', value)
                    if topics:
                        extracted[field] = topics
                    else:
                        extracted[field] = [value]
                elif field == 'participants':
                    # Try to extract as array
                    participants = re.findall(r'["\']([^"\']+)["\']', value)
                    if participants:
                        extracted[field] = participants
                    else:
                        extracted[field] = [value]
                elif field == 'confidence':
                    # Try to extract as number
                    try:
                        extracted[field] = float(value)
                    except:
                        extracted[field] = 0.5
                else:
                    extracted[field] = value
        
        if len(extracted) >= 3:  # At least summary, key_topics, participants
            return json.dumps(extracted)
        
        return None
    
    def _parse_json_string(self, json_str: str) -> Optional[Dict]:
        """Parse JSON string with error handling."""
        try:
            summary = json.loads(json_str)
            normalized_summary = self._normalize_summary_fields(summary)
            
            if normalized_summary:
                return normalized_summary
            else:
                logger.warning(f"Failed to normalize summary fields: {summary}")
                return self._create_fallback_summary(summary)
                
        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse JSON: {e}")
            logger.debug(f"JSON string: {json_str}")
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean up common JSON formatting issues."""
        # Remove trailing commas in arrays and objects
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix common quote issues - unquoted field names
        json_str = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1 "\2":', json_str)
        
        # Fix single quotes to double quotes
        json_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
        
        # Fix missing quotes around string values
        json_str = re.sub(r':\s*([a-zA-Z][a-zA-Z0-9_]*)\s*([,}])', r': "\1"\2', json_str)
        
        # Fix boolean values
        json_str = re.sub(r':\s*(true|false)\s*([,}])', r': \1\2', json_str)
        
        # Fix numeric values
        json_str = re.sub(r':\s*(\d+\.?\d*)\s*([,}])', r': \1\2', json_str)
        
        # Remove any non-printable characters except newlines and tabs
        json_str = ''.join(char for char in json_str if char.isprintable() or char in '\n\t')
        
        # Remove excessive whitespace
        json_str = re.sub(r'\s+', ' ', json_str)
        
        return json_str
    
    def _normalize_summary_fields(self, summary: Dict) -> Optional[Dict]:
        """Normalize summary fields to handle variations in field names."""
        normalized = {}
        
        # Field name mappings (expected -> possible variations)
        field_mappings = {
            'summary': ['summary', 'conversation_summary', 'brief_summary'],
            'key_topics': ['key_topics', 'topics', 'main_topics', 'key_points'],
            'participants': ['participants', 'users', 'people'],
            'conversation_type': ['conversation_type', 'type', 'conversation_phase', 'chat_type'],
            'key_decisions': ['key_decisions', 'decisions', 'important_decisions', 'key_points'],
            'outcomes': ['outcomes', 'results', 'accomplishments', 'learnings'],
            'complexity': ['complexity', 'difficulty', 'level'],
            'domain': ['domain', 'category', 'field'],
            'confidence': ['confidence', 'certainty', 'score']
        }
        
        # Try to map each expected field
        for expected_field, possible_variations in field_mappings.items():
            value = None
            
            # First try the exact expected field name
            if expected_field in summary:
                value = summary[expected_field]
            else:
                # Try variations
                for variation in possible_variations:
                    if variation in summary:
                        value = summary[variation]
                        logger.debug(f"Mapped field '{variation}' to '{expected_field}'")
                        break
            
            if value is not None:
                normalized[expected_field] = value
            else:
                # Provide default value for missing field
                default_value = self._get_default_value(expected_field)
                normalized[expected_field] = default_value
                logger.debug(f"Using default value for missing field '{expected_field}': {default_value}")
        
        # Ensure we have at least the essential fields
        essential_fields = ['summary', 'key_topics', 'participants']
        if all(field in normalized for field in essential_fields):
            return normalized
        else:
            logger.warning(f"Missing essential fields after normalization: {normalized}")
            return None
    
    def _get_default_value(self, field_name: str):
        """Get default value for a field."""
        defaults = {
            'summary': 'Conversation summary unavailable',
            'key_topics': ['general'],
            'participants': ['user', 'assistant'],
            'conversation_type': 'other',
            'key_decisions': [],
            'outcomes': 'No specific outcomes identified',
            'complexity': 'unknown',
            'domain': 'other',
            'confidence': 0.5
        }
        return defaults.get(field_name, 'unknown')
    
    def _create_fallback_summary(self, partial_summary: Dict) -> Dict:
        """Create a fallback summary when LLM response is incomplete."""
        # Use the normalization method to ensure consistent structure
        normalized = self._normalize_summary_fields(partial_summary)
        
        if normalized:
            # Mark as fallback and lower confidence
            normalized['confidence'] = min(normalized.get('confidence', 0.5) * 0.8, 0.5)
            normalized['summary'] = f"[FALLBACK] {normalized.get('summary', 'Conversation summary unavailable')}"
            return normalized
        else:
            # Complete fallback if normalization failed
            fallback = {
                'summary': '[FALLBACK] Conversation summary unavailable',
                'key_topics': ['general'],
                'participants': ['user', 'assistant'],
                'conversation_type': 'other',
                'key_decisions': [],
                'outcomes': 'No specific outcomes identified',
                'complexity': 'unknown',
                'domain': 'other',
                'confidence': 0.3
            }
            return fallback
    
    def _should_chunk_conversation(self, messages: List[Dict]) -> bool:
        """Determine if conversation should be chunked based on size."""
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        return total_chars > 24000  # Our current limit
    
    def _create_chunks(self, messages: List[Dict], max_chars: int = 24000) -> List[List[Dict]]:
        """Split conversation into manageable chunks."""
        chunks = []
        current_chunk = []
        current_chars = 0
        
        for msg in messages:
            msg_content = msg.get('content', '')
            msg_line = f"{msg.get('role', 'unknown').upper()}: {msg_content}"
            
            if current_chars + len(msg_line) > max_chars and current_chunk:
                # Start new chunk
                chunks.append(current_chunk)
                current_chunk = [msg]
                current_chars = len(msg_line)
            else:
                # Add to current chunk
                current_chunk.append(msg)
                current_chars += len(msg_line)
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _summarize_chunk(self, chunk: List[Dict], chunk_index: int, total_chunks: int) -> Optional[Dict]:
        """Summarize a single chunk of the conversation."""
        # Format chunk
        conversation_lines = []
        for msg in chunk:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '').strip()
            if content:
                conversation_lines.append(f"{role.upper()}: {content}")
        
        if not conversation_lines:
            return None
        
        conversation_text = "\n\n".join(conversation_lines)
        
        prompt = f"""Summarize this conversation chunk ({chunk_index + 1} of {total_chunks}) in JSON format:

{conversation_text}

Respond with JSON only:
{{
    "summary": "Brief summary of this chunk",
    "key_topics": ["topic1", "topic2"],
    "conversation_phase": "beginning|middle|end",
    "key_points": ["point1", "point2"],
    "participants": ["user", "assistant"],
    "confidence": 0.85
}}"""
        
        return self._get_summary_from_llm(prompt)
    
    def _create_comprehensive_summary_prompt(self, chunk_summaries: List[Dict]) -> str:
        """Create prompt to combine chunk summaries into comprehensive summary."""
        summaries_text = "\n\n".join([
            f"Chunk {i+1}: {summary.get('summary', '')}"
            for i, summary in enumerate(chunk_summaries)
        ])
        
        # Check if combined summaries exceed token limit
        total_chars = len(summaries_text)
        max_chars = 20000  # Conservative limit for final summary prompt
        
        if total_chars > max_chars:
            logger.warning(f"Combined chunk summaries ({total_chars} chars) exceed limit ({max_chars} chars)")
            return self._create_hierarchical_summary_prompt(chunk_summaries)
        
        prompt = f"""Combine these conversation chunk summaries into a comprehensive summary:

{summaries_text}

Respond with JSON only:
{{
    "summary": "Comprehensive summary of the entire conversation",
    "key_topics": ["topic1", "topic2", "topic3"],
    "participants": ["user", "assistant"],
    "conversation_type": "technical_discussion|casual_chat|problem_solving|tutorial|brainstorming|other",
    "key_decisions": ["decision1", "decision2"],
    "outcomes": "What was accomplished or learned",
    "complexity": "beginner|intermediate|advanced",
    "domain": "technical|personal|business|academic|creative|other",
    "conversation_evolution": "How the conversation progressed and evolved",
    "confidence": 0.85
}}"""
        
        return prompt
    
    def _create_hierarchical_summary_prompt(self, chunk_summaries: List[Dict]) -> str:
        """Create hierarchical summary when too many chunks exist."""
        # Group chunks into manageable batches
        batch_size = 5  # Process 5 chunks at a time
        batches = [chunk_summaries[i:i + batch_size] for i in range(0, len(chunk_summaries), batch_size)]
        
        logger.info(f"Creating hierarchical summary from {len(chunk_summaries)} chunks in {len(batches)} batches")
        
        # Create intermediate summaries for each batch
        intermediate_summaries = []
        for i, batch in enumerate(batches):
            batch_text = "\n\n".join([
                f"Chunk {j+1}: {summary.get('summary', '')}"
                for j, summary in enumerate(batch)
            ])
            
            intermediate_prompt = f"""Summarize this batch of conversation chunks ({i+1} of {len(batches)}):

{batch_text}

Respond with JSON only:
{{
    "summary": "Summary of this batch of chunks",
    "key_topics": ["topic1", "topic2"],
    "key_points": ["point1", "point2"],
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
            return self._create_final_summary_from_intermediates(intermediate_summaries[0])
        else:
            # Multiple batches, combine them
            return self._create_final_summary_from_intermediates(intermediate_summaries)
    
    def _create_final_summary_from_intermediates(self, intermediate_summaries: Union[Dict, List[Dict]]) -> str:
        """Create final summary from intermediate summaries."""
        if isinstance(intermediate_summaries, dict):
            # Single intermediate summary
            summary_text = intermediate_summaries.get('summary', '')
            prompt = f"""Create a comprehensive summary from this conversation summary:

{summary_text}

Respond with JSON only:
{{
    "summary": "Comprehensive summary of the entire conversation",
    "key_topics": ["topic1", "topic2", "topic3"],
    "participants": ["user", "assistant"],
    "conversation_type": "technical_discussion|casual_chat|problem_solving|tutorial|brainstorming|other",
    "key_decisions": ["decision1", "decision2"],
    "outcomes": "What was accomplished or learned",
    "complexity": "beginner|intermediate|advanced",
    "domain": "technical|personal|business|academic|creative|other",
    "conversation_evolution": "How the conversation progressed and evolved",
    "confidence": 0.85
}}"""
        else:
            # Multiple intermediate summaries
            summaries_text = "\n\n".join([
                f"Batch {i+1}: {summary.get('summary', '')}"
                for i, summary in enumerate(intermediate_summaries)
            ])
            
            prompt = f"""Combine these conversation batch summaries into a comprehensive summary:

{summaries_text}

Respond with JSON only:
{{
    "summary": "Comprehensive summary of the entire conversation",
    "key_topics": ["topic1", "topic2", "topic3"],
    "participants": ["user", "assistant"],
    "conversation_type": "technical_discussion|casual_chat|problem_solving|tutorial|brainstorming|other",
    "key_decisions": ["decision1", "decision2"],
    "outcomes": "What was accomplished or learned",
    "complexity": "beginner|intermediate|advanced",
    "domain": "technical|personal|business|academic|creative|other",
    "conversation_evolution": "How the conversation progressed and evolved",
    "confidence": 0.85
}}"""
        
        return prompt
    
    def _summarize_chat(self, chat: Dict) -> Optional[Dict]:
        """Summarize a single chat conversation."""
        # Use content_hash as chat_id, fallback to 'unknown' if not available
        chat_id = chat.get('content_hash', chat.get('chat_id', 'unknown'))
        messages = chat.get('messages', [])
        
        logger.info(f"Summarizing chat {chat_id} with {len(messages)} messages")
        
        # Check if conversation needs chunking
        if self._should_chunk_conversation(messages):
            logger.info(f"Chat {chat_id} is large, using chunked summarization")
            return self._summarize_chat_chunked(chat)
        else:
            # Use original single-pass summarization
            return self._summarize_chat_single_pass(chat)
    
    def _summarize_chat_single_pass(self, chat: Dict) -> Optional[Dict]:
        """Summarize chat using single pass (original method)."""
        # Use content_hash as chat_id, fallback to 'unknown' if not available
        chat_id = chat.get('content_hash', chat.get('chat_id', 'unknown'))
        messages = chat.get('messages', [])
        
        # Create prompt
        prompt = self._create_summary_prompt(chat)
        if not prompt:
            logger.warning(f"No content to summarize for chat {chat_id}")
            return None
        
        # Get summary from LLM
        summary = self._get_summary_from_llm(prompt)
        
        if summary:
            # Add metadata
            summary['chat_id'] = chat_id
            summary['message_count'] = len(messages)
            summary['timestamp'] = datetime.now().isoformat()
            summary['model'] = 'gemma:2b'
            summary['processing_method'] = 'single_pass'
            
            # Calculate duration if timestamps are available
            if messages:
                first_msg = messages[0]
                last_msg = messages[-1]
                if 'timestamp' in first_msg and 'timestamp' in last_msg:
                    try:
                        start_time = datetime.fromisoformat(first_msg['timestamp'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(last_msg['timestamp'].replace('Z', '+00:00'))
                        duration_minutes = (end_time - start_time).total_seconds() / 60
                        summary['duration_minutes'] = round(duration_minutes, 1)
                    except:
                        summary['duration_minutes'] = None
                else:
                    summary['duration_minutes'] = None
            
            logger.info(f"Successfully summarized chat {chat_id}")
            return summary
        else:
            logger.warning(f"Failed to summarize chat {chat_id}")
            return None
    
    def _summarize_chat_chunked(self, chat: Dict) -> Optional[Dict]:
        """Summarize chat using chunked approach for large conversations."""
        # Use content_hash as chat_id, fallback to 'unknown' if not available
        chat_id = chat.get('content_hash', chat.get('chat_id', 'unknown'))
        messages = chat.get('messages', [])
        
        # Create chunks
        chunks = self._create_chunks(messages)
        logger.info(f"Split chat {chat_id} into {len(chunks)} chunks")
        
        # Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Summarizing chunk {i+1}/{len(chunks)} for chat {chat_id}")
            chunk_summary = self._summarize_chunk(chunk, i, len(chunks))
            if chunk_summary:
                chunk_summary['chunk_index'] = i
                chunk_summary['total_chunks'] = len(chunks)
                chunk_summaries.append(chunk_summary)
        
        if not chunk_summaries:
            logger.warning(f"No valid chunk summaries for chat {chat_id}")
            return None
        
        # Create comprehensive summary from chunk summaries
        logger.info(f"Creating comprehensive summary from {len(chunk_summaries)} chunks")
        comprehensive_prompt = self._create_comprehensive_summary_prompt(chunk_summaries)
        comprehensive_summary = self._get_summary_from_llm(comprehensive_prompt)
        
        if comprehensive_summary:
            # Add metadata
            comprehensive_summary['chat_id'] = chat_id
            comprehensive_summary['message_count'] = len(messages)
            comprehensive_summary['timestamp'] = datetime.now().isoformat()
            comprehensive_summary['model'] = 'gemma:2b'
            
            # Determine processing method based on whether hierarchical was used
            total_chars = sum(len(summary.get('summary', '')) for summary in chunk_summaries)
            if total_chars > 20000:
                comprehensive_summary['processing_method'] = 'hierarchical_chunked'
                logger.info(f"Used hierarchical summarization for large chat {chat_id}")
            else:
                comprehensive_summary['processing_method'] = 'chunked'
            
            comprehensive_summary['chunk_count'] = len(chunks)
            comprehensive_summary['chunk_summaries'] = chunk_summaries  # Include for detailed analysis
            
            # Calculate duration if timestamps are available
            if messages:
                first_msg = messages[0]
                last_msg = messages[-1]
                if 'timestamp' in first_msg and 'timestamp' in last_msg:
                    try:
                        start_time = datetime.fromisoformat(first_msg['timestamp'].replace('Z', '+00:00'))
                        end_time = datetime.fromisoformat(last_msg['timestamp'].replace('Z', '+00:00'))
                        duration_minutes = (end_time - start_time).total_seconds() / 60
                        comprehensive_summary['duration_minutes'] = round(duration_minutes, 1)
                    except:
                        comprehensive_summary['duration_minutes'] = None
                else:
                    comprehensive_summary['duration_minutes'] = None
            
            logger.info(f"Successfully summarized large chat {chat_id} using chunked approach")
            return comprehensive_summary
        else:
            logger.warning(f"Failed to create comprehensive summary for chat {chat_id}")
            return None
    
    def process_chats_to_summaries(self, force_reprocess: bool = False) -> Dict:
        """Process chats into summaries."""
        logger.info("🚀 Starting chat summarization...")
        
        # Load existing summaries
        summaries_file = self.output_dir / "chat_summaries.json"
        existing_summaries = self._load_existing_summaries(summaries_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_chat_hashes()
            logger.info(f"Found {len(processed_hashes)} existing processed hashes")
        
        # Load chats
        chats = self._load_chats()
        
        if not chats:
            logger.warning("No chats found")
            return {'status': 'no_chats'}
        
        # Process each chat
        new_summaries = {}
        processed_chat_hashes = set()
        
        # Track statistics
        total_chats = len(chats)
        successful_summaries = 0
        failed_summaries = 0
        skipped_chats = 0
        
        for i, chat in enumerate(chats, 1):
            # Use content_hash as chat_id, fallback to 'unknown' if not available
            chat_id = chat.get('content_hash', chat.get('chat_id', 'unknown'))
            messages = chat.get('messages', [])
            
            # Generate chat hash
            chat_hash = self._generate_chat_hash(chat_id, messages)
            
            # Check if already processed
            if chat_hash not in processed_hashes or force_reprocess:
                logger.info(f"Processing chat {i}/{total_chats}: {chat_id} with {len(messages)} messages")
                summary = self._summarize_chat(chat)
                if summary:
                    new_summaries[chat_id] = summary
                    processed_chat_hashes.add(chat_hash)  # Only save hash if summary was successful
                    successful_summaries += 1
                    logger.info(f"✅ Successfully summarized chat {chat_id}")
                else:
                    failed_summaries += 1
                    logger.warning(f"❌ Failed to summarize chat {chat_id}, will retry on next run")
            else:
                skipped_chats += 1
                logger.debug(f"⏭️ Chat {chat_id} already processed, skipping")
        
        # Log summary statistics
        logger.info(f"📊 Processing Summary:")
        logger.info(f"  Total chats: {total_chats}")
        logger.info(f"  Successful: {successful_summaries}")
        logger.info(f"  Failed: {failed_summaries}")
        logger.info(f"  Skipped: {skipped_chats}")
        if total_chats > 0:
            success_rate = (successful_summaries / total_chats) * 100
            logger.info(f"  Success rate: {success_rate:.1f}%")
        
        if not new_summaries and not force_reprocess:
            logger.info("No new chats to process")
            return {'status': 'no_new_chats'}
        
        # Combine existing and new summaries
        all_summaries = {**existing_summaries, **new_summaries}
        
        # Save summaries
        with open(summaries_file, 'w') as f:
            json.dump(all_summaries, f, indent=2)
        
        # Save hashes and metadata
        all_processed_hashes = processed_hashes.union(processed_chat_hashes)
        self._save_processed_chat_hashes(all_processed_hashes)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_chats': len(all_summaries),
            'new_summaries': len(new_summaries),
            'existing_summaries': len(existing_summaries),
            'processed_chats': len(processed_chat_hashes)
        }
        
        self._save_metadata(stats)
        
        logger.info(f"✅ Chat summarization complete: {len(new_summaries)} new summaries created")
        return stats


@click.command()
@click.option('--chats-file', 
              default='data/processed/ingestion/chats.jsonl',
              help='Input chats file')
@click.option('--force', is_flag=True, help='Force reprocess all chats')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(chats_file: str, force: bool, check_only: bool):
    """Run local chat summarization."""
    if check_only:
        logger.info("🔍 Checking setup...")
        
        # Check input files
        chats_path = Path(chats_file)
        
        if not chats_path.exists():
            logger.error(f"❌ Chats file not found: {chats_path}")
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
    summarizer = LocalChatSummarizer(chats_file)
    result = summarizer.process_chats_to_summaries(force_reprocess=force)
    
    if result.get('status') == 'success':
        logger.info("✅ Chat summarization completed successfully")
        return 0
    else:
        logger.error(f"❌ Chat summarization failed: {result.get('status')}")
        return 1


if __name__ == "__main__":
    main() 