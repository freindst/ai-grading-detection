"""
Report Generator - Generate comprehensive grading reports
"""

from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """Generate comprehensive reports from grading results"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_text_report(
        self,
        results: List[Dict],
        assignment_name: str = "Assignment",
        include_feedback: bool = True
    ) -> str:
        """
        Generate comprehensive text report
        
        Returns:
            Report text
        """
        report = []
        report.append("=" * 70)
        report.append(f"GRADING REPORT: {assignment_name}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 70)
        report.append("")
        
        # Summary statistics
        total = len(results)
        successful = sum(1 for r in results if r.get('success'))
        
        report.append("SUMMARY")
        report.append("-" * 70)
        report.append(f"Total Submissions: {total}")
        report.append(f"Successfully Graded: {successful}")
        report.append(f"Failed: {total - successful}")
        report.append(f"Success Rate: {(successful/total*100):.1f}%")
        report.append("")
        
        # Grade distribution
        grade_dist = {}
        for result in results:
            if result.get('success'):
                grade = result.get('grade', 'N/A')
                grade_dist[grade] = grade_dist.get(grade, 0) + 1
        
        report.append("GRADE DISTRIBUTION")
        report.append("-" * 70)
        for grade, count in sorted(grade_dist.items()):
            percentage = (count / successful * 100) if successful > 0 else 0
            bar = "█" * int(percentage / 5)
            report.append(f"{grade:5s}: {count:3d} ({percentage:5.1f}%) {bar}")
        report.append("")
        
        # Individual results
        report.append("INDIVIDUAL RESULTS")
        report.append("=" * 70)
        report.append("")
        
        for i, result in enumerate(results, 1):
            report.append(f"[{i}] {result.get('filename', 'Unknown')}")
            report.append("-" * 70)
            
            if result.get('success'):
                report.append(f"Grade: {result.get('grade', 'N/A')}")
                report.append(f"Confidence: {result.get('confidence', 'N/A')}")
                
                if result.get('strengths'):
                    report.append("\nStrengths:")
                    for strength in result['strengths']:
                        report.append(f"  + {strength}")
                
                if result.get('weaknesses'):
                    report.append("\nWeaknesses:")
                    for weakness in result['weaknesses']:
                        report.append(f"  - {weakness}")
                
                if include_feedback and result.get('student_feedback'):
                    report.append("\nStudent Feedback:")
                    report.append(f"  {result['student_feedback']}")
                
                if result.get('ai_keywords_found'):
                    report.append(f"\n⚠️ AI Keywords Detected: {', '.join(result['ai_keywords_found'])}")
                
                if result.get('plagiarism_pairs'):
                    max_sim = max((p['similarity'] for p in result['plagiarism_pairs']), default=0)
                    if max_sim >= 60:
                        report.append(f"\n⚠️ Plagiarism Detected: {max_sim}% similarity")
            else:
                report.append(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            report.append("")
        
        return "\n".join(report)
    
    def save_text_report(
        self,
        results: List[Dict],
        output_file: str,
        assignment_name: str = "Assignment"
    ) -> tuple[bool, str]:
        """Save text report to file"""
        try:
            output_path = self.output_dir / output_file
            report_text = self.generate_text_report(results, assignment_name)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            
            return True, f"Report saved to {output_path}"
        
        except Exception as e:
            return False, f"Failed to save report: {str(e)}"
    
    def generate_pdf_report(
        self,
        results: List[Dict],
        output_file: str,
        assignment_name: str = "Assignment"
    ) -> tuple[bool, str]:
        """Generate PDF report"""
        try:
            try:
                from fpdf import FPDF
            except ImportError:
                return False, "fpdf2 not installed. Run: pip install fpdf2"
            
            output_path = self.output_dir / output_file
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            
            # Title
            pdf.cell(0, 10, f"Grading Report: {assignment_name}", ln=True, align="C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
            pdf.ln(5)
            
            # Summary
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Summary", ln=True)
            pdf.set_font("Arial", "", 11)
            
            total = len(results)
            successful = sum(1 for r in results if r.get('success'))
            
            pdf.cell(0, 8, f"Total Submissions: {total}", ln=True)
            pdf.cell(0, 8, f"Successfully Graded: {successful}", ln=True)
            pdf.cell(0, 8, f"Success Rate: {(successful/total*100):.1f}%", ln=True)
            pdf.ln(5)
            
            # Grade distribution
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Grade Distribution", ln=True)
            pdf.set_font("Arial", "", 11)
            
            grade_dist = {}
            for result in results:
                if result.get('success'):
                    grade = result.get('grade', 'N/A')
                    grade_dist[grade] = grade_dist.get(grade, 0) + 1
            
            for grade, count in sorted(grade_dist.items()):
                percentage = (count / successful * 100) if successful > 0 else 0
                pdf.cell(0, 8, f"{grade}: {count} ({percentage:.1f}%)", ln=True)
            
            pdf.ln(10)
            
            # Individual results (summary only for PDF)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Individual Results", ln=True)
            pdf.set_font("Arial", "", 10)
            
            for i, result in enumerate(results, 1):
                if pdf.get_y() > 250:  # New page if near bottom
                    pdf.add_page()
                
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 8, f"{i}. {result.get('filename', 'Unknown')}", ln=True)
                pdf.set_font("Arial", "", 10)
                
                if result.get('success'):
                    pdf.cell(0, 6, f"Grade: {result.get('grade', 'N/A')} (Confidence: {result.get('confidence', 'N/A')})", ln=True)
                else:
                    pdf.cell(0, 6, f"Error: {result.get('error', 'Unknown')[:50]}", ln=True)
                
                pdf.ln(3)
            
            pdf.output(str(output_path))
            return True, f"PDF report saved to {output_path}"
        
        except Exception as e:
            return False, f"PDF generation failed: {str(e)}"
    
    def generate_html_report(
        self,
        results: List[Dict],
        output_file: str,
        assignment_name: str = "Assignment"
    ) -> tuple[bool, str]:
        """Generate HTML report"""
        try:
            output_path = self.output_dir / output_file
            
            # Calculate statistics
            total = len(results)
            successful = sum(1 for r in results if r.get('success'))
            
            grade_dist = {}
            for result in results:
                if result.get('success'):
                    grade = result.get('grade', 'N/A')
                    grade_dist[grade] = grade_dist.get(grade, 0) + 1
            
            # Generate HTML
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Grading Report: {assignment_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #e8f5e9; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .grade-chart {{ margin: 20px 0; }}
        .grade-bar {{ background: #4CAF50; height: 25px; margin: 5px 0; color: white; padding: 5px; border-radius: 3px; }}
        .result-card {{ border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .success {{ border-left: 4px solid #4CAF50; }}
        .failed {{ border-left: 4px solid #f44336; }}
        .grade {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .strengths {{ color: #4CAF50; }}
        .weaknesses {{ color: #ff5722; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Grading Report: {assignment_name}</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p><strong>Total Submissions:</strong> {total}</p>
            <p><strong>Successfully Graded:</strong> {successful}</p>
            <p><strong>Failed:</strong> {total - successful}</p>
            <p><strong>Success Rate:</strong> {(successful/total*100):.1f}%</p>
        </div>
        
        <h2>Grade Distribution</h2>
        <div class="grade-chart">
"""
            
            for grade, count in sorted(grade_dist.items()):
                percentage = (count / successful * 100) if successful > 0 else 0
                width = int(percentage * 5)
                html += f'            <div class="grade-bar" style="width: {width}px;">{grade}: {count} ({percentage:.1f}%)</div>\n'
            
            html += """
        </div>
        
        <h2>Individual Results</h2>
"""
            
            for i, result in enumerate(results, 1):
                success_class = "success" if result.get('success') else "failed"
                html += f'        <div class="result-card {success_class}">\n'
                html += f'            <h3>{i}. {result.get("filename", "Unknown")}</h3>\n'
                
                if result.get('success'):
                    html += f'            <p class="grade">Grade: {result.get("grade", "N/A")}</p>\n'
                    html += f'            <p><strong>Confidence:</strong> {result.get("confidence", "N/A")}</p>\n'
                    
                    if result.get('strengths'):
                        html += '            <p class="strengths"><strong>Strengths:</strong></p><ul>\n'
                        for strength in result['strengths']:
                            html += f'                <li>{strength}</li>\n'
                        html += '            </ul>\n'
                    
                    if result.get('weaknesses'):
                        html += '            <p class="weaknesses"><strong>Weaknesses:</strong></p><ul>\n'
                        for weakness in result['weaknesses']:
                            html += f'                <li>{weakness}</li>\n'
                        html += '            </ul>\n'
                else:
                    html += f'            <p><strong>Error:</strong> {result.get("error", "Unknown error")}</p>\n'
                
                html += '        </div>\n'
            
            html += """
    </div>
</body>
</html>
"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return True, f"HTML report saved to {output_path}"
        
        except Exception as e:
            return False, f"HTML generation failed: {str(e)}"

