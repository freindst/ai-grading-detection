#!/bin/bash
# Quick launcher for Grading System on WSL

echo ""
echo "========================================"
echo "  STARTING GRADING SYSTEM"
echo "========================================"
echo ""

cd /mnt/e/GradingSystem || exit 1

echo "Activating virtual environment..."
source venv/bin/activate

echo "✓ Environment activated"
echo ""
echo "Starting Gradio application..."
echo "Once started, open in your Windows browser:"
echo "  http://localhost:7860"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""
echo "----------------------------------------"
echo ""

python -m src.app
