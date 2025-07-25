#!/usr/bin/env python3
"""
ChatMind API Runner

Simple script to start the ChatMind API server.
"""

import uvicorn
import os
from pathlib import Path

def main():
    """Start the ChatMind API server"""
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Change to the script directory to ensure relative imports work
    os.chdir(script_dir)
    
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    
    print(f"Starting ChatMind API on {host}:{port}")
    print(f"Reload mode: {reload}")
    print(f"API docs will be available at: http://{host}:{port}/docs")
    
    # Start the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main() 