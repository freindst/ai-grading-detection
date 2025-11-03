"""
Criteria Parser - Convert structured criteria to natural language prompts
"""

import json
import yaml
from typing import Dict, List, Union


class CriteriaParser:
    """Parse and convert various criteria formats to natural language"""
    
    def parse_criteria(self, criteria_input: str, format_hint: str = "auto") -> str:
        """
        Parse criteria from various formats to natural language
        
        Args:
            criteria_input: The input criteria (JSON, YAML, or text)
            format_hint: Format hint ('json', 'yaml', 'bullet', 'auto')
            
        Returns:
            Natural language criteria text
        """
        if format_hint == "auto":
            format_hint = self._detect_format(criteria_input)
        
        if format_hint == "json":
            return self._parse_json(criteria_input)
        elif format_hint == "yaml":
            return self._parse_yaml(criteria_input)
        elif format_hint == "bullet":
            return self._parse_bullet_points(criteria_input)
        else:
            # Already natural language
            return criteria_input
    
    def _detect_format(self, text: str) -> str:
        """Detect the format of criteria input"""
        stripped = text.strip()
        
        # Check for JSON
        if (stripped.startswith('{') or stripped.startswith('[')):
            try:
                json.loads(stripped)
                return "json"
            except:
                pass
        
        # Check for YAML
        if ':' in stripped and ('\n' in stripped or '  ' in stripped):
            try:
                yaml.safe_load(stripped)
                return "yaml"
            except:
                pass
        
        # Check for bullet points
        if any(line.strip().startswith(('-', '*', '•', '1.', '2.')) for line in stripped.split('\n')):
            return "bullet"
        
        return "text"
    
    def _parse_json(self, json_str: str) -> str:
        """Parse JSON criteria to natural language"""
        try:
            data = json.loads(json_str)
            return self._format_structured_criteria(data)
        except json.JSONDecodeError as e:
            return f"[Error parsing JSON: {e}]\n{json_str}"
    
    def _parse_yaml(self, yaml_str: str) -> str:
        """Parse YAML criteria to natural language"""
        try:
            data = yaml.safe_load(yaml_str)
            return self._format_structured_criteria(data)
        except yaml.YAMLError as e:
            return f"[Error parsing YAML: {e}]\n{yaml_str}"
    
    def _parse_bullet_points(self, text: str) -> str:
        """Parse bullet point criteria (already readable, just clean up)"""
        lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            if stripped:
                # Remove bullet characters for cleaner look
                if stripped[0] in ['-', '*', '•']:
                    stripped = stripped[1:].strip()
                lines.append(stripped)
        return '\n'.join(lines)
    
    def _format_structured_criteria(self, data: Union[Dict, List]) -> str:
        """Convert structured data to natural language criteria"""
        output = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    output.append(f"{key}: {value} points")
                elif isinstance(value, str):
                    output.append(f"{key}: {value}")
                elif isinstance(value, dict):
                    output.append(f"\n{key}:")
                    for sub_key, sub_value in value.items():
                        output.append(f"  - {sub_key}: {sub_value}")
                elif isinstance(value, list):
                    output.append(f"\n{key}:")
                    for item in value:
                        output.append(f"  - {item}")
        
        elif isinstance(data, list):
            for i, item in enumerate(data, 1):
                if isinstance(item, str):
                    output.append(f"{i}. {item}")
                elif isinstance(item, dict):
                    output.append(f"\n{i}. {list(item.keys())[0] if item else 'Item'}:")
                    for k, v in item.items():
                        output.append(f"   - {k}: {v}")
        
        return '\n'.join(output)
    
    def validate_criteria(self, criteria: str) -> tuple[bool, str]:
        """
        Validate criteria is not empty and has content
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not criteria or not criteria.strip():
            return False, "Criteria cannot be empty"
        
        if len(criteria.strip()) < 10:
            return False, "Criteria is too short (minimum 10 characters)"
        
        return True, "Criteria is valid"
    
    def extract_rubric_items(self, criteria: str) -> List[Dict]:
        """
        Extract individual rubric items from criteria
        
        Returns:
            List of dicts with 'item' and optionally 'points'
        """
        items = []
        format_type = self._detect_format(criteria)
        
        if format_type == "json":
            try:
                data = json.loads(criteria)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (int, float)):
                            items.append({"item": key, "points": value})
                        else:
                            items.append({"item": key, "description": str(value)})
                elif isinstance(data, list):
                    for item in data:
                        items.append({"item": str(item)})
            except:
                pass
        
        elif format_type == "yaml":
            try:
                data = yaml.safe_load(criteria)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (int, float)):
                            items.append({"item": key, "points": value})
                        else:
                            items.append({"item": key, "description": str(value)})
            except:
                pass
        
        else:
            # Extract from bullet points or text
            for line in criteria.split('\n'):
                stripped = line.strip()
                if stripped and any(stripped.startswith(c) for c in ['-', '*', '•', '1', '2', '3']):
                    # Remove bullet/number
                    text = stripped.lstrip('-*•123456789. ')
                    if text:
                        items.append({"item": text})
        
        return items if items else [{"item": criteria}]

