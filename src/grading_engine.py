"""
Grading Engine - Core grading logic and prompt management
"""

import json
import re
from typing import Dict, Optional, Tuple
from src.llm_client import OllamaClient


class GradingEngine:
    """Handles grading logic, prompt building, and output parsing"""
    
    def __init__(self, llm_client: OllamaClient):
        self.llm_client = llm_client
        self.default_output_format = """
Please provide your grading in the following JSON format:
{
  "grade": "A/B/C/D/E or numeric score",
  "detailed_feedback": "Comprehensive feedback for instructor with specific details, strengths, weaknesses, and justification",
  "student_feedback": "Concise, constructive feedback suitable for posting as a comment to the student",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "deductions": [
    {"reason": "specific issue", "points": number}
  ],
  "confidence": "high/medium/low"
}
"""
    
    def build_grading_prompt(
        self,
        submission_text: str,
        assignment_instruction: str,
        grading_criteria: str,
        output_format: str = "letter",  # letter (A-E) or numeric
        max_score: Optional[int] = 100,
        ai_keywords: Optional[str] = "",
        additional_requirements: Optional[str] = "",
        few_shot_examples: Optional[str] = ""
    ) -> Tuple[str, str]:
        """
        Build the grading prompt
        
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Build output format instruction based on type
        if output_format.lower() == "numeric":
            format_instruction = f"""
OUTPUT FORMAT REQUIREMENT (CRITICAL):
You MUST provide a NUMERIC score between 0 and {max_score}.
DO NOT use letter grades (A, B, C, D, E, F).
DO NOT use percentages.
ONLY use a whole number between 0 and {max_score}.

Example of CORRECT format:
  "grade": "85"
  "grade": "92"
  "grade": "{max_score}"

Example of INCORRECT format (DO NOT USE):
  "grade": "A"
  "grade": "B+"
  "grade": "85%"
"""
        else:
            format_instruction = f"""
OUTPUT FORMAT REQUIREMENT:
You MUST provide a LETTER grade: A, B, C, D, or E.
DO NOT use numeric scores.
DO NOT use percentages.
You may use + or - modifiers (e.g., A-, B+).

Example of CORRECT format:
  "grade": "A"
  "grade": "B+"
  "grade": "C-"

Example of INCORRECT format (DO NOT USE):
  "grade": "85"
  "grade": "92/100"
"""
        
        system_prompt = f"""You are an expert college-level homework grading assistant. Your task is to evaluate student submissions fairly and provide constructive feedback.

{format_instruction}

{self.default_output_format}

CRITICAL INSTRUCTIONS:
1. Be fair, consistent, and constructive in your grading
2. Provide specific examples from the submission to support your evaluation
3. The "student_feedback" field should contain ONLY constructive feedback suitable for posting to the student
4. Keep your feedback focused on the quality of work
5. The "detailed_feedback" field is for the instructor and can include technical analysis of the work
6. AVOID generic praise phrases like "Good job", "Great work", "Keep up the good work", "Well done"
7. Be direct and specific - if something is good, explain WHY it's good with specific examples
8. Focus on actionable feedback rather than platitudes
9. Student feedback should be professional but straightforward - no need for compromises or sugar-coating"""

        user_prompt = f"""# Assignment Instructions
{assignment_instruction}

# Grading Criteria
{grading_criteria}

{f"# Additional Requirements: {additional_requirements}" if additional_requirements else ""}

{few_shot_examples if few_shot_examples else ""}

# Student Submission
{submission_text}

Please grade this submission according to the criteria provided above."""

        return system_prompt, user_prompt
    
    def grade_submission(
        self,
        submission_text: str,
        assignment_instruction: str,
        grading_criteria: str,
        output_format: str = "letter",
        max_score: Optional[int] = 100,
        ai_keywords: Optional[str] = "",
        additional_requirements: Optional[str] = "",
        temperature: float = 0.3,
        keep_context: bool = False,
        few_shot_examples: Optional[str] = ""
    ) -> Dict:
        """
        Grade a single submission
        
        Returns:
            Dict with grading results, formatted output, raw output, and metadata
        """
        # Build prompts
        system_prompt, user_prompt = self.build_grading_prompt(
            submission_text=submission_text,
            assignment_instruction=assignment_instruction,
            grading_criteria=grading_criteria,
            output_format=output_format,
            max_score=max_score,
            ai_keywords=ai_keywords,
            additional_requirements=additional_requirements,
            few_shot_examples=few_shot_examples
        )
        
        # Generate response from LLM
        llm_response = self.llm_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            keep_context=keep_context
        )
        
        if not llm_response.get('success'):
            return {
                "success": False,
                "error": llm_response.get('error', 'Unknown error'),
                "raw_output": llm_response.get('raw_output', ''),
                "formatted_output": None,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            }
        
        # Parse the output
        parsed_result = self.parse_grading_output(llm_response['response'])
        
        return {
            "success": True,
            "raw_llm_output": llm_response['response'],
            "raw_api_response": llm_response.get('raw_output', ''),
            "parsed_result": parsed_result,
            "formatted_output": self.format_grading_result(parsed_result),
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "model": llm_response.get('model'),
            "tokens": {
                "prompt": llm_response.get('prompt_tokens', 0),
                "completion": llm_response.get('completion_tokens', 0)
            }
        }
    
    def parse_grading_output(self, llm_output: str) -> Dict:
        """
        Parse LLM output to extract grading information
        Supports both JSON format and natural language format
        """
        print(f"\n=== JSON PARSING DEBUG ===")
        print(f"Output length: {len(llm_output)} characters")
        print(f"First 100 chars: {llm_output[:100]}")
        print(f"Last 100 chars: {llm_output[-100:]}")
        
        # Try JSON parsing first - use multiple strategies
        # Strategy 1: Extract JSON from markdown code block
        code_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', llm_output, re.DOTALL)
        if code_block_match:
            print("Strategy 1: Found markdown code block")
            try:
                parsed = json.loads(code_block_match.group(1))
                print("Strategy 1: JSON parsed successfully!")
                return self._build_parsed_result(parsed)
            except json.JSONDecodeError as e:
                print(f"Strategy 1: JSON decode error: {e}")
                pass
        else:
            print("Strategy 1: No markdown code block found")
        
        # Strategy 2: Find JSON object (non-greedy, balanced braces)
        # This is more robust than the greedy [\s\S]* pattern
        # IMPORTANT: Account for braces inside string literals (they don't count)
        json_start = llm_output.find('{')
        if json_start != -1:
            print(f"Strategy 2: Found opening brace at position {json_start}")
            # Find matching closing brace, skipping braces inside quoted strings
            brace_count = 0
            json_end = -1
            in_string = False
            escape_next = False
            
            for i, char in enumerate(llm_output[json_start:], start=json_start):
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                # Only count braces when not inside a string
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
            
            if json_end > json_start:
                json_str = llm_output[json_start:json_end]
                print(f"Strategy 2: Extracted JSON from position {json_start} to {json_end}")
                print(f"Strategy 2: JSON string length: {len(json_str)}")
                try:
                    parsed = json.loads(json_str)
                    print("Strategy 2: JSON parsed successfully!")
                    return self._build_parsed_result(parsed)
                except json.JSONDecodeError as e:
                    print(f"Strategy 2: JSON decode error: {e}")
                    print(f"Strategy 2: Failed JSON (first 200 chars): {json_str[:200]}")
            else:
                print(f"Strategy 2: Could not find matching closing brace")
        else:
            print("Strategy 2: No opening brace found")
        
        # Strategy 3: Try greedy match as last resort
        json_match = re.search(r'\{[\s\S]*\}', llm_output)
        if json_match:
            print("Strategy 3: Found JSON with greedy regex")
            try:
                parsed = json.loads(json_match.group())
                print("Strategy 3: JSON parsed successfully!")
                return self._build_parsed_result(parsed)
            except json.JSONDecodeError as e:
                print(f"Strategy 3: JSON decode error: {e}")
                pass
        else:
            print("Strategy 3: Greedy regex found nothing")
        
        # Fallback: Try to extract JSON fields even if parsing failed
        # This handles cases where JSON is slightly malformed but still extractable
        print("❌ ALL JSON PARSING STRATEGIES FAILED - Attempting field extraction from raw text")
        
        # Try to extract individual fields using regex (even if full JSON parse failed)
        fallback_result = self._extract_fields_from_failed_json(llm_output)
        if fallback_result and fallback_result.get('grade') != 'N/A':
            print("✓ Successfully extracted fields from failed JSON using regex")
            return fallback_result
        
        # Last resort: Use regex-based parsing for natural language output
        print("⚠️ Field extraction also failed - Using regex fallback")
        return self._parse_natural_language(llm_output)
    
    def _build_parsed_result(self, parsed: Dict) -> Dict:
        """Build standardized parsed result from JSON dict with smart field extraction"""
        # CLEANUP: Remove any "AI Detection Keywords:" text that the LLM incorrectly included
        detailed_feedback = parsed.get("detailed_feedback", "")
        student_feedback = parsed.get("student_feedback", "")
        
        # Smart extraction: If student_feedback is missing, try to extract it from detailed_feedback
        if not student_feedback and detailed_feedback:
            # Look for patterns like "Student Feedback:", "Feedback for Student:", etc.
            patterns = [
                r'Student Feedback:\s*\n\n(.+?)(?:\n\n[A-Z]|$)',  # "Student Feedback:\n\nText..."
                r'Student Feedback:\s*(.+?)(?:\n\n|$)',  # "Student Feedback: Text..."
                r'Feedback for [Ss]tudent:\s*\n\n(.+?)(?:\n\n|$)',  # "Feedback for student:..."
                r'For [Ss]tudent:\s*\n\n(.+?)(?:\n\n|$)',  # "For student:..."
            ]
            
            for pattern in patterns:
                match = re.search(pattern, detailed_feedback, re.DOTALL | re.IGNORECASE)
                if match:
                    student_feedback = match.group(1).strip()
                    # Remove the student feedback section from detailed_feedback
                    detailed_feedback = re.sub(
                        r'Student Feedback:.*$', 
                        '', 
                        detailed_feedback, 
                        flags=re.DOTALL | re.IGNORECASE
                    ).strip()
                    print(f"✓ Extracted student_feedback from detailed_feedback ({len(student_feedback)} chars)")
                    break
        
        # Clean up AI detection text if present
        if detailed_feedback:
            detailed_feedback = self._remove_ai_detection_text(detailed_feedback)
            detailed_feedback = self._remove_generic_phrases(detailed_feedback)
        if student_feedback:
            student_feedback = self._remove_ai_detection_text(student_feedback)
            student_feedback = self._remove_generic_phrases(student_feedback)
        
        # Extract grade - handle both string and numeric, with robust validation
        grade = parsed.get("grade", "N/A")
        
        # Handle various formats: string, number, None, empty
        if grade is None:
            grade = "N/A"
        elif isinstance(grade, (int, float)):
            # Convert numeric grade to string
            grade = str(int(grade))
        elif isinstance(grade, str):
            grade = grade.strip()
            # Check if it's actually empty after stripping
            if not grade:
                grade = "N/A"
        else:
            # Unexpected type, convert to string
            grade = str(grade).strip() if grade else "N/A"
        
        # Final validation - ensure we have a valid grade
        if not grade or grade == "N/A":
            # Try to extract from other fields if grade is missing
            # Sometimes LLM puts grade in a different field
            for alt_field in ["score", "final_grade", "grade_value"]:
                alt_grade = parsed.get(alt_field)
                if alt_grade:
                    grade = str(alt_grade).strip()
                    print(f"✓ Found grade in alternate field '{alt_field}': {grade}")
                    break
        
        # Validate that feedback fields contain actual text, not JSON strings
        # This can happen if JSON parsing partially failed or returned wrong structure
        if detailed_feedback and isinstance(detailed_feedback, str):
            # Check if it looks like JSON (starts with '{' and contains JSON-like structure)
            if detailed_feedback.strip().startswith('{') and '"grade"' in detailed_feedback:
                print("⚠️ WARNING: detailed_feedback appears to be raw JSON, attempting to extract text")
                # Try to re-extract from parsed dict
                detailed_feedback = parsed.get("detailed_feedback", "")
                if isinstance(detailed_feedback, str) and detailed_feedback.strip().startswith('{'):
                    # Still JSON, something went wrong - use fallback
                    detailed_feedback = ""
        
        if student_feedback and isinstance(student_feedback, str):
            # Check if it looks like JSON
            if student_feedback.strip().startswith('{') and '"grade"' in student_feedback:
                print("⚠️ WARNING: student_feedback appears to be raw JSON, attempting to extract text")
                # Try to re-extract from parsed dict
                student_feedback = parsed.get("student_feedback", "")
                if isinstance(student_feedback, str) and student_feedback.strip().startswith('{'):
                    # Still JSON, something went wrong - use fallback
                    student_feedback = ""
        
        return {
            "parse_method": "json",
            "grade": grade,
            "detailed_feedback": detailed_feedback if detailed_feedback else "N/A",
            "student_feedback": student_feedback if student_feedback else "N/A",
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
            "deductions": parsed.get("deductions", []),
            "ai_keywords_found": parsed.get("ai_detection_keywords", []),
            "confidence": parsed.get("confidence", "medium")
        }
    
    def _remove_ai_detection_text(self, text: str) -> str:
        """
        Remove any 'AI Detection Keywords:' text that the LLM incorrectly included.
        This is a safety net since the LLM should not include this text at all.
        
        Args:
            text: Feedback text that may contain AI detection keyword mentions
        
        Returns:
            Cleaned text without AI detection keyword mentions
        """
        if not text:
            return text
        
        # Remove patterns like:
        # "AI Detection Keywords: ['keyword']"
        # "   AI Detection Keywords: []"  (with leading spaces)
        # "AI detection keywords: None"
        # "\n\nAI Detection Keywords: ['x']" (with multiple newlines)
        # Also handles various capitalizations and whitespace
        patterns = [
            # Pattern 1: Multiple newlines + optional whitespace + AI Detection text
            r'\n+\s*AI [Dd]etection [Kk]eywords?:\s*\[.*?\]',
            r'\n+\s*AI [Dd]etection [Kk]eywords?:\s*\[\s*\]',
            r'\n+\s*AI [Dd]etection [Kk]eywords?:\s*None',
            r'\n+\s*AI [Dd]etection [Kk]eywords?:.*?(?=\n|$)',
            # Pattern 2: Single newline + optional whitespace
            r'\n\s*AI [Dd]etection [Kk]eywords?:\s*\[.*?\]',
            r'\n\s*AI [Dd]etection [Kk]eywords?:\s*None',
            # Pattern 3: Just whitespace (no newline)
            r'\s+AI [Dd]etection [Kk]eywords?:\s*\[.*?\]',
            r'\s+AI [Dd]etection [Kk]eywords?:\s*None',
            # Pattern 4: Final catch-all at end of string
            r'\s*AI [Dd]etection [Kk]eywords?:.*$',
        ]
        
        cleaned_text = text
        for pattern in patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove any trailing whitespace and excessive newlines
        cleaned_text = cleaned_text.strip()
        # Replace multiple consecutive newlines with just two
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text
    
    def _remove_generic_phrases(self, text: str) -> str:
        """
        Remove generic praise phrases that don't add value to feedback.
        
        The system prompt explicitly instructs to avoid these phrases, but sometimes
        the LLM includes them anyway. This is a safety net to remove them.
        
        Args:
            text: Feedback text that may contain generic phrases
        
        Returns:
            Cleaned text without generic praise phrases
        """
        if not text:
            return text
        
        # List of generic phrases to remove (case-insensitive)
        generic_phrases = [
            r'Keep up the good work!?',
            r'Keep up the great work!?',
            r'Well done!?',
            r'Good job!?',
            r'Great job!?',
            r'Great work!?',
            r'Nice work!?',
            r'Excellent work!?',
            r'Keep it up!?',
            r'Continue the good work!?',
            r'You\'re doing great!?',
            r'You did great!?',
        ]
        
        cleaned_text = text
        
        # Remove each generic phrase
        for phrase_pattern in generic_phrases:
            # Try to match at the end of sentences or standalone
            patterns_to_try = [
                # At the end with punctuation
                r'\s+' + phrase_pattern + r'\s*$',
                # At the end of a sentence
                r'\s+' + phrase_pattern + r'\s+',
                # Standalone with surrounding whitespace
                r'^\s*' + phrase_pattern + r'\s*$',
                # After punctuation
                r'\.\s+' + phrase_pattern,
            ]
            
            for pattern in patterns_to_try:
                cleaned_text = re.sub(pattern, '. ', cleaned_text, flags=re.IGNORECASE)
        
        # Clean up any resulting multiple spaces or periods
        cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
        cleaned_text = re.sub(r'\.{2,}', '.', cleaned_text)
        cleaned_text = re.sub(r'\.\s*\.', '.', cleaned_text)
        
        # Clean up trailing/leading whitespace
        cleaned_text = cleaned_text.strip()
        
        # Remove trailing period-space if it's now at the end
        cleaned_text = re.sub(r'\.\s*$', '.', cleaned_text)
        
        return cleaned_text
    
    def _extract_fields_from_failed_json(self, text: str) -> Dict:
        """
        When JSON parsing fails, try to extract individual fields using regex.
        This is more robust than full JSON parsing for slightly malformed JSON.
        """
        result = {
            "parse_method": "regex_extraction",
            "grade": "N/A",
            "detailed_feedback": "",
            "student_feedback": "",
            "strengths": [],
            "weaknesses": [],
            "deductions": [],
            "ai_keywords_found": [],
            "confidence": "low"
        }
        
        # Extract grade field (most critical)
        grade_patterns = [
            r'"grade"\s*:\s*"([^"]+)"',  # "grade": "16"
            r'"grade"\s*:\s*(\d+)',      # "grade": 16
            r'"grade"\s*:\s*"([A-E][\+\-]?)"',  # "grade": "A"
        ]
        for pattern in grade_patterns:
            match = re.search(pattern, text)
            if match:
                result["grade"] = match.group(1).strip()
                print(f"✓ Extracted grade from failed JSON: '{result['grade']}'")
                break
        
        # Extract detailed_feedback
        detailed_patterns = [
            r'"detailed_feedback"\s*:\s*"((?:[^"\\]|\\.)*)"',  # Handles escaped quotes
            r'"detailed_feedback"\s*:\s*"([^"]+)"',  # Simple version
        ]
        for pattern in detailed_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                # Unescape common escape sequences
                feedback = match.group(1)
                feedback = feedback.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                result["detailed_feedback"] = feedback.strip()
                if result["detailed_feedback"]:
                    print(f"✓ Extracted detailed_feedback ({len(result['detailed_feedback'])} chars)")
                    break
        
        # Extract student_feedback
        student_patterns = [
            r'"student_feedback"\s*:\s*"((?:[^"\\]|\\.)*)"',
            r'"student_feedback"\s*:\s*"([^"]+)"',
        ]
        for pattern in student_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                feedback = match.group(1)
                feedback = feedback.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
                result["student_feedback"] = feedback.strip()
                if result["student_feedback"]:
                    print(f"✓ Extracted student_feedback ({len(result['student_feedback'])} chars)")
                    break
        
        # Only return if we extracted at least the grade
        if result["grade"] != "N/A":
            return result
        
        return None  # Signal that extraction failed
    
    def _parse_natural_language(self, text: str) -> Dict:
        """
        Parse natural language grading output using regex patterns
        """
        result = {
            "parse_method": "regex",
            "grade": "N/A",
            "detailed_feedback": text,
            "student_feedback": text[:500] if len(text) > 500 else text,
            "strengths": [],
            "weaknesses": [],
            "deductions": [],
            "ai_keywords_found": [],
            "confidence": "medium"
        }
        
        # Extract grade
        grade_patterns = [
            r"[Gg]rade:\s*([A-E][\+\-]?|\d+)",
            r"[Ss]core:\s*(\d+)",
            r"^([A-E][\+\-]?)",
        ]
        for pattern in grade_patterns:
            match = re.search(pattern, text)
            if match:
                result["grade"] = match.group(1)
                break
        
        # Extract strengths
        strengths_match = re.search(r"[Ss]trengths?:?\s*([\s\S]*?)(?:[Ww]eaknesses?|[Dd]eductions?|[Ff]eedback|$)", text)
        if strengths_match:
            strengths_text = strengths_match.group(1)
            result["strengths"] = [s.strip() for s in re.findall(r"[-•*]\s*(.+)", strengths_text)]
        
        # Extract weaknesses
        weaknesses_match = re.search(r"[Ww]eaknesses?:?\s*([\s\S]*?)(?:[Ss]trengths?|[Dd]eductions?|[Ff]eedback|$)", text)
        if weaknesses_match:
            weaknesses_text = weaknesses_match.group(1)
            result["weaknesses"] = [w.strip() for w in re.findall(r"[-•*]\s*(.+)", weaknesses_text)]
        
        return result
    
    def format_grading_result(self, parsed_result: Dict) -> str:
        """Format parsed result into human-readable text"""
        output = []
        output.append(f"Grade: {parsed_result.get('grade', 'N/A')}")
        output.append(f"Confidence: {parsed_result.get('confidence', 'N/A')}")
        output.append("")
        
        if parsed_result.get('detailed_feedback'):
            output.append("=== DETAILED FEEDBACK (For Instructor) ===")
            output.append(parsed_result['detailed_feedback'])
            output.append("")
        
        if parsed_result.get('student_feedback'):
            output.append("=== STUDENT FEEDBACK (For Posting) ===")
            output.append(parsed_result['student_feedback'])
            output.append("")
        
        if parsed_result.get('strengths'):
            output.append("Strengths:")
            for strength in parsed_result['strengths']:
                output.append(f"  + {strength}")
            output.append("")
        
        if parsed_result.get('weaknesses'):
            output.append("Weaknesses:")
            for weakness in parsed_result['weaknesses']:
                output.append(f"  - {weakness}")
            output.append("")
        
        if parsed_result.get('deductions'):
            output.append("Deductions:")
            for deduction in parsed_result['deductions']:
                output.append(f"  • {deduction.get('reason', 'N/A')}: -{deduction.get('points', 0)} points")
            output.append("")
        
        if parsed_result.get('ai_keywords_found'):
            output.append(f"⚠️ AI Detection Keywords Found: {', '.join(parsed_result['ai_keywords_found'])}")
            output.append("")
        
        output.append(f"Parse Method: {parsed_result.get('parse_method', 'unknown')}")
        
        return "\n".join(output)
    
    def llm_based_parse(self, raw_output: str) -> Dict:
        """
        Use LLM to parse its own output if standard parsing fails
        This is a fallback method for complex or malformed outputs
        """
        parsing_prompt = f"""You previously generated this grading output:

{raw_output}

Please extract and structure the key information into this JSON format:
{{
  "grade": "extracted grade",
  "detailed_feedback": "feedback for instructor",
  "student_feedback": "feedback for student",
  "strengths": ["list of strengths"],
  "weaknesses": ["list of weaknesses"],
  "deductions": [{{"reason": "...", "points": ...}}],
  "confidence": "high/medium/low"
}}

Only output valid JSON, nothing else."""

        response = self.llm_client.generate(
            prompt=parsing_prompt,
            temperature=0.1,
            keep_context=False
        )
        
        if response.get('success'):
            try:
                parsed = json.loads(response['response'])
                parsed['parse_method'] = 'llm_assisted'
                return parsed
            except json.JSONDecodeError:
                pass
        
        # If LLM parsing fails, return raw output wrapped
        return {
            "parse_method": "failed",
            "grade": "N/A",
            "detailed_feedback": raw_output,
            "student_feedback": raw_output[:500],
            "strengths": [],
            "weaknesses": [],
            "deductions": [],
            "confidence": "low"
        }

