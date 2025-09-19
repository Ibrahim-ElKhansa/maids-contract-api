import json
import base64
import fitz

# Read the base64 PDF data from your file
with open('test_pdf_base64.json', 'r') as f:
    pdf_base64 = f.read().strip()

# Remove any JSON structure if it exists
if pdf_base64.startswith('{'):
    try:
        data = json.loads(pdf_base64)
        if 'pdf_base64' in data:
            pdf_base64 = data['pdf_base64']
        elif isinstance(data, dict) and len(data) == 1:
            pdf_base64 = list(data.values())[0]
    except:
        pass

# If the data has quotes around it, remove them
if pdf_base64.startswith('"') and pdf_base64.endswith('"'):
    pdf_base64 = pdf_base64[1:-1]

try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    print(f"PDF has {pdf_document.page_count} pages")
    
    # Focus on page 3 where we found "monthly"
    page = pdf_document[2]  # Page 3 (0-indexed)
    
    print("\n=== PAGE 3 ANALYSIS ===")
    
    # Method 1: Get text with dictionary format (most detailed)
    text_dict = page.get_text("dict")
    print("Analyzing text blocks with formatting...")
    
    for block_num, block in enumerate(text_dict.get("blocks", [])):
        if "lines" in block:
            for line_num, line in enumerate(block["lines"]):
                for span_num, span in enumerate(line.get("spans", [])):
                    text = span.get("text", "").strip()
                    if text and ("monthly" in text.lower() or "weekly" in text.lower()):
                        print(f"\nBlock {block_num}, Line {line_num}, Span {span_num}:")
                        print(f"  Text: '{text}'")
                        print(f"  Font: {span.get('font', 'N/A')}")
                        print(f"  Size: {span.get('size', 'N/A')}")
                        print(f"  Flags: {span.get('flags', 'N/A')} (binary: {bin(span.get('flags', 0))})")
                        print(f"  Color: {span.get('color', 'N/A')}")
                        print(f"  Bbox: {span.get('bbox', 'N/A')}")
                        
                        # Check flags for underline (flag 4)
                        flags = span.get('flags', 0)
                        if flags & 4:
                            print(f"  *** UNDERLINE FLAG DETECTED! ***")
                        if flags & 16:
                            print(f"  *** ALTERNATE UNDERLINE FLAG DETECTED! ***")
    
    # Method 2: Check annotations
    print("\n=== CHECKING ANNOTATIONS ===")
    annotations = page.annots()
    if annotations:
        for annot_num, annot in enumerate(annotations):
            print(f"Annotation {annot_num}:")
            print(f"  Type: {annot.type}")
            print(f"  Content: {annot.content}")
            print(f"  Rect: {annot.rect}")
            if annot.type[1] == 'Underline':
                print(f"  *** UNDERLINE ANNOTATION FOUND! ***")
                # Get text in this area
                rect = annot.rect
                text_in_rect = page.get_textbox(rect)
                print(f"  Text in annotation area: '{text_in_rect}'")
    else:
        print("No annotations found")
    
    # Method 3: Check drawings
    print("\n=== CHECKING DRAWINGS ===")
    drawings = page.get_drawings()
    if drawings:
        print(f"Found {len(drawings)} drawings")
        for draw_num, drawing in enumerate(drawings):
            print(f"Drawing {draw_num}: {drawing}")
    else:
        print("No drawings found")
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error: {e}")