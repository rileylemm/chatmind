#!/usr/bin/env python3
"""
Prompt Templates for Auto-Tagging

Defines the prompts used by the tagger to instruct GPT
on how to tag semantic chunks with hashtags and categories.
"""

def tagging_prompt(chunk_text: str) -> str:
    """
    Main prompt for tagging semantic chunks.
    
    Args:
        chunk_text: The chunk text to be tagged
    
    Returns:
        Formatted prompt string for GPT
    """
    return f"""
You are an AI assistant that analyzes text and assigns relevant semantic tags and a concise category.

TASK:
Analyze the following text and:
1. Generate 3–5 relevant hashtags
2. Assign a short, descriptive category label

GUIDELINES:
- Tags must be specific and meaningful (avoid generic tags like #general or #misc)
- Use hashtags to represent key ideas, tools, topics, or themes
- Tags can be:
  - **Technical** (e.g., #python, #api-design)
  - **Conceptual** (e.g., #consciousness, #systems-thinking)
  - **Personal or reflective** (e.g., #relationships, #burnout)
  - **Creative or artistic** (e.g., #storytelling, #design-process)
- The category must be a short phrase, not a full sentence (e.g., "AI Alignment Debate", "Personal Reflections on Friendship")
- Focus on the dominant theme or insight of the text
- Think about how this chunk could be rediscovered or grouped meaningfully in a broader context

OUTPUT FORMAT:
Return ONLY a valid JSON object in this exact structure:
{{
  "tags": ["#tag1", "#tag2", "#tag3"],
  "category": "A concise category title"
}}

TEXT TO TAG:
---
{chunk_text}
---

Remember: Return ONLY the JSON object — no additional commentary or explanation.
"""


def tagging_prompt_detailed(chunk_text: str) -> str:
    """
    More detailed prompt for complex technical content.
    
    Args:
        chunk_text: The chunk text to be tagged
    
    Returns:
        Detailed prompt string for GPT
    """
    return f"""
You are an expert technical classifier specializing in AI, programming, and technology content.

TASK: Analyze the following text and create comprehensive tags and categories.

TAGGING CRITERIA:
1. **Technical Focus**: Identify programming languages, frameworks, tools
2. **AI/ML Topics**: Tag machine learning, AI, data science concepts
3. **Problem Types**: Classify debugging, optimization, architecture, etc.
4. **Domain Areas**: Identify web dev, mobile, backend, frontend, etc.
5. **Complexity Level**: Consider beginner, intermediate, advanced content

TAG CATEGORIES TO CONSIDER:
- Programming: #python, #javascript, #java, #cpp, #rust
- Frameworks: #react, #fastapi, #django, #flask, #vue
- AI/ML: #machine-learning, #llm, #nlp, #computer-vision
- Databases: #sql, #mongodb, #postgresql, #redis
- Cloud: #aws, #azure, #gcp, #docker, #kubernetes
- Tools: #git, #docker, #vscode, #jupyter
- Concepts: #api, #microservices, #testing, #deployment

OUTPUT FORMAT: Return ONLY a valid JSON object:
{{
  "tags": ["#specific-tag1", "#specific-tag2", "#specific-tag3", "#specific-tag4"],
  "category": "Specific technical category (e.g., 'API Development with FastAPI')"
}}

TECHNICAL TEXT TO TAG:
---
{chunk_text}
---

Return ONLY the JSON object. No explanations.
"""


def tagging_prompt_general(chunk_text: str) -> str:
    """
    General-purpose prompt for non-technical content.
    
    Args:
        chunk_text: The chunk text to be tagged
    
    Returns:
        General prompt string for GPT
    """
    return f"""
You are an expert content classifier that analyzes conversations and assigns relevant tags.

TASK: Analyze the following conversation text and create appropriate tags and categories.

CONTENT TYPES TO CONSIDER:
- Learning & Education: #learning, #tutorial, #how-to
- Problem Solving: #problem-solving, #debugging, #troubleshooting
- Planning & Strategy: #planning, #strategy, #architecture
- Creative & Design: #design, #creativity, #ui-ux
- Business & Productivity: #productivity, #business, #workflow
- Personal & Life: #personal, #life, #reflection
- Research & Analysis: #research, #analysis, #investigation

TAGGING GUIDELINES:
- Focus on the main topic or theme
- Include relevant hashtags for easy discovery
- Make tags specific but not overly technical
- Consider the context and purpose of the conversation
- Use common, recognizable hashtag formats

OUTPUT FORMAT: Return ONLY a valid JSON object:
{{
  "tags": ["#relevant-tag1", "#relevant-tag2", "#relevant-tag3"],
  "category": "General category description"
}}

CONVERSATION TEXT TO TAG:
---
{chunk_text}
---

Return ONLY the JSON object. No additional text.
"""


def get_tagging_prompt(chunk_text: str, style: str = "standard") -> str:
    """
    Get the appropriate tagging prompt based on style.
    
    Args:
        chunk_text: The chunk text to tag
        style: Prompt style ("standard", "detailed", "general")
    
    Returns:
        Appropriate prompt string
    """
    if style == "detailed":
        return tagging_prompt_detailed(chunk_text)
    elif style == "general":
        return tagging_prompt_general(chunk_text)
    else:
        return tagging_prompt(chunk_text) 