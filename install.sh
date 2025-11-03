#!/bin/bash
# Installation Script for Linux/Mac
# Grading Assistant System - Automated Setup

echo ""
echo "========================================"
echo "  GRADING ASSISTANT SYSTEM INSTALLER"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Found: $PYTHON_VERSION"

if [[ $PYTHON_VERSION =~ Python\ 3\.([0-9]+) ]]; then
    VERSION=${BASH_REMATCH[1]}
    if [ $VERSION -ge 10 ]; then
        echo "✓ Python version is compatible (3.10+)"
        echo ""
    else
        echo "✗ Python 3.10+ required. Please upgrade Python"
        echo ""
        exit 1
    fi
else
    echo "✗ Could not determine Python version"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet
echo "✓ Pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check Ollama
echo "Checking Ollama installation..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama is installed"
    echo ""
    
    echo "Checking for models..."
    if ollama list | grep -q "qwen2.5-coder"; then
        echo "✓ qwen2.5-coder model found"
        echo ""
    else
        echo "! qwen2.5-coder model not found"
        echo "  Downloading model (this will take several minutes)..."
        ollama pull qwen2.5-coder
        echo "✓ Model downloaded"
        echo ""
    fi
else
    echo "✗ Ollama not found!"
    echo "  Please install from: https://ollama.ai"
    echo "  Then run this script again"
    echo ""
    exit 1
fi

echo "========================================"
echo "  INSTALLATION COMPLETE!"
echo "========================================"
echo ""

echo "To run the application:"
echo "  1. Make sure virtual environment is activated:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the application:"
echo "     python -m src.app"
echo ""
echo "  3. Open browser to:"
echo "     http://localhost:7860"
echo ""

