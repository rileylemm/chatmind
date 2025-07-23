#!/usr/bin/env python3
"""
Demo: Semantic Chunking

This script demonstrates the GPT-driven semantic chunking functionality.
"""

import json
from pathlib import Path
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

def test_semantic_chunking():
    """Test semantic chunking with a sample conversation."""
    
    print("🧠 ChatMind Semantic Chunking Demo")
    print("=" * 50)
    
    # Load test sample
    test_file = Path("chatmind/semantic_chunker/test_sample.json")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    with open(test_file, 'r') as f:
        test_data = json.load(f)
    
    print(f"📋 Test Conversation: {test_data['title']}")
    print(f"📝 Content length: {len(test_data['content'])} characters")
    
    try:
        # Import semantic chunker
        from chatmind.semantic_chunker import SemanticChunker
        
        # Initialize chunker
        chunker = SemanticChunker(model="gpt-4", temperature=0.3)
        
        # Prepare chat data
        chat_data = {
            'title': test_data['title'],
            'content_hash': test_data['id'],
            'messages': [
                {
                    'role': 'user' if 'USER:' in line else 'assistant',
                    'content': line.replace('USER: ', '').replace('GPT: ', '')
                }
                for line in test_data['content'].split('\n\n')
                if line.strip()
            ]
        }
        
        print("\n🔍 Running semantic chunking...")
        
        # Chunk the conversation
        chunks = chunker.chunk_chat(chat_data)
        
        print(f"\n✅ Chunking complete! Created {len(chunks)} semantic chunks:")
        
        for i, chunk in enumerate(chunks):
            print(f"\n📄 Chunk {i+1}: {chunk['title']}")
            print(f"   Type: {chunk.get('chunk_type', 'unknown')}")
            print(f"   Content length: {len(chunk['content'])} characters")
            print(f"   Preview: {chunk['content'][:100]}...")
        
        # Show chunking statistics
        semantic_chunks = [c for c in chunks if c.get('chunk_type') == 'semantic']
        fallback_chunks = [c for c in chunks if c.get('chunk_type') == 'fallback']
        
        print(f"\n📊 Statistics:")
        print(f"  - Total chunks: {len(chunks)}")
        print(f"  - Semantic chunks: {len(semantic_chunks)}")
        print(f"  - Fallback chunks: {len(fallback_chunks)}")
        
        # Show example of semantic chunking benefits
        if semantic_chunks:
            print(f"\n🎯 Semantic Chunking Benefits:")
            print(f"  - Chunks focus on specific topics/themes")
            print(f"  - Better context preservation")
            print(f"  - More meaningful titles")
            print(f"  - Improved clustering quality")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have installed the required dependencies:")
        print("   pip install openai tqdm")
    except Exception as e:
        print(f"❌ Error during chunking: {e}")
        print("💡 Make sure your OPENAI_API_KEY is set in the environment")


def test_prompt_styles():
    """Test different prompt styles."""
    
    print("\n" + "="*60)
    print("🎨 Testing Different Prompt Styles")
    print("="*60)
    
    try:
        from chatmind.semantic_chunker.prompts import get_chunking_prompt
        
        test_text = "This is a sample conversation for testing different prompt styles."
        
        styles = ["standard", "detailed", "technical"]
        
        for style in styles:
            print(f"\n📝 {style.title()} Style Prompt:")
            prompt = get_chunking_prompt(test_text, style)
            print(f"   Length: {len(prompt)} characters")
            print(f"   Preview: {prompt[:100]}...")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")


def test_integration():
    """Test integration with the embedding pipeline."""
    
    print("\n" + "="*60)
    print("🔗 Testing Integration with Embedding Pipeline")
    print("="*60)
    
    try:
        from chatmind.embedding.embed_and_cluster import ChatEmbedder
        
        # Test with semantic chunking enabled
        embedder = ChatEmbedder(
            model_name="all-MiniLM-L6-v2",
            processed_dir="data/processed",
            embeddings_dir="data/embeddings"
        )
        
        print("✅ Successfully imported ChatEmbedder with semantic chunking support")
        print("💡 To use semantic chunking in the pipeline:")
        print("   python chatmind/embedding/embed_and_cluster.py --semantic-chunking")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")


if __name__ == "__main__":
    test_semantic_chunking()
    test_prompt_styles()
    test_integration()
    
    print("\n" + "="*60)
    print("🎯 Semantic Chunking Summary")
    print("="*60)
    print("""
✅ What We Built:
- GPT-driven semantic chunking of conversations
- Multiple prompt styles (standard, detailed, technical)
- Fallback to simple chunking if GPT fails
- Integration with existing embedding pipeline
- Rich metadata preservation

🔧 Usage:
- Direct: from chatmind.semantic_chunker import SemanticChunker
- Pipeline: python embed_and_cluster.py --semantic-chunking
- Standalone: python semantic_chunker/run_chunking.py

💡 Benefits:
- Better semantic coherence in chunks
- Improved clustering quality
- More meaningful chunk titles
- Context preservation
- Fallback safety

🔄 Next Steps:
- Test with your actual ChatGPT exports
- Adjust prompt styles for your use case
- Monitor API costs and performance
- Fine-tune chunking parameters
    """) 