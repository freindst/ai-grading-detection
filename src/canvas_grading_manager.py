"""
Canvas Grading Manager - Orchestrates Canvas + LLM grading workflow
"""

from typing import Dict, List, Optional, Callable
import json
import logging
from pathlib import Path

# Setup logging for Canvas grading errors
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "canvas_errors.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

# Only add handler if not already added
if not logger.handlers:
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


class CanvasGradingManager:
    """
    Orchestrates the Canvas grading workflow:
    1. Download submissions from Canvas
    2. Grade each with LLM engine
    3. Store both raw JSON and parsed results
    4. Track progress and handle errors
    """
    
    def __init__(self, canvas_client, grading_engine, db_manager, document_parser):
        """
        Initialize Canvas grading manager
        
        Args:
            canvas_client: CanvasClient instance
            grading_engine: GradingEngine instance
            db_manager: DatabaseManager instance
            document_parser: DocumentParser instance (for file submissions)
        """
        self.canvas_client = canvas_client
        self.grading_engine = grading_engine
        self.db_manager = db_manager
        self.document_parser = document_parser
    
    def download_and_grade_assignment(
        self,
        course_id: int,
        course_name: str,
        assignment_id: int,
        assignment_name: str,
        assignment_instructions: str,
        grading_criteria: str,
        output_format: str = "numeric",
        max_score: int = 100,
        ai_keywords: str = "",
        additional_requirements: str = "",
        model: str = "qwen2.5-coder",
        temperature: float = 0.3,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Download all submissions and grade them with LLM
        
        Args:
            course_id: Canvas course ID
            course_name: Course name
            assignment_id: Canvas assignment ID
            assignment_name: Assignment name
            assignment_instructions: Instructions for the assignment
            grading_criteria: Grading rubric
            output_format: 'numeric' or 'letter'
            max_score: Maximum score
            ai_keywords: Keywords to detect AI usage
            additional_requirements: Extra grading requirements
            model: LLM model to use
            temperature: LLM temperature
            progress_callback: Function to call with progress updates
            
        Returns:
            Dictionary with session info and results
        """
        # Step 1: Download submissions from Canvas
        if progress_callback:
            progress_callback(0, 100, "Downloading submissions from Canvas...")
        
        success, submissions = self.canvas_client.get_submissions(course_id, assignment_id)
        
        if not success:
            return {
                "success": False,
                "error": f"Failed to download submissions: {submissions}",
                "session_id": None
            }
        
        if not submissions:
            return {
                "success": False,
                "error": "No submissions found for this assignment",
                "session_id": None
            }
        
        total_submissions = len(submissions)
        
        # Step 2: Create grading session in database
        session_id = self.db_manager.create_grading_session(
            canvas_assignment_id=assignment_id,
            canvas_course_id=course_id,
            course_name=course_name,
            assignment_name=assignment_name,
            total_submissions=total_submissions,
            assignment_instructions=assignment_instructions,
            grading_criteria=grading_criteria,
            output_format=output_format,
            max_score=max_score
        )
        
        # Step 3: Grade each submission
        # Set the model on the LLM client before grading
        if model:
            try:
                self.grading_engine.llm_client.set_model(model)
            except Exception as e:
                # If model setting fails, continue with current model
                pass
        
        graded_count = 0
        error_count = 0
        errors = []
        
        for i, submission in enumerate(submissions):
            if progress_callback:
                progress_callback(
                    i + 1,
                    total_submissions,
                    f"Grading {i + 1}/{total_submissions}: {submission['student_name']}"
                )
            
            submission_text = ""  # Initialize before try block
            try:
                # Extract submission text
                submission_text = self.canvas_client.get_submission_text(submission)
                
                # Handle file submissions (if attachments exist)
                if submission.get("attachments"):
                    # Create download directory for this assignment
                    download_dir = Path(f"data/canvas_submissions/{course_id}/{assignment_id}")
                    download_dir.mkdir(parents=True, exist_ok=True)
                    
                    attachment_texts = []
                    attachment_names = []
                    failed_files = []
                    
                    for attachment in submission["attachments"]:
                        filename = attachment.get("filename", "unknown")
                        attachment_names.append(filename)
                        
                        # Download the file
                        success, result = self.canvas_client.download_attachment(
                            attachment,
                            str(download_dir)
                        )
                        
                        if success:
                            # Parse the downloaded file
                            file_path = result
                            parse_result = self.document_parser.parse_file(file_path)
                            
                            if parse_result.get("success"):
                                text = parse_result.get("text", "")
                                if text.strip():
                                    attachment_texts.append(f"\n\n--- Content from {filename} ---\n{text}")
                                else:
                                    failed_files.append(f"{filename} (empty)")
                                    logger.error(
                                        "File parsing returned empty (session %s, file %s)",
                                        session_id,
                                        filename
                                    )
                            else:
                                error_msg = parse_result.get("error", "Unknown parse error")
                                failed_files.append(f"{filename} ({error_msg})")
                                logger.error(
                                    "File parsing failed (session %s, file %s): %s",
                                    session_id,
                                    filename,
                                    error_msg
                                )
                        else:
                            failed_files.append(f"{filename} (download failed: {result})")
                            logger.error(
                                "File download failed (session %s, file %s): %s",
                                session_id,
                                filename,
                                result
                            )
                    
                    # Combine all parsed text
                    if attachment_texts:
                        submission_text += "\n\n=== ATTACHED FILES ===" + "".join(attachment_texts)
                    
                    # Add metadata about files
                    submission_text += f"\n\n[Submitted files: {', '.join(attachment_names)}]"
                    
                    if failed_files:
                        submission_text += f"\n[Failed to parse: {', '.join(failed_files)}]"
                
                # Grade with LLM
                result = self.grading_engine.grade_submission(
                    submission_text=submission_text,
                    assignment_instruction=assignment_instructions,
                    grading_criteria=grading_criteria,
                    output_format=output_format,
                    max_score=max_score,
                    ai_keywords=ai_keywords,
                    additional_requirements=additional_requirements,
                    temperature=temperature,
                    keep_context=False  # Each submission is independent
                )
                
                # Clear context after each submission
                self.grading_engine.llm_client.clear_context()
                
                if not result.get("success", False):
                    error_message = result.get("error", "Unknown grading failure")
                    logger.error(
                        "Grading failed (session %s, submission %s - %s): %s",
                        session_id,
                        submission.get("id"),
                        submission.get("student_name"),
                        error_message
                    )
                    raise RuntimeError(error_message)
                
                # Extract parsed values from parsed_result
                parsed = result.get("parsed_result", {})
                grade = parsed.get("grade", "ERROR")
                detailed_feedback = parsed.get("detailed_feedback", "Error parsing feedback")
                student_feedback = parsed.get("student_feedback", "Error parsing feedback")
                raw_output = result.get("raw_llm_output", "")
                
                # Store in database with BOTH raw JSON and parsed results
                self.db_manager.save_submission_grade(
                    session_id=session_id,
                    canvas_submission_id=submission["id"],
                    student_id=submission["user_id"],
                    student_name=submission["student_name"],
                    submission_text=submission_text,
                    raw_llm_json=raw_output,  # Store complete raw output for review
                    parsed_grade=grade,
                    parsed_detailed_feedback=detailed_feedback,
                    parsed_student_feedback=student_feedback,
                    submission_url=submission.get("url", "")
                )
                
                graded_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = f"{submission['student_name']}: {str(e)[:100]}"
                errors.append(error_msg)
                logger.error(
                    "Error grading submission (session %s, submission %s - %s): %s",
                    session_id,
                    submission.get("id"),
                    submission.get("student_name"),
                    str(e),
                    exc_info=True  # Log full traceback
                )
                
                # Store error in database too
                self.db_manager.save_submission_grade(
                    session_id=session_id,
                    canvas_submission_id=submission["id"],
                    student_id=submission["user_id"],
                    student_name=submission["student_name"],
                    submission_text=submission_text or "Error extracting text",
                    raw_llm_json=f"ERROR: {str(e)}",
                    parsed_grade="ERROR",
                    parsed_detailed_feedback=f"Grading failed: {str(e)}",
                    parsed_student_feedback="Error during grading",
                    submission_url=submission.get("url", "")
                )
        
        # Step 4: Update session status
        status = "completed" if error_count == 0 else "completed_with_errors"
        self.db_manager.update_session_status(session_id, status, completed=True)
        
        if progress_callback:
            progress_callback(
                total_submissions,
                total_submissions,
                f"✅ Complete: {graded_count} graded, {error_count} errors"
            )
        
        return {
            "success": True,
            "session_id": session_id,
            "total_submissions": total_submissions,
            "graded_count": graded_count,
            "error_count": error_count,
            "errors": errors
        }
    
    def upload_grades_to_canvas(
        self,
        session_id: int,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Upload all reviewed grades from a session to Canvas
        
        Args:
            session_id: Grading session ID
            progress_callback: Function to call with progress updates
            
        Returns:
            Dictionary with upload results
        """
        # Get session info
        session = self.db_manager.get_grading_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        course_id = session["canvas_course_id"]
        assignment_id = session["canvas_assignment_id"]
        
        # Get all grades ready to upload (reviewed and not yet uploaded)
        grades_to_upload = self.db_manager.get_unuploaded_grades(session_id)
        
        if not grades_to_upload:
            return {
                "success": False,
                "error": "No grades ready to upload (all must be reviewed first)"
            }
        
        total_grades = len(grades_to_upload)
        uploaded_count = 0
        failed_count = 0
        errors = []
        
        if progress_callback:
            progress_callback(0, total_grades, "Starting grade upload...")
        
        # Upload each grade
        for i, grade_info in enumerate(grades_to_upload):
            if progress_callback:
                progress_callback(
                    i + 1,
                    total_grades,
                    f"Uploading {i + 1}/{total_grades}: {grade_info['student_name']}"
                )
            
            try:
                success, message = self.canvas_client.upload_grade(
                    course_id=course_id,
                    assignment_id=assignment_id,
                    user_id=grade_info["student_id"],
                    grade=grade_info["final_grade"],
                    comment=grade_info["final_comments"]
                )
                
                if success:
                    # Mark as uploaded in database
                    self.db_manager.mark_grade_uploaded(grade_info["id"], success=True)
                    uploaded_count += 1
                else:
                    # Mark as failed
                    self.db_manager.mark_grade_uploaded(grade_info["id"], success=False)
                    failed_count += 1
                    errors.append(f"{grade_info['student_name']}: {message}")
            
            except Exception as e:
                failed_count += 1
                error_msg = f"{grade_info['student_name']}: {str(e)[:100]}"
                errors.append(error_msg)
                self.db_manager.mark_grade_uploaded(grade_info["id"], success=False)
        
        if progress_callback:
            progress_callback(
                total_grades,
                total_grades,
                f"✅ Upload complete: {uploaded_count} uploaded, {failed_count} failed"
            )
        
        return {
            "success": failed_count == 0,
            "uploaded_count": uploaded_count,
            "failed_count": failed_count,
            "errors": errors
        }
    
    def upload_single_grade(
        self,
        session_id: int,
        grade_id: int
    ) -> Dict:
        """
        Upload a single grade to Canvas
        
        Args:
            session_id: Grading session ID
            grade_id: Submission grade ID
            
        Returns:
            Dictionary with result
        """
        # Get session info
        session = self.db_manager.get_grading_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        # Get grade info
        grades = self.db_manager.get_session_grades(session_id)
        grade_info = next((g for g in grades if g["id"] == grade_id), None)
        
        if not grade_info:
            return {"success": False, "error": "Grade not found"}
        
        if grade_info["needs_review"]:
            return {"success": False, "error": "Grade must be reviewed before uploading"}
        
        # Upload to Canvas
        try:
            success, message = self.canvas_client.upload_grade(
                course_id=session["canvas_course_id"],
                assignment_id=session["canvas_assignment_id"],
                user_id=grade_info["student_id"],
                grade=grade_info["final_grade"],
                comment=grade_info["final_comments"]
            )
            
            if success:
                self.db_manager.mark_grade_uploaded(grade_id, success=True)
                return {"success": True, "message": message}
            else:
                self.db_manager.mark_grade_uploaded(grade_id, success=False)
                return {"success": False, "error": message}
        
        except Exception as e:
            self.db_manager.mark_grade_uploaded(grade_id, success=False)
            return {"success": False, "error": str(e)}

