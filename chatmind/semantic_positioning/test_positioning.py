#!/usr/bin/env python3
"""
Test script for semantic positioning functionality.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chatmind.semantic_positioning.apply_topic_layout import apply_topic_layout


def test_positioning():
    """Test the semantic positioning functionality."""
    print("🧪 Testing semantic positioning...")
    
    # Check if input file exists
    input_file = Path("data/processed/tagged_chunks.jsonl")
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("Please run the tagging step first: python run_pipeline.py --skip-positioning")
        return False
    
    # Test the positioning
    success = apply_topic_layout(
        input_file=input_file,
        output_file=Path("data/processed/test_topics_with_coords.jsonl")
    )
    
    if success:
        print("✅ Semantic positioning test completed successfully!")
        
        # Check the output
        output_file = Path("data/processed/test_topics_with_coords.jsonl")
        if output_file.exists():
            import jsonlines
            count = 0
            with jsonlines.open(output_file) as reader:
                for topic in reader:
                    count += 1
                    if count <= 3:  # Show first 3 topics
                        print(f"  Topic {count}: {topic.get('topic_id', 'unknown')} "
                              f"at ({topic.get('x', 0):.3f}, {topic.get('y', 0):.3f})")
            
            print(f"📊 Generated {count} topics with coordinates")
            print(f"📁 Output saved to: {output_file}")
        else:
            print("❌ Output file not created")
            return False
    else:
        print("❌ Semantic positioning test failed!")
        return False
    
    return True


if __name__ == "__main__":
    success = test_positioning()
    sys.exit(0 if success else 1) 