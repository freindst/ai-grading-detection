"""
Main Gradio Application for Grading Assistant System
"""

import gradio as gr
import os
import time
from pathlib import Path
from src.llm_client import OllamaClient
from src.grading_engine import GradingEngine
from src.document_parser import DocumentParser
from src.batch_processor import BatchProcessor
from src.plagiarism_checker import PlagiarismChecker


# Initialize components
llm_client = OllamaClient()
grading_engine = GradingEngine(llm_client)
document_parser = DocumentParser()
batch_processor = BatchProcessor(grading_engine, max_workers=3)
plagiarism_checker = PlagiarismChecker()

# Global state
current_context_mode = "new"


def check_ollama_connection():
    """Check if Ollama is running"""
    if llm_client.test_connection():
        models = llm_client.get_available_models()
        return f"✅ Connected to Ollama\n\nAvailable models:\n" + "\n".join(f"  • {m}" for m in models)
    else:
        return "❌ Cannot connect to Ollama. Please ensure Ollama is running on http://localhost:11434"


def grade_single_submission(
    submission_text,
    assignment_instruction,
    grading_criteria,
    output_format,
    max_score,
    ai_keywords,
    additional_requirements,
    temperature,
    model_name,
    context_mode,
    use_llm_parse
):
    """Grade a single text submission"""
    global current_context_mode
    
    # Validation
    if not submission_text.strip():
        return "❌ Error: Submission text is required", "", "", "", ""
    if not assignment_instruction.strip():
        return "❌ Error: Assignment instruction is required", "", "", "", ""
    if not grading_criteria.strip():
        return "❌ Error: Grading criteria is required", "", "", "", ""
    
    # Set model
    llm_client.set_model(model_name)
    
    # Handle context management
    keep_context = False
    if context_mode == "clear":
        llm_client.clear_context()
        current_context_mode = "new"
    elif context_mode == "continue":
        keep_context = True
        current_context_mode = "continue"
    
    # Grade the submission
    result = grading_engine.grade_submission(
        submission_text=submission_text,
        assignment_instruction=assignment_instruction,
        grading_criteria=grading_criteria,
        output_format=output_format,
        max_score=int(max_score) if max_score else 100,
        ai_keywords=ai_keywords,
        additional_requirements=additional_requirements,
        temperature=temperature,
        keep_context=keep_context
    )
    
    if not result.get('success'):
        error_msg = f"❌ Error: {result.get('error', 'Unknown error')}"
        return error_msg, result.get('raw_output', ''), "", "", ""
    
    # If LLM-based parsing is requested and standard parsing had low confidence
    parsed = result['parsed_result']
    if use_llm_parse and parsed.get('parse_method') != 'json':
        parsed = grading_engine.llm_based_parse(result['raw_llm_output'])
        result['parsed_result'] = parsed
        result['formatted_output'] = grading_engine.format_grading_result(parsed)
    
    # Prepare outputs
    formatted_output = result['formatted_output']
    raw_llm_output = result['raw_llm_output']
    
    # Show input prompts
    input_display = f"""=== SYSTEM PROMPT ===
{result['system_prompt']}

=== USER PROMPT ===
{result['user_prompt']}

=== MODEL ===
{result['model']}

=== TOKENS ===
Prompt: {result['tokens']['prompt']} | Completion: {result['tokens']['completion']}
"""
    
    # Detailed feedback for instructor
    detailed_feedback = parsed.get('detailed_feedback', 'N/A')
    
    # Student feedback for posting
    student_feedback = parsed.get('student_feedback', 'N/A')
    
    return formatted_output, raw_llm_output, input_display, detailed_feedback, student_feedback


def clear_context_action():
    """Clear the conversation context"""
    llm_client.clear_context()
    return "✅ Context cleared. Next grading will start fresh."


def grade_file_submission(
    file_obj,
    assignment,
    criteria,
    output_format,
    max_score,
    ai_keywords,
    additional,
    temperature,
    model_name
):
    """Grade a single uploaded file"""
    if file_obj is None:
        return "❌ Please upload a file", "", "", ""
    
    if not assignment.strip() or not criteria.strip():
        return "❌ Assignment and criteria are required", "", "", ""
    
    # Parse the uploaded file
    file_path = file_obj.name if hasattr(file_obj, 'name') else file_obj
    parse_result = document_parser.parse_file(file_path)
    
    if not parse_result['success']:
        return f"❌ Failed to parse file: {parse_result['error']}", "", "", parse_result.get('text', '')
    
    extracted_text = parse_result['text']
    
    # Set model and grade
    llm_client.set_model(model_name)
    llm_client.clear_context()  # Always clear for file uploads
    
    grading_result = grading_engine.grade_submission(
        submission_text=extracted_text,
        assignment_instruction=assignment,
        grading_criteria=criteria,
        output_format=output_format,
        max_score=int(max_score) if max_score else 100,
        ai_keywords=ai_keywords,
        additional_requirements=additional,
        temperature=temperature,
        keep_context=False
    )
    
    if not grading_result['success']:
        return f"❌ Grading failed: {grading_result.get('error')}", "", "", extracted_text
    
    parsed = grading_result['parsed_result']
    formatted = grading_result['formatted_output']
    detailed = parsed.get('detailed_feedback', 'N/A')
    student = parsed.get('student_feedback', 'N/A')
    
    return formatted, detailed, student, extracted_text


def grade_batch_submissions(
    files,
    assignment,
    criteria,
    check_plag,
    output_format,
    max_score,
    ai_keywords,
    temperature,
    model_name
):
    """Grade multiple files in batch"""
    if not files or len(files) == 0:
        return (
            "❌ Please upload files",
            [],
            "No files uploaded",
            "No plagiarism check performed",
            "Ready to process..."
        )
    
    if not assignment.strip() or not criteria.strip():
        return (
            "❌ Assignment and criteria are required",
            [],
            "Missing configuration",
            "No plagiarism check performed",
            "Ready to process..."
        )
    
    # Set model
    llm_client.set_model(model_name)
    
    # Extract file paths
    file_paths = [f.name if hasattr(f, 'name') else f for f in files]
    
    # Progress callback
    progress_messages = []
    def update_progress(current, total, message):
        progress_messages.append(f"[{current}/{total}] {message}")
    
    # Process batch
    results = batch_processor.process_batch(
        file_paths=file_paths,
        assignment_instruction=assignment,
        grading_criteria=criteria,
        output_format=output_format,
        max_score=int(max_score) if max_score else 100,
        ai_keywords=ai_keywords,
        temperature=temperature,
        progress_callback=update_progress,
        check_plagiarism=check_plag
    )
    
    # Build results table
    table_data = []
    for result in results:
        # Determine plagiarism status
        plag_status = "None"
        if result.get('plagiarism_pairs'):
            max_similarity = max((p['similarity'] for p in result['plagiarism_pairs']), default=0)
            if max_similarity >= 80:
                plag_status = f"🔴 High ({max_similarity}%)"
            elif max_similarity >= 60:
                plag_status = f"🟡 Medium ({max_similarity}%)"
            else:
                plag_status = f"🟢 Low ({max_similarity}%)"
        
        table_data.append([
            result.get('filename', 'N/A'),
            result.get('grade', 'N/A'),
            result.get('confidence', 'N/A'),
            plag_status,
            'Success' if result.get('success') else f"Failed: {result.get('error', 'Unknown')}"
        ])
    
    # Summary stats
    stats = batch_processor.get_summary_stats()
    summary_text = f"""
=== Batch Processing Summary ===

Total Submissions: {stats['total']}
Successfully Graded: {stats['successful']}
Failed: {stats['failed']}
Success Rate: {stats['success_rate']}

=== Grade Distribution ===
"""
    for grade, count in stats['grade_distribution'].items():
        summary_text += f"{grade}: {count} student(s)\n"
    
    # Plagiarism report
    plag_report = "Plagiarism checking disabled"
    if check_plag:
        # Collect all plagiarism pairs
        all_plag_pairs = []
        for result in results:
            all_plag_pairs.extend(result.get('plagiarism_pairs', []))
        
        # Remove duplicates
        unique_pairs = []
        seen = set()
        for pair in all_plag_pairs:
            key = tuple(sorted([pair['file1'], pair['file2']]))
            if key not in seen:
                seen.add(key)
                unique_pairs.append(pair)
        
        plag_report = plagiarism_checker.generate_report(unique_pairs)
    
    progress_text = "\n".join(progress_messages[-5:])  # Show last 5 messages
    
    return (
        progress_text,
        table_data,
        summary_text,
        plag_report,
        f"✅ Processed {len(files)} file(s)"
    )


def export_batch_results(format_type):
    """Export batch results to file"""
    if not batch_processor.results:
        return "❌ No results to export. Please run batch grading first."
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"grading_results_{timestamp}.{format_type}"
    output_path = Path("exports") / filename
    
    # Ensure exports directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    success = batch_processor.export_results(str(output_path), format=format_type)
    
    if success:
        return f"✅ Results exported to: {output_path}"
    else:
        return "❌ Export failed"


# Build Gradio Interface
with gr.Blocks(title="Grading Assistant System", theme=gr.themes.Soft()) as app:
    gr.Markdown("""
    # 📚 Grading Assistant System
    ### AI-Powered College Homework Grading with Local LLM
    """)
    
    # Connection Status
    with gr.Row():
        with gr.Column(scale=3):
            connection_status = gr.Textbox(
                label="Ollama Connection Status",
                value=check_ollama_connection(),
                lines=4,
                interactive=False
            )
        with gr.Column(scale=1):
            refresh_btn = gr.Button("🔄 Refresh Status", size="sm")
            refresh_btn.click(check_ollama_connection, outputs=connection_status)
    
    gr.Markdown("---")
    
    # Main Grading Interface
    with gr.Tabs():
        # Tab 1: Single Text Grading
        with gr.Tab("📝 Text Input Grading"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Input Configuration")
                    
                    assignment_instruction = gr.Textbox(
                        label="Assignment Instructions",
                        placeholder="Enter the homework assignment description and requirements...",
                        lines=5
                    )
                    
                    grading_criteria = gr.Textbox(
                        label="Grading Criteria",
                        placeholder="Enter grading rubric and criteria...\nExample:\n- Correctness (40 pts)\n- Code quality (30 pts)\n- Documentation (20 pts)\n- Creativity (10 pts)",
                        lines=6
                    )
                    
                    with gr.Accordion("Advanced Settings", open=False):
                        output_format = gr.Radio(
                            choices=["letter", "numeric"],
                            value="letter",
                            label="Output Format"
                        )
                        max_score = gr.Number(
                            label="Maximum Score (for numeric grading)",
                            value=100
                        )
                        ai_keywords = gr.Textbox(
                            label="AI Detection Keywords (comma-separated)",
                            placeholder="keyword1, keyword2, keyword3"
                        )
                        additional_requirements = gr.Textbox(
                            label="Additional Requirements",
                            placeholder="Any extra grading considerations...",
                            lines=2
                        )
                        temperature = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.3,
                            step=0.1,
                            label="Temperature (lower = more consistent)"
                        )
                        model_selector = gr.Dropdown(
                            choices=llm_client.available_models,
                            value=llm_client.current_model,
                            label="Select Model"
                        )
                        use_llm_parse = gr.Checkbox(
                            label="Use LLM-based parsing (if standard parsing fails)",
                            value=False
                        )
                
                with gr.Column(scale=1):
                    gr.Markdown("### Student Submission")
                    
                    submission_text = gr.Textbox(
                        label="Submission Text",
                        placeholder="Paste the student's submission here...",
                        lines=20
                    )
                    
                    with gr.Row():
                        context_mode = gr.Radio(
                            choices=[("Clear Context (New)", "clear"), ("Continue Context", "continue")],
                            value="clear",
                            label="Context Mode"
                        )
                    
                    grade_btn = gr.Button("🎓 Grade Submission", variant="primary", size="lg")
            
            gr.Markdown("---")
            
            # Output Section
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Grading Results")
                    
                    with gr.Tabs():
                        with gr.Tab("📊 Formatted Output"):
                            formatted_output = gr.Textbox(
                                label="Formatted Grading Result",
                                lines=15,
                                interactive=False
                            )
                        
                        with gr.Tab("👨‍🏫 Detailed Feedback (Instructor)"):
                            detailed_feedback_output = gr.Textbox(
                                label="Detailed feedback with comprehensive analysis for instructor review",
                                lines=15,
                                interactive=False
                            )
                        
                        with gr.Tab("👨‍🎓 Student Feedback (Post as Comment)"):
                            student_feedback_output = gr.Textbox(
                                label="Concise, constructive feedback suitable for posting to student",
                                lines=15,
                                interactive=False
                            )
                        
                        with gr.Tab("🔍 Raw LLM Output"):
                            raw_output = gr.Textbox(
                                label="Raw Output from LLM",
                                lines=15,
                                interactive=False
                            )
                        
                        with gr.Tab("📥 Input Sent to LLM"):
                            input_display = gr.Textbox(
                                label="System Prompt + User Prompt",
                                lines=15,
                                interactive=False
                            )
            
            # Wire up the grading action
            grade_btn.click(
                fn=grade_single_submission,
                inputs=[
                    submission_text,
                    assignment_instruction,
                    grading_criteria,
                    output_format,
                    max_score,
                    ai_keywords,
                    additional_requirements,
                    temperature,
                    model_selector,
                    context_mode,
                    use_llm_parse
                ],
                outputs=[
                    formatted_output,
                    raw_output,
                    input_display,
                    detailed_feedback_output,
                    student_feedback_output
                ]
            )
        
        # Tab 2: File Upload Grading
        with gr.Tab("📁 File Upload Grading"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Assignment Configuration")
                    
                    file_assignment = gr.Textbox(
                        label="Assignment Instructions",
                        placeholder="Enter assignment description...",
                        lines=4
                    )
                    file_criteria = gr.Textbox(
                        label="Grading Criteria",
                        placeholder="Enter grading rubric...",
                        lines=5
                    )
                    
                    with gr.Accordion("Advanced Settings", open=False):
                        file_output_format = gr.Radio(
                            choices=["letter", "numeric"],
                            value="letter",
                            label="Output Format"
                        )
                        file_max_score = gr.Number(label="Max Score", value=100)
                        file_ai_keywords = gr.Textbox(label="AI Keywords", placeholder="keyword1, keyword2")
                        file_additional = gr.Textbox(label="Additional Requirements", lines=2)
                        file_temperature = gr.Slider(0.0, 1.0, 0.3, step=0.1, label="Temperature")
                        file_model = gr.Dropdown(
                            choices=llm_client.available_models,
                            value=llm_client.current_model,
                            label="Model"
                        )
                
                with gr.Column(scale=1):
                    gr.Markdown("### Upload File")
                    
                    file_upload = gr.File(
                        label="Upload Student Submission",
                        file_types=[".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"]
                    )
                    
                    gr.Markdown("**Supported formats**: PDF, DOCX, TXT, Images (PNG, JPG)")
                    
                    file_grade_btn = gr.Button("🎓 Grade File", variant="primary", size="lg")
            
            with gr.Row():
                with gr.Column():
                    with gr.Tabs():
                        with gr.Tab("📊 Results"):
                            file_results = gr.Textbox(label="Grading Results", lines=15, interactive=False)
                        with gr.Tab("👨‍🏫 Detailed"):
                            file_detailed = gr.Textbox(label="Detailed Feedback", lines=15, interactive=False)
                        with gr.Tab("👨‍🎓 Student"):
                            file_student = gr.Textbox(label="Student Feedback", lines=15, interactive=False)
                        with gr.Tab("📄 Extracted Text"):
                            file_extracted = gr.Textbox(label="Extracted Text", lines=15, interactive=False)
            
            # Wire up file grading
            file_grade_btn.click(
                fn=grade_file_submission,
                inputs=[
                    file_upload, file_assignment, file_criteria,
                    file_output_format, file_max_score, file_ai_keywords,
                    file_additional, file_temperature, file_model
                ],
                outputs=[file_results, file_detailed, file_student, file_extracted]
            )
        
        # Tab 3: Batch Processing
        with gr.Tab("📦 Batch Grading"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Batch Configuration")
                    
                    batch_assignment = gr.Textbox(
                        label="Assignment Instructions",
                        lines=4
                    )
                    batch_criteria = gr.Textbox(
                        label="Grading Criteria",
                        lines=5
                    )
                    
                    batch_check_plagiarism = gr.Checkbox(
                        label="Check for Plagiarism",
                        value=True
                    )
                    
                    with gr.Accordion("Advanced Settings", open=False):
                        batch_output_format = gr.Radio(
                            choices=["letter", "numeric"],
                            value="letter",
                            label="Output Format"
                        )
                        batch_max_score = gr.Number(label="Max Score", value=100)
                        batch_ai_keywords = gr.Textbox(label="AI Keywords")
                        batch_temperature = gr.Slider(0.0, 1.0, 0.3, step=0.1, label="Temperature")
                        batch_model = gr.Dropdown(
                            choices=llm_client.available_models,
                            value=llm_client.current_model,
                            label="Model"
                        )
                
                with gr.Column(scale=1):
                    gr.Markdown("### Upload Files")
                    
                    batch_upload = gr.File(
                        label="Upload Multiple Submissions",
                        file_count="multiple",
                        file_types=[".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"]
                    )
                    
                    batch_progress = gr.Textbox(
                        label="Progress",
                        value="Ready to process...",
                        lines=2,
                        interactive=False
                    )
                    
                    batch_grade_btn = gr.Button("🎓 Grade Batch", variant="primary", size="lg")
            
            gr.Markdown("---")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Batch Results")
                    
                    with gr.Tabs():
                        with gr.Tab("📊 Results Table"):
                            batch_results_table = gr.Dataframe(
                                headers=["Filename", "Grade", "Confidence", "Suspicion", "Status"],
                                label="Grading Results",
                                interactive=False
                            )
                        
                        with gr.Tab("📈 Summary Statistics"):
                            batch_summary = gr.Textbox(
                                label="Summary Stats",
                                lines=10,
                                interactive=False
                            )
                        
                        with gr.Tab("⚠️ Plagiarism Report"):
                            plagiarism_report = gr.Textbox(
                                label="Plagiarism Detection Results",
                                lines=15,
                                interactive=False
                            )
                        
                        with gr.Tab("📥 Export"):
                            with gr.Row():
                                export_format = gr.Radio(
                                    choices=["csv", "json"],
                                    value="csv",
                                    label="Export Format"
                                )
                                export_btn = gr.Button("💾 Export Results")
                            export_status = gr.Textbox(label="Export Status", lines=2)
            
            # Wire up batch grading
            batch_grade_btn.click(
                fn=grade_batch_submissions,
                inputs=[
                    batch_upload, batch_assignment, batch_criteria,
                    batch_check_plagiarism, batch_output_format,
                    batch_max_score, batch_ai_keywords,
                    batch_temperature, batch_model
                ],
                outputs=[
                    batch_progress, batch_results_table,
                    batch_summary, plagiarism_report, batch_progress
                ]
            )
            
            # Wire up export
            export_btn.click(
                fn=export_batch_results,
                inputs=[export_format],
                outputs=[export_status]
            )
    
    gr.Markdown("""
    ---
    ### 📖 How to Use
    1. **Check Connection**: Ensure Ollama is running and connected
    2. **Configure**: Enter assignment instructions and grading criteria
    3. **Submit**: Paste student submission and click "Grade Submission"
    4. **Review**: Check formatted output, detailed feedback, and student feedback
    5. **Context**: Use "Clear Context" for new submissions, "Continue Context" for follow-up questions
    
    ### 🎯 Features in This Version (Phases 1-3)
    ✅ Text-based grading with local LLM  
    ✅ Multiple model support  
    ✅ Context management (clear/continue)  
    ✅ Dual feedback (detailed for instructor, concise for students)  
    ✅ Raw input/output inspection  
    ✅ LLM-based parsing fallback  
    ✅ File upload (PDF, DOCX, TXT, Images with OCR)  
    ✅ Batch processing with concurrent grading  
    ✅ Plagiarism detection with suspicion levels  
    ✅ Export results (CSV/JSON)  
    """)


def launch_app():
    """Launch the Gradio application"""
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    launch_app()

