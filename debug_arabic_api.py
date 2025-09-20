#!/usr/bin/env python3
import base64
import io
import fitz  # PyMuPDF
import re
from pdf_processor import PDFProcessor

def debug_arabic_extraction():
    # Read the base64 content
    with open("arabic-pdf-base64.txt", "r", encoding="utf-8") as f:
        base64_content = f.read().strip()
    
    print(f"Base64 content length: {len(base64_content)}")
    
    try:
        # Decode the base64 to get PDF bytes
        pdf_bytes = base64.b64decode(base64_content)
        print(f"PDF bytes length: {len(pdf_bytes)}")
        
        # Open the PDF directly like the processor does
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        print(f"PDF has {len(pdf_document)} pages")
        
        # Check what text is on each page
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()
            print(f"\n=== PAGE {page_num + 1} ===")
            print(f"Text length: {len(text)}")
            print(f"First 200 chars: {repr(text[:200])}")
            
            # Check for Arabic characters
            arabic_chars = [c for c in text if ord(c) >= 1536 and ord(c) <= 1791]
            print(f"Arabic characters found: {len(arabic_chars)}")
            if arabic_chars:
                print(f"Sample Arabic chars: {arabic_chars[:10]}")
            
            # Check for our specific search terms
            search_terms = [
                "ﺍﻟﻤﻮﺿﻮﻉ",
                "الموضوع", 
                "ﺍﻟﻤﻮﺿﻮﻉ".encode('utf-8').decode('utf-8'),
                # Try different encodings
                "الموضوع".encode('cp1256').decode('cp1256', errors='ignore'),
            ]
            
            for term in search_terms:
                try:
                    count = text.count(term)
                    if count > 0:
                        print(f"Found '{term}': {count} times")
                except Exception as e:
                    print(f"Error searching for '{term}': {e}")
        
        pdf_document.close()
        
        # Now test with the processor
        print("\n=== PROCESSOR RESULTS ===")
        processor = PDFProcessor()
        result = processor.extract_underlined_words(pdf_bytes)
        print(f"Arabic contract count from processor: {result.get('arabic_contract_count', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_arabic_extraction()