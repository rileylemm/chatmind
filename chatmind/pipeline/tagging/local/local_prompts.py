#!/usr/bin/env python3
"""
Optimized Prompts for Gemma-2B Model

Clean, direct prompts designed for Gemma-2B to return valid JSON.
Uses instruction format optimized for Gemma's behavior.
"""

def get_gemma_tagging_prompt(chunk_text: str, conversation_context: str = "") -> str:
    """
    Optimized prompt for Gemma-2B model to return JSON tags.
    
    Gemma-2B is good at following instructions but needs clear constraints.
    
    Args:
        chunk_text: The chunk text to be tagged
        conversation_context: Optional context about the overall conversation
    
    Returns:
        Optimized prompt string for Gemma-2B
    """
    
    context_info = f"\nContext: {conversation_context}" if conversation_context else ""
    
    return f"""You are a content classifier. Return ONLY valid JSON with tags and category.

IMPORTANT: No explanations, no conversational text, no additional content.
IMPORTANT: Do not start with "Sure," "Here's," or similar phrases.
IMPORTANT: Return ONLY the JSON object.

Tag this text with 3-5 relevant hashtags and a category:

{context_info}
Text: {chunk_text}

Return ONLY this JSON format:
{{
  "tags": ["#specific-tag1", "#specific-tag2", "#specific-tag3"],
  "category": "Specific category name",
  "domain": "technical|personal|medical|business|creative"
}}"""


def get_gemma_conversation_prompt(conversation_text: str) -> str:
    """
    Optimized prompt for conversation-level analysis with Gemma-2B.
    
    Args:
        conversation_text: The full conversation text
    
    Returns:
        Optimized prompt string for Gemma-2B
    """
    
    return f"""You are a conversation analyzer. Return ONLY valid JSON.

IMPORTANT: No explanations, no conversational text, no additional content.
IMPORTANT: Return ONLY the JSON object.

Analyze this conversation and return JSON:

{conversation_text}

Return ONLY this JSON format:
{{
  "primary_domain": "technical|personal|medical|business|creative",
  "key_topics": ["topic1", "topic2", "topic3"],
  "conversation_type": "discussion|tutorial|planning|support",
  "complexity": "low|medium|high"
}}"""


def get_gemma_validation_prompt(chunk_text: str, proposed_tags: list, conversation_context: str = "") -> str:
    """
    Optimized prompt for tag validation with Gemma-2B.
    
    Args:
        chunk_text: The chunk text
        proposed_tags: List of proposed tags
        conversation_context: Optional context
    
    Returns:
        Optimized prompt string for Gemma-2B
    """
    
    context_info = f"\nContext: {conversation_context}" if conversation_context else ""
    tags_str = ", ".join(proposed_tags)
    
    return f"""You are a tag validator. Return ONLY valid JSON.

IMPORTANT: No explanations, no conversational text, no additional content.
IMPORTANT: Return ONLY the JSON object.

Validate these tags for this text:

{context_info}
Text: {chunk_text}
Proposed tags: {tags_str}

Return ONLY this JSON format:
{{
  "is_valid": true|false,
  "suggested_tags": ["#tag1", "#tag2", "#tag3"],
  "reasoning": "Brief explanation"
}}""" 