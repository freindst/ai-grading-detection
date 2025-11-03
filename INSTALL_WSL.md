# WSL Installation Guide
# Grading Assistant System - Running on WSL

## Your Project Location

**Windows Path:** `E:\GradingSystem`  
**WSL Path:** `/mnt/e/GradingSystem`

---

## Prerequisites

### 1. Install/Enable WSL (if not already installed)

Open PowerShell as Administrator and run:

```powershell
# Enable WSL
wsl --install

# Or install Ubuntu specifically
wsl --install -d Ubuntu
```

Restart your computer after installation.

### 2. Verify WSL Installation

```powershell
wsl --list --verbose
```

Should show Ubuntu or another Linux distribution.

---

## Installation Steps for WSL

### Step 1: Access Your Project in WSL

Open WSL (Ubuntu) terminal:

```bash
# Navigate to your project
cd /mnt/e/GradingSystem

# Verify you're in the right place
ls -la
```

You should see: `src/`, `requirements.txt`, `README.md`, etc.

### Step 2: Update WSL System

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y
```

### Step 3: Install Python 3.11 in WSL

```bash
# Add deadsnakes PPA for Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11 and required tools
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Verify installation
python3.11 --version
```

### Step 4: Install Additional Dependencies

```bash
# Install Tesseract for OCR (for image support)
sudo apt install tesseract-ocr -y

# Install other system dependencies
sudo apt install build-essential libssl-dev libffi-dev -y
```

### Step 5: Create Virtual Environment

```bash
# Navigate to project
cd /mnt/e/GradingSystem

# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your prompt
```

### Step 6: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 7: Install Ollama in WSL

```bash
# Download and install Ollama for Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull the model (in a new terminal or after Ctrl+Z and bg)
ollama pull qwen2.5-coder
```

Alternatively, if Ollama is already running on Windows, you can access it from WSL using Windows host.

---

## Running the Application

### Option A: Use Ollama from Windows Host

If Ollama is already running on Windows (which you have):

1. **In WSL, create a connection to Windows Ollama:**

```bash
# Set environment variable to use Windows Ollama
export OLLAMA_HOST="http://$(hostname).local:11434"
# Or try this if above doesn't work:
export OLLAMA_HOST="http://localhost:11434"
```

2. **Activate environment and run:**

```bash
cd /mnt/e/GradingSystem
source venv/bin/activate
python -m src.app
```

### Option B: Use Ollama in WSL

If you installed Ollama in WSL:

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run the app
cd /mnt/e/GradingSystem
source venv/bin/activate
python -m src.app
```

---

## Accessing the Application

Once running, open your Windows browser to:
```
http://localhost:7860
```

The app running in WSL will be accessible from Windows!

---

## Quick Start Script for WSL

Save this as `start_wsl.sh` in your project directory:

```bash
#!/bin/bash
# Quick start script for WSL

echo "Starting Grading Assistant System in WSL..."

# Navigate to project
cd /mnt/e/GradingSystem

# Activate virtual environment
source venv/bin/activate

# Set Ollama host (if using Windows Ollama)
export OLLAMA_HOST="http://localhost:11434"

# Run application
echo "Starting application..."
echo "Open browser to: http://localhost:7860"
python -m src.app
```

Make it executable:
```bash
chmod +x start_wsl.sh
```

Run it:
```bash
./start_wsl.sh
```

---

## Automated WSL Installation Script

Create and run this installation script:

```bash
#!/bin/bash
# install_wsl.sh - Automated installation for WSL

set -e  # Exit on error

echo "========================================"
echo "  GRADING SYSTEM - WSL INSTALLER"
echo "========================================"
echo ""

# Navigate to project
cd /mnt/e/GradingSystem

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
echo "Installing Python 3.11..."
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev python3-pip -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install tesseract-ocr build-essential libssl-dev libffi-dev -y

# Create virtual environment
echo "Creating virtual environment..."
python3.11 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python packages
echo "Installing Python packages (this may take a few minutes)..."
pip install -r requirements.txt

# Check if Ollama is accessible
echo ""
echo "Checking Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is accessible from Windows"
    echo ""
    echo "Checking for models..."
    if curl -s http://localhost:11434/api/tags | grep -q "qwen2.5-coder"; then
        echo "✓ qwen2.5-coder model found"
    else
        echo "! Model not found. Downloading qwen2.5-coder..."
        curl -X POST http://localhost:11434/api/pull -d '{"name":"qwen2.5-coder"}' || echo "Please run: ollama pull qwen2.5-coder (in Windows)"
    fi
else
    echo "! Ollama not accessible. Make sure Ollama is running on Windows"
    echo "  Or install in WSL: curl -fsSL https://ollama.com/install.sh | sh"
fi

echo ""
echo "========================================"
echo "  INSTALLATION COMPLETE!"
echo "========================================"
echo ""
echo "To run the application:"
echo "  1. cd /mnt/e/GradingSystem"
echo "  2. source venv/bin/activate"
echo "  3. python -m src.app"
echo "  4. Open browser: http://localhost:7860"
echo ""
```

---

## Troubleshooting WSL Issues

### Issue: Can't access project files

**Solution:**
```bash
# Make sure you're using /mnt/e/ not /e/
cd /mnt/e/GradingSystem
ls -la
```

### Issue: Permission denied

**Solution:**
```bash
# Fix permissions
sudo chown -R $USER:$USER /mnt/e/GradingSystem
```

### Issue: Can't connect to Ollama on Windows

**Solution:**
```bash
# Find Windows IP from WSL
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'

# Use that IP
export OLLAMA_HOST="http://172.x.x.x:11434"

# Or try localhost
export OLLAMA_HOST="http://localhost:11434"

# Test connection
curl http://localhost:11434/api/tags
```

### Issue: Port 7860 already in use

**Solution:**
```bash
# Find what's using the port
sudo lsof -i :7860

# Kill it
sudo kill <PID>

# Or use a different port in the app
```

### Issue: Module not found errors

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Advantages of Using WSL

✅ Better compatibility with Python packages  
✅ Native Linux tools and commands  
✅ Faster package installation  
✅ Better for shell scripts  
✅ More stable for long-running processes  
✅ Access to both Windows and Linux tools  

---

## File Editing

You can edit files from:

1. **Windows:** Use VS Code, Notepad++, etc. on `E:\GradingSystem`
2. **WSL:** Use nano, vim, or VS Code with WSL extension
3. **VS Code + WSL:** Best option!
   ```bash
   # Install VS Code WSL extension, then:
   code .
   ```

---

## Next Steps

1. Open WSL (Ubuntu)
2. Navigate to `/mnt/e/GradingSystem`
3. Run the installation script above
4. Start the application
5. Open http://localhost:7860 in Windows browser

Your Windows files are accessible in WSL, and WSL services are accessible from Windows!

