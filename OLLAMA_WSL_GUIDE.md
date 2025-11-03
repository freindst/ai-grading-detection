# WSL-Windows Ollama Connection Guide

## The Problem

WSL needs to connect to Ollama running on Windows, but there are several ways this can work (or fail):

---

## How WSL Networking Works

### WSL2 (Default)
- WSL runs in a lightweight VM
- Has its own IP address
- Windows services accessible via special networking
- Usually works via `localhost`, but not always

### Three Connection Methods

#### Method 1: localhost (Best, if it works)
```bash
curl http://localhost:11434/api/tags
```
**Works when**: WSL2 has automatic port forwarding enabled (default)

#### Method 2: 127.0.0.1 (Alternative localhost)
```bash
curl http://127.0.0.1:11434/api/tags
```
**Works when**: localhost forwarding configured differently

#### Method 3: Windows Host IP (Fallback)
```bash
# Find Windows IP
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
# Example: 172.20.48.1

curl http://172.20.48.1:11434/api/tags
```
**Works when**: localhost doesn't work, but you know Windows IP

---

## Automatic Configuration Script

We created `configure_ollama.sh` to automatically detect and configure for you!

### What It Does:
1. ✅ Tests `localhost:11434`
2. ✅ Tests `127.0.0.1:11434`
3. ✅ Finds Windows IP automatically
4. ✅ Tests Windows IP
5. ✅ Provides exact configuration commands
6. ✅ Optionally adds to ~/.bashrc automatically
7. ✅ Shows troubleshooting if all fail

### Usage:
```bash
cd /mnt/e/GradingSystem
chmod +x configure_ollama.sh
./configure_ollama.sh
```

### Output Example (Success):
```
🔍 Testing connection to localhost:11434...
✅ SUCCESS! Ollama accessible via localhost

Configuration:
  export OLLAMA_HOST="http://localhost:11434"

This is already set in start_wsl.sh - you're good to go!
```

### Output Example (Needs Configuration):
```
🔍 Testing connection to localhost:11434...
❌ localhost:11434 not accessible

🔍 Finding Windows host IP...
Found potential Windows IP: 172.20.48.1

🔍 Testing connection to 172.20.48.1:11434...
✅ SUCCESS! Ollama accessible via Windows IP

════════════════════════════════════════
  CONFIGURATION NEEDED
════════════════════════════════════════

Option 1 (Recommended): Add to ~/.bashrc
  echo 'export OLLAMA_HOST="http://172.20.48.1:11434"' >> ~/.bashrc
  source ~/.bashrc

Option 2: Set each time before running
  export OLLAMA_HOST="http://172.20.48.1:11434"

Option 3: I'll do it for you now
  Add to ~/.bashrc automatically? (y/n):
```

---

## Manual Configuration (If Needed)

### Step 1: Find What Works

Test each method:
```bash
# Test 1
curl http://localhost:11434/api/tags

# Test 2
curl http://127.0.0.1:11434/api/tags

# Test 3 - Find Windows IP first
WINDOWS_IP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo $WINDOWS_IP
curl http://$WINDOWS_IP:11434/api/tags
```

### Step 2: Set OLLAMA_HOST

Whichever works, set it:

**Temporary (current session only):**
```bash
export OLLAMA_HOST="http://localhost:11434"
# or
export OLLAMA_HOST="http://172.20.48.1:11434"
```

**Permanent (add to ~/.bashrc):**
```bash
echo 'export OLLAMA_HOST="http://localhost:11434"' >> ~/.bashrc
source ~/.bashrc
```

### Step 3: Verify
```bash
echo $OLLAMA_HOST
curl $OLLAMA_HOST/api/tags
```

---

## Troubleshooting

### Issue: None of the methods work

#### Solution 1: Check Ollama is Running (Windows)
```powershell
# In Windows PowerShell
ollama list
# Should show installed models

# If not running, start it
ollama serve
```

#### Solution 2: Windows Firewall
```powershell
# In Windows PowerShell (as Administrator)
New-NetFirewallRule -DisplayName "Ollama for WSL" `
  -Direction Inbound `
  -LocalPort 11434 `
  -Protocol TCP `
  -Action Allow
```

#### Solution 3: Make Ollama Listen on All Interfaces
```powershell
# In Windows PowerShell
$env:OLLAMA_HOST = "0.0.0.0"
ollama serve
```

#### Solution 4: Install Ollama in WSL Instead
```bash
# In WSL
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5-coder
```

### Issue: Windows IP keeps changing

**Solution**: Add script to detect dynamically
```bash
# Add to ~/.bashrc
export OLLAMA_HOST="http://$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):11434"
```

Or use our `start_wsl.sh` which detects automatically!

---

## Integration with Our Scripts

### `install_wsl.sh`
- Checks Ollama connection
- If not found, tells you to run `configure_ollama.sh`

### `configure_ollama.sh` (NEW!)
- Automatically detects best method
- Guides configuration
- Can update ~/.bashrc for you

### `start_wsl.sh`
- Sets OLLAMA_HOST="http://localhost:11434" by default
- If that fails, tries to find Windows IP automatically
- Falls back gracefully

---

## Quick Start Workflow

### If Ollama Works Immediately:
```bash
./install_wsl.sh
# Shows: ✓ Ollama is accessible

./start_wsl.sh
# Just works! 🎉
```

### If Ollama Needs Configuration:
```bash
./install_wsl.sh
# Shows: ⚠️ Ollama not accessible
#        Run: ./configure_ollama.sh

./configure_ollama.sh
# Automatically detects and configures

./start_wsl.sh
# Now works! 🎉
```

---

## Technical Details

### Why localhost Sometimes Fails

**WSL2 Networking Modes**:
1. **NAT Mode** (default) - localhost usually works
2. **Bridged Mode** - need Windows IP
3. **Mirrored Mode** (Windows 11 22H2+) - localhost always works

### How to Check Your Mode:
```bash
# In WSL
ip addr show eth0

# If you see 172.x.x.x - you're in NAT mode
# If you see same subnet as Windows - bridged mode
```

### Force Mirrored Mode (Windows 11 22H2+):
Create `.wslconfig` in Windows user folder:
```ini
[wsl2]
networkingMode=mirrored
```

Then restart WSL:
```powershell
wsl --shutdown
wsl
```

---

## Summary

✅ **We've got you covered!**

1. Run `./install_wsl.sh` - it checks for Ollama
2. If not detected, run `./configure_ollama.sh` - it guides you
3. Configuration is automatic or semi-automatic
4. `start_wsl.sh` has built-in fallbacks

**You won't get stuck!** The scripts will guide you through any configuration needed.

---

**Created**: November 2, 2025  
**Purpose**: Ensure seamless WSL → Windows Ollama connectivity  
**Status**: Fully automated detection and configuration

