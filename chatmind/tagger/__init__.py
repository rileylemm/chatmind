#!/usr/bin/env python3
"""
Auto-Tagger Package for ChatMind

Provides GPT-driven automatic tagging of semantic chunks.
"""

from .tagger import ChunkTagger, tag_chunk
from .prompts import tagging_prompt, get_tagging_prompt

__all__ = [
    'ChunkTagger',
    'tag_chunk',
    'tagging_prompt',
    'get_tagging_prompt'
] 