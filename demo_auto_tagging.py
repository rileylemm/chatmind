#!/usr/bin/env python3
"""
Demo: Auto-Tagging

This script demonstrates the GPT-driven auto-tagging functionality.
"""

import json
from pathlib import Path
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

def test_auto_tagging():
    """Test auto-tagging with sample chunks."""
    
    print("🏷️ ChatMind Auto-Tagging Demo")
    print("=" * 50)
    
    # Load test chunks
    test_file = Path("chatmind/tagger/test_chunks.jsonl")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    chunks = []
    with open(test_file, 'r') as f:
        for line in f:
            chunks.append(json.loads(line))
    
    print(f"📋 Loaded {len(chunks)} test chunks")
    
    try:
        # Import auto-tagger
        from chatmind.tagger import ChunkTagger
        
        # Initialize tagger
        tagger = ChunkTagger(model="gpt-4", temperature=0.2)
        
        print("\n🔍 Running auto-tagging...")
        
        # Tag the chunks
        tagged_chunks = tagger.tag_multiple_chunks(chunks)
        
        print(f"\n✅ Tagging complete! Tagged {len(tagged_chunks)} chunks:")
        
        for i, chunk in enumerate(tagged_chunks):
            print(f"\n📄 Chunk {i+1}: {chunk['title']}")
            print(f"   Tags: {chunk.get('tags', [])}")
            print(f"   Category: {chunk.get('category', 'N/A')}")
            print(f"   Model: {chunk.get('tagging_model', 'N/A')}")
        
        # Show tagging statistics
        stats = tagger.get_tagging_stats(tagged_chunks)
        
        print(f"\n📊 Tagging Statistics:")
        print(f"  - Total chunks: {stats['total_chunks']}")
        print(f"  - Total tags applied: {stats['total_tags']}")
        print(f"  - Unique tags: {stats['unique_tags']}")
        print(f"  - Unique categories: {stats['unique_categories']}")
        
        if stats['top_tags']:
            print(f"  - Top tags: {[tag for tag, count in stats['top_tags'][:5]]}")
        
        # Show example of tagging benefits
        print(f"\n🎯 Auto-Tagging Benefits:")
        print(f"  - Automatic hashtag generation")
        print(f"  - Semantic categorization")
        print(f"  - Improved search and filtering")
        print(f"  - Better content organization")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have installed the required dependencies:")
        print("   pip install openai tqdm")
    except Exception as e:
        print(f"❌ Error during tagging: {e}")
        print("💡 Make sure your OPENAI_API_KEY is set in the environment")


def test_prompt_styles():
    """Test different tagging prompt styles."""
    
    print("\n" + "="*60)
    print("🎨 Testing Different Tagging Prompt Styles")
    print("="*60)
    
    try:
        from chatmind.tagger.prompts import get_tagging_prompt
        
        test_text = "This is a sample chunk about Python web development with FastAPI."
        
        styles = ["standard", "detailed", "general"]
        
        for style in styles:
            print(f"\n📝 {style.title()} Style Prompt:")
            prompt = get_tagging_prompt(test_text, style)
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
        
        # Test with auto-tagging enabled
        embedder = ChatEmbedder(
            model_name="all-MiniLM-L6-v2",
            processed_dir="data/processed",
            embeddings_dir="data/embeddings"
        )
        
        print("✅ Successfully imported ChatEmbedder with auto-tagging support")
        print("💡 To use auto-tagging in the pipeline:")
        print("   python chatmind/embedding/embed_and_cluster.py --auto-tagging")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")


def test_standalone_tagging():
    """Test standalone tagging script."""
    
    print("\n" + "="*60)
    print("🔄 Testing Standalone Tagging Script")
    print("="*60)
    
    try:
        from chatmind.tagger.run_tagging import process_chunks_with_tagging
        from pathlib import Path
        
        input_file = Path("chatmind/tagger/test_chunks.jsonl")
        output_file = Path("data/processed/test_tagged_chunks.jsonl")
        
        if input_file.exists():
            print("✅ Testing standalone tagging...")
            process_chunks_with_tagging(
                input_file=input_file,
                output_file=output_file,
                model="gpt-4",
                style="detailed"
            )
            print("✅ Standalone tagging test completed!")
        else:
            print("❌ Test chunks file not found")
    
    except ImportError as e:
        print(f"❌ Import error: {e}")


if __name__ == "__main__":
    test_auto_tagging()
    test_prompt_styles()
    test_integration()
    test_standalone_tagging()
    
    print("\n" + "="*60)
    print("🎯 Auto-Tagging Summary")
    print("="*60)
    print("""
✅ What We Built:
- GPT-driven automatic tagging of semantic chunks
- Multiple prompt styles (standard, detailed, general)
- Fallback safety when GPT fails
- Integration with existing embedding pipeline
- Rich tagging statistics and metadata

🔧 Usage:
- Direct: from chatmind.tagger import ChunkTagger
- Pipeline: python embed_and_cluster.py --auto-tagging
- Standalone: python tagger/run_tagging.py

💡 Benefits:
- Automatic hashtag generation
- Semantic categorization
- Improved search and filtering
- Better content organization
- Fallback safety

🔄 Pipeline Flow:
1. Extract conversations → Semantic chunking → Auto-tagging → Embedding → Clustering

🎯 Next Steps:
- Test with your actual semantic chunks
- Adjust prompt styles for your use case
- Monitor API costs and performance
- Fine-tune tagging parameters
- Add tag-based filtering to frontend
    """) 