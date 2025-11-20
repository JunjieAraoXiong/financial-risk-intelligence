#!/bin/bash
# FE-EKG Demo Launcher
# Automatically starts Jupyter with the correct environment

echo "🚀 FE-EKG Demo Launcher"
echo "======================="
echo ""

# Navigate to demos directory
cd "$(dirname "$0")"

# Activate main project venv
VENV_PATH="../venv/bin/activate"

if [ ! -f "$VENV_PATH" ]; then
    echo "❌ Error: Virtual environment not found at $VENV_PATH"
    echo "   Please run this from the demos folder"
    exit 1
fi

echo "✅ Activating virtual environment..."
source "$VENV_PATH"

# Check if Jupyter is installed
if ! command -v jupyter &> /dev/null; then
    echo "❌ Error: Jupyter not installed in virtual environment"
    echo "   Run: pip install jupyter"
    exit 1
fi

echo "✅ Starting Jupyter Notebook..."
echo ""
echo "📋 Available demos:"
echo "   • triple_formation_demo.ipynb - Educational walkthrough"
echo "   • crisis_timeline_demo.ipynb - Interactive presentation"
echo ""
echo "📖 Instructions:"
echo "   1. Your browser will open at http://localhost:8888"
echo "   2. Click on a .ipynb file to open it"
echo "   3. Click 'Cell' → 'Run All' to execute the demo"
echo ""
echo "⏸  Press Ctrl+C to stop Jupyter when done"
echo ""

# Start Jupyter
jupyter notebook
