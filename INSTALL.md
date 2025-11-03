# Grading Assistant System - Installation Guide

## Choose Your Installation Method

### Option 1: Python Virtual Environment (Recommended for most users)
**Best for**: Standard Python installations, most compatible

### Option 2: Conda Environment (Recommended for data scientists)
**Best for**: Users already using Anaconda/Miniconda

---

## Prerequisites

Before installing, ensure you have:

1. **Python 3.10 or higher** (3.11 recommended)
   - Check: `python --version`
   - Download: https://www.python.org/downloads/

2. **Ollama** (for local LLM)
   - Download: https://ollama.ai
   - Verify: `ollama --version`

---

## Installation Steps

### Windows Users

#### Option A: Virtual Environment (venv)

1. **Open PowerShell as Administrator** (for script execution)
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Navigate to project directory**
   ```powershell
   cd E:\GradingSystem
   ```

3. **Run installation script**
   ```powershell
   .\install.ps1
   ```

4. **Launch the application**
   ```powershell
   .\venv\Scripts\Activate.ps1
   python -m src.app
   ```

#### Option B: Conda Environment

1. **Open Anaconda Prompt or PowerShell**

2. **Navigate to project directory**
   ```powershell
   cd E:\GradingSystem
   ```

3. **Run Conda installation script**
   ```powershell
   .\install_conda.ps1
   ```

4. **Launch the application**
   ```powershell
   conda activate grading-system
   python -m src.app
   ```

---

### Linux/Mac Users

#### Option A: Virtual Environment (venv)

1. **Open Terminal**

2. **Navigate to project directory**
   ```bash
   cd /path/to/GradingSystem
   ```

3. **Make script executable and run**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

4. **Launch the application**
   ```bash
   source venv/bin/activate
   python -m src.app
   ```

#### Option B: Conda Environment

1. **Open Terminal**

2. **Create and activate conda environment**
   ```bash
   conda create -n grading-system python=3.11 -y
   conda activate grading-system
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download LLM model**
   ```bash
   ollama pull qwen2.5-coder
   ```

5. **Launch the application**
   ```bash
   python -m src.app
   ```

---

## Manual Installation (If scripts don't work)

### Step 1: Create Environment

**For venv:**
```bash
python -m venv venv
```

**For conda:**
```bash
conda create -n grading-system python=3.11 -y
```

### Step 2: Activate Environment

**Windows (venv):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/Mac (venv):**
```bash
source venv/bin/activate
```

**Conda (all platforms):**
```bash
conda activate grading-system
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install Ollama and Models

1. Download Ollama from https://ollama.ai
2. Install and start Ollama
3. Pull a model:
   ```bash
   ollama pull qwen2.5-coder
   ```

### Step 5: Run Application

```bash
python -m src.app
```

---

## Verification

After installation, verify everything works:

1. **Check Ollama is running**
   ```bash
   ollama list
   ```
   Should show: qwen2.5-coder (and other models)

2. **Check Python packages**
   ```bash
   pip list | grep gradio
   ```
   Should show: gradio 4.x.x

3. **Test the application**
   - Run: `python -m src.app`
   - Open: http://localhost:7860
   - Click "Refresh Status" button
   - Should show "✅ Connected to Ollama"

---

## Troubleshooting

### Issue: "Cannot run scripts" (Windows)

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: "Python not found"

**Solution:**
- Ensure Python is in PATH
- Try `python3` instead of `python`
- Reinstall Python with "Add to PATH" option

### Issue: "pip install fails"

**Solution:**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install packages individually if needed
pip install gradio requests PyPDF2 python-docx Pillow
```

### Issue: "Ollama not connecting"

**Solution:**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# In another terminal, pull model
ollama pull qwen2.5-coder
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Make sure you're in the right directory
cd E:\GradingSystem

# Make sure environment is activated
# For venv:
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# For conda:
conda activate grading-system

# Reinstall requirements
pip install -r requirements.txt
```

### Issue: "Out of memory" with models

**Solution:**
Use a smaller model:
```bash
ollama pull mistral  # Smaller, faster
```

Or in the app, select "mistral" from the model dropdown.

---

## Quick Start After Installation

1. **Activate environment**
   ```bash
   # venv (Windows)
   .\venv\Scripts\Activate.ps1
   
   # venv (Linux/Mac)
   source venv/bin/activate
   
   # conda
   conda activate grading-system
   ```

2. **Start Ollama** (if not auto-started)
   ```bash
   ollama serve
   ```

3. **Run application**
   ```bash
   python -m src.app
   ```

4. **Open browser**
   ```
   http://localhost:7860
   ```

---

## Environment Comparison

| Feature | venv | conda |
|---------|------|-------|
| Installation Speed | Fast | Slower |
| Package Management | pip only | pip + conda |
| Disk Space | Smaller | Larger |
| Compatibility | Standard Python | Better for ML/Data Science |
| Recommendation | ✅ Most users | Data scientists |

---

## Uninstallation

### Remove venv:
```bash
# Deactivate first
deactivate

# Remove directory
rm -rf venv  # Linux/Mac
Remove-Item -Recurse -Force venv  # Windows
```

### Remove conda environment:
```bash
conda deactivate
conda env remove -n grading-system
```

---

## Next Steps

After successful installation, see:
- **QUICKSTART.md** - First grading session examples
- **README.md** - Full feature documentation
- **IMPLEMENTATION_SUMMARY.md** - Technical details

---

## Getting Help

If you encounter issues:
1. Check the error message carefully
2. Verify all prerequisites are installed
3. Try manual installation steps
4. Check Ollama is running: `ollama list`
5. Verify Python version: `python --version` (should be 3.10+)

