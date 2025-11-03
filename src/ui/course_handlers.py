"""
Course Management Handlers

Handles all CRUD operations for courses: create, read, update, delete.
"""

import gradio as gr


def get_db_manager():
    """Get database manager instance from main app"""
    from src import app
    return app.db_manager


def load_courses_dropdown():
    """Load courses for dropdown"""
    db_manager = get_db_manager()
    courses = db_manager.get_all_courses()
    if not courses:
        return gr.Dropdown(choices=["[No courses - create one below]"], value=None)
    
    choices = [f"{c['id']}: {c['code']} - {c['name']}" for c in courses]
    return gr.Dropdown(choices=choices, value=None)


def parse_course_id(selection):
    """Extract course ID from selection"""
    if not selection or "[No courses" in selection:
        return None
    try:
        return int(selection.split(":")[0])
    except:
        return None


def create_course(name, code, desc):
    """Create new course"""
    db_manager = get_db_manager()
    if not name.strip() or not code.strip():
        return "❌ Name and code required", "", load_courses_dropdown()
    
    course_id = db_manager.create_course(name, code, desc)
    if course_id == -1:
        return f"❌ Code '{code}' exists", "", load_courses_dropdown()
    
    dropdown = load_courses_dropdown()
    # Select the newly created course
    new_selection = f"{course_id}: {code} - {name}"
    return f"✅ Created course: {name}", "", gr.Dropdown(choices=dropdown.choices, value=new_selection)


def load_course_details(selection):
    """Load course details for editing"""
    db_manager = get_db_manager()
    course_id = parse_course_id(selection)
    if not course_id:
        return "", "", "", ""
    
    course = db_manager.get_course(course_id)
    if course:
        return course['id'], course['name'], course['code'], course.get('description', '')
    return "", "", "", ""


def update_course_action(course_id, name, code, desc):
    """Update course"""
    db_manager = get_db_manager()
    if not course_id:
        return "❌ Select course first", "", load_courses_dropdown()
    
    if not name.strip() or not code.strip():
        return "❌ Name and code required", "", load_courses_dropdown()
    
    if db_manager.update_course(int(course_id), name, code, desc):
        dropdown = load_courses_dropdown()
        updated_selection = f"{course_id}: {code} - {name}"
        return f"✅ Updated course: {name}", "", gr.Dropdown(choices=dropdown.choices, value=updated_selection)
    return "❌ Update failed", "", load_courses_dropdown()


def delete_course_action(course_id):
    """Delete course"""
    db_manager = get_db_manager()
    if not course_id:
        return "❌ Select course first", "", load_courses_dropdown()
    
    if db_manager.delete_course(int(course_id)):
        return "✅ Course deleted", "", load_courses_dropdown()
    return "❌ Delete failed", "", load_courses_dropdown()

