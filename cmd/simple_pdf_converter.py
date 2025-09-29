#!/usr/bin/env python3
"""
Simple PDF to Text Converter
A simplified version for basic PDF text extraction
"""

import fitz  # PyMuPDF
import sys
import os

def convert_pdf_to_text(pdf_path, output_path=None):
    """
    Convert PDF to text (simple version without OCR)
    
    Args:
        pdf_path (str): Path to input PDF file
        output_path (str): Path to output text file (optional)
    
    Returns:
        str: Extracted text
    """
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        extracted_text = []
        
        print(f"Processing PDF: {pdf_path}")
        print(f"Total pages: {len(doc)}")
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            print(f"Processing page {page_num + 1}/{len(doc)}")
            
            # Extract text from page
            text = page.get_text()
            if text.strip():
                extracted_text.append(f"=== Page {page_num + 1} ===\n{text}\n")
        
        doc.close()
        
        # Combine all text
        final_text = "\n".join(extracted_text)
        
        # Save to file if output path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_text)
            print(f"Text saved to: {output_path}")
        
        return final_text
        
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return ""

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_pdf_converter.py <input_pdf> [output_txt]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_txt = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if input file exists
    if not os.path.exists(input_pdf):
        print(f"Error: Input file '{input_pdf}' not found")
        sys.exit(1)
    
    # Convert PDF
    result = convert_pdf_to_text(input_pdf, output_txt)
    
    if result:
        print("Conversion completed successfully!")
    else:
        print("Conversion failed!")

if __name__ == "__main__":
    main()
