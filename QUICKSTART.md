# Quick Start Guide - Grading Assistant System

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Prerequisites

1. **Install Python 3.10+**
   - Windows: Download from [python.org](https://python.org)
   - Mac: `brew install python`
   - Linux: `sudo apt install python3`

2. **Install Ollama**
   - Visit [ollama.ai](https://ollama.ai) and download for your OS
   - Start Ollama (usually auto-starts)

### Step 2: Set Up Project

```bash
# Navigate to project directory
cd GradingSystem

# Create virtual environment (RECOMMENDED)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Download LLM Models

```bash
# Download recommended models (choose at least one)
ollama pull qwen2.5-coder
ollama pull llama3.1
ollama pull mistral
```

### Step 4: Launch Application

```bash
python -m src.app
```

The app will open at: **http://localhost:7860**

---

## 📝 Your First Grading Session

### Example 1: Text Input Grading

1. **Open Tab 1: Text Input Grading**

2. **Enter Assignment Instructions:**
```
Write a Python function to calculate the factorial of a number using recursion.
The function should handle edge cases and include docstrings.
```

3. **Enter Grading Criteria:**
```
- Correct implementation (40 pts)
- Proper recursion (20 pts)
- Edge case handling (20 pts)
- Code documentation (10 pts)
- Code style (10 pts)
```

4. **Paste Student Submission:**
```python
def factorial(n):
    """Calculate factorial of n using recursion"""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)
```

5. **Click "Grade Submission"**

6. **Review Results** in multiple tabs:
   - Formatted Output
   - Detailed Feedback (for you)
   - Student Feedback (to post)
   - Raw LLM Output
   - Input Sent to LLM

---

### Example 2: Batch Grading with Plagiarism Detection

1. **Open Tab 3: Batch Grading**

2. **Configure Assignment:**
   - Enter instructions and criteria (same as above)
   - **Enable "Check for Plagiarism"** ✓

3. **Upload Files:**
   - Click "Upload Multiple Submissions"
   - Select 3-5 student submission files (PDF, DOCX, TXT)

4. **Click "Grade Batch"**

5. **Wait for Processing:**
   - Watch progress indicator
   - System grades all submissions concurrently
   - Plagiarism check runs automatically

6. **Review Results:**
   - **Results Table**: See all grades at a glance
   - **Summary Statistics**: Grade distribution
   - **Plagiarism Report**: Check suspicious pairs
   - **Export**: Download as CSV, JSON, or HTML

---

## 🎓 Best Practices

### For Accurate Grading

1. **Be Specific in Criteria**
   - ✅ "Correct implementation with proper error handling (30 pts)"
   - ❌ "Good code"

2. **Use Structured Rubrics**
   ```json
   {
     "Correctness": 40,
     "Style": 20,
     "Documentation": 20,
     "Efficiency": 20
   }
   ```

3. **Set Appropriate Temperature**
   - **0.1-0.3**: Consistent, conservative grading
   - **0.4-0.6**: Balanced
   - **0.7-1.0**: More creative, less consistent

4. **Use Context Management**
   - **Clear Context**: For each new submission
   - **Continue Context**: For follow-up questions about same submission

### For Plagiarism Detection

1. **Upload Complete Batch**
   - Plagiarism detection works by comparing within batch
   - Upload all submissions from the same assignment

2. **Review Suspicion Levels**
   - 🔴 **High (80%+)**: Likely plagiarism
   - 🟡 **Medium (60-79%)**: Investigate further
   - 🟢 **Low (40-59%)**: Probably coincidental

3. **Manual Verification**
   - System provides suspicion level
   - You make the final judgment

### For Better Results Over Time

1. **Mark Good Examples**
   - When you see excellent grading, mark it as "good example"
   - System uses these for in-context learning

2. **Provide Feedback**
   - If grading is off, provide feedback
   - System stores this for future improvement

3. **Use Templates**
   - Save assignment profiles for reuse
   - Duplicate and modify for similar assignments

---

## 🔧 Common Use Cases

### Use Case 1: Programming Assignment

**Assignment Type:** Write a sorting algorithm  
**Best Settings:**
- Model: `qwen2.5-coder` (specializes in code)
- Temperature: `0.3` (consistent)
- Output Format: Numeric (0-100)

### Use Case 2: Essay/Written Assignment

**Assignment Type:** 500-word argumentative essay  
**Best Settings:**
- Model: `llama3.1` or `mistral` (better for text)
- Temperature: `0.4` (balanced)
- Output Format: Letter (A-E)
- Enable: Reference verification

### Use Case 3: Math/Problem Solving

**Assignment Type:** Calculus problem set  
**Best Settings:**
- Model: `qwen2.5-coder` (good with math)
- Temperature: `0.2` (precise)
- Output Format: Numeric
- Criteria: Step-by-step solution evaluation

---

## 🐛 Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve
```

### "Model not found"
```bash
# Pull the model
ollama pull qwen2.5-coder
```

### "Out of memory"
- Use smaller model: `ollama pull mistral`
- Reduce batch size
- Close other applications

### "Parsing failed / Grade N/A"
- Enable "Use LLM-based parsing"
- Lower temperature for more structured output
- Check criteria format (avoid complex formatting)

---

## 📊 Export & Reporting

### Quick Export
1. Grade batch → Click "Export" tab
2. Choose format (CSV, JSON)
3. Click "Export Results"
4. Files saved to `/exports` folder

### Generate Reports
- **Text Report**: Full details, all submissions
- **HTML Report**: Interactive, shareable
- **PDF Report**: Professional, printable
- **Excel Report**: Sortable, filterable

---

## 💡 Tips & Tricks

1. **Keyboard Shortcuts**
   - Tab through fields quickly
   - Use Ctrl+V to paste submissions

2. **Batch Optimization**
   - Process 10-15 files at a time for best speed
   - More concurrent workers = faster but more memory

3. **Model Selection**
   - **qwen2.5-coder**: Code, math, technical
   - **llama3.1**: Essays, analysis, general
   - **mistral**: Fast, balanced, efficient

4. **Criteria Formats**
   - Plain text: Most flexible
   - JSON: Best for weighted rubrics
   - YAML: Good for hierarchical criteria
   - Bullet points: Quick and readable

---

## 📚 Next Steps

1. **Explore Advanced Features**
   - Set up course profiles (Tab 4)
   - Create prompt templates
   - Use few-shot learning

2. **Optimize Your Workflow**
   - Save common criteria as templates
   - Create course-specific prompts
   - Build library of good examples

3. **Customize**
   - Adjust plagiarism thresholds
   - Create custom export templates
   - Fine-tune prompts for your needs

---

## 🆘 Need Help?

- Check `README.md` for detailed documentation
- See `plan.md` for system architecture
- Review error messages in "Raw LLM Output" tab
- Adjust settings and retry

**Happy Grading! 🎉**

