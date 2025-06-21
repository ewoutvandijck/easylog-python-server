#!/usr/bin/env python3
"""
Script to convert the Italian presentation markdown to PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
import re


def create_presentation_pdf():
    # Read the markdown file
    with open('presentazione-fiore-le-saline.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate("presentazione-fiore-le-saline.pdf", pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Get styles and create custom ones
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#2E8B57')  # Sea Green
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=20,
        textColor=HexColor('#4682B4')  # Steel Blue
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=12,
        textColor=HexColor('#708090')  # Slate Gray
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leftIndent=20
    )
    
    center_style = ParagraphStyle(
        'CustomCenter',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=HexColor('#2E8B57')
    )
    
    # Story to build the PDF
    story = []
    
    # Process content line by line
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # Main title (# with emoji)
        if line.startswith('# 🌟'):
            title_text = re.sub(r'^# 🌟\s*', '', line)
            story.append(Paragraph(f"🌟 {title_text}", title_style))
            story.append(Spacer(1, 20))
        
        # Major headings (## with emoji)
        elif line.startswith('## '):
            heading_text = re.sub(r'^## \*\*(.*?)\*\*$', r'\1', line)
            heading_text = re.sub(r'^## (.*?)$', r'\1', heading_text)
            story.append(Paragraph(heading_text, heading_style))
            story.append(Spacer(1, 10))
        
        # Sub headings (### with emoji)
        elif line.startswith('### '):
            subheading_text = re.sub(r'^### \*\*(.*?)\*\*$', r'\1', line)
            subheading_text = re.sub(r'^### (.*?)$', r'\1', subheading_text)
            story.append(Paragraph(subheading_text, subheading_style))
            story.append(Spacer(1, 8))
        
        # Sub-sub headings (#### with emoji)
        elif line.startswith('#### '):
            subheading_text = re.sub(r'^#### \*\*(.*?)\*\*$', r'\1', line)
            subheading_text = re.sub(r'^#### (.*?)$', r'\1', subheading_text)
            story.append(Paragraph(subheading_text, subheading_style))
            story.append(Spacer(1, 6))
        
        # Horizontal rules
        elif line.startswith('---'):
            story.append(Spacer(1, 20))
            continue
        
        # Bullet points
        elif line.startswith('- ') or line.startswith('✅'):
            bullet_text = re.sub(r'^- ', '', line)
            bullet_text = re.sub(r'^✅ ', '✅ ', bullet_text)
            # Handle bold text
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            story.append(Paragraph(bullet_text, bullet_style))
        
        # Italic text at the end
        elif line.startswith('_') and line.endswith('_'):
            italic_text = re.sub(r'^_(.*?)_$', r'<i>\1</i>', line)
            story.append(Spacer(1, 20))
            story.append(Paragraph(italic_text, center_style))
        
        # Regular paragraphs
        elif line and not line.startswith('#'):
            # Handle bold text
            paragraph_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
            story.append(Paragraph(paragraph_text, body_style))
    
    # Build PDF
    doc.build(story)
    print("✅ PDF created successfully: presentazione-fiore-le-saline.pdf")


if __name__ == "__main__":
    create_presentation_pdf() 