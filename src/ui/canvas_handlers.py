"""
Canvas UI Handlers - Event handlers for Canvas LMS integration
"""

import gradio as gr
from typing import Tuple, Dict


def get_canvas_client():
    """Get canvas client instance from main app"""
    from src import app
    return app.canvas_client


def get_canvas_manager():
    """Get canvas grading manager instance from main app"""
    from src import app
    return app.canvas_grading_manager


def get_db_manager():
    """Get database manager instance from main app"""
    from src import app
    return app.db_manager


# Authentication handlers
def connect_to_canvas(canvas_url: str, access_token: str) -> Tuple[str, str, str]:
    """
    Connect to Canvas and verify credentials
    
    Returns:
        Tuple of (status_message, courses_dropdown_value, instructor_name)
    """
    if not canvas_url or not access_token:
        return "⚠️ Please enter Canvas URL and access token", gr.Dropdown(choices=[]), ""
    
    canvas_client = get_canvas_client()
    
    # Set credentials
    canvas_client.set_credentials(canvas_url, access_token)
    
    # Verify connection
    success, message, user_info = canvas_client.verify_connection()
    
    if not success:
        return message, gr.Dropdown(choices=[]), ""
    
    # Store encrypted credentials in database
    from src.canvas_client import TokenEncryption
    encrypted_token = TokenEncryption.encrypt_token(access_token)
    
    db = get_db_manager()
    db.store_canvas_credentials(
        canvas_url=canvas_url,
        access_token_encrypted=encrypted_token,
        instructor_name=user_info["name"]
    )
    
    # Get courses
    success, courses = canvas_client.get_courses()
    
    if not success:
        return f"{message}\n⚠️ Could not load courses: {courses}", gr.Dropdown(choices=[]), user_info["name"]
    
    if not courses:
        return f"{message}\n⚠️ No courses found", gr.Dropdown(choices=[]), user_info["name"]
    
    # Format courses for dropdown
    course_choices = [f"{c['id']} - {c['name']}" for c in courses]
    
    return f"{message}\n✅ Loaded {len(courses)} courses", gr.Dropdown(choices=course_choices, value=course_choices[0] if course_choices else None), user_info["name"]


def load_stored_credentials() -> Tuple[str, str, str, str]:
    """
    Load stored Canvas credentials on startup
    
    Returns:
        Tuple of (canvas_url, access_token_hint, status, instructor_name)
    """
    db = get_db_manager()
    creds = db.get_canvas_credentials()
    
    if not creds:
        return "", "", "No stored credentials", ""
    
    from src.canvas_client import TokenEncryption
    
    try:
        decrypted_token = TokenEncryption.decrypt_token(creds["access_token_encrypted"])
        
        # Set in client
        canvas_client = get_canvas_client()
        canvas_client.set_credentials(creds["canvas_url"], decrypted_token)
        
        # Verify it still works
        success, message, user_info = canvas_client.verify_connection()
        
        if success:
            return creds["canvas_url"], decrypted_token, f"✅ Loaded credentials for {user_info['name']}", user_info["name"]
        else:
            return creds["canvas_url"], "", f"⚠️ Stored credentials expired: {message}", ""
    
    except Exception as e:
        return "", "", f"❌ Error loading credentials: {str(e)[:100]}", ""


# Course and assignment handlers
def load_assignments_for_course(course_selection: str) -> Tuple[str, str]:
    """
    Load assignments when course is selected
    
    Args:
        course_selection: Selected course string (format: "ID - Name")
        
    Returns:
        Tuple of (assignments_dropdown, assignment_info_text)
    """
    if not course_selection:
        return gr.Dropdown(choices=[]), "Select a course first"
    
    # Parse course ID
    try:
        course_id = int(course_selection.split(" - ")[0])
    except (ValueError, IndexError):
        return gr.Dropdown(choices=[]), "Invalid course selection"
    
    canvas_client = get_canvas_client()
    success, assignments = canvas_client.get_assignments(course_id)
    
    if not success:
        return gr.Dropdown(choices=[]), f"❌ Error loading assignments: {assignments}"
    
    if not assignments:
        return gr.Dropdown(choices=[]), "No assignments found for this course"
    
    # Format assignments for dropdown
    assignment_choices = [f"{a['id']} - {a['name']}" for a in assignments]
    
    return gr.Dropdown(choices=assignment_choices, value=assignment_choices[0] if assignment_choices else None), f"✅ Loaded {len(assignments)} assignments"


def show_assignment_details(course_selection: str, assignment_selection: str) -> str:
    """
    Show details for selected assignment
    
    Returns:
        Assignment details text
    """
    if not course_selection or not assignment_selection:
        return "Select course and assignment"
    
    try:
        course_id = int(course_selection.split(" - ")[0])
        assignment_id = int(assignment_selection.split(" - ")[0])
    except (ValueError, IndexError):
        return "Invalid selection"
    
    canvas_client = get_canvas_client()
    
    # Get assignment details
    success, assignments = canvas_client.get_assignments(course_id)
    
    if not success:
        return f"Error: {assignments}"
    
    assignment = next((a for a in assignments if a["id"] == assignment_id), None)
    
    if not assignment:
        return "Assignment not found"
    
    # Get submission count
    success, submissions = canvas_client.get_submissions(course_id, assignment_id)
    submission_count = len(submissions) if success else "Unknown"
    
    details = f"""
**Assignment:** {assignment['name']}
**Points Possible:** {assignment['points_possible']}
**Due Date:** {assignment['due_at'] or 'No due date'}
**Submission Types:** {', '.join(assignment['submission_types'])}
**Total Submissions:** {submission_count}
"""
    
    return details


# Grading handlers
def download_and_grade_submissions(
    course_selection: str,
    assignment_selection: str,
    instructions: str,
    criteria: str,
    output_format: str,
    max_score: int,
    ai_keywords: str,
    model: str,
    temperature: float,
    progress=gr.Progress()
) -> Tuple[str, str]:
    """
    Download submissions from Canvas and grade them
    
    Returns:
        Tuple of (result_message, sessions_table_html)
    """
    if not course_selection or not assignment_selection:
        return "❌ Please select course and assignment", ""
    
    if not instructions or not criteria:
        return "❌ Please provide assignment instructions and grading criteria", ""
    
    try:
        course_id = int(course_selection.split(" - ")[0])
        course_name = " - ".join(course_selection.split(" - ")[1:])
        assignment_id = int(assignment_selection.split(" - ")[0])
        assignment_name = " - ".join(assignment_selection.split(" - ")[1:])
    except (ValueError, IndexError):
        return "❌ Invalid course/assignment selection", ""
    
    # Progress callback
    def update_progress(current, total, message):
        progress((current, total), desc=message)
    
    # Start grading
    manager = get_canvas_manager()
    result = manager.download_and_grade_assignment(
        course_id=course_id,
        course_name=course_name,
        assignment_id=assignment_id,
        assignment_name=assignment_name,
        assignment_instructions=instructions,
        grading_criteria=criteria,
        output_format=output_format,
        max_score=max_score,
        ai_keywords=ai_keywords,
        model=model,
        temperature=temperature,
        progress_callback=update_progress
    )
    
    if not result["success"]:
        return f"❌ {result['error']}", ""
    
    # Create result message
    message = f"""
✅ **Grading Complete!**
- Session ID: {result['session_id']}
- Total Submissions: {result['total_submissions']}
- Successfully Graded: {result['graded_count']}
- Errors: {result['error_count']}
"""
    
    if result["errors"]:
        message += "\n**Errors:**\n" + "\n".join(f"- {e}" for e in result["errors"][:5])
    
    # Refresh sessions table
    sessions_html = load_grading_sessions()
    
    return message, sessions_html


def load_grading_sessions() -> str:
    """
    Load all grading sessions and format as HTML table
    
    Returns:
        HTML table of sessions
    """
    db = get_db_manager()
    sessions = db.get_all_grading_sessions()
    
    if not sessions:
        return "<p style='color: #000000;'>No grading sessions yet. Download and grade an assignment to create one.</p>"
    
    # Build HTML table with consistent styling
    html = """
<table style="width:100%; background-color: #f9f9f9; color: #000000; border-collapse: collapse;">
    <thead>
        <tr style="background-color: #e0e0e0; color: #000000;">
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Session ID</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Course</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Assignment</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Date</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Status</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Progress</th>
        </tr>
    </thead>
    <tbody>
"""
    
    for session in sessions:
        status_icon = "✅" if session["status"] == "completed" else "⚠️" if "error" in session["status"] else "🔄"
        
        html += f"""
        <tr style="background-color: #ffffff; color: #000000;" onmouseover="this.style.backgroundColor='#e8f4f8';" onmouseout="this.style.backgroundColor='#ffffff';">
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000; font-weight: bold;">{session['id']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{session['course_name']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{session['assignment_name']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{session['started_at'][:16]}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{status_icon} {session['status']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{session['graded_count']}/{session['total_submissions']} graded, {session['uploaded_count']} uploaded</td>
        </tr>
"""
    
    html += """
    </tbody>
</table>
<br>
<p style="font-size: 12px; color: #000000;">
<b>💡 Use the Session ID to load grades in the sections below</b><br>
Hover over rows for highlight effect.
</p>
"""
    
    return html


# Grade review and editing handlers
def load_session_for_review(session_id: int) -> Tuple[str, str, str]:
    """
    Load a grading session for review
    
    Returns:
        Tuple of (session_info, grades_table_html, filter_dropdown)
    """
    if not session_id:
        return "Enter a session ID", "", gr.Dropdown(choices=["All", "Needs Review", "Ready to Upload"], value="All")
    
    db = get_db_manager()
    session = db.get_grading_session(session_id)
    
    if not session:
        return f"❌ Session {session_id} not found", "", gr.Dropdown(choices=["All", "Needs Review", "Ready to Upload"], value="All")
    
    # Session info
    info = f"""
**Course:** {session['course_name']}
**Assignment:** {session['assignment_name']}
**Total Submissions:** {session['total_submissions']}
**Graded:** {session['graded_count']}
**Uploaded:** {session['uploaded_count']}
**Status:** {session['status']}
"""
    
    # Load grades
    grades_html = load_grades_table(session_id, "All")
    
    return info, grades_html, gr.Dropdown(choices=["All", "Needs Review", "Ready to Upload"], value="All")


def load_grades_table(session_id: int, filter_type: str = "All") -> str:
    """
    Load grades for a session and format as HTML table
    
    Args:
        session_id: Session ID
        filter_type: "All", "Needs Review", or "Ready to Upload"
        
    Returns:
        HTML table of grades
    """
    db = get_db_manager()
    
    filter_map = {
        "All": "all",
        "Needs Review": "needs_review",
        "Ready to Upload": "ready_to_upload"
    }
    
    grades = db.get_session_grades(session_id, filter_map.get(filter_type, "all"))
    
    if not grades:
        return f"<p style='color: #000000;'>No grades found with filter: {filter_type}</p>"
    
    # Build HTML table with JavaScript for click-to-load
    html = f"""
<div id="grades-table-{session_id}">
<table style="width:100%; background-color: #f9f9f9; color: #000000; border-collapse: collapse;">
    <thead>
        <tr style="background-color: #e0e0e0; color: #000000;">
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Grade ID</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Student</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Parsed Grade</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Final Grade</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Status</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Upload Status</th>
            <th style="padding: 10px; border: 1px solid #ccc; color: #000000; font-weight: bold;">Action</th>
        </tr>
    </thead>
    <tbody>
"""
    
    for grade in grades:
        needs_review = "⚠️ Needs Review" if grade["needs_review"] else "✅ Reviewed"
        upload_status = {"pending": "⏳ Pending", "uploaded": "✅ Uploaded", "failed": "❌ Failed"}.get(grade["upload_status"], grade["upload_status"])
        
        # Highlight if manual grade differs from parsed
        grade_style = "background-color: #ffffcc; color: #000000;"
        if not (grade["manual_grade"] and grade["manual_grade"] != grade["parsed_grade"]):
            grade_style = "background-color: #ffffff; color: #000000;"
        
        html += f"""
        <tr style="background-color: #ffffff; color: #000000;" onmouseover="this.style.backgroundColor='#e8f4f8';" onmouseout="this.style.backgroundColor='#ffffff';">
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{grade['id']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{grade['student_name']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{grade['parsed_grade']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; {grade_style}">{grade['final_grade']}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{needs_review}</td>
            <td style="padding: 8px; border: 1px solid #ddd; color: #000000;">{upload_status}</td>
            <td style="padding: 8px; border: 1px solid #ddd; text-align: center;">
                <button onclick="(function(){{
                    const gradeId = {grade['id']};
                    const sessionId = {session_id};
                    console.log('Loading grade ID:', gradeId, 'from session:', sessionId);
                    
                    // Find inputs by looking for specific section
                    let sessionIdInput = null;
                    let gradeIdInput = null;
                    
                    // Strategy: Find all number inputs and identify them by their position and context
                    const allInputs = document.querySelectorAll('input[type=\\'number\\']');
                    
                    // Find by checking the actual aria-label or nearby text
                    for (let input of allInputs) {{
                        const ariaLabel = input.getAttribute('aria-label') || '';
                        
                        // Also check parent labels
                        let parent = input.parentElement;
                        let contextText = '';
                        for (let i = 0; i < 5; i++) {{
                            if (!parent) break;
                            contextText += (parent.textContent || '');
                            parent = parent.parentElement;
                        }}
                        
                        // Match Grade ID specifically (more specific than Session ID)
                        if ((ariaLabel === 'Grade ID' || contextText.includes('Grade ID')) && 
                            !contextText.includes('Session ID') &&
                            contextText.includes('Edit Individual Grade')) {{
                            gradeIdInput = input;
                        }}
                        // Match Session ID in the Grade Review section
                        else if ((ariaLabel === 'Session ID' || contextText.includes('Session ID')) &&
                                 contextText.includes('Grade Review')) {{
                            sessionIdInput = input;
                        }}
                    }}
                    
                    // Set session ID if found and not already set
                    if (sessionIdInput && parseInt(sessionIdInput.value) !== sessionId) {{
                        sessionIdInput.value = sessionId;
                        sessionIdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        sessionIdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    
                    // Set grade ID
                    if (gradeIdInput) {{
                        gradeIdInput.value = gradeId;
                        gradeIdInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        gradeIdInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        // Click Load Grade button
                        setTimeout(() => {{
                            const buttons = document.querySelectorAll('button');
                            for (let btn of buttons) {{
                                const btnText = btn.textContent || '';
                                if (btnText.includes('📝') && btnText.includes('Load Grade')) {{
                                    btn.click();
                                    break;
                                }}
                            }}
                        }}, 300);
                    }} else {{
                        alert('Could not find Grade ID field. Grade ID: ' + gradeId + ', Session: ' + sessionId);
                    }}
                }})()" 
                        style="padding: 6px 12px; cursor: pointer; background: #2563eb; color: white; border: none; border-radius: 4px; font-weight: bold;">
                    Load
                </button>
            </td>
        </tr>
"""
    
    html += """
    </tbody>
</table>
</div>
<br>
<p style="font-size: 12px; color: #000000;">
<b>💡 Click "Load" button to edit a grade</b><br>
Yellow highlight = Manual grade differs from parsed grade<br>
Hover over rows for highlight effect.
</p>
"""
    
    return html


def get_grade_details(session_id: int, grade_id: int) -> Tuple[str, str, str, str, str, bool]:
    """
    Get details for a specific grade to edit
    
    Returns:
        Tuple of (student_name, parsed_grade, manual_grade, comments, raw_json, needs_review)
    """
    import sys
    print(f"DEBUG: get_grade_details called with session_id={session_id}, grade_id={grade_id}", flush=True, file=sys.stderr)
    
    if not session_id or not grade_id:
        print("DEBUG: Missing session_id or grade_id", flush=True, file=sys.stderr)
        return "ERROR: Missing ID", "", "", "", "", False
    
    db = get_db_manager()
    grades = db.get_session_grades(session_id)
    print(f"DEBUG: Found {len(grades) if grades else 0} grades in session {session_id}", flush=True, file=sys.stderr)
    
    grade = next((g for g in grades if g["id"] == grade_id), None)
    
    if not grade:
        print(f"DEBUG: Grade {grade_id} not found in session {session_id}", flush=True, file=sys.stderr)
        return f"Grade {grade_id} not found", "", "", "", "", False
    
    print(f"DEBUG: Found grade for {grade['student_name']}", flush=True, file=sys.stderr)
    
    return (
        grade["student_name"],
        grade["parsed_grade"],
        grade["manual_grade"] or grade["parsed_grade"],
        grade["manual_comments"] or grade["parsed_student_feedback"],
        grade["raw_llm_json"],
        grade["needs_review"] == 1
    )


def update_grade(session_id: int, grade_id: int, new_grade: str, new_comments: str, mark_reviewed: bool) -> Tuple[str, str]:
    """
    Update a grade with manual edits
    
    Returns:
        Tuple of (result_message, refreshed_grades_table)
    """
    if not session_id or not grade_id:
        return "❌ Invalid session or grade ID", ""
    
    db = get_db_manager()
    success = db.update_manual_grade(
        grade_id=grade_id,
        manual_grade=new_grade,
        manual_comments=new_comments,
        mark_reviewed=mark_reviewed
    )
    
    if success:
        message = f"✅ Grade {grade_id} updated successfully"
        if mark_reviewed:
            message += " and marked as reviewed"
    else:
        message = f"❌ Failed to update grade {grade_id}"
    
    # Refresh table
    grades_html = load_grades_table(session_id, "All")
    
    return message, grades_html


def accept_all_parsed_grades(session_id: int) -> Tuple[str, str]:
    """
    Accept all parsed grades and mark as reviewed
    
    Returns:
        Tuple of (result_message, refreshed_grades_table)
    """
    if not session_id:
        return "❌ Invalid session ID", ""
    
    db = get_db_manager()
    grades = db.get_session_grades(session_id, "needs_review")
    
    count = 0
    for grade in grades:
        success = db.update_manual_grade(
            grade_id=grade["id"],
            manual_grade=grade["parsed_grade"],
            manual_comments=grade["parsed_student_feedback"],
            mark_reviewed=True
        )
        if success:
            count += 1
    
    message = f"✅ Accepted and reviewed {count} grades"
    grades_html = load_grades_table(session_id, "All")
    
    return message, grades_html


# Upload handlers
def upload_all_grades(session_id: int, progress=gr.Progress()) -> str:
    """
    Upload all reviewed grades to Canvas
    
    Returns:
        Result message
    """
    if not session_id:
        return "❌ Invalid session ID"
    
    def update_progress(current, total, message):
        progress((current, total), desc=message)
    
    manager = get_canvas_manager()
    result = manager.upload_grades_to_canvas(session_id, progress_callback=update_progress)
    
    if result["success"]:
        message = f"✅ All grades uploaded successfully!\n"
    else:
        message = f"⚠️ Upload completed with errors\n"
    
    message += f"- Uploaded: {result['uploaded_count']}\n"
    message += f"- Failed: {result['failed_count']}\n"
    
    if result.get("errors"):
        message += "\n**Errors:**\n" + "\n".join(f"- {e}" for e in result["errors"][:5])
    
    return message


def upload_single_grade(session_id: int, grade_id: int) -> str:
    """
    Upload a single grade to Canvas
    
    Returns:
        Result message
    """
    if not session_id or not grade_id:
        return "❌ Invalid session or grade ID"
    
    manager = get_canvas_manager()
    result = manager.upload_single_grade(session_id, grade_id)
    
    if result["success"]:
        return f"✅ Grade {grade_id} uploaded successfully"
    else:
        return f"❌ Failed to upload grade {grade_id}: {result.get('error', 'Unknown error')}"


# Spreadsheet view handlers
def load_grades_spreadsheet(session_id: int) -> Tuple[list, str]:
    """
    Load all grades for a session into a spreadsheet-style dataframe
    
    Returns:
        Tuple of (dataframe_rows, info_message)
    """
    if not session_id:
        return [], "❌ Invalid session ID"
    
    db = get_db_manager()
    
    # Get session info
    session = db.get_grading_session(session_id)
    if not session:
        return [], f"❌ Session {session_id} not found"
    
    # Get all grades
    grades = db.get_session_grades(session_id)
    if not grades:
        return [], f"⚠️ Session {session_id} has no grades yet"
    
    # Build dataframe rows
    rows = []
    for grade in grades:
        # Truncate long text fields
        submission_preview = (grade.get("submission_text", "") or "")[:200]
        if len(grade.get("submission_text", "") or "") > 200:
            submission_preview += "..."
        
        feedback_preview = (grade.get("parsed_detailed_feedback", "") or "")[:200]
        if len(grade.get("parsed_detailed_feedback", "") or "") > 200:
            feedback_preview += "..."
        
        raw_json_preview = (grade.get("raw_llm_json", "") or "")[:200]
        if len(grade.get("raw_llm_json", "") or "") > 200:
            raw_json_preview += "..."
        
        # Determine final grade and comments
        final_grade = grade.get("final_grade") or grade.get("manual_grade") or grade.get("parsed_grade", "")
        final_comments = grade.get("final_comments") or grade.get("manual_comments") or grade.get("parsed_student_feedback", "")
        
        rows.append([
            grade["id"],
            grade["student_name"],
            grade.get("parsed_grade", ""),
            final_grade,
            final_comments,
            submission_preview,
            feedback_preview,
            raw_json_preview,
            "Yes" if grade.get("needs_review", 1) else "No"
        ])
    
    info = f"✅ Loaded {len(rows)} grades from session {session_id} - {session['assignment_name']}"
    return rows, info


def save_bulk_grades(session_id: int, dataframe: list, mark_all_reviewed: bool) -> str:
    """
    Save all modified grades from the spreadsheet
    
    Args:
        session_id: Grading session ID
        dataframe: List of rows from the dataframe
        mark_all_reviewed: If True, mark all grades as reviewed
        
    Returns:
        Result message
    """
    if not session_id:
        return "❌ Invalid session ID"
    
    if not dataframe or len(dataframe) == 0:
        return "❌ No data to save"
    
    db = get_db_manager()
    
    updated_count = 0
    error_count = 0
    errors = []
    
    # Process each row
    for row in dataframe:
        try:
            # Extract values from row
            # Columns: ID, Student, Parsed Grade, Final Grade, Comments, Submission, Feedback, Raw JSON, Needs Review
            grade_id = int(row[0])
            final_grade = str(row[3]) if row[3] else ""
            final_comments = str(row[4]) if row[4] else ""
            
            # Update in database
            success = db.update_manual_grade(
                grade_id=grade_id,
                manual_grade=final_grade,
                manual_comments=final_comments,
                mark_reviewed=mark_all_reviewed
            )
            
            if success:
                updated_count += 1
            else:
                error_count += 1
                errors.append(f"Grade ID {grade_id}: Update failed")
        
        except Exception as e:
            error_count += 1
            errors.append(f"Row error: {str(e)[:50]}")
    
    # Build result message
    message = f"✅ Bulk save complete:\n"
    message += f"- Updated: {updated_count}\n"
    message += f"- Errors: {error_count}\n"
    
    if mark_all_reviewed:
        message += f"- All grades marked as reviewed\n"
    
    if errors:
        message += "\n⚠️ **Errors:**\n" + "\n".join(f"- {e}" for e in errors[:5])
        if len(errors) > 5:
            message += f"\n- ... and {len(errors) - 5} more"
    
    return message


def export_grades_csv(session_id: int) -> Tuple[str, str]:
    """
    Export all grades to CSV file with full (non-truncated) data
    
    Returns:
        Tuple of (file_path, message)
    """
    import csv
    from pathlib import Path
    from datetime import datetime
    
    if not session_id:
        return None, "❌ Invalid session ID"
    
    db = get_db_manager()
    
    # Get session info
    session = db.get_grading_session(session_id)
    if not session:
        return None, f"❌ Session {session_id} not found"
    
    # Get all grades
    grades = db.get_session_grades(session_id)
    if not grades:
        return None, f"⚠️ Session {session_id} has no grades to export"
    
    # Create export directory
    export_dir = Path("data/canvas_exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"session_{session_id}_{timestamp}.csv"
    file_path = export_dir / filename
    
    # Write CSV
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "ID", "Student Name", "Student ID",
            "Parsed Grade", "Manual Grade", "Final Grade",
            "Parsed Feedback", "Manual Comments", "Final Comments",
            "Submission Text", "Detailed Feedback", "Raw LLM JSON",
            "Needs Review", "Reviewed At", "Uploaded At", "Upload Status"
        ])
        
        # Data rows
        for grade in grades:
            writer.writerow([
                grade["id"],
                grade["student_name"],
                grade["student_id"],
                grade.get("parsed_grade", ""),
                grade.get("manual_grade", ""),
                grade.get("final_grade", ""),
                grade.get("parsed_student_feedback", ""),
                grade.get("manual_comments", ""),
                grade.get("final_comments", ""),
                grade.get("submission_text", ""),
                grade.get("parsed_detailed_feedback", ""),
                grade.get("raw_llm_json", ""),
                "Yes" if grade.get("needs_review", 1) else "No",
                grade.get("reviewed_at", ""),
                grade.get("uploaded_at", ""),
                grade.get("upload_status", "")
            ])
    
    message = f"✅ Exported {len(grades)} grades to CSV:\n`{file_path}`"
    return str(file_path), message

