# Quick Installation Guide for Your System

## Your System Status:
- ⚠️ Python: NOT FOUND (Required!)
- ✅ Ollama: Installed (v0.12.9) ✓
- ⚠️ Conda: Not installed (optional)

## STEP 1: Install Python (REQUIRED)

### Option A: Microsoft Store (Easiest for Windows)
1. Open Microsoft Store
2. Search for "Python 3.11"
3. Click "Get" or "Install"
4. Wait for installation to complete

### Option B: Official Website (Recommended)
1. Go to: https://www.python.org/downloads/
2. Download Python 3.11.x (latest stable)
3. Run installer
4. ✅ **IMPORTANT**: Check "Add Python to PATH"
5. Click "Install Now"

## STEP 2: Verify Python Installation

Open a NEW PowerShell window and run:
```powershell
python --version
```

Should show: Python 3.11.x or 3.10.x

## STEP 3: Install Grading System

Once Python is installed, run ONE of these options:

### Option A: Automatic Installation (Recommended)
```powershell
cd E:\GradingSystem
.\install.ps1
```

### Option B: Manual Installation (If script doesn't work)
```powershell
cd E:\GradingSystem

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download LLM model
ollama pull qwen2.5-coder
```

## STEP 4: Run the Application

```powershell
# Activate environment (if not already active)
.\venv\Scripts\Activate.ps1

# Run the app
python -m src.app
```

## STEP 5: Open in Browser

Go to: http://localhost:7860

---

## Troubleshooting

### If "python not found" after installation:
1. Close ALL PowerShell windows
2. Open a NEW PowerShell
3. Try again: `python --version`

### If script execution is blocked:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### If you prefer Conda:
1. Install Anaconda from: https://www.anaconda.com/download
2. Open Anaconda Prompt
3. Run:
```bash
conda create -n grading-system python=3.11 -y
conda activate grading-system
pip install -r requirements.txt
ollama pull qwen2.5-coder
python -m src.app
```

---

## Quick Reference Card (Save This!)

**Every time you want to run the app:**

1. Open PowerShell
2. Navigate to project:
   ```powershell
   cd E:\GradingSystem
   ```
3. Activate environment:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
4. Run app:
   ```powershell
   python -m src.app
   ```
5. Open browser: http://localhost:7860

**To stop the app:**
Press `Ctrl+C` in PowerShell

---

## What to Do Right Now:

1. ✅ Ollama is already installed - Good!
2. ⚠️ Install Python 3.11 (see Step 1 above)
3. ⚠️ Come back and run the installation (Step 3)

After Python is installed, I can help you complete the setup!

