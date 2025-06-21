#!/usr/bin/env python3
"""
Create PDF from Italian presentation for Fiore Le Saline
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import re


def clean_markdown_text(text):
    """Clean markdown formatting for PDF"""
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Remove markdown bold/italic and convert to HTML
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Handle underscores for italics
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Keep emojis and stars
    text = re.sub(r'⭐+', '⭐⭐⭐⭐⭐', text)
    # Remove markdown list markers and format as bullet points
    text = re.sub(r'^- ', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\* ', '• ', text, flags=re.MULTILINE)
    # Handle checkmarks
    text = re.sub(r'^✅ ', '✅ ', text, flags=re.MULTILINE)
    return text


def create_presentation_pdf():
    """Create PDF from Italian presentation markdown"""
    
    # Read the markdown file
    try:
        with open('presentazione-fiore-le-saline.md', 'r',
                  encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: presentazione-fiore-le-saline.md not found!")
        return False
    
    # Create PDF document
    pdf_filename = "presentazione-fiore-le-saline.pdf"
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
    
    # Define custom styles with Italian theme colors
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=16,
        textColor=HexColor('#2E8B57'),  # Sea Green
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12,
        textColor=HexColor('#4682B4')  # Steel Blue
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        spaceAfter=8,
        spaceBefore=8,
        textColor=HexColor('#708090')  # Slate Gray
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=20,
        leading=13
    )
    
    center_style = ParagraphStyle(
        'CustomCenter',
        parent=styles['Normal'],
        fontSize=11,
        alignment=1,  # Center
        textColor=HexColor('#2E8B57'),
        spaceAfter=8
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
        if section.startswith('# 🌟'):
            # Main title with emoji
            title_text = clean_text.replace('# 🌟', '🌟')
            story.append(Paragraph(title_text, title_style))
            story.append(Spacer(1, 16))
            
        elif section.startswith('## '):
            # Major heading
            heading_text = clean_text.replace('## ', '')
            story.append(Spacer(1, 16))
            story.append(Paragraph(heading_text, heading_style))
            story.append(Spacer(1, 8))
            
        elif section.startswith('### '):
            # Subheading
            subheading_text = clean_text.replace('### ', '')
            story.append(Paragraph(subheading_text, subheading_style))
            story.append(Spacer(1, 6))
        
        elif section.startswith('#### '):
            # Sub-subheading
            subheading_text = clean_text.replace('#### ', '')
            story.append(Paragraph(subheading_text, subheading_style))
            story.append(Spacer(1, 4))
            
        elif section.startswith('---'):
            # Section break
            story.append(Spacer(1, 20))
            
        else:
            # Regular content
            if clean_text:
                # Check if it's bullet points
                lines = clean_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Handle bullet points and checkmarks
                    if line.startswith('• ') or line.startswith('✅'):
                        story.append(Paragraph(line, bullet_style))
                    # Handle italic text (signature)
                    elif line.startswith('<i>') and line.endswith('</i>'):
                        story.append(Spacer(1, 12))
                        story.append(Paragraph(line, center_style))
                    else:
                        story.append(Paragraph(line, body_style))
                        story.append(Spacer(1, 4))
    
    # Build PDF
    try:
        doc.build(story)
        print(f"✅ Successfully created {pdf_filename}")
        return True
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return False


if __name__ == "__main__":
    create_presentation_pdf() 