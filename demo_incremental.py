#!/usr/bin/env python3
"""
Demo: Incremental Processing with ChatMind

This script demonstrates how ChatMind handles re-ingestion of new ChatGPT exports
and avoids duplicate data through persistent state tracking.
"""

import subprocess
import sys
import time
from pathlib import Path
import jsonlines

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

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

def main():
    print("🧠 ChatMind Incremental Processing Demo")
    print("This demo shows how the system handles re-ingestion of new data")
    
    # Ensure data directories exist
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    print_separator("Step 1: Initial Processing")
    print("First, let's process any existing ChatGPT exports...")
    
    initial_count = count_chats()
    print(f"Current chats in database: {initial_count}")
    
    # Run initial processing
    try:
        subprocess.run([
            sys.executable, "chatmind/data_ingestion/extract_and_flatten.py"
        ], check=True)
        
        new_count = count_chats()
        print(f"After processing: {new_count} chats")
        print(f"Added: {new_count - initial_count} new chats")
        
    except subprocess.CalledProcessError:
        print("❌ No data to process or processing failed")
        print("💡 Place some ChatGPT export ZIP files in data/raw/ to continue")
        return
    
    print_separator("Step 2: Demonstrate Incremental Processing")
    print("Now let's run the same command again to show incremental behavior...")
    
    before_count = count_chats()
    print(f"Chats before re-processing: {before_count}")
    
    # Run processing again (should be incremental)
    start_time = time.time()
    subprocess.run([
        sys.executable, "chatmind/data_ingestion/extract_and_flatten.py"
    ], check=True)
    end_time = time.time()
    
    after_count = count_chats()
    print(f"Chats after re-processing: {after_count}")
    print(f"Processing time: {end_time - start_time:.2f} seconds")
    
    if after_count == before_count:
        print("✅ No new chats added - incremental processing worked!")
    else:
        print(f"📈 Added {after_count - before_count} new chats")
    
    print_separator("Step 3: State Files")
    print("The system maintains content hashes to track unique chats:")
    
    hash_file = Path("data/processed/content_hashes.pkl")
    if hash_file.exists():
        import pickle
        with open(hash_file, 'rb') as f:
            hashes = pickle.load(f)
        print(f"✅ content_hashes.pkl: {len(hashes)} unique content hashes")
    else:
        print(f"❌ content_hashes.pkl: Not found")
    
    print_separator("Step 4: Force Reprocessing")
    print("You can force reprocessing with the --force flag:")
    print("python chatmind/data_ingestion/extract_and_flatten.py --force")
    
    print_separator("Step 5: Clear State")
    print("You can clear all state and start fresh with:")
    print("python chatmind/data_ingestion/extract_and_flatten.py --clear-state")
    
    print_separator("How It Works")
    print("""
🔍 Content-Based Deduplication Strategy:
1. Content Hashing: Each chat is hashed using SHA256 of normalized content
2. Smart Normalization: Excludes timestamps and metadata that change between exports
3. Content Matching: Only truly unique conversations are added to the database
4. Persistent State: Content hashes are saved between runs

📊 Benefits:
- Handles overlapping exports (same conversations in different ZIP files)
- No duplicate data in the knowledge graph
- Works with ChatGPT's full-history exports
- Maintains data integrity across multiple runs

🛠️ Usage Examples:
- Add new exports: Place ZIP files in data/raw/ and run the pipeline
- Force reprocess: Use --force flag to reprocess all files
- Fresh start: Use --clear-state to reset all content tracking
    """)

if __name__ == "__main__":
    main() 