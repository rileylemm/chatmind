#!/usr/bin/env python3
"""
Optimized Tag Post-Processing for ChatMind with Gemma-2B

Maps unconstrained tags to master list, tracks missing tags,
and provides mechanisms for auto-adding good tags.
Updated for message-level tagging in the new pipeline structure.
"""

import json
import jsonlines
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging
from collections import Counter
import click
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GemmaOptimizedTagPostProcessor:
    """Post-processes tags optimized for Gemma-2B's clean output."""
    
    def __init__(self, master_list_path: str = "../../data/tags_masterlist/tags_master_list.json"):
        self.master_list_path = Path(master_list_path)
        self.master_tags = self.load_master_tags()
        self.missing_tags = Counter()
        self.mapped_tags = Counter()
        self.domain_fixes = Counter()
        
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
    
    def fix_domain_field(self, domain: str) -> str:
        """Fix Gemma-2B's domain field which sometimes includes the full enum."""
        if not domain:
            return "unknown"
        
        # Gemma sometimes returns the full enum string instead of a single value
        if "|" in domain:
            # Extract the first valid domain from the enum
            domains = domain.split("|")
            for d in domains:
                d = d.strip().lower()
                if d in ["technical", "personal", "medical", "business", "creative"]:
                    return d
            return "unknown"
        
        # Normalize single domain
        domain = domain.strip().lower()
        if domain in ["technical", "personal", "medical", "business", "creative"]:
            return domain
        
        return "unknown"
    
    def find_best_match(self, tag: str, master_tags: Set[str]) -> str:
        """Find the best matching tag in master list."""
        normalized_tag = self.normalize_tag(tag)
        
        # Exact match (master list is already normalized)
        if normalized_tag in master_tags:
            return normalized_tag
        
        # Try to find semantic matches by removing hyphens/underscores/spaces
        # This handles cases like #webdev -> #web-dev
        semantic_normalized = re.sub(r'[-_\s]+', '', normalized_tag)
        
        for master_tag in master_tags:
            master_semantic = re.sub(r'[-_\s]+', '', master_tag)
            if semantic_normalized == master_semantic:
                return master_tag
        
        # No match found - return the normalized tag
        return normalized_tag
    
    def process_message_tags(self, message: Dict) -> Dict:
        """Process tags for a single message."""
        original_tags = message.get('tags', [])
        processed_tags = []
        tags_mapped = 0
        tags_unmapped = 0
        
        # Process each tag
        for tag in original_tags:
            if not tag or tag.strip() == '':
                continue
                
            # Find best match in master list
            mapped_tag = self.find_best_match(tag, self.master_tags)
            
            # Check if the mapped tag is in the master list (could be semantic match)
            if mapped_tag in self.master_tags:
                # Tag mapped to master list
                self.mapped_tags[mapped_tag] += 1
                tags_mapped += 1
                processed_tags.append(mapped_tag)
            else:
                # Tag not in master list
                self.missing_tags[tag] += 1
                tags_unmapped += 1
                processed_tags.append(mapped_tag)  # Use normalized version
        
        # Fix domain field
        original_domain = message.get('domain', 'unknown')
        fixed_domain = self.fix_domain_field(original_domain)
        if fixed_domain != original_domain:
            self.domain_fixes[original_domain] += 1
        
        # Create processed message
        processed_message = {
            **message,
            'tags': processed_tags,
            'domain': fixed_domain,
            'tags_mapped': tags_mapped,
            'tags_unmapped': tags_unmapped,
            'original_tags': original_tags  # Keep for reference
        }
        
        return processed_message
    
    def process_file(self, input_file: Path, output_file: Path, force: bool = False) -> Dict:
        """Process all messages in a file with incremental processing support."""
        logger.info(f"Processing tags in {input_file}")
        
        # Load existing processed messages if file exists and not forcing
        existing_processed = {}
        if output_file.exists() and not force:
            logger.info(f"Loading existing processed data from {output_file}")
            with jsonlines.open(output_file, 'r') as reader:
                for message in reader:
                    message_hash = message.get('message_hash', '')
                    if message_hash:
                        existing_processed[message_hash] = message
            logger.info(f"Loaded {len(existing_processed)} existing processed messages")
        
        processed_messages = []
        total_messages = 0
        total_mapped = 0
        total_unmapped = 0
        domain_fixes_count = 0
        new_messages = 0
        skipped_messages = 0
        
        with jsonlines.open(input_file) as reader:
            for message in reader:
                message_hash = message.get('message_hash', '')
                
                # Skip if already processed (unless forcing)
                if message_hash in existing_processed and not force:
                    skipped_messages += 1
                    continue
                
                processed_message = self.process_message_tags(message)
                processed_messages.append(processed_message)
                total_messages += 1
                total_mapped += processed_message['tags_mapped']
                total_unmapped += processed_message['tags_unmapped']
                new_messages += 1
                
                # Count domain fixes
                if processed_message.get('domain') != message.get('domain'):
                    domain_fixes_count += 1
        
        # Combine existing and new processed messages
        all_processed_messages = list(existing_processed.values()) + processed_messages
        
        # Save all processed messages
        with jsonlines.open(output_file, 'w') as writer:
            for message in all_processed_messages:
                writer.write(message)
        
        logger.info(f"Processed {new_messages} new messages")
        logger.info(f"Skipped {skipped_messages} already processed messages")
        logger.info(f"Total messages in file: {len(all_processed_messages)}")
        logger.info(f"New tags mapped: {total_mapped}")
        logger.info(f"New tags unmapped: {total_unmapped}")
        logger.info(f"Domain fields fixed: {domain_fixes_count}")
        
        return {
            'new_messages': new_messages,
            'skipped_messages': skipped_messages,
            'total_messages_in_file': len(all_processed_messages),
            'total_mapped': total_mapped,
            'total_unmapped': total_unmapped,
            'domain_fixes': domain_fixes_count,
            'missing_tags': dict(self.missing_tags),
            'mapped_tags': dict(self.mapped_tags),
            'domain_fixes_breakdown': dict(self.domain_fixes)
        }
    
    def save_missing_tags_report(self, output_file: Path):
        """Save report of missing tags for review."""
        if not self.missing_tags:
            logger.info("No missing tags to report")
            return
        
        report = {
            'missing_tags': dict(self.missing_tags),
            'total_missing_occurrences': sum(self.missing_tags.values()),
            'unique_missing_tags': len(self.missing_tags),
            'domain_fixes': dict(self.domain_fixes)
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Missing tags report saved to {output_file}")
        logger.info(f"Found {len(self.missing_tags)} unique missing tags")
        logger.info(f"Total missing tag occurrences: {sum(self.missing_tags.values())}")
        logger.info(f"Domain fixes: {sum(self.domain_fixes.values())}")
    
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
        
        # Add suggested tags (normalized)
        added_tags = []
        for tag in suggestions:
            normalized_tag = self.normalize_tag(tag)
            if normalized_tag not in master_tags:
                master_tags.append(normalized_tag)
                added_tags.append(normalized_tag)
        
        # Save updated master list
        with open(self.master_list_path, 'w') as f:
            json.dump(master_tags, f, indent=2)
        
        logger.info(f"Auto-added {len(added_tags)} tags to master list: {added_tags}")
        
        # Reload master tags
        self.master_tags = self.load_master_tags()


@click.command()
@click.option('--input-file', 
              default='../../data/processed/tagging/tags.jsonl',
              help='Input file with tagged messages')
@click.option('--output-file', 
              default='../../data/processed/tagging/processed_tags.jsonl',
              help='Output file for processed messages')
@click.option('--missing-report', 
              default='../../data/processed/tagging/missing_tags_report.json',
              help='Report file for missing tags')
@click.option('--auto-add-threshold', 
              default=3,
              help='Minimum occurrences to auto-add tag')
@click.option('--auto-add', is_flag=True,
              help='Automatically add frequently occurring missing tags')
@click.option('--force', is_flag=True,
              help='Force reprocess all messages (overwrite existing)')
@click.option('--check-only', is_flag=True,
              help='Only check setup, don\'t process')
def main(input_file: str, output_file: str, missing_report: str, 
         auto_add_threshold: int, auto_add: bool, force: bool, check_only: bool):
    """Post-process tags optimized for Gemma-2B output."""
    
    if check_only:
        logger.info("🔍 Checking post-processing setup...")
        
        # Check input file
        input_path = Path(input_file)
        if input_path.exists():
            logger.info(f"✅ Input file exists: {input_file}")
        else:
            logger.error(f"❌ Input file not found: {input_file}")
            return 1
        
        # Check master tag list
        master_list_path = Path("data/tags_masterlist/tags_master_list.json")
        if master_list_path.exists():
            logger.info(f"✅ Master tag list exists: {master_list_path}")
        else:
            logger.error(f"❌ Master tag list not found: {master_list_path}")
            return 1
        
        # Check output directory
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Output directory ready: {output_path.parent}")
        
        logger.info("✅ Post-processing setup looks good!")
        return 0
    
    # Initialize processor
    processor = GemmaOptimizedTagPostProcessor()
    
    # Process the file
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_file}")
        return 1
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Process the file
    stats = processor.process_file(input_path, output_path, force=force)
    
    # Auto-add tags if requested (before saving report)
    if auto_add:
        processor.auto_add_suggested_tags(auto_add_threshold)
    
    # Save missing tags report (after auto-add)
    missing_report_path = Path(missing_report)
    missing_report_path.parent.mkdir(parents=True, exist_ok=True)
    processor.save_missing_tags_report(missing_report_path)
    
    # Print summary
    logger.info("")
    logger.info("📊 Post-processing Summary:")
    logger.info(f"  New messages processed: {stats['new_messages']}")
    logger.info(f"  Messages skipped (already processed): {stats['skipped_messages']}")
    logger.info(f"  Total messages in file: {stats['total_messages_in_file']}")
    logger.info(f"  New tags mapped to master list: {stats['total_mapped']}")
    logger.info(f"  New tags not in master list: {stats['total_unmapped']}")
    logger.info(f"  Domain fields fixed: {stats['domain_fixes']}")
    logger.info(f"  Unique missing tags: {len(stats['missing_tags'])}")
    
    if stats['missing_tags']:
        logger.info("")
        logger.info("🔍 Top missing tags:")
        for tag, count in sorted(stats['missing_tags'].items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {tag}: {count} occurrences")
    
    logger.info("")
    logger.info("✅ Post-processing completed successfully!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 