"""
Convert markdown files to PDFs with content-based naming.
Uses markdown + reportlab for PDF generation.
"""
import os
import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import markdown
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib import colors
except ImportError:
    print("Installing required packages...")
    os.system("pip install markdown reportlab")
    import markdown
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib import colors


def markdown_to_paragraphs(md_content: str, styles):
    """Convert markdown content to ReportLab Paragraph objects"""
    from html import unescape
    
    # Convert markdown to HTML first
    md = markdown.Markdown(extensions=['extra', 'tables'])
    html_content = md.convert(md_content)
    
    # Parse HTML and convert to paragraphs
    paragraphs = []
    lines = html_content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            paragraphs.append(Spacer(1, 0.1*inch))
            continue
        
        # Handle headings
        if line.startswith('<h1>'):
            text = re.sub(r'<[^>]+>', '', line)
            paragraphs.append(Paragraph(unescape(text), styles['Heading1']))
            paragraphs.append(Spacer(1, 0.2*inch))
        elif line.startswith('<h2>'):
            text = re.sub(r'<[^>]+>', '', line)
            paragraphs.append(Paragraph(unescape(text), styles['Heading2']))
            paragraphs.append(Spacer(1, 0.15*inch))
        elif line.startswith('<h3>'):
            text = re.sub(r'<[^>]+>', '', line)
            paragraphs.append(Paragraph(unescape(text), styles['Heading3']))
            paragraphs.append(Spacer(1, 0.1*inch))
        elif line.startswith('<p>'):
            text = re.sub(r'<[^>]+>', '', line)
            if text:
                paragraphs.append(Paragraph(unescape(text), styles['Normal']))
                paragraphs.append(Spacer(1, 0.1*inch))
        elif line.startswith('<li>'):
            text = re.sub(r'<[^>]+>', '', line)
            if text:
                paragraphs.append(Paragraph(f"• {unescape(text)}", styles['Normal']))
                paragraphs.append(Spacer(1, 0.05*inch))
        elif line.startswith('<strong>') or '<strong>' in line:
            text = re.sub(r'<[^>]+>', '', line)
            if text:
                paragraphs.append(Paragraph(unescape(text), styles['Heading3']))
                paragraphs.append(Spacer(1, 0.1*inch))
        else:
            # Regular text
            text = re.sub(r'<[^>]+>', '', line)
            if text and len(text) > 3:
                paragraphs.append(Paragraph(unescape(text), styles['Normal']))
                paragraphs.append(Spacer(1, 0.1*inch))
    
    return paragraphs


def convert_md_to_pdf(md_path: Path, output_pdf_path: Path, pdf_name: str = None):
    """
    Convert markdown file to PDF.
    
    Args:
        md_path: Path to markdown file
        output_pdf_path: Path to output PDF file
        pdf_name: Desired PDF filename (unused, kept for compatibility)
    """
    print(f"\nConverting: {md_path.name}")
    
    # Read markdown content
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(output_pdf_path),
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles - modify existing styles
    styles['Heading1'].fontSize = 24
    styles['Heading1'].textColor = colors.HexColor('#2c3e50')
    styles['Heading1'].spaceAfter = 12
    
    styles['Heading2'].fontSize = 18
    styles['Heading2'].textColor = colors.HexColor('#34495e')
    styles['Heading2'].spaceAfter = 10
    
    # Convert markdown to paragraphs
    try:
        story = markdown_to_paragraphs(md_content, styles)
        
        # Build PDF
        doc.build(story)
        print(f"✅ Created: {output_pdf_path.name}")
        return True
    except Exception as e:
        print(f"❌ Error converting {md_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main conversion function"""
    # Define paths
    md_dir = Path("data/md files")
    pdf_dir = Path("data/pdfs")
    
    # Ensure PDF directory exists
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Mapping of MD files to PDF names (based on content)
    md_to_pdf_mapping = {
        "comprehensive_tour_faq.md": "comprehensive_tour_guide_and_faq.pdf",
        "production_history_database.md": "complete_production_history_database.pdf",
        "expanded_facilities_technical.md": "expanded_facilities_technical_specifications.pdf",
        "enhanced_interactive_experiences.md": "enhanced_interactive_experiences_guide.pdf",
        "detailed_scripts_and_scenes.md": "detailed_scripts_and_scenes_database.pdf"
    }
    
    print("=" * 80)
    print("Markdown to PDF Converter")
    print("=" * 80)
    
    converted = 0
    skipped = 0
    
    for md_filename, pdf_filename in md_to_pdf_mapping.items():
        md_path = md_dir / md_filename
        
        if not md_path.exists():
            print(f"⚠️  Skipping: {md_filename} (not found)")
            skipped += 1
            continue
        
        pdf_path = pdf_dir / pdf_filename
        
        # Check if PDF already exists
        if pdf_path.exists():
            print(f"⚠️  Skipping: {pdf_filename} (already exists)")
            skipped += 1
            continue
        
        # Convert
        if convert_md_to_pdf(md_path, pdf_path, pdf_filename):
            converted += 1
    
    print("\n" + "=" * 80)
    print(f"Conversion complete!")
    print(f"  ✅ Converted: {converted}")
    print(f"  ⚠️  Skipped: {skipped}")
    print("=" * 80)


if __name__ == "__main__":
    main()
