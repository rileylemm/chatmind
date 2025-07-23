#!/usr/bin/env python3
"""
Test: Overlapping ChatGPT Exports

This script demonstrates how ChatMind handles overlapping exports
where the same conversations appear in multiple ZIP files.
"""

import subprocess
import sys
import jsonlines
from pathlib import Path

def count_chats():
    """Count chats in the processed data."""
    chats_file = Path("data/processed/chats.jsonl")
    if not chats_file.exists():
        return 0
    
    count = 0
    with jsonlines.open(chats_file) as reader:
        for _ in reader:
            count += 1
    return count

def print_chat_titles():
    """Print titles of processed chats."""
    chats_file = Path("data/processed/chats.jsonl")
    if not chats_file.exists():
        return
    
    print("\n📋 Current chats in database:")
    with jsonlines.open(chats_file) as reader:
        for i, chat in enumerate(reader, 1):
            print(f"  {i}. {chat.get('title', 'Untitled')}")

def main():
    print("🧪 Testing Overlapping Export Handling")
    print("=" * 50)
    
    # Ensure directories exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    print("\n📊 Current state:")
    chat_count = count_chats()
    print(f"Chats in database: {chat_count}")
    
    if chat_count > 0:
        print_chat_titles()
    
    print("\n💡 To test overlapping exports:")
    print("1. Place your first ChatGPT export ZIP in data/raw/")
    print("2. Run: python chatmind/data_ingestion/extract_and_flatten.py")
    print("3. Place a second export ZIP (with overlapping content) in data/raw/")
    print("4. Run the same command again")
    print("5. Check that only new conversations were added")
    
    print("\n🔍 The system will:")
    print("✅ Process all ZIP files (even if they contain overlapping content)")
    print("✅ Use content hashing to identify duplicate conversations")
    print("✅ Only add truly new conversations to the database")
    print("✅ Skip conversations that already exist (regardless of which ZIP they came from)")
    
    print("\n📈 Expected behavior:")
    print("- First export: All conversations added")
    print("- Second export: Only new conversations added, duplicates skipped")
    print("- Third export: Only new conversations added, all existing skipped")
    
    print("\n🛠️ Commands to test:")
    print("python chatmind/data_ingestion/extract_and_flatten.py --verbose")
    print("python demo_incremental.py")

if __name__ == "__main__":
    main() 