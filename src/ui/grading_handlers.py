"""
Grading Handlers

Handles all grading operations, feedback management, few-shot learning,
and batch processing.
"""

import gradio as gr
import json
import os
import time
import random
from datetime import datetime


def get_components():
    """Get initialized components from main app"""
    from src import app
    return (
        app.llm_client,
        app.grading_engine,
        app.document_parser,
        app.batch_processor,
        app.db_manager
    )


def validate_grading_profile(instruction, rubric):
    """
    Validate that a grading profile is loaded before grading.
    
    Args:
        instruction: Assignment instruction text
        rubric: Grading rubric/criteria text
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not instruction or not instruction.strip():
        return False, "⚠️ No assignment instruction provided! Please load a profile or enter instructions."
    
    if not rubric or not rubric.strip():
        return False, "⚠️ No grading rubric provided! Please load a profile or enter grading criteria."
    
    return True, ""


# === TOKEN ESTIMATION & CONTEXT ===

def estimate_tokens(text):
    """Rough token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4


def get_model_max_tokens(model_name):
    """Return max context for common models"""
    model_limits = {
        "mistral": 8192,
        "llama2": 4096,
        "llama3": 8192,
        "codellama": 16384,
        "phi": 2048,
    }
    for key, limit in model_limits.items():
        if key in model_name.lower():
            return limit
    return 4096  # default


def format_context_display(estimated_tokens, max_tokens):
    """Format context usage display"""
    percentage = (estimated_tokens / max_tokens) * 100
    
    if percentage >= 90:
        status = "🔴 CRITICAL - Too close to limit!"
    elif percentage >= 75:
        status = "🟡 WARNING - Approaching limit"
    elif percentage >= 50:
        status = "🟢 MODERATE usage"
    else:
        status = "🟢 GOOD - Plenty of space"
    
    details = f"**{estimated_tokens:,} tokens** / {max_tokens:,} max | {status}"
    return percentage, details


# === FEW-SHOT LEARNING ===

def load_feedback_examples():
    """Load all saved feedback examples"""
    corrections_dir = "data/corrections"
    if not os.path.exists(corrections_dir):
        return []
    
    examples = []
    for filename in sorted(os.listdir(corrections_dir), reverse=True):
        if filename.endswith('.json'):
            filepath = os.path.join(corrections_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['filename'] = filename
                    examples.append(data)
            except:
                pass
    
    return examples


def select_few_shot_examples(max_examples=3, min_required=2):
    """
    Select good examples for few-shot in-context learning
    
    Args:
        max_examples: Maximum number of examples to include
        min_required: Minimum examples needed to enable few-shot (default: 2)
    
    Returns:
        tuple: (few_shot_text, status_message, num_examples_found)
    """
    examples = load_feedback_examples()
    
    # Filter only good examples
    good_examples = [ex for ex in examples if ex.get('is_good_example', False)]
    
    num_found = len(good_examples)
    
    # Not enough examples for few-shot learning
    if num_found < min_required:
        if num_found == 0:
            return "", "ℹ️ Few-shot learning disabled: No good examples saved yet. Mark some gradings as good examples first.", 0
        else:
            return "", f"ℹ️ Few-shot learning disabled: Only {num_found} example(s) saved, need at least {min_required} for effective learning.", num_found
    
    # Take up to max_examples (most recent first, or random if more available)
    if num_found <= max_examples:
        selected = good_examples[:max_examples]
    else:
        selected = random.sample(good_examples, max_examples)
    
    # Format as few-shot examples
    few_shot_text = "\n\n# EXAMPLES OF GOOD GRADING (for your reference):\n\n"
    
    for i, ex in enumerate(selected, 1):
        original_grade = ex.get('original_grade', '')
        reasoning = ex.get('grading_reason', '')
        comments = ex.get('human_comments', '')
        
        few_shot_text += f"## Example {i}:\n"
        few_shot_text += f"**Grade Given:** {original_grade}\n"
        few_shot_text += f"**Reasoning:** {reasoning[:300]}{'...' if len(reasoning) > 300 else ''}\n"
        few_shot_text += f"**Why this was effective:** {comments[:200]}{'...' if len(comments) > 200 else ''}\n\n"
    
    few_shot_text += "Please use these examples as guidance for consistency and quality.\n\n"
    
    status = f"✅ Using {len(selected)} good example(s) for few-shot learning (from {num_found} available)"
    
    return few_shot_text, status, len(selected)


# === GRADING OPERATIONS ===

def generate_preview(filename, text):
    """
    Generate preview showing filename and first 5 non-empty lines
    
    Args:
        filename: Name of file or "Direct Text Submission"
        text: Full submission text
    
    Returns:
        Formatted preview string
    """
    lines = text.split('\n')
    
    # Filter out empty lines (after stripping whitespace)
    non_empty_lines = [line for line in lines if line.strip()]
    
    # Get first 5 non-empty lines
    preview_lines = non_empty_lines[:5]
    
    preview = f"📄 File: {filename}\n"
    preview += f"📊 Total Length: {len(text)} characters, {len(lines)} lines ({len(non_empty_lines)} non-empty)\n"
    preview += "─" * 60 + "\n"
    preview += "First 5 non-empty lines:\n"
    preview += "─" * 60 + "\n"
    for i, line in enumerate(preview_lines, 1):
        # Truncate long lines
        display_line = line[:100] + "..." if len(line) > 100 else line
        preview += f"{i}. {display_line}\n"
    
    return preview


def grade_submission(text, file_obj, instructions, criteria, fmt, score, keywords, reqs, temp, model, use_llm, use_few_shot, num_examples):
    """Grade submission"""
    llm_client, grading_engine, document_parser, batch_processor, db_manager = get_components()
    
    # Validate grading profile is loaded
    is_valid, error_msg = validate_grading_profile(instructions, criteria)
    if not is_valid:
        preview = "⚠️ Validation failed - no submission preview"
        return (
            preview,  # submission_preview
            "N/A",  # grade
            "",  # grading_reason
            "",  # student_feedback
            "",  # ai_detection
            "",  # context_bar
            "",  # context_details
            "",  # raw_output
            "",  # system_prompt
            "",  # user_prompt
            error_msg,  # status_message (error)
            ""  # notification_message
        )
    
    # Determine filename and extract text
    if file_obj:
        filename = os.path.basename(file_obj.name) if hasattr(file_obj, 'name') else "uploaded_file"
        parse_result = document_parser.parse_file(file_obj.name if hasattr(file_obj, 'name') else file_obj)
        if not parse_result['success']:
            return "", f"❌ Parse error: {parse_result['error']}", "", "", "", 0, "", "", "", "", ""
        text_to_grade = parse_result['text']
    elif text.strip():
        filename = "Direct Text Submission"
        text_to_grade = text
    else:
        return "", "❌ Provide text or file", "", "", "", 0, "", "", "", "", ""
    
    # Generate preview immediately
    preview = generate_preview(filename, text_to_grade)
    
    if not instructions.strip() or not criteria.strip():
        return preview, "❌ Instructions and criteria required", "", "", "", 0, "", "", "", "", ""
    
    # Stage 1: Regex keyword detection (instant, accurate)
    from src.ai_detector import AIDetector
    ai_detector = AIDetector()
    
    keywords_found = []
    if keywords and keywords.strip():
        keywords_found = ai_detector.detect_keywords(text_to_grade, keywords)
    
    llm_client.set_model(model)
    llm_client.clear_context()
    
    # Get few-shot examples if enabled
    few_shot_examples = ""
    few_shot_status = ""
    if use_few_shot and num_examples > 0:
        few_shot_examples, few_shot_status, num_used = select_few_shot_examples(max_examples=int(num_examples), min_required=2)
    elif use_few_shot and num_examples == 0:
        few_shot_status = "ℹ️ Few-shot learning: Slider set to 0 examples"
    elif not use_few_shot:
        few_shot_status = "ℹ️ Few-shot learning: Disabled by user"
    
    # Build prompts for debugging
    system_prompt, user_prompt = grading_engine.build_grading_prompt(
        submission_text=text_to_grade,
        assignment_instruction=instructions,
        grading_criteria=criteria,
        output_format=fmt,
        max_score=int(score) if score else 100,
        ai_keywords=keywords,
        additional_requirements=reqs,
        few_shot_examples=few_shot_examples
    )
    
    # Estimate tokens
    total_text = system_prompt + user_prompt + text_to_grade
    estimated_tokens = estimate_tokens(total_text)
    model_max = get_model_max_tokens(model)
    context_percentage, context_text = format_context_display(estimated_tokens, model_max)
    
    result = grading_engine.grade_submission(
        submission_text=text_to_grade,
        assignment_instruction=instructions,
        grading_criteria=criteria,
        output_format=fmt,
        max_score=int(score) if score else 100,
        ai_keywords=keywords,
        additional_requirements=reqs,
        temperature=temp,
        keep_context=False,
        few_shot_examples=few_shot_examples
    )
    
    if not result.get('success'):
        error = result.get('error', 'Error')
        # Check for context overflow
        if "context" in error.lower() or "too long" in error.lower() or "overflow" in error.lower():
            return (
                preview,
                f"❌ {error}",
                "Context overflow - submission + prompts exceed model capacity",
                "Cannot grade - input too large",
                "🔴 CONTEXT OVERFLOW",
                100,
                "**Model capacity exceeded!** Try: 1) Shorter submission, 2) Simpler rubric, 3) Larger context model",
                "",
                "",
                "",
                ""
            )
        return preview, f"❌ {error}", "", "", "", 0, "", "", "", "", ""
    
    # Get ACTUAL token counts from Ollama
    actual_prompt_tokens = result.get('prompt_tokens', 0)
    actual_completion_tokens = result.get('completion_tokens', 0)
    total_duration_ns = result.get('total_duration', 0)
    
    # Use actual tokens if available, otherwise use estimate
    if actual_prompt_tokens > 0:
        context_percentage, context_text = format_context_display(actual_prompt_tokens, model_max)
        
        # Add recommendations
        recommendations = []
        if context_percentage >= 90:
            recommendations.append("🔴 **CRITICAL**: Very close to limit - use shorter inputs or larger model")
        elif context_percentage >= 75:
            recommendations.append("🟡 **WARNING**: Consider shorter submissions or switch to larger context model")
        elif context_percentage >= 50:
            recommendations.append("🟢 Moderate usage - model handling this fine")
        else:
            recommendations.append("🟢 Good usage - plenty of capacity")
        
        # Add performance info
        if total_duration_ns > 0:
            duration_sec = total_duration_ns / 1_000_000_000
            recommendations.append(f"⏱️ Processing time: {duration_sec:.1f}s")
        
        if actual_completion_tokens > 0:
            recommendations.append(f"📤 Output: {actual_completion_tokens} tokens")
        
        context_text = f"{context_text}\n\n" + "\n".join(recommendations)
    else:
        # Fallback to estimate
        context_percentage, context_text = format_context_display(estimated_tokens, model_max)
        context_text += "\n\n⚠️ Actual token count not available from model"
    
    parsed = result['parsed_result']
    grade = parsed.get('grade', 'N/A')
    
    # Only use LLM fallback parsing if grade extraction actually failed
    if use_llm and (grade == 'N/A' or grade is None or grade == ''):
        fallback_parsed = grading_engine.llm_based_parse(result['raw_llm_output'])
        if fallback_parsed.get('grade') not in ['N/A', None, '']:
            parsed = fallback_parsed
            grade = parsed.get('grade', 'N/A')
    
    grading_reason = parsed.get('detailed_feedback', 'N/A')
    student_fb = parsed.get('student_feedback', 'N/A')
    raw_output = result['raw_llm_output']
    
    # Stage 2: AI disclosure analysis (LLM-based)
    ai_disclosure = {"disclosure_found": False, "recommendation": "NOT_CHECKED"}
    if keywords and keywords.strip():
        try:
            ai_disclosure = ai_detector.analyze_ai_disclosure(text_to_grade, llm_client)
        except Exception as e:
            ai_disclosure = {
                "disclosure_found": False,
                "error": str(e),
                "recommendation": "ERROR"
            }
    
    # Format keyword detection result
    if keywords_found:
        keyword_display = f"🔍 Found {len(keywords_found)} keyword(s): {', '.join(keywords_found)}"
    else:
        keyword_display = "✅ No keywords detected"
    
    # Format disclosure analysis result
    if ai_disclosure.get("disclosure_found"):
        disclosure_type = ai_disclosure.get('disclosure_type', 'unclear')
        tools = ', '.join(ai_disclosure.get('ai_tools_mentioned', [])) or 'Generic AI tool'
        statement = ai_disclosure.get('disclosure_statement', '') or ''  # Ensure not None
        assessment = ai_disclosure.get('assessment', 'unknown')
        recommendation = ai_disclosure.get('recommendation', 'UNKNOWN')
        evidence = ai_disclosure.get('evidence', '') or ''  # Ensure not None
        
        # Safe string slicing
        statement_preview = statement[:200] + ('...' if len(statement) > 200 else '') if statement else 'N/A'
        
        disclosure_display = f"""✓ Disclosure Found: Yes
Type: {disclosure_type}
AI Tools: {tools}
Statement: "{statement_preview}"
Assessment: {assessment}
Evidence: {evidence}
Recommendation: {recommendation}"""
    elif ai_disclosure.get("error"):
        error_msg = ai_disclosure.get('error', 'Unknown error')
        evidence = ai_disclosure.get('evidence', '')
        recommendation = ai_disclosure.get('recommendation', 'ERROR')
        
        # Provide informative error message with guidance
        if 'JSON parse error' in error_msg or 'Expecting value' in error_msg:
            disclosure_display = f"""⚠️ Disclosure Check Error
Issue: LLM returned invalid JSON format
Status: Analysis incomplete
Recommendation: {recommendation}

This might happen if:
• The LLM model is struggling with the task
• The context is too long
• The model needs to be restarted

You can still grade the submission normally - this only affects AI disclosure detection."""
        elif 'Empty response' in error_msg:
            disclosure_display = f"""⚠️ Disclosure Check Error
Issue: LLM returned empty response
Status: Analysis incomplete
Recommendation: {recommendation}

The model may be:
• Overloaded or timing out
• Not responding properly
• Needing to be restarted

You can still grade the submission normally - this only affects AI disclosure detection."""
        elif 'LLM generation error' in error_msg or 'generation failed' in error_msg:
            disclosure_display = f"""⚠️ Disclosure Check Error
Issue: {error_msg}
Status: Analysis incomplete
Recommendation: {recommendation}

LLM generation failed. Check:
• Is Ollama running?
• Is the selected model loaded?
• Is the model responding to other tasks?

You can still grade the submission normally - this only affects AI disclosure detection."""
        else:
            disclosure_display = f"""⚠️ Disclosure Check Error
Issue: {error_msg}
Evidence: {evidence}
Recommendation: {recommendation}

You can still grade the submission normally - this only affects AI disclosure detection."""
    elif not keywords or not keywords.strip():
        disclosure_display = "ℹ️ No keywords configured - AI disclosure check skipped"
    else:
        disclosure_display = "❌ No AI usage disclosure found in submission"
    
    return (
        preview,
        grade,
        grading_reason,
        student_fb,
        keyword_display,  # AI keyword detection result
        disclosure_display,  # AI disclosure analysis result
        context_percentage,
        context_text,
        raw_output,
        system_prompt,
        user_prompt,
        few_shot_status  # Add few-shot status to return values
    )


def grade_with_loading(text, file_obj, instructions, criteria, fmt, score, keywords, reqs, temp, model, use_llm, use_few_shot, num_examples):
    """Grade submission with loading state"""
    start_time = time.time()
    
    # Show loading state - now returns preview + system_message
    yield (
        "⏳ Parsing document...",  # preview
        "⏳ Processing...",        # grade
        "⏳ Waiting for LLM...",   # grading_reason
        "⏳ Waiting...",            # student_feedback
        "⏳ Checking keywords...",  # keyword_display (NEW)
        "⏳ Analyzing disclosure...", # disclosure_display (NEW)
        0,                          # context_percentage
        "Calculating...",          # context_text
        "",                         # raw_output
        "",                         # system_prompt
        "",                         # user_prompt
        "⏳ Grading in progress..."  # system_message (combined)
    )
    
    result = grade_submission(text, file_obj, instructions, criteria, fmt, score, keywords, reqs, temp, model, use_llm, use_few_shot, num_examples)
    
    elapsed = time.time() - start_time
    
    # Extract few-shot status (last element) from result
    result_list = list(result)
    few_shot_notification = result_list[-1] if len(result_list) > 11 else ""
    
    # Create combined system message
    status = f"✅ Grading completed in {elapsed:.1f}s"
    notification = few_shot_notification if few_shot_notification else ""
    
    # Combine status and notification with clear separation
    if notification:
        system_message = f"{status}\n{notification}"
    else:
        system_message = status
    
    # Remove the few_shot_status from result list and add combined system_message
    result_list = result_list[:-1]  # Remove the few_shot_status
    result_list.append(system_message)  # Add single combined message
    
    yield tuple(result_list)


# === FEEDBACK MANAGEMENT ===

def save_correction(grade, reason, student_fb, corrected_grade, comments, is_good_example):
    """Save human correction and comments"""
    corrections_dir = "data/corrections"
    os.makedirs(corrections_dir, exist_ok=True)
    
    # Count existing good examples
    existing_good = len([f for f in os.listdir(corrections_dir) if f.endswith('.json')])
    
    correction_data = {
        "timestamp": datetime.now().isoformat(),
        "original_grade": grade,
        "grading_reason": reason,
        "student_feedback": student_fb,
        "corrected_grade": corrected_grade,
        "human_comments": comments,
        "is_good_example": is_good_example,
        "category": "good_example" if is_good_example else "needs_improvement"
    }
    
    filename = f"{corrections_dir}/correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(correction_data, f, indent=2, ensure_ascii=False)
        
        status = f"✅ Saved as {'good example' if is_good_example else 'correction'}"
        notification = f"ℹ️ Now have {existing_good + 1} saved examples" if is_good_example else ""
        return status, notification
    except Exception as e:
        return f"❌ Failed to save: {str(e)}", ""


def format_feedback_table():
    """Format feedback examples as table data with few-shot status"""
    examples = load_feedback_examples()
    
    if not examples:
        return []
    
    table_data = []
    for ex in examples:
        timestamp = ex.get('timestamp', '')[:19].replace('T', ' ')  # Format: YYYY-MM-DD HH:MM:SS
        category = "✅ Good" if ex.get('is_good_example', False) else "❌ Needs Work"
        original = ex.get('original_grade', '')[:20]
        corrected = ex.get('corrected_grade', '')[:20] if ex.get('corrected_grade') else original
        comments = ex.get('human_comments', '')[:50]
        use_fewshot = "✓" if ex.get('is_good_example', False) else ""  # NEW: Few-shot indicator
        
        table_data.append([
            timestamp,
            category,
            original,
            corrected,
            comments,
            use_fewshot,  # NEW column
            ex.get('filename', '')
        ])
    
    return table_data


def delete_feedback_example(filename):
    """Delete a specific feedback example"""
    if not filename:
        return "❌ No file selected", "", format_feedback_table()
    
    filepath = os.path.join("data/corrections", filename)
    
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return f"✅ Deleted {filename}", "", format_feedback_table()
        else:
            return "❌ File not found", "", format_feedback_table()
    except Exception as e:
        return f"❌ Error: {str(e)}", "", format_feedback_table()


def toggle_fewshot_status(filename, enable):
    """Toggle whether example is used for few-shot learning"""
    if not filename:
        return "❌ No file selected", "", format_feedback_table()
    
    filepath = os.path.join("data/corrections", filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['is_good_example'] = enable
        data['category'] = "good_example" if enable else "needs_improvement"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        status = f"✅ Updated: {'Enabled' if enable else 'Disabled'} for few-shot learning"
        notification = "ℹ️ Changes will take effect on next grading"
        return status, notification, format_feedback_table()
    except Exception as e:
        return f"❌ Error: {str(e)}", "", format_feedback_table()


def view_feedback_details(filename):
    """Load details of a specific feedback example"""
    if not filename:
        return "Select an example from the table", "", "", "", "", False
    
    filepath = os.path.join("data/corrections", filename)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        category = "✅ Good Example" if data.get('is_good_example', False) else "❌ Needs Improvement"
        is_fewshot = data.get('is_good_example', False)  # NEW
        
        return (
            category,
            data.get('original_grade', ''),
            data.get('grading_reason', ''),
            data.get('corrected_grade', '') if data.get('corrected_grade') else data.get('original_grade', ''),
            data.get('human_comments', ''),
            is_fewshot  # NEW: Set checkbox state
        )
    except Exception as e:
        return f"Error: {str(e)}", "", "", "", "", False


def handle_table_select(evt: gr.SelectData):
    """Handle table row selection and extract filename"""
    import pandas as pd
    
    # Get the dataframe from feedback table
    table_data = format_feedback_table()
    
    if evt.index is not None and isinstance(table_data, pd.DataFrame):
        row_idx = evt.index[0]  # Get row index
        if row_idx < len(table_data):
            # Return the filename (last column)
            return table_data.iloc[row_idx, -1]
    
    return ""


# === BATCH PROCESSING ===

def grade_batch(files, instructions, criteria, check_plag, fmt, score, keywords, reqs, temp, model):
    """Grade batch"""
    llm_client, grading_engine, document_parser, batch_processor, db_manager = get_components()
    
    if not files:
        return "❌ Upload files", []
    
    if not instructions.strip() or not criteria.strip():
        return "❌ Instructions and criteria required", []
    
    llm_client.set_model(model)
    file_paths = [f.name if hasattr(f, 'name') else f for f in files]
    
    results = batch_processor.process_batch(
        file_paths=file_paths,
        assignment_instruction=instructions,
        grading_criteria=criteria,
        output_format=fmt,
        max_score=int(score) if score else 100,
        ai_keywords=keywords,
        temperature=temp,
        progress_callback=None,
        check_plagiarism=check_plag
    )
    
    table_data = []
    for result in results:
        plag = "None"
        if result.get('plagiarism_pairs'):
            max_sim = max((p['similarity'] for p in result['plagiarism_pairs']), default=0)
            if max_sim >= 80:
                plag = f"🔴{max_sim}%"
            elif max_sim >= 60:
                plag = f"🟡{max_sim}%"
            else:
                plag = f"🟢{max_sim}%"
        
        table_data.append([
            result['filename'],
            result['grade'] if result['success'] else "Error",
            plag
        ])
    
    return f"✅ Processed {len(results)} files", table_data

