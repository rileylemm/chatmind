#!/usr/bin/env python3
"""
Pipeline Dependency Checker

Checks if all required dependencies for the ChatMind pipeline are installed.
"""

import importlib
import sys
from pathlib import Path

def check_dependency(module_name: str, package_name: str = None) -> bool:
    """Check if a dependency is available."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def main():
    """Check all pipeline dependencies."""
    print("🔍 Checking ChatMind pipeline dependencies...")
    print("=" * 50)
    
    # Core dependencies
    core_deps = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("jsonlines", "jsonlines"),
        ("click", "click"),
        ("tqdm", "tqdm"),
    ]
    
    # ML/AI dependencies
    ml_deps = [
        ("sentence_transformers", "sentence-transformers"),
        ("sklearn", "scikit-learn"),
        ("hdbscan", "hdbscan"),
        ("umap", "umap-learn"),
    ]
    
    # Optional dependencies
    optional_deps = [
        ("openai", "openai"),
        ("requests", "requests"),
    ]
    
    all_good = True
    
    print("📦 Core Dependencies:")
    for module, package in core_deps:
        if check_dependency(module):
            print(f"  ✅ {package}")
        else:
            print(f"  ❌ {package} - MISSING")
            all_good = False
    
    print("\n🤖 ML/AI Dependencies:")
    for module, package in ml_deps:
        if check_dependency(module):
            print(f"  ✅ {package}")
        else:
            print(f"  ❌ {package} - MISSING")
            all_good = False
    
    print("\n🔧 Optional Dependencies:")
    for module, package in optional_deps:
        if check_dependency(module):
            print(f"  ✅ {package}")
        else:
            print(f"  ⚠️  {package} - Optional (for cloud API)")
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("🎉 All required dependencies are installed!")
        print("✅ You can run the pipeline with: python run_pipeline.py")
    else:
        print("❌ Some dependencies are missing.")
        print("💡 Install missing dependencies with:")
        print("   pip install -r chatmind/pipeline/requirements.txt")
    
    # Check for external tools
    print("\n🔧 External Tools:")
    
    # Check Ollama
    try:
        import subprocess
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Ollama (for local models)")
        else:
            print("  ❌ Ollama - not found")
    except FileNotFoundError:
        print("  ❌ Ollama - not found")
    
    # Check Neo4j
    try:
        import subprocess
        result = subprocess.run(["neo4j", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Neo4j (for graph database)")
        else:
            print("  ⚠️  Neo4j - not found (optional for pipeline)")
    except FileNotFoundError:
        print("  ⚠️  Neo4j - not found (optional for pipeline)")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    exit(main()) 