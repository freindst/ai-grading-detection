"""
Prompt Builder - Template system for building grading prompts
"""

from typing import Dict, List, Optional
import re


class PromptBuilder:
    """Build and manage prompt templates with variables"""
    
    def __init__(self):
        self.default_template = {
            'system': """You are an expert college-level homework grading assistant. Your task is to evaluate student submissions fairly and provide constructive feedback.

Grading Output Format: {output_format}
{score_info}

Please provide your grading in JSON format with:
- grade: The final grade
- detailed_feedback: Comprehensive analysis for instructor
- student_feedback: Concise feedback for student
- strengths: List of strengths
- weaknesses: List of weaknesses
- deductions: List of point deductions (if numeric)
- ai_detection_keywords: Any embedded keywords found
- confidence: high/medium/low

Be fair, consistent, and constructive.""",
            
            'user': """# Assignment Instructions
{instructions}

# Grading Criteria
{criteria}

{ai_keywords_section}

{additional_requirements_section}

# Student Submission
{submission}

Please grade this submission according to the criteria provided above."""
        }
    
    def build_prompt(
        self,
        instructions: str,
        criteria: str,
        submission: str,
        output_format: str = "letter",
        max_score: int = 100,
        ai_keywords: str = "",
        additional_requirements: str = "",
        template: Dict = None
    ) -> tuple[str, str]:
        """
        Build system and user prompts from template
        
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        if template is None:
            template = self.default_template
        
        # Build score info
        if output_format.lower() == "numeric":
            score_info = f"Maximum Score: {max_score}"
        else:
            score_info = "Grade Scale: A (Excellent) to E (Failing)"
        
        # Build AI keywords section
        ai_keywords_section = ""
        if ai_keywords and ai_keywords.strip():
            ai_keywords_section = f"# AI Detection Keywords\nCheck if these appear in submission: {ai_keywords}"
        
        # Build additional requirements section
        additional_requirements_section = ""
        if additional_requirements and additional_requirements.strip():
            additional_requirements_section = f"# Additional Requirements\n{additional_requirements}"
        
        # Format system prompt
        system_prompt = template['system'].format(
            output_format=output_format.upper(),
            score_info=score_info
        )
        
        # Format user prompt
        user_prompt = template['user'].format(
            instructions=instructions,
            criteria=criteria,
            submission=submission,
            ai_keywords_section=ai_keywords_section,
            additional_requirements_section=additional_requirements_section
        )
        
        return system_prompt, user_prompt
    
    def create_template(
        self,
        name: str,
        system_template: str,
        user_template: str,
        description: str = ""
    ) -> Dict:
        """Create a new prompt template"""
        return {
            'name': name,
            'description': description,
            'system': system_template,
            'user': user_template
        }
    
    def get_template_variables(self, template_str: str) -> List[str]:
        """Extract variables from template string"""
        # Find all {variable} patterns
        variables = re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', template_str)
        return list(set(variables))
    
    def validate_template(self, template: Dict, required_vars: List[str] = None) -> tuple[bool, str]:
        """
        Validate template has required structure and variables
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if 'system' not in template or 'user' not in template:
            return False, "Template must have 'system' and 'user' keys"
        
        if required_vars:
            system_vars = self.get_template_variables(template['system'])
            user_vars = self.get_template_variables(template['user'])
            all_vars = set(system_vars + user_vars)
            
            for var in required_vars:
                if var not in all_vars:
                    return False, f"Required variable '{var}' not found in template"
        
        return True, "Template is valid"
    
    def get_default_template(self) -> Dict:
        """Get the default template"""
        return self.default_template.copy()
    
    def merge_templates(self, base_template: Dict, override_template: Dict) -> Dict:
        """Merge two templates, with override taking precedence"""
        merged = base_template.copy()
        merged.update(override_template)
        return merged

