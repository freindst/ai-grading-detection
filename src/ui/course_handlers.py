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
        return gr.update(choices=["[No courses - create one below]"], value=None)
    
    choices = [f"{c['id']}: {c['code']} - {c['name']}" for c in courses]
    return gr.update(choices=choices, value=None)


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
        dropdown_update = load_courses_dropdown()
        return "❌ Name and code required", dropdown_update
    
    course_id = db_manager.create_course(name, code, desc)
    if course_id == -1:
        dropdown_update = load_courses_dropdown()
        return f"❌ Code '{code}' exists", dropdown_update
    
    # Reload courses and select the newly created course
    courses = db_manager.get_all_courses()
    choices = [f"{c['id']}: {c['code']} - {c['name']}" for c in courses]
    new_selection = f"{course_id}: {code} - {name}"
    return f"✅ Created course: {name}", gr.update(choices=choices, value=new_selection)


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
        dropdown_update = load_courses_dropdown()
        return "❌ Select course first", dropdown_update
    
    if not name.strip() or not code.strip():
        dropdown_update = load_courses_dropdown()
        return "❌ Name and code required", dropdown_update
    
    if db_manager.update_course(int(course_id), name, code, desc):
        courses = db_manager.get_all_courses()
        choices = [f"{c['id']}: {c['code']} - {c['name']}" for c in courses]
        updated_selection = f"{course_id}: {code} - {name}"
        return f"✅ Updated course: {name}", gr.update(choices=choices, value=updated_selection)
    
    dropdown_update = load_courses_dropdown()
    return "❌ Update failed", dropdown_update


def delete_course_action(course_id):
    """Delete course"""
    db_manager = get_db_manager()
    if not course_id:
        dropdown_update = load_courses_dropdown()
        return "❌ Select course first", dropdown_update
    
    if db_manager.delete_course(int(course_id)):
        dropdown_update = load_courses_dropdown()
        return "✅ Course deleted", dropdown_update
    
    dropdown_update = load_courses_dropdown()
    return "❌ Delete failed", dropdown_update

