#!/usr/bin/env python3
"""
Pipeline Virtual Environment Setup

Creates a dedicated virtual environment for the ChatMind pipeline.
This allows for isolated pipeline development and deployment.
"""

import subprocess
import sys
import os
from pathlib import Path
import click

@click.command()
@click.option('--venv-name', default='pipeline_env', help='Name of the virtual environment')
@click.option('--force', is_flag=True, help='Force recreate virtual environment')
@click.option('--check-only', is_flag=True, help='Only check if venv exists')
def main(venv_name: str, force: bool, check_only: bool):
    """Set up a pipeline-specific virtual environment."""
    
    pipeline_dir = Path("chatmind/pipeline")
    venv_path = pipeline_dir / venv_name
    
    print("🔧 ChatMind Pipeline Virtual Environment Setup")
    print("=" * 50)
    
    # Check if venv already exists
    if venv_path.exists() and not force:
        if check_only:
            print(f"✅ Pipeline virtual environment exists: {venv_path}")
            return 0
        else:
            print(f"⚠️  Virtual environment already exists: {venv_path}")
            print("   Use --force to recreate it")
            return 1
    
    # Create virtual environment
    print(f"📦 Creating virtual environment: {venv_path}")
    
    try:
        subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], check=True)
        print("✅ Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return 1
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate"
        pip_path = venv_path / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    # Install dependencies
    print("📥 Installing pipeline dependencies...")
    
    try:
        subprocess.run([
            str(pip_path), "install", "-r", str(pipeline_dir / "requirements.txt")
        ], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return 1
    
    # Create activation script
    activation_script = pipeline_dir / "activate_pipeline.sh"
    if os.name != 'nt':  # Unix/Linux/macOS
        with open(activation_script, 'w') as f:
            f.write(f"""#!/bin/bash
# ChatMind Pipeline Virtual Environment Activation Script

echo "🔧 Activating ChatMind Pipeline Virtual Environment..."
source {venv_path}/bin/activate

echo "✅ Pipeline virtual environment activated!"
echo "📦 Installed packages:"
pip list

echo ""
echo "🚀 You can now run pipeline commands:"
echo "   python run_pipeline.py --help"
echo ""
echo "💡 To deactivate: deactivate"
""")
        os.chmod(activation_script, 0o755)
    
    # Create Windows activation script
    activation_bat = pipeline_dir / "activate_pipeline.bat"
    if os.name == 'nt':  # Windows
        with open(activation_bat, 'w') as f:
            f.write(f"""@echo off
REM ChatMind Pipeline Virtual Environment Activation Script

echo 🔧 Activating ChatMind Pipeline Virtual Environment...
call {venv_path}\\Scripts\\activate.bat

echo ✅ Pipeline virtual environment activated!
echo 📦 Installed packages:
pip list

echo.
echo 🚀 You can now run pipeline commands:
echo    python run_pipeline.py --help
echo.
echo 💡 To deactivate: deactivate
""")
    
    print("\n🎉 Pipeline virtual environment setup complete!")
    print(f"📁 Location: {venv_path}")
    
    if os.name == 'nt':  # Windows
        print(f"🔧 Activation script: {activation_bat}")
        print(f"   Run: {activation_bat}")
    else:
        print(f"🔧 Activation script: {activation_script}")
        print(f"   Run: source {activation_script}")
    
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment")
    print("2. Check dependencies: python scripts/check_pipeline_dependencies.py")
    print("3. Run pipeline: python run_pipeline.py --help")
    
    return 0

if __name__ == "__main__":
    exit(main()) 