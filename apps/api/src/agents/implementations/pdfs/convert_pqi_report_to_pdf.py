#!/usr/bin/env python3
"""
Convert PQI Audit Report markdown to PDF
"""

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, 
                                PageBreak, Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
import re
import os


def clean_markdown_text(text):
    """Clean markdown formatting for PDF"""
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    # Remove markdown bold/italic
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Remove markdown links but keep text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove markdown list markers and format as bullet points
    text = re.sub(r'^- ', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\* ', '• ', text, flags=re.MULTILINE)
    return text


def parse_table_data(content):
    """Parse the audit data table from markdown"""
    table_data = []
    lines = content.split('\n')
    
    in_table = False
    headers = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('| Audit datum'):
            # Found the table header
            in_table = True
            headers = [cell.strip() for cell in line.split('|')[1:-1]]
            continue
        elif line.startswith('|---'):
            # Skip separator line
            continue
        elif (in_table and line.startswith('|') and 
              ('2024-' in line or '2025-' in line)):
            # Data row
            row_data = [cell.strip() for cell in line.split('|')[1:-1]]
            if len(row_data) == len(headers):
                table_data.append(row_data)
        elif in_table and not line.startswith('|'):
            # End of table
            break
    
    return headers, table_data


def create_audit_table(headers, data):
    """Create a formatted table for the audit data"""
    if not data:
        return None
    
    # Select key columns for the PDF (to fit on page)
    key_columns = ['Audit datum', 'Project', 'Uitvoerder', 'Onderwerp', 'PQI Score', 'Soort']
    
    # Find indices of key columns
    key_indices = []
    display_headers = []
    for col in key_columns:
        try:
            idx = headers.index(col)
            key_indices.append(idx)
            display_headers.append(col)
        except ValueError:
            continue
    
    # Build table data with selected columns
    table_data = [display_headers]
    for row in data:  # Include all rows
        if len(row) > max(key_indices):
            filtered_row = [row[i] if i < len(row) else '' for i in key_indices]
            # Truncate long text for better readability
            filtered_row = [cell[:40] + '...' if len(cell) > 40 else cell for cell in filtered_row]
            table_data.append(filtered_row)
    
    # Create table
    table = Table(table_data, repeatRows=1)
    
    # Style the table
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2E5984')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#F5F5F5')]),
    ]))
    
    return table


def create_pdf():
    """Create PDF from PQI audit report markdown"""
    
    # Read the markdown file
    input_file = 'pqi_audit_report.md'
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: {input_file} not found!")
        return False
    
    # Create PDF document
    pdf_filename = "pqi_audit_report.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=12,
        textColor=HexColor('#2E5984'),
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=8,
        spaceBefore=12,
        textColor=HexColor('#2E5984')
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=14,
        spaceAfter=6,
        spaceBefore=8,
        textColor=HexColor('#4A6FA5')
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6,
        leading=14
    )
    
    meta_style = ParagraphStyle(
        'MetaInfo',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        textColor=HexColor('#666666')
    )
    
    # Build content
    story = []
    
    # Split content into sections
    sections = content.split('\n\n')
    
    # Process each section
    for i, section in enumerate(sections):
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
            story.append(Spacer(1, 8))
            
        elif section.startswith('**Export Date:**') or section.startswith('**Dataset:**'):
            # Metadata
            story.append(Paragraph(clean_text, meta_style))
            
        elif '| Audit datum |' in section:
            # This is the data table
            story.append(Paragraph('<b>Complete Audit Data Overview</b>', subheading_style))
            story.append(Spacer(1, 6))
            
            headers, table_data = parse_table_data(section)
            if table_data:
                audit_table = create_audit_table(headers, table_data)
                if audit_table:
                    story.append(audit_table)
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(f'<i>Complete dataset: {len(table_data)} audit records</i>', meta_style))
            
        elif section.startswith('---'):
            # Page break or separator
            story.append(PageBreak())
            
        else:
            # Regular content
            if clean_text and not clean_text.startswith('|'):
                # Split into paragraphs
                paragraphs = clean_text.split('\n')
                for para in paragraphs:
                    para = para.strip()
                    if para and not para.startswith('|'):
                        story.append(Paragraph(para, body_style))
                        story.append(Spacer(1, 3))
    
    # Build PDF
    try:
        doc.build(story)
        print(f"✅ Successfully created {pdf_filename}")
        print(f"   Location: {os.path.abspath(pdf_filename)}")
        return True
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return False


if __name__ == "__main__":
    create_pdf() 