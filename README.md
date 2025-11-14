# Grading Assistant System

**GitHub Repository**: [https://github.com/freindst/ai-grading-detection](https://github.com/freindst/ai-grading-detection)

An AI-powered college homework grading assistant using local LLM models via Ollama.

## Features (All 8 Phases Implemented!)

### Phase 1-3: Core Grading & Batch Processing
✅ **Text-based Grading**: Grade student submissions with AI assistance  
✅ **Multiple LLM Models**: Switch between qwen2.5-coder, llama3.1, mistral, and more  
✅ **Context Management**: Clear context for new submissions or continue conversation  
✅ **Dual Feedback System**: Detailed for instructors, concise for students  
✅ **File Upload Support**: PDF, DOCX, TXT, and images (with OCR)  
✅ **Batch Processing**: Grade multiple submissions concurrently  
✅ **Plagiarism Detection**: Simple similarity checking with suspicion levels  
✅ **Transparency**: View raw LLM output and input prompts  
✅ **Flexible Parsing**: JSON, regex, and LLM-based fallbacks  

### Phase 4-5: Profile Management & Advanced Parsing
✅ **Course & Assignment Profiles**: Organize grading by courses and assignments  
✅ **Database Management**: SQLite database for storing profiles and history  
✅ **Prompt Templates**: Reusable prompt templates with variable substitution  
✅ **Criteria Parser**: Convert JSON/YAML/bullet points to natural language  
✅ **Enhanced Output Parsing**: Multiple parsing strategies with high accuracy  
✅ **Feedback Collection**: Collect human feedback for model alignment  

### Phase 6-7: Advanced Features
✅ **In-Context Learning**: Few-shot learning with good examples  
✅ **Internet Search**: Verify references and citations  
✅ **Reference Verification**: Extract and verify URLs and citations  
✅ **AI Keyword Detection**: Embed keywords to detect AI-generated content  

### Phase 8: Export & Reporting
✅ **Multiple Export Formats**: CSV, JSON, Excel, PDF, HTML  
✅ **Comprehensive Reports**: Text, PDF, and HTML reports with statistics  
✅ **Summary Statistics**: Grade distribution, success rates, plagiarism summary  
✅ **Customizable Exports**: Full feedback or summary versions  

### Canvas LMS Integration (New!)
✅ **Canvas Authentication**: Secure token-based authentication with encryption  
✅ **Course & Assignment Management**: Browse courses and assignments from Canvas  
✅ **Auto-Download Submissions**: Download all student submissions automatically  
✅ **AI-Powered Grading**: Grade all submissions using LLM with custom rubrics  
✅ **Manual Review Interface**: Review, edit, and correct AI-generated grades  
✅ **Raw JSON Viewing**: Debug parser errors by viewing complete LLM output  
✅ **Session Management**: Track multiple grading sessions with full history  
✅ **Batch Upload**: Upload all reviewed grades to Canvas in one click  

## Prerequisites

1. **Python 3.10+**
2. **Ollama** - Install from [ollama.ai](https://ollama.ai)
3. **Virtual Environment** (recommended)

## Installation

### 1. Set up virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install and start Ollama

Download and install Ollama from [ollama.ai](https://ollama.ai)

Pull recommended models:

```bash
ollama pull qwen2.5-coder
ollama pull llama3.1
ollama pull mistral
```

Start Ollama (it usually starts automatically):

```bash
ollama serve
```

### 4. Run the application

```bash
python -m src.app
```

The application will be available at `http://localhost:7860`

### Podman Deployment (Optional)

You can run the grading assistant inside a Podman container while keeping Ollama on the host machine.

1. Ensure Podman is installed and, on macOS/Windows, start the Podman machine (`podman machine init && podman machine start`).
2. Make sure Ollama is running on the host (`ollama serve`) and accessible (typically `http://localhost:11434`).
3. Build and launch the container:

   ```bash
   chmod +x podman-run.sh
   ./podman-run.sh
   ```

   - The script builds the image from `Containerfile`, mounts the host `data/` directory into the container, and re-uses `.env` if present.
   - It automatically sets `OLLAMA_HOST` based on your environment: defaults to `http://host.containers.internal:11434` for native Podman on Windows/macOS and falls back to your Windows host IP when run from WSL.
   - Override any value by exporting an environment variable before running the script (e.g., `export OLLAMA_HOST=http://localhost:11434` on Linux).

4. Access the UI at `http://localhost:7860`.

**Platform notes**

- **WSL / Windows host Ollama**: Keep Ollama running on Windows and run Podman inside WSL. The default `host.containers.internal` address resolves to the Windows host. If you use a different address, set `OLLAMA_HOST` accordingly in `.env` or the environment.
- **macOS**: Start `ollama serve` on macOS and run Podman via `podman machine`. The default host address works out of the box.
- **Linux**: When Podman runs on the same Linux host as Ollama, override `OLLAMA_HOST` to `http://localhost:11434` or use `--network host` if you prefer host networking.

The application will still be available at `http://localhost:7860` while the container is running.

## Usage Guide

### 1. Text Input Grading (Tab 1)
- Enter assignment instructions and grading criteria
- Paste student submission text
- Choose output format (letter/numeric)
- Select context mode (clear/continue)
- View results in multiple formats:
  - **Formatted Output**: Structured grading
  - **Detailed Feedback**: For instructor review
  - **Student Feedback**: To post to students
  - **Raw LLM Output**: Unprocessed response
  - **Input Sent**: View prompts sent to LLM

### 2. File Upload Grading (Tab 2)
- Upload PDF, DOCX, TXT, or image files
- System extracts text automatically (OCR for images)
- Configure grading parameters
- View extracted text and grading results

### 3. Batch Grading (Tab 3)
- Upload multiple files at once
- Enable plagiarism checking (optional)
- View results in table format
- See summary statistics and grade distribution
- Check plagiarism report for suspicious pairs
- Export results in CSV, JSON, Excel, or HTML

### 4. Profile Management (Advanced)
- Create courses and assignments in the database
- Save grading criteria as reusable templates
- Store grading history for reference
- Mark good examples for in-context learning
- Export/import assignment profiles

### 5. Advanced Features
- **Few-Shot Learning**: System learns from marked good examples
- **Reference Verification**: Automatically check citations
- **Flexible Parsing**: Multiple strategies for extracting grades
- **Feedback Collection**: Improve grading over time

### 6. Canvas LMS Integration (Tab 5)

#### Step 1: Authentication
1. Navigate to the **Canvas LMS** tab
2. Enter your Canvas instance URL (e.g., `https://cuwaa.instructure.com/`)
3. Generate an access token from Canvas:
   - Log in to Canvas → Account → Settings → "+ New Access Token"
   - Copy the generated token
4. Paste the token in the application and click **Connect & Verify**
5. System will verify connection and load your courses

#### Step 2: Select Course & Assignment
1. Choose a course from the dropdown (populated after authentication)
2. Select an assignment to grade
3. View assignment details (due date, points possible, submission count)

#### Step 3: Configure Grading
1. Enter assignment instructions
2. Enter grading criteria/rubric
3. Set output format (numeric recommended for Canvas)
4. Set maximum score
5. Add AI keywords (optional)
6. Select LLM model and temperature

#### Step 4: Download & Grade
1. Click **Download & Grade All Submissions**
2. System will:
   - Download all student submissions from Canvas
   - Extract text from each submission
   - Grade with LLM using your criteria
   - Store BOTH raw JSON output AND parsed results
   - Create a grading session in the database
3. Progress bar shows grading status

#### Step 5: Review Grades
1. Note the Session ID from the result message
2. Enter Session ID and click **Load Session**
3. Review the grades table:
   - **Parsed Grade**: AI-extracted grade
   - **Final Grade**: Editable grade (defaults to parsed)
   - **Status**: Needs Review / Reviewed
   - **Upload Status**: Pending / Uploaded / Failed

#### Step 6: Edit Individual Grades
1. Enter a Grade ID from the table
2. Click **Load Grade** to see details
3. Review:
   - Student name
   - Parsed grade (what AI extracted)
   - Manual grade (editable)
   - Comments (editable)
   - **Raw LLM JSON** (full output for debugging)
4. Edit grade/comments if needed
5. Check "Mark as Reviewed"
6. Click **Save Grade**

**Pro Tip**: Click "Accept All Parsed Grades" to quickly accept all AI grades at once

#### Step 7: Upload to Canvas
1. Once all grades are reviewed, click **Upload All Reviewed Grades**
2. System uploads grades and comments to Canvas in batch
3. View upload results (success/failure for each student)
4. Alternatively, upload individual grades using Grade ID

### Security Note
- Access tokens are encrypted using `cryptography.fernet`
- Encrypted tokens stored in database
- Encryption key stored in `data/.canvas_key`
- Never share your access token or `.canvas_key` file

## Project Structure

```
GradingSystem/
├── src/
│   ├── app.py              # Main Gradio application
│   ├── llm_client.py       # Ollama integration
│   └── grading_engine.py   # Core grading logic
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── plan.md                # Full implementation plan
```

## All Features Implemented!

All 8 phases of development are complete:
- ✅ Phase 1: Core infrastructure with Ollama integration
- ✅ Phase 2: File upload and batch processing
- ✅ Phase 3: Plagiarism detection
- ✅ Phase 4: Profile and prompt management
- ✅ Phase 5: Advanced parsing and feedback collection
- ✅ Phase 6: In-context learning
- ✅ Phase 7: Internet search for reference verification
- ✅ Phase 8: Export and reporting system

**Future Enhancements** (Optional):
- LoRA/QLoRA fine-tuning integration (Phase 6 extension)
- Advanced AI content detection
- Integration with LMS platforms
- Real-time grading dashboard

## Troubleshooting

### Cannot connect to Ollama

- Ensure Ollama is installed and running
- Check if service is accessible at `http://localhost:11434`
- Try: `ollama list` to verify installation

### Model not found

- Pull the model: `ollama pull <model-name>`
- Check available models: `ollama list`

### Out of memory

- Use smaller models (mistral instead of llama3.1)
- Reduce context window size
- Close other applications

## Configuration

### Changing Ollama Port

If Ollama runs on a different port, modify `src/llm_client.py`:

```python
llm_client = OllamaClient(base_url="http://localhost:YOUR_PORT")
```

### Adding More Models

Edit `src/llm_client.py` to add models to `available_models` list:

```python
self.available_models = [
    "qwen2.5-coder:latest",
    "llama3.1:latest",
    "your-model-name:latest"
]
```

## Contributing

This is an ongoing project with 8 planned phases. See `plan.md` for the full roadmap.

## License

MIT License

