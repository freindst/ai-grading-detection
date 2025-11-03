# Bugs and Issues Tracker

This document tracks all known bugs, issues, and their resolution status.

**Last Updated**: November 2, 2025

---

## Active Issues

### Critical (Blocking core functionality)

*None currently*

### High Priority (Important but workarounds exist)

*None currently*

### Medium Priority (Should fix soon)

*None currently*

### Low Priority (Minor issues, future improvement)

*None currently*

---

## Resolved Issues

#### Issue #52: Sticky Header/Tab CSS Not Working Correctly ✅
- **Date Reported**: November 3, 2025
- **Date Resolved**: November 3, 2025
- **Severity**: Low
- **Component**: UI (src/app.py CSS)
- **Description**: The sticky positioning for system messages and tab navigation bars was not implementing correctly. The floating effect was causing layout issues and not providing the intended UX benefit.
- **Root Cause**: 
  - `position: sticky` CSS rules for `#system-message` and `.tabs > .tab-nav` were overly complex
  - Multiple attempts to fix scrolling behavior had added complexity without proper results
  - The implementation didn't work reliably across different content heights
- **Solution**: 
  - Removed all `position: sticky` CSS rules
  - Removed `overflow-y: auto` and `max-height` constraints on `.tabitem`
  - Removed `z-index` stacking complexity
  - Simplified to normal scroll flow with clean tab styling
  - Removed `elem_id="system-message"` from system_message component
  - Result: Clean, predictable scrolling behavior without floating elements
- **Files Changed**: 
  - `src/app.py` (lines 237-271): Simplified CSS from 44 lines to 31 lines
  - Removed 5 CSS properties: `position`, `top`, `z-index`, `overflow-y`, `max-height`
- **Status**: Resolved

### 2025-11-02 (Session)

#### 1. Feedback Table Selection Error ✅
**Type**: Bug  
**Severity**: High  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
Clicking on rows in the feedback library table resulted in `NoneType' object has no attribute 'value` error.

**Root Cause**:  
Event handler used incorrect lambda syntax: `lambda evt: evt.value[5]` which doesn't work with Gradio's SelectData event system.

**Solution Applied**:  
- Created proper `handle_table_select(evt: gr.SelectData)` function
- Uses `evt.index[0]` to get row index
- Extracts filename from dataframe using proper indexing
- Updated event handler to use new function

**Files Changed**:
- `src/app.py` (lines 646-659, 1163-1166)

---

#### 2. Feedback Table Unreadable (Poor Contrast) ✅
**Type**: UI/UX Bug  
**Severity**: Medium  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
Feedback table had similar text and background colors making it very hard to read.

**Root Cause**:  
No custom CSS styling for Gradio dataframe components - relied on default dark theme.

**Solution Applied**:  
Added comprehensive CSS overrides:
- Table background: white (#ffffff)
- Text color: black (#000000)
- Headers: blue background (#0066ff) with white text
- Alternating row colors with hover effects
- Clear borders and padding

**Files Changed**:
- `src/app.py` (lines 743-767 - CSS section)

---

#### 3. AI Detection Output Not Clear ✅
**Type**: UI/UX Issue  
**Severity**: Low  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
AI detection results were too brief and unclear. User wanted explicit "no detection" message when no keywords found.

**Root Cause**:  
Messages were minimal: "✅ No AI keywords detected" without explanation.

**Solution Applied**:  
Enhanced messages:
- When detected: "🚨 AI KEYWORDS DETECTED\n\nFound: [keywords]\n\nThis submission may be AI-generated."
- When clean: "✅ NO AI KEYWORDS DETECTED\n\nNo suspicious AI-related phrases found in submission."
- Added warnings to grade and grading reason fields when detected

**Files Changed**:
- `src/app.py` (lines 421-428)

---

#### 4. No Few-Shot In-Context Learning ✅
**Type**: Missing Feature  
**Severity**: Medium  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
System collected feedback examples but didn't use them to improve LLM performance through few-shot learning.

**Solution Applied**:  
Implemented complete few-shot learning system:
1. Added `select_few_shot_examples(max_examples=3)` function
   - Filters for "good examples" only
   - Randomly selects up to N examples
   - Formats with grade, reasoning, and effectiveness notes
2. Updated grading engine to accept few-shot examples parameter
3. Added UI controls (checkbox + slider) to enable/disable and configure
4. Examples injected into prompt before student submission

**Files Changed**:
- `src/app.py` (lines 603-643, 332-347, 450-469, 894-900, 1116-1124)
- `src/grading_engine.py` (lines 32-42, 104, 113-125, 133-142)

**Future Improvements**:
See `FUTURE_PLANS.md` for roadmap:
- Embedding-based similarity search
- Performance tracking per example
- Adaptive user preference learning
- Category/assignment-type matching

---

#### 5. Output Format Not Respected (Numeric vs Letter Grade) ✅
**Type**: Bug  
**Severity**: High  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
When using numeric output format (0-100), the LLM returned letter grades (A, B, C, etc.) instead of numeric scores.

**Root Cause**:  
Prompt builder was not emphasizing numeric format strongly enough to LLM.

**Solution Applied**:  
Updated `src/grading_engine.py` `build_grading_prompt()` method to include explicit, emphatic format instructions with examples of correct/incorrect formats.

**Files Changed**:
- `src/grading_engine.py` (lines 48-83)

---

#### 2. Method Name Error in Profile Update ✅
**Type**: Bug  
**Severity**: High  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
When updating criteria profiles, got error "create_grading_criteria method not found".

**Root Cause**:  
In `src/app.py` line 250, calling `db_manager.create_grading_criteria()` but the actual method name in `src/database.py` was `create_criteria()`.

**Solution Applied**:  
Fixed method name in `src/app.py` line 250 from `create_grading_criteria` to `create_criteria`.

**Files Changed**:
- `src/app.py` (line 250)

---

#### 3. No Feedback/Criticism Collection UI ✅
**Type**: Missing Feature  
**Severity**: Medium  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
User wanted to provide feedback/criticism on grading results and see the actual prompts sent to LLM.

**Solution Applied**:  
Added new "🔍 Prompt & Feedback" tab with:
1. Display of system prompt (LLM instructions)
2. Display of user prompt (submission + criteria)
3. Feedback text area for user criticism
4. Checkbox to mark as "good example" for in-context learning
5. Save button that stores feedback to `data/feedback/` as JSON

**Files Changed**:
- `src/app.py`:
  - Added feedback UI tab (lines 600-635)
  - Updated `grade_submission()` to return prompts (lines 316-332)
  - Added `save_feedback_to_db()` function (lines 343-379)
  - Added global `last_grading_context` for feedback tracking (lines 335-340)
  - Wired up save_feedback button (lines 804-808)

---

#### 4. Radio Button & Checkbox Selection Not Visible ✅
**Type**: UI/UX Bug  
**Severity**: Medium  
**Status**: **RESOLVED**  
**Resolved Date**: 2025-11-02  

**Description**:  
Radio buttons and checkboxes had minimal visual feedback when selected. Selection state was hard to see after clicking elsewhere.

**Root Cause**:  
CSS selectors were not correctly targeting Gradio's component structure. The `:has()` pseudo-class was needed to style parent labels based on checked input state.

**Solution Applied**:  
Completely rewrote CSS for radio buttons and checkboxes (lines 515-628):
- Used `:has(input:checked)` selector to style selected state
- Added blue border (#0066ff) and dark blue background (#1a3a5a) for selected items
- Added glowing box-shadow for visual emphasis
- Increased input size to 20px × 20px
- Added hover states with color transitions
- Made selected text brighter and bolder
- Used `accent-color` for native checkmarks/radio circles

**Visual Changes**:
- **Unselected**: Gray border (#505050), dark background (#2a2a2a)
- **Hover**: Lighter background (#353535), blue border
- **Selected**: Blue border with glow, blue-tinted background, white bold text

**Files Changed**:
- `src/app.py` (lines 515-628)

---

*Previous resolved issues - Initial release*

---

## Known Limitations (Not Bugs)

These are intentional limitations or design decisions, not bugs:

### 1. No Automated Fine-Tuning Pipeline
**Type**: Feature Not Implemented  
**Severity**: Low  
**Description**: While PEFT library is included and foundation is ready, the complete LoRA/QLoRA training pipeline UI is not yet integrated.  
**Workaround**: Manual fine-tuning possible with external tools  
**Planned**: Future enhancement

### 2. Large Batches May Be Memory Intensive
**Type**: Performance Limitation  
**Severity**: Low  
**Description**: Processing 50+ files simultaneously can consume significant RAM  
**Workaround**: Process in smaller batches (10-20 files)  
**Mitigation**: Concurrent worker count limited to 3

### 3. OCR Requires Tesseract Installation
**Type**: Dependency Requirement  
**Severity**: Low  
**Description**: Image grading requires tesseract-ocr to be installed separately  
**Workaround**: Install tesseract: `sudo apt install tesseract-ocr` (Linux)  
**Documentation**: Mentioned in INSTALL guides

### 4. Web Search Requires Internet
**Type**: Design Decision  
**Severity**: Low  
**Description**: Reference verification needs internet connection  
**Workaround**: Toggle off reference verification if offline  
**Status**: Working as intended

### 5. Database Not Distributed
**Type**: Design Decision  
**Severity**: Low  
**Description**: Each installation has its own database (not shared)  
**Rationale**: Privacy and simplicity  
**Status**: Working as intended

---

## Issue Template

When reporting a new issue, use this format:

```markdown
### Issue Title (Brief Description)
**Type**: Bug / Performance / Enhancement
**Severity**: Critical / High / Medium / Low
**Status**: Open / In Progress / Resolved / Won't Fix
**Reported**: YYYY-MM-DD
**Resolved**: YYYY-MM-DD (if resolved)

**Description**:
Clear description of the issue

**Steps to Reproduce**:
1. Step one
2. Step two
3. Step three

**Expected Behavior**:
What should happen

**Actual Behavior**:
What actually happens

**Environment**:
- OS: Windows 11 / WSL Ubuntu 22.04 / etc.
- Python: 3.11.x
- Ollama: 0.12.9
- Model: qwen2.5-coder

**Error Messages** (if any):
```
Error output here
```

**Workaround** (if found):
Temporary solution

**Resolution** (when fixed):
How it was fixed, which commit/date
```

---

## Common Issues & Solutions

### "Cannot connect to Ollama"
**Type**: Configuration  
**Solution**: 
1. Check Ollama is running: `ollama list`
2. Start if needed: `ollama serve`
3. Check port 11434 is accessible

### "Model not found"
**Type**: Configuration  
**Solution**:
1. Pull the model: `ollama pull qwen2.5-coder`
2. Verify: `ollama list`

### "Module not found" errors
**Type**: Installation  
**Solution**:
1. Activate venv: `source venv/bin/activate`
2. Reinstall: `pip install -r requirements.txt`

### "Permission denied" on scripts
**Type**: File Permissions  
**Solution**:
```bash
chmod +x install_wsl.sh start_wsl.sh
```

### "Out of memory" during batch processing
**Type**: Performance  
**Solution**:
1. Use smaller batches (5-10 files)
2. Use smaller model (mistral instead of qwen2.5-coder)
3. Close other applications

### Parsing returns "Grade: N/A"
**Type**: LLM Output  
**Solution**:
1. Enable "Use LLM-based parsing" option
2. Lower temperature (0.1-0.3)
3. Simplify grading criteria
4. Check "Raw LLM Output" tab to see what model returned

---

## Issue Categories

- **Bug**: Something broken that should work
- **Enhancement**: New feature or improvement request
- **Performance**: Speed or resource usage issue
- **Documentation**: Missing or incorrect docs
- **Configuration**: Setup or installation issue
- **Compatibility**: Works on some systems but not others
- **Security**: Security vulnerability or concern

---

## Severity Levels

- **Critical**: System unusable, data loss, security breach
- **High**: Major feature broken, significant impact
- **Medium**: Feature partially broken, workaround exists
- **Low**: Minor issue, cosmetic, edge case

---

## Status Values

- **Open**: Issue reported, not yet investigated
- **In Progress**: Currently being worked on
- **Resolved**: Issue fixed and verified
- **Won't Fix**: Issue acknowledged but will not be fixed
- **Cannot Reproduce**: Unable to verify issue
- **Duplicate**: Same as another issue
- **By Design**: Working as intended, not a bug

---

## How to Use This File

### When You Encounter a Bug:
1. Check if already listed in Active Issues
2. If not, add it using the template
3. Try to find workaround
4. Report in DEVELOPMENT_LOG.md
5. Attempt to fix or note for future

### When You Fix a Bug:
1. Update status to "Resolved"
2. Add resolution date
3. Describe the fix
4. Move to "Resolved Issues" section
5. Update CHANGELOG.md
6. Update DEVELOPMENT_LOG.md

### Before Making Changes:
1. Check if you're fixing a known issue
2. Reference issue number in commits
3. Cross-reference with DEVELOPMENT_LOG.md

---

## Contributing

If you're not the original developer:
1. Check this file before starting work
2. Add issues you encounter
3. Update when you fix something
4. Keep descriptions clear and actionable

---

**Maintained By**: AI Assistant (with user oversight)
**Format**: GitHub-style issue tracking
**Location**: `E:\GradingSystem\BUGS_AND_ISSUES.md`

