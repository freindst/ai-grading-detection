"""
Feedback Collector - Collect and manage human feedback for model alignment
"""

from typing import Dict, List, Optional
from src.database import DatabaseManager


class FeedbackCollector:
    """Collect human feedback on grading results for future training"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def collect_feedback(
        self,
        grading_history_id: int,
        feedback_text: str,
        feedback_type: str = "general",
        mark_as_example: bool = False
    ) -> tuple[bool, str]:
        """
        Collect feedback on a grading result
        
        Args:
            grading_history_id: ID of the grading in history
            feedback_text: The human feedback
            feedback_type: Type of feedback ('general', 'format', 'accuracy', 'tone')
            mark_as_example: Whether to mark this as a good example
            
        Returns:
            Tuple of (success, message)
        """
        # Add feedback type to text
        formatted_feedback = f"[{feedback_type.upper()}] {feedback_text}"
        
        success = self.db.add_human_feedback(
            grading_history_id,
            formatted_feedback,
            mark_as_example
        )
        
        if success:
            msg = "Feedback collected successfully"
            if mark_as_example:
                msg += " and marked as good example"
            return True, msg
        
        return False, "Failed to collect feedback"
    
    def get_feedback_dataset(
        self,
        assignment_id: Optional[int] = None,
        only_examples: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get feedback dataset for training
        
        Returns:
            List of grading records with feedback
        """
        if only_examples:
            return self.db.get_good_examples(assignment_id, limit)
        
        # Get all records with feedback
        # This would require an additional DB query
        # For now, return good examples
        return self.db.get_good_examples(assignment_id, limit)
    
    def prepare_training_data(
        self,
        feedback_dataset: List[Dict]
    ) -> List[Dict]:
        """
        Prepare feedback dataset for fine-tuning
        
        Converts grading history to training format:
        {
          "instruction": "Grade this submission...",
          "input": "submission text",
          "output": "grading result"
        }
        
        Returns:
            List of training examples
        """
        training_data = []
        
        for record in feedback_dataset:
            example = {
                "instruction": "Grade the following student submission according to the provided criteria.",
                "input": record.get('submission_text', ''),
                "output": {
                    "grade": record.get('grade', ''),
                    "detailed_feedback": record.get('detailed_feedback', ''),
                    "student_feedback": record.get('student_feedback', '')
                },
                "human_feedback": record.get('human_feedback', ''),
                "model_used": record.get('model_used', ''),
                "temperature": record.get('temperature', 0.7)
            }
            training_data.append(example)
        
        return training_data
    
    def export_feedback_dataset(
        self,
        output_file: str,
        assignment_id: Optional[int] = None,
        format: str = 'jsonl'
    ) -> tuple[bool, str]:
        """
        Export feedback dataset to file
        
        Args:
            output_file: Path to output file
            assignment_id: Optional filter by assignment
            format: 'jsonl' or 'json'
            
        Returns:
            Tuple of (success, message)
        """
        import json
        from pathlib import Path
        
        try:
            dataset = self.get_feedback_dataset(assignment_id, only_examples=True)
            training_data = self.prepare_training_data(dataset)
            
            # Ensure directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'jsonl':
                with open(output_file, 'w', encoding='utf-8') as f:
                    for item in training_data:
                        f.write(json.dumps(item, ensure_ascii=False) + '\n')
            else:  # json
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            return True, f"Exported {len(training_data)} examples to {output_file}"
        
        except Exception as e:
            return False, f"Export failed: {str(e)}"
    
    def get_feedback_statistics(self, assignment_id: Optional[int] = None) -> Dict:
        """Get statistics about collected feedback"""
        examples = self.get_feedback_dataset(assignment_id, only_examples=True)
        all_feedback = self.get_feedback_dataset(assignment_id, only_examples=False)
        
        return {
            "total_feedback": len(all_feedback),
            "marked_as_examples": len(examples),
            "ready_for_training": len(examples) >= 5,  # Minimum for fine-tuning
            "recommended_examples": max(10, len(examples)),
        }

