import argparse
import sys
import os
from comparator import compare_specs, load_yaml
from report_generator import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description="OpenAPI Diff Tool")
    parser.add_argument("old_spec", help="Path to the old OpenAPI spec")
    parser.add_argument("new_spec", help="Path to the new OpenAPI spec")
    parser.add_argument("--format", choices=['markdown', 'docx'], default='markdown', help="Output format")
    parser.add_argument("--detail", choices=['synthetic', 'verbose'], default='synthetic', help="Level of detail")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--style", choices=['enterprise', 'impact', 'analytic'], default='enterprise', help="Visual style (docx only)")

    args = parser.parse_args()

    # Load specs
    try:
        spec1 = load_yaml(args.old_spec)
        spec2 = load_yaml(args.new_spec)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    # Compare
    diff = compare_specs(spec1, spec2)

    # Generate Report
    if args.format == 'markdown':
        generator = ReportGenerator()
        report = generator.generate(diff, format='markdown', detail=args.detail, output_file=args.output)
        
        if args.output:
            print(f"Report generated at {args.output}")
        else:
            print(report)
            
    elif args.format == 'docx':
        if args.style == 'impact':
            from impact_generator import ImpactDocxGenerator
            generator = ImpactDocxGenerator(spec1, spec2, diff)
            generator.generate(args.output or 'report_impact.docx')
        elif args.style == 'analytic':
            from analytic_generator import AnalyticDocxGenerator
            generator = AnalyticDocxGenerator(spec1, spec2, diff)
            generator.generate(args.output or 'report_analytic.docx')
        else:
            # Fallback or Enterprise (Legacy)
            from docx_generator import DocxReportGenerator
            generator = DocxReportGenerator(spec1, spec2, diff)
            generator.generate(args.output or 'report.docx')

if __name__ == "__main__":
    main()
