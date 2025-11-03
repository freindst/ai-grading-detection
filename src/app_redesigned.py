"""
Main Gradio Application for Grading Assistant System (Redesigned)
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
from src.database import DatabaseManager
from src.profile_manager import ProfileManager


# Initialize components
llm_client = OllamaClient()
grading_engine = GradingEngine(llm_client)
document_parser = DocumentParser()
batch_processor = BatchProcessor(grading_engine, max_workers=3)
plagiarism_checker = PlagiarismChecker()
db_manager = DatabaseManager()
profile_manager = ProfileManager(db_manager)

# Global state
current_criteria_id = None


def get_installed_models():
    """Get list of installed Ollama models"""
    try:
        models = llm_client.get_available_models()
        return models if models else ["mistral:latest"]
    except:
        return ["mistral:latest"]


def check_ollama_connection():
    """Check if Ollama is running"""
    if llm_client.test_connection():
        models = get_installed_models()
        return f"✅ Connected to Ollama\n\nInstalled models:\n" + "\n".join(f"  • {m}" for m in models)
    else:
        return "❌ Cannot connect to Ollama. Please ensure Ollama is running."


# === CRITERIA PROFILE MANAGEMENT ===

def load_criteria_profiles():
    """Load all saved criteria profiles"""
    profiles = db_manager.get_all_criteria()
    if not profiles:
        return gr.Dropdown(choices=[], value=None)
    
    choices = [f"{p['id']}: {p['assignment_name']}" if p.get('assignment_name') else f"{p['id']}: Criteria #{p['id']}" 
               for p in profiles]
    return gr.Dropdown(choices=choices, value=None)


def save_criteria_profile(name, instructions, criteria, output_format, max_score, ai_keywords, requirements):
    """Save current criteria as a profile"""
    if not name.strip():
        return "❌ Profile name is required", load_criteria_profiles()
    
    if not instructions.strip() or not criteria.strip():
        return "❌ Instructions and criteria cannot be empty", load_criteria_profiles()
    
    # Create an assignment without a course
    assignment_id = db_manager.create_assignment(
        course_id=None,
        name=name,
        description="",
        instructions=instructions
    )
    
    if assignment_id == -1:
        return "❌ Failed to save profile", load_criteria_profiles()
    
    # Save criteria
    criteria_id = db_manager.create_grading_criteria(
        assignment_id=assignment_id,
        criteria_text=criteria,
        output_format=output_format,
        max_score=int(max_score) if max_score else 100,
        ai_keywords=ai_keywords,
        additional_requirements=requirements
    )
    
    if criteria_id == -1:
        return "❌ Failed to save criteria", load_criteria_profiles()
    
    return f"✅ Profile '{name}' saved successfully!", load_criteria_profiles()


def load_criteria_profile(selected_profile):
    """Load a saved criteria profile"""
    if not selected_profile:
        return "", "", "", "letter", 100, "", ""
    
    # Extract criteria ID from selection
    try:
        criteria_id = int(selected_profile.split(":")[0])
    except:
        return "", "", "", "letter", 100, "", ""
    
    criteria = db_manager.get_grading_criteria(criteria_id)
    if not criteria:
        return "", "", "", "letter", 100, "", ""
    
    # Get assignment info
    assignment = db_manager.get_assignment(criteria['assignment_id'])
    if not assignment:
        return "", "", "", "letter", 100, "", ""
    
    global current_criteria_id
    current_criteria_id = criteria_id
    
    return (
        assignment['instructions'],
        criteria['criteria_text'],
        f"Loaded: {assignment['name']}",
        criteria['output_format'],
        criteria['max_score'],
        criteria['ai_keywords'] or "",
        criteria['additional_requirements'] or ""
    )


def delete_criteria_profile(selected_profile):
    """Delete a saved criteria profile"""
    if not selected_profile:
        return "❌ No profile selected", load_criteria_profiles()
    
    try:
        criteria_id = int(selected_profile.split(":")[0])
    except:
        return "❌ Invalid selection", load_criteria_profiles()
    
    criteria = db_manager.get_grading_criteria(criteria_id)
    if criteria:
        db_manager.delete_assignment(criteria['assignment_id'])
        return "✅ Profile deleted successfully!", load_criteria_profiles()
    
    return "❌ Profile not found", load_criteria_profiles()


def copy_criteria_profile(selected_profile, new_name):
    """Copy an existing criteria profile"""
    if not selected_profile:
        return "❌ No profile selected", load_criteria_profiles()
    
    if not new_name.strip():
        return "❌ New profile name is required", load_criteria_profiles()
    
    try:
        criteria_id = int(selected_profile.split(":")[0])
    except:
        return "❌ Invalid selection", load_criteria_profiles()
    
    criteria = db_manager.get_grading_criteria(criteria_id)
    if not criteria:
        return "❌ Profile not found", load_criteria_profiles()
    
    assignment = db_manager.get_assignment(criteria['assignment_id'])
    if not assignment:
        return "❌ Assignment not found", load_criteria_profiles()
    
    # Create new assignment
    new_assignment_id = db_manager.create_assignment(
        course_id=None,
        name=new_name,
        description=assignment.get('description', ''),
        instructions=assignment['instructions']
    )
    
    if new_assignment_id == -1:
        return "❌ Failed to copy profile", load_criteria_profiles()
    
    # Create new criteria
    new_criteria_id = db_manager.create_grading_criteria(
        assignment_id=new_assignment_id,
        criteria_text=criteria['criteria_text'],
        output_format=criteria['output_format'],
        max_score=criteria['max_score'],
        ai_keywords=criteria.get('ai_keywords'),
        additional_requirements=criteria.get('additional_requirements')
    )
    
    if new_criteria_id == -1:
        return "❌ Failed to copy criteria", load_criteria_profiles()
    
    return f"✅ Profile copied as '{new_name}'!", load_criteria_profiles()


# === GRADING FUNCTIONS ===

def grade_submission(
    submission_text,
    file_obj,
    assignment_instruction,
    grading_criteria,
    output_format,
    max_score,
    ai_keywords,
    additional_requirements,
    temperature,
    model_name,
    use_llm_parse
):
    """Grade a submission (either text or file)"""
    
    # Determine input source
    if file_obj is not None:
        # File upload
        file_path = file_obj.name if hasattr(file_obj, 'name') else file_obj
        parse_result = document_parser.parse_file(file_path)
        
        if not parse_result['success']:
            return {
                formatted_output: f"❌ Failed to parse file: {parse_result['error']}",
                raw_output: "",
                detailed_fb: "",
                student_fb: "",
                extracted_text: parse_result.get('text', '')
            }
        
        text_to_grade = parse_result['text']
        extracted = parse_result['text']
    elif submission_text.strip():
        # Text input
        text_to_grade = submission_text
        extracted = ""
    else:
        return {
            formatted_output: "❌ Please provide either text or upload a file",
            raw_output: "",
            detailed_fb: "",
            student_fb: "",
            extracted_text: ""
        }
    
    # Validation
    if not assignment_instruction.strip():
        return {
            formatted_output: "❌ Assignment instruction is required",
            raw_output: "",
            detailed_fb: "",
            student_fb: "",
            extracted_text: extracted
        }
    
    if not grading_criteria.strip():
        return {
            formatted_output: "❌ Grading criteria is required",
            raw_output: "",
            detailed_fb: "",
            student_fb: "",
            extracted_text: extracted
        }
    
    # Set model
    llm_client.set_model(model_name)
    llm_client.clear_context()
    
    # Grade the submission
    result = grading_engine.grade_submission(
        submission_text=text_to_grade,
        assignment_instruction=assignment_instruction,
        grading_criteria=grading_criteria,
        output_format=output_format,
        max_score=int(max_score) if max_score else 100,
        ai_keywords=ai_keywords,
        additional_requirements=additional_requirements,
        temperature=temperature,
        keep_context=False
    )
    
    if not result.get('success'):
        error_msg = f"❌ Error: {result.get('error', 'Unknown error')}"
        return {
            formatted_output: error_msg,
            raw_output: result.get('raw_llm_output', ''),
            detailed_fb: "",
            student_fb: "",
            extracted_text: extracted
        }
    
    # If LLM-based parsing is requested
    parsed = result['parsed_result']
    if use_llm_parse and parsed.get('parse_method') != 'json':
        parsed = grading_engine.llm_based_parse(result['raw_llm_output'])
        result['parsed_result'] = parsed
        result['formatted_output'] = grading_engine.format_grading_result(parsed)
    
    return {
        formatted_output: result['formatted_output'],
        raw_output: result['raw_llm_output'],
        detailed_fb: parsed.get('detailed_feedback', 'N/A'),
        student_fb: parsed.get('student_feedback', 'N/A'),
        extracted_text: extracted
    }


def grade_batch(
    files,
    assignment_instruction,
    grading_criteria,
    check_plag,
    output_format,
    max_score,
    ai_keywords,
    additional_requirements,
    temperature,
    model_name
):
    """Grade multiple files in batch"""
    if not files or len(files) == 0:
        return "❌ Please upload files", [], "No files uploaded", "No plagiarism check"
    
    if not assignment_instruction.strip() or not grading_criteria.strip():
        return "❌ Assignment and criteria are required", [], "Missing configuration", "No plagiarism check"
    
    # Set model
    llm_client.set_model(model_name)
    
    # Extract file paths
    file_paths = [f.name if hasattr(f, 'name') else f for f in files]
    
    # Process batch
    results = batch_processor.process_batch(
        file_paths=file_paths,
        assignment_instruction=assignment_instruction,
        grading_criteria=grading_criteria,
        output_format=output_format,
        max_score=int(max_score) if max_score else 100,
        ai_keywords=ai_keywords,
        temperature=temperature,
        progress_callback=None,
        check_plagiarism=check_plag
    )
    
    # Build results table
    table_data = []
    for result in results:
        plag_status = "None"
        if result.get('plagiarism_pairs'):
            max_similarity = max((p['similarity'] for p in result['plagiarism_pairs']), default=0)
            if max_similarity >= 80:
                plag_status = f"🔴 {max_similarity}%"
            elif max_similarity >= 60:
                plag_status = f"🟡 {max_similarity}%"
            else:
                plag_status = f"🟢 {max_similarity}%"
        
        table_data.append([
            result['filename'],
            result['grade'] if result['success'] else "Error",
            plag_status,
            result['detailed_feedback'][:100] + "..." if len(result.get('detailed_feedback', '')) > 100 else result.get('detailed_feedback', '')
        ])
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    summary = f"Processed: {len(results)} files\nSuccessful: {successful}\nFailed: {len(results) - successful}"
    
    # Plagiarism report
    plag_report = "No plagiarism check performed"
    if check_plag and results:
        plag_pairs = []
        for result in results:
            if result.get('plagiarism_pairs'):
                for pair in result['plagiarism_pairs']:
                    plag_pairs.append(
                        f"⚠️ {result['filename']} ↔ {pair['other_file']}: {pair['similarity']}% similarity"
                    )
        
        if plag_pairs:
            plag_report = "\n".join(plag_pairs)
        else:
            plag_report = "✅ No significant plagiarism detected"
    
    return "✅ Batch processing complete!", table_data, summary, plag_report


# === UI CONSTRUCTION ===

def build_interface():
    """Build the Gradio interface"""
    
    with gr.Blocks(title="Grading Assistant System", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🎓 AI Grading Assistant System")
        gr.Markdown("*Powered by Ollama - Local LLM for homework grading*")
        
        # === GRADING CRITERIA PANEL (Shared across all tabs) ===
        with gr.Accordion("📋 Grading Criteria & Configuration", open=True):
            with gr.Row():
                with gr.Column(scale=3):
                    assignment_instruction = gr.Textbox(
                        label="Assignment Instructions",
                        placeholder="Describe the assignment task...",
                        lines=3
                    )
                    grading_criteria = gr.Textbox(
                        label="Grading Criteria",
                        placeholder="Enter grading rubric (JSON, YAML, bullets, or plain text)...",
                        lines=4
                    )
                
                with gr.Column(scale=1):
                    gr.Markdown("### Settings")
                    output_format = gr.Radio(
                        choices=["letter", "numeric", "pass/fail"],
                        value="letter",
                        label="Output Format"
                    )
                    max_score = gr.Number(value=100, label="Max Score")
                    model_dropdown = gr.Dropdown(
                        choices=get_installed_models(),
                        value=get_installed_models()[0] if get_installed_models() else None,
                        label="Model",
                        interactive=True
                    )
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.3,
                        step=0.1,
                        label="Temperature"
                    )
            
            with gr.Accordion("⚙️ Advanced Settings", open=False):
                with gr.Row():
                    ai_keywords = gr.Textbox(
                        label="AI Detection Keywords (comma-separated)",
                        placeholder="e.g., generic, boilerplate, template",
                        lines=1
                    )
                    additional_requirements = gr.Textbox(
                        label="Additional Requirements",
                        placeholder="Any specific grading requirements...",
                        lines=1
                    )
                    use_llm_parse = gr.Checkbox(label="Use LLM Parsing (if standard fails)", value=False)
        
        # === PROFILE MANAGEMENT ===
        with gr.Accordion("💾 Criteria Profiles (Save/Load/Edit)", open=False):
            with gr.Row():
                with gr.Column(scale=2):
                    profile_dropdown = gr.Dropdown(
                        label="Saved Profiles",
                        choices=[],
                        interactive=True
                    )
                    profile_status = gr.Textbox(label="Status", interactive=False, lines=1)
                
                with gr.Column(scale=1):
                    load_btn = gr.Button("📂 Load Profile", size="sm")
                    with gr.Row():
                        delete_btn = gr.Button("🗑️ Delete", size="sm", variant="stop")
                        refresh_btn = gr.Button("🔄 Refresh", size="sm")
            
            with gr.Row():
                profile_name = gr.Textbox(label="Profile Name", placeholder="Enter name to save current criteria...")
                save_btn = gr.Button("💾 Save Current as Profile", variant="primary")
            
            with gr.Row():
                copy_name = gr.Textbox(label="New Name", placeholder="Name for copied profile...")
                copy_btn = gr.Button("📋 Copy Selected Profile", size="sm")
        
        # === TABS ===
        with gr.Tabs():
            # TAB 1: INPUT
            with gr.Tab("📝 Input"):
                gr.Markdown("### Provide your submission")
                with gr.Row():
                    with gr.Column():
                        submission_text = gr.Textbox(
                            label="Text Submission (paste directly)",
                            placeholder="Paste student's text submission here...",
                            lines=10
                        )
                    with gr.Column():
                        file_upload = gr.File(
                            label="OR Upload File (PDF, DOCX, TXT, Images)",
                            file_types=[".pdf", ".docx", ".doc", ".txt", ".jpg", ".png"]
                        )
                        extracted_text_display = gr.Textbox(
                            label="Extracted Text (from file)",
                            interactive=False,
                            lines=10
                        )
                
                grade_btn = gr.Button("🎓 Grade Submission", variant="primary", size="lg")
            
            # TAB 2: OUTPUT
            with gr.Tab("📊 Output"):
                gr.Markdown("### Grading Results")
                with gr.Row():
                    with gr.Column():
                        formatted_output = gr.Textbox(label="Grade Summary", lines=8, interactive=False)
                        raw_output = gr.Textbox(label="Raw LLM Output", lines=8, interactive=False)
                    with gr.Column():
                        detailed_fb = gr.Textbox(label="Detailed Feedback (Instructor)", lines=8, interactive=False)
                        student_fb = gr.Textbox(label="Student Feedback (To Share)", lines=8, interactive=False)
            
            # TAB 3: BATCH PROCESSING
            with gr.Tab("📦 Batch Processing"):
                gr.Markdown("### Grade Multiple Files")
                batch_files = gr.File(
                    label="Upload Multiple Files",
                    file_count="multiple",
                    file_types=[".pdf", ".docx", ".doc", ".txt"]
                )
                check_plagiarism = gr.Checkbox(label="Check for Plagiarism", value=True)
                batch_grade_btn = gr.Button("🎓 Grade Batch", variant="primary", size="lg")
                
                batch_status = gr.Textbox(label="Status", interactive=False)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        batch_results = gr.Dataframe(
                            headers=["Filename", "Grade", "Plagiarism", "Feedback Preview"],
                            label="Results",
                            interactive=False
                        )
                    with gr.Column(scale=1):
                        batch_summary = gr.Textbox(label="Summary", lines=6, interactive=False)
                        plagiarism_report = gr.Textbox(label="Plagiarism Report", lines=6, interactive=False)
            
            # TAB 4: SYSTEM INFO
            with gr.Tab("ℹ️ System Info"):
                connection_info = gr.Textbox(label="Ollama Connection Status", lines=8, interactive=False)
                check_connection_btn = gr.Button("🔄 Check Connection")
                
                gr.Markdown("### Quick Help")
                gr.Markdown("""
                **How to use:**
                1. Set up grading criteria in the top panel
                2. Optionally save/load criteria profiles for reuse
                3. Go to Input tab and paste text or upload a file
                4. Click "Grade Submission"
                5. View results in Output tab
                
                **Batch Processing:**
                - Upload multiple files in Batch tab
                - Enable plagiarism checking if needed
                - Results show in table format
                
                **Models:**
                - Only installed models are shown
                - Run `ollama pull <model>` to add more models
                """)
        
        # === EVENT HANDLERS ===
        
        # Profile management
        refresh_btn.click(
            fn=load_criteria_profiles,
            outputs=[profile_dropdown]
        )
        
        save_btn.click(
            fn=save_criteria_profile,
            inputs=[profile_name, assignment_instruction, grading_criteria, output_format, max_score, ai_keywords, additional_requirements],
            outputs=[profile_status, profile_dropdown]
        )
        
        load_btn.click(
            fn=load_criteria_profile,
            inputs=[profile_dropdown],
            outputs=[assignment_instruction, grading_criteria, profile_status, output_format, max_score, ai_keywords, additional_requirements]
        )
        
        delete_btn.click(
            fn=delete_criteria_profile,
            inputs=[profile_dropdown],
            outputs=[profile_status, profile_dropdown]
        )
        
        copy_btn.click(
            fn=copy_criteria_profile,
            inputs=[profile_dropdown, copy_name],
            outputs=[profile_status, profile_dropdown]
        )
        
        # Grading
        grade_btn.click(
            fn=grade_submission,
            inputs=[
                submission_text, file_upload,
                assignment_instruction, grading_criteria,
                output_format, max_score, ai_keywords, additional_requirements,
                temperature, model_dropdown, use_llm_parse
            ],
            outputs=[formatted_output, raw_output, detailed_fb, student_fb, extracted_text_display]
        )
        
        # Batch processing
        batch_grade_btn.click(
            fn=grade_batch,
            inputs=[
                batch_files,
                assignment_instruction, grading_criteria,
                check_plagiarism,
                output_format, max_score, ai_keywords, additional_requirements,
                temperature, model_dropdown
            ],
            outputs=[batch_status, batch_results, batch_summary, plagiarism_report]
        )
        
        # System info
        check_connection_btn.click(
            fn=check_ollama_connection,
            outputs=[connection_info]
        )
        
        # Load initial data
        app.load(
            fn=lambda: (check_ollama_connection(), load_criteria_profiles()),
            outputs=[connection_info, profile_dropdown]
        )
    
    return app


def launch_app():
    """Launch the Gradio application"""
    app = build_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    print("Starting Grading Assistant System...")
    print(f"Ollama Status: {check_ollama_connection()}")
    launch_app()

