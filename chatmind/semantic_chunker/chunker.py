#!/usr/bin/env python3
"""
Semantic Chunker for ChatMind

Uses GPT to intelligently split conversations into semantically coherent chunks.
"""

import openai
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import time
from tqdm import tqdm

from .prompts import chunking_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticChunker:
    """Handles semantic chunking of chat conversations using GPT."""
    
    def __init__(self, 
                 model: str = "gpt-4",
                 temperature: float = 0.3,
                 max_retries: int = 3,
                 delay_between_calls: float = 1.0):
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        
        # Initialize OpenAI client
        try:
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            openai.api_key = api_key
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            raise
    
    def chunk_chat(self, chat_data: Dict) -> List[Dict]:
        """
        Chunk a single chat conversation semantically.
        
        Args:
            chat_data: Dictionary containing chat information
                - 'title': Chat title
                - 'messages': List of message dictionaries
                - 'content_hash': Unique identifier
                - Other metadata
        
        Returns:
            List of chunk dictionaries with semantic titles and content
        """
        # Prepare chat text for GPT
        chat_text = self._prepare_chat_text(chat_data)
        
        # Get semantic chunks from GPT
        chunks = self._get_semantic_chunks(chat_text, chat_data)
        
        return chunks
    
    def _prepare_chat_text(self, chat_data: Dict) -> str:
        """Prepare chat text for GPT processing."""
        title = chat_data.get('title', 'Untitled')
        messages = chat_data.get('messages', [])
        
        # Build conversation text
        chat_text = f"Title: {title}\n\n"
        
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if content.strip():
                chat_text += f"{role.upper()}: {content}\n\n"
        
        return chat_text.strip()
    
    def _get_semantic_chunks(self, chat_text: str, chat_data: Dict) -> List[Dict]:
        """Get semantic chunks from GPT with retry logic."""
        prompt = chunking_prompt(chat_text)
        
        for attempt in range(self.max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert in semantic chunking of conversations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                )
                
                # Track the API call
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    
                    # Extract token usage from response
                    usage = response.get('usage', {})
                    input_tokens = usage.get('prompt_tokens', 0)
                    output_tokens = usage.get('completion_tokens', 0)
                    
                    track_api_call(
                        model=self.model,
                        operation='chunking',
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        success=True,
                        metadata={
                            'chat_id': chat_data.get('content_hash', 'unknown'),
                            'chunk_count': len(chat_data.get('messages', [])),
                            'attempt': attempt + 1
                        }
                    )
                except ImportError:
                    logger.debug("Cost tracker not available")
                except Exception as e:
                    logger.warning(f"Failed to track API call: {e}")
                
                # Parse response
                content = response['choices'][0]['message']['content']
                chunks = json.loads(content)
                
                # Validate and enhance chunks
                enhanced_chunks = self._enhance_chunks(chunks, chat_data)
                
                logger.info(f"Successfully chunked chat into {len(enhanced_chunks)} semantic sections")
                return enhanced_chunks
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse GPT response (attempt {attempt + 1}): {e}")
                
                # Track failed API call
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    track_api_call(
                        model=self.model,
                        operation='chunking',
                        input_tokens=len(prompt.split()),  # Rough estimate
                        output_tokens=0,
                        success=False,
                        error_message=f"JSON decode error: {e}",
                        metadata={'attempt': attempt + 1}
                    )
                except ImportError:
                    pass
                except Exception as tracking_error:
                    logger.warning(f"Failed to track failed API call: {tracking_error}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    logger.error("Failed to get valid chunks from GPT, falling back to simple chunking")
                    return self._fallback_chunking(chat_data)
                    
            except Exception as e:
                logger.error(f"Error calling GPT (attempt {attempt + 1}): {e}")
                
                # Track failed API call
                try:
                    from chatmind.cost_tracker.tracker import track_api_call
                    track_api_call(
                        model=self.model,
                        operation='chunking',
                        input_tokens=len(prompt.split()),  # Rough estimate
                        output_tokens=0,
                        success=False,
                        error_message=str(e),
                        metadata={'attempt': attempt + 1}
                    )
                except ImportError:
                    pass
                except Exception as tracking_error:
                    logger.warning(f"Failed to track failed API call: {tracking_error}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                else:
                    logger.error("Failed to get chunks from GPT, falling back to simple chunking")
                    return self._fallback_chunking(chat_data)
    
    def _enhance_chunks(self, chunks: List[Dict], chat_data: Dict) -> List[Dict]:
        """Enhance chunks with metadata and validation."""
        enhanced_chunks = []
        chat_id = chat_data.get('content_hash', 'unknown')
        
        for i, chunk in enumerate(chunks):
            # Validate required fields
            if not chunk.get('title') or not chunk.get('content'):
                logger.warning(f"Skipping invalid chunk {i} in chat {chat_id}")
                continue
            
            enhanced_chunk = {
                'chat_id': chat_id,
                'chunk_id': f"{chat_id}_semantic_{i}",
                'title': chunk['title'],
                'content': chunk['content'],
                'chunk_type': 'semantic',
                'original_title': chat_data.get('title', 'Untitled'),
                'create_time': chat_data.get('create_time'),
                'source_file': chat_data.get('source_file', ''),
                'message_count': len(chat_data.get('messages', [])),
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def _fallback_chunking(self, chat_data: Dict) -> List[Dict]:
        """Fallback to simple chunking if GPT fails."""
        chat_id = chat_data.get('content_hash', 'unknown')
        title = chat_data.get('title', 'Untitled')
        messages = chat_data.get('messages', [])
        
        # Simple chunking: one chunk per message
        chunks = []
        for i, msg in enumerate(messages):
            if msg.get('content', '').strip():
                chunk = {
                    'chat_id': chat_id,
                    'chunk_id': f"{chat_id}_fallback_{i}",
                    'title': f"{title} - Message {i+1}",
                    'content': msg['content'],
                    'chunk_type': 'fallback',
                    'original_title': title,
                    'create_time': chat_data.get('create_time'),
                    'source_file': chat_data.get('source_file', ''),
                    'message_count': len(messages),
                    'chunk_index': i,
                    'total_chunks': len(messages),
                    'role': msg.get('role', 'unknown'),
                    'timestamp': msg.get('timestamp'),
                    'parent_id': msg.get('parent_id')
                }
                chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} fallback chunks for chat {chat_id}")
        return chunks
    
    def chunk_multiple_chats(self, chats: List[Dict]) -> List[Dict]:
        """Chunk multiple chats with progress tracking."""
        all_chunks = []
        
        for chat in tqdm(chats, desc="Semantic chunking"):
            try:
                chunks = self.chunk_chat(chat)
                all_chunks.extend(chunks)
                
                # Add delay between API calls
                time.sleep(self.delay_between_calls)
                
            except Exception as e:
                logger.error(f"Failed to chunk chat {chat.get('content_hash', 'unknown')}: {e}")
                # Try fallback chunking
                fallback_chunks = self._fallback_chunking(chat)
                all_chunks.extend(fallback_chunks)
        
        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks


def chunk_chat(chat_text: str, model: str = "gpt-4") -> List[Dict]:
    """
    Convenience function for chunking a single chat.
    
    Args:
        chat_text: Raw chat text
        model: GPT model to use
    
    Returns:
        List of chunk dictionaries
    """
    chunker = SemanticChunker(model=model)
    
    # Create minimal chat data structure
    chat_data = {
        'title': 'Chat',
        'messages': [{'role': 'user', 'content': chat_text}],
        'content_hash': 'temp'
    }
    
    return chunker.chunk_chat(chat_data) 