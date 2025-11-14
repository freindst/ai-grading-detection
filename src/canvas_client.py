"""
Canvas LMS API Client - Handles all Canvas API interactions
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
import os


# Default Canvas URL (hardcoded for user's institution)
DEFAULT_CANVAS_URL = "https://cuwaa.instructure.com/"


class CanvasClient:
    """
    Canvas LMS API client for authentication, course management,
    and grade operations
    """
    
    def __init__(self, canvas_url: str = DEFAULT_CANVAS_URL, access_token: str = None):
        """
        Initialize Canvas client
        
        Args:
            canvas_url: Canvas instance URL (e.g., https://cuwaa.instructure.com)
            access_token: Canvas API access token
        """
        self.canvas_url = canvas_url
        self.access_token = access_token
        self.headers = {}
        self.rate_limit_remaining = 600  # Canvas default: 600 req/hour
        self.rate_limit_reset = None
        
        if access_token:
            self.headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
    
    def set_credentials(self, canvas_url: str, access_token: str):
        """
        Set or update Canvas credentials
        
        Args:
            canvas_url: Canvas instance URL
            access_token: Canvas API access token
        """
        self.canvas_url = canvas_url.rstrip('/')
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Tuple[bool, any]:
        """
        Make API request with error handling and rate limiting
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
            
        Returns:
            Tuple of (success: bool, result: dict or error message)
        """
        if not self.canvas_url or not self.access_token:
            return False, "Canvas credentials not set"
        
        url = f"{self.canvas_url}/api/v1/{endpoint.lstrip('/')}"
        
        try:
            # Check rate limit
            if self.rate_limit_remaining < 10:
                return False, f"Rate limit nearly exceeded ({self.rate_limit_remaining} remaining)"
            
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=data,
                timeout=30
            )
            
            # Update rate limit info from headers
            remaining = response.headers.get('X-Rate-Limit-Remaining')
            if remaining is not None:
                try:
                    self.rate_limit_remaining = int(float(remaining))
                except (ValueError, TypeError):
                    # If parsing fails, use a safe default
                    self.rate_limit_remaining = 600
            
            # Handle response
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 201:
                return True, response.json()
            elif response.status_code == 204:
                return True, {"message": "Success (no content)"}
            elif response.status_code == 401:
                return False, "Authentication failed - check access token"
            elif response.status_code == 403:
                return False, "Permission denied"
            elif response.status_code == 404:
                return False, "Resource not found"
            elif response.status_code == 429:
                return False, "Rate limit exceeded"
            else:
                return False, f"Error {response.status_code}: {response.text[:200]}"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error - check Canvas URL"
        except Exception as e:
            return False, f"Request error: {str(e)[:200]}"
    
    def verify_connection(self) -> Tuple[bool, str, Optional[Dict]]:
        """
        Verify Canvas connection and get user info
        
        Returns:
            Tuple of (success: bool, message: str, user_info: dict)
        """
        success, result = self._make_request("GET", "/users/self")
        
        if success:
            user_info = {
                "id": result.get("id"),
                "name": result.get("name"),
                "email": result.get("email", result.get("login_id", "N/A"))
            }
            return True, f"✅ Connected as {user_info['name']}", user_info
        else:
            return False, f"❌ Connection failed: {result}", None
    
    def get_courses(self) -> Tuple[bool, any]:
        """
        Get list of courses for the authenticated user
        
        Returns:
            Tuple of (success: bool, courses: list or error message)
        """
        # Get only active courses where user is teacher
        params = {
            "enrollment_state": "active",
            "enrollment_type": "teacher",
            "per_page": 100
        }
        
        success, result = self._make_request("GET", "/courses", params=params)
        
        if success:
            # Filter and format courses
            courses = []
            for course in result:
                if not course.get("access_restricted_by_date"):
                    courses.append({
                        "id": course.get("id"),
                        "name": course.get("name"),
                        "course_code": course.get("course_code"),
                        "enrollment_term": course.get("enrollment_term_id")
                    })
            return True, courses
        else:
            return False, result
    
    def get_assignments(self, course_id: int) -> Tuple[bool, any]:
        """
        Get list of assignments for a course
        
        Args:
            course_id: Canvas course ID
            
        Returns:
            Tuple of (success: bool, assignments: list or error message)
        """
        params = {"per_page": 100}
        
        success, result = self._make_request("GET", f"/courses/{course_id}/assignments", params=params)
        
        if success:
            # Format assignments
            assignments = []
            for assignment in result:
                assignments.append({
                    "id": assignment.get("id"),
                    "name": assignment.get("name"),
                    "due_at": assignment.get("due_at"),
                    "points_possible": assignment.get("points_possible", 100),
                    "description": assignment.get("description", ""),
                    "submission_types": assignment.get("submission_types", [])
                })
            return True, assignments
        else:
            return False, result
    
    def get_submissions(self, course_id: int, assignment_id: int) -> Tuple[bool, any]:
        """
        Get all submissions for an assignment
        
        Args:
            course_id: Canvas course ID
            assignment_id: Canvas assignment ID
            
        Returns:
            Tuple of (success: bool, submissions: list or error message)
        """
        params = {
            "include[]": ["user", "submission_comments"],
            "per_page": 100
        }
        
        success, result = self._make_request(
            "GET",
            f"/courses/{course_id}/assignments/{assignment_id}/submissions",
            params=params
        )
        
        if success:
            # Format submissions
            submissions = []
            for submission in result:
                # Skip submissions with no attempt
                if submission.get("workflow_state") == "unsubmitted":
                    continue
                
                user = submission.get("user", {})
                submissions.append({
                    "id": submission.get("id"),
                    "user_id": submission.get("user_id"),
                    "student_name": user.get("name", "Unknown"),
                    "submitted_at": submission.get("submitted_at"),
                    "score": submission.get("score"),
                    "grade": submission.get("grade"),
                    "submission_type": submission.get("submission_type"),
                    "body": submission.get("body", ""),  # Text submission
                    "url": submission.get("url", ""),  # URL submission
                    "attachments": submission.get("attachments", [])  # File submissions
                })
            return True, submissions
        else:
            return False, result
    
    def get_submission_text(self, submission: Dict) -> str:
        """
        Extract text from a submission based on its type
        
        Args:
            submission: Submission dictionary from get_submissions
            
        Returns:
            Submission text content
        """
        submission_type = submission.get("submission_type", "")
        
        if submission_type == "online_text_entry":
            # HTML content - strip tags for plain text
            body = submission.get("body", "")
            # Simple tag removal (for better parsing, could use BeautifulSoup)
            import re
            text = re.sub(r'<[^>]+>', '', body)
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        
        elif submission_type == "online_url":
            return f"URL Submission: {submission.get('url', 'N/A')}"
        
        elif submission_type == "online_upload":
            attachments = submission.get("attachments", [])
            if attachments:
                filenames = [att.get("filename", "unknown") for att in attachments]
                return f"File Upload: {', '.join(filenames)}"
            return "File upload (no files listed)"
        
        else:
            return f"Submission type: {submission_type} (no text content)"
    
    def download_attachment(
        self,
        attachment: Dict,
        save_dir: str
    ) -> Tuple[bool, str]:
        """
        Download a Canvas file attachment to local storage
        
        Args:
            attachment: Attachment dictionary from submission
            save_dir: Directory to save the file
            
        Returns:
            Tuple of (success: bool, file_path or error_message: str)
        """
        from pathlib import Path
        
        try:
            # Get attachment URL and filename
            url = attachment.get("url")
            filename = attachment.get("filename", "unknown_file")
            
            if not url:
                return False, "Attachment URL not found"
            
            # Create save directory
            save_path = Path(save_dir)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = save_path / filename
            
            # Download file with authentication
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                # Save file
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return True, str(file_path)
            else:
                return False, f"Download failed: HTTP {response.status_code}"
        
        except requests.exceptions.Timeout:
            return False, "Download timeout (file too large or network issue)"
        except Exception as e:
            return False, f"Download error: {str(e)}"
    
    def upload_grade(
        self,
        course_id: int,
        assignment_id: int,
        user_id: int,
        grade: str,
        comment: str = None
    ) -> Tuple[bool, str]:
        """
        Upload a grade for a student submission
        
        Args:
            course_id: Canvas course ID
            assignment_id: Canvas assignment ID
            user_id: Student user ID
            grade: Grade to assign
            comment: Optional comment to post
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        data = {
            "submission": {
                "posted_grade": grade
            }
        }
        
        # Add comment if provided
        if comment:
            data["comment"] = {
                "text_comment": comment
            }
        
        success, result = self._make_request(
            "PUT",
            f"/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}",
            data=data
        )
        
        if success:
            return True, f"✅ Grade uploaded successfully"
        else:
            return False, f"❌ Upload failed: {result}"
    
    def upload_grades_batch(
        self,
        course_id: int,
        assignment_id: int,
        grades: List[Dict]
    ) -> Tuple[int, int, List[str]]:
        """
        Upload multiple grades at once
        
        Args:
            course_id: Canvas course ID
            assignment_id: Canvas assignment ID
            grades: List of dicts with keys: user_id, grade, comment
            
        Returns:
            Tuple of (success_count: int, fail_count: int, errors: list)
        """
        success_count = 0
        fail_count = 0
        errors = []
        
        for grade_info in grades:
            user_id = grade_info.get("user_id")
            grade = grade_info.get("grade")
            comment = grade_info.get("comment", "")
            
            success, message = self.upload_grade(
                course_id, assignment_id, user_id, grade, comment
            )
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                errors.append(f"User {user_id}: {message}")
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        return success_count, fail_count, errors


# Token encryption utilities
class TokenEncryption:
    """Handle secure token encryption/decryption"""
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key"""
        return Fernet.generate_key()
    
    @staticmethod
    def get_or_create_key() -> bytes:
        """
        Get existing encryption key or create new one
        Stores in data/.canvas_key file
        """
        key_path = "data/.canvas_key"
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        else:
            # Create new key
            key = TokenEncryption.generate_key()
            os.makedirs("data", exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(key)
            return key
    
    @staticmethod
    def encrypt_token(token: str) -> str:
        """
        Encrypt Canvas access token
        
        Args:
            token: Plain text token
            
        Returns:
            Encrypted token (base64 string)
        """
        key = TokenEncryption.get_or_create_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(token.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """
        Decrypt Canvas access token
        
        Args:
            encrypted_token: Encrypted token (base64 string)
            
        Returns:
            Plain text token
        """
        key = TokenEncryption.get_or_create_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()

