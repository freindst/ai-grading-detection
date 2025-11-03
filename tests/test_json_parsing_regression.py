"""
JSON Parsing Regression Test

This test ensures that the JSON parser correctly handles the user's exact JSON format
and maintains backward compatibility after any changes to the parsing logic.

IMPORTANT: Run this test after ANY changes to:
- src/grading_engine.py (especially parse_grading_output, _build_parsed_result, _extract_fields_from_failed_json)
- src/output_parser.py
- Any JSON parsing logic

This test uses the exact JSON structure that was reported as failing, ensuring
we don't regress on this specific case.

Usage:
    python3 tests/test_json_parsing_regression.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.grading_engine import GradingEngine


# User's exact JSON from the error report (November 2025)
# This is the canonical test case - if this fails, parsing has regressed
USER_JSON_TEST_CASE = """{
  "grade": "16",
  "detailed_feedback": "The student's submission demonstrates a good understanding of the comparison between paper-based and digital calendars, as well as shared wall planners and shared web-based calendars. The explanation of the main concepts and metaphors used in each type is clear and detailed. However, there are some areas where the student could improve.\\n\\nThe evolution and functionality section could be more detailed, explaining how specific features of paper-based calendars have influenced digital designs and what new features were added beyond automatic reminders and notifications, event sharing, collaboration, integration with emails, contacts, and to-do lists, and cross-synchronization across devices.\\n\\nThe student also could have provided more examples of confusing aspects of the conceptual models, explaining why they are confusing and how they might be improved.\\n\\nLastly, the personal reflection section is well-written but could benefit from a more in-depth analysis of the pros and cons of using Google Calendar specifically, beyond just stating that it is convenient and environmentally friendly.\\n\\nOverall, the writing and organization are clear and free of major grammar or spelling errors.",
  "student_feedback": "Great job comparing paper-based and digital calendars! Your explanation of how time is conceptualized in each is clear and detailed. However, consider providing more examples of confusing aspects of the conceptual models and analyzing the pros and cons of using Google Calendar specifically in your personal reflection.",
  "strengths": ["Clear comparison between paper-based and digital calendars", "Detailed explanation of concepts and metaphors"],
  "weaknesses": ["Could provide more examples of confusing aspects of conceptual models", "Personal reflection could be more in-depth"],
  "deductions": [
    {"reason": "Lacks detail in evolution and functionality section", "points": 2},
    {"reason": "Personal reflection could benefit from a more in-depth analysis", "points": 1}
  ],
  "confidence": "high"
}"""

# Test cases with different formats
TEST_CASES = [
    {
        "name": "Plain JSON (user's exact format)",
        "input": USER_JSON_TEST_CASE,
        "expected_grade": "16",
        "expected_method": "json",
        "min_feedback_length": 1000
    },
    {
        "name": "JSON with surrounding text",
        "input": f"""Here is my grading analysis:

{USER_JSON_TEST_CASE}

This evaluation provides comprehensive feedback on the student's work.""",
        "expected_grade": "16",
        "expected_method": "json",
        "min_feedback_length": 1000
    },
    {
        "name": "JSON in markdown code block",
        "input": f"""Here is the grading result:

```json
{USER_JSON_TEST_CASE}
```

I hope this helps.""",
        "expected_grade": "16",
        "expected_method": "json",
        "min_feedback_length": 1000
    }
]


def run_regression_test():
    """
    Run regression tests for JSON parsing.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("=" * 80)
    print("JSON PARSING REGRESSION TEST")
    print("=" * 80)
    print("Testing parser with user's exact JSON format from error report")
    print("This ensures backward compatibility after parser changes")
    print("=" * 80)
    
    # Create a minimal GradingEngine (we don't need LLM client for parsing)
    class MockLLMClient:
        pass
    
    engine = GradingEngine(MockLLMClient())
    
    all_passed = True
    passed_count = 0
    failed_count = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}/{len(TEST_CASES)}: {test_case['name']}")
        print(f"{'=' * 80}")
        
        try:
            result = engine.parse_grading_output(test_case['input'])
            
            # Check parse method
            parse_method = result.get('parse_method', 'unknown')
            if parse_method != test_case['expected_method']:
                print(f"❌ FAIL: Expected parse_method '{test_case['expected_method']}', got '{parse_method}'")
                all_passed = False
                failed_count += 1
                continue
            
            # Check grade extraction
            grade = result.get('grade', 'MISSING')
            if grade != test_case['expected_grade']:
                print(f"❌ FAIL: Expected grade '{test_case['expected_grade']}', got '{grade}'")
                all_passed = False
                failed_count += 1
                continue
            
            # Check feedback fields
            detailed_feedback = result.get('detailed_feedback', '')
            student_feedback = result.get('student_feedback', '')
            
            if len(detailed_feedback) < test_case['min_feedback_length']:
                print(f"❌ FAIL: detailed_feedback too short ({len(detailed_feedback)} chars, expected >= {test_case['min_feedback_length']})")
                all_passed = False
                failed_count += 1
                continue
            
            if not student_feedback or len(student_feedback) < 50:
                print(f"❌ FAIL: student_feedback missing or too short ({len(student_feedback)} chars)")
                all_passed = False
                failed_count += 1
                continue
            
            # Check if feedback fields contain JSON (should be parsed text, not JSON)
            if detailed_feedback.strip().startswith('{') and '"grade"' in detailed_feedback:
                print(f"❌ FAIL: detailed_feedback contains raw JSON instead of parsed text")
                print(f"   First 200 chars: {detailed_feedback[:200]}")
                all_passed = False
                failed_count += 1
                continue
            
            if student_feedback.strip().startswith('{') and '"grade"' in student_feedback:
                print(f"❌ FAIL: student_feedback contains raw JSON instead of parsed text")
                print(f"   First 200 chars: {student_feedback[:200]}")
                all_passed = False
                failed_count += 1
                continue
            
            # Check strengths/weaknesses/deductions
            strengths = result.get('strengths', [])
            weaknesses = result.get('weaknesses', [])
            deductions = result.get('deductions', [])
            
            if not isinstance(strengths, list) or len(strengths) < 1:
                print(f"⚠️  WARNING: strengths missing or empty (got: {strengths})")
            
            if not isinstance(weaknesses, list) or len(weaknesses) < 1:
                print(f"⚠️  WARNING: weaknesses missing or empty (got: {weaknesses})")
            
            if not isinstance(deductions, list) or len(deductions) < 1:
                print(f"⚠️  WARNING: deductions missing or empty (got: {deductions})")
            
            # All checks passed
            print(f"✅ PASS: Grade '{grade}' extracted correctly")
            print(f"   Parse method: {parse_method}")
            print(f"   Detailed feedback: {len(detailed_feedback)} chars")
            print(f"   Student feedback: {len(student_feedback)} chars")
            print(f"   Strengths: {len(strengths)} items")
            print(f"   Weaknesses: {len(weaknesses)} items")
            print(f"   Deductions: {len(deductions)} items")
            passed_count += 1
            
        except Exception as e:
            print(f"❌ EXCEPTION: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
            failed_count += 1
    
    # Summary
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total tests: {len(TEST_CASES)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    
    if all_passed:
        print(f"\n✅ ALL TESTS PASSED - Parser is backward compatible")
        return True
    else:
        print(f"\n❌ SOME TESTS FAILED - Parser may have regressed")
        return False


if __name__ == "__main__":
    success = run_regression_test()
    sys.exit(0 if success else 1)

