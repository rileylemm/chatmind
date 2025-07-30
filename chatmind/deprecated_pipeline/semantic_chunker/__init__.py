#!/usr/bin/env python3
"""
Semantic Chunker Package for ChatMind

Provides GPT-driven semantic chunking of conversations.
"""

from .chunker import SemanticChunker, chunk_chat
from .prompts import chunking_prompt, get_chunking_prompt

__all__ = [
    'SemanticChunker',
    'chunk_chat', 
    'chunking_prompt',
    'get_chunking_prompt'
] 