# Installation Script using Conda
# Grading Assistant System - Conda Environment Setup

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  GRADING ASSISTANT - CONDA INSTALLER" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if conda is available
Write-Host "Checking for Conda/Anaconda..." -ForegroundColor Yellow
$condaCheck = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCheck) {
    Write-Host "✗ Conda not found!" -ForegroundColor Red
    Write-Host "  Please install Anaconda or Miniconda first" -ForegroundColor Yellow
    Write-Host "  Or use the regular install.ps1 script for venv`n" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Conda found`n" -ForegroundColor Green

# Create conda environment
Write-Host "Creating conda environment 'grading-system' with Python 3.11..." -ForegroundColor Yellow
conda create -n grading-system python=3.11 -y
Write-Host "✓ Conda environment created`n" -ForegroundColor Green

# Activate environment
Write-Host "Activating conda environment..." -ForegroundColor Yellow
conda activate grading-system
Write-Host "✓ Environment activated`n" -ForegroundColor Green

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
Write-Host "  1. Activate conda environment:" -ForegroundColor White
Write-Host "     conda activate grading-system`n" -ForegroundColor Cyan
Write-Host "  2. Run the application:" -ForegroundColor White
Write-Host "     python -m src.app`n" -ForegroundColor Cyan
Write-Host "  3. Open browser to:" -ForegroundColor White
Write-Host "     http://localhost:7860`n" -ForegroundColor Cyan

