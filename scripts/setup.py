#!/usr/bin/env python3
"""
ChatMind Setup Script

Helps users set up the ChatMind project for the first time.
"""

import os
import sys
import subprocess
from pathlib import Path
import click

@click.command()
@click.option('--skip-frontend', is_flag=True, help='Skip frontend setup')
@click.option('--skip-neo4j', is_flag=True, help='Skip Neo4j setup instructions')
def main(skip_frontend: bool, skip_neo4j: bool):
    """Setup ChatMind project."""
    
    print("🚀 Welcome to ChatMind Setup!")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create necessary directories
    directories = [
        "data/raw",
        "data/processed", 
        "data/embeddings"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Install Python dependencies
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Python dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        sys.exit(1)
    
    # Setup environment file
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\n🔧 Setting up environment variables...")
        try:
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env file from template")
            print("📝 Please edit .env with your Neo4j credentials")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️ No env.example found, please create .env manually")
    
    # Setup frontend
    if not skip_frontend:
        frontend_dir = Path("chatmind/frontend")
        if frontend_dir.exists():
            print("\n🎨 Setting up frontend...")
            try:
                # Check if npm is available
                subprocess.run(["npm", "--version"], check=True, capture_output=True)
                print("✅ npm detected")
                
                # Install frontend dependencies
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
                print("✅ Frontend dependencies installed")
            except subprocess.CalledProcessError:
                print("❌ Failed to install frontend dependencies")
                print("💡 Make sure Node.js and npm are installed")
            except FileNotFoundError:
                print("❌ npm not found")
                print("💡 Please install Node.js and npm first")
        else:
            print("⚠️ Frontend directory not found")
    
    # Neo4j setup instructions
    if not skip_neo4j:
        print("\n🗄️ Neo4j Setup Instructions:")
        print("1. Install Neo4j Desktop or use Docker:")
        print("   docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest")
        print("2. Access Neo4j Browser at http://localhost:7474")
        print("3. Default credentials: neo4j/password")
        print("4. Update .env file with your Neo4j connection details")
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Place ChatGPT export ZIP files in data/raw/")
    print("2. Run: python run_pipeline.py")
    print("3. Run: python start_services.py")
    print("4. Open http://localhost:3000 in your browser")
    
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main() 