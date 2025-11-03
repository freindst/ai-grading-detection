# Ignore Files Reference

This document explains what files are excluded from Cursor indexing and Git tracking.

---

## Files Created

1. **`.cursorignore`** - Tells Cursor IDE what files/folders to ignore
2. **`.gitignore`** - Tells Git what files/folders not to track
3. **`.gitkeep`** files - Placeholder files to preserve empty directory structure in Git

---

## What's Being Ignored

### 🐍 Python Environment & Cache (Won't appear in Cursor or Git)

```
venv/                   # Virtual environment directory
__pycache__/            # Python cache files
*.pyc, *.pyo           # Compiled Python files
```

**Why**: These are generated files, not source code. They're large and change frequently.

### 💾 Database Files (Won't appear in Cursor or Git)

```
*.db                    # SQLite database files
data/database.db        # Your grading history database
```

**Why**: Databases contain user data and can get large. Each installation should have its own.

### 📦 Uploads & Exports (Won't appear in Cursor or Git)

```
data/uploads/           # Student submissions (temporary)
exports/                # Generated CSV, Excel, PDF reports
```

**Why**: These are user-generated files, not part of the codebase.

### 🤖 Model Files (Won't appear in Cursor or Git)

```
models/adapters/        # LoRA/QLoRA model weights
*.pth, *.bin           # PyTorch/model files
```

**Why**: Model files are very large (GBs). Download separately via Ollama.

### 📝 Logs & Temporary Files (Won't appear in Cursor or Git)

```
*.log                   # Log files
*.tmp, *.temp          # Temporary files
*.swp, *.swo           # Vim swap files
```

**Why**: These are runtime artifacts, not source code.

### 🔐 Environment Variables (Won't appear in Cursor or Git)

```
.env                    # Environment variables
.env.local             # Local overrides
```

**Why**: May contain API keys, passwords, or sensitive configuration. Never commit!

### 💻 IDE & OS Files (Won't appear in Cursor or Git)

```
.vscode/               # VS Code settings (optional)
.idea/                 # PyCharm settings
.DS_Store              # macOS folder metadata
Thumbs.db              # Windows thumbnail cache
```

**Why**: Personal IDE settings and OS metadata. Each user should have their own.

### 🧪 Testing & Build Files (Won't appear in Cursor or Git)

```
.pytest_cache/         # Pytest cache
build/, dist/          # Build artifacts
*.egg-info/            # Package metadata
```

**Why**: Generated during testing/building. Not part of source code.

---

## What IS Tracked

### ✅ Source Code (Tracked in Git, Indexed by Cursor)

```
src/*.py               # All Python source files
```

### ✅ Documentation (Tracked in Git, Indexed by Cursor)

```
*.md                   # All markdown files
README.md
QUICKSTART.md
BUILD_PLAN.md
etc.
```

### ✅ Configuration (Tracked in Git, Indexed by Cursor)

```
requirements.txt       # Python dependencies
install*.sh, *.ps1    # Installation scripts
```

### ✅ Empty Directory Structure (Tracked in Git)

```
exports/.gitkeep
models/adapters/.gitkeep
data/uploads/.gitkeep
prompts/templates/.gitkeep
```

**Why**: Git doesn't track empty directories. `.gitkeep` files preserve the structure.

---

## Common Scenarios

### Scenario 1: After Running Installation

**Created but ignored**:
- `venv/` - Virtual environment (100+ MB)
- `__pycache__/` - Python cache (several MB)

**Result**: Cursor won't index these, keeps IDE fast.

### Scenario 2: After Grading Students

**Created but ignored**:
- `data/database.db` - Your grading history (can grow to MBs)
- `data/uploads/` - Temporary student files
- `exports/` - Your generated reports

**Result**: These are your data, not shared via Git.

### Scenario 3: If You Use Git

**What gets committed**:
```
✅ src/*.py (source code)
✅ *.md (documentation)
✅ requirements.txt
✅ install scripts
```

**What doesn't get committed**:
```
❌ venv/ (too large)
❌ *.db (user data)
❌ exports/ (user reports)
❌ .env (secrets)
```

---

## Customization

### To Track Additional Files

**Edit `.gitignore`**, comment out lines with `#`:

```bash
# Want to track logs? Comment this out:
# *.log
```

### To Show Hidden Files in Cursor

**Edit `.cursorignore`**, remove or comment lines:

```bash
# Want to see venv in Cursor? Comment this out:
# venv/
```

### To Ignore Additional Patterns

Add new lines to `.cursorignore` or `.gitignore`:

```bash
# Ignore all test files:
*_test.py
test_*.py

# Ignore specific file:
sensitive_data.csv
```

---

## Benefits

### 🚀 Faster IDE Performance
- Cursor doesn't index thousands of venv files
- Search results are more relevant
- Autocomplete is faster

### 🔒 Better Security
- `.env` files with secrets won't be committed
- Database with student data stays local

### 📦 Cleaner Repository
- Only source code in Git
- Easy to clone and share
- Smaller repository size

### 🎯 Focused Development
- See only what matters in file explorer
- Less clutter in search results
- Easier to find files

---

## File Sizes Saved

**Typical ignored files**:
- `venv/`: 100-500 MB
- `__pycache__/`: 5-50 MB
- `data/database.db`: 1-100 MB (depends on usage)
- `models/adapters/`: 100 MB - 10 GB (if you use fine-tuning)
- `exports/`: 1-50 MB (depends on reports)

**Total saved from Git**: 200 MB - 10+ GB  
**Total saved from Cursor indexing**: 100-500 MB

---

## Verification

### Check what Cursor sees:
Look at Cursor's file explorer - should not see:
- ❌ venv/
- ❌ __pycache__/
- ❌ *.pyc files

### Check what Git tracks (if using Git):
```bash
git status
```

Should not list:
- ❌ venv/
- ❌ *.db
- ❌ exports/

---

## Quick Commands

### List all ignored files:
```bash
# What would be ignored by Git:
git status --ignored

# What files match .gitignore pattern:
git check-ignore -v **/*
```

### Clean up already-tracked files:
```bash
# If you accidentally committed venv/ before:
git rm -r --cached venv/
git commit -m "Remove venv from tracking"
```

### See Cursor's indexed files:
- Open Cursor
- Press Ctrl+P (Cmd+P on Mac)
- Type filename - should not see ignored files

---

## Support

If you want to change what's ignored:
1. Edit `.cursorignore` (for Cursor)
2. Edit `.gitignore` (for Git)
3. Reload Cursor (Ctrl+Shift+P → "Reload Window")
4. For Git changes, may need to clear cache

---

**Created**: November 2, 2025  
**Last Updated**: November 2, 2025

