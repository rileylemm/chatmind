#!/usr/bin/env python3
"""
Extract tag frequencies from tagged semantic chunks.

Loads all tagged chunks from data/processed/tagged_chunks.jsonl,
normalizes and counts tag occurrences, and writes the frequencies
as JSON to data/interim/tag_frequencies.json.
"""

import sys
import json
from pathlib import Path

def main():
    # Define input and output paths
    input_path = Path("data/processed/tagged_chunks.jsonl")
    output_path = Path("data/interim/tag_frequencies.json")

    # Check that input exists
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Count normalized tag frequencies
    tag_counts = {}
    # Read JSONL line by line
    with input_path.open('r') as f:
        for line in f:
            record = json.loads(line)
            tags = record.get('tags', []) or []
            for tag in tags:
                # Normalize to lowercase and replace underscores with hyphens
                norm = tag.lower().replace('_', '-')
                tag_counts[norm] = tag_counts.get(norm, 0) + 1

    # Write out frequencies as JSON
    with output_path.open('w') as f:
        json.dump(tag_counts, f, indent=2)

    print(f"Saved {len(tag_counts)} tag frequencies to {output_path}")

if __name__ == '__main__':
    main()