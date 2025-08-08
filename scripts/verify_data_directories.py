#!/usr/bin/env python3
"""
Data Directory Verification Script

Verifies that all required data directories exist and are properly set up
for the ChatMind pipeline.
"""

import os
from pathlib import Path
import click

@click.command()
def main():
    """Verify all required data directories exist."""
    
    # Required directories from our documentation
    required_dirs = [
        # Core data directories
        "data/raw",
        "data/processed",
        "data/interim",
        "data/tags_masterlist",
        
        # Pipeline step directories
        "data/processed/ingestion",
        "data/processed/chunking", 
        "data/processed/embedding",
        "data/processed/clustering",
        "data/processed/tagging",
        "data/processed/cluster_summarization",
        "data/processed/chat_summarization",
        "data/processed/positioning",
        "data/processed/similarity",
        
        # Data lake directories
        "data/lake",
        "data/lake/raw",
        "data/lake/processed", 
        "data/lake/interim",
        
        # Backup directories (optional)
        "data/backup_old_data",
    ]
    
    print("🔍 Verifying data directory structure...")
    print("=" * 50)
    
    all_exist = True
    missing_dirs = []
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - MISSING")
            missing_dirs.append(dir_path)
            all_exist = False
    
    print("=" * 50)
    
    if all_exist:
        print("🎉 All required data directories exist!")
    else:
        print(f"⚠️  {len(missing_dirs)} directories are missing:")
        for missing in missing_dirs:
            print(f"   - {missing}")
        print("\nRun the following command to create missing directories:")
        print("mkdir -p " + " ".join(missing_dirs))
    
    # Check for additional backup directories
    backup_dirs = [d for d in Path("data").iterdir() if d.name.startswith("backup_")]
    if backup_dirs:
        print(f"\n📦 Found {len(backup_dirs)} backup directories:")
        for backup in backup_dirs:
            print(f"   - {backup}")
    
    return 0 if all_exist else 1

if __name__ == "__main__":
    exit(main()) 