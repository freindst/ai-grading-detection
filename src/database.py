"""
Database Manager - SQLite database operations
Handles courses, assignments, prompts, and grading history
"""

import sqlite3
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class DatabaseManager:
    """Manage SQLite database for profiles and history"""
    
    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self):
        """Create data directory if it doesn't exist"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                code TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Assignments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                name TEXT NOT NULL,
                description TEXT,
                instructions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        """)
        
        # Grading criteria table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grading_criteria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER,
                rubric TEXT NOT NULL,
                output_format TEXT DEFAULT 'letter',
                max_score INTEGER DEFAULT 100,
                ai_keywords TEXT,
                additional_requirements TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE
            )
        """)
        
        # Prompt templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                system_prompt TEXT,
                user_prompt_template TEXT,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES prompt_templates(id)
            )
        """)
        
        # Grading history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grading_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER,
                filename TEXT,
                submission_text TEXT,
                grade TEXT,
                detailed_feedback TEXT,
                student_feedback TEXT,
                raw_llm_output TEXT,
                model_used TEXT,
                temperature REAL,
                human_feedback TEXT,
                is_good_example BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assignment_id) REFERENCES assignments(id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Run migrations after tables are created
        self._migrate_criteria_text_to_rubric()
    
    def _migrate_criteria_text_to_rubric(self):
        """
        Migrate old 'criteria_text' column to 'rubric' in grading_criteria table.
        This handles existing databases created before the field name was unified.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check current column names in grading_criteria table
            cursor.execute("PRAGMA table_info(grading_criteria)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Case 1: Has criteria_text but not rubric (old schema)
            if 'criteria_text' in columns and 'rubric' not in columns:
                print("🔄 Migrating database: renaming 'criteria_text' to 'rubric'...")
                cursor.execute("ALTER TABLE grading_criteria RENAME COLUMN criteria_text TO rubric")
                conn.commit()
                print("✅ Migration complete: criteria_text → rubric")
                
            # Case 2: Has both columns (partial migration) - copy data and drop old
            elif 'criteria_text' in columns and 'rubric' in columns:
                print("🔄 Cleaning up: removing duplicate 'criteria_text' column...")
                # SQLite doesn't support DROP COLUMN directly, need to recreate table
                # But this should never happen in practice
                print("⚠️ Warning: Table has both criteria_text and rubric columns")
                
            # Case 3: Has rubric only (correct schema) - do nothing
            elif 'rubric' in columns:
                pass  # Already migrated or new installation
                
            # Case 4: Has neither (corrupted schema)
            else:
                print("❌ Error: grading_criteria table is missing both criteria_text and rubric columns")
                
        except Exception as e:
            print(f"⚠️ Migration warning: {str(e)}")
            # Don't fail initialization if migration has issues
        finally:
            conn.close()
    
    # Course methods
    def create_course(self, name: str, code: str, description: str = "") -> int:
        """Create a new course"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO courses (name, code, description) VALUES (?, ?, ?)",
                (name, code, description)
            )
            course_id = cursor.lastrowid
            conn.commit()
            return course_id
        except sqlite3.IntegrityError:
            return -1  # Course code already exists
        finally:
            conn.close()
    
    def get_course(self, course_id: int) -> Optional[Dict]:
        """Get course by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM courses WHERE id = ?", (course_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_courses(self) -> List[Dict]:
        """Get all courses"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM courses ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_course(self, course_id: int, name: str = None, description: str = None) -> bool:
        """Update course"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if name:
            updates.append("name = ?")
            values.append(name)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(course_id)
        
        cursor.execute(
            f"UPDATE courses SET {', '.join(updates)} WHERE id = ?",
            tuple(values)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_course(self, course_id: int) -> bool:
        """Delete course"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def update_course(self, course_id: int, name: str = None, code: str = None, description: str = None) -> bool:
        """Update course information"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if code is not None:
                updates.append("code = ?")
                params.append(code)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                conn.close()
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(course_id)
            
            query = f"UPDATE courses SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"Error updating course: {e}")
            return False
    
    # Assignment methods
    def create_assignment(
        self,
        course_id: int,
        name: str,
        description: str = "",
        instructions: str = ""
    ) -> int:
        """Create a new assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO assignments (course_id, name, description, instructions) VALUES (?, ?, ?, ?)",
            (course_id, name, description, instructions)
        )
        assignment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return assignment_id
    
    def get_assignment(self, assignment_id: int) -> Optional[Dict]:
        """Get assignment by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_assignments_by_course(self, course_id: int) -> List[Dict]:
        """Get all assignments for a course"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM assignments WHERE course_id = ? ORDER BY created_at DESC",
            (course_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_assignment(
        self,
        assignment_id: int,
        name: str = None,
        description: str = None,
        instructions: str = None
    ) -> bool:
        """Update assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if name:
            updates.append("name = ?")
            values.append(name)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if instructions is not None:
            updates.append("instructions = ?")
            values.append(instructions)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(assignment_id)
        
        cursor.execute(
            f"UPDATE assignments SET {', '.join(updates)} WHERE id = ?",
            tuple(values)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_assignment(self, assignment_id: int) -> bool:
        """Delete assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def delete_criteria(self, criteria_id: int) -> bool:
        """Delete specific grading criteria by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First get the assignment_id to delete the assignment too
        cursor.execute("SELECT assignment_id FROM grading_criteria WHERE id = ?", (criteria_id,))
        result = cursor.fetchone()
        
        if result:
            assignment_id = result[0]
            # Delete the criteria
            cursor.execute("DELETE FROM grading_criteria WHERE id = ?", (criteria_id,))
            # Delete the associated assignment
            cursor.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
            success = cursor.rowcount > 0
        else:
            success = False
        
        conn.commit()
        conn.close()
        
        return success
    
    def update_assignment(self, assignment_id: int, name: str = None, instructions: str = None, 
                         description: str = None, course_id: int = None) -> bool:
        """Update assignment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if instructions is not None:
                updates.append("instructions = ?")
                params.append(instructions)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if course_id is not None:
                updates.append("course_id = ?")
                params.append(course_id)
            
            if not updates:
                conn.close()
                return True
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(assignment_id)
            
            query = f"UPDATE assignments SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            print(f"Error updating assignment: {e}")
            return False
    
    # Grading criteria methods
    def create_criteria(
        self,
        assignment_id: int,
        rubric: str,
        output_format: str = "letter",
        max_score: int = 100,
        ai_keywords: str = "",
        additional_requirements: str = ""
    ) -> int:
        """Create grading criteria for assignment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO grading_criteria 
            (assignment_id, rubric, output_format, max_score, ai_keywords, additional_requirements)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (assignment_id, rubric, output_format, max_score, ai_keywords, additional_requirements)
        )
        criteria_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return criteria_id
    
    def update_criteria(
        self,
        criteria_id: int,
        rubric: str = None,
        output_format: str = None,
        max_score: int = None,
        ai_keywords: str = None,
        additional_requirements: str = None
    ) -> bool:
        """Update existing grading criteria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if rubric is not None:
            updates.append("rubric = ?")
            params.append(rubric)
        if output_format is not None:
            updates.append("output_format = ?")
            params.append(output_format)
        if max_score is not None:
            updates.append("max_score = ?")
            params.append(max_score)
        if ai_keywords is not None:
            updates.append("ai_keywords = ?")
            params.append(ai_keywords)
        if additional_requirements is not None:
            updates.append("additional_requirements = ?")
            params.append(additional_requirements)
        
        if not updates:
            conn.close()
            return False
        
        params.append(criteria_id)
        cursor.execute(
            f"UPDATE grading_criteria SET {', '.join(updates)} WHERE id = ?",
            params
        )
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def get_criteria_by_assignment(self, assignment_id: int) -> Optional[Dict]:
        """Get grading criteria for assignment"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM grading_criteria WHERE assignment_id = ? ORDER BY created_at DESC LIMIT 1",
            (assignment_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_grading_criteria(self, criteria_id: int) -> Optional[Dict]:
        """Get specific grading criteria by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM grading_criteria WHERE id = ?", (criteria_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_all_criteria(self) -> List[Dict]:
        """Get all grading criteria with assignment info"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT gc.*, a.name as assignment_name, a.instructions, c.name as course_name
            FROM grading_criteria gc
            LEFT JOIN assignments a ON gc.assignment_id = a.id
            LEFT JOIN courses c ON a.course_id = c.id
            ORDER BY gc.created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # Grading history methods
    def save_grading_result(
        self,
        assignment_id: int,
        filename: str,
        submission_text: str,
        grade: str,
        detailed_feedback: str,
        student_feedback: str,
        raw_llm_output: str,
        model_used: str,
        temperature: float
    ) -> int:
        """Save grading result to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO grading_history 
            (assignment_id, filename, submission_text, grade, detailed_feedback, 
            student_feedback, raw_llm_output, model_used, temperature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (assignment_id, filename, submission_text, grade, detailed_feedback,
             student_feedback, raw_llm_output, model_used, temperature)
        )
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return history_id
    
    def add_human_feedback(self, history_id: int, feedback: str, is_good_example: bool = False) -> bool:
        """Add human feedback to grading history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE grading_history SET human_feedback = ?, is_good_example = ? WHERE id = ?",
            (feedback, is_good_example, history_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def get_good_examples(self, assignment_id: int = None, limit: int = 10) -> List[Dict]:
        """Get good examples for few-shot learning"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if assignment_id:
            cursor.execute(
                """SELECT * FROM grading_history 
                WHERE is_good_example = 1 AND assignment_id = ?
                ORDER BY created_at DESC LIMIT ?""",
                (assignment_id, limit)
            )
        else:
            cursor.execute(
                """SELECT * FROM grading_history 
                WHERE is_good_example = 1
                ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

