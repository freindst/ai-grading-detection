#!/bin/bash
# Ollama Configuration Helper for WSL
# This script helps connect WSL to Ollama running on Windows

echo ""
echo "========================================"
echo "  OLLAMA CONFIGURATION FOR WSL"
echo "========================================"
echo ""

# Get Windows host IP
WINDOWS_IP=$(ip route | grep default | awk '{print $3}')
echo "Windows host IP: $WINDOWS_IP"
echo ""

# Test localhost first
echo "Testing localhost:11434..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama accessible at localhost:11434"
    echo ""
    echo "Configuration: Use http://localhost:11434"
    exit 0
fi

# Test Windows IP
echo "Testing ${WINDOWS_IP}:11434..."
if curl -s http://${WINDOWS_IP}:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama accessible at ${WINDOWS_IP}:11434"
    echo ""
    echo "Creating configuration file..."
    
    # Create .env file with Ollama URL
    cat > /mnt/e/GradingSystem/.env << EOF
# Ollama Configuration
OLLAMA_HOST=http://${WINDOWS_IP}:11434
EOF
    
    echo "✓ Configuration saved to .env"
    echo ""
    echo "Ollama is accessible from WSL!"
    echo "You can now run the application."
    exit 0
fi

# Neither worked
echo "⚠️  Could not connect to Ollama"
echo ""
echo "Please ensure Ollama is running on Windows:"
echo "  1. Open PowerShell as Administrator"
echo "  2. Run: ollama serve"
echo ""
echo "If Ollama is running, you may need to configure it to accept connections from WSL:"
echo "  1. In Windows, set environment variable:"
echo "     setx OLLAMA_HOST 0.0.0.0:11434"
echo "  2. Restart Ollama service"
echo "  3. Run this script again"
echo ""
