import fitz  # PyMuPDF
import os

def test_company_detection(pdf_path, pdf_name):
    """Test the new company string detection logic"""
    print(f"\n{'='*80}")
    print(f"TESTING COMPANY DETECTION: {pdf_name}")
    print(f"{'='*80}")
    
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    print(f"Total pages: {pdf_document.page_count}")
    
    # Search throughout the entire PDF for company strings
    signature_layout = None
    found_on_page = None
    found_text = None
    
    print(f"\n--- SEARCHING FOR COMPANY STRINGS ---")
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "").strip()
                        
                        # Check for Maids CC company string
                        if "Maids CC Domestic Workers" in text:
                            signature_layout = "high"
                            found_on_page = page_num + 1
                            found_text = text
                            print(f"✅ Found 'Maids CC Domestic Workers' on page {page_num + 1}")
                            print(f"   Full text: '{text}'")
                            print(f"   ➡️ Will use HIGH layout (Y: 425-537)")
                            break
                        
                        # Check for Al Mustaqeem company string  
                        elif "Al Mustaqeem Domestic Workers" in text:
                            signature_layout = "low" 
                            found_on_page = page_num + 1
                            found_text = text
                            print(f"✅ Found 'Al Mustaqeem Domestic Workers' on page {page_num + 1}")
                            print(f"   Full text: '{text}'")
                            print(f"   ➡️ Will use LOW layout (Y: 508-608)")
                            break
                    
                    if signature_layout:
                        break
                if signature_layout:
                    break
        if signature_layout:
            break
    
    if not signature_layout:
        print("❌ No company identification string found!")
        print("   Will default to HIGH layout")
        signature_layout = "high"
    
    # Show which coordinates would be used
    print(f"\n--- SIGNATURE BOX COORDINATES ---")
    if signature_layout == "high":
        print(f"MAIDS CC layout (HIGH):")
        print(f"  Left:  (95, 425) to (290, 537)")
        print(f"  Right: (300, 425) to (500, 537)")
    else:
        print(f"AL MUSTAQEEM layout (LOW):")
        print(f"  Left:  (95, 508) to (290, 608)")
        print(f"  Right: (300, 508) to (500, 608)")
    
    # Also search for partial matches to help debug
    print(f"\n--- SEARCHING FOR PARTIAL MATCHES ---")
    partial_matches = []
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "").strip()
                        
                        if "Maids" in text or "CC" in text or "Domestic" in text or "Workers" in text:
                            if text not in partial_matches:
                                partial_matches.append(f"Page {page_num + 1}: '{text}'")
                        elif "Al Mustaqeem" in text or "Mustaqeem" in text:
                            if text not in partial_matches:
                                partial_matches.append(f"Page {page_num + 1}: '{text}'")
    
    if partial_matches:
        print("Related text found:")
        for match in partial_matches[:10]:  # Show first 10
            print(f"  {match}")
        if len(partial_matches) > 10:
            print(f"  ... and {len(partial_matches) - 10} more")
    else:
        print("No related text found")
    
    pdf_document.close()

if __name__ == "__main__":
    # Check all PDFs in the directory
    pdf_files = [
        "Contract-with-stamp-and-signature.pdf",
        "extracted_document.pdf"
    ]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            test_company_detection(pdf_file, pdf_file)