#!/usr/bin/env python3
"""
Local Enhanced Message Tagging

Tags messages using local LLMs (Gemma/TinyLlama).
Uses modular directory structure: data/processed/tagging/
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


class LocalEnhancedMessageTagger:
    """Tags messages using local LLMs."""
    
    def __init__(self, 
                 model: str = "gemma:2b",
                 processed_dir: str = "data/processed"):
        self.model = model
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.tagging_dir = self.processed_dir / "tagging"
        self.tagging_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_message_hash(self, message: Dict) -> str:
        """Generate a hash for a message to track if it's been processed."""
        # Create a normalized version for hashing
        normalized_message = {
            'content': message.get('content', ''),
            'chat_id': message.get('chat_id', ''),
            'message_id': message.get('id', ''),
            'role': message.get('role', '')
        }
        content = json.dumps(normalized_message, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_message_hashes(self) -> Set[str]:
        """Load hashes of messages that have already been tagged."""
        hash_file = self.tagging_dir / "hashes.pkl"
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed message hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def _save_processed_message_hashes(self, hashes: Set[str]) -> None:
        """Save hashes of processed messages."""
        hash_file = self.tagging_dir / "hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed message hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _load_existing_tagged_messages(self, tagged_file: Path) -> List[Dict]:
        """Load existing tagged messages from file."""
        messages = []
        if tagged_file.exists():
            with jsonlines.open(tagged_file) as reader:
                for message in reader:
                    messages.append(message)
            logger.info(f"Loaded {len(messages)} existing tagged messages")
        return messages
    
    def _load_messages_from_chats(self, chats_file: Path) -> List[Dict]:
        """Load individual messages from chats JSONL file."""
        messages = []
        with jsonlines.open(chats_file) as reader:
            for chat in reader:
                chat_id = chat.get('content_hash', 'unknown')
                # Extract individual messages from each chat
                for message in chat.get('messages', []):
                    # Only process user and assistant messages with content
                    if message.get('role') in ['user', 'assistant'] and message.get('content', '').strip():
                        # Add chat context to message
                        message_with_context = {
                            **message,
                            'chat_id': chat_id,
                            'chat_title': chat.get('title', 'Untitled'),
                            'message_id': f"{chat_id}_{message.get('id', 'unknown')}"
                        }
                        messages.append(message_with_context)
        
        logger.info(f"Loaded {len(messages)} messages from {chats_file}")
        return messages
    
    def _identify_new_messages(self, all_messages: List[Dict], processed_hashes: Set[str]) -> List[Dict]:
        """Identify messages that haven't been tagged yet."""
        new_messages = []
        for message in all_messages:
            message_hash = self._generate_message_hash(message)
            if message_hash not in processed_hashes:
                new_messages.append(message)
        
        logger.info(f"Found {len(new_messages)} new messages out of {len(all_messages)} total")
        return new_messages
    
    def _generate_tagging_prompt(self, message: Dict) -> str:
        """Generate a prompt for tagging a message."""
        content = message.get('content', '').strip()
        role = message.get('role', '')
        
        if not content:
            return ""
        
        # Create the prompt
        prompt = f"""You are an AI assistant that tags conversation messages with relevant topics and categories.

Message (Role: {role}):
{content}

Please provide a JSON response with the following structure:
{{
    "tags": ["tag1", "tag2", "tag3"],
    "topics": ["topic1", "topic2"],
    "domain": "technology|health|business|personal|education|entertainment|other",
    "complexity": "low|medium|high",
    "sentiment": "positive|negative|neutral",
    "intent": "question|statement|request|explanation|other"
}}

Guidelines:
- tags: 3-5 specific hashtag-style tags (e.g., "#python", "#cooking", "#health")
- topics: 2-3 broader topics or themes
- domain: primary category of the content
- complexity: technical or conceptual difficulty level
- sentiment: emotional tone of the message
- intent: what the speaker is trying to accomplish

Focus on the most relevant tags and topics. Keep tags specific and actionable."""

        return prompt
    
    def _call_ollama(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call Ollama API to generate tags."""
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
                        "num_predict": 300
                    }
                }
                
                # Call Ollama
                result = subprocess.run(
                    ["ollama", "generate", "--json"],
                    input=json.dumps(request_data),
                    capture_output=True,
                    text=True,
                    timeout=60
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
    
    def _tag_message(self, message: Dict) -> Optional[Dict]:
        """Tag a single message."""
        prompt = self._generate_tagging_prompt(message)
        
        if not prompt:
            logger.warning(f"Empty prompt for message {message.get('message_id', 'unknown')}")
            return None
        
        response = self._call_ollama(prompt)
        
        if not response:
            logger.warning(f"No response for message {message.get('message_id', 'unknown')}")
            return None
        
        tag_data = self._extract_json_from_response(response)
        
        if tag_data:
            # Create minimal tag entry with only hashes and tags
            message_hash = self._generate_message_hash(message)
            tag_entry = {
                'message_hash': message_hash,
                'message_id': message.get('message_id', ''),
                'chat_id': message.get('chat_id', ''),
                'tags': tag_data.get('tags', []),
                'topics': tag_data.get('topics', []),
                'domain': tag_data.get('domain', 'other'),
                'complexity': tag_data.get('complexity', 'medium'),
                'sentiment': tag_data.get('sentiment', 'neutral'),
                'intent': tag_data.get('intent', 'other'),
                'tagged_at': datetime.now().isoformat()
            }
            return tag_entry
        else:
            logger.warning(f"Failed to extract tags for message {message.get('message_id', 'unknown')}")
            return None
    
    def _save_tagged_messages(self, tagged_messages: List[Dict]) -> None:
        """Save tagged messages to file."""
        tagged_messages_file = self.tagging_dir / "tags.jsonl"
        with jsonlines.open(tagged_messages_file, mode='w') as writer:
            for tag_entry in tagged_messages:
                writer.write(tag_entry)
        
        logger.info(f"Saved {len(tagged_messages)} tag entries to {tagged_messages_file}")
    
    def process_messages_to_tags(self, chats_file: Path, force_reprocess: bool = False) -> Dict:
        """Process messages into tag entries."""
        logger.info("🚀 Starting message tagging...")
        
        # Load existing tag entries
        tags_file = self.tagging_dir / "tags.jsonl"
        existing_tags = self._load_existing_tagged_messages(tags_file)
        
        # Load processed hashes
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_message_hashes()
            logger.info(f"Found {len(processed_hashes)} existing processed hashes")
        
        # Load messages from chats
        all_messages = self._load_messages_from_chats(chats_file)
        if not all_messages:
            logger.warning("No messages found")
            return {'status': 'no_messages'}
        
        # Identify new messages
        new_messages = self._identify_new_messages(all_messages, processed_hashes)
        
        if not new_messages and not force_reprocess:
            logger.info("No new messages to process")
            return {'status': 'no_new_messages'}
        
        # Tag new messages
        new_tag_entries = []
        for message in tqdm(new_messages, desc="Tagging messages"):
            tag_entry = self._tag_message(message)
            if tag_entry:
                new_tag_entries.append(tag_entry)
                message_hash = self._generate_message_hash(message)
                processed_hashes.add(message_hash)
        
        if not new_tag_entries and not force_reprocess:
            logger.info("No new tag entries generated")
            return {'status': 'no_tagged_messages'}
        
        # Combine existing and new tag entries
        all_tag_entries = existing_tags + new_tag_entries
        
        # Save tag entries
        self._save_tagged_messages(all_tag_entries)
        
        # Save hashes and metadata
        self._save_processed_message_hashes(processed_hashes)
        
        # Calculate statistics
        stats = {
            'status': 'success',
            'total_tag_entries': len(all_tag_entries),
            'new_tag_entries': len(new_tag_entries),
            'existing_tag_entries': len(existing_tags),
            'model_used': self.model
        }
        
        self._save_metadata(stats)
        
        logger.info("✅ Message tagging completed!")
        logger.info(f"  Total tag entries: {stats['total_tag_entries']}")
        logger.info(f"  New tag entries: {stats['new_tag_entries']}")
        logger.info(f"  Model used: {stats['model_used']}")
        
        return stats


@click.command()
@click.option('--input-file',
              default='data/processed/ingestion/chats.jsonl',
              help='Input JSONL file with chats')
@click.option('--output-file',
              default='data/processed/tagging/tagged_messages.jsonl',
              help='Output JSONL file for tagged messages')
@click.option('--model', default='gemma:2b', help='Ollama model to use')
@click.option('--force', is_flag=True, help='Force reprocess all messages (ignore state)')
def main(input_file: str, output_file: str, model: str, force: bool):
    """Tag messages using local LLMs."""
    
    tagger = LocalEnhancedMessageTagger(model=model)
    
    result = tagger.process_messages_to_tags(
        chats_file=Path(input_file),
        force_reprocess=force
    )
    
    if result['status'] == 'success':
        logger.info(f"✅ Tagging completed successfully!")
        logger.info(f"   Total tag entries: {result['total_tag_entries']}")
        logger.info(f"   New tag entries: {result['new_tag_entries']}")
    else:
        logger.info(f"ℹ️ Tagging status: {result['status']}")


if __name__ == "__main__":
    main() 