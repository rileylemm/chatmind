#!/usr/bin/env python3
"""
ChatGPT URL Mapper

Maps conversation IDs to ChatGPT URLs for direct linking back to original conversations.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass, asdict
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChatGPTURL:
    """Represents a ChatGPT conversation URL mapping."""
    conversation_id: str
    chat_id: str
    url: str
    title: str
    create_time: Optional[int]
    source_file: str


class ChatGPTURLMapper:
    """Maps conversation IDs to ChatGPT URLs and manages URL storage."""
    
    def __init__(self, data_lake_dir: str = "data/lake"):
        self.data_lake_dir = Path(data_lake_dir)
        self.urls_dir = self.data_lake_dir / "urls"
        self.urls_dir.mkdir(parents=True, exist_ok=True)
        
        # ChatGPT URL patterns
        self.url_patterns = [
            r"https://chat\.openai\.com/c/([a-zA-Z0-9-]+)",
            r"https://chat\.openai\.com/share/([a-zA-Z0-9-]+)",
            r"https://chat\.openai\.com/chat/([a-zA-Z0-9-]+)"
        ]
    
    def extract_conversation_id_from_url(self, url: str) -> Optional[str]:
        """Extract conversation ID from ChatGPT URL."""
        for pattern in self.url_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def generate_chatgpt_url(self, conversation_id: str) -> str:
        """Generate ChatGPT URL from conversation ID."""
        return f"https://chat.openai.com/c/{conversation_id}"
    
    def extract_conversation_ids_from_chat(self, chat_data: Dict) -> List[str]:
        """Extract conversation IDs from chat content (messages)."""
        conversation_ids = set()
        
        # Look for URLs in message content
        for message in chat_data.get('messages', []):
            content = message.get('content', '')
            
            # Extract URLs from content
            urls = re.findall(r'https://chat\.openai\.com/[^\s]+', content)
            for url in urls:
                conv_id = self.extract_conversation_id_from_url(url)
                if conv_id:
                    conversation_ids.add(conv_id)
        
        return list(conversation_ids)
    
    def store_url_mapping(self, chat_id: str, conversation_id: str, chat_data: Dict) -> ChatGPTURL:
        """Store a URL mapping for a chat."""
        url = self.generate_chatgpt_url(conversation_id)
        
        url_mapping = ChatGPTURL(
            conversation_id=conversation_id,
            chat_id=chat_id,
            url=url,
            title=chat_data.get('title', 'Untitled'),
            create_time=chat_data.get('create_time'),
            source_file=chat_data.get('source_file', '')
        )
        
        # Store mapping
        mapping_file = self.urls_dir / f"{conversation_id}.json"
        with open(mapping_file, 'w') as f:
            json.dump(asdict(url_mapping), f, indent=2, default=str)
        
        logger.info(f"Stored URL mapping: {conversation_id} -> {chat_id}")
        return url_mapping
    
    def get_url_mapping(self, conversation_id: str) -> Optional[ChatGPTURL]:
        """Get URL mapping by conversation ID."""
        mapping_file = self.urls_dir / f"{conversation_id}.json"
        if not mapping_file.exists():
            return None
        
        with open(mapping_file, 'r') as f:
            data = json.load(f)
        
        return ChatGPTURL(**data)
    
    def get_chat_urls(self, chat_id: str) -> List[ChatGPTURL]:
        """Get all URL mappings for a specific chat."""
        urls = []
        
        for mapping_file in self.urls_dir.glob("*.json"):
            with open(mapping_file, 'r') as f:
                data = json.load(f)
            
            if data.get('chat_id') == chat_id:
                urls.append(ChatGPTURL(**data))
        
        return urls
    
    def search_urls_by_title(self, query: str) -> List[ChatGPTURL]:
        """Search URL mappings by chat title."""
        matching_urls = []
        
        for mapping_file in self.urls_dir.glob("*.json"):
            with open(mapping_file, 'r') as f:
                data = json.load(f)
            
            if query.lower() in data.get('title', '').lower():
                matching_urls.append(ChatGPTURL(**data))
        
        return matching_urls
    
    def get_all_urls(self) -> List[ChatGPTURL]:
        """Get all URL mappings."""
        urls = []
        
        for mapping_file in self.urls_dir.glob("*.json"):
            with open(mapping_file, 'r') as f:
                data = json.load(f)
            
            urls.append(ChatGPTURL(**data))
        
        return urls
    
    def get_stats(self) -> Dict:
        """Get URL mapping statistics."""
        url_count = len(list(self.urls_dir.glob("*.json")))
        
        return {
            "total_url_mappings": url_count,
            "urls_directory": str(self.urls_dir)
        }


class URLMappingExtractor:
    """Extends the data lake extractor to also extract and store URL mappings."""
    
    def __init__(self, url_mapper: ChatGPTURLMapper):
        self.url_mapper = url_mapper
        self.processed_chat_ids = set()
    
    def process_chat_for_urls(self, chat_data: Dict, chat_id: str) -> List[ChatGPTURL]:
        """Process a chat to extract and store URL mappings."""
        conversation_ids = self.url_mapper.extract_conversation_ids_from_chat(chat_data)
        url_mappings = []
        
        for conv_id in conversation_ids:
            # Check if we already processed this conversation
            if conv_id not in self.processed_chat_ids:
                url_mapping = self.url_mapper.store_url_mapping(chat_id, conv_id, chat_data)
                url_mappings.append(url_mapping)
                self.processed_chat_ids.add(conv_id)
        
        return url_mappings


@click.command()
@click.option('--data-lake-dir', default='data/lake', help='Data lake directory')
@click.option('--processed-dir', default='data/processed', help='Processed data directory')
@click.option('--extract-urls', is_flag=True, help='Extract URLs from existing data')
def main(data_lake_dir: str, processed_dir: str, extract_urls: bool):
    """Process existing data to extract ChatGPT URL mappings."""
    
    url_mapper = ChatGPTURLMapper(data_lake_dir)
    
    if extract_urls:
        logger.info("Extracting URLs from existing data...")
        
        # Process existing JSONL data
        processed_file = Path(processed_dir) / "chats.jsonl"
        if processed_file.exists():
            import jsonlines
            
            extractor = URLMappingExtractor(url_mapper)
            total_urls = 0
            
            with jsonlines.open(processed_file) as reader:
                for chat_data in reader:
                    # Generate chat_id (same logic as data lake)
                    import hashlib
                    content_hash = hashlib.sha256(
                        json.dumps(chat_data, sort_keys=True).encode()
                    ).hexdigest()
                    chat_id = f"chat_{content_hash[:16]}"
                    
                    # Extract URLs
                    url_mappings = extractor.process_chat_for_urls(chat_data, chat_id)
                    total_urls += len(url_mappings)
            
            logger.info(f"Extracted {total_urls} URL mappings")
    
    # Print stats
    stats = url_mapper.get_stats()
    logger.info(f"URL mapping stats: {stats}")


if __name__ == "__main__":
    main() 