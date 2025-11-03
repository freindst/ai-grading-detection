"""
Profile Manager - Manage courses, assignments, and grading profiles
"""

from typing import Dict, List, Optional, Tuple
from src.database import DatabaseManager


class ProfileManager:
    """Manage grading profiles, courses, and assignments"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    # Course management
    def create_course_profile(self, name: str, code: str, description: str = "") -> Tuple[bool, str, int]:
        """
        Create a new course profile
        
        Returns:
            Tuple of (success, message, course_id)
        """
        course_id = self.db.create_course(name, code, description)
        
        if course_id == -1:
            return False, f"Course with code '{code}' already exists", -1
        
        return True, f"Course '{name}' created successfully", course_id
    
    def get_course_list(self) -> List[Dict]:
        """Get list of all courses"""
        return self.db.get_all_courses()
    
    def get_course_details(self, course_id: int) -> Optional[Dict]:
        """Get detailed information for a course"""
        course = self.db.get_course(course_id)
        if not course:
            return None
        
        # Get assignments for this course
        assignments = self.db.get_assignments_by_course(course_id)
        course['assignments'] = assignments
        course['assignment_count'] = len(assignments)
        
        return course
    
    def update_course_profile(
        self,
        course_id: int,
        name: str = None,
        description: str = None
    ) -> Tuple[bool, str]:
        """Update course profile"""
        success = self.db.update_course(course_id, name, description)
        
        if success:
            return True, "Course updated successfully"
        return False, "Failed to update course"
    
    def delete_course_profile(self, course_id: int) -> Tuple[bool, str]:
        """Delete course profile"""
        success = self.db.delete_course(course_id)
        
        if success:
            return True, "Course deleted successfully"
        return False, "Failed to delete course"
    
    # Assignment management
    def create_assignment_profile(
        self,
        course_id: int,
        name: str,
        description: str,
        instructions: str,
        rubric: str,
        output_format: str = "letter",
        max_score: int = 100,
        ai_keywords: str = "",
        additional_requirements: str = ""
    ) -> Tuple[bool, str, int]:
        """
        Create a new assignment profile with grading criteria
        
        Returns:
            Tuple of (success, message, assignment_id)
        """
        # Create assignment
        assignment_id = self.db.create_assignment(
            course_id, name, description, instructions
        )
        
        if assignment_id <= 0:
            return False, "Failed to create assignment", -1
        
        # Create grading criteria
        criteria_id = self.db.create_criteria(
            assignment_id, rubric, output_format,
            max_score, ai_keywords, additional_requirements
        )
        
        if criteria_id <= 0:
            # Rollback: delete assignment if criteria creation fails
            self.db.delete_assignment(assignment_id)
            return False, "Failed to create grading criteria", -1
        
        return True, f"Assignment '{name}' created successfully", assignment_id
    
    def get_assignment_profile(self, assignment_id: int) -> Optional[Dict]:
        """Get complete assignment profile including criteria"""
        assignment = self.db.get_assignment(assignment_id)
        if not assignment:
            return None
        
        # Get grading criteria
        criteria = self.db.get_criteria_by_assignment(assignment_id)
        if criteria:
            assignment['criteria'] = criteria
        
        return assignment
    
    def get_assignments_for_course(self, course_id: int) -> List[Dict]:
        """Get all assignments for a course"""
        return self.db.get_assignments_by_course(course_id)
    
    def update_assignment_profile(
        self,
        assignment_id: int,
        name: str = None,
        description: str = None,
        instructions: str = None
    ) -> Tuple[bool, str]:
        """Update assignment profile"""
        success = self.db.update_assignment(assignment_id, name, description, instructions)
        
        if success:
            return True, "Assignment updated successfully"
        return False, "Failed to update assignment"
    
    def delete_assignment_profile(self, assignment_id: int) -> Tuple[bool, str]:
        """Delete assignment profile"""
        success = self.db.delete_assignment(assignment_id)
        
        if success:
            return True, "Assignment deleted successfully"
        return False, "Failed to delete assignment"
    
    def duplicate_assignment_profile(
        self,
        source_assignment_id: int,
        new_name: str,
        course_id: int = None
    ) -> Tuple[bool, str, int]:
        """
        Duplicate an existing assignment profile as a template
        
        Returns:
            Tuple of (success, message, new_assignment_id)
        """
        # Get source assignment
        source = self.get_assignment_profile(source_assignment_id)
        if not source:
            return False, "Source assignment not found", -1
        
        # Use same course if not specified
        if course_id is None:
            course_id = source['course_id']
        
        # Create new assignment
        new_assignment_id = self.db.create_assignment(
            course_id,
            new_name,
            source.get('description', ''),
            source.get('instructions', '')
        )
        
        if new_assignment_id <= 0:
            return False, "Failed to duplicate assignment", -1
        
        # Duplicate criteria if exists
        if 'criteria' in source and source['criteria']:
            criteria = source['criteria']
            self.db.create_criteria(
                new_assignment_id,
                criteria.get('rubric', ''),
                criteria.get('output_format', 'letter'),
                criteria.get('max_score', 100),
                criteria.get('ai_keywords', ''),
                criteria.get('additional_requirements', '')
            )
        
        return True, f"Assignment duplicated as '{new_name}'", new_assignment_id
    
    # Grading history and feedback
    def save_grading(
        self,
        assignment_id: int,
        filename: str,
        submission_text: str,
        grading_result: Dict,
        model_used: str,
        temperature: float
    ) -> int:
        """Save grading result to history"""
        parsed = grading_result.get('parsed_result', {})
        
        history_id = self.db.save_grading_result(
            assignment_id=assignment_id,
            filename=filename,
            submission_text=submission_text,
            grade=parsed.get('grade', 'N/A'),
            detailed_feedback=parsed.get('detailed_feedback', ''),
            student_feedback=parsed.get('student_feedback', ''),
            raw_llm_output=grading_result.get('raw_llm_output', ''),
            model_used=model_used,
            temperature=temperature
        )
        
        return history_id
    
    def add_feedback(
        self,
        history_id: int,
        feedback: str,
        mark_as_good_example: bool = False
    ) -> Tuple[bool, str]:
        """Add human feedback to a grading result"""
        success = self.db.add_human_feedback(history_id, feedback, mark_as_good_example)
        
        if success:
            msg = "Feedback saved"
            if mark_as_good_example:
                msg += " and marked as good example for in-context learning"
            return True, msg
        return False, "Failed to save feedback"
    
    def get_few_shot_examples(self, assignment_id: int, limit: int = 5) -> List[Dict]:
        """Get good examples for few-shot prompting"""
        return self.db.get_good_examples(assignment_id, limit)
    
    # Export and import profiles
    def export_assignment_profile(self, assignment_id: int) -> Optional[Dict]:
        """Export assignment profile as JSON-compatible dict"""
        profile = self.get_assignment_profile(assignment_id)
        if not profile:
            return None
        
        # Remove IDs and timestamps for clean template
        export = {
            'name': profile.get('name'),
            'description': profile.get('description'),
            'instructions': profile.get('instructions'),
            'criteria': {}
        }
        
        if 'criteria' in profile and profile['criteria']:
            criteria = profile['criteria']
            export['criteria'] = {
                'rubric': criteria.get('rubric'),
                'output_format': criteria.get('output_format'),
                'max_score': criteria.get('max_score'),
                'ai_keywords': criteria.get('ai_keywords'),
                'additional_requirements': criteria.get('additional_requirements')
            }
        
        return export
    
    def import_assignment_profile(
        self,
        course_id: int,
        profile_data: Dict
    ) -> Tuple[bool, str, int]:
        """Import assignment profile from dict"""
        try:
            criteria = profile_data.get('criteria', {})
            
            return self.create_assignment_profile(
                course_id=course_id,
                name=profile_data.get('name', 'Imported Assignment'),
                description=profile_data.get('description', ''),
                instructions=profile_data.get('instructions', ''),
                rubric=criteria.get('rubric', ''),
                output_format=criteria.get('output_format', 'letter'),
                max_score=criteria.get('max_score', 100),
                ai_keywords=criteria.get('ai_keywords', ''),
                additional_requirements=criteria.get('additional_requirements', '')
            )
        except Exception as e:
            return False, f"Import failed: {str(e)}", -1

