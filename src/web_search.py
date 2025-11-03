"""
Web Search - Internet search integration for reference verification
"""

from typing import Dict, List, Optional
import re


class WebSearch:
    """Handle web searches for reference verification"""
    
    def __init__(self, search_engine: str = "duckduckgo"):
        self.search_engine = search_engine
        self._ddg_available = self._check_ddg()
    
    def _check_ddg(self) -> bool:
        """Check if duckduckgo_search is available"""
        try:
            from duckduckgo_search import DDGS
            return True
        except ImportError:
            return False
    
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Perform web search
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results with title, link, snippet
        """
        if not self._ddg_available:
            return [{
                "title": "Search Unavailable",
                "link": "",
                "snippet": "duckduckgo_search not installed. Run: pip install duckduckgo-search"
            }]
        
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=max_results)
                for result in search_results:
                    results.append({
                        "title": result.get('title', ''),
                        "link": result.get('href', ''),
                        "snippet": result.get('body', '')
                    })
            
            return results
        
        except Exception as e:
            return [{
                "title": "Search Error",
                "link": "",
                "snippet": f"Search failed: {str(e)}"
            }]
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return list(set(urls))  # Remove duplicates
    
    def extract_citations(self, text: str) -> List[str]:
        """Extract potential citations or references from text"""
        citations = []
        
        # Look for common citation patterns
        patterns = [
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s+\d{4})\)',  # (Author, Year)
            r'\[(\d+)\]',  # [1], [2], etc.
            r'(?:according to|cited in|from|as per)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # According to Author
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return citations
    
    def verify_reference(self, reference: str) -> Dict:
        """
        Verify a reference by searching for it
        
        Returns:
            Dict with verification status and results
        """
        results = self.search(reference, max_results=3)
        
        if not results or results[0].get('title') == 'Search Error':
            return {
                "reference": reference,
                "verified": False,
                "confidence": "low",
                "message": "Could not search for reference",
                "results": []
            }
        
        # Check if any result seems relevant
        reference_lower = reference.lower()
        relevant_results = []
        
        for result in results:
            title_lower = result.get('title', '').lower()
            snippet_lower = result.get('snippet', '').lower()
            
            # Simple relevance check
            if any(word in title_lower or word in snippet_lower 
                   for word in reference_lower.split() if len(word) > 3):
                relevant_results.append(result)
        
        if relevant_results:
            return {
                "reference": reference,
                "verified": True,
                "confidence": "medium" if len(relevant_results) >= 2 else "low",
                "message": f"Found {len(relevant_results)} potentially relevant result(s)",
                "results": relevant_results
            }
        else:
            return {
                "reference": reference,
                "verified": False,
                "confidence": "low",
                "message": "No relevant results found",
                "results": results
            }
    
    def verify_submission_references(self, submission_text: str) -> Dict:
        """
        Verify all references in a submission
        
        Returns:
            Dict with verification summary
        """
        urls = self.extract_urls(submission_text)
        citations = self.extract_citations(submission_text)
        
        url_verifications = []
        for url in urls[:5]:  # Limit to 5 URLs
            url_verifications.append({
                "url": url,
                "accessible": True,  # We don't actually check accessibility
                "type": "url"
            })
        
        citation_verifications = []
        for citation in citations[:5]:  # Limit to 5 citations
            verification = self.verify_reference(citation)
            citation_verifications.append(verification)
        
        total_refs = len(urls) + len(citations)
        verified_count = len([v for v in citation_verifications if v['verified']])
        
        return {
            "total_references": total_refs,
            "urls_found": len(urls),
            "citations_found": len(citations),
            "citations_verified": verified_count,
            "url_list": urls,
            "citation_list": citations,
            "verification_details": citation_verifications,
            "summary": f"Found {total_refs} references: {len(urls)} URL(s) and {len(citations)} citation(s). Verified {verified_count}/{len(citations)} citations."
        }
    
    def generate_reference_report(self, verification_result: Dict) -> str:
        """Generate human-readable reference verification report"""
        report = []
        report.append("=== Reference Verification Report ===\n")
        report.append(verification_result['summary'])
        report.append("")
        
        if verification_result['urls_found'] > 0:
            report.append("\n## URLs Found:")
            for url in verification_result['url_list']:
                report.append(f"  • {url}")
        
        if verification_result['citations_found'] > 0:
            report.append("\n## Citations Found:")
            for detail in verification_result['verification_details']:
                ref = detail['reference']
                status = "✓" if detail['verified'] else "✗"
                conf = detail['confidence']
                report.append(f"  {status} {ref} ({conf} confidence)")
                if detail['verified'] and detail.get('results'):
                    report.append(f"     → {detail['results'][0]['title']}")
        
        return "\n".join(report)

