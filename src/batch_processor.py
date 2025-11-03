"""
Batch Processor - Handle multiple submissions with concurrent processing
"""

import os
import time
from typing import List, Dict, Callable, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.document_parser import DocumentParser
from src.grading_engine import GradingEngine


class BatchProcessor:
    """Process multiple submissions in batch"""
    
    def __init__(self, grading_engine: GradingEngine, max_workers: int = 3):
        self.grading_engine = grading_engine
        self.document_parser = DocumentParser()
        self.max_workers = max_workers
        self.current_batch = []
        self.results = []
    
    def process_batch(
        self,
        file_paths: List[str],
        assignment_instruction: str,
        grading_criteria: str,
        output_format: str = "letter",
        max_score: int = 100,
        ai_keywords: str = "",
        additional_requirements: str = "",
        temperature: float = 0.3,
        progress_callback: Optional[Callable] = None,
        check_plagiarism: bool = False
    ) -> List[Dict]:
        """
        Process multiple submissions in batch
        
        Args:
            file_paths: List of file paths to grade
            assignment_instruction: Assignment description
            grading_criteria: Grading rubric
            output_format: 'letter' or 'numeric'
            max_score: Maximum score for numeric grading
            ai_keywords: Keywords to detect AI usage
            additional_requirements: Extra grading requirements
            temperature: LLM temperature setting
            progress_callback: Function to call with progress updates
            check_plagiarism: Whether to check for plagiarism
            
        Returns:
            List of grading results
        """
        self.results = []
        self.current_batch = []
        total_files = len(file_paths)
        
        # First, parse all documents
        if progress_callback:
            progress_callback(0, total_files, "Parsing documents...")
        
        parsed_docs = []
        for i, file_path in enumerate(file_paths):
            parse_result = self.document_parser.parse_file(file_path)
            parsed_docs.append({
                "file_path": file_path,
                "filename": parse_result.get('filename', Path(file_path).name),
                "text": parse_result.get('text', ''),
                "parse_success": parse_result.get('success', False),
                "parse_error": parse_result.get('error', ''),
                "format": parse_result.get('format', ''),
                "size": parse_result.get('size', 0)
            })
            
            if progress_callback:
                progress_callback(i + 1, total_files, f"Parsed {i + 1}/{total_files} documents")
        
        self.current_batch = parsed_docs
        
        # Now grade all submissions
        if progress_callback:
            progress_callback(0, total_files, "Grading submissions...")
        
        def grade_single(doc_data, index):
            """Grade a single document"""
            if not doc_data['parse_success']:
                return {
                    "index": index,
                    "filename": doc_data['filename'],
                    "success": False,
                    "error": f"Parse error: {doc_data['parse_error']}",
                    "grade": "N/A",
                    "text": "",
                    "grading_result": None
                }
            
            # Grade the submission
            grading_result = self.grading_engine.grade_submission(
                submission_text=doc_data['text'],
                assignment_instruction=assignment_instruction,
                grading_criteria=grading_criteria,
                output_format=output_format,
                max_score=max_score,
                ai_keywords=ai_keywords,
                additional_requirements=additional_requirements,
                temperature=temperature,
                keep_context=False  # Always clear context for batch
            )
            
            if grading_result.get('success'):
                parsed = grading_result['parsed_result']
                return {
                    "index": index,
                    "filename": doc_data['filename'],
                    "success": True,
                    "grade": parsed.get('grade', 'N/A'),
                    "detailed_feedback": parsed.get('detailed_feedback', ''),
                    "student_feedback": parsed.get('student_feedback', ''),
                    "strengths": parsed.get('strengths', []),
                    "weaknesses": parsed.get('weaknesses', []),
                    "confidence": parsed.get('confidence', 'medium'),
                    "text": doc_data['text'],
                    "grading_result": grading_result,
                    "ai_keywords_found": parsed.get('ai_keywords_found', [])
                }
            else:
                return {
                    "index": index,
                    "filename": doc_data['filename'],
                    "success": False,
                    "error": grading_result.get('error', 'Unknown error'),
                    "grade": "N/A",
                    "text": doc_data['text'],
                    "grading_result": None
                }
        
        # Process with thread pool for concurrent grading
        graded_results = [None] * total_files
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(grade_single, doc, i): i 
                for i, doc in enumerate(parsed_docs)
            }
            
            completed = 0
            for future in as_completed(future_to_index):
                result = future.result()
                graded_results[result['index']] = result
                completed += 1
                
                if progress_callback:
                    progress_callback(
                        completed, 
                        total_files, 
                        f"Graded {completed}/{total_files} submissions"
                    )
        
        self.results = graded_results
        
        # Optionally check for plagiarism
        plagiarism_results = []
        if check_plagiarism:
            if progress_callback:
                progress_callback(0, 1, "Checking for plagiarism...")
            
            from src.plagiarism_checker import PlagiarismChecker
            checker = PlagiarismChecker()
            
            # Extract texts from successful gradings
            texts = []
            filenames = []
            for result in graded_results:
                if result['success'] and result.get('text'):
                    texts.append(result['text'])
                    filenames.append(result['filename'])
            
            if len(texts) > 1:
                plagiarism_results = checker.check_batch(texts, filenames)
            
            if progress_callback:
                progress_callback(1, 1, "Plagiarism check complete")
        
        # Add plagiarism info to results
        for i, result in enumerate(graded_results):
            result['plagiarism_pairs'] = []
            for plag in plagiarism_results:
                if result['filename'] in [plag['file1'], plag['file2']]:
                    result['plagiarism_pairs'].append(plag)
        
        if progress_callback:
            progress_callback(total_files, total_files, "Batch processing complete!")
        
        return graded_results
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics for the batch"""
        if not self.results:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "grade_distribution": {}
            }
        
        successful = sum(1 for r in self.results if r.get('success'))
        failed = len(self.results) - successful
        
        # Grade distribution
        grade_dist = {}
        for result in self.results:
            if result.get('success'):
                grade = result.get('grade', 'N/A')
                grade_dist[grade] = grade_dist.get(grade, 0) + 1
        
        return {
            "total": len(self.results),
            "successful": successful,
            "failed": failed,
            "grade_distribution": grade_dist,
            "success_rate": f"{(successful / len(self.results) * 100):.1f}%"
        }
    
    def export_results(self, output_file: str, format: str = 'csv') -> bool:
        """Export results to file"""
        try:
            if format == 'csv':
                return self._export_csv(output_file)
            elif format == 'json':
                return self._export_json(output_file)
            else:
                return False
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def _export_csv(self, output_file: str) -> bool:
        """Export as CSV"""
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Filename', 'Grade', 'Confidence', 'Detailed Feedback', 
                'Student Feedback', 'Strengths', 'Weaknesses', 
                'AI Keywords Found', 'Status', 'Error'
            ])
            
            for result in self.results:
                writer.writerow([
                    result.get('filename', ''),
                    result.get('grade', 'N/A'),
                    result.get('confidence', 'N/A'),
                    result.get('detailed_feedback', '')[:500],  # Truncate
                    result.get('student_feedback', '')[:500],
                    '; '.join(result.get('strengths', [])),
                    '; '.join(result.get('weaknesses', [])),
                    '; '.join(result.get('ai_keywords_found', [])),
                    'Success' if result.get('success') else 'Failed',
                    result.get('error', '')
                ])
        
        return True
    
    def _export_json(self, output_file: str) -> bool:
        """Export as JSON"""
        import json
        
        # Simplify results for JSON (remove full grading_result objects)
        simplified_results = []
        for result in self.results:
            simplified = {
                "filename": result.get('filename'),
                "success": result.get('success'),
                "grade": result.get('grade'),
                "detailed_feedback": result.get('detailed_feedback'),
                "student_feedback": result.get('student_feedback'),
                "strengths": result.get('strengths'),
                "weaknesses": result.get('weaknesses'),
                "confidence": result.get('confidence'),
                "ai_keywords_found": result.get('ai_keywords_found'),
                "plagiarism_pairs": result.get('plagiarism_pairs'),
                "error": result.get('error')
            }
            simplified_results.append(simplified)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(simplified_results, f, indent=2, ensure_ascii=False)
        
        return True

