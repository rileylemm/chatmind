#!/usr/bin/env python3
"""
Data Lake Storage for ChatMind

Stores extracted chats and messages in a hierarchical data lake structure
that enables navigation from Neo4j graph → chat → message.
"""

import json
import jsonlines
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import hashlib
import logging
from dataclasses import dataclass, asdict
import click
import re
import unicodedata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in a chat."""
    id: str
    chat_id: str
    role: str
    content: str  # Original content (lightly cleaned, with emojis)
    timestamp: Optional[int]
    parent_id: Optional[str]
    cluster_id: Optional[int] = None
    embedding: Optional[List[float]] = None


@dataclass
class Chat:
    """Represents a complete chat conversation."""
    id: str
    title: str
    create_time: Optional[int]
    update_time: Optional[int]
    current_node: Optional[str]
    source_file: str
    content_hash: str
    message_count: int
    messages: List[Message]


class DataLakeStorage:
    """Manages hierarchical storage of chats and messages in a data lake."""
    
    def __init__(self, data_lake_dir: str = "data/lake"):
        self.data_lake_dir = Path(data_lake_dir)
        self.chats_dir = self.data_lake_dir / "chats"
        self.messages_dir = self.data_lake_dir / "messages"
        self.metadata_dir = self.data_lake_dir / "metadata"
        
        # Create directory structure
        self.chats_dir.mkdir(parents=True, exist_ok=True)
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def _generate_chat_id(self, chat_data: Dict) -> str:
        """Generate a unique chat ID."""
        content_hash = hashlib.sha256(
            json.dumps(chat_data, sort_keys=True).encode()
        ).hexdigest()
        return f"chat_{content_hash[:16]}"
    
    def _generate_message_id(self, chat_id: str, message_data: Dict) -> str:
        """Generate a unique message ID."""
        content = f"{chat_id}_{message_data['content']}_{message_data.get('timestamp', '')}"
        message_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"msg_{message_hash[:16]}"
    
    def store_chat(self, chat_data: Dict) -> str:
        """Store a chat and its messages in the data lake."""
        chat_id = self._generate_chat_id(chat_data)
        
        # Create chat object
        messages = []
        for msg_data in chat_data.get('messages', []):
            message_id = self._generate_message_id(chat_id, msg_data)
            original_content = msg_data.get('content', '')
            sanitized_content = self._sanitize_text(original_content)
            
            message = Message(
                id=message_id,
                chat_id=chat_id,
                role=msg_data.get('role', 'unknown'),
                content=original_content,  # Keep original with emojis
                timestamp=msg_data.get('timestamp'),
                parent_id=msg_data.get('parent_id')
            )
            messages.append(message)
        
        chat = Chat(
            id=chat_id,
            title=chat_data.get('title', 'Untitled'),
            create_time=chat_data.get('create_time'),
            update_time=chat_data.get('update_time'),
            current_node=chat_data.get('current_node'),
            source_file=chat_data.get('source_file', ''),
            content_hash=chat_data.get('content_hash', ''),
            message_count=len(messages),
            messages=messages
        )
        
        # Store chat metadata
        chat_file = self.chats_dir / f"{chat_id}.json"
        with open(chat_file, 'w') as f:
            json.dump(asdict(chat), f, indent=2, default=str)
        
        # Store individual messages
        for message in messages:
            message_file = self.messages_dir / f"{message.id}.json"
            with open(message_file, 'w') as f:
                json.dump(asdict(message), f, indent=2, default=str)
        
        logger.info(f"Stored chat {chat_id} with {len(messages)} messages")
        return chat_id
    
    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Retrieve a chat by ID."""
        chat_file = self.chats_dir / f"{chat_id}.json"
        if not chat_file.exists():
            return None
        
        with open(chat_file, 'r') as f:
            chat_data = json.load(f)
        
        # Reconstruct messages
        messages = []
        for msg_data in chat_data['messages']:
            message = Message(**msg_data)
            messages.append(message)
        
        chat = Chat(
            id=chat_data['id'],
            title=chat_data['title'],
            create_time=chat_data['create_time'],
            update_time=chat_data['update_time'],
            current_node=chat_data['current_node'],
            source_file=chat_data['source_file'],
            content_hash=chat_data['content_hash'],
            message_count=chat_data['message_count'],
            messages=messages
        )
        
        return chat
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Retrieve a message by ID."""
        message_file = self.messages_dir / f"{message_id}.json"
        if not message_file.exists():
            return None
        
        with open(message_file, 'r') as f:
            message_data = json.load(f)
        
        return Message(**message_data)
    
    def get_chat_messages(self, chat_id: str) -> List[Message]:
        """Get all messages for a specific chat."""
        messages = []
        for message_file in self.messages_dir.glob("*.json"):
            with open(message_file, 'r') as f:
                message_data = json.load(f)
            
            if message_data.get('chat_id') == chat_id:
                messages.append(Message(**message_data))
        
        # Sort by timestamp if available
        messages.sort(key=lambda x: x.timestamp or 0)
        return messages
    
    def search_chats(self, query: str) -> List[str]:
        """Search chats by title or content."""
        matching_chat_ids = []
        
        for chat_file in self.chats_dir.glob("*.json"):
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)
            
            # Search in title
            if query.lower() in chat_data['title'].lower():
                matching_chat_ids.append(chat_data['id'])
                continue
            
            # Search in message content
            for message in chat_data.get('messages', []):
                if query.lower() in message.get('content', '').lower():
                    matching_chat_ids.append(chat_data['id'])
                    break
        
        return list(set(matching_chat_ids))
    
    def search_messages(self, query: str) -> List[str]:
        """Search messages by content."""
        matching_message_ids = []
        
        for message_file in self.messages_dir.glob("*.json"):
            with open(message_file, 'r') as f:
                message_data = json.load(f)
            
            if query.lower() in message_data.get('content', '').lower():
                matching_message_ids.append(message_data['id'])
        
        return matching_message_ids
    
    def get_stats(self) -> Dict:
        """Get data lake statistics."""
        chat_count = len(list(self.chats_dir.glob("*.json")))
        message_count = len(list(self.messages_dir.glob("*.json")))
        
        return {
            "total_chats": chat_count,
            "total_messages": message_count,
            "data_lake_path": str(self.data_lake_dir)
        }
    
    def create_index(self):
        """Create search indexes for faster retrieval."""
        index_file = self.metadata_dir / "chat_index.json"
        
        chat_index = {}
        for chat_file in self.chats_dir.glob("*.json"):
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)
            
            chat_index[chat_data['id']] = {
                'title': chat_data['title'],
                'message_count': chat_data['message_count'],
                'create_time': chat_data['create_time'],
                'content_hash': chat_data['content_hash']
            }
        
        with open(index_file, 'w') as f:
            json.dump(chat_index, f, indent=2)
        
        logger.info(f"Created chat index with {len(chat_index)} entries")
    
    def get_chat_index(self) -> Dict:
        """Get the chat index for quick lookups."""
        index_file = self.metadata_dir / "chat_index.json"
        if not index_file.exists():
            self.create_index()
        
        with open(index_file, 'r') as f:
            return json.load(f)


class DataLakeExtractor:
    """Extends the regular extractor to also store in data lake."""
    
    def __init__(self, data_lake: DataLakeStorage):
        self.data_lake = data_lake
        self.processed_chat_ids = set()
    
    def process_chats(self, chats: List[Dict]) -> List[str]:
        """Process chats and store them in the data lake."""
        chat_ids = []
        
        for chat_data in chats:
            # Check if already processed
            content_hash = chat_data.get('content_hash', '')
            if content_hash in self.processed_chat_ids:
                continue
            
            # Store in data lake
            chat_id = self.data_lake.store_chat(chat_data)
            chat_ids.append(chat_id)
            self.processed_chat_ids.add(content_hash)
        
        return chat_ids


@click.command()
@click.option('--data-lake-dir', default='data/lake', help='Data lake directory')
@click.option('--processed-dir', default='data/processed', help='Processed data directory')
@click.option('--create-index', is_flag=True, help='Create search indexes')
def main(data_lake_dir: str, processed_dir: str, create_index: bool):
    """Process existing JSONL data into data lake structure."""
    
    data_lake = DataLakeStorage(data_lake_dir)
    extractor = DataLakeExtractor(data_lake)
    
    # Process existing JSONL data
    processed_file = Path(processed_dir) / "chats.jsonl"
    if processed_file.exists():
        logger.info("Processing existing JSONL data into data lake...")
        
        with jsonlines.open(processed_file) as reader:
            chats = list(reader)
        
        chat_ids = extractor.process_chats(chats)
        logger.info(f"Stored {len(chat_ids)} chats in data lake")
    
    if create_index:
        data_lake.create_index()
    
    # Print stats
    stats = data_lake.get_stats()
    logger.info(f"Data lake stats: {stats}")


if __name__ == "__main__":
    main() 