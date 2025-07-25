#!/usr/bin/env python3
"""
Tag Post-Processing for ChatMind

Maps unconstrained tags to master list, tracks missing tags,
and provides mechanisms for auto-adding good tags.
"""

import json
import jsonlines
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging
from collections import Counter
import click

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TagPostProcessor:
    """Post-processes tags to map to master list and track missing tags."""
    
    def __init__(self, master_list_path: str = "data/tags/tags_master_list.json"):
        self.master_list_path = Path(master_list_path)
        self.master_tags = self.load_master_tags()
        self.missing_tags = Counter()
        self.mapped_tags = Counter()
        
    def load_master_tags(self) -> Set[str]:
        """Load master tag list."""
        if not self.master_list_path.exists():
            logger.error(f"Master tag list not found: {self.master_list_path}")
            return set()
        
        with open(self.master_list_path, 'r') as f:
            master_tags = json.load(f)
        
        # Normalize master tags for comparison
        normalized_master = {self.normalize_tag(tag) for tag in master_tags}
        logger.info(f"Loaded {len(normalized_master)} master tags")
        return normalized_master
    
    def normalize_tag(self, tag: str) -> str:
        """Normalize tag for comparison."""
        # Remove leading/trailing whitespace
        tag = tag.strip()
        
        # Ensure single # prefix
        if not tag.startswith('#'):
            tag = '#' + tag
        elif tag.startswith('##'):
            tag = '#' + tag[2:]
        
        # Convert to lowercase
        tag = tag.lower()
        
        # Replace underscores with hyphens
        tag = tag.replace('_', '-')
        
        return tag
    
    def find_best_match(self, tag: str, master_tags: Set[str]) -> str:
        """Find the best matching tag in master list."""
        normalized_tag = self.normalize_tag(tag)
        
        # Exact match
        if normalized_tag in master_tags:
            return normalized_tag
        
        # Partial matches (tag contains master tag or vice versa)
        for master_tag in master_tags:
            if normalized_tag in master_tag or master_tag in normalized_tag:
                return master_tag
        
        # No match found
        return None
    
    def process_chunk_tags(self, chunk: Dict) -> Dict:
        """Process tags for a single chunk."""
        original_tags = chunk.get('tags', [])
        processed_tags = []
        
        for tag in original_tags:
            best_match = self.find_best_match(tag, self.master_tags)
            
            if best_match:
                processed_tags.append(best_match)
                self.mapped_tags[best_match] += 1
            else:
                # Track missing tag
                normalized_missing = self.normalize_tag(tag)
                self.missing_tags[normalized_missing] += 1
                # Keep original tag for now
                processed_tags.append(tag)
        
        # Update chunk with processed tags
        processed_chunk = {
            **chunk,
            'tags': processed_tags,
            'original_tags': original_tags,
            'tags_mapped': len([t for t in original_tags if self.find_best_match(t, self.master_tags) is not None]),
            'tags_unmapped': len([t for t in original_tags if self.find_best_match(t, self.master_tags) is None])
        }
        
        return processed_chunk
    
    def process_file(self, input_file: Path, output_file: Path) -> Dict:
        """Process all chunks in a file."""
        logger.info(f"Processing tags in {input_file}")
        
        processed_chunks = []
        total_chunks = 0
        total_mapped = 0
        total_unmapped = 0
        
        with jsonlines.open(input_file) as reader:
            for chunk in reader:
                processed_chunk = self.process_chunk_tags(chunk)
                processed_chunks.append(processed_chunk)
                total_chunks += 1
                total_mapped += processed_chunk['tags_mapped']
                total_unmapped += processed_chunk['tags_unmapped']
        
        # Save processed chunks
        with jsonlines.open(output_file, 'w') as writer:
            for chunk in processed_chunks:
                writer.write(chunk)
        
        logger.info(f"Processed {total_chunks} chunks")
        logger.info(f"Total tags mapped: {total_mapped}")
        logger.info(f"Total tags unmapped: {total_unmapped}")
        
        return {
            'total_chunks': total_chunks,
            'total_mapped': total_mapped,
            'total_unmapped': total_unmapped,
            'missing_tags': dict(self.missing_tags),
            'mapped_tags': dict(self.mapped_tags)
        }
    
    def save_missing_tags_report(self, output_file: Path):
        """Save report of missing tags for review."""
        if not self.missing_tags:
            logger.info("No missing tags to report")
            return
        
        report = {
            'missing_tags': dict(self.missing_tags),
            'total_missing_occurrences': sum(self.missing_tags.values()),
            'unique_missing_tags': len(self.missing_tags)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Missing tags report saved to {output_file}")
        logger.info(f"Found {len(self.missing_tags)} unique missing tags")
        logger.info(f"Total missing tag occurrences: {sum(self.missing_tags.values())}")
    
    def suggest_auto_additions(self, min_occurrences: int = 3) -> List[str]:
        """Suggest tags to auto-add based on frequency."""
        suggestions = []
        
        for tag, count in self.missing_tags.most_common():
            if count >= min_occurrences:
                suggestions.append(tag)
        
        return suggestions
    
    def auto_add_suggested_tags(self, min_occurrences: int = 3):
        """Automatically add frequently occurring missing tags to master list."""
        suggestions = self.suggest_auto_additions(min_occurrences)
        
        if not suggestions:
            logger.info("No tags meet the minimum occurrence threshold for auto-addition")
            return
        
        # Load current master list
        with open(self.master_list_path, 'r') as f:
            master_tags = json.load(f)
        
        # Add suggested tags
        added_tags = []
        for tag in suggestions:
            if tag not in master_tags:
                master_tags.append(tag)
                added_tags.append(tag)
        
        # Save updated master list
        with open(self.master_list_path, 'w') as f:
            json.dump(master_tags, f, indent=2)
        
        logger.info(f"Auto-added {len(added_tags)} tags to master list: {added_tags}")
        
        # Reload master tags
        self.master_tags = self.load_master_tags()


@click.command()
@click.option('--input-file', 
              default='data/processed/tagged_chunks.jsonl',
              help='Input file with tagged chunks')
@click.option('--output-file', 
              default='data/processed/processed_tagged_chunks.jsonl',
              help='Output file for processed chunks')
@click.option('--missing-report', 
              default='data/interim/missing_tags_report.json',
              help='Report file for missing tags')
@click.option('--auto-add-threshold', 
              default=3,
              help='Minimum occurrences to auto-add tag')
@click.option('--auto-add', is_flag=True,
              help='Automatically add frequently occurring missing tags')
def main(input_file: str, output_file: str, missing_report: str, 
         auto_add_threshold: int, auto_add: bool):
    """Post-process tags to map to master list."""
    
    processor = TagPostProcessor()
    
    # Process the file
    stats = processor.process_file(Path(input_file), Path(output_file))
    
    # Save missing tags report
    processor.save_missing_tags_report(Path(missing_report))
    
    # Auto-add if requested
    if auto_add:
        processor.auto_add_suggested_tags(auto_add_threshold)
    
    # Print summary
    print(f"\n📊 Tag Processing Summary:")
    print(f"  - Total chunks processed: {stats['total_chunks']}")
    print(f"  - Tags successfully mapped: {stats['total_mapped']}")
    print(f"  - Tags that couldn't be mapped: {stats['total_unmapped']}")
    print(f"  - Unique missing tags: {len(stats['missing_tags'])}")
    
    if stats['missing_tags']:
        print(f"\n🔍 Top missing tags:")
        for tag, count in sorted(stats['missing_tags'].items(), 
                                key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {tag}: {count} occurrences")


if __name__ == "__main__":
    main() 