"""
AI Detector - Handles keyword detection and AI disclosure analysis
"""

import json
import re
from typing import Dict, List


class AIDetector:
    """Handles AI-related detection: keyword matching (regex) and disclosure analysis (LLM)"""

    def detect_keywords(self, text: str, keywords: str) -> List[str]:
        """
        Use regex to find exact keyword matches.

        Args:
            text: Submission text to search
            keywords: Comma-separated keywords from profile (e.g., "ChatGPT, as an AI")

        Returns:
            List of found keywords (case-insensitive exact matches)
        """
        if not keywords or not keywords.strip():
            return []

        found = []
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

        for keyword in keyword_list:
            # Escape special regex chars, use word boundary for exact match
            escaped = re.escape(keyword)
            pattern = rf"\b{escaped}\b"

            # Case-insensitive search
            if re.search(pattern, text, re.IGNORECASE):
                found.append(keyword)

        return found

    def analyze_ai_disclosure(self, text: str, llm_client) -> Dict:
        """
        Use LLM to analyze AI usage disclosure statements.

        Args:
            text: Submission text to analyze
            llm_client: Ollama client for LLM calls

        Returns:
            Dict with disclosure analysis containing:
            - disclosure_found: bool
            - disclosure_type: str
            - ai_tools_mentioned: List[str]
            - disclosure_statement: str or None
            - assessment: str
            - evidence: str
            - recommendation: str
        """
        system_prompt = """You are an academic integrity analyzer.
Your job is to identify AI usage disclosure statements in student submissions."""

        # Few-shot examples from user's academic integrity policy
        few_shot_examples = """
# Few-Shot Learning Examples

## Example 1: Honest Disclosure - Organizing & Outlining (ACCEPTABLE)
**Student Submission Excerpt:**
"...conclusion of my research paper.

AI Usage Disclosure
I used ChatGPT-5 to help me organize ideas, outline sections, and clarify explanations for this research paper. However, all the actual writing, examples, and phrasing in this paper were done by me in my own words to ensure originality."

**Expected Analysis:**
{
  "disclosure_found": true,
  "disclosure_type": "brainstorming",
  "ai_tools_mentioned": ["ChatGPT-5"],
  "disclosure_statement": "I used ChatGPT-5 to help me organize ideas, outline sections, and clarify explanations for this research paper. However, all the actual writing, examples, and phrasing in this paper were done by me in my own words to ensure originality.",
  "assessment": "honest_disclosure",
  "evidence": "Student explicitly disclosed ChatGPT-5 use for organization and outlining, clearly stated all writing was their own",
  "recommendation": "ACCEPTABLE"
}

## Example 2: Honest Disclosure - High-Level Brainstorming (ACCEPTABLE)
**Student Submission Excerpt:**
"...final thoughts on this topic.

Author's note on AI assistance: I used an AI assistant for high level brainstorming related to outline structure and concept checkpoints. I wrote all prose myself. I verified claims against the cited sources and formatted citations manually. No AI generated text was copied into the submitted paper."

**Expected Analysis:**
{
  "disclosure_found": true,
  "disclosure_type": "brainstorming",
  "ai_tools_mentioned": ["AI assistant"],
  "disclosure_statement": "I used an AI assistant for high level brainstorming related to outline structure and concept checkpoints. I wrote all prose myself. I verified claims against the cited sources and formatted citations manually. No AI generated text was copied into the submitted paper.",
  "assessment": "honest_disclosure",
  "evidence": "Student disclosed AI use for brainstorming/outline only, explicitly stated all prose written by themselves, verified sources manually, no AI text copied",
  "recommendation": "ACCEPTABLE"
}
"""

        user_prompt = f"""Analyze this student submission for AI usage disclosures.

# Academic Integrity Policy Context
Students must disclose any AI tool usage (ChatGPT, Copilot, Gemini, Claude, etc.)
- **Acceptable**: Brainstorming, outlining, idea organization, concept checkpoints
- **Unacceptable**: Direct copying AI-generated text without disclosure

{few_shot_examples}

# Submission Text to Analyze
{text}

# Your Task
Search for explicit statements where the student discusses AI tool usage. Follow the pattern shown in the examples above.

Return JSON in this exact format:
{{
  "disclosure_found": true or false,
  "disclosure_type": "none" or "brainstorming" or "editing" or "writing" or "unclear",
  "ai_tools_mentioned": ["ChatGPT", "Copilot", ...] or [],
  "disclosure_statement": "exact quote from submission" or null,
  "assessment": "honest_disclosure" or "no_disclosure" or "suspicious_disclosure" or "full_ai_generation",
  "evidence": "brief explanation of what you found",
  "recommendation": "ACCEPTABLE" or "NEEDS_REVIEW" or "VIOLATION"
}}

IMPORTANT RULES:
- Only report if you find EXPLICIT mentions of AI use (like the examples above)
- Look for sections titled "AI Usage Disclosure", "Author's note", or similar
- Look for phrases like "I used ChatGPT", "AI assistance", "I used an AI assistant"
- Be conservative - if no clear disclosure found, return "disclosure_found": false
- Do NOT guess or assume AI use without explicit statement
- If student only MENTIONS AI tools in content (not disclosure), that's NOT a disclosure
"""

        try:
            # Add timeout and better parameters for more reliable response
            result = llm_client.generate(
                system_prompt=system_prompt,
                prompt=user_prompt,
                temperature=0.1,  # Low temperature for more consistent JSON
                max_tokens=1000   # Limit response length
            )
            
            # Check if generation was successful
            if not result.get("success"):
                error_msg = result.get("error", "LLM generation failed")
                print(f"AI disclosure analysis failed: {error_msg}")
                return {
                    "disclosure_found": False,
                    "error": error_msg,
                    "recommendation": "ERROR",
                    "evidence": f"LLM generation error: {error_msg}"
                }
            
            # Extract the actual response text
            response = result.get("response", "")
            
            # Check for empty response
            if not response or not response.strip():
                print("AI disclosure analysis: Empty response from LLM")
                return {
                    "disclosure_found": False,
                    "error": "Empty response from LLM",
                    "recommendation": "ERROR",
                    "evidence": "LLM returned empty response"
                }
            
            # Parse JSON response (handle potential markdown code blocks)
            response_clean = response.strip()
            
            # Strategy 1: Extract from markdown code block
            if response_clean.startswith("```"):
                json_match = re.search(
                    r"```(?:json)?\s*(\{.*\})\s*```", response_clean, re.DOTALL
                )
                if json_match:
                    response_clean = json_match.group(1)
            # Strategy 2: Find first complete JSON object
            elif '{' in response_clean:
                json_start = response_clean.find('{')
                brace_count = 0
                for i, char in enumerate(response_clean[json_start:], start=json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            response_clean = response_clean[json_start:i+1]
                            break
            
            # Try to parse JSON
            try:
                parsed_result = json.loads(response_clean)
                
                # Validate required fields
                if not isinstance(parsed_result, dict):
                    raise ValueError("Response is not a JSON object")
                
                # Ensure all required fields exist with defaults
                parsed_result.setdefault("disclosure_found", False)
                parsed_result.setdefault("disclosure_type", "none")
                parsed_result.setdefault("ai_tools_mentioned", [])
                parsed_result.setdefault("disclosure_statement", None)
                parsed_result.setdefault("assessment", "no_disclosure")
                parsed_result.setdefault("evidence", "No evidence found")
                parsed_result.setdefault("recommendation", "NOT_CHECKED")
                
                return parsed_result
                
            except json.JSONDecodeError as e:
                print(f"AI disclosure JSON parse error: {e}")
                print(f"Response (first 200 chars): {response_clean[:200]}")
                return {
                    "disclosure_found": False,
                    "error": f"JSON parse error: {str(e)}",
                    "recommendation": "ERROR",
                    "evidence": "Failed to parse LLM response as JSON"
                }
            except ValueError as e:
                print(f"AI disclosure validation error: {e}")
                return {
                    "disclosure_found": False,
                    "error": str(e),
                    "recommendation": "ERROR",
                    "evidence": "Invalid response format"
                }
                
        except Exception as e:
            print(f"AI disclosure unexpected error: {e}")
            return {
                "disclosure_found": False,
                "error": str(e),
                "recommendation": "ERROR",
                "evidence": f"Unexpected error: {str(e)}"
            }

