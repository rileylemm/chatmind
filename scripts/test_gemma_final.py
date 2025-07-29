#!/usr/bin/env python3
"""
Final test of Gemma-2B with simplified prompts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatmind.tagger.local.local_enhanced_tagger import LocalEnhancedChunkTagger
from chatmind.tagger.local.local_prompts import get_gemma_tagging_prompt

def test_gemma_performance():
    """Test Gemma-2B performance with sample texts."""
    
    print("🧪 Testing Gemma-2B with Simplified Prompts")
    print("=" * 60)
    
    # Sample texts covering different domains
    sample_texts = [
        {
            "text": "The sickness 'mono' is short for 'mononucleosis', also known as the 'kissing disease' in English.",
            "expected_domain": "medical"
        },
        {
            "text": "Let's build a React portfolio site with Tailwind CSS and animations",
            "expected_domain": "technical"
        },
        {
            "text": "I'm planning a trip to Japan next spring to see the cherry blossoms",
            "expected_domain": "personal"
        },
        {
            "text": "The API endpoint is returning 404 errors when the database connection fails",
            "expected_domain": "technical"
        },
        {
            "text": "We want to showcase our adventures with retro TV effects and smooth animations",
            "expected_domain": "creative"
        }
    ]
    
    tagger = LocalEnhancedChunkTagger(
        model="gemma:2b",
        temperature=0.1,  # Low temperature for consistency
        max_retries=2,
        delay_between_calls=0.1
    )
    
    # Check if model is available
    if not tagger.check_model_availability():
        print("❌ Gemma-2B not available. Please run: ollama pull gemma:2b")
        return
    
    print("✅ Gemma-2B available")
    print(f"📊 Testing {len(sample_texts)} sample texts...\n")
    
    successful_tags = 0
    total_tests = len(sample_texts)
    
    for i, sample in enumerate(sample_texts, 1):
        text = sample["text"]
        expected_domain = sample["expected_domain"]
        
        print(f"--- Test {i}/{total_tests} ---")
        print(f"Text: {text[:80]}...")
        print(f"Expected domain: {expected_domain}")
        
        try:
            result = tagger.tag_chunk({
                'content': text,
                'chat_id': f'test_chat_{i}',
                'message_id': f'test_message_{i}'
            })
            
            tags = result.get('tags', [])
            category = result.get('category', 'N/A')
            domain = result.get('domain', 'N/A')
            
            # Check if we got useful tags (not fallback tags)
            if tags and not any(tag in ['#unprocessed', '#needs-review', '#error'] for tag in tags):
                successful_tags += 1
                print(f"✅ Success: {tags}")
            else:
                print(f"❌ Fallback tags: {tags}")
            
            print(f"Category: {category}")
            print(f"Domain: {domain}")
            
            # Check domain accuracy
            if expected_domain.lower() in domain.lower():
                print(f"🎯 Domain match: {expected_domain} ✓")
            else:
                print(f"⚠️  Domain mismatch: expected {expected_domain}, got {domain}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()  # Empty line for readability
    
    success_rate = (successful_tags / total_tests) * 100
    print(f"📊 Final Results:")
    print(f"Success Rate: {success_rate:.1f}% ({successful_tags}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 Excellent! Gemma-2B is ready for production.")
    elif success_rate >= 60:
        print("✅ Good! Gemma-2B is performing well.")
    else:
        print("⚠️  Needs improvement. Consider prompt adjustments.")
    
    return success_rate

def test_prompt_format():
    """Test the prompt format to make sure it's clean."""
    
    print("\n🔍 Testing Prompt Format")
    print("=" * 40)
    
    sample_text = "Let's build a React portfolio site with Tailwind CSS and animations"
    prompt = get_gemma_tagging_prompt(sample_text, "Domain: technical, Topics: web development")
    
    print("Generated prompt:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    # Check for common issues
    issues = []
    if "<|system|>" in prompt or "<|user|>" in prompt:
        issues.append("Contains chat tokens (should be instruction format)")
    if "{{" in prompt:
        issues.append("Contains response prefilling (not needed for Gemma)")
    if "DO NOT" in prompt:
        issues.append("Uses negative language (should use 'IMPORTANT')")
    
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Prompt format looks good!")

if __name__ == "__main__":
    test_prompt_format()
    test_gemma_performance() 