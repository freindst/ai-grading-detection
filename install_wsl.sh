#!/bin/bash
# WSL Installation Script for Grading Assistant System
# Run this in WSL (Ubuntu/Debian)

set -e  # Exit on any error

echo ""
echo "========================================"
echo "  GRADING SYSTEM - WSL INSTALLER"
echo "========================================"
echo ""

# Navigate to project directory
echo "Navigating to project directory..."
cd /mnt/e/GradingSystem || { echo "Error: Could not find /mnt/e/GradingSystem"; exit 1; }
echo "✓ Project directory found"
echo ""

# Update system
echo "Updating system packages..."
sudo apt update -qq

# Install Python 3.11
echo "Checking for Python 3.11..."
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    sudo apt install software-properties-common -y -qq
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update -qq
    sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y
    echo "✓ Python 3.11 installed"
else
    echo "✓ Python 3.11 already installed"
fi

PYTHON_VERSION=$(python3.11 --version)
echo "  $PYTHON_VERSION"
echo ""

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y tesseract-ocr build-essential libssl-dev libffi-dev > /dev/null 2>&1
echo "✓ System dependencies installed"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "! Virtual environment already exists, removing old one..."
    rm -rf venv
fi
python3.11 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet
echo "✓ Pip upgraded"
echo ""

# Install Python packages
echo "Installing Python packages (this may take 3-5 minutes)..."
echo "Please wait..."
pip install -r requirements.txt --quiet
echo "✓ Python packages installed"
echo ""

# Check Ollama connection
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is accessible"
    echo ""
    
    echo "Checking for models..."
    if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "qwen2.5-coder"; then
        echo "✓ qwen2.5-coder model found"
    else
        echo "! qwen2.5-coder model not found"
        echo "  Downloading from Windows (run in PowerShell):"
        echo "  ollama pull qwen2.5-coder"
    fi
else
    echo "⚠️  Ollama not accessible from WSL"
    echo ""
    echo "Don't worry! I've created a configuration helper."
    echo "After installation completes, run:"
    echo "  ./configure_ollama.sh"
    echo ""
    echo "It will automatically detect and configure Ollama for you."
    echo ""
fi

echo ""
echo "========================================"
echo "  INSTALLATION COMPLETE!"
echo "========================================"
echo ""
echo "To run the application:"
echo ""
echo "  cd /mnt/e/GradingSystem"
echo "  source venv/bin/activate"
echo "  python -m src.app"
echo ""
echo "Then open in Windows browser:"
echo "  http://localhost:7860"
echo ""
echo "To stop the app: Press Ctrl+C"
echo ""

