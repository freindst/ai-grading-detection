# Installation Complete! 🎉

## What's Been Installed

✅ Python 3.12.4 virtual environment  
✅ All Python dependencies (gradio, torch, transformers, etc.)  
✅ Ollama configuration for WSL  
✅ Quick launcher scripts

## ⚠️ Important: Install an Ollama Model

Before running the application, you need to download at least one model.

**In Windows PowerShell or Command Prompt, run:**

```powershell
# Recommended: Fast and good for code grading
ollama pull qwen2.5-coder

# OR: Alternative models
ollama pull llama3.1
ollama pull mistral
ollama pull qwen2.5
```

This will take 5-15 minutes depending on your internet speed.

## How to Run the Application

### Option 1: Using the Quick Launcher (Recommended)

```bash
cd /mnt/e/GradingSystem
./start_wsl.sh
```

### Option 2: Manual Start

```bash
cd /mnt/e/GradingSystem
source venv/bin/activate
python -m src.app
```

Then open in your **Windows browser**:
**http://localhost:7860**

## Optional: Install Tesseract for Image OCR

If you want to grade image files (JPG, PNG), install tesseract:

```bash
sudo apt install tesseract-ocr
```

## Configuration Files Created

- `.env` - Ollama connection settings (auto-configured for your system)
- `venv/` - Python virtual environment
- `configure_ollama.sh` - Helper script to reconfigure Ollama if needed

## Quick Test

1. Pull a model (see above)
2. Run `./start_wsl.sh`
3. Open http://localhost:7860
4. Try the "Text Input Grading" tab with a sample assignment

## Troubleshooting

### "Cannot connect to Ollama"
- Make sure Ollama is running on Windows
- Run: `./configure_ollama.sh` to reconfigure

### "Model not found"
- Pull a model in Windows PowerShell: `ollama pull qwen2.5-coder`

### Permission denied on scripts
```bash
chmod +x start_wsl.sh configure_ollama.sh install_wsl.sh
```

## Next Steps

1. **Pull an Ollama model** (see above) ⚠️
2. Start the application with `./start_wsl.sh`
3. Read `QUICKSTART.md` for usage examples
4. Read `README.md` for full documentation

---

**Installation completed on:** $(date)  
**System:** WSL Ubuntu on Windows  
**Python:** 3.12.4  
**Ollama:** Configured at http://172.23.48.1:11434

