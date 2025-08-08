#!/usr/bin/env python3
"""
ChatGPT Export Extractor and Flattener

Extracts chat data from ChatGPT export ZIP files, deduplicates content,
and flattens into a standardized JSONL format for processing.
Uses modular directory structure: data/processed/ingestion/
"""

import json
import zipfile
import hashlib
import jsonlines
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
import click
from tqdm import tqdm
import logging
import pickle
import re
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import data lake storage
try:
    from .data_lake_storage import DataLakeStorage, DataLakeExtractor
    from .chatgpt_url_mapper import ChatGPTURLMapper, URLMappingExtractor
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from data_lake_storage import DataLakeStorage, DataLakeExtractor
    from chatgpt_url_mapper import ChatGPTURLMapper, URLMappingExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatExtractor:
    """Extracts and processes ChatGPT export data."""
    
    def __init__(self, raw_data_dir: str = "data/raw", processed_dir: str = "data/processed", data_lake_dir: str = "data/lake"):
        self.raw_data_dir = Path(raw_data_dir)
        self.processed_dir = Path(processed_dir)
        
        # Use modular directory structure
        self.ingestion_dir = self.processed_dir / "ingestion"
        self.ingestion_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data lake storage
        self.data_lake = DataLakeStorage(data_lake_dir)
        self.data_lake_extractor = DataLakeExtractor(self.data_lake)
        
        # Initialize URL mapper
        self.url_mapper = ChatGPTURLMapper(data_lake_dir)
        self.url_extractor = URLMappingExtractor(self.url_mapper)
        
        # Load existing hashes to enable content-based deduplication
        self.seen_hashes: Set[str] = self._load_existing_hashes()
    
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
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _load_existing_hashes(self) -> Set[str]:
        """Load existing content hashes from previous runs."""
        hash_file = self.ingestion_dir / "hashes.pkl"
        if hash_file.exists():
            try:
                with open(hash_file, 'rb') as f:
                    hashes = pickle.load(f)
                logger.info(f"Loaded {len(hashes)} existing content hashes")
                return hashes
            except Exception as e:
                logger.warning(f"Failed to load existing hashes: {e}")
        return set()
    
    def _save_hashes(self):
        """Save current content hashes for future runs."""
        hash_file = self.ingestion_dir / "hashes.pkl"
        try:
            with open(hash_file, 'wb') as f:
                pickle.dump(self.seen_hashes, f)
            logger.info(f"Saved {len(self.seen_hashes)} content hashes")
        except Exception as e:
            logger.error(f"Failed to save hashes: {e}")
    
    def _save_metadata(self, stats: Dict):
        """Save processing metadata."""
        metadata_file = self.ingestion_dir / "metadata.json"
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'step': 'ingestion',
            'stats': stats,
            'files_processed': list(self.seen_hashes),
            'version': '1.0'
        }
        try:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {metadata_file}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    

    
    def extract_zip_file(self, zip_path: Path) -> List[Dict]:
        """Extract chat data from a ChatGPT export ZIP file."""
        chats = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Look for conversation files
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('.json'):
                        with zip_ref.open(file_info.filename) as f:
                            try:
                                data = json.load(f)
                                
                                # Handle ChatGPT export format where conversations.json contains an array
                                if isinstance(data, list):
                                    # This is the conversations.json file with an array of conversations
                                    for conversation in data:
                                        if self._is_valid_chat(conversation):
                                            chats.append(self._normalize_chat(conversation))
                                elif self._is_valid_chat(data):
                                    # This is a single conversation file
                                    chats.append(self._normalize_chat(data))
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"Invalid JSON in {file_info.filename}")
                                continue
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {zip_path}")
            return []
            
        return chats
    
    def _is_valid_chat(self, data: Dict) -> bool:
        """Check if the data represents a valid chat conversation."""
        return (
            isinstance(data, dict) and
            'title' in data and
            'mapping' in data and
            isinstance(data['mapping'], dict)
        )
    
    def _normalize_chat(self, chat_data: Dict) -> Dict:
        """Normalize chat data into a standard format."""
        messages = []
        
        # Extract messages from the mapping
        for node_id, node_data in chat_data['mapping'].items():
            if 'message' in node_data and node_data['message']:
                message = node_data['message']
                if 'content' in message and 'parts' in message['content']:
                    # Extract text content
                    text_parts = []
                    for part in message['content']['parts']:
                        if isinstance(part, dict) and 'text' in part:
                            text_parts.append(part['text'])
                        elif isinstance(part, str):
                            text_parts.append(part)
                    if text_parts:
                        combined_text = ' '.join(text_parts)
                        # For chats.jsonl: fully sanitize
                        sanitized_text = self._sanitize_text(combined_text)
                        if sanitized_text:  # Only add message if sanitized text is not empty
                            messages.append({
                                'id': node_id,
                                'role': message.get('author', {}).get('role', 'unknown'),
                                'content': sanitized_text,  # Only sanitized content in chats.jsonl
                                'timestamp': message.get('create_time'),
                                'parent_id': message.get('parent_id'),
                                '_original_content': combined_text  # Keep for data lake, will not be written to chats.jsonl
                            })
        return {
            'title': chat_data.get('title', 'Untitled'),
            'create_time': chat_data.get('create_time'),
            'update_time': chat_data.get('update_time'),
            'current_node': chat_data.get('current_node'),
            'messages': messages,
            'source_file': str(chat_data.get('source_file', ''))
        }
    
    def _generate_content_hash(self, chat: Dict) -> str:
        """Generate a SHA256 hash of the chat content for deduplication."""
        # Create a normalized version for hashing (exclude timestamps that might change)
        normalized_chat = {
            'title': chat['title'],
            'messages': sorted(chat['messages'], key=lambda x: x['content'])
        }
        content = json.dumps(normalized_chat, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def process_all_exports(self, force_reprocess: bool = False) -> str:
        """Process all ZIP files in the raw data directory with content-based deduplication."""
        zip_files = list(self.raw_data_dir.glob("*.zip"))
        
        if not zip_files:
            logger.warning(f"No ZIP files found in {self.raw_data_dir}")
            return ""
        
        all_chats = []
        total_processed = 0
        total_new = 0
        total_duplicates = 0
        
        for zip_file in tqdm(zip_files, desc="Processing ZIP files"):
            logger.info(f"Processing {zip_file.name}")
            chats = self.extract_zip_file(zip_file)
            
            file_new_chats = 0
            file_duplicates = 0
            
            for chat in chats:
                content_hash = self._generate_content_hash(chat)
                
                if content_hash not in self.seen_hashes:
                    self.seen_hashes.add(content_hash)
                    chat['content_hash'] = content_hash
                    all_chats.append(chat)
                    total_new += 1
                    file_new_chats += 1
                else:
                    total_duplicates += 1
                    file_duplicates += 1
                    logger.debug(f"Duplicate chat found: {chat['title']}")
            
            logger.info(f"File {zip_file.name}: {file_new_chats} new, {file_duplicates} duplicates")
        
        # Save to JSONL (append mode for incremental processing)
        output_file = self.ingestion_dir / "chats.jsonl"
        
        if all_chats:  # Only write if we have new chats
            with jsonlines.open(output_file, mode='a') as writer:
                for chat in all_chats:
                    # Remove _original_content before writing to chats.jsonl
                    for msg in chat['messages']:
                        if '_original_content' in msg:
                            del msg['_original_content']
                    writer.write(chat)
            # Store in data lake
            # For data lake, use original content (lightly cleaned)
            for chat in all_chats:
                for msg in chat['messages']:
                    if '_original_content' in msg:
                        # Minimal cleaning: normalize whitespace
                        msg['content'] = ' '.join(msg['_original_content'].split())
                        del msg['_original_content']
            chat_ids = self.data_lake_extractor.process_chats(all_chats)
            logger.info(f"Stored {len(chat_ids)} chats in data lake")
            
            # Extract and store URL mappings
            total_urls = 0
            for chat_data in all_chats:
                # Generate chat_id for URL mapping
                content_hash = self._generate_content_hash(chat_data)
                chat_id = f"chat_{content_hash[:16]}"
                
                # Extract URLs from this chat
                url_mappings = self.url_extractor.process_chat_for_urls(chat_data, chat_id)
                total_urls += len(url_mappings)
            
            logger.info(f"Extracted {total_urls} ChatGPT URL mappings")
            
            # Save state for next run
            self._save_hashes()
            self._save_metadata({"total_chats": total_new, "total_messages": total_new, "unique_hashes": len(self.seen_hashes)})
        
        logger.info(f"Processing summary:")
        logger.info(f"  - New chats: {total_new}")
        logger.info(f"  - Duplicate chats: {total_duplicates}")
        logger.info(f"  - Total unique chats: {len(self.seen_hashes)}")
        
        return str(output_file)
    
    def get_stats(self) -> Dict:
        """Get processing statistics."""
        output_file = self.ingestion_dir / "chats.jsonl"
        if not output_file.exists():
            return {"total_chats": 0, "total_messages": 0}
        
        total_chats = 0
        total_messages = 0
        
        with jsonlines.open(output_file) as reader:
            for chat in reader:
                total_chats += 1
                total_messages += len(chat.get('messages', []))
        
        return {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "unique_hashes": len(self.seen_hashes)
        }
    
    def clear_processed_state(self):
        """Clear all processed state (for fresh start)."""
        hash_file = self.ingestion_dir / "hashes.pkl"
        
        if hash_file.exists():
            hash_file.unlink()
        
        self.seen_hashes.clear()
        
        logger.info("Cleared all processed state")


@click.command()
@click.option('--raw-dir', default='data/raw', help='Directory containing ZIP files')
@click.option('--processed-dir', default='data/processed', help='Output directory for processed data')
@click.option('--force', is_flag=True, help='Force reprocess all files (ignore previous state)')
@click.option('--clear-state', is_flag=True, help='Clear all processed state and start fresh')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def main(raw_dir: str, processed_dir: str, force: bool, clear_state: bool, verbose: bool):
    """Extract and flatten ChatGPT exports."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    extractor = ChatExtractor(raw_dir, processed_dir)
    
    if clear_state:
        extractor.clear_processed_state()
        logger.info("Cleared processed state")
    
    output_file = extractor.process_all_exports(force_reprocess=force)
    
    if output_file:
        stats = extractor.get_stats()
        logger.info(f"Processing complete!")
        logger.info(f"Stats: {stats}")
    else:
        logger.error("No data processed. Check your raw data directory.")


if __name__ == "__main__":
    main() 