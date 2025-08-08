#!/bin/bash
# ChatMind Pipeline Virtual Environment Activation Script

echo "🔧 Activating ChatMind Pipeline Virtual Environment..."
source chatmind/pipeline/pipeline_env/bin/activate

echo "✅ Pipeline virtual environment activated!"
echo "📦 Installed packages:"
pip list

echo ""
echo "🚀 You can now run pipeline commands:"
echo "   python run_pipeline.py --help"
echo ""
echo "💡 To deactivate: deactivate"
