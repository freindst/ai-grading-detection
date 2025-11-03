"""
Few-Shot Manager - Manage examples for in-context learning
"""

from typing import Dict, List, Optional
from src.database import DatabaseManager


class FewShotManager:
    """Manage few-shot examples for in-context learning"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_examples_for_prompt(
        self,
        assignment_id: Optional[int] = None,
        num_examples: int = 3,
        example_type: str = "best"
    ) -> List[Dict]:
        """
        Get examples to include in prompt
        
        Args:
            assignment_id: Filter by assignment
            num_examples: Number of examples to include
            example_type: 'best' (high quality), 'diverse' (varied grades), 'recent'
            
        Returns:
            List of example dicts
        """
        examples = self.db.get_good_examples(assignment_id, limit=num_examples * 2)
        
        if not examples:
            return []
        
        if example_type == "best":
            # Return top examples
            return examples[:num_examples]
        
        elif example_type == "diverse":
            # Try to get diverse grade distribution
            diverse_examples = []
            seen_grades = set()
            
            for ex in examples:
                grade = ex.get('grade', 'N/A')
                if grade not in seen_grades or len(diverse_examples) < num_examples:
                    diverse_examples.append(ex)
                    seen_grades.add(grade)
                
                if len(diverse_examples) >= num_examples:
                    break
            
            return diverse_examples
        
        elif example_type == "recent":
            # Sort by most recent
            return sorted(
                examples,
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )[:num_examples]
        
        return examples[:num_examples]
    
    def build_few_shot_prompt(
        self,
        base_prompt: str,
        examples: List[Dict],
        format: str = "structured"
    ) -> str:
        """
        Build prompt with few-shot examples
        
        Args:
            base_prompt: The base prompt without examples
            examples: List of example grading results
            format: 'structured' or 'conversational'
            
        Returns:
            Prompt with examples included
        """
        if not examples:
            return base_prompt
        
        few_shot_section = "\n\n# Example Gradings\n\n"
        few_shot_section += "Here are some examples of well-graded submissions to guide your evaluation:\n\n"
        
        for i, example in enumerate(examples, 1):
            if format == "structured":
                few_shot_section += f"## Example {i}\n"
                few_shot_section += f"**Submission:** {example.get('submission_text', '')[:200]}...\n"
                few_shot_section += f"**Grade:** {example.get('grade', 'N/A')}\n"
                few_shot_section += f"**Feedback:** {example.get('student_feedback', '')[:300]}...\n\n"
            
            else:  # conversational
                few_shot_section += f"Example {i}:\n"
                few_shot_section += f"The student submitted: \"{example.get('submission_text', '')[:150]}...\"\n"
                few_shot_section += f"Grade given: {example.get('grade', 'N/A')}\n"
                few_shot_section += f"Feedback: \"{example.get('student_feedback', '')[:200]}...\"\n\n"
        
        few_shot_section += "---\n\n"
        few_shot_section += "Now, please grade the following submission using similar standards:\n\n"
        
        return base_prompt + few_shot_section
    
    def evaluate_example_quality(self, example: Dict) -> Dict:
        """
        Evaluate the quality of an example for few-shot learning
        
        Returns:
            Dict with quality metrics
        """
        score = 0
        reasons = []
        
        # Check if has human feedback
        if example.get('human_feedback'):
            score += 30
            reasons.append("Has human feedback")
        
        # Check if marked as good example
        if example.get('is_good_example'):
            score += 25
            reasons.append("Marked as good example")
        
        # Check feedback completeness
        if example.get('detailed_feedback') and len(example.get('detailed_feedback', '')) > 100:
            score += 20
            reasons.append("Has comprehensive feedback")
        
        # Check if has grade
        if example.get('grade') and example.get('grade') != 'N/A':
            score += 15
            reasons.append("Has clear grade")
        
        # Check submission length (not too short)
        if example.get('submission_text') and len(example.get('submission_text', '')) > 200:
            score += 10
            reasons.append("Has substantial submission text")
        
        quality = "poor"
        if score >= 70:
            quality = "excellent"
        elif score >= 50:
            quality = "good"
        elif score >= 30:
            quality = "fair"
        
        return {
            "quality": quality,
            "score": score,
            "reasons": reasons
        }
    
    def recommend_examples(
        self,
        assignment_id: Optional[int] = None,
        min_quality_score: int = 50
    ) -> List[Dict]:
        """
        Recommend best examples for few-shot learning
        
        Returns:
            List of recommended examples with quality scores
        """
        examples = self.db.get_good_examples(assignment_id, limit=20)
        
        recommendations = []
        for example in examples:
            quality_eval = self.evaluate_example_quality(example)
            
            if quality_eval['score'] >= min_quality_score:
                recommendations.append({
                    'example': example,
                    'quality': quality_eval
                })
        
        # Sort by quality score
        recommendations.sort(key=lambda x: x['quality']['score'], reverse=True)
        
        return recommendations
    
    def augment_prompt_with_examples(
        self,
        system_prompt: str,
        user_prompt: str,
        assignment_id: Optional[int] = None,
        num_examples: int = 3
    ) -> tuple[str, str]:
        """
        Augment prompts with few-shot examples
        
        Returns:
            Tuple of (augmented_system_prompt, augmented_user_prompt)
        """
        examples = self.get_examples_for_prompt(assignment_id, num_examples)
        
        if not examples:
            return system_prompt, user_prompt
        
        # Add examples to user prompt
        augmented_user = self.build_few_shot_prompt(user_prompt, examples)
        
        # Update system prompt to mention examples
        augmented_system = system_prompt + "\n\nYou have been provided with example gradings to guide your evaluation. Use these as reference for quality and consistency."
        
        return augmented_system, augmented_user

