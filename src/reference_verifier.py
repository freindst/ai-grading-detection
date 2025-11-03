"""
Reference Verifier - Verify citations and references in submissions
"""

from typing import Dict, List
from src.web_search import WebSearch


class ReferenceVerifier:
    """Verify references and citations in student submissions"""
    
    def __init__(self):
        self.web_search = WebSearch()
    
    def verify_submission(self, submission_text: str, check_references: bool = True) -> Dict:
        """
        Verify all references in a submission
        
        Returns:
            Verification results
        """
        if not check_references:
            return {
                "enabled": False,
                "message": "Reference verification disabled"
            }
        
        verification = self.web_search.verify_submission_references(submission_text)
        report = self.web_search.generate_reference_report(verification)
        
        return {
            "enabled": True,
            "verification": verification,
            "report": report
        }
    
    def check_url_accessibility(self, url: str) -> Dict:
        """
        Check if a URL is accessible (basic check)
        
        Note: This is a placeholder. Full implementation would use requests
        to actually check URL accessibility
        """
        import re
        
        # Basic URL validation
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        is_valid_format = bool(re.match(url_pattern, url))
        
        return {
            "url": url,
            "valid_format": is_valid_format,
            "accessible": None,  # Would need actual HTTP request
            "status_code": None
        }
    
    def suggest_reference_improvements(self, verification_result: Dict) -> List[str]:
        """
        Suggest improvements for references
        
        Returns:
            List of suggestions
        """
        suggestions = []
        
        if not verification_result.get('enabled'):
            return suggestions
        
        verif = verification_result['verification']
        
        # No references found
        if verif['total_references'] == 0:
            suggestions.append("Consider adding citations to support your claims.")
        
        # URLs without proper citations
        if verif['urls_found'] > 0 and verif['citations_found'] == 0:
            suggestions.append("URLs found but no formal citations. Consider adding proper citations.")
        
        # Low verification rate
        if verif['citations_found'] > 0:
            verification_rate = verif['citations_verified'] / verif['citations_found']
            if verification_rate < 0.5:
                suggestions.append(f"Only {verif['citations_verified']}/{verif['citations_found']} citations could be verified. Check citation accuracy.")
        
        return suggestions

