"""
Main Application Entry Point for Grading Assistant System

This is the cleaned-up modular version. All business logic has been extracted
to separate modules for better maintainability.
"""

import gradio as gr

# Core components
from src.llm_client import OllamaClient
from src.grading_engine import GradingEngine
from src.document_parser import DocumentParser
from src.batch_processor import BatchProcessor
from src.database import DatabaseManager

# UI modules
from src.ui import course_handlers, profile_handlers, grading_handlers

# Initialize global components (shared across all modules)
llm_client = OllamaClient()
grading_engine = GradingEngine(llm_client)
document_parser = DocumentParser()
batch_processor = BatchProcessor(grading_engine, max_workers=3)
db_manager = DatabaseManager()


def get_installed_models():
    """Get list of installed Ollama models"""
    try:
        models = llm_client.get_available_models()
        if not models:
            return ["⚠️ No models found - Check Ollama"]
        return models
    except Exception as e:
        print(f"Error getting models: {e}")
        return ["⚠️ Error connecting to Ollama"]


def check_ollama_status():
    """
    Check if Ollama is running and return status message.
    Returns tuple: (is_connected: bool, message: str, models: list)
    """
    try:
        models = llm_client.get_available_models()
        if models:
            model_list = ", ".join(models)
            return (
                True,
                f"✅ Ollama Connected | Models: {model_list}",
                models
            )
        else:
            return (
                False,
                f"⚠️ Ollama Not Responding | Check if Ollama is running at {llm_client.base_url}",
                []
            )
    except Exception as e:
        return (
            False,
            f"❌ Ollama Connection Error | {str(e)[:100]}",
            []
        )


def validate_grading_input(text: str, file) -> tuple:
    """
    Validate that at least one input (text or file) is provided before grading.
    
    Args:
        text: Text submission content
        file: Uploaded file
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    # Check if both are empty
    has_text = text and text.strip()
    has_file = file is not None
    
    if not has_text and not has_file:
        return False, "⚠️ No input provided. Please paste text or upload a file before grading."
    
    return True, ""


def validate_and_switch_tab(text: str, file):
    """
    Validate input and switch to Output tab if valid.
    Returns: (should_switch: bool, error_message: str)
    """
    is_valid, error_msg = validate_grading_input(text, file)
    if is_valid:
        return gr.Tabs(selected=1), ""  # Switch to Output tab
    else:
        return gr.Tabs(selected=0), error_msg  # Stay on Input tab, show error


def conditional_grade_with_loading(text, file, *args):
    """
    Wrapper that only calls grading if input is valid.
    Otherwise returns empty/error values for all outputs.
    """
    from src.ui.grading_handlers import grade_with_loading
    
    # Validate input first
    is_valid, error_msg = validate_grading_input(text, file)
    
    if not is_valid:
        # Yield empty values for all 12 outputs, with error in system_message
        yield (
            "",  # submission_preview
            "N/A",  # grade_result
            "",  # grading_reason
            "",  # student_feedback_output
            "",  # ai_keyword_result
            "",  # ai_disclosure_result
            0,  # context_bar (INTEGER percentage, not BarPlot object!)
            "",  # context_details
            "",  # raw_llm_output
            "",  # system_prompt_display
            "",  # user_prompt_display
            error_msg  # system_message with error
        )
        return  # Stop here, don't proceed with grading
    
    # Input is valid, proceed with normal grading (yield from generator)
    yield from grade_with_loading(text, file, *args)


def toggle_view_mode(view_mode):
    """
    Toggle between Classic View and Split View.
    
    Args:
        view_mode: "Classic" or "Split"
    
    Returns:
        Tuple of visibility updates for rows and button active states
    """
    if view_mode == "Classic":
        # Show full layout, hide split layout
        # Classic button active, Split button inactive
        return (
            gr.update(visible=True),   # full_layout_row
            gr.update(visible=False),  # split_layout_row
            gr.update(elem_classes=["theme-btn", "theme-btn-active"]),  # classic_btn (active)
            gr.update(elem_classes=["theme-btn"]),  # split_btn (inactive)
        )
    else:  # view_mode == "Split"
        # Hide full layout, show split layout
        # Split button active, Classic button inactive
        return (
            gr.update(visible=False),  # full_layout_row
            gr.update(visible=True),   # split_layout_row
            gr.update(elem_classes=["theme-btn"]),  # classic_btn (inactive)
            gr.update(elem_classes=["theme-btn", "theme-btn-active"]),  # split_btn (active)
        )


def build_interface():
    """
    Build the Gradio interface.
    
    This function imports all event handlers from the ui modules and wires them together.
    The UI layout is defined here, but the business logic is in separate handler modules.
    """
    
    # Import handler functions
    from src.ui.course_handlers import (
        load_courses_dropdown, create_course, load_course_details,
        update_course_action, delete_course_action
    )
    from src.ui.profile_handlers import (
        load_profiles_for_course, create_profile, update_profile_action,
        delete_profile_action, load_profile_into_fields
    )
    from src.ui.grading_handlers import (
        grade_with_loading, save_correction, format_feedback_table,
        delete_feedback_example, toggle_fewshot_status, view_feedback_details,
        handle_table_select, grade_batch
    )
    
    # Theme configuration
    theme = gr.themes.Base(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ).set(
        body_background_fill="#0a0a0a",
        panel_background_fill="#1a1a1a",
        block_background_fill="#2a2a2a",
        block_border_color="#404040",
        input_background_fill="#1a1a1a",
        input_border_color="#606060",
        input_background_fill_focus="#252525",
        input_border_color_focus="#0066ff",
        button_primary_background_fill="#0066ff",
        button_primary_background_fill_hover="#0052cc",
        button_secondary_background_fill="#333333",
        button_secondary_background_fill_hover="#444444",
        body_text_color="#f0f0f0",
        block_label_text_color="#e0e0e0",
        block_title_text_color="#0088ff",
        input_placeholder_color="#808080",
    )
    
    # Custom CSS for better contrast and styling
    custom_css = """
        .gradio-container {max-width: 100% !important; padding: 6px !important;}
        .contain {max-height: calc(100vh - 80px) !important; overflow-y: auto !important;}
        * {font-size: 11px !important;}
        h1 {font-size: 18px !important; margin: 8px 0 !important;}
        h3 {font-size: 12px !important; margin: 6px 0 !important;}
        textarea, input, select {
            color: #f0f0f0 !important; 
            background: #1a1a1a !important; 
            border: 1px solid #606060 !important;
        }
        textarea:focus, input:focus, select:focus {
            background: #252525 !important; 
            border-color: #0066ff !important;
        }
        h1 {color: #f0f0f0 !important;}
        h3 {color: #e0e0e0 !important;}
        label {color: #e0e0e0 !important; font-weight: 600 !important;}
        .gr-panel {background: #1a1a1a !important;}
        .tabitem {background: #1a1a1a !important;}
        .tabs > .tab-nav {background: #0a0a0a !important;}
        
        /* Copy feedback button styling */
        .copy-feedback-btn {
            background: #2563eb !important;
            color: white !important;
            border: 1px solid #1e40af !important;
            padding: 4px 8px !important;
            margin-left: auto !important;
            min-width: 80px !important;
        }
        .copy-feedback-btn:hover {
            background: #1d4ed8 !important;
            border-color: #1e3a8a !important;
        }
        .tab-nav button {
            color: #f0f0f0 !important;
            background: #2a2a2a !important;
            border: 1px solid #606060 !important;
        }
        .tab-nav button.selected,
        .tab-nav button[aria-selected="true"] {
            background: #0066ff !important;
            color: #ffffff !important;
        }
        .markdown-body, .gr-markdown {color: #f0f0f0 !important;}
        .gr-accordion {
            border: 1px solid #606060 !important;
            background: #1a1a1a !important;
        }
        
        /* Dropdown styling */
        .gr-dropdown {
            border: 1px solid currentColor !important;
        }
        .gr-dropdown input,
        .gr-dropdown .wrap,
        .gr-dropdown-wrapper input {
            color: #f0f0f0 !important;
            background: #1a1a1a !important;
            border: 1px solid #606060 !important;
            font-weight: 600 !important;
        }
        .gr-dropdown input:focus {
            background: #252525 !important;
            border-color: #0066ff !important;
        }
        
        /* Dropdown menu items */
        .gr-dropdown ul,
        .gr-dropdown-menu,
        .svelte-1gfkn6j,
        .options {
            background: #1a1a1a !important;
            border: 2px solid #606060 !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.5) !important;
        }
        .gr-dropdown li,
        .gr-dropdown-item,
        .item {
            color: #f0f0f0 !important;
            background: #1a1a1a !important;
            padding: 8px 12px !important;
            font-weight: 500 !important;
        }
        .gr-dropdown li:hover,
        .gr-dropdown-item:hover,
        .item:hover {
            background: #0066ff !important;
            color: #ffffff !important;
        }
        .gr-dropdown li.selected,
        .item.selected {
            background: #0066ff !important;
            color: #ffffff !important;
        }
        
        /* Checkboxes and Radio buttons */
        input[type="checkbox"] {
            width: 20px !important;
            height: 20px !important;
            cursor: pointer !important;
            accent-color: #0066ff !important;
            border: 2px solid #606060 !important;
        }
        input[type="radio"] {
            width: 18px !important;
            height: 18px !important;
            cursor: pointer !important;
            accent-color: #0066ff !important;
            border: 2px solid #606060 !important;
        }
        
        /* Dataframe/Table styling */
        .gr-dataframe table {
            background: #1a1a1a !important;
            color: #f0f0f0 !important;
        }
        .gr-dataframe th {
            background: #0066ff !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            padding: 10px !important;
            border: 2px solid #0044cc !important;
        }
        .gr-dataframe td {
            color: #f0f0f0 !important;
            background: #1a1a1a !important;
            border: 1px solid #606060 !important;
            padding: 8px !important;
            font-weight: 500 !important;
        }
        .gr-dataframe tr:hover td {
            background: #2a2a2a !important;
        }
        .gr-dataframe tr:nth-child(even) td {
            background: #0a0a0a !important;
        }
        .gr-dataframe tr.selected td,
        .gr-dataframe tr[aria-selected="true"] td {
            background: #0066ff !important;
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        .gr-dataframe .cell-wrap,
        .gr-dataframe .cell {
            color: inherit !important;
        }
        
        /* File uploader */
        .gr-file,
        .gr-file-upload,
        .upload-container,
        .file-preview,
        [data-testid="file-upload"] {
            color: #f0f0f0 !important;
            background: #1a1a1a !important;
            border: 2px solid #606060 !important;
        }
        .gr-file:hover,
        .gr-file-upload:hover {
            background: #252525 !important;
            border-color: #0066ff !important;
        }
        
        /* Common styles */
        .gr-button {font-weight: 600 !important; padding: 6px 12px !important;}
        .gr-box {padding: 8px !important;}
        .gr-form {gap: 6px !important;}
        
        /* Tab styling */
        .tabs {
            margin: 0 !important;
            padding: 0 !important;
        }
        .tabs > .tab-nav {
            padding: 8px 4px !important;
            margin: 0 !important;
            border-bottom: 2px solid #0066ff !important;
            display: flex !important;
            flex-wrap: wrap !important;
        }
        .tab-nav button {
            min-width: 100px !important;
            height: 44px !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            padding: 10px 16px !important;
            margin: 2px !important;
            border-radius: 4px !important;
        }
        
        /* Sliders */
        .gr-slider input[type="range"] {
            accent-color: #0066ff !important;
        }
        
        /* View mode toggle buttons */
        .theme-btn {
            border: 2px solid #404040 !important;
            background: #2a2a2a !important;
            color: #e0e0e0 !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
            transition: all 0.2s ease !important;
        }
        .theme-btn:hover {
            border-color: #606060 !important;
            background: #333333 !important;
        }
        .theme-btn-active {
            border: 2px solid #0066ff !important;
            background: #0066ff !important;
            color: #ffffff !important;
            font-weight: bold !important;
        }
        .theme-btn-active:hover {
            border-color: #0088ff !important;
            background: #0088ff !important;
        }
    """
    
    with gr.Blocks(title="Grading Assistant", theme=theme, css=custom_css) as app:
        
        gr.Markdown("# 🎓 Grading Assistant")
        
        # View mode toggle buttons
        with gr.Row():
            classic_btn = gr.Button("🏛️ Classic View", elem_classes=["theme-btn", "theme-btn-active"], scale=1)
            split_btn = gr.Button("⚡ Split View", elem_classes=["theme-btn"], scale=1)
        
        # System message area
        system_message = gr.Textbox(
            label="📢 System Messages",
            interactive=False,
            lines=2,
            max_lines=4,
            value="Ready",
            info="Status, notifications, and progress updates",
            show_copy_button=False
        )
        
        # FULL LAYOUT - Left Panel
        with gr.Row(visible=True) as full_layout_row:
            # LEFT PANEL - Tabs for Course and Profile Management
            with gr.Column(scale=1, min_width=340):
                with gr.Tabs():
                    # TAB 1: COURSE MANAGEMENT
                    with gr.Tab("📚 Courses"):
                        gr.Markdown("### Manage Courses")
                        
                        course_dropdown = gr.Dropdown(label="Select Course", choices=[], show_label=True)
                        
                        with gr.Row():
                            course_edit_btn = gr.Button("✏️ Edit", size="sm", scale=1)
                            course_delete_btn = gr.Button("🗑️ Delete", size="sm", scale=1, variant="stop")
                            course_refresh_btn = gr.Button("🔄", size="sm", scale=1)
                        
                        with gr.Accordion("➕ Create New Course", open=False):
                            new_course_name = gr.Textbox(label="Name", placeholder="Course name", max_lines=1)
                            new_course_code = gr.Textbox(label="Code", placeholder="e.g. CS101", max_lines=1)
                            new_course_desc = gr.Textbox(label="Description", placeholder="Optional", max_lines=2)
                            create_course_btn = gr.Button("➕ Create Course", variant="primary", size="sm")
                        
                        with gr.Accordion("✏️ Edit Selected Course", open=False) as edit_course_acc:
                            edit_course_id = gr.Textbox(label="ID", interactive=False, visible=False)
                            edit_course_name = gr.Textbox(label="Name", max_lines=1)
                            edit_course_code = gr.Textbox(label="Code", max_lines=1)
                            edit_course_desc = gr.Textbox(label="Description", max_lines=2)
                            update_course_btn = gr.Button("💾 Update Course", variant="secondary", size="sm")
                    
                    # TAB 2: PROFILE MANAGEMENT
                    with gr.Tab("💾 Profiles"):
                        gr.Markdown("### Manage Grading Profiles")
                        
                        gr.Markdown("**Step 1: Select Course**")
                        profile_course_dropdown = gr.Dropdown(label="Select Course First", choices=[], show_label=True)
                        
                        selected_course_info = gr.Textbox(label="Currently Managing", interactive=False, max_lines=1, value="[Select a course above]")
                        
                        gr.Markdown("**Step 2: Manage Profiles**")
                        profile_list = gr.Textbox(label="Profiles in This Course", lines=5, max_lines=5, interactive=False)
                        profile_dropdown = gr.Dropdown(label="Select Profile to Load/Delete", choices=[], show_label=True)
                        
                        profile_delete_btn = gr.Button("🗑️ Delete Selected Profile", size="sm", variant="stop")
                
                gr.Markdown("---")
                gr.Markdown("### ⚙️ Grading Setup / Profile Editor")
                
                profile_name_field = gr.Textbox(label="Profile Name (for saving)", placeholder="e.g., Essay Assignment 1", max_lines=1)
                
                with gr.Row():
                    save_as_new_btn = gr.Button("💾 Save as New Profile", size="sm", scale=1, variant="primary")
                    profile_update_btn = gr.Button("✏️ Update Selected Profile", size="sm", scale=1, variant="secondary")
                
                assignment_instruction = gr.Textbox(label="Instructions", placeholder="Task...", lines=3, max_lines=3)
                grading_criteria = gr.Textbox(label="Rubric", placeholder="Criteria...", lines=4, max_lines=4)
                
                with gr.Row():
                    output_format = gr.Dropdown(
                        choices=["letter", "numeric", "pass/fail"],
                        value="letter",
                        label="Output Format", 
                        scale=2
                    )
                    max_score = gr.Number(value=100, label="Max", precision=0, scale=1)
                
                    model_dropdown = gr.Dropdown(
                        choices=get_installed_models(),
                        value=get_installed_models()[0] if get_installed_models() else None,
                    label="Model"
                )
                temperature = gr.Slider(0.0, 1.0, value=0.3, step=0.1, label="Temp")
                
                gr.Markdown("---")
                gr.Markdown("### 🎯 Few-Shot Learning")
                gr.Markdown("Use saved good examples to guide the LLM:")
                use_few_shot = gr.Checkbox(label="Enable few-shot learning", value=True)
                num_examples = gr.Slider(minimum=0, maximum=5, value=2, step=1, label="Number of examples to use")
                
                gr.Markdown("---")
                gr.Markdown("### ⚠️ AI Detection")
                gr.Markdown("Keywords that will flag submission as AI-generated:")
                ai_keywords = gr.Textbox(
                    label="AI Detection Keywords (comma-separated)",
                    placeholder="e.g., ChatGPT, as an AI language model, I apologize",
                    lines=2,
                    max_lines=2
                )
                
                additional_requirements = gr.Textbox(
                    label="Additional Requirements",
                    placeholder="Extra grading requirements...",
                    lines=2,
                    max_lines=2
                )
                use_llm_parse = gr.Checkbox(label="Use LLM Parse if JSON fails", value=False)
        
            # RIGHT PANEL - Full Layout
            with gr.Column(scale=2):
                with gr.Tabs() as main_tabs:
                    with gr.Tab("📝 Input", id=0):
                        # Grade button at very top
                        grade_btn = gr.Button("🎓 Grade", variant="primary", size="lg")
                        clear_all_btn = gr.Button("🗑️ Clear All", variant="secondary", size="sm")
                        
                        gr.Markdown("---")
                        
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("**📁 File Submission**")
                                file_upload = gr.File(label="File", file_types=[".pdf", ".docx", ".doc", ".txt", ".jpg", ".png"])
                            with gr.Column():
                                gr.Markdown("**📝 Text Submission**")
                                submission_text = gr.Textbox(label="Text", placeholder="Paste work...", lines=16, max_lines=16)
                    
                    with gr.Tab("📊 Output", id=1):
                        # Submission Preview (shown immediately on grade start)
                        with gr.Accordion("📄 Submission Preview", open=True):
                            submission_preview = gr.Textbox(
                                label="Document Preview",
                                lines=6,
                                max_lines=6,
                                interactive=False,
                                placeholder="Preview will appear here when grading starts..."
                            )
                        
                        # Main Row: Grading Results (left) + Human Correction (right)
                        with gr.Row():
                            # LEFT COLUMN: Grading Results
                            with gr.Column(scale=3):
                                gr.Markdown("### Grading Results")
                                
                                # Row 1: Grade + AI Detection side by side
                                with gr.Row():
                                    with gr.Column(scale=1):
                                        with gr.Row():
                                            gr.Markdown("**Extracted Grade**")
                                            copy_grade_btn = gr.Button("📋 Copy", size="sm", elem_classes="copy-feedback-btn")
                                        grade_result = gr.Textbox(label="Grade", interactive=False, max_lines=2)
                                    with gr.Column(scale=1):
                                        gr.Markdown("**🔍 Keyword Detection**")
                                        ai_keyword_result = gr.Textbox(
                                            label="Exact Match (Regex)",
                                            interactive=False,
                                            max_lines=2,
                                            value="Not checked yet",
                                            info="Regex-based exact keyword matching"
                                        )
                                    with gr.Column(scale=1):
                                        gr.Markdown("**📋 AI Disclosure**")
                                        ai_disclosure_result = gr.Textbox(
                                            label="Academic Integrity Check",
                                            interactive=False,
                                            max_lines=4,
                                            value="Not checked yet",
                                            info="LLM analysis of AI usage disclosures"
                                        )
                                
                                # Row 2: Grading Reason + Student Feedback side by side
                                with gr.Row():
                                    with gr.Column(scale=1):
                                        gr.Markdown("**Grading Reason (for Instructor)**")
                                        grading_reason = gr.Textbox(label="Detailed Feedback", lines=6, max_lines=6, interactive=False)
                                    with gr.Column(scale=1):
                                        with gr.Row():
                                            gr.Markdown("**Student Feedback**")
                                            copy_student_feedback_btn = gr.Button("📋 Copy", size="sm", elem_classes="copy-feedback-btn")
                                        student_feedback_output = gr.Textbox(label="Feedback for Student", lines=6, max_lines=6, interactive=False)
                                
                                # Context Usage - more compact
                                gr.Markdown("---")
                                with gr.Row():
                                    context_bar = gr.Slider(minimum=0, maximum=100, value=0, label="Context Usage (%)", interactive=False, scale=2)
                                    with gr.Column(scale=1):
                                        context_details = gr.Markdown("Not calculated")
                                
                                # Debug accordions
                                with gr.Accordion("🔍 Debug: Raw LLM Output", open=False):
                                    raw_llm_output = gr.Textbox(label="Raw LLM Response", lines=12, max_lines=12, interactive=False)
                                
                                with gr.Accordion("🔍 Debug: Prompt Sent to LLM", open=False):
                                    system_prompt_display = gr.Textbox(label="System Prompt", lines=10, max_lines=10, interactive=False)
                                    user_prompt_display = gr.Textbox(label="User Prompt", lines=10, max_lines=10, interactive=False)
                            
                            # RIGHT COLUMN: Human Correction & Feedback
                            with gr.Column(scale=2):
                                gr.Markdown("### Human Correction & Feedback")
                                gr.Markdown("Save this grading for future reference:")
                
                                corrected_grade = gr.Textbox(label="Corrected Grade (if needed)", placeholder="Enter correct grade if AI was wrong", max_lines=1)
                                correction_comments = gr.Textbox(label="Comments/Suggestions", placeholder="Why was this good or bad? What should improve?", lines=5, max_lines=5)
                
                                gr.Markdown("**Mark this grading as:**")
                                with gr.Row():
                                    mark_as_good_btn = gr.Button("✅ Good Example", variant="primary", size="sm")
                                    mark_as_bad_btn = gr.Button("❌ Needs Improvement", variant="stop", size="sm")
                    
                    with gr.Tab("📦 Batch", id=2):
                        batch_files = gr.File(label="Files", file_count="multiple", file_types=[".pdf", ".docx", ".doc", ".txt"])
                        check_plagiarism = gr.Checkbox(label="Check Plagiarism", value=True)
                        batch_grade_btn = gr.Button("🎓 Grade Batch", variant="primary")
                        
                        batch_results = gr.Dataframe(headers=["File", "Grade", "Plag"], label="Results", max_height=450)
                    
                    with gr.Tab("💬 Feedback Library", id=3):
                        gr.Markdown("### Manage Saved Grading Feedback")
                        gr.Markdown("Review and manage all saved grading examples for training/reference")
                
                        with gr.Row():
                            refresh_feedback_btn = gr.Button("🔄 Refresh", size="sm")
                            delete_selected_btn = gr.Button("🗑️ Delete Selected", variant="stop", size="sm")
                        
                        feedback_table = gr.Dataframe(
                            headers=["Timestamp", "Category", "Original Grade", "Corrected Grade", "Comments", "Use Few-Shot", "Filename"],
                            label="Saved Feedback Examples",
                            max_height=300,
                            interactive=False
                        )
                        
                        gr.Markdown("---")
                        gr.Markdown("### Selected Example Details")
                        
                        selected_filename = gr.Textbox(label="Selected Filename", visible=False)
                        
                        with gr.Row():
                            with gr.Column():
                                detail_category = gr.Textbox(label="Category", interactive=False)
                                detail_original = gr.Textbox(label="Original Grade", lines=2, interactive=False)
                                detail_corrected = gr.Textbox(label="Corrected Grade", lines=2, interactive=False)
                            with gr.Column():
                                detail_reason = gr.Textbox(label="Grading Reason", lines=6, interactive=False)
                                detail_comments = gr.Textbox(label="Human Comments", lines=6, interactive=False)
                        
                        gr.Markdown("---")
                        gr.Markdown("### Few-Shot Learning Control")
                        with gr.Row():
                            use_for_fewshot_toggle = gr.Checkbox(
                                label="✅ Use this example for few-shot learning",
                                value=False,
                                interactive=True
                            )
                            update_fewshot_btn = gr.Button("Update Few-Shot Status", size="sm", variant="primary")
        
        # SPLIT VIEW LAYOUT - Input on Left, Output on Right
        with gr.Row(visible=False) as split_layout_row:
            # LEFT COLUMN: Input Panel
            with gr.Column(scale=1):
                gr.Markdown("### ⚡ Split View - Quick Input")
                
                # Action buttons
                split_grade_btn = gr.Button("🎓 Grade", variant="primary", size="lg")
                split_clear_btn = gr.Button("🗑️ Clear All", variant="secondary", size="sm")
                
                gr.Markdown("---")
                
                # File upload
                gr.Markdown("**📁 File Submission**")
                split_file_upload = gr.File(
                    label="File", 
                    file_types=[".pdf", ".docx", ".doc", ".txt", ".jpg", ".png"]
                )
                
                # Text submission
                gr.Markdown("**📝 Text Submission**")
                split_submission_text = gr.Textbox(
                    label="Text", 
                    placeholder="Paste student work here...", 
                    lines=25, 
                    max_lines=25
                )
            
            # RIGHT COLUMN: Output Panel (ALL outputs except submission preview)
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Grading Results")
                
                # Main grading results
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Row():
                            gr.Markdown("**Extracted Grade**")
                            copy_split_grade_btn = gr.Button("📋 Copy", size="sm", elem_classes="copy-feedback-btn")
                        split_grade_result = gr.Textbox(label="Grade", interactive=False, max_lines=2)
                    with gr.Column(scale=1):
                        gr.Markdown("**🔍 Keyword Detection**")
                        split_ai_keyword_result = gr.Textbox(
                            label="Exact Match (Regex)",
                            interactive=False,
                            max_lines=2,
                            value="Not checked yet",
                            info="Regex-based exact keyword matching"
                        )
                
                # Detailed Feedback
                gr.Markdown("**📝 Detailed Feedback (for instructor)**")
                split_detailed_feedback = gr.Textbox(
                    label="Detailed Feedback",
                    lines=6,
                    max_lines=6,
                    interactive=False,
                    placeholder="Detailed feedback will appear here..."
                )
                
                # Student Feedback
                with gr.Row():
                    gr.Markdown("**💬 Student Feedback**")
                    copy_split_student_feedback_btn = gr.Button("📋 Copy", size="sm", elem_classes="copy-feedback-btn")
                split_student_feedback = gr.Textbox(
                    label="Student Feedback",
                    lines=6,
                    max_lines=6,
                    interactive=False,
                    placeholder="Student-facing feedback will appear here..."
                )
                
                # Strengths and Weaknesses
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("**✅ Strengths**")
                        split_strengths = gr.Textbox(
                            label="Strengths",
                            lines=4,
                            max_lines=4,
                            interactive=False,
                            placeholder="Strengths identified..."
                        )
                    with gr.Column():
                        gr.Markdown("**❌ Weaknesses**")
                        split_weaknesses = gr.Textbox(
                            label="Weaknesses",
                            lines=4,
                            max_lines=4,
                            interactive=False,
                            placeholder="Areas for improvement..."
                        )
                
                # Deductions
                gr.Markdown("**📉 Deductions**")
                split_deductions = gr.Textbox(
                    label="Deductions",
                    lines=3,
                    max_lines=3,
                    interactive=False,
                    placeholder="Point deductions will appear here..."
                )
                
                # Statistics
                with gr.Accordion("📈 Grading Statistics", open=False):
                    split_stats = gr.Textbox(
                        label="Statistics",
                        lines=6,
                        max_lines=6,
                        interactive=False,
                        placeholder="Statistics will appear here..."
                    )
                
                # Human Correction Panel
                with gr.Accordion("✏️ Human Correction", open=False):
                    gr.Markdown("**Adjust grade or feedback if needed**")
                    with gr.Row():
                        split_corrected_grade = gr.Textbox(
                            label="Corrected Grade",
                            placeholder="Enter corrected grade...",
                            scale=1
                        )
                        split_correction_reason = gr.Textbox(
                            label="Reason for Correction",
                            placeholder="Why did you change the grade?",
                            scale=2
                        )
                    split_corrected_feedback = gr.Textbox(
                        label="Corrected Feedback",
                        placeholder="Adjusted feedback for student...",
                        lines=4,
                        max_lines=4
                    )
                    split_save_correction_btn = gr.Button("💾 Save Correction", variant="primary")
                    split_correction_status = gr.Textbox(
                        label="Status",
                        interactive=False,
                        max_lines=2
                    )
                
                # Prompts (for debugging)
                with gr.Accordion("🔍 View Prompts", open=False):
                    split_system_prompt = gr.Textbox(label="System Prompt", lines=10, max_lines=10, interactive=False)
                    split_user_prompt = gr.Textbox(label="User Prompt", lines=10, max_lines=10, interactive=False)
                
                # Hidden outputs for compatibility with grading function (not displayed in split view)
                split_submission_preview = gr.Textbox(visible=False)
                split_ai_disclosure_result = gr.Textbox(visible=False)
                split_context_bar = gr.Slider(minimum=0, maximum=100, value=0, interactive=False, visible=False)
                split_context_details = gr.Textbox(visible=False)
                split_raw_llm_output = gr.Textbox(visible=False)
        
        # === EVENT HANDLERS ===
        
        # View mode toggle buttons (Classic vs Split)
        classic_btn.click(
            fn=lambda: toggle_view_mode("Classic"),
            inputs=[],
            outputs=[full_layout_row, split_layout_row, classic_btn, split_btn]
        )
        
        split_btn.click(
            fn=lambda: toggle_view_mode("Split"),
            inputs=[],
            outputs=[full_layout_row, split_layout_row, classic_btn, split_btn]
        )
        
        # Course refresh
        course_refresh_btn.click(
            fn=load_courses_dropdown,
            outputs=[course_dropdown]
        ).then(
            fn=load_courses_dropdown,
            outputs=[profile_course_dropdown]
        )
        
        # Profile course selection changes profile list
        profile_course_dropdown.change(
            fn=load_profiles_for_course,
            inputs=[profile_course_dropdown],
            outputs=[selected_course_info, profile_dropdown, profile_list]
        )
        
        # Auto-load profile when selected
        profile_dropdown.select(
            fn=load_profile_into_fields,
            inputs=[profile_dropdown],
            outputs=[
                assignment_instruction,
                grading_criteria,
                output_format,
                max_score,
                ai_keywords,
                additional_requirements,
                system_message
            ]
        )
        
        # Course create
        create_course_btn.click(
            fn=create_course,
            inputs=[new_course_name, new_course_code, new_course_desc],
            outputs=[system_message, course_dropdown]
        ).then(
            fn=load_courses_dropdown,
            outputs=[profile_course_dropdown]
        )
        
        # Course edit button - load details
        course_edit_btn.click(
            fn=load_course_details,
            inputs=[course_dropdown],
            outputs=[edit_course_id, edit_course_name, edit_course_code, edit_course_desc]
        )
        
        # Course update
        update_course_btn.click(
            fn=update_course_action,
            inputs=[edit_course_id, edit_course_name, edit_course_code, edit_course_desc],
            outputs=[system_message, course_dropdown]
        ).then(
            fn=load_courses_dropdown,
            outputs=[profile_course_dropdown]
        )
        
        # Course delete
        course_delete_btn.click(
            fn=delete_course_action,
            inputs=[edit_course_id],
            outputs=[system_message, course_dropdown]
        ).then(
            fn=load_courses_dropdown,
            outputs=[profile_course_dropdown]
        )
        
        # Profile create (save as new)
        save_as_new_btn.click(
            fn=create_profile,
            inputs=[profile_course_dropdown, profile_name_field, assignment_instruction, grading_criteria,
                    output_format, max_score, ai_keywords, additional_requirements],
            outputs=[system_message, selected_course_info, profile_dropdown, profile_list]
        )
        
        # Profile update
        profile_update_btn.click(
            fn=update_profile_action,
            inputs=[profile_dropdown, profile_name_field, assignment_instruction, grading_criteria,
                    output_format, max_score, ai_keywords, additional_requirements, profile_course_dropdown],
            outputs=[system_message, selected_course_info, profile_dropdown, profile_list,
                     assignment_instruction, grading_criteria, output_format, max_score, ai_keywords, additional_requirements]
        )
        
        # Profile delete
        profile_delete_btn.click(
            fn=delete_profile_action,
            inputs=[profile_dropdown, profile_course_dropdown],
            outputs=[system_message, selected_course_info, profile_dropdown, profile_list]
        )
        
        # Clear all button - clears both text and file
        clear_all_btn.click(
            fn=lambda: ("", None),
            outputs=[submission_text, file_upload]
        )
        
        # Grading with loading state - validate input, switch tab if valid, then grade
        grade_btn.click(
            fn=validate_and_switch_tab,
            inputs=[submission_text, file_upload],
            outputs=[main_tabs, system_message]
        ).then(
            fn=conditional_grade_with_loading,
            inputs=[submission_text, file_upload, assignment_instruction, grading_criteria,
                output_format, max_score, ai_keywords, additional_requirements,
                    temperature, model_dropdown, use_llm_parse, use_few_shot, num_examples],
            outputs=[submission_preview, grade_result, grading_reason, student_feedback_output,
                     ai_keyword_result, ai_disclosure_result, context_bar, context_details,
                     raw_llm_output, system_prompt_display, user_prompt_display, system_message]
        )
        
        # === SPLIT VIEW HANDLERS ===
        
        # Split view clear button
        split_clear_btn.click(
            fn=lambda: ("", None),
            outputs=[split_submission_text, split_file_upload]
        )
        
        # Split view grade button - uses course/profile data from full layout sidebar
        split_grade_btn.click(
            fn=conditional_grade_with_loading,
            inputs=[
                split_submission_text, split_file_upload,
                assignment_instruction, grading_criteria, output_format, max_score,
                ai_keywords, additional_requirements, temperature, model_dropdown,
                use_llm_parse, use_few_shot, num_examples
            ],
            outputs=[
                split_submission_preview,
                split_grade_result,
                split_detailed_feedback,
                split_student_feedback,
                split_ai_keyword_result,
                split_ai_disclosure_result,
                split_context_bar,
                split_context_details,
                split_raw_llm_output,
                split_system_prompt,
                split_user_prompt,
                system_message
            ]
        )
        
        # Split view save correction
        split_save_correction_btn.click(
            fn=lambda cg, cr, cf: (f"✅ Correction saved: {cg}" if cg else "❌ No grade entered"),
            inputs=[split_corrected_grade, split_correction_reason, split_corrected_feedback],
            outputs=[split_correction_status]
        )
        
        # Copy buttons for student feedback (uses JavaScript to copy to clipboard)
        copy_student_feedback_btn.click(
            fn=None,
            inputs=[student_feedback_output],
            outputs=[],
            js="(feedback) => { navigator.clipboard.writeText(feedback); return []; }"
        )
        
        copy_split_student_feedback_btn.click(
            fn=None,
            inputs=[split_student_feedback],
            outputs=[],
            js="(feedback) => { navigator.clipboard.writeText(feedback); return []; }"
        )
        
        # Copy buttons for grade (uses JavaScript to copy to clipboard)
        copy_grade_btn.click(
            fn=None,
            inputs=[grade_result],
            outputs=[],
            js="(grade) => { navigator.clipboard.writeText(grade); return []; }"
        )
        
        copy_split_grade_btn.click(
            fn=None,
            inputs=[split_grade_result],
            outputs=[],
            js="(grade) => { navigator.clipboard.writeText(grade); return []; }"
        )
        
        # Save correction
        mark_as_good_btn.click(
            fn=lambda g, r, s, cg, c: save_correction(g, r, s, cg, c, True),
            inputs=[grade_result, grading_reason, student_feedback_output, corrected_grade, correction_comments],
            outputs=[system_message]
        )
        
        # Mark as bad example
        mark_as_bad_btn.click(
            fn=lambda g, r, s, cg, c: save_correction(g, r, s, cg, c, False),
            inputs=[grade_result, grading_reason, student_feedback_output, corrected_grade, correction_comments],
            outputs=[system_message]
        )
        
        # Feedback library management
        refresh_feedback_btn.click(
            fn=format_feedback_table,
            outputs=[feedback_table]
        )
        
        # Select row in feedback table to view details
        feedback_table.select(
            fn=handle_table_select,
            outputs=[selected_filename]
        ).then(
            fn=view_feedback_details,
            inputs=[selected_filename],
            outputs=[detail_category, detail_original, detail_reason, detail_corrected, detail_comments, use_for_fewshot_toggle]
        )
        
        # Update few-shot status
        update_fewshot_btn.click(
            fn=toggle_fewshot_status,
            inputs=[selected_filename, use_for_fewshot_toggle],
            outputs=[system_message, feedback_table]
        )
        
        # Delete selected feedback
        delete_selected_btn.click(
            fn=delete_feedback_example,
            inputs=[selected_filename],
            outputs=[system_message, feedback_table]
        )
        
        batch_grade_btn.click(
            fn=grade_batch,
            inputs=[batch_files, assignment_instruction, grading_criteria, check_plagiarism,
                output_format, max_score, ai_keywords, additional_requirements,
                    temperature, model_dropdown],
            outputs=[system_message, batch_results]
        )
        
        # Initial load
        app.load(
            fn=lambda: check_ollama_status()[1],  # Check Ollama and show status
            outputs=[system_message]
        ).then(
            fn=load_courses_dropdown,
            outputs=[course_dropdown]
        ).then(
            fn=load_courses_dropdown,
            outputs=[profile_course_dropdown]
        ).then(
            fn=format_feedback_table,
            outputs=[feedback_table]
        )
    
    return app


def launch_app():
    """Launch the application"""
    app = build_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    print("🚀 Starting Grading Assistant System (Modular Version)...")
    print("🔍 Checking Ollama connection...")
    
    is_connected, status_msg, models = check_ollama_status()
    if is_connected:
        print(f"✅ {status_msg}")
    else:
        print(f"⚠️ {status_msg}")
        print("   The app will still start, but you won't be able to grade until Ollama is running.")
    
    launch_app()
