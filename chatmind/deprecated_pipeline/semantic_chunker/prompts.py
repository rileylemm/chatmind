#!/usr/bin/env python3
"""
Prompt Templates for Semantic Chunking

Defines the prompts used by the semantic chunker to instruct GPT
on how to split conversations into meaningful sections.
"""

def chunking_prompt(chat_text: str) -> str:
    """
    Main prompt for semantic chunking of conversations.
    
    Args:
        chat_text: The full conversation text to be chunked
    
    Returns:
        Formatted prompt string for GPT
    """
    return f"""
You are an expert at analyzing conversations and breaking them into semantically coherent sections.

TASK: Split the following ChatGPT conversation into meaningful sections. Each section should focus on one main topic, problem, or theme.

GUIDELINES:
- Create sections that are semantically coherent and focused
- Each section should have a clear, descriptive title
- Include all relevant messages in each section
- Don't split in the middle of a coherent discussion
- Aim for 2-6 sections per conversation (unless it's very short)
- Preserve the original conversation flow and context

OUTPUT FORMAT: Return ONLY a valid JSON array of objects with this exact structure:
[
  {{
    "title": "Descriptive section title",
    "content": "Full conversation text for this section (including all relevant messages)"
  }},
  {{
    "title": "Another section title", 
    "content": "Content for this section"
  }}
]

CONVERSATION TO CHUNK:
---
{chat_text}
---

Remember: Return ONLY the JSON array, no other text or explanations.
"""


def chunking_prompt_detailed(chat_text: str) -> str:
    """
    More detailed prompt for complex conversations.
    
    Args:
        chat_text: The full conversation text to be chunked
    
    Returns:
        Detailed prompt string for GPT
    """
    return f"""
You are an expert conversation analyst specializing in semantic chunking of technical discussions, brainstorming sessions, and problem-solving conversations.

TASK: Analyze the following conversation and break it into semantically coherent sections that capture distinct topics, problems, or themes.

ANALYSIS CRITERIA:
1. **Topic Transitions**: Look for natural shifts in conversation topics
2. **Problem-Solution Pairs**: Group related problems and their solutions
3. **Conceptual Coherence**: Keep related concepts and explanations together
4. **Context Preservation**: Maintain enough context for each section to be understandable
5. **Logical Flow**: Respect the natural progression of the conversation

CHUNKING STRATEGY:
- **Short conversations** (< 10 messages): 1-2 sections
- **Medium conversations** (10-30 messages): 2-4 sections  
- **Long conversations** (> 30 messages): 4-6 sections
- **Very long conversations** (> 50 messages): 6-8 sections

SECTION TITLES:
- Be specific and descriptive
- Capture the main topic or problem
- Use action-oriented language when appropriate
- Examples: "Initial Problem Definition", "Code Review and Debugging", "Performance Optimization Discussion"

OUTPUT FORMAT: Return ONLY a valid JSON array:
[
  {{
    "title": "Specific, descriptive section title",
    "content": "Complete conversation text for this section, including all relevant messages in original format"
  }}
]

CONVERSATION:
---
{chat_text}
---

Return ONLY the JSON array. No explanations or additional text.
"""


def chunking_prompt_technical(chat_text: str) -> str:
    """
    Specialized prompt for technical conversations with code.
    
    Args:
        chat_text: The full conversation text to be chunked
    
    Returns:
        Technical-focused prompt string for GPT
    """
    return f"""
You are an expert at analyzing technical conversations, especially those involving code, debugging, and problem-solving.

TASK: Split this technical conversation into semantically coherent sections, paying special attention to:

TECHNICAL CONSIDERATIONS:
- **Code Blocks**: Keep code and its explanation together
- **Error Sequences**: Group error messages with their solutions
- **Debugging Sessions**: Keep debugging steps and resolutions together
- **Concept Explanations**: Group related technical concepts
- **Implementation Steps**: Keep planning and implementation together

CHUNKING RULES:
1. Don't split in the middle of a code block
2. Keep error messages with their solutions
3. Group related technical explanations
4. Preserve the logical flow of problem-solving
5. Maintain context for technical terms and concepts

SECTION TYPES TO LOOK FOR:
- Problem Definition & Initial Analysis
- Code Review & Debugging
- Error Investigation & Resolution  
- Implementation & Testing
- Optimization & Refinement
- Conceptual Explanations
- Final Solutions & Summary

OUTPUT FORMAT: Return ONLY a valid JSON array:
[
  {{
    "title": "Technical section title (e.g., 'Database Connection Debugging')",
    "content": "Complete conversation text for this technical section"
  }}
]

TECHNICAL CONVERSATION:
---
{chat_text}
---

Return ONLY the JSON array. No additional text.
"""


def get_chunking_prompt(chat_text: str, style: str = "standard") -> str:
    """
    Get the appropriate chunking prompt based on style.
    
    Args:
        chat_text: The conversation text to chunk
        style: Prompt style ("standard", "detailed", "technical")
    
    Returns:
        Appropriate prompt string
    """
    if style == "detailed":
        return chunking_prompt_detailed(chat_text)
    elif style == "technical":
        return chunking_prompt_technical(chat_text)
    else:
        return chunking_prompt(chat_text) 