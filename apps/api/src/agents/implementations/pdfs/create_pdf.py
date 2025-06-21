#!/usr/bin/env python3
"""
Create PDF from Resort Le Saline knowledge base
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import re


def clean_markdown_text(text):
    """Clean markdown formatting for PDF"""
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Remove markdown bold/italic
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove extra stars/emojis that cause issues
    text = re.sub(r'⭐+', '★', text)
    # Remove markdown list markers and format as bullet points
    text = re.sub(r'^- ', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\* ', '• ', text, flags=re.MULTILINE)
    return text


def create_pdf():
    """Create PDF from markdown knowledge base"""
    
    # Read the markdown file
    try:
        with open('resort-le-saline-knowledge-base.md', 'r',
                  encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: resort-le-saline-knowledge-base.md not found!")
        return False
    
    # Create PDF document
    pdf_filename = "resort-le-saline-knowledge-base.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        textColor=HexColor('#2E5984'),
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=8,
        textColor=HexColor('#2E5984')
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=6,
        textColor=HexColor('#4A6FA5')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leading=12
    )
    
    # Build content
    story = []
    
    # Split content into sections
    sections = content.split('\n\n')
    
    for section in sections:
        if not section.strip():
            continue
            
        # Clean the text
        clean_text = clean_markdown_text(section.strip())
        
        # Determine style based on content
        if section.startswith('# '):
            # Main title
            title_text = clean_text.replace('# ', '')
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 12))
            
        elif section.startswith('## '):
            # Major heading
            heading_text = clean_text.replace('## ', '')
            story.append(Spacer(1, 12))
            story.append(Paragraph(heading_text, heading_style))
            story.append(Spacer(1, 6))
            
        elif section.startswith('### '):
            # Subheading
            subheading_text = clean_text.replace('### ', '')
            story.append(Paragraph(subheading_text, subheading_style))
            story.append(Spacer(1, 4))
            
        elif section.startswith('---'):
            # Page break for major sections
            story.append(PageBreak())
            
        else:
            # Regular content
            if clean_text:
                # Split into paragraphs
                paragraphs = clean_text.split('\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para.strip(), body_style))
                        story.append(Spacer(1, 3))
    
    # Build PDF
    try:
        doc.build(story)
        print(f"✅ Successfully created {pdf_filename}")
        return True
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return False


if __name__ == "__main__":
    create_pdf() 