#!/usr/bin/env python3
"""
PDF to Text Converter
Converts PDF files to text, including handling images with OCR
"""

import os
import sys
import argparse
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import json

class PDFToTextConverter:
    def __init__(self, tesseract_path=None):
        """
        Initialize the converter
        
        Args:
            tesseract_path (str): Path to tesseract executable (optional)
        """
        self.tesseract_path = tesseract_path
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def extract_text_from_image(self, image):
        """
        Extract text from image using OCR
        
        Args:
            image: PIL Image object
            
        Returns:
            str: Extracted text from image
        """
        try:
            # Convert image to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""
    
    def convert_pdf_to_text(self, pdf_path, output_path=None, include_images=True):
        """
        Convert PDF to text
        
        Args:
            pdf_path (str): Path to input PDF file
            output_path (str): Path to output text file (optional)
            include_images (bool): Whether to extract text from images
            
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
                
                # Extract text from images if requested
                if include_images:
                    image_list = page.get_images()
                    if image_list:
                        print(f"  Found {len(image_list)} images on page {page_num + 1}")
                        
                        for img_index, img in enumerate(image_list):
                            try:
                                # Get image data
                                xref = img[0]
                                pix = fitz.Pixmap(doc, xref)
                                
                                # Convert to PIL Image
                                img_data = pix.tobytes("png")
                                pil_image = Image.open(io.BytesIO(img_data))
                                
                                # Extract text from image
                                img_text = self.extract_text_from_image(pil_image)
                                if img_text:
                                    extracted_text.append(f"--- Image {img_index + 1} on Page {page_num + 1} ---\n{img_text}\n")
                                
                                pix = None  # Free memory
                                
                            except Exception as e:
                                print(f"  Error processing image {img_index + 1}: {e}")
                                continue
            
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
    
    def convert_pdf_to_json(self, pdf_path, output_path=None, include_images=True):
        """
        Convert PDF to structured JSON format
        
        Args:
            pdf_path (str): Path to input PDF file
            output_path (str): Path to output JSON file (optional)
            include_images (bool): Whether to extract text from images
            
        Returns:
            dict: Structured data
        """
        try:
            doc = fitz.open(pdf_path)
            pages_data = []
            
            print(f"Processing PDF: {pdf_path}")
            print(f"Total pages: {len(doc)}")
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                print(f"Processing page {page_num + 1}/{len(doc)}")
                
                page_data = {
                    "page_number": page_num + 1,
                    "text": "",
                    "images": []
                }
                
                # Extract text from page
                text = page.get_text()
                if text.strip():
                    page_data["text"] = text.strip()
                
                # Extract text from images if requested
                if include_images:
                    image_list = page.get_images()
                    if image_list:
                        print(f"  Found {len(image_list)} images on page {page_num + 1}")
                        
                        for img_index, img in enumerate(image_list):
                            try:
                                xref = img[0]
                                pix = fitz.Pixmap(doc, xref)
                                
                                img_data = pix.tobytes("png")
                                pil_image = Image.open(io.BytesIO(img_data))
                                
                                img_text = self.extract_text_from_image(pil_image)
                                
                                image_info = {
                                    "image_index": img_index + 1,
                                    "text": img_text,
                                    "width": pil_image.width,
                                    "height": pil_image.height
                                }
                                page_data["images"].append(image_info)
                                
                                pix = None
                                
                            except Exception as e:
                                print(f"  Error processing image {img_index + 1}: {e}")
                                continue
                
                pages_data.append(page_data)
            
            doc.close()
            
            result = {
                "pdf_path": pdf_path,
                "total_pages": len(pages_data),
                "pages": pages_data
            }
            
            # Save to file if output path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"JSON saved to: {output_path}")
            
            return result
            
        except Exception as e:
            print(f"Error converting PDF to JSON: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to text with OCR support')
    parser.add_argument('input_pdf', help='Path to input PDF file')
    parser.add_argument('-o', '--output', help='Path to output file')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (text or json)')
    parser.add_argument('--no-images', action='store_true',
                       help='Skip image text extraction')
    parser.add_argument('--tesseract-path', help='Path to tesseract executable')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_pdf):
        print(f"Error: Input file '{args.input_pdf}' not found")
        sys.exit(1)
    
    # Initialize converter
    converter = PDFToTextConverter(tesseract_path=args.tesseract_path)
    
    # Determine output path
    if not args.output:
        input_path = Path(args.input_pdf)
        if args.format == 'json':
            args.output = input_path.with_suffix('.json')
        else:
            args.output = input_path.with_suffix('.txt')
    
    # Convert PDF
    if args.format == 'json':
        result = converter.convert_pdf_to_json(
            args.input_pdf, 
            args.output, 
            include_images=not args.no_images
        )
    else:
        result = converter.convert_pdf_to_text(
            args.input_pdf, 
            args.output, 
            include_images=not args.no_images
        )
    
    print("Conversion completed!")

if __name__ == "__main__":
    main()
