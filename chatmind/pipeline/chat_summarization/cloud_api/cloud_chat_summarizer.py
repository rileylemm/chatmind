#!/usr/bin/env python3
"""
ChatMind Cloud API Chat Summarizer

Creates summaries for entire conversations using OpenAI API.
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
import openai
import os
import re
import unicodedata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CloudChatSummarizer:
    """Creates chat summaries using OpenAI API."""
    
    def __init__(self, chats_file: str = "data/processed/ingestion/chats.jsonl"):
        self.chats_file = Path(chats_file)
        
        # Use modular directory structure
        self.output_dir = Path("data/processed/chat_summarization")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
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
        max_chars = 200000  # Much higher limit for GPT-4o-mini (128k tokens ≈ 400k chars)
        
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
        
        prompt = f"""Analyze this entire conversation and create a comprehensive summary.

Conversation:
{conversation_text}

Please provide a JSON response with the following structure:
{{
    "summary": "A comprehensive summary of the entire conversation",
    "key_topics": ["topic1", "topic2", "topic3"],
    "participants": ["user", "assistant"],
    "conversation_type": "technical_discussion|casual_chat|problem_solving|tutorial|brainstorming|other",
    "key_decisions": ["decision1", "decision2"],
    "outcomes": "What was accomplished, resolved, or learned",
    "complexity": "beginner|intermediate|advanced",
    "domain": "technical|personal|business|academic|creative|other",
    "confidence": 0.85
}}

Focus on:
1. Main purpose and flow of the conversation
2. Key topics and themes discussed
3. Important decisions or conclusions reached
4. What was accomplished or learned
5. The overall tone and complexity
6. The domain and context of the discussion

Respond only with valid JSON."""

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
    
    def _get_summary_from_openai(self, prompt: str) -> Optional[Dict]:
        """Get summary from OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates comprehensive summaries of conversation content. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    summary = json.loads(json_str)
                    
                    # Validate required fields
                    required_fields = ['summary', 'key_topics', 'participants', 'conversation_type', 
                                    'key_decisions', 'outcomes', 'complexity', 'domain', 'confidence']
                    if all(field in summary for field in required_fields):
                        return summary
                    else:
                        logger.warning(f"Missing required fields in summary: {summary}")
                        # Try to create a fallback summary
                        return self._create_fallback_summary(summary)
                else:
                    logger.warning(f"No JSON found in response: {response_text}")
                    return self._create_fallback_summary({})
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from response: {e}")
                logger.warning(f"Response: {response_text}")
                return self._create_fallback_summary({})
        
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
        
        return None
    
    def _should_chunk_conversation(self, messages: List[Dict]) -> bool:
        """Determine if conversation should be chunked based on size."""
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        return total_chars > 200000  # Much higher limit for GPT-4o-mini (128k tokens ≈ 400k chars)
    
    def _create_chunks(self, messages: List[Dict], max_chars: int = 200000) -> List[List[Dict]]:
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
        
        return self._get_summary_from_openai(prompt)
    
    def _create_comprehensive_summary_prompt(self, chunk_summaries: List[Dict]) -> str:
        """Create prompt to combine chunk summaries into comprehensive summary."""
        summaries_text = "\n\n".join([
            f"Chunk {i+1}: {summary.get('summary', '')}"
            for i, summary in enumerate(chunk_summaries)
        ])
        
        # Check if combined summaries exceed token limit
        total_chars = len(summaries_text)
        max_chars = 80000  # Higher limit for GPT-4o-mini (128k tokens ≈ 400k chars)
        
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
        batch_size = 10  # Process 10 chunks at a time (higher for GPT-4o-mini)
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
            
            intermediate_summary = self._get_summary_from_openai(intermediate_prompt)
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
    
    def _create_fallback_summary(self, partial_summary: Dict) -> Dict:
        """Create a fallback summary when API response is incomplete."""
        fallback = {
            'summary': partial_summary.get('summary', 'Conversation summary unavailable'),
            'key_topics': partial_summary.get('key_topics', ['general']),
            'participants': partial_summary.get('participants', ['user', 'assistant']),
            'conversation_type': partial_summary.get('conversation_type', 'other'),
            'key_decisions': partial_summary.get('key_decisions', []),
            'outcomes': partial_summary.get('outcomes', 'No specific outcomes identified'),
            'complexity': partial_summary.get('complexity', 'unknown'),
            'domain': partial_summary.get('domain', 'other'),
            'confidence': partial_summary.get('confidence', 0.5)
        }
        return fallback
    
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
        
        # Get summary from OpenAI
        summary = self._get_summary_from_openai(prompt)
        
        if summary:
            # Add metadata
            summary['chat_id'] = chat_id
            summary['message_count'] = len(messages)
            summary['timestamp'] = datetime.now().isoformat()
            summary['model'] = 'gpt-4o-mini'
            summary['processing_method'] = 'single_pass'
            
            # Calculate duration if timestamps are available
            if messages:
                first_msg = messages[0]
                last_msg = messages[-1]
                if 'timestamp' in first_msg and 'timestamp' in last_msg:
                    try:
                        from datetime import datetime
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
        comprehensive_summary = self._get_summary_from_openai(comprehensive_prompt)
        
        if comprehensive_summary:
            # Add metadata
            comprehensive_summary['chat_id'] = chat_id
            comprehensive_summary['message_count'] = len(messages)
            comprehensive_summary['timestamp'] = datetime.now().isoformat()
            comprehensive_summary['model'] = 'gpt-4o-mini'
            comprehensive_summary['processing_method'] = 'chunked'
            comprehensive_summary['chunk_count'] = len(chunks)
            comprehensive_summary['chunk_summaries'] = chunk_summaries  # Include for detailed analysis
            
            # Calculate duration if timestamps are available
            if messages:
                first_msg = messages[0]
                last_msg = messages[-1]
                if 'timestamp' in first_msg and 'timestamp' in last_msg:
                    try:
                        from datetime import datetime
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
        
        for chat in chats:
            # Use content_hash as chat_id, fallback to 'unknown' if not available
            chat_id = chat.get('content_hash', chat.get('chat_id', 'unknown'))
            messages = chat.get('messages', [])
            
            # Generate chat hash
            chat_hash = self._generate_chat_hash(chat_id, messages)
            
            # Check if already processed
            if chat_hash not in processed_hashes or force_reprocess:
                summary = self._summarize_chat(chat)
                if summary:
                    new_summaries[chat_id] = summary
                    processed_chat_hashes.add(chat_hash)
            else:
                logger.info(f"Chat {chat_id} already processed, skipping")
        
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
    """Run cloud chat summarization."""
    if check_only:
        logger.info("🔍 Checking setup...")
        
        # Check input files
        chats_path = Path(chats_file)
        
        if not chats_path.exists():
            logger.error(f"❌ Chats file not found: {chats_path}")
            return 1
        
        # Check OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            logger.error("❌ OPENAI_API_KEY environment variable not set")
            return 1
        
        logger.info("✅ Setup check passed")
        return 0
    
    # Run summarization
    summarizer = CloudChatSummarizer(chats_file)
    result = summarizer.process_chats_to_summaries(force_reprocess=force)
    
    if result.get('status') == 'success':
        logger.info("✅ Chat summarization completed successfully")
        return 0
    else:
        logger.error(f"❌ Chat summarization failed: {result.get('status')}")
        return 1


if __name__ == "__main__":
    main() 