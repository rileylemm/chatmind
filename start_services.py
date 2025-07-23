#!/usr/bin/env python3
"""
ChatMind Service Starter

Starts the API server and optionally the frontend development server.
"""

import subprocess
import sys
import time
import signal
import os
from pathlib import Path
import click
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global process references
api_process = None
frontend_process = None


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info("🛑 Shutting down services...")
    
    if api_process:
        api_process.terminate()
        logger.info("✅ API server stopped")
    
    if frontend_process:
        frontend_process.terminate()
        logger.info("✅ Frontend server stopped")
    
    sys.exit(0)


@click.command()
@click.option('--api-only', is_flag=True, help='Start only the API server')
@click.option('--frontend-only', is_flag=True, help='Start only the frontend server')
@click.option('--api-port', default=8000, help='API server port')
@click.option('--frontend-port', default=3000, help='Frontend server port')
def main(api_only: bool, frontend_only: bool, api_port: int, frontend_port: int):
    """Start ChatMind services."""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting ChatMind services...")
    
    # Start API server
    if not frontend_only:
        logger.info(f"🌐 Starting API server on port {api_port}...")
        try:
            api_process = subprocess.Popen([
                sys.executable, "chatmind/api/main.py"
            ])
            logger.info("✅ API server started")
        except Exception as e:
            logger.error(f"❌ Failed to start API server: {e}")
            return 1
    
    # Start frontend server
    if not api_only:
        logger.info(f"🎨 Starting frontend server on port {frontend_port}...")
        try:
            frontend_dir = Path("chatmind/frontend")
            if not frontend_dir.exists():
                logger.error("❌ Frontend directory not found. Run 'npm install' first.")
                return 1
            
            frontend_process = subprocess.Popen([
                "npm", "start"
            ], cwd=frontend_dir)
            logger.info("✅ Frontend server started")
        except Exception as e:
            logger.error(f"❌ Failed to start frontend server: {e}")
            return 1
    
    logger.info("")
    logger.info("🎉 Services started successfully!")
    logger.info("")
    if not frontend_only:
        logger.info(f"📡 API: http://localhost:{api_port}")
        logger.info("📖 API docs: http://localhost:8000/docs")
    if not api_only:
        logger.info(f"🌐 Frontend: http://localhost:{frontend_port}")
    logger.info("")
    logger.info("Press Ctrl+C to stop all services")
    
    try:
        # Wait for processes
        if api_process:
            api_process.wait()
        if frontend_process:
            frontend_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    sys.exit(main()) 