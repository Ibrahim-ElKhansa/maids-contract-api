#!/usr/bin/env python3
import base64
import io
from pdf_processor import PDFProcessor

def test_arabic_pdf():
    # Read the base64 content
    with open("arabic-pdf-base64.txt", "r", encoding="utf-8") as f:
        base64_content = f.read().strip()
    
    print(f"Base64 content length: {len(base64_content)}")
    
    try:
        # Decode the base64 to get PDF bytes
        pdf_bytes = base64.b64decode(base64_content)
        print(f"PDF bytes length: {len(pdf_bytes)}")
        
        # Create PDF processor and analyze
        processor = PDFProcessor()
        result = processor.extract_underlined_words(pdf_bytes)
        
        print("\nAnalysis Results:")
        print(f"- Pages: {result.get('pages', 'N/A')}")
        print(f"- Article count: {result.get('article_count', 'N/A')}")
        print(f"- Arabic contract count: {result.get('arabic_contract_count', 'N/A')}")
        print(f"- Signature layout: {result.get('signature_layout', 'N/A')}")
        print(f"- Company found: {result.get('company_found', 'N/A')}")
        
        # Print detailed element information
        if 'detailed_element_info' in result:
            print(f"\nDetailed Element Info:")
            for key, value in result['detailed_element_info'].items():
                print(f"- {key}: {value}")
        
        print(f"\nFull result keys: {list(result.keys())}")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_arabic_pdf()