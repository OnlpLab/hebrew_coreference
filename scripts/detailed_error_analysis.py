#!/usr/bin/env python3
"""
Detailed Error Analysis for Hebrew Coreference Resolution

This script provides in-depth error analysis including:
- Qualitative case studies
- Error pattern analysis
- Cross-approach comparison
- Specific error categories for Hebrew
- Recommendations for improvement
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from collections import defaultdict, Counter
import argparse
import re
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

@dataclass
class DetailedErrorCase:
    """Detailed error case with Hebrew-specific analysis"""
    doc_key: str
    error_type: str
    gold_cluster: List[List[int]]
    predicted_cluster: Optional[List[List[int]]]
    gold_text: str
    predicted_text: Optional[str]
    context: str
    severity: str
    hebrew_specific_issues: List[str]  # Hebrew-specific error patterns
    error_category: str  # e.g., "pronoun_resolution", "named_entity", "definite_article"
    notes: str = ""

class HebrewErrorAnalyzer:
    """Specialized error analyzer for Hebrew coreference"""
    
    def __init__(self):
        # Hebrew-specific error patterns
        self.hebrew_patterns = {
            "definite_article": r"ה[א-ת]",
            "pronoun_patterns": r"(הוא|היא|הם|הן|אני|אתה|את|אנחנו|אתם|אתן)",
            "possessive_patterns": r"(של|שלה|שלו|שלהם|שלהן|שלי|שלך|שלכם|שלכן)",
            "demonstrative": r"(זה|זו|אלה|אלו|הזה|הזו|האלה|האלו)",
            "relative_clause": r"(ש|אשר|שאשר)",
        }
        
        # Error categories for Hebrew
        self.error_categories = {
            "pronoun_resolution": "Pronoun antecedent resolution",
            "named_entity": "Named entity coreference",
            "definite_article": "Definite article resolution",
            "possessive_construction": "Possessive construction resolution",
            "demonstrative": "Demonstrative pronoun resolution",
            "relative_clause": "Relative clause resolution",
            "quantifier": "Quantifier scope resolution",
            "generic_reference": "Generic reference resolution"
        }
    
    def analyze_hebrew_specific_errors(self, text: str, spans: List[List[int]]) -> List[str]:
        """Analyze Hebrew-specific error patterns"""
        issues = []
        
        # Extract text for each span
        span_texts = []
        for span in spans:
            if len(span) == 2:
                start, end = span
                # This would need actual token data
                span_texts.append(f"span_{start}_{end}")
        
        # Check for Hebrew-specific patterns
        for pattern_name, pattern in self.hebrew_patterns.items():
            for span_text in span_texts:
                if re.search(pattern, span_text):
                    issues.append(f"{pattern_name}_mismatch")
        
        return issues
    
    def categorize_hebrew_error(self, gold_cluster: List[List[int]], 
                               predicted_cluster: Optional[List[List[int]]]) -> str:
        """Categorize error based on Hebrew-specific patterns"""
        if not predicted_cluster:
            return "no_prediction"
        
        # Analyze the nature of the error
        gold_size = len(gold_cluster)
        pred_size = len(predicted_cluster)
        
        if gold_size == 1 and pred_size > 1:
            return "over_segmentation"
        elif gold_size > 1 and pred_size == 1:
            return "under_segmentation"
        elif gold_size == pred_size:
            return "wrong_association"
        else:
            return "size_mismatch"
    
    def generate_case_studies(self, error_cases: List[DetailedErrorCase]) -> Dict:
        """Generate detailed case studies for the paper"""
        case_studies = {
            "pronoun_resolution": [],
            "named_entity": [],
            "definite_article": [],
            "possessive_construction": [],
            "demonstrative": [],
            "relative_clause": [],
            "quantifier": [],
            "generic_reference": []
        }
        
        for case in error_cases:
            category = case.error_category
            if category in case_studies:
                case_studies[category].append(case)
        
        return case_studies
    
    def analyze_error_patterns(self, error_cases: List[DetailedErrorCase]) -> Dict:
        """Analyze patterns in errors"""
        patterns = {
            "error_type_distribution": Counter(),
            "severity_distribution": Counter(),
            "category_distribution": Counter(),
            "hebrew_issue_distribution": Counter(),
            "document_error_frequency": Counter()
        }
        
        for case in error_cases:
            patterns["error_type_distribution"][case.error_type] += 1
            patterns["severity_distribution"][case.severity] += 1
            patterns["category_distribution"][case.error_category] += 1
            patterns["document_error_frequency"][case.doc_key] += 1
            
            for issue in case.hebrew_specific_issues:
                patterns["hebrew_issue_distribution"][issue] += 1
        
        return patterns
    
    def generate_qualitative_analysis(self, error_cases: List[DetailedErrorCase]) -> str:
        """Generate qualitative analysis for the paper"""
        analysis = []
        analysis.append("# Qualitative Error Analysis for Hebrew Coreference Resolution\n")
        
        # Overall statistics
        total_errors = len(error_cases)
        analysis.append(f"## Overview\n")
        analysis.append(f"Total error cases analyzed: {total_errors}\n")
        
        # Error type analysis
        error_types = Counter(case.error_type for case in error_cases)
        analysis.append("## Error Type Distribution\n")
        for error_type, count in error_types.most_common():
            percentage = (count / total_errors) * 100
            analysis.append(f"- **{error_type.replace('_', ' ').title()}**: {count} ({percentage:.1f}%)")
        
        # Hebrew-specific analysis
        hebrew_issues = Counter()
        for case in error_cases:
            for issue in case.hebrew_specific_issues:
                hebrew_issues[issue] += 1
        
        if hebrew_issues:
            analysis.append("\n## Hebrew-Specific Error Patterns\n")
            for issue, count in hebrew_issues.most_common():
                percentage = (count / total_errors) * 100
                analysis.append(f"- **{issue.replace('_', ' ').title()}**: {count} ({percentage:.1f}%)")
        
        # Category analysis
        categories = Counter(case.error_category for case in error_cases)
        analysis.append("\n## Error Category Analysis\n")
        for category, count in categories.most_common():
            percentage = (count / total_errors) * 100
            analysis.append(f"- **{category.replace('_', ' ').title()}**: {count} ({percentage:.1f}%)")
        
        # Case studies
        case_studies = self.generate_case_studies(error_cases)
        analysis.append("\n## Representative Case Studies\n")
        
        for category, cases in case_studies.items():
            if cases:
                analysis.append(f"\n### {category.replace('_', ' ').title()}\n")
                # Show top 3 cases for each category
                for i, case in enumerate(cases[:3]):
                    analysis.append(f"**Case {i+1}**: {case.doc_key}")
                    analysis.append(f"- Error Type: {case.error_type}")
                    analysis.append(f"- Severity: {case.severity}")
                    analysis.append(f"- Hebrew Issues: {', '.join(case.hebrew_specific_issues)}")
                    analysis.append(f"- Notes: {case.notes}")
                    analysis.append("")
        
        return "\n".join(analysis)
    
    def create_detailed_visualizations(self, error_cases: List[DetailedErrorCase], output_dir: str):
        """Create detailed visualizations for Hebrew error analysis"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Error category distribution
        categories = Counter(case.error_category for case in error_cases)
        plt.figure(figsize=(12, 8))
        plt.pie(categories.values(), labels=categories.keys(), autopct='%1.1f%%')
        plt.title('Error Category Distribution')
        plt.tight_layout()
        plt.savefig(output_path / 'error_category_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Hebrew-specific issues
        hebrew_issues = Counter()
        for case in error_cases:
            for issue in case.hebrew_specific_issues:
                hebrew_issues[issue] += 1
        
        if hebrew_issues:
            plt.figure(figsize=(10, 6))
            issues, counts = zip(*hebrew_issues.most_common())
            plt.bar(issues, counts)
            plt.title('Hebrew-Specific Error Patterns')
            plt.xlabel('Error Pattern')
            plt.ylabel('Count')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_path / 'hebrew_error_patterns.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # Error severity by category
        severity_by_category = defaultdict(Counter)
        for case in error_cases:
            severity_by_category[case.error_category][case.severity] += 1
        
        if severity_by_category:
            categories = list(severity_by_category.keys())
            severities = ['high', 'medium', 'low']
            
            fig, ax = plt.subplots(figsize=(12, 8))
            x = np.arange(len(categories))
            width = 0.25
            
            for i, severity in enumerate(severities):
                counts = [severity_by_category[cat][severity] for cat in categories]
                ax.bar(x + i * width, counts, width, label=severity.title())
            
            ax.set_xlabel('Error Category')
            ax.set_ylabel('Count')
            ax.set_title('Error Severity by Category')
            ax.set_xticks(x + width)
            ax.set_xticklabels([cat.replace('_', ' ').title() for cat in categories])
            ax.legend()
            plt.tight_layout()
            plt.savefig(output_path / 'severity_by_category.png', dpi=300, bbox_inches='tight')
            plt.close()
    
    def generate_recommendations(self, error_cases: List[DetailedErrorCase]) -> str:
        """Generate recommendations for improvement"""
        recommendations = []
        recommendations.append("# Recommendations for Hebrew Coreference Resolution\n")
        
        # Analyze patterns to generate recommendations
        error_types = Counter(case.error_type for case in error_cases)
        categories = Counter(case.error_category for case in error_cases)
        hebrew_issues = Counter()
        for case in error_cases:
            for issue in case.hebrew_specific_issues:
                hebrew_issues[issue] += 1
        
        # Most common error types
        most_common_error = error_types.most_common(1)[0] if error_types else ("none", 0)
        most_common_category = categories.most_common(1)[0] if categories else ("none", 0)
        most_common_hebrew_issue = hebrew_issues.most_common(1)[0] if hebrew_issues else ("none", 0)
        
        recommendations.append("## Key Recommendations\n")
        
        # General recommendations
        recommendations.append("### General Improvements\n")
        recommendations.append("1. **Enhanced Tokenization**: Improve tokenization to better handle Hebrew morphological complexity")
        recommendations.append("2. **Context Window**: Increase context window to capture longer-range dependencies")
        recommendations.append("3. **Hebrew-Specific Features**: Incorporate Hebrew-specific linguistic features")
        
        # Category-specific recommendations
        recommendations.append("\n### Category-Specific Recommendations\n")
        
        if most_common_category[0] != "none":
            recommendations.append(f"1. **{most_common_category[0].replace('_', ' ').title()}**: Focus on improving {most_common_category[0]} resolution")
        
        if most_common_hebrew_issue[0] != "none":
            recommendations.append(f"2. **Hebrew Pattern**: Address {most_common_hebrew_issue[0]} pattern recognition")
        
        # Model-specific recommendations
        recommendations.append("\n### Model-Specific Recommendations\n")
        recommendations.append("1. **Neural Models**: Incorporate Hebrew morphological analysis")
        recommendations.append("2. **LLM Models**: Provide Hebrew-specific prompting strategies")
        recommendations.append("3. **Hybrid Approaches**: Combine neural and rule-based methods")
        
        return "\n".join(recommendations)

def main():
    parser = argparse.ArgumentParser(description="Perform detailed error analysis")
    parser.add_argument("--error_analysis_dir", default="outputs/error_analysis",
                       help="Directory containing error analysis results")
    parser.add_argument("--output_dir", default="outputs/detailed_error_analysis",
                       help="Output directory for detailed analysis")
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = HebrewErrorAnalyzer()
    
    # Load error cases from previous analysis
    error_analysis_dir = Path(args.error_analysis_dir)
    error_cases = []
    
    # Load error cases from JSON files
    for error_file in error_analysis_dir.glob("*_errors.json"):
        with open(error_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            # Convert to DetailedErrorCase
            detailed_case = DetailedErrorCase(
                doc_key=item["doc_key"],
                error_type=item["error_type"],
                gold_cluster=item["gold_cluster"],
                predicted_cluster=item["predicted_cluster"],
                gold_text=item.get("gold_text", ""),
                predicted_text=item.get("predicted_text", ""),
                context=item["context"],
                severity=item["severity"],
                hebrew_specific_issues=analyzer.analyze_hebrew_specific_errors(
                    item.get("gold_text", ""), item["gold_cluster"]
                ),
                error_category=analyzer.categorize_hebrew_error(
                    item["gold_cluster"], item["predicted_cluster"]
                ),
                notes=item.get("notes", "")
            )
            error_cases.append(detailed_case)
    
    if not error_cases:
        print("No error cases found to analyze!")
        return
    
    # Generate outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Generate qualitative analysis
    qualitative_analysis = analyzer.generate_qualitative_analysis(error_cases)
    with open(output_dir / "qualitative_analysis.md", 'w', encoding='utf-8') as f:
        f.write(qualitative_analysis)
    
    # Generate recommendations
    recommendations = analyzer.generate_recommendations(error_cases)
    with open(output_dir / "recommendations.md", 'w', encoding='utf-8') as f:
        f.write(recommendations)
    
    # Create detailed visualizations
    analyzer.create_detailed_visualizations(error_cases, str(output_dir))
    
    # Save detailed error patterns
    patterns = analyzer.analyze_error_patterns(error_cases)
    with open(output_dir / "error_patterns.json", 'w', encoding='utf-8') as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✓ Detailed error analysis complete! Results saved to {output_dir}")
    print(f"  - Qualitative analysis: {output_dir}/qualitative_analysis.md")
    print(f"  - Recommendations: {output_dir}/recommendations.md")
    print(f"  - Error patterns: {output_dir}/error_patterns.json")
    print(f"  - Visualizations: {output_dir}/*.png")

if __name__ == "__main__":
    main() 