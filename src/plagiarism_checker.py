"""
Plagiarism Checker - Simple similarity detection for batch submissions
"""

from typing import List, Dict, Tuple
from difflib import SequenceMatcher


class PlagiarismChecker:
    """Simple plagiarism detection using text similarity"""
    
    def __init__(self, threshold_high: float = 0.8, threshold_medium: float = 0.6):
        """
        Initialize plagiarism checker
        
        Args:
            threshold_high: Similarity threshold for high suspicion (80%+)
            threshold_medium: Similarity threshold for medium suspicion (60%+)
        """
        self.threshold_high = threshold_high
        self.threshold_medium = threshold_medium
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using SequenceMatcher
        
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        # Normalize texts (lowercase, strip whitespace)
        text1_norm = ' '.join(text1.lower().split())
        text2_norm = ' '.join(text2.lower().split())
        
        # Use SequenceMatcher for simple similarity
        matcher = SequenceMatcher(None, text1_norm, text2_norm)
        return matcher.ratio()
    
    def get_suspicion_level(self, similarity: float) -> str:
        """
        Determine suspicion level based on similarity score
        
        Returns:
            'high', 'medium', 'low', or 'none'
        """
        if similarity >= self.threshold_high:
            return 'high'
        elif similarity >= self.threshold_medium:
            return 'medium'
        elif similarity >= 0.4:
            return 'low'
        else:
            return 'none'
    
    def check_pair(self, text1: str, text2: str, file1: str, file2: str) -> Dict:
        """
        Check a pair of submissions for plagiarism
        
        Returns:
            Dict with similarity info and suspicion level
        """
        similarity = self.calculate_similarity(text1, text2)
        suspicion = self.get_suspicion_level(similarity)
        
        return {
            "file1": file1,
            "file2": file2,
            "similarity": round(similarity * 100, 2),
            "suspicion_level": suspicion,
            "flagged": suspicion in ['high', 'medium']
        }
    
    def check_batch(self, texts: List[str], filenames: List[str]) -> List[Dict]:
        """
        Check all pairs in a batch for plagiarism
        
        Args:
            texts: List of submission texts
            filenames: List of corresponding filenames
            
        Returns:
            List of plagiarism results for pairs with suspicion
        """
        results = []
        n = len(texts)
        
        # Compare each pair
        for i in range(n):
            for j in range(i + 1, n):
                result = self.check_pair(
                    texts[i], 
                    texts[j], 
                    filenames[i], 
                    filenames[j]
                )
                
                # Only include pairs with some level of suspicion
                if result['suspicion_level'] != 'none':
                    results.append(result)
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results
    
    def generate_report(self, plagiarism_results: List[Dict]) -> str:
        """
        Generate a human-readable plagiarism report
        
        Returns:
            Formatted report string
        """
        if not plagiarism_results:
            return "✅ No plagiarism detected in this batch."
        
        report = []
        report.append(f"⚠️ Plagiarism Check Results: {len(plagiarism_results)} suspicious pair(s) found\n")
        report.append("=" * 70)
        
        for i, result in enumerate(plagiarism_results, 1):
            icon = "🔴" if result['suspicion_level'] == 'high' else "🟡" if result['suspicion_level'] == 'medium' else "🟢"
            report.append(f"\n{icon} Pair #{i} - {result['suspicion_level'].upper()} Suspicion")
            report.append(f"   File 1: {result['file1']}")
            report.append(f"   File 2: {result['file2']}")
            report.append(f"   Similarity: {result['similarity']}%")
            
            if result['suspicion_level'] == 'high':
                report.append("   ⚠️  Recommend manual review - High similarity detected")
            elif result['suspicion_level'] == 'medium':
                report.append("   ⚠️  Moderate similarity - Consider checking")
        
        report.append("\n" + "=" * 70)
        report.append(f"\nTotal pairs checked: {len(plagiarism_results)}")
        high_count = sum(1 for r in plagiarism_results if r['suspicion_level'] == 'high')
        medium_count = sum(1 for r in plagiarism_results if r['suspicion_level'] == 'medium')
        report.append(f"High suspicion: {high_count} | Medium suspicion: {medium_count}")
        
        return "\n".join(report)
    
    def set_thresholds(self, high: float, medium: float):
        """Update similarity thresholds"""
        self.threshold_high = high
        self.threshold_medium = medium

