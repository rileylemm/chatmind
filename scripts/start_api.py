#!/usr/bin/env python3
"""
Start ChatMind API from project root
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the ChatMind API"""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    api_dir = project_root / "chatmind" / "api"
    
    # Check if API directory exists
    if not api_dir.exists():
        print(f"❌ API directory not found: {api_dir}")
        sys.exit(1)
    
    # Change to API directory
    os.chdir(api_dir)
    
    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
        print("✅ Dependencies found")
    except ImportError:
        print("📦 Installing API dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Set environment variables
    env = os.environ.copy()
    env.setdefault("API_HOST", "0.0.0.0")
    env.setdefault("API_PORT", "8000")
    env.setdefault("API_RELOAD", "true")
    
    print("🚀 Starting ChatMind API...")
    print(f"   Host: {env['API_HOST']}")
    print(f"   Port: {env['API_PORT']}")
    print(f"   Reload: {env['API_RELOAD']}")
    print("   API docs: http://localhost:8000/docs")
    print("   Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    
    # Start the API
    try:
        subprocess.run([sys.executable, "run.py"], env=env)
    except KeyboardInterrupt:
        print("\n👋 API stopped")

if __name__ == "__main__":
    main() 