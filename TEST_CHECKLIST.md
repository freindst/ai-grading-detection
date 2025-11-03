# UI Control Test Checklist

**Date**: November 2, 2025  
**Version**: 1.0.1 (Few-Shot Learning Update)  
**App URL**: http://localhost:7860

---

## ✅ **Test 1: Course Management**

### Test 1.1: Create New Course
- [ ] Navigate to "Course Management" tab
- [ ] Ensure "Create" mode is selected (radio button)
- [ ] Fill in: Course Name, Course Code (optional), Description (optional)
- [ ] Click "Create Course"
- [ ] **Expected**: Success message appears, course shows in dropdown
- [ ] **Status**: ___________

### Test 1.2: Edit Existing Course
- [ ] Navigate to "Course Management" tab
- [ ] Select "Edit" mode (radio button)
- [ ] Select a course from dropdown
- [ ] Modify course name
- [ ] Click "Update Course"
- [ ] **Expected**: Success message, course name updated in dropdown
- [ ] **Status**: ___________

### Test 1.3: Delete Course
- [ ] Navigate to "Course Management" tab
- [ ] Select "Edit" mode
- [ ] Select a course
- [ ] Click "Delete Course"
- [ ] **Expected**: Confirmation, course removed from list
- [ ] **Status**: ___________

---

## ✅ **Test 2: Profile Management**

### Test 2.1: Create New Profile
- [ ] Navigate to "Profile Management" tab
- [ ] Select "Create" mode
- [ ] Select a course from dropdown
- [ ] Enter profile name
- [ ] Fill in assignment instructions
- [ ] Fill in grading criteria (rubric)
- [ ] Click "Save Profile"
- [ ] **Expected**: Profile created and linked to selected course
- [ ] **Status**: ___________

### Test 2.2: Load Profile
- [ ] Select a course
- [ ] Select a profile from the profile dropdown
- [ ] **Expected**: Instructions and criteria populate in the grading setup panel
- [ ] **Status**: ___________

### Test 2.3: Edit Profile
- [ ] Navigate to "Profile Management" tab
- [ ] Select "Edit" mode
- [ ] Select profile from dropdown
- [ ] Modify instructions or criteria
- [ ] Click "Update Profile"
- [ ] **Expected**: Changes saved successfully
- [ ] **Status**: ___________

### Test 2.4: Delete Profile
- [ ] Select "Edit" mode
- [ ] Select a profile
- [ ] Click "Delete Profile"
- [ ] **Expected**: Profile removed (only the selected one, not all)
- [ ] **Status**: ___________

---

## ✅ **Test 3: Grading Controls**

### Test 3.1: Text Input Grading
- [ ] Navigate to "Input" tab
- [ ] Paste text into submission area
- [ ] Ensure instructions and criteria are filled
- [ ] Select output format (Letter/Numeric)
- [ ] Set temperature (0.3 recommended)
- [ ] Click "Grade Submission"
- [ ] **Expected**: Results appear in Output tab with grade, reasoning, feedback
- [ ] **Status**: ___________

### Test 3.2: File Upload Grading
- [ ] Navigate to "Input" tab
- [ ] Upload a file (.pdf, .docx, .txt, image)
- [ ] Ensure instructions and criteria are filled
- [ ] Click "Grade Submission"
- [ ] **Expected**: File parsed, grading completed
- [ ] **Status**: ___________

### Test 3.3: Output Format Selection
- [ ] Test with "Letter Grade (A-F)"
- [ ] **Expected**: LLM returns letter grade
- [ ] Test with "Numeric (0-100)"
- [ ] **Expected**: LLM returns numeric score
- [ ] **Status**: ___________

### Test 3.4: Temperature Adjustment
- [ ] Set temperature to 0.0 (deterministic)
- [ ] Grade same submission twice
- [ ] **Expected**: Very similar results
- [ ] Set temperature to 1.0 (creative)
- [ ] Grade same submission twice
- [ ] **Expected**: More variation
- [ ] **Status**: ___________

### Test 3.5: Model Selection
- [ ] Click "Refresh Models" button
- [ ] **Expected**: Dropdown updates with installed Ollama models
- [ ] Select different model
- [ ] **Expected**: Grading uses selected model
- [ ] **Status**: ___________

---

## ✅ **Test 4: Few-Shot Learning (NEW)**

### Test 4.1: Few-Shot Disabled (No Examples)
- [ ] Ensure no good examples saved yet (check Feedback Library tab)
- [ ] Enable few-shot checkbox ✓
- [ ] Set slider to 2-5 examples
- [ ] Grade a submission
- [ ] **Expected**: Message shows "Few-shot learning disabled: No good examples saved yet"
- [ ] **Status**: ___________

### Test 4.2: Few-Shot Disabled (Insufficient Examples)
- [ ] Save exactly 1 good example
- [ ] Enable few-shot checkbox ✓
- [ ] Set slider to 2+ examples
- [ ] Grade a submission
- [ ] **Expected**: Message shows "Only 1 example(s) saved, need at least 2 for effective learning"
- [ ] **Status**: ___________

### Test 4.3: Few-Shot Enabled (Enough Examples)
- [ ] Save at least 2 good examples (see Test 5 below)
- [ ] Enable few-shot checkbox ✓
- [ ] Set slider to 2 examples
- [ ] Grade a submission
- [ ] **Expected**: Message shows "✅ Using 2 good example(s) for few-shot learning"
- [ ] Check "Debug: Prompt Sent to LLM" - should contain example section
- [ ] **Status**: ___________

### Test 4.4: Few-Shot Slider
- [ ] Enable few-shot ✓
- [ ] Set slider to 0
- [ ] **Expected**: Message shows "Few-shot learning: Slider set to 0 examples"
- [ ] Set slider to 5 (if 5+ examples saved)
- [ ] **Expected**: Uses 5 examples
- [ ] **Status**: ___________

### Test 4.5: Few-Shot Disabled by User
- [ ] Uncheck few-shot checkbox
- [ ] Grade submission
- [ ] **Expected**: Message shows "Few-shot learning: Disabled by user"
- [ ] Check prompt - should NOT contain examples
- [ ] **Status**: ___________

---

## ✅ **Test 5: AI Detection**

### Test 5.1: No AI Keywords Detected
- [ ] Grade submission without AI keywords
- [ ] Check "AI Detection Result" field
- [ ] **Expected**: Shows "✅ NO AI KEYWORDS DETECTED\n\nNo suspicious AI-related phrases found in submission."
- [ ] **Status**: ___________

### Test 5.2: AI Keywords Detected
- [ ] Add AI keywords to detection field: "ChatGPT, as an AI language model"
- [ ] Grade submission containing one of these keywords
- [ ] **Expected**: Shows "🚨 AI KEYWORDS DETECTED\n\nFound: [keywords]\n\nThis submission may be AI-generated."
- [ ] **Expected**: Grade field also shows warning
- [ ] **Status**: ___________

---

## ✅ **Test 6: Feedback Library**

### Test 6.1: Save Good Example
- [ ] Grade a submission
- [ ] Enter corrected grade (if needed)
- [ ] Enter comments in "Comments/Suggestions" field
- [ ] Click "✅ Good Example" button
- [ ] **Expected**: Success message appears
- [ ] Navigate to "Feedback Library" tab
- [ ] **Expected**: Example appears in table
- [ ] **Status**: ___________

### Test 6.2: Save Needs Improvement Example
- [ ] Grade a submission
- [ ] Enter corrections
- [ ] Click "❌ Needs Improvement" button
- [ ] Check Feedback Library
- [ ] **Expected**: Appears with "needs_improvement" category
- [ ] **Status**: ___________

### Test 6.3: View Feedback Details
- [ ] Navigate to Feedback Library tab
- [ ] Click on a row in the table
- [ ] **Expected**: Details populate below (category, original grade, reasoning, corrected grade, comments)
- [ ] **Status**: ___________

### Test 6.4: Delete Feedback Example
- [ ] Select an example in table
- [ ] Click "Delete Selected Example"
- [ ] Click "Refresh Table"
- [ ] **Expected**: Only the selected example is deleted (not all)
- [ ] **Status**: ___________

### Test 6.5: Table Readability
- [ ] Open Feedback Library tab
- [ ] **Expected**: Table has white background, dark text, blue headers
- [ ] **Expected**: Rows alternate colors
- [ ] **Expected**: Hover shows highlight
- [ ] **Status**: ___________

---

## ✅ **Test 7: Context Length Display**

### Test 7.1: Small Submission
- [ ] Grade short text (< 500 words)
- [ ] Check context length bar and details
- [ ] **Expected**: Shows low percentage (< 25%), green status
- [ ] **Status**: ___________

### Test 7.2: Large Submission
- [ ] Grade long text (> 2000 words) or large PDF
- [ ] Check context length bar
- [ ] **Expected**: Shows higher percentage, may show warnings
- [ ] **Status**: ___________

### Test 7.3: Context Overflow
- [ ] Grade extremely large submission (if possible)
- [ ] **Expected**: Error message about context overflow with recommendations
- [ ] **Status**: ___________

---

## ✅ **Test 8: Debug Features**

### Test 8.1: View Raw LLM Output
- [ ] Grade submission
- [ ] Expand "🔍 Debug: Raw LLM Output" section
- [ ] **Expected**: Shows full JSON response from LLM
- [ ] **Status**: ___________

### Test 8.2: View Prompt Sent to LLM
- [ ] Grade submission
- [ ] Expand "🔍 Debug: Prompt Sent to LLM" section
- [ ] **Expected**: Shows system prompt and user prompt
- [ ] With few-shot enabled, should show examples section
- [ ] **Status**: ___________

---

## ✅ **Test 9: Batch Grading**

### Test 9.1: Batch Upload
- [ ] Navigate to "Batch" tab
- [ ] Upload multiple files (2-5 files)
- [ ] Fill in instructions and criteria
- [ ] Click "Grade Batch"
- [ ] **Expected**: Progress shown, results appear in table
- [ ] **Status**: ___________

### Test 9.2: Batch with Plagiarism Check
- [ ] Enable "Check Plagiarism" checkbox
- [ ] Upload batch files
- [ ] Grade batch
- [ ] **Expected**: Results include similarity scores
- [ ] **Status**: ___________

### Test 9.3: Export Batch Results
- [ ] After grading batch
- [ ] Click "Export to CSV"
- [ ] **Expected**: CSV file downloaded with all results
- [ ] **Status**: ___________

---

## ✅ **Test 10: System Info**

### Test 10.1: Model List
- [ ] Navigate to "System Info" tab
- [ ] Check installed models list
- [ ] **Expected**: Shows all Ollama models
- [ ] **Status**: ___________

### Test 10.2: Database Stats
- [ ] Check database statistics
- [ ] **Expected**: Shows course count, profile count, grading history count
- [ ] **Status**: ___________

---

## 🎯 **Integration Tests**

### Integration 1: Complete Workflow
- [ ] Create course
- [ ] Create profile for course
- [ ] Load profile
- [ ] Grade submission
- [ ] Mark as good example
- [ ] Grade another submission with few-shot enabled
- [ ] **Expected**: Second grading uses first as example
- [ ] **Status**: ___________

### Integration 2: Profile-Course Linking
- [ ] Create 2 courses (Course A, Course B)
- [ ] Create profile for Course A
- [ ] Switch to Course B
- [ ] **Expected**: Profile from Course A should NOT appear
- [ ] **Status**: ___________

### Integration 3: Few-Shot Evolution
- [ ] Start with 0 examples - verify disabled message
- [ ] Save 1 example - verify "need at least 2" message
- [ ] Save 2nd example - verify "using 2 examples" message
- [ ] Save 3rd, 4th, 5th examples
- [ ] Set slider to 5
- [ ] **Expected**: Uses all 5 examples
- [ ] **Status**: ___________

---

## 🐛 **Bug Regression Tests** (Previously Fixed Issues)

### Regression 1: Numeric Format
- [ ] Create profile with numeric format
- [ ] Grade submission
- [ ] **Expected**: Returns number (0-100), NOT letter grade
- [ ] **Status**: ___________

### Regression 2: Delete Profile
- [ ] Create 3 profiles
- [ ] Delete middle profile
- [ ] **Expected**: Only that profile deleted, others remain
- [ ] **Status**: ___________

### Regression 3: Feedback Table Selection
- [ ] Click on feedback table row
- [ ] **Expected**: No errors, details populate
- [ ] **Status**: ___________

### Regression 4: Dropdown Contrast
- [ ] Check all dropdowns (course, profile, model)
- [ ] **Expected**: Text clearly visible on background
- [ ] **Status**: ___________

### Regression 5: Radio/Checkbox Visibility
- [ ] Check all radio buttons and checkboxes
- [ ] **Expected**: Clear when selected vs unselected
- [ ] **Status**: ___________

---

## 📊 **Test Summary**

**Total Tests**: 50+  
**Passed**: _____  
**Failed**: _____  
**Skipped**: _____  

**Critical Issues Found**: _____________________

**Notes**:
_____________________________________________
_____________________________________________
_____________________________________________

---

## 🎯 **Priority Tests** (Must Pass)

1. ✅ Test 4.1-4.5: Few-Shot Learning Logic
2. ✅ Test 6.3: Feedback Table Selection (regression)
3. ✅ Test 6.5: Table Readability (regression)
4. ✅ Test 5.1-5.2: AI Detection Display
5. ✅ Test 2.4: Delete Profile (regression)
6. ✅ Regression 1: Numeric Format
7. ✅ Integration 3: Few-Shot Evolution

---

**Tester**: _______________  
**Test Completion Date**: _______________  
**App Version**: 1.0.1 (Few-Shot Update)

