#!/usr/bin/env python3
"""
Convert Resort Le Saline knowledge base HTML to PDF
"""

import subprocess
import os


def convert_html_to_pdf():
    html_file = "resort-le-saline-knowledge-base.html"
    pdf_file = "resort-le-saline-knowledge-base.pdf"
    
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found!")
        return False
    
    # Try different methods to convert HTML to PDF
    methods = [
        # Method 1: Using wkhtmltopdf if available
        ["wkhtmltopdf", "--page-size", "A4", "--margin-top", "0.75in",
         "--margin-right", "0.75in", "--margin-bottom", "0.75in",
         "--margin-left", "0.75in", html_file, pdf_file],
        
        # Method 2: Using Google Chrome/Chromium headless
        ["google-chrome", "--headless", "--disable-gpu",
         "--print-to-pdf=" + pdf_file, html_file],
        ["chromium", "--headless", "--disable-gpu",
         "--print-to-pdf=" + pdf_file, html_file],
        ["chrome", "--headless", "--disable-gpu",
         "--print-to-pdf=" + pdf_file, html_file],
    ]
    
    for method in methods:
        try:
            print(f"Trying: {' '.join(method)}")
            result = subprocess.run(
                method, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ Successfully created {pdf_file}")
                return True
            else:
                print(f"❌ Failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
        except FileNotFoundError:
            print(f"❌ {method[0]} not found")
        except subprocess.TimeoutExpired:
            print(f"❌ {method[0]} timed out")
        except Exception as e:
            print(f"❌ Error with {method[0]}: {e}")
    
    print("❌ All conversion methods failed.")
    print("\n📋 Alternative options:")
    print("1. Open resort-le-saline-knowledge-base.html in browser "
          "and use 'Print to PDF'")
    print("2. Install wkhtmltopdf: brew install wkhtmltopdf")
    print("3. Use an online HTML to PDF converter")
    return False


if __name__ == "__main__":
    convert_html_to_pdf() 