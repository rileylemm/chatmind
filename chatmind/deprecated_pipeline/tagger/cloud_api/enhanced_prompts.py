#!/usr/bin/env python3
"""
Enhanced Prompt Templates for Auto-Tagging

Improved prompts with better examples, validation, and domain awareness.
"""

def enhanced_tagging_prompt(chunk_text: str, conversation_context: str = "") -> str:
    """
    Enhanced prompt with examples, validation, and context awareness.
    
    Args:
        chunk_text: The chunk text to be tagged
        conversation_context: Optional context about the overall conversation
    
    Returns:
        Enhanced prompt string for GPT
    """
    
    context_info = f"\nCONVERSATION CONTEXT: {conversation_context}" if conversation_context else ""
    
    return f"""
You are an expert content classifier that analyzes text and assigns relevant, accurate tags and categories.

TASK:
Analyze the following text and:
1. Generate 3-5 specific, relevant hashtags
2. Assign a concise, descriptive category
3. Ensure tags accurately reflect the content domain and topic

CRITICAL VALIDATION RULES:
- Tags MUST match the actual content domain (technical, personal, medical, etc.)
- Do NOT apply medical tags to non-medical content
- Do NOT apply technical tags to non-technical content
- Tags should be specific and meaningful, not generic
- Avoid systematic bias - don't apply the same tags repeatedly without justification

EXAMPLES OF CORRECT TAGGING:

✅ WEB DEVELOPMENT CONTENT:
Text: "Let's build a React portfolio site with Tailwind CSS and animations"
Tags: ["#web-development", "#react", "#frontend", "#portfolio", "#tailwind-css"]
Category: "Web Development Project Planning"

✅ TECHNICAL DISCUSSION:
Text: "The API endpoint is returning 404 errors when the database connection fails"
Tags: ["#api", "#debugging", "#database", "#error-handling", "#backend"]
Category: "API Troubleshooting"

✅ PERSONAL/CREATIVE CONTENT:
Text: "We want to showcase our adventures with retro TV effects and smooth animations"
Tags: ["#creative-design", "#portfolio", "#animation", "#personal-project", "#adventure"]
Category: "Creative Portfolio Design"

❌ INCORRECT TAGGING (AVOID THESE):
Text: "Building a React website with animations"
WRONG: ["#genetic-disorder", "#symptoms", "#family-health"]  # Completely wrong domain
RIGHT: ["#web-development", "#react", "#frontend", "#animation"]

TAG CATEGORIES BY DOMAIN:

TECHNICAL/CONVERSATIONS:
- Programming: #python, #javascript, #react, #api, #database
- Development: #web-development, #frontend, #backend, #debugging
- Tools: #git, #docker, #vscode, #npm
- Concepts: #architecture, #testing, #deployment, #optimization

PERSONAL/CREATIVE:
- Projects: #portfolio, #personal-project, #creative-design
- Activities: #adventure, #travel, #hobby, #learning
- Life: #personal, #reflection, #planning, #goals

MEDICAL/HEALTH (ONLY for actual medical content):
- Medical: #health, #medical, #symptoms, #treatment
- Mental Health: #mental-health, #wellness, #therapy

BUSINESS/PRODUCTIVITY:
- Work: #productivity, #business, #workflow, #planning
- Learning: #education, #tutorial, #learning, #skill-development

OUTPUT FORMAT:
Return ONLY a valid JSON object:
{{
  "tags": ["#specific-tag1", "#specific-tag2", "#specific-tag3"],
  "category": "Concise category description",
  "confidence": "high|medium|low",
  "domain": "technical|personal|medical|business|creative"
}}

TEXT TO TAG:{context_info}
---
{chunk_text}
---

IMPORTANT: 
- Verify the tags match the actual content domain
- Be specific and accurate
- Return ONLY the JSON object
"""


def conversation_level_prompt(conversation_text: str) -> str:
    """
    Prompt for tagging at the conversation level first.
    
    Args:
        conversation_text: The full conversation or representative chunks
    
    Returns:
        Conversation-level prompt string
    """
    return f"""
You are an expert conversation classifier. Analyze this conversation and identify the primary domain and topics.

TASK:
1. Determine the main domain (technical, personal, medical, business, creative, etc.)
2. Identify 5-8 key topics/themes
3. Assign a primary category
4. Note any sub-domains or secondary themes

DOMAIN CLASSIFICATION:
- TECHNICAL: Programming, development, debugging, tools, APIs
- PERSONAL: Life, relationships, hobbies, personal projects
- MEDICAL: Health, symptoms, treatment, medical advice
- BUSINESS: Work, productivity, planning, professional topics
- CREATIVE: Art, design, creative projects, storytelling
- EDUCATIONAL: Learning, tutorials, how-to content
- OTHER: Travel, food, entertainment, etc.

CONVERSATION ANALYSIS:
---
{conversation_text}
---

OUTPUT FORMAT:
Return ONLY a valid JSON object:
{{
  "primary_domain": "technical|personal|medical|business|creative|educational|other",
  "key_topics": ["topic1", "topic2", "topic3", "topic4", "topic5"],
  "primary_category": "Main category description",
  "sub_domains": ["sub-domain1", "sub-domain2"],
  "conversation_tags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
  "confidence": "high|medium|low"
}}

Return ONLY the JSON object.
"""


def validation_prompt(chunk_text: str, proposed_tags: list, conversation_context: str = "") -> str:
    """
    Prompt to validate if proposed tags are appropriate for the content.
    
    Args:
        chunk_text: The chunk text
        proposed_tags: Tags to validate
        conversation_context: Conversation context
    
    Returns:
        Validation prompt string
    """
    return f"""
You are a tag validation expert. Review the proposed tags and determine if they accurately represent the content.

TASK:
Validate if the proposed tags are appropriate for the given content.

VALIDATION CRITERIA:
1. Do the tags match the content domain?
2. Are the tags specific and meaningful?
3. Are there any systematic biases or errors?
4. Would these tags help someone find this content later?

CONTENT:
---
{chunk_text}
---

PROPOSED TAGS: {proposed_tags}

CONVERSATION CONTEXT: {conversation_context}

OUTPUT FORMAT:
Return ONLY a valid JSON object:
{{
  "is_valid": true|false,
  "issues": ["issue1", "issue2"],
  "suggested_tags": ["#better-tag1", "#better-tag2"],
  "reasoning": "Brief explanation of validation decision"
}}

Return ONLY the JSON object.
"""


def get_enhanced_prompt(chunk_text: str, conversation_context: str = "", style: str = "enhanced") -> str:
    """
    Get the appropriate enhanced prompt.
    
    Args:
        chunk_text: The chunk text to tag
        conversation_context: Optional conversation context
        style: Prompt style ("enhanced", "conversation", "validation")
    
    Returns:
        Appropriate prompt string
    """
    if style == "conversation":
        return conversation_level_prompt(chunk_text)
    elif style == "validation":
        return validation_prompt(chunk_text, [], conversation_context)
    else:
        return enhanced_tagging_prompt(chunk_text, conversation_context) 