# Installation Script for Windows PowerShell
# Grading Assistant System - Automated Setup

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  GRADING ASSISTANT SYSTEM INSTALLER" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

if ($pythonVersion -match "Python 3\.(1[0-9]|[1-9][0-9])") {
    Write-Host "✓ Python version is compatible (3.10+)`n" -ForegroundColor Green
} else {
    Write-Host "✗ Python 3.10+ required. Please install from python.org`n" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
Write-Host "✓ Virtual environment created`n" -ForegroundColor Green

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated`n" -ForegroundColor Green

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✓ Pip upgraded`n" -ForegroundColor Green

# Install requirements
Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "✓ Dependencies installed`n" -ForegroundColor Green

# Check Ollama
Write-Host "Checking Ollama installation..." -ForegroundColor Yellow
$ollamaCheck = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaCheck) {
    Write-Host "✓ Ollama is installed`n" -ForegroundColor Green
    
    Write-Host "Checking for models..." -ForegroundColor Yellow
    $models = ollama list 2>&1
    if ($models -match "qwen2.5-coder") {
        Write-Host "✓ qwen2.5-coder model found`n" -ForegroundColor Green
    } else {
        Write-Host "! qwen2.5-coder model not found" -ForegroundColor Yellow
        Write-Host "  Downloading model (this will take several minutes)..." -ForegroundColor Yellow
        ollama pull qwen2.5-coder
        Write-Host "✓ Model downloaded`n" -ForegroundColor Green
    }
} else {
    Write-Host "✗ Ollama not found!" -ForegroundColor Red
    Write-Host "  Please install from: https://ollama.ai" -ForegroundColor Yellow
    Write-Host "  Then run this script again`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "To run the application:" -ForegroundColor Yellow
Write-Host "  1. Make sure virtual environment is activated:" -ForegroundColor White
Write-Host "     .\venv\Scripts\Activate.ps1`n" -ForegroundColor Cyan
Write-Host "  2. Run the application:" -ForegroundColor White
Write-Host "     python -m src.app`n" -ForegroundColor Cyan
Write-Host "  3. Open browser to:" -ForegroundColor White
Write-Host "     http://localhost:7860`n" -ForegroundColor Cyan

