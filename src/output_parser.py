"""
Output Parser - Enhanced parsing with LLM assistance fallback
(This extends the parsing already in grading_engine.py)
"""

import json
import re
from typing import Dict, Optional
from src.llm_client import OllamaClient


class OutputParser:
    """Advanced output parser with multiple strategies"""
    
    def __init__(self, llm_client: Optional[OllamaClient] = None):
        self.llm_client = llm_client
    
    def parse(self, llm_output: str, use_llm_fallback: bool = True) -> Dict:
        """
        Parse LLM output using multiple strategies
        
        Priority:
        1. JSON extraction
        2. Regex pattern matching
        3. LLM-assisted parsing (if enabled)
        4. Return raw text
        
        Returns:
            Parsed grading dictionary
        """
        # Strategy 1: JSON extraction
        json_result = self._try_json_parse(llm_output)
        if json_result['success']:
            return json_result['data']
        
        # Strategy 2: Regex patterns
        regex_result = self._try_regex_parse(llm_output)
        if regex_result['confidence'] != 'low':
            return regex_result
        
        # Strategy 3: LLM-assisted parsing
        if use_llm_fallback and self.llm_client:
            llm_result = self._try_llm_parse(llm_output)
            if llm_result['parse_method'] == 'llm_assisted':
                return llm_result
        
        # Strategy 4: Return raw with low confidence
        return {
            "parse_method": "failed",
            "grade": "N/A",
            "detailed_feedback": llm_output,
            "student_feedback": llm_output[:500] if len(llm_output) > 500 else llm_output,
            "strengths": [],
            "weaknesses": [],
            "deductions": [],
            "ai_keywords_found": [],
            "confidence": "low"
        }
    
    def _try_json_parse(self, text: str) -> Dict:
        """Try to extract and parse JSON from text"""
        # Look for JSON block
        json_patterns = [
            r'\{[\s\S]*\}',  # Complete object
            r'```json\s*([\s\S]*?)\s*```',  # Markdown code block
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # If from markdown block, match is the content
                    json_str = match if pattern.startswith('```') else match
                    parsed = json.loads(json_str)
                    
                    # Validate it has expected fields
                    if isinstance(parsed, dict) and 'grade' in parsed:
                        return {
                            'success': True,
                            'data': {
                                "parse_method": "json",
                                "grade": parsed.get("grade", "N/A"),
                                "detailed_feedback": parsed.get("detailed_feedback", ""),
                                "student_feedback": parsed.get("student_feedback", ""),
                                "strengths": parsed.get("strengths", []),
                                "weaknesses": parsed.get("weaknesses", []),
                                "deductions": parsed.get("deductions", []),
                                "ai_keywords_found": parsed.get("ai_detection_keywords", []),
                                "confidence": parsed.get("confidence", "medium")
                            }
                        }
                except json.JSONDecodeError:
                    continue
        
        return {'success': False}
    
    def _try_regex_parse(self, text: str) -> Dict:
        """Parse using regex patterns"""
        result = {
            "parse_method": "regex",
            "grade": "N/A",
            "detailed_feedback": text,
            "student_feedback": "",
            "strengths": [],
            "weaknesses": [],
            "deductions": [],
            "ai_keywords_found": [],
            "confidence": "medium"
        }
        
        # Extract grade
        grade_patterns = [
            r"[Gg]rade:\s*([A-E][\+\-]?|\d+(?:\.\d+)?)",
            r"[Ss]core:\s*(\d+(?:\.\d+)?)",
            r"[Ff]inal\s+[Gg]rade:\s*([A-E][\+\-]?|\d+(?:\.\d+)?)",
            r"^([A-E][\+\-]?)\s*$",  # Just a letter grade alone
        ]
        
        for pattern in grade_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                result["grade"] = match.group(1)
                break
        
        # Extract detailed feedback section
        detailed_match = re.search(
            r"(?:detailed|instructor)[\s_]*feedback:?\s*(.*?)(?=\n\n|student[\s_]*feedback|strengths|$)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        if detailed_match:
            result["detailed_feedback"] = detailed_match.group(1).strip()
        
        # Extract student feedback section
        student_match = re.search(
            r"student[\s_]*feedback:?\s*(.*?)(?=\n\n|strengths|weaknesses|$)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        if student_match:
            result["student_feedback"] = student_match.group(1).strip()
        else:
            # Use first paragraph as student feedback if not found
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if paragraphs:
                result["student_feedback"] = paragraphs[0][:500]
        
        # Extract strengths
        strengths_match = re.search(
            r"[Ss]trengths?:?\s*(.*?)(?=\n\n|[Ww]eaknesses?|[Dd]eductions?|$)",
            text,
            re.DOTALL
        )
        if strengths_match:
            strengths_text = strengths_match.group(1)
            result["strengths"] = [
                s.strip() for s in re.findall(r"[-•*]\s*(.+)", strengths_text)
            ]
        
        # Extract weaknesses
        weaknesses_match = re.search(
            r"[Ww]eaknesses?:?\s*(.*?)(?=\n\n|[Ss]trengths?|[Dd]eductions?|$)",
            text,
            re.DOTALL
        )
        if weaknesses_match:
            weaknesses_text = weaknesses_match.group(1)
            result["weaknesses"] = [
                w.strip() for w in re.findall(r"[-•*]\s*(.+)", weaknesses_text)
            ]
        
        # Confidence based on how much we extracted
        extracted_count = sum([
            result["grade"] != "N/A",
            len(result["strengths"]) > 0,
            len(result["weaknesses"]) > 0,
            bool(result["student_feedback"])
        ])
        
        if extracted_count >= 3:
            result["confidence"] = "high"
        elif extracted_count >= 2:
            result["confidence"] = "medium"
        else:
            result["confidence"] = "low"
        
        return result
    
    def _try_llm_parse(self, raw_output: str) -> Dict:
        """Use LLM to parse its own output"""
        if not self.llm_client:
            return {"parse_method": "failed"}
        
        parsing_prompt = f"""You previously generated this grading output:

{raw_output}

Please extract and structure the key information into this JSON format:
{{
  "grade": "extracted grade (A-E or numeric)",
  "detailed_feedback": "comprehensive feedback for instructor",
  "student_feedback": "concise feedback for student",
  "strengths": ["list", "of", "strengths"],
  "weaknesses": ["list", "of", "weaknesses"],
  "deductions": [{{"reason": "...", "points": ...}}],
  "confidence": "high/medium/low"
}}

Output ONLY valid JSON, nothing else."""

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
        
        return {"parse_method": "failed"}
    
    def validate_parsed_output(self, parsed: Dict) -> tuple[bool, str]:
        """
        Validate parsed output has minimum required fields
        
        Returns:
            Tuple of (is_valid, message)
        """
        required_fields = ['grade', 'detailed_feedback', 'student_feedback']
        
        for field in required_fields:
            if field not in parsed:
                return False, f"Missing required field: {field}"
        
        if parsed['grade'] == "N/A":
            return False, "Grade not extracted"
        
        return True, "Valid output"

