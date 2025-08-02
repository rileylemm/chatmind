#!/usr/bin/env python3
"""
Test script to debug hash matching between chunks and processed tags.
"""

import jsonlines
import json
import hashlib

def test_hash_matching():
    # Load processed tags
    processed_tags = {}
    with open('data/processed/tagging/processed_tags.jsonl') as f:
        for line in f:
            data = json.loads(line)
            processed_tags[data['message_hash']] = data
    
    print(f"Loaded {len(processed_tags)} processed tags")
    
    # Load chunks and test matching
    chunks = []
    with open('data/processed/chunking/chunks.jsonl') as f:
        for line in f:
            chunks.append(json.loads(line))
    
    print(f"Loaded {len(chunks)} chunks")
    
    # Test all chunks
    matched = 0
    total = len(chunks)
    
    for i, chunk in enumerate(chunks):
        if i % 1000 == 0:
            print(f"Processing chunk {i}/{total}...")
            
        message_data = {
            'content': chunk['content'],
            'chat_id': chunk['chat_id'],
            'message_id': chunk['message_ids'][0],
            'role': chunk['role']
        }
        message_hash = hashlib.sha256(json.dumps(message_data, sort_keys=True).encode()).hexdigest()
        
        if message_hash in processed_tags:
            matched += 1
    
    print(f"\nFinal results:")
    print(f"Matched {matched}/{total} chunks ({matched/total*100:.1f}%)")
    
    # Check if any processed tag hashes exist in our test
    processed_hashes = set(processed_tags.keys())
    test_hashes = set()
    for chunk in chunks:
        message_data = {
            'content': chunk['content'],
            'chat_id': chunk['chat_id'],
            'message_id': chunk['message_ids'][0],
            'role': chunk['role']
        }
        message_hash = hashlib.sha256(json.dumps(message_data, sort_keys=True).encode()).hexdigest()
        test_hashes.add(message_hash)
    
    intersection = processed_hashes.intersection(test_hashes)
    print(f"Hash intersection: {len(intersection)} out of {len(test_hashes)} unique chunk hashes")
    print(f"Unique processed hashes: {len(processed_hashes)}")
    print(f"Unique chunk hashes: {len(test_hashes)}")

if __name__ == "__main__":
    test_hash_matching() 