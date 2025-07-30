#!/usr/bin/env python3
"""
Gemma-2B Optimized Cluster Summarizer for ChatMind

Uses Gemma-2B via Ollama to generate intelligent cluster summaries from chunks.
Optimized for Gemma-2B's JSON compliance and performance characteristics.
"""

import json
import jsonlines
from pathlib import Path
from collections import defaultdict, Counter
import logging
from typing import Dict, List, Set, Optional
import time
import requests
import click
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GemmaOptimizedClusterSummarizer:
    """Gemma-2B optimized cluster summarizer using local models via Ollama."""
    
    def __init__(self, model: str = "gemma:2b", max_retries: int = 3, 
                 delay_between_calls: float = 0.1):
        self.model = model
        self.max_retries = max_retries
        self.delay_between_calls = delay_between_calls
        self.stats = {
            'clusters_processed': 0,
            'api_calls': 0,
            'errors': 0,
            'total_tokens': 0,
            'json_parsing_failures': 0
        }
    
    def _sanitize_content(self, text: str) -> str:
        """Sanitize content by removing problematic Unicode characters."""
        import re
        
        # Replace smart quotes with regular quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Replace em dashes and en dashes with regular dashes
        text = text.replace('—', '-').replace('–', '-')
        
        # Remove emojis and special Unicode characters
        text = re.sub(r'[^\x00-\x7F\u00A0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u2C60-\u2C7F\uA720-\uA7FF]+', '', text)
        
        # Remove zero-width characters
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def get_gemma_cluster_summary_prompt(self, cluster_chunks: List[Dict]) -> str:
        """Generate Gemma-2B optimized prompt for cluster summarization."""
        # Collect sample content from chunks
        sample_contents = []
        sample_titles = []
        
        for chunk in cluster_chunks[:6]:  # Limit to first 6 chunks for Gemma
            content = chunk.get('content', '').strip()
            if content and len(content) > 30:  # Lower threshold for Gemma
                # Sanitize content before using in prompt
                sanitized_content = self._sanitize_content(content)
                sample_contents.append(sanitized_content[:120])  # Shorter excerpts for Gemma
            
            title = chunk.get('chat_title', '').strip()
            if title and title not in sample_titles:
                # Sanitize title as well
                sanitized_title = self._sanitize_content(title)
                sample_titles.append(sanitized_title)
        
        # Create Gemma-2B optimized prompt using schema-based approach
        prompt = f"""Write JSON output that matches the schema to extract information.

Cluster Analysis:
- Number of chunks: {len(cluster_chunks)}
- Sample titles: {', '.join(sample_titles[:3])}
- Content samples:
{chr(10).join([f"- {content}" for content in sample_contents[:3]])}

Schema:
{{
  "topic": "string - specific topic name (e.g., 'Bicycle Derailleur Repair', 'German Medical Terms', 'Python Programming Tutorial')",
  "description": "string - brief description of cluster content",
  "key_concepts": ["string", "string", "string"] - list of 3-5 key concepts from the content,
  "domain": "string - one of: technical, personal, medical, academic, creative, business, other",
  "complexity": "string - one of: beginner, intermediate, advanced",
  "sample_questions": ["string", "string"] - list of 2 specific questions someone might ask about this topic,
  "tags": ["string", "string", "string"] - list of 3-5 hashtag tags (e.g., "#bicycle", "#repair", "#technical")
}}

Domain guidelines:
- technical: programming, engineering, science, technology, computers
- personal: relationships, daily life, hobbies, cooking, food, travel
- medical: health, medicine, symptoms, treatment, disease, illness
- academic: education, research, learning, studies, university
- creative: art, writing, design, music, entertainment, storytelling
- business: work, finance, money, investment, entrepreneurship
- other: anything else

Complexity guidelines:
- beginner: basic concepts, simple explanations, general knowledge
- intermediate: detailed explanations, specific techniques, moderate depth
- advanced: complex concepts, specialized knowledge, expert-level

Return ONLY the JSON object matching the schema above. No explanations or additional text."""
        
        return prompt
    
    def _call_local_model(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """Call Gemma-2B via Ollama API."""
        try:
            # Prepare the request optimized for Gemma-2B
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,  # Lower temperature for more consistent JSON
                    "top_p": 0.8,
                    "num_predict": 300,  # Shorter responses for Gemma
                    "repeat_penalty": 1.1
                }
            }
            
            if system_prompt:
                request_data["system"] = system_prompt
            
            # Make the API call
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=request_data,
                timeout=45  # Shorter timeout for Gemma
            )
            
            if response.status_code == 200:
                result = response.json()
                self.stats['api_calls'] += 1
                # Estimate tokens (rough approximation)
                self.stats['total_tokens'] += len(prompt.split()) + len(result.get('response', '').split())
                return result.get('response', '')
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to call Gemma-2B: {e}")
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from Gemma-2B response with robust parsing."""
        try:
            # Find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                
                # Try to clean up common issues
                json_str = self._clean_json_string(json_str)
                
                return json.loads(json_str)
            else:
                logger.warning(f"Could not find JSON in response: {response[:200]}...")
                return None
                
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from response: {e}")
            self.stats['json_parsing_failures'] += 1
            return None
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean up common JSON formatting issues from Gemma-2B."""
        try:
            # Remove trailing commas before closing braces/brackets
            import re
            json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
            
            # Fix common delimiter issues
            json_str = re.sub(r'(["\w])\s*\n\s*(["\w])', r'\1,\2', json_str)
            
            # Remove any trailing content after the JSON
            last_brace = json_str.rfind('}')
            if last_brace != -1:
                json_str = json_str[:last_brace + 1]
            
            # Fix common Gemma 2B issues
            json_str = re.sub(r'(\w+):\s*"([^"]*)"\s*([^,}\s])', r'\1: "\2", \3', json_str)
            json_str = re.sub(r'(\w+):\s*\[([^\]]*)\]\s*([^,}\s])', r'\1: [\2], \3', json_str)
            
            # Remove any schema comments that might have been included
            json_str = re.sub(r'//.*?\n', '', json_str)
            json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
            
            return json_str
            
        except Exception as e:
            logger.warning(f"Failed to clean JSON string: {e}")
            return json_str
    
    def _fix_and_parse_json(self, response: str) -> Optional[Dict]:
        """Fix common JSON issues and parse."""
        try:
            # First try direct extraction
            json_data = self._extract_json_from_response(response)
            if json_data:
                return json_data
            
            # Try to fix common issues
            cleaned_response = response.strip()
            
            # Remove conversational prefixes
            conversational_prefixes = [
                "Here's the analysis:", "Analysis:", "Summary:", "JSON:", 
                "The cluster analysis:", "Based on the content:", "Here's the JSON:",
                "Cluster analysis:", "Here's the summary:", "Summary of cluster:"
            ]
            for prefix in conversational_prefixes:
                if cleaned_response.startswith(prefix):
                    cleaned_response = cleaned_response[len(prefix):].strip()
            
            # Try to find JSON again
            json_data = self._extract_json_from_response(cleaned_response)
            if json_data:
                return json_data
            
            # Try more aggressive cleaning
            json_data = self._aggressive_json_extraction(response)
            if json_data:
                return json_data
            
            # Last resort: try to construct minimal JSON
            logger.warning("Attempting to construct minimal JSON from response")
            return self._construct_minimal_json(response)
            
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            self.stats['json_parsing_failures'] += 1
            return None
    
    def _aggressive_json_extraction(self, response: str) -> Optional[Dict]:
        """More aggressive JSON extraction for problematic responses."""
        try:
            # Look for JSON-like structure
            lines = response.split('\n')
            json_lines = []
            in_json = False
            brace_count = 0
            
            for line in lines:
                line = line.strip()
                if '{' in line:
                    in_json = True
                    brace_count += line.count('{')
                if in_json:
                    json_lines.append(line)
                if '}' in line and in_json:
                    brace_count -= line.count('}')
                    if brace_count <= 0:
                        break
            
            if json_lines:
                json_str = '\n'.join(json_lines)
                json_str = self._clean_json_string(json_str)
                return json.loads(json_str)
            
            # Try to find JSON between specific markers
            if "Schema:" in response and "{" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                    json_str = self._clean_json_string(json_str)
                    return json.loads(json_str)
            
            return None
            
        except Exception as e:
            logger.warning(f"Aggressive JSON extraction failed: {e}")
            return None
    
    def _construct_minimal_json(self, response: str) -> Optional[Dict]:
        """Construct minimal JSON when parsing fails."""
        try:
            # Extract key information from response
            lines = response.split('\n')
            topic = "Unknown Topic"
            description = "Cluster content"
            domain = "unknown"
            
            for line in lines:
                line = line.strip().lower()
                if "topic" in line and ":" in line:
                    topic = line.split(":", 1)[1].strip()
                elif "description" in line and ":" in line:
                    description = line.split(":", 1)[1].strip()
                elif "domain" in line and ":" in line:
                    domain = line.split(":", 1)[1].strip()
            
            return {
                "topic": topic,
                "description": description,
                "key_concepts": ["concept1", "concept2"],
                "domain": domain,
                "complexity": "unknown",
                "sample_questions": ["What is this about?"],
                "tags": ["#cluster", "#unknown"]
            }
            
        except Exception as e:
            logger.error(f"Failed to construct minimal JSON: {e}")
            return None
    
    def summarize_cluster_with_gemma(self, cluster_chunks: List[Dict]) -> Optional[Dict]:
        """Summarize a cluster using Gemma-2B."""
        prompt = self.get_gemma_cluster_summary_prompt(cluster_chunks)
        system_prompt = "You are a content analyst. Provide JSON summaries only."
        
        for attempt in range(self.max_retries):
            try:
                response = self._call_local_model(prompt, system_prompt)
                
                if response:
                    summary = self._fix_and_parse_json(response)
                    
                    if summary:
                        # Validate and fix summary structure
                        summary = self._validate_summary_structure(summary)
                        
                        # Add metadata
                        summary['cluster_size'] = len(cluster_chunks)
                        summary['sample_titles'] = list(set([
                            chunk.get('chat_title', '') for chunk in cluster_chunks[:5]
                            if chunk.get('chat_title', '')
                        ]))
                        summary['total_messages'] = len(cluster_chunks)
                        summary['summary_model'] = f"gemma-{self.model}"
                        summary['summary_timestamp'] = int(time.time())
                        
                        return summary
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
                    
            except Exception as e:
                logger.error(f"Gemma-2B call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_between_calls)
                    continue
        
        return None
    
    def _validate_summary_structure(self, summary: Dict) -> Dict:
        """Validate and fix summary structure."""
        required_fields = {
            'topic': 'Unknown Topic',
            'description': 'Cluster content',
            'key_concepts': [],
            'domain': 'unknown',
            'complexity': 'unknown',
            'sample_questions': [],
            'tags': []
        }
        
        # Ensure all required fields exist
        for field, default_value in required_fields.items():
            if field not in summary:
                summary[field] = default_value
            elif summary[field] is None:
                summary[field] = default_value
        
        # Ensure lists are actually lists
        for field in ['key_concepts', 'sample_questions', 'tags']:
            if not isinstance(summary[field], list):
                summary[field] = []
        
        # Validate domain
        valid_domains = ['technical', 'personal', 'medical', 'academic', 'creative', 'business', 'other']
        if summary['domain'] not in valid_domains:
            summary['domain'] = 'other' # Default to 'other' if invalid
        
        # Validate complexity
        valid_complexities = ['beginner', 'intermediate', 'advanced']
        if summary['complexity'] not in valid_complexities:
            summary['complexity'] = 'beginner' # Default to 'beginner' if invalid
        
        return summary
    
    def generate_gemma_summaries(self, chunks_file: Path, output_file: Path) -> Dict:
        """Generate Gemma-2B optimized cluster summaries from chunks data."""
        logger.info(f"Generating Gemma-2B cluster summaries from {chunks_file}")
        
        # Group chunks by cluster
        clusters = defaultdict(list)
        cluster_sizes = Counter()
        
        with jsonlines.open(chunks_file) as reader:
            for chunk in reader:
                cluster_id = chunk.get('cluster_id')
                if cluster_id is not None and cluster_id != -1:
                    clusters[cluster_id].append(chunk)
                    cluster_sizes[cluster_id] += 1
        
        logger.info(f"Found {len(clusters)} clusters")
        
        # Generate summaries for each cluster
        summaries = {}
        
        for cluster_id, chunks in tqdm(clusters.items(), desc="Summarizing clusters"):
            try:
                summary = self.summarize_cluster_with_gemma(chunks)
                
                if summary:
                    summaries[str(cluster_id)] = summary
                    self.stats['clusters_processed'] += 1
                else:
                    # Fallback to basic summary
                    logger.warning(f"Gemma-2B summary failed for cluster {cluster_id}, using fallback")
                    summaries[str(cluster_id)] = self._generate_fallback_summary(cluster_id, chunks)
                    self.stats['errors'] += 1
                
                # Add delay between calls
                time.sleep(self.delay_between_calls)
                
            except Exception as e:
                logger.error(f"Failed to summarize cluster {cluster_id}: {e}")
                summaries[str(cluster_id)] = self._generate_fallback_summary(cluster_id, chunks)
                self.stats['errors'] += 1
        
        # Save summaries
        with open(output_file, 'w') as f:
            json.dump(summaries, f, indent=2)
        
        logger.info(f"Generated Gemma-2B summaries for {len(summaries)} clusters")
        logger.info(f"Saved to {output_file}")
        
        return summaries
    
    def _generate_fallback_summary(self, cluster_id: int, chunks: List[Dict]) -> Dict:
        """Generate a meaningful fallback summary when Gemma-2B fails."""
        # Extract top words from content
        all_text = " ".join([chunk.get('content', '') for chunk in chunks])
        
        # Sanitize the text before processing
        all_text = self._sanitize_content(all_text)
        
        # Simple word extraction
        import re
        words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'this', 'that', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must', 'shall', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'that', 'there', 'here', 'from', 'into', 'during', 'including', 'until', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning', 'considering', 'following', 'regarding', 'including', 'containing', 'involving', 'concerning', 'relating', 'regarding', 'about', 'over', 'under', 'above', 'below', 'within', 'without', 'between', 'among', 'across', 'through', 'around', 'along', 'beside', 'beyond', 'behind', 'before', 'after', 'during', 'since', 'until', 'while', 'when', 'where', 'why', 'how', 'what', 'which', 'who', 'whom', 'whose', 'that', 'this', 'these', 'those', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'you', 'your', 'yours', 'yourself', 'yourselves', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'}
        word_counts = Counter(word for word in words if word not in stop_words)
        top_words = [word for word, _ in word_counts.most_common(10)]
        
        # Get sample titles
        sample_titles = list(set([
            self._sanitize_content(chunk.get('chat_title', '')) for chunk in chunks[:5]
            if chunk.get('chat_title', '')
        ]))
        
        # Determine domain based on content analysis
        domain = self._analyze_domain(all_text, top_words, sample_titles)
        
        # Determine complexity based on content length and vocabulary
        complexity = self._analyze_complexity(all_text, chunks)
        
        # Generate meaningful topic from titles and content
        topic = self._generate_topic_from_content(sample_titles, top_words, all_text)
        
        # Generate meaningful description
        description = self._generate_description_from_content(all_text, top_words, len(chunks))
        
        # Generate meaningful concepts
        concepts = self._extract_meaningful_concepts(all_text, top_words, domain)
        
        # Generate meaningful tags
        tags = self._generate_meaningful_tags(top_words, domain, topic)
        
        return {
            'topic': topic,
            'description': description,
            'key_concepts': concepts,
            'domain': domain,
            'complexity': complexity,
            'sample_questions': self._generate_sample_questions(topic, domain),
            'tags': tags,
            'cluster_size': len(chunks),
            'sample_titles': sample_titles,
            'total_messages': len(chunks),
            'summary_model': 'gemma-fallback',
            'summary_timestamp': int(time.time())
        }
    
    def _analyze_domain(self, text: str, top_words: List[str], titles: List[str]) -> str:
        """Analyze content to determine domain."""
        text_lower = text.lower()
        titles_lower = " ".join(titles).lower()
        
        # Technical indicators
        tech_words = ['programming', 'code', 'python', 'javascript', 'algorithm', 'database', 'api', 'software', 'computer', 'technology', 'engineering', 'science', 'math', 'physics', 'chemistry']
        if any(word in text_lower for word in tech_words) or any(word in titles_lower for word in tech_words):
            return 'technical'
        
        # Medical indicators
        medical_words = ['health', 'medical', 'doctor', 'symptoms', 'treatment', 'medicine', 'patient', 'diagnosis', 'therapy', 'hospital', 'disease', 'illness', 'pain']
        if any(word in text_lower for word in medical_words) or any(word in titles_lower for word in medical_words):
            return 'medical'
        
        # Personal indicators
        personal_words = ['cooking', 'recipe', 'food', 'family', 'relationship', 'hobby', 'travel', 'home', 'garden', 'sports', 'fitness', 'lifestyle']
        if any(word in text_lower for word in personal_words) or any(word in titles_lower for word in personal_words):
            return 'personal'
        
        # Creative indicators
        creative_words = ['art', 'design', 'music', 'writing', 'creative', 'drawing', 'painting', 'photography', 'film', 'entertainment', 'story', 'poetry']
        if any(word in text_lower for word in creative_words) or any(word in titles_lower for word in creative_words):
            return 'creative'
        
        # Business indicators
        business_words = ['business', 'finance', 'money', 'investment', 'work', 'job', 'career', 'management', 'entrepreneur', 'startup', 'company', 'market']
        if any(word in text_lower for word in business_words) or any(word in titles_lower for word in business_words):
            return 'business'
        
        # Academic indicators
        academic_words = ['study', 'research', 'education', 'learning', 'university', 'college', 'school', 'course', 'lecture', 'academic', 'thesis', 'paper']
        if any(word in text_lower for word in academic_words) or any(word in titles_lower for word in academic_words):
            return 'academic'
        
        return 'other'
    
    def _analyze_complexity(self, text: str, chunks: List[Dict]) -> str:
        """Analyze content to determine complexity level."""
        # Count unique words (vocabulary diversity)
        words = text.lower().split()
        unique_words = len(set(words))
        total_words = len(words)
        
        # Average content length per chunk
        avg_content_length = sum(len(chunk.get('content', '')) for chunk in chunks) / len(chunks)
        
        # Complexity indicators
        complex_words = ['algorithm', 'implementation', 'architecture', 'optimization', 'analysis', 'methodology', 'framework', 'protocol', 'specification', 'configuration']
        complex_count = sum(1 for word in complex_words if word in text.lower())
        
        # Determine complexity based on multiple factors
        if (unique_words / max(total_words, 1) > 0.7 and avg_content_length > 200) or complex_count > 2:
            return 'advanced'
        elif (unique_words / max(total_words, 1) > 0.5 and avg_content_length > 100) or complex_count > 0:
            return 'intermediate'
        else:
            return 'beginner'
    
    def _generate_topic_from_content(self, titles: List[str], top_words: List[str], text: str) -> str:
        """Generate a meaningful topic from titles and content."""
        if titles:
            # Use the most descriptive title
            main_title = titles[0]
            if len(main_title) > 10 and main_title != "Main topic or theme":
                return main_title
        
        # Generate topic from top words and content
        if len(top_words) >= 2:
            # Look for specific patterns in text
            if 'cooking' in text.lower() or 'recipe' in text.lower():
                return f"{top_words[0].title()} Cooking"
            elif 'programming' in text.lower() or 'code' in text.lower():
                return f"{top_words[0].title()} Programming"
            elif 'health' in text.lower() or 'medical' in text.lower():
                return f"{top_words[0].title()} Health"
            else:
                return f"{top_words[0].title()} and {top_words[1].title()}"
        elif len(top_words) >= 1:
            return f"{top_words[0].title()} Topics"
        else:
            return "General Discussion"
    
    def _generate_description_from_content(self, text: str, top_words: List[str], chunk_count: int) -> str:
        """Generate a meaningful description from content."""
        if len(top_words) >= 3:
            return f"Cluster containing {chunk_count} chunks about {', '.join(top_words[:3])}"
        elif len(top_words) >= 1:
            return f"Cluster containing {chunk_count} chunks about {top_words[0]}"
        else:
            return f"Cluster containing {chunk_count} chunks with various topics"
    
    def _generate_sample_questions(self, topic: str, domain: str) -> List[str]:
        """Generate sample questions based on topic and domain."""
        questions = []
        
        if domain == 'technical':
            questions = ["How does this work?", "What are the best practices?"]
        elif domain == 'medical':
            questions = ["What are the symptoms?", "How is this treated?"]
        elif domain == 'personal':
            questions = ["How do I do this?", "What are the benefits?"]
        elif domain == 'creative':
            questions = ["How can I create this?", "What techniques are used?"]
        elif domain == 'business':
            questions = ["What are the strategies?", "How can this be implemented?"]
        else:
            questions = ["What is this about?", "How does this work?"]
        
        return questions
    
    def _extract_meaningful_concepts(self, text: str, top_words: List[str], domain: str) -> List[str]:
        """Extract meaningful concepts based on domain and content."""
        concepts = []
        
        # Add top meaningful words
        for word in top_words[:5]:
            if len(word) > 3 and word not in concepts:
                concepts.append(word)
        
        # Add domain-specific concepts
        if domain == 'technical':
            tech_concepts = ['programming', 'algorithm', 'database', 'software', 'technology', 'engineering', 'code', 'system', 'development', 'implementation']
            for concept in tech_concepts:
                if concept in text.lower() and concept not in concepts:
                    concepts.append(concept)
        
        elif domain == 'medical':
            medical_concepts = ['health', 'treatment', 'symptoms', 'diagnosis', 'medicine', 'patient', 'therapy', 'disease', 'illness', 'medical']
            for concept in medical_concepts:
                if concept in text.lower() and concept not in concepts:
                    concepts.append(concept)
        
        elif domain == 'personal':
            personal_concepts = ['cooking', 'recipe', 'food', 'family', 'relationship', 'hobby', 'travel', 'home', 'garden', 'sports', 'fitness']
            for concept in personal_concepts:
                if concept in text.lower() and concept not in concepts:
                    concepts.append(concept)
        
        # Ensure we have at least 3 concepts
        while len(concepts) < 3:
            concepts.append(f"concept{len(concepts) + 1}")
        
        return concepts[:5]  # Limit to 5 concepts
    
    def _generate_meaningful_tags(self, top_words: List[str], domain: str, topic: str) -> List[str]:
        """Generate meaningful tags based on content and domain."""
        tags = []
        
        # Add domain-specific tags
        if domain == 'technical':
            tags.extend(['#technology', '#technical'])
        elif domain == 'medical':
            tags.extend(['#medical', '#health'])
        elif domain == 'personal':
            tags.extend(['#personal', '#lifestyle'])
        elif domain == 'creative':
            tags.extend(['#creative', '#art'])
        elif domain == 'business':
            tags.extend(['#business', '#finance'])
        elif domain == 'academic':
            tags.extend(['#academic', '#education'])
        
        # Add topic-specific tags
        for word in top_words[:3]:
            if len(word) > 3:
                tags.append(f"#{word}")
        
        # Ensure we have at least 3 tags
        while len(tags) < 3:
            tags.append(f"#tag{len(tags) + 1}")
        
        return tags[:5]  # Limit to 5 tags
    
    def get_summary_stats(self) -> Dict:
        """Get statistics about the summarization process."""
        return {
            'clusters_processed': self.stats['clusters_processed'],
            'api_calls': self.stats['api_calls'],
            'errors': self.stats['errors'],
            'json_parsing_failures': self.stats['json_parsing_failures'],
            'total_tokens': self.stats['total_tokens'],
            'success_rate': (self.stats['clusters_processed'] - self.stats['errors']) / max(self.stats['clusters_processed'], 1)
        }


@click.command()
@click.option('--input-file', 
              default='data/embeddings/chunks_with_clusters.jsonl',
              help='Input chunks file')
@click.option('--output-file', 
              default='data/embeddings/gemma_cluster_summaries.json',
              help='Output summaries file')
@click.option('--model', 
              default='gemma:2b',
              help='Local model to use (default: gemma:2b)')
@click.option('--max-retries', 
              default=3,
              help='Maximum retries for API calls')
@click.option('--delay', 
              default=0.1,
              help='Delay between API calls (seconds)')
@click.option('--check-only', is_flag=True,
              help='Only check setup, don\'t process')
def main(input_file: str, output_file: str, model: str, max_retries: int, delay: float, check_only: bool):
    """Generate Gemma-2B optimized cluster summaries using local models."""
    
    if check_only:
        logger.info("🔍 Checking Gemma-2B cluster summarizer setup...")
        
        # Check input file
        input_path = Path(input_file)
        if input_path.exists():
            logger.info(f"✅ Input file exists: {input_file}")
        else:
            logger.error(f"❌ Input file not found: {input_file}")
            return 1
        
        # Check output directory
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Output directory ready: {output_path.parent}")
        
        # Test Ollama connection
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                gemma_available = any('gemma' in model.get('name', '').lower() for model in models)
                if gemma_available:
                    logger.info("✅ Gemma-2B model available via Ollama")
                else:
                    logger.warning("⚠️  Gemma-2B not found in available models")
            else:
                logger.error("❌ Cannot connect to Ollama API")
                return 1
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {e}")
            return 1
        
        logger.info("✅ Gemma-2B cluster summarizer setup looks good!")
        return 0
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize summarizer
    summarizer = GemmaOptimizedClusterSummarizer(
        model=model,
        max_retries=max_retries,
        delay_between_calls=delay
    )
    
    # Generate summaries
    summaries = summarizer.generate_gemma_summaries(input_path, output_path)
    
    # Get statistics
    stats = summarizer.get_summary_stats()
    
    # Print summary statistics
    total_clusters = len(summaries)
    total_messages = sum(s['total_messages'] for s in summaries.values())
    avg_cluster_size = total_messages / total_clusters if total_clusters > 0 else 0
    
    logger.info("")
    logger.info("📊 Gemma-2B Cluster Summary Statistics:")
    logger.info(f"  Total clusters: {total_clusters}")
    logger.info(f"  Total messages: {total_messages}")
    logger.info(f"  Average cluster size: {avg_cluster_size:.1f}")
    logger.info(f"  Model calls made: {stats['api_calls']}")
    logger.info(f"  Estimated tokens used: {stats['total_tokens']}")
    logger.info(f"  Success rate: {stats['success_rate']:.1%}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info(f"  JSON parsing failures: {stats['json_parsing_failures']}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 