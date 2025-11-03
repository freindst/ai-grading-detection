"""
Profile Management Handlers

Handles all CRUD operations for grading profiles (criteria templates linked to courses).
Profiles are tied to courses through assignments.
"""

import gradio as gr


def get_db_manager():
    """Get database manager instance from main app"""
    from src import app
    return app.db_manager


def parse_course_id(selection):
    """Extract course ID from selection (reused from course_handlers)"""
    if not selection or "[No courses" in selection:
        return None
    try:
        return int(selection.split(":")[0])
    except:
        return None


def load_profiles_for_course(course_selection):
    """Load profiles that belong to selected course"""
    db_manager = get_db_manager()
    course_id = parse_course_id(course_selection)
    
    if not course_id:
        return (
            "[Select a course first]",
            gr.update(choices=["[Select a course first]"], value=None),
            "[Select course to see profiles]"
        )
    
    # Get course info
    course = db_manager.get_course(course_id)
    course_info = f"📚 {course['code']} - {course['name']}" if course else "Unknown Course"
    
    all_profiles = db_manager.get_all_criteria()
    course_profiles = []
    
    for profile in all_profiles:
        assignment = db_manager.get_assignment(profile['assignment_id'])
        if assignment and assignment['course_id'] == course_id:
            profile_name = assignment['name']
            course_profiles.append({
                'id': profile['id'],
                'name': profile_name,
                'format': profile['output_format'],
                'score': profile['max_score']
            })
    
    if not course_profiles:
        return (
            course_info,
            gr.update(choices=["[No profiles - create one below]"], value=None),
            "No profiles yet for this course"
        )
    
    choices = [f"{p['id']}: {p['name']} [{p['format']}, {p['score']}pts]" for p in course_profiles]
    
    # Build profile list display
    profile_list = []
    for p in course_profiles:
        profile_list.append(f"💾 {p['name']} [{p['format']}, {p['score']}pts] [ID:{p['id']}]")
    
    return (
        course_info,
        gr.update(choices=choices, value=None),
        "\n".join(profile_list)
    )


def parse_profile_id(selection):
    """Extract profile ID from selection"""
    if not selection or "[No profiles" in selection or "[Select" in selection:
        return None
    try:
        return int(selection.split(":")[0])
    except:
        return None


def create_profile(course_selection, name, instructions, criteria, fmt, score, keywords, reqs):
    """Create profile for selected course"""
    db_manager = get_db_manager()
    course_id = parse_course_id(course_selection)
    
    if not course_id:
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Please select a course first", course_info, dropdown, profile_list
    
    if not name.strip():
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Profile Name is required", course_info, dropdown, profile_list
    
    if not instructions.strip():
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Instructions are required", course_info, dropdown, profile_list
    
    if not criteria.strip():
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Rubric is required", course_info, dropdown, profile_list
    
    assignment_id = db_manager.create_assignment(course_id, name, "", instructions)
    if assignment_id == -1:
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Failed to create", course_info, dropdown, profile_list
    
    criteria_id = db_manager.create_criteria(
        assignment_id, criteria, fmt, int(score) if score else 100, keywords, reqs
    )
    
    if criteria_id == -1:
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Failed to save criteria", course_info, dropdown, profile_list
    
    course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
    return f"✅ Created profile: {name}", course_info, dropdown, profile_list


def load_profile_to_criteria(profile_selection):
    """Load selected profile into criteria form"""
    db_manager = get_db_manager()
    profile_id = parse_profile_id(profile_selection)
    
    if not profile_id:
        return "", "", "Select a profile", "letter", 100, "", ""
    
    criteria = db_manager.get_grading_criteria(profile_id)
    if not criteria:
        return "", "", "Profile not found", "letter", 100, "", ""
    
    assignment = db_manager.get_assignment(criteria['assignment_id'])
    if not assignment:
        return "", "", "Assignment not found", "letter", 100, "", ""
    
    return (
        assignment['instructions'],
        criteria.get('rubric', ''),
        f"✅ Loaded: {assignment['name']}",
        criteria['output_format'],
        criteria['max_score'],
        criteria['ai_keywords'] or "",
        criteria['additional_requirements'] or ""
    )


def update_profile_action(profile_selection, name, instructions, criteria, fmt, score, keywords, reqs, course_selection):
    """Update selected profile"""
    db_manager = get_db_manager()
    profile_id = parse_profile_id(profile_selection)
    
    if not profile_id:
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Select profile first", course_info, dropdown, profile_list, "", "", "letter", 100, "", ""
    
    if not name.strip() or not instructions.strip() or not criteria.strip():
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Required fields missing", course_info, dropdown, profile_list, instructions, criteria, fmt, score, keywords, reqs
    
    crit = db_manager.get_grading_criteria(profile_id)
    if not crit:
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Profile not found", course_info, dropdown, profile_list, "", "", "letter", 100, "", ""
    
    # Update assignment name and instructions
    course_id = parse_course_id(course_selection)
    db_manager.update_assignment(crit['assignment_id'], name=name, instructions=instructions, course_id=course_id)
    
    # Update criteria
    db_manager.update_criteria(
        profile_id, criteria, fmt, int(score) if score else 100, keywords, reqs
    )
    
    # Reload the updated profile data to return fresh values
    updated_crit = db_manager.get_grading_criteria(profile_id)
    updated_assignment = db_manager.get_assignment(updated_crit['assignment_id'])
    
    course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
    
    # Return 10 values: status, course_info, dropdown, profile_list, + 6 form fields
    return (
        f"✅ Updated profile: {name}",
        course_info,
        dropdown,
        profile_list,
        updated_assignment['instructions'],
        updated_crit.get('rubric', ''),
        updated_crit.get('output_format', 'letter'),
        updated_crit.get('max_score', 100),
        updated_crit.get('ai_keywords', ''),
        updated_crit.get('additional_requirements', '')
    )


def delete_profile_action(profile_selection, course_selection):
    """Delete selected profile"""
    db_manager = get_db_manager()
    profile_id = parse_profile_id(profile_selection)
    
    if not profile_id:
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "❌ Select profile first", course_info, dropdown, profile_list
    
    # Delete the specific criteria (and its assignment) by criteria ID
    if db_manager.delete_criteria(profile_id):
        course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
        return "✅ Profile deleted", course_info, dropdown, profile_list
    
    course_info, dropdown, profile_list = load_profiles_for_course(course_selection)
    return "❌ Delete failed", course_info, dropdown, profile_list


def load_profile_into_fields(profile_selection):
    """
    Auto-load profile details into grading fields when profile is selected.
    
    Returns: (instructions, rubric, output_format, max_score, ai_keywords, additional_requirements, status)
    """
    db_manager = get_db_manager()
    
    profile_id = parse_profile_id(profile_selection)
    
    if not profile_id:
        return "", "", "letter", 100, "", "", "ℹ️ Select a profile to load"
    
    criteria = db_manager.get_grading_criteria(profile_id)
    
    if not criteria:
        return "", "", "letter", 100, "", "", "❌ Profile not found"
    
    assignment = db_manager.get_assignment(criteria['assignment_id'])
    
    if not assignment:
        return "", "", "letter", 100, "", "", "❌ Assignment not found"
    
    # Extract values
    instructions_value = assignment.get('instructions', '')
    rubric_value = criteria.get('rubric', '')
    format_value = criteria.get('output_format', 'letter')
    score_value = criteria.get('max_score', 100)
    keywords_value = criteria.get('ai_keywords', '') or ''
    reqs_value = criteria.get('additional_requirements', '') or ''
    
    return (
        instructions_value,
        rubric_value,
        format_value,
        score_value,
        keywords_value,
        reqs_value,
        f"✅ Loaded: {assignment['name']}"
    )

