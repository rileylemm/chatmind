#!/usr/bin/env python3
"""
Tag Setup Script for ChatMind

This script helps new users set up their personal tag list from the generic template.
"""

import json
import shutil
from pathlib import Path
import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_personal_tags():
    """Set up personal tag list from generic template."""
    
    generic_file = Path("data/tags/tags_master_list_generic.json")
    personal_file = Path("data/tags_masterlist/tags_master_list.json")
    
    # Check if generic file exists
    if not generic_file.exists():
        logger.error(f"Generic tag list not found: {generic_file}")
        logger.error("Please ensure you have the generic tag list file.")
        return False
    
    # Check if personal file already exists
    if personal_file.exists():
        logger.warning(f"Personal tag list already exists: {personal_file}")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            logger.info("Setup cancelled. Your existing tag list is preserved.")
            return True
    
    # Create data/tags directory if it doesn't exist
    personal_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Copy generic file to personal file
    try:
        shutil.copy2(generic_file, personal_file)
        logger.info(f"✅ Created personal tag list: {personal_file}")
        
        # Load and display some info about the tags
        with open(personal_file, 'r') as f:
            tags = json.load(f)
        
        logger.info(f"📊 Tag list contains {len(tags)} tags")
        logger.info("🎯 You can now customize this list to match your interests!")
        logger.info("💡 The pipeline will suggest new tags based on your content.")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create personal tag list: {e}")
        return False


def show_tag_info():
    """Show information about the current tag setup."""
    
    generic_file = Path("data/tags/tags_master_list_generic.json")
    personal_file = Path("data/tags_masterlist/tags_master_list.json")
    
    print("\n📋 Tag List Status:")
    print(f"  Generic tags: {'✅' if generic_file.exists() else '❌'} {generic_file}")
    print(f"  Personal tags: {'✅' if personal_file.exists() else '❌'} {personal_file}")
    
    if personal_file.exists():
        with open(personal_file, 'r') as f:
            tags = json.load(f)
        print(f"  Personal tag count: {len(tags)}")
        
        # Show some sample tags
        print(f"  Sample tags: {', '.join(tags[:5])}...")
    
    print("\n🔒 Privacy: Your personal tag list is excluded from git")
    print("📦 Generic tags are included in the repository for new users")


@click.command()
@click.option('--info', is_flag=True, help='Show current tag setup information')
def main(info: bool):
    """Set up personal tag list for ChatMind."""
    
    if info:
        show_tag_info()
        return
    
    print("🚀 Setting up personal tag list for ChatMind...")
    print("This will create your personal tag list from the generic template.")
    print("You can then customize it to match your interests.\n")
    
    success = setup_personal_tags()
    
    if success:
        print("\n✅ Tag setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit data/tags_masterlist/tags_master_list.json to customize your tags")
        print("2. Run the pipeline: python run_pipeline.py")
        print("3. Check data/interim/missing_tags_report.json for suggested new tags")
    else:
        print("\n❌ Tag setup failed. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    exit(main()) 