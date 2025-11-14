# Changelog

All notable changes to the Grading Assistant System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Canvas Spreadsheet View (Bulk Edit)**: New spreadsheet-style interface for reviewing and editing multiple Canvas grades at once
  - Editable dataframe showing all submissions with: Student, Parsed Grade (reference), Final Grade (editable), Comments (editable), Submission preview, Detailed Feedback, Raw JSON preview, Needs Review status
  - "Load Spreadsheet" button to populate all grades from a grading session
  - "Save All Changes" button for bulk updating all modified grades in one operation
  - "Mark All as Reviewed" checkbox to approve all grades simultaneously
  - "Export Full CSV" button to download complete grade dataset (untruncated) for offline review/archiving
  - Complements existing one-by-one grade editor (both workflows available based on instructor preference)
  - CSV exports saved to `data/canvas_exports/` with timestamp
  - New handlers: `load_grades_spreadsheet()`, `save_bulk_grades()`, `export_grades_csv()` in `src/ui/canvas_handlers.py`
- **Canvas LMS Integration**: Complete workflow for downloading, grading, and uploading Canvas assignments
  - New Canvas LMS tab with authentication, course/assignment selection, and grading configuration
  - Canvas API client (`src/canvas_client.py`) for all Canvas operations (auth, courses, assignments, submissions, grade uploads)
  - Canvas grading manager (`src/canvas_grading_manager.py`) orchestrates download → LLM grading → storage workflow
  - Three new database tables: `canvas_credentials`, `canvas_grading_sessions`, `canvas_submission_grades`
  - Stores BOTH raw LLM JSON output AND parsed results for manual verification and debugging
  - Session-based grading with historical record of all grading attempts
  - Grade review interface with inline editing, raw JSON viewing, and manual override
  - Filter grades by status (All / Needs Review / Ready to Upload)
  - Batch or individual grade upload to Canvas
  - Secure token encryption using `cryptography.fernet`
  - UI handlers in `src/ui/canvas_handlers.py` for all Canvas operations
  - Added `cryptography>=41.0.0` dependency

### Removed
- **Simple Layout**: Removed unused Simple Layout code (dead code cleanup)
  - Simple Layout was never accessible to users (no toggle button, always hidden)
  - Split View serves the same purpose with better UX
  - Removed ~200 lines of code including UI components, functions, and event handlers
  - Simplified `toggle_view_mode` function to only handle Classic ↔ Split views
  - No user-facing impact (feature was never visible)

### Changed
- **Responsive Design**: Implemented adaptive scaling for ultrawide and Full HD displays
  - CSS custom properties with media queries for automatic size adjustment
  - 3440x1440 (Ultrawide): Larger fonts (14px base), spacious buttons and inputs
  - 1920x1080 (Full HD): Medium fonts (13px base), balanced layout
  - < 1920px: Compact fonts (12px base), optimized for smaller screens
  - All UI elements scale proportionally: text, buttons, inputs, spacing, checkboxes
  - No manual zoom required - optimal readability at native resolution
  - Smooth transitions between breakpoints for consistent experience
- **Input Order**: File submission now appears before text submission in all views
  - Classic View: File upload (left column) → Text submission (right column)
  - Split View: File upload → Text submission (vertical order)
  - More intuitive workflow for file-based grading (PDFs, DOCX, images)
- **Repository Data Handling**: Updated `.gitignore` and `.containerignore` so the `data/` directory is tracked in Git and copied into container builds, improving portability when running on new machines

### Added
- **Podman Container Support**: Added container artifacts for portable deployment
  - New `Containerfile` builds a Python 3.11 image that installs project dependencies and exposes Gradio on port 7860
  - `podman-run.sh` script builds/runs the image, mounts the host `data/` directory, reuses `.env`, and forwards port 7860
  - Script auto-detects the best `OLLAMA_HOST` (uses `host.containers.internal` for native Podman on Windows/macOS, falls back to detected Windows IP in WSL) while still allowing manual overrides
  - Created `.containerignore` to keep the image lean by excluding virtual envs, caches, and local data during build
- **Copy Grade Button**: Added one-click copy button for extracted grade
  - Button appears in the header next to "Extracted Grade" (top-right corner)
  - Same distinctive blue styling as student feedback copy button for consistency
  - Available in both Classic and Split views
  - Convenient for quickly copying grades to LMS gradebooks or spreadsheets
- **Copy Student Feedback Button**: Added one-click copy button for student feedback
  - Button appears in the header of student feedback panel (top-right corner)
  - Distinctive blue background (#2563eb) with hover effect for easy identification
  - Uses JavaScript clipboard API for instant copying
  - Shortened text "📋 Copy" for compact header placement
  - Convenient for pasting feedback into email, LMS, or other communication tools
- **Split View Layout**: New streamlined layout mode for quick grading
  - Toggle between "Classic View" and "Split View" using two buttons at the top
  - Active button styling: Blue border and background (#0066ff) to show current mode
  - Split View features:
    - Left panel: Input controls (text submission, file upload, grade button, clear button)
    - Right panel: All grading outputs (grade, feedback, strengths, weaknesses, deductions, statistics, human correction, debug prompts)
    - Submission preview excluded from split view (not needed for streamlined workflow)
    - Uses course/profile data from Classic View sidebar (no duplication)
  - Perfect for quick grading sessions without needing course/profile management UI
  - Fully integrated with existing grading engine and course/profile system

### Fixed
- **Canvas Rate Limit Parsing Error**: Fixed "invalid literal for int() with base 10: '700.0'" error
  - Root cause: Canvas API returns rate limit as decimal string (e.g., "700.0"), but code used `int()` directly
  - Solution: Changed to `int(float(remaining))` with try-except fallback to safe default (600)
  - This fix was implemented twice due to code reformatting removing the original fix
- **Canvas Grading Error**: Fixed "GradingEngine.grade_submission() got an unexpected keyword argument 'model'" error
  - Root cause: `canvas_grading_manager.py` was passing `model=` and `clear_context=` arguments to `grade_submission()` which doesn't accept them
  - Solution: Set model on `llm_client` before grading loop, removed invalid arguments, fixed result parsing to use `result["parsed_result"]`
  - Added explicit `llm_client.clear_context()` call after each submission for proper context isolation
- **Canvas File Attachments**: Implemented full download and parsing for Canvas file submissions
  - Added `download_attachment()` method to `canvas_client.py` for authenticated file downloads
  - Modified grading loop to download all attachments to `data/canvas_submissions/{course_id}/{assignment_id}/`
  - Integrated with `document_parser` to extract text from PDF, DOCX, and image files
  - Combined all parsed text into submission for LLM grading
  - Added comprehensive error logging to `data/logs/canvas_errors.log` with full tracebacks
  - Robust error handling for download failures, parse failures, and empty files
- **Split View Grading Error (ROOT CAUSE FIXED)**: Completely resolved `'int' object has no attribute 'to_json'` error
  - Root cause: `split_context_bar` was created as `gr.BarPlot` instead of `gr.Slider`
  - Issue: BarPlot expects complex data structure, but grading function returns integer percentage
  - Fix: Changed `split_context_bar` from `gr.BarPlot(visible=False)` to `gr.Slider(minimum=0, maximum=100, value=0, interactive=False, visible=False)`
  - Now matches full layout and simple layout which both use Slider for context usage
  - Split view grade button now fully functional
- **Split View Grading Error (FINAL FIX)**: Completely resolved `'int' object has no attribute 'to_json'` error
  - Root cause: Validation failure case was creating `gr.BarPlot` object instead of returning integer value
  - Key insight: `context_bar` BarPlot component expects integer percentage (0-100), not a BarPlot object
  - Fixed line 120: Changed from `gr.BarPlot(value=None, visible=False)` to `0`
  - Split view grade button now fully functional with text/file input and validation
- **Split View Grading Error (Critical Fix)**: Fixed persistent `'int' object has no attribute 'to_json'` error
  - Root cause: Generator function `conditional_grade_with_loading` used `return` instead of `yield` for validation failure
  - Changed validation failure from `return (...)` to `yield (...)` to properly update existing components
  - Split view grade button now works correctly with text input, file upload, and validation
- **Split View Grading Error**: Fixed `'int' object has no attribute 'to_json'` error
  - Added hidden output components to split_layout_row for compatibility with grading function
  - Split view grade button now works correctly with all 12 expected outputs
- **Theme Inconsistency**: Completely restored original dark theme
  - Removed incomplete light theme rollback
  - Restored dark theme configuration (#0a0a0a backgrounds, #f0f0f0 text)
  - Theme is now consistent throughout the application

### Removed
- **Theme Toggle Feature**: Removed light/dark theme switcher per user request
  - Removed theme_selector Radio button
  - Removed theme_toggle_js JavaScript (~20 lines)
  - Removed dual light/dark theme CSS (~70 lines)
  - Simplified CSS to single dark theme only
  - Cleaned up ~150 lines of unnecessary theme switching code
- **System Prompt Redesign**: Completely rewrote grading prompt for better feedback quality
  - New layout mode selector at top of interface (Radio button)
  - **Full Layout**: Original layout with course/profile management on left, tabs on right
  - **Simple Layout**: Simplified two-column layout (Input left, Output right) for quick grading
  - Simple layout includes:
    - Large input textbox (20 lines) and file upload on left
    - Grading settings in collapsed accordion (instructions, rubric, format, model, etc.)
    - All grading results displayed on right panel
    - No tabs needed - everything visible at once
  - Layout toggle switches between modes without losing data
  - Simple layout validates instructions and rubric before grading
  - Both layouts use the same grading engine and validation logic
- **Vision Model Support Planning**: Added comprehensive documentation for future vision/image understanding capabilities
  - Documented in FUTURE_PLANS.md (section 5.5) as "Planning Phase, Low Priority, High Complexity"
  - Details current OCR capabilities vs. future vision model needs
  - Includes requirements, technical challenges, dependencies, and implementation steps
  - Note: This is a planned feature, not implemented yet
- **Future Features Implementation Rules**: Added critical rules to .cursorrules to prevent accidental implementation
  - New "For Future Features / TODO Items" workflow section
  - Rule: FUTURE_PLANS.md items are for planning only, not immediate implementation
  - Only implement when user explicitly requests (e.g., "implement this", "do this now")
  - Added special case handling for when users mention FUTURE_PLANS features
- **Input Validation**: Grade button now validates input before processing
  - Checks if text or file is provided before grading
  - Shows clear error message: "⚠️ No input provided. Please paste text or upload a file before grading."
  - Stays on Input tab instead of switching to Output when validation fails
  - Prevents wasted LLM calls on empty input
- **Robust AI Disclosure Analysis**: Comprehensive error handling for AI disclosure checks
  - Multi-strategy JSON parsing (markdown blocks, balanced braces, greedy fallback)
  - Empty response detection with informative messages
  - Default field values for missing data
  - Category-specific error messages (JSON parse, empty response, LLM failure)
  - Detailed troubleshooting suggestions in UI
  - Clear reminder that grading continues even if disclosure check fails
- **Smart Field Extraction**: Parser now intelligently extracts missing fields
  - Automatically detects and extracts student_feedback from detailed_feedback when LLM combines them
  - Recognizes patterns: "Student Feedback:", "Feedback for student:", etc.
  - Removes extracted student feedback from detailed_feedback to avoid duplication
  - Philosophy: "Parse as much as you can" - graceful degradation over strict validation
  - Works even when LLM doesn't follow exact JSON structure
- **Ollama Connection Health Check**: App now verifies Ollama connectivity on startup

### Changed
- **LLM Feedback Style**: Instructed LLM to avoid generic praise and be more direct
  - No more "Good job", "Great work", "Keep up the good work", "Well done"
  - Focus on specific, actionable feedback with examples
  - Professional but straightforward - no unnecessary compromises or sugar-coating
  - Explains WHY something is good rather than just saying it is
- **UI Simplified**: Removed "Clear Text" button - only "Clear All" button remains (clears both text and file)

### Changed
- **UI Component Repositioning**: Improved layout of input components
  - Text Submission moved back to left column (more prominent)
  - File Submission moved to right column
  - Clear All button moved under Grade button (related actions together)
  - Applied to both Full Layout and Simple Layout
  - Better workflow: primary text input is on the left, clear action with grade action
- **Feedback Cleanup: Remove Generic Praise Phrases** - Student feedback now filtered to remove generic phrases
  - Removes: "Keep up the good work!", "Well done!", "Good job!", "Great job!", "Keep it up!", etc.
  - System prompt already instructs to avoid these, but this is a safety net
  - Applied after JSON parsing to both detailed and student feedback
  - Results in more focused, actionable feedback

### Fixed
- **Enhanced JSON Parser Robustness**: Improved parser to handle edge cases and extract grades from malformed JSON
  - Problem: Grade showing "N/A" and feedback fields displaying JSON format instead of parsed text
  - Solution: Multiple parser improvements:
    1. Improved brace matching that correctly handles braces inside string literals
    2. Robust grade extraction with support for various formats (string, number, None, empty)
    3. New field extraction fallback that extracts individual fields using regex when full JSON parsing fails
    4. Feedback validation that detects and corrects raw JSON in feedback fields
  - Result: Parser now successfully extracts grade "16" even from slightly malformed JSON
  - Backward compatible: All existing JSON formats continue to work correctly
  - Testing: Added `tests/test_json_parsing_regression.py` for ongoing regression testing
    - Contains user's exact JSON format as canonical test case
    - Documented in `.cursorrules` as mandatory test after parser changes
    - Ensures backward compatibility is maintained
- **Layout Component Value Sync**: Fixed simple layout to preserve grading settings when switching modes
  - Problem: Switching to simple layout showed "Instructions required" error
  - Root cause: Simple layout components were separate and empty
  - Solution: Added bidirectional value sync when toggling between layouts
  - All 11 grading settings now persist across layout switches (instructions, rubric, format, model, temperature, AI keywords, etc.)
  - Switching from full to simple: copies values from full layout
  - Switching from simple to full: copies values from simple layout back
- **Grading Button Error**: Fixed critical error where grading button returned generator object instead of yielding values
  - Changed `return grade_with_loading()` to `yield from grade_with_loading()` in `conditional_grade_with_loading()`
  - Error was: "A function didn't return enough output values (needed: 12, returned: 1)"
  - Root cause: returning a generator gives 1 object, yielding from it gives 12 separate values
  - Grading now works correctly with all 12 output fields populated
  - AI Detection Keywords already handled as optional throughout pipeline (no changes needed)
- **Save Profile Button Error**: Fixed "Save as New Profile" button that threw "Textbox.__init__() got unexpected keyword 'choices'"
  - Changed all profile handler functions to use `gr.update()` instead of `gr.Dropdown()` for dropdown updates
  - Fixed return value counts: `create_profile()` returns 4 values, `update_profile_action()` returns 10 values, `delete_profile_action()` returns 4 values
  - All dropdown updates now use correct Gradio update format
  - Button now works correctly and profile list refreshes after creation
- **Create Course Button Not Working**: Fixed course creation button that was not completing
  - Fixed return value mismatch: `create_course()` now returns 2 values matching 2 outputs
  - Changed dropdown updates to use `gr.update()` instead of `gr.Dropdown()` objects
  - Updated all course handler functions (`create_course`, `update_course_action`, `delete_course_action`, `load_courses_dropdown`) to use correct Gradio update format
  - Button now works correctly and dropdown refreshes after course creation
- **JSON Parsing Failure**: Fixed grading output displaying raw JSON instead of parsed fields
  - Implemented multi-strategy JSON parsing with 3 fallback methods
  - Strategy 1: Extract from markdown code blocks (```json ... ```)
  - Strategy 2: Balanced brace matching for robust JSON extraction
  - Strategy 3: Greedy regex as last resort
  - Added debug logging for each parsing attempt
  - Extracted helper method `_build_parsed_result()` for cleaner code
  - Now correctly extracts grade, detailed_feedback, and student_feedback
  - Handles JSON with surrounding text or formatting issues
- **AI Disclosure Analysis TypeError**: Fixed crash when LLM returns incomplete or invalid JSON
  - Added null-safety checks for `disclosure_statement` and `evidence` fields
  - Safe string slicing prevents `NoneType` subscriptable errors
  - Improved error messages: "LLM returned invalid response" instead of raw JSON errors
  - Graceful handling of all AI disclosure edge cases
  - No more crashes when AI disclosure analysis fails
- **Submission Preview Display**: Shows filename and first 5 lines at top of Output tab
  - Displays immediately when grading starts, before LLM processing
  - Shows filename (or "Direct Text Submission" for pasted text)
  - Shows total character count and line count
  - Shows first 5 lines of submission (truncates long lines >100 chars)
  - Helps instructors identify which student's work is being graded
  - Provides quick context without switching tabs
  - Added collapsible accordion for preview in Output tab
- **Auto-Switch to Output Tab**: Automatically switches to Output tab when grading starts
  - User clicks "Grade" → UI immediately switches to Output tab → Shows "Processing..." → Displays results
  - Eliminates manual tab switching step
  - Provides immediate visual feedback for better UX
  - Uses Gradio's chained event handlers for seamless transition
- **Database Migration System**: Automatic schema migration for existing databases
  - Added `_migrate_criteria_text_to_rubric()` method to `DatabaseManager`
  - Automatically detects and migrates old `criteria_text` column to `rubric`
  - Runs on every app startup with clear status messages
  - Preserves all existing user data during migration
  - Handles edge cases: old schema, new schema, partial migration, corrupted schema
  - Non-blocking: app continues even if migration encounters issues
- **Modular Architecture**: Restructured entire codebase for better maintainability
  - Created new `src/ui/` module with clean separation of concerns
  - `src/ui/course_handlers.py`: All course CRUD operations (5 functions, 90 lines)
  - `src/ui/profile_handlers.py`: All profile CRUD operations (7 functions, 273 lines)
  - `src/ui/grading_handlers.py`: All grading and feedback operations (14 functions, 575 lines)
  - Main `src/app.py` reduced from 1422 lines to 613 lines
  - NO breaking changes - all existing functionality preserved
  - Each module is now self-contained and easier to test/debug
  - Eliminates cascading indentation errors that plagued the monolithic file

### Changed
- **Clear Button Layout**: Reorganized Input tab for better UX
  - Moved both "Clear Text" and "Clear All" buttons under file uploader column
  - Removed clear button from under text submission area
  - Creates a more logical grouping with action buttons in one location
  - Cleaner, more intuitive interface layout
- **Model Selection Logic**: Now dynamically loads only installed Ollama models
  - Removed hardcoded fallback list of 5 models (qwen2.5-coder, llama3.1, mistral, qwen2.5, deepseek-r1)
  - Model dropdown now shows ONLY models actually installed in your Ollama instance
  - Added helpful error message "⚠️ No models found - Check Ollama" if Ollama unreachable
  - Added 3-second timeout to prevent UI hanging during Ollama connection attempts
  - Better error handling with specific connection failure messages
  - Auto-selects first available model as default
- **Tab Scrolling Behavior**: Removed sticky positioning for simpler, more reliable UX
  - Removed `position: sticky` from system messages and tab navigation bars
  - Removed `overflow-y: auto` and `max-height` constraints on tab content
  - Removed `z-index` stacking complexity
  - Simplified CSS from 44 lines to 31 lines (13 lines removed)
  - Result: Normal scroll flow that works consistently across all content heights
  - No more floating/sticky elements that caused layout issues
- **Tab Visual Styling**: Normalized all tab components for consistent appearance
  - All tabs now have identical button sizes (100px min-width, 44px height)
  - Consistent padding (10px 16px) and margins (2px) for all tab buttons
  - Unified container styling with normalized margins and padding
  - Both left panel (Courses/Profiles) and right panel (Input/Output/Batch/Feedback) tabs now match visually
  - Fixed inconsistencies caused by different tab counts and hierarchies
  - Added border-radius (4px) for polished button appearance
- **AI Detection Prompt System**: Redesigned for silent, professional keyword detection
  - Restructured system prompt with explicit "Do NOT mention keywords in feedback" instructions
  - Changed "AI Detection Keywords" to "SILENT KEYWORD DETECTION (Internal Use Only)"
  - Added 3 critical reminders throughout prompt to prevent keyword leakage
  - Keywords now only appear in `ai_detection_keywords` JSON field, never in student-facing feedback
  - Student feedback remains professional and focused on work quality
  - Preserves academic integrity by not alerting students to detection
- **Output Tab Layout**: Reorganized into 2-column layout for better workflow
  - Left column (scale=3): Grading Results (grade, AI detection, feedback, context, debug)
  - Right column (scale=2): Human Correction & Feedback for easy side-by-side comparison
  - Improves efficiency when reviewing and correcting AI grading
- **Font Sizes Reduced**: Global font size reduction for more condensed UI
  - Base font: 12px → 11px
  - H1: 20px → 18px
  - H3: 13px → 12px
  - Entire interface now more compact and fits more information on screen
- **Database Schema Consistency**: Renamed `criteria_text` field to `rubric` throughout entire codebase
  - Updated database.py: CREATE TABLE, create_criteria(), update_criteria()
  - Updated app.py: load_profile_into_fields()
  - Updated profile_manager.py: create_assignment_profile(), duplicate_assignment(), export_profile(), import_profile()
  - Provides more intuitive and user-friendly field naming

### Fixed
- **CRITICAL: AI Detection Text Leaking into detailed_feedback (Second Fix)**
  - **Problem**: LLM was including "AI Detection Keywords: []" as literal text inside the `detailed_feedback` field
  - **Root Cause**: Previous fix prevented keyword mentions but not the "AI Detection Keywords:" label text itself
  - **Solution**: Enhanced prompts in `src/grading_engine.py` with explicit instructions
  - Added 3 new system prompt instructions: "do NOT write 'AI Detection Keywords:' as text", "NEVER include phrases like 'AI Detection Keywords: []'", "data goes ONLY in JSON array field"
  - Added 7 JSON format reminders in user prompt explicitly forbidding text labels
  - **Result**: The `ai_detection_keywords` array is now completely separate from feedback text
- **CRITICAL: AI Detection Keywords Leaking into Student Feedback**
  - **Problem**: Keywords like "histocompatibility" were appearing in student feedback (e.g., "I appreciate the use of 'histocompatibility'..."), alerting students they were flagged
  - **Root Cause**: Old prompt explicitly told LLM about keywords, making it treat them as grading criteria
  - **Solution**: Redesigned prompts with "SILENT KEYWORD DETECTION" section and multiple "Do NOT mention" instructions
  - **Result**: Keywords now only appear in instructor's `ai_detection_keywords` field, never in student-facing text
  - **Impact**: Preserves academic integrity by not alerting students to detection
- **"No such column: rubric" Error**: Fixed database schema mismatch causing profile update failures
  - Root cause: Code was updated to use `rubric` but existing databases still had `criteria_text` column
  - Solution: Added automatic migration that renames column on first startup
  - Users with existing databases will see migration message and data is preserved
  - New installations work correctly with `rubric` column from the start
- **Critical Rubric Bug**: Fixed profile rubric field not loading or saving correctly
  - Root cause: `load_profile_to_criteria()` was using wrong database field name (`criteria_text` instead of `rubric`)
  - Changed to `criteria.get('rubric', '')` in `src/ui/profile_handlers.py`
  - Rubric now loads and saves correctly when selecting/updating profiles
  - This was preventing users from viewing or editing grading criteria
- **Profile Auto-Load Event**: Fixed profile dropdown not loading rubric and other fields
  - Changed from `.change()` to `.select()` event handler
  - `.select()` fires specifically on user selection, not programmatic updates
  - Ensures reliable loading of all form fields when a profile is selected
- **Grade Parsing Logic**: Fixed issue where valid grades (like "85") were showing as "N/A"
  - Changed logic to only trigger LLM fallback parsing when grade is actually missing
  - Previously would re-parse valid JSON if "Use LLM Parse" checkbox was checked
  - Now preserves valid grades from initial JSON parse
- **Profile Update UI Refresh**: Fixed issue where form fields (especially rubric) didn't refresh after clicking update button
  - Modified `update_profile_action()` to return updated form field values after database update
  - Updated event handler to refresh all 6 form fields (instructions, rubric, format, score, keywords, requirements)
  - Users now see their changes immediately reflected in the UI
- **Profile Loading Error**: Fixed `KeyError: 'rubric'` when selecting a profile from dropdown
- **Multiple Indentation Errors**: Corrected inconsistent indentation in app.py that prevented startup (lines 943, 1042-1054, 1058-1059, 1088, 1097, 1107, 1112, 1134, 1151-1157)

### Removed
- **Redundant Load Profile Button**: Removed separate "Load Profile" button
  - Profile dropdown now auto-loads on selection via existing `.change()` event
  - Simplifies UI and reduces user clicks
  - Delete button is now standalone for clarity

### Added
- **Few-Shot In-Context Learning**: System now uses saved "good examples" to guide LLM grading
  - New `select_few_shot_examples()` function that selects up to N good examples
  - Examples formatted with grade, reasoning, and effectiveness notes
  - Integrated into grading prompt before submission
- **Few-Shot UI Controls**: New settings in grading section
  - Checkbox: "Enable few-shot learning" (default: ON)
  - Slider: Choose 0-5 examples to use (default: 2)
  - Visual feedback when examples are being used
- **FUTURE_PLANS.md**: Comprehensive roadmap for intelligent example selection
  - Embedding-based similarity search
  - Performance tracking per example
  - Adaptive user preference learning
  - Category/assignment-type matching
- **Enhanced Feedback Table Styling**: Dramatically improved readability
  - White background with dark text (#000000)
  - Blue headers (#0066ff) with white text
  - Alternating row colors with hover effects
  - Clear borders and padding
- **Improved AI Detection Messages**: More explicit and user-friendly
  - "🚨 AI KEYWORDS DETECTED" with full explanation when keywords found
  - "✅ NO AI KEYWORDS DETECTED" with reassurance when clean
  - Clear visibility in dedicated output field
- **Prompt & Feedback Tab**: New "🔍 Prompt & Feedback" tab to view LLM prompts and provide feedback
  - Display system prompt (LLM instructions)
  - Display user prompt (submission + criteria)
  - Feedback text area for user criticism
  - "Mark as good example" checkbox for in-context learning
  - Saves feedback to `data/feedback/` as JSON files
- **Tree Structure View**: Hierarchical display showing courses with their profiles
  - Visual tree showing Course → Profile relationships
  - Clear ID display for easy selection: [ID:123]
  - Shows orphan profiles (not assigned to any course)
- **Create/Edit Toggle**: Mode switch for course and profile management
  - Radio button to toggle between Create and Edit modes
  - Edit mode shows selection field + delete button
  - Cleaner workflow with single form for both operations
- **Smaller Font Sizes**: Condensed UI (12-13px) for better content density
- **Enhanced Dropdown Contrast**: CSS-based fixes for visibility
  - Dropdown text: #f0f0f0 on #1a1a1a background
  - Hover states: #333333 background
  - Clear borders and focus states
- **Profile-Course Connection**: Profiles now properly linked to courses in tree
- `.cursorrules`, `CHANGELOG.md`, `BUGS_AND_ISSUES.md`, `DEVELOPMENT_LOG.md`
- `.cursorignore`, `.gitignore`, `IGNORE_FILES_GUIDE.md`
- `configure_ollama.sh`, `INSTALLATION_COMPLETE.md`, `.env`

### Fixed
- **Feedback table selection error**: Fixed `NoneType' object has no attribute 'value` error
  - Replaced broken lambda with proper `handle_table_select()` function
  - Uses Gradio's SelectData event with proper index handling
  - Now correctly extracts filename from selected row
- **Feedback table readability**: Fixed similar text/background colors
  - Applied comprehensive CSS overrides for dataframe
  - Dark text on white background for maximum contrast
  - Blue headers with white text for clear visual hierarchy
- **AI detection output clarity**: More explicit messaging
  - Before: "✅ No AI keywords detected" (minimal)
  - After: "✅ NO AI KEYWORDS DETECTED\n\nNo suspicious AI-related phrases found in submission."
  - Clear warnings when keywords ARE detected with full context
- **Numeric grading format** - LLM now correctly returns numeric scores (0-100) instead of letter grades when profile uses numeric format (emphatic prompt rewrite)
- **Profile update error** - Fixed `AttributeError: create_grading_criteria method not found` (corrected to `create_criteria`)
- **Radio button/checkbox visibility** - Completely redesigned CSS with:
  - Clear selected states using `:has()` pseudo-class
  - Blue border (#0066ff) with glow effect for selected items
  - Blue-tinted background (#1a3a5a) for selected state
  - Larger 20px inputs with better contrast
  - Smooth hover transitions

### Changed
- **src/grading_engine.py**: Added `few_shot_examples` parameter to `build_grading_prompt()` and `grade_submission()`
  - Examples are injected into prompt before student submission
  - Formatted with clear markdown for LLM consumption
- **src/app.py**: Major updates for few-shot learning and bug fixes
  - Added `select_few_shot_examples()` function (random/recent selection from good examples)
  - Added `handle_table_select()` function (proper Gradio SelectData handling)
  - Updated `grade_submission()` to accept and use `use_few_shot` and `num_examples` parameters
  - Updated `grade_with_loading()` wrapper to pass through few-shot parameters
  - Enhanced AI detection messages in output formatting
  - Added comprehensive CSS for dataframe/table styling
- **Grading UI**: New few-shot controls added between Temperature and AI Detection sections
- **Event handlers**: Updated `grade_btn.click()` and `feedback_table.select()` with new parameters
- **Prompt builder enhanced** - Added explicit format instructions with examples for numeric vs letter grading
- **Grade submission function** - Now returns system and user prompts for display
- **Complete UI Redesign**: Tree-based management (~650 lines)
- **src/app.py**: Tree view with create/edit toggles
  - Left: Tree view + Course/Profile tabs with mode toggles
  - Right: Input/Output/Batch tabs
  - Font sizes reduced to 12-13px
  - All heights optimized for single-page view
- **src/database.py**: Added `update_assignment()` method
- **Management Workflow**: Select from tree, toggle to Edit mode, modify
- `requirements.txt` - Removed sqlite3 (built-in to Python)
- `src/llm_client.py` - Added dotenv support
- `start_wsl.sh` - Updated launcher

### Fixed
- Installation error with sqlite3 dependency
- Ollama WSL connectivity (Windows host IP auto-detection)
- Missing `get_all_criteria` method
- Course and profile not properly connected - now shows hierarchy
- Dropdown text invisible - fixed with CSS overrides
- Font too large - reduced to 12-13px
- UI too tall - now fits one page

### Removed
- None

---

## [1.0.0] - 2025-11-02

### Added

#### Phase 1: Core Infrastructure
- `src/llm_client.py` - Ollama client with model management
- `src/grading_engine.py` - Core grading logic and prompt building
- `src/app.py` - Main Gradio UI (775+ lines)
- Support for multiple LLM models (qwen2.5-coder, llama3.1, mistral, etc.)
- Context management (clear/continue modes)
- Dual feedback system (detailed for instructor, concise for student)
- Raw and formatted input/output display
- JSON, regex, and LLM-based output parsing
- AI keyword detection system
- Connection status checking

#### Phase 2: File Upload & Batch Processing
- `src/document_parser.py` - Multi-format document parser
- `src/batch_processor.py` - Concurrent batch processing
- PDF parsing support (PyPDF2)
- DOCX/DOC parsing support (python-docx)
- Plain text parsing with multiple encoding support
- Image OCR support (pytesseract + Pillow)
- ThreadPoolExecutor for concurrent grading (max 3 workers)
- Progress tracking with callback system
- Results table display
- CSV and JSON export

#### Phase 3: Plagiarism Detection
- `src/plagiarism_checker.py` - Text similarity detection
- Pairwise comparison using SequenceMatcher
- Suspicion level classification (high/medium/low/none)
- Configurable similarity thresholds (80%/60%/40%)
- Batch plagiarism checking
- Human-readable plagiarism reports
- Integration with batch processor

#### Phase 4: Profile & Prompt Management
- `src/database.py` - SQLite database operations
- `src/profile_manager.py` - Course and assignment management
- `src/prompt_builder.py` - Template system
- 6 normalized database tables (courses, assignments, criteria, templates, history)
- Complete CRUD operations for courses and assignments
- Grading criteria storage and management
- Prompt template system with variable substitution
- Template inheritance and duplication
- Profile export/import functionality
- Grading history tracking
- Good example marking for training

#### Phase 5: Advanced Parsing & Feedback
- `src/criteria_parser.py` - Multi-format criteria parser
- `src/output_parser.py` - Multi-strategy output parser
- `src/feedback_collector.py` - Human feedback collection
- Auto-format detection (JSON, YAML, bullets, plain text)
- Natural language conversion for criteria
- Three-strategy parsing (JSON → regex → LLM)
- Confidence scoring for parsed results
- Human feedback collection interface
- Training data preparation
- Feedback dataset export (JSONL/JSON)

#### Phase 6: In-Context Learning
- `src/few_shot_manager.py` - Few-shot learning management
- Example quality evaluation system (0-100 scoring)
- Multiple selection strategies (best, diverse, recent)
- Few-shot prompt building (structured/conversational)
- System and user prompt augmentation
- Example recommendation system
- Foundation for LoRA/QLoRA fine-tuning (PEFT library)

#### Phase 7: Internet Search & Reference Verification
- `src/web_search.py` - Web search integration
- `src/reference_verifier.py` - Citation verification
- DuckDuckGo search API integration
- URL extraction from submissions
- Citation pattern extraction (Author, Year), [1], etc.
- Reference verification with confidence scoring
- Verification report generation
- Reference improvement suggestions

#### Phase 8: Export & Reporting
- `src/export_manager.py` - Multi-format export
- `src/report_generator.py` - Comprehensive report generation
- CSV export (full/summary options)
- JSON export (pretty/compact)
- Excel export with formatting (openpyxl)
- PDF report generation (fpdf2)
- HTML report generation (styled, interactive)
- Summary statistics export
- Grade distribution visualization
- Plagiarism summaries in reports
- Timestamped filenames

#### Documentation
- `README.md` - Comprehensive user documentation
- `QUICKSTART.md` - Quick start guide with examples
- `INSTALL.md` - Complete installation guide
- `INSTALL_WSL.md` - WSL-specific installation guide
- `IMPLEMENTATION_SUMMARY.md` - Technical summary
- `BUILD_PLAN.md` - Complete architecture documentation
- `QUICK_REFERENCE.md` - Quick command reference

#### Installation Scripts
- `install.ps1` - Windows PowerShell installer (venv)
- `install.sh` - Linux/Mac installer (venv)
- `install_conda.ps1` - Windows Conda installer
- `install_wsl.sh` - WSL Ubuntu/Debian installer
- `start_wsl.sh` - WSL quick launcher script

#### Configuration
- `requirements.txt` - Python dependencies (20+ packages)
- Project directory structure (data/, exports/, models/, prompts/)
- `.gitkeep` files for empty directory preservation

### Features

- **3-Tab Interface**: Text Input, File Upload, Batch Grading
- **5 Output Views**: Formatted, Detailed, Student, Raw, Input
- **7 File Formats**: PDF, DOCX, DOC, TXT, PNG, JPG, JPEG
- **5 Export Formats**: CSV, JSON, Excel, PDF, HTML
- **5+ LLM Models**: Any Ollama-compatible model
- **Concurrent Processing**: Up to 3 submissions simultaneously
- **Database-Backed**: SQLite with 6 normalized tables
- **Privacy-First**: Local LLM execution, no cloud dependencies
- **Cross-Platform**: Windows, Linux, macOS, WSL

### Technical Details

- **Total Files**: 17 Python modules, 7 documentation files, 5 installation scripts
- **Lines of Code**: ~5,000+ (excluding dependencies)
- **Python Version**: 3.10+ (tested with 3.11)
- **UI Framework**: Gradio 4.0+
- **LLM Backend**: Ollama
- **Database**: SQLite3
- **Testing**: Manual testing completed for all features

---

## Version History

- **1.0.0** (2025-11-02) - Initial release, all 8 phases complete
- **Unreleased** - Current development version

---

## Change Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

---

## How to Use This Changelog

1. **Before making changes**: Check if similar change was already made
2. **After making changes**: Add entry to [Unreleased] section
3. **When releasing**: Move [Unreleased] entries to new version section
4. **Always**: Keep changes organized by category
5. **Be specific**: Include file names and brief description

---

**Maintained By**: AI Assistant (with user oversight)
**Last Updated**: November 2, 2025

