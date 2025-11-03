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

