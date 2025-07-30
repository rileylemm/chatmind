#!/usr/bin/env python3
"""
Enhanced Message Tagger for ChatMind (Cloud API Version)

Tags messages using OpenAI API with conversation-level context.
Updated for message-level tagging in the new pipeline structure.
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
import jsonlines
import hashlib
import pickle
from datetime import datetime
import click
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedMessageTagger:
    """Enhanced message tagger with conversation-level context."""
    
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
    
    def _generate_message_hash(self, message: Dict) -> str:
        """Generate a hash for a message to track if it's been processed."""
        normalized_message = {
            'content': message.get('content', ''),
            'chat_id': message.get('chat_id', ''),
            'message_id': message.get('id', ''),
            'role': message.get('role', '')
        }
        content = json.dumps(normalized_message, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _load_processed_message_hashes(self, hash_file: Path) -> set:
        """Load hashes of messages that have already been tagged."""
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} processed message hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load processed hashes: {e}")
        return set()
    
    def _save_processed_message_hashes(self, hashes: set, hash_file: Path) -> None:
        """Save hashes of processed messages."""
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(hashes, f)
            logger.info(f"Saved {len(hashes)} processed message hashes")
        except Exception as e:
            logger.error(f"Failed to save processed hashes: {e}")
    
    def _save_metadata(self, stats: Dict, metadata_file: Path) -> None:
        """Save processing metadata."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'tagging',
            'method': 'cloud_api',
            'stats': stats,
            'version': '1.0'
        }
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def analyze_conversation(self, messages: List[Dict]) -> Dict:
        """
        Analyze conversation at the conversation level to understand context.
        
        Args:
            messages: List of messages from the same conversation
        
        Returns:
            Conversation analysis with domain and key topics
        """
        if not self.enable_conversation_context or not messages:
            return {}
        
        # Create a representative sample of the conversation
        total_content = ""
        for message in messages[:10]:  # Sample first 10 messages
            content = message.get('content', '')
            total_content += content[:500] + "\n"  # Limit each message
        
        if len(total_content) > 4000:  # Truncate if too long
            total_content = total_content[:4000]
        
        try:
            prompt = f"""
            Analyze this conversation and provide context in JSON format:
            
            {total_content}
            
            Return: {{
                "primary_domain": "technical|personal|medical|business|creative",
                "key_topics": ["topic1", "topic2"],
                "conversation_type": "discussion|question|tutorial|casual"
            }}
            """
            
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
    
    def _get_tags_from_gpt(self, text: str, conversation_context: str = "") -> Dict:
        """Get tags from GPT for a single message."""
        sanitized_text = self._sanitize_text(text)
        sanitized_context = self._sanitize_text(conversation_context)
        if not sanitized_text:
            return self._get_enhanced_fallback_tags()
        
        prompt = f"""
        Analyze this message and provide tags in JSON format:
        
        Message: {sanitized_text}
        
        Context: {sanitized_context}
        
        Return: {{
            "tags": ["#tag1", "#tag2", "#tag3"],
            "domain": "technical|personal|medical|business|creative",
            "complexity": "beginner|intermediate|advanced",
            "confidence": 0.85
        }}
        
        Guidelines:
        - Use descriptive tags starting with #
        - Choose appropriate domain
        - Assess complexity level
        - Provide confidence score (0-1)
        """
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert content tagger."},
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
                
                # Validate result
                if self._validate_enhanced_result(result):
                    return result
                else:
                    logger.warning(f"Invalid result on attempt {attempt + 1}, retrying...")
                    
            except Exception as e:
                logger.warning(f"API call failed on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
        
        # Return fallback if all attempts failed
        logger.error(f"All attempts failed for message, using fallback")
        return self._get_enhanced_fallback_tags()
    
    def _validate_enhanced_result(self, result: Dict) -> bool:
        """Validate the enhanced tagging result."""
        required_fields = ['tags', 'domain', 'complexity', 'confidence']
        
        for field in required_fields:
            if field not in result:
                return False
        
        # Validate tags
        tags = result.get('tags', [])
        if not isinstance(tags, list):
            return False
        
        # Validate domain
        valid_domains = ['technical', 'personal', 'medical', 'business', 'creative']
        if result.get('domain') not in valid_domains:
            return False
        
        # Validate complexity
        valid_complexities = ['beginner', 'intermediate', 'advanced']
        if result.get('complexity') not in valid_complexities:
            return False
        
        # Validate confidence
        confidence = result.get('confidence', 0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            return False
        
        return True
    
    def _get_enhanced_fallback_tags(self) -> Dict:
        """Get fallback tags when API calls fail."""
        return {
            'tags': ['#untagged'],
            'domain': 'unknown',
            'complexity': 'unknown',
            'confidence': 0.0
        }
    
    def tag_message(self, message: Dict, conversation_context: Dict = None) -> Dict:
        """Tag a single message."""
        content = message.get('content', '')
        if not content.strip():
            return {
                **message,
                'tags': ['#empty'],
                'domain': 'unknown',
                'complexity': 'unknown',
                'confidence': 0.0
            }
        
        # Get conversation context string
        context_str = ""
        if conversation_context:
            context_str = f"Domain: {conversation_context.get('primary_domain', 'unknown')}, Topics: {', '.join(conversation_context.get('key_topics', []))}"
        
        # Get tags from GPT
        tagging_result = self._get_tags_from_gpt(content, context_str)
        
        # Create tagged message
        tagged_message = {
            **message,
            'tags': tagging_result.get('tags', []),
            'domain': tagging_result.get('domain', 'unknown'),
            'complexity': tagging_result.get('complexity', 'unknown'),
            'confidence': tagging_result.get('confidence', 0.0),
            'tagging_model': self.model,
            'tagging_timestamp': int(time.time())
        }
        
        return tagged_message
    
    def process_messages_to_tags(self, chats_file: Path, output_file: Path, force_reprocess: bool = False) -> Dict:
        """Process messages from chats file to tagged messages."""
        logger.info("🚀 Starting cloud API message tagging...")
        
        # Setup output directory
        output_dir = output_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing tagged messages
        existing_messages = []
        if output_file.exists() and not force_reprocess:
            with jsonlines.open(output_file) as reader:
                for message in reader:
                    existing_messages.append(message)
            logger.info(f"Loaded {len(existing_messages)} existing tagged messages")
        
        # Load processed hashes
        hash_file = output_dir / "hashes.pkl"
        processed_hashes = set()
        if not force_reprocess:
            processed_hashes = self._load_processed_message_hashes(hash_file)
        
        # Extract messages from chats
        messages = []
        with jsonlines.open(chats_file) as reader:
            for chat in reader:
                chat_id = chat.get('content_hash', 'unknown')
                for message in chat.get('messages', []):
                    # Only process user and assistant messages with content
                    content = message.get('content', '')
                    if message.get('role') in ['user', 'assistant'] and content.strip():
                        # Add chat context to message
                        message_with_context = {
                            **message,
                            'chat_id': chat_id,
                            'chat_title': chat.get('title', 'Untitled'),
                            'message_id': f"{chat_id}_{message.get('id', 'unknown')}"
                        }
                        messages.append(message_with_context)
        
        logger.info(f"Loaded {len(messages)} messages from chats")
        
        # Group messages by conversation
        conversation_groups = defaultdict(list)
        for message in messages:
            chat_id = message.get('chat_id', 'unknown')
            conversation_groups[chat_id].append(message)
        
        # Process conversations
        new_tagged_messages = []
        for chat_id, messages in conversation_groups.items():
            logger.info(f"Processing conversation {chat_id} with {len(messages)} messages")
            
            # Analyze conversation first
            conversation_context = self.analyze_conversation(messages)
            
            # Tag messages with conversation context
            for message in tqdm(messages, desc=f"Tagging messages in {chat_id}"):
                message_hash = self._generate_message_hash(message)
                
                # Skip if already processed
                if message_hash in processed_hashes and not force_reprocess:
                    continue
                
                try:
                    tagged_message = self.tag_message(message, conversation_context)
                    new_tagged_messages.append(tagged_message)
                    processed_hashes.add(message_hash)
                    
                    # Add delay between API calls
                    time.sleep(self.delay_between_calls)
                    
                except Exception as e:
                    logger.error(f"Failed to tag message {message.get('message_id', 'unknown')}: {e}")
                    # Add fallback tags
                    fallback_message = {
                        **message,
                        'tags': ['#error'],
                        'domain': 'unknown',
                        'complexity': 'unknown',
                        'confidence': 0.0,
                        'tagging_model': 'fallback',
                        'tagging_timestamp': int(time.time())
                    }
                    new_tagged_messages.append(fallback_message)
                    processed_hashes.add(message_hash)
        
        # Combine existing and new messages
        all_tagged_messages = existing_messages + new_tagged_messages
        
        # Save tagged messages
        with jsonlines.open(output_file, mode='w') as writer:
            for message in all_tagged_messages:
                writer.write(message)
        
        # Save hashes and metadata
        self._save_processed_message_hashes(processed_hashes, hash_file)
        
        # Calculate statistics
        all_tags = []
        domains = []
        complexities = []
        confidences = []
        
        for message in all_tagged_messages:
            tags = message.get('tags', [])
            all_tags.extend(tags)
            domains.append(message.get('domain', ''))
            complexities.append(message.get('complexity', ''))
            confidences.append(message.get('confidence', 0))
        
        stats = {
            'status': 'success',
            'total_messages': len(all_tagged_messages),
            'new_messages': len(new_tagged_messages),
            'existing_messages': len(existing_messages),
            'total_tags': len(all_tags),
            'unique_tags': len(set(all_tags)),
            'avg_tags_per_message': len(all_tags) / max(1, len(all_tagged_messages)),
            'domain_distribution': dict(Counter(domains)),
            'complexity_distribution': dict(Counter(complexities)),
            'avg_confidence': sum(confidences) / max(1, len(confidences))
        }
        
        metadata_file = output_dir / "metadata.json"
        self._save_metadata(stats, metadata_file)
        
        logger.info("✅ Cloud API message tagging completed!")
        logger.info(f"  Total messages: {stats['total_messages']}")
        logger.info(f"  New messages: {stats['new_messages']}")
        logger.info(f"  Total tags: {stats['total_tags']}")
        logger.info(f"  Unique tags: {stats['unique_tags']}")
        logger.info(f"  Avg tags per message: {stats['avg_tags_per_message']:.2f}")
        logger.info(f"  Avg confidence: {stats['avg_confidence']:.2f}")
        
        return stats


@click.command()
@click.option('--input-file',
              default='data/processed/ingestion/chats.jsonl',
              help='Input JSONL file with chats')
@click.option('--output-file',
              default='data/processed/tagging/tags.jsonl',
              help='Output JSONL file for tagged messages')
@click.option('--model', default='gpt-3.5-turbo', help='OpenAI model to use')
@click.option('--force', is_flag=True, help='Force reprocess all messages')
@click.option('--check-only', is_flag=True, help='Only check setup, don\'t process')
def main(input_file: str, output_file: str, model: str, force: bool, check_only: bool):
    """Tag messages using OpenAI API."""
    
    if check_only:
        logger.info("🔍 Checking cloud API setup...")
        
        # Check OpenAI API key
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("❌ OPENAI_API_KEY environment variable not set")
            return 1
        
        logger.info("✅ OpenAI API key is configured")
        
        # Check input file
        input_path = Path(input_file)
        if input_path.exists():
            logger.info(f"✅ Input file exists: {input_file}")
        else:
            logger.error(f"❌ Input file not found: {input_file}")
            return 1
        
        # Check output directory
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Output directory ready: {output_path.parent}")
        
        logger.info("✅ Cloud API setup looks good!")
        return 0
    
    # Initialize tagger
    tagger = EnhancedMessageTagger(model=model)
    
    # Process messages
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1
    
    stats = tagger.process_messages_to_tags(input_path, output_path, force)
    
    if stats['status'] == 'success':
        logger.info("✅ Cloud API tagging successful!")
        return 0
    else:
        logger.error(f"❌ Cloud API tagging failed: {stats.get('reason', 'unknown')}")
        return 1


if __name__ == "__main__":
    main() 