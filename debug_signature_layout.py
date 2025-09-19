import fitz  # PyMuPDF
import os

def debug_signature_layout(pdf_path, pdf_name):
    """Debug where 'Signature' text is located to understand layout detection"""
    print(f"\n{'='*80}")
    print(f"DEBUGGING SIGNATURE LAYOUT: {pdf_name}")
    print(f"{'='*80}")
    
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    # Get the last page
    last_page_num = pdf_document.page_count - 1
    last_page = pdf_document[last_page_num]
    
    print(f"Last page number: {last_page_num + 1}")
    print(f"Page dimensions: {last_page.rect.width} x {last_page.rect.height}")
    
    # Find all "Signature" text occurrences
    text_dict = last_page.get_text("dict")
    signature_found = False
    
    print(f"\n--- SEARCHING FOR 'SIGNATURE' TEXT ---")
    
    for block_idx, block in enumerate(text_dict["blocks"]):
        if "bbox" in block and "lines" in block:
            for line_idx, line in enumerate(block["lines"]):
                for span_idx, span in enumerate(line["spans"]):
                    text = span.get("text", "").strip()
                    if "signature" in text.lower():
                        signature_found = True
                        bbox = block["bbox"]
                        center_x = (bbox[0] + bbox[2]) / 2
                        center_y = (bbox[1] + bbox[3]) / 2
                        
                        print(f"Found 'Signature' text: '{text}'")
                        print(f"  Block {block_idx}, Line {line_idx}, Span {span_idx}")
                        print(f"  Block bbox: ({bbox[0]:.1f}, {bbox[1]:.1f}) to ({bbox[2]:.1f}, {bbox[3]:.1f})")
                        print(f"  Center: ({center_x:.1f}, {center_y:.1f})")
                        
                        # Check against our detection criteria
                        print(f"\n  Layout Detection Analysis:")
                        high_match = (93 <= center_x <= 145 and 412 <= center_y <= 422)
                        low_match = (92 <= center_x <= 142 and 497 <= center_y <= 505)
                        
                        print(f"  HIGH layout check (93-145 X, 412-422 Y): {high_match}")
                        print(f"  LOW layout check (92-142 X, 497-505 Y): {low_match}")
                        
                        if high_match:
                            print(f"  ➡️ Would use HIGH layout (Y: 425-537)")
                        elif low_match:
                            print(f"  ➡️ Would use LOW layout (Y: 508-608)")
                        else:
                            print(f"  ❌ No layout match! Need to adjust detection criteria")
                            # Suggest new criteria based on actual position
                            suggested_x_min = max(90, center_x - 10)
                            suggested_x_max = min(150, center_x + 10)
                            suggested_y_min = max(400, center_y - 10)
                            suggested_y_max = min(520, center_y + 10)
                            print(f"  💡 Suggested criteria: ({suggested_x_min:.0f}-{suggested_x_max:.0f} X, {suggested_y_min:.0f}-{suggested_y_max:.0f} Y)")
                        
                        print()
    
    if not signature_found:
        print("❌ No 'Signature' text found on last page!")
        print("Checking all text blocks...")
        
        for block_idx, block in enumerate(text_dict["blocks"]):
            if "bbox" in block and "lines" in block:
                for line_idx, line in enumerate(block["lines"]):
                    for span_idx, span in enumerate(line["spans"]):
                        text = span.get("text", "").strip()
                        if text:  # Any text
                            bbox = block["bbox"]
                            center_x = (bbox[0] + bbox[2]) / 2
                            center_y = (bbox[1] + bbox[3]) / 2
                            print(f"  Text '{text}' at ({center_x:.1f}, {center_y:.1f})")
    
    # Also check what signature boxes would be used
    print(f"\n--- CURRENT BOX COORDINATES ---")
    print(f"HIGH layout boxes:")
    print(f"  Left:  (95, 425) to (290, 537)")
    print(f"  Right: (300, 425) to (500, 537)")
    print(f"LOW layout boxes:")
    print(f"  Left:  (95, 508) to (290, 608)")
    print(f"  Right: (300, 508) to (500, 608)")
    
    pdf_document.close()

if __name__ == "__main__":
    # Check all PDFs in the directory
    pdf_files = [
        "Contract-with-stamp-and-signature.pdf",
        "extracted_document.pdf"
    ]
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            debug_signature_layout(pdf_file, pdf_file)