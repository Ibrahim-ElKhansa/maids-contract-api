import fitz
import json

def analyze_signature_boxes(pdf_path):
    """Analyze the signature boxes on the last page"""
    try:
        pdf_document = fitz.open(pdf_path)
        last_page_num = pdf_document.page_count - 1
        last_page = pdf_document[last_page_num]
        
        print(f"Analyzing last page (page {last_page_num + 1}) of {pdf_document.page_count} total pages")
        
        # Get all text to find signature boxes
        text_dict = last_page.get_text("dict")
        signature_boxes = []
        
        # Find all instances of "Signature" text
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if "signature" in text.lower():
                            bbox = span.get('bbox')
                            signature_boxes.append({
                                'text': text,
                                'bbox': bbox,
                                'position': 'left' if bbox[0] < 300 else 'right'  # Assume left if x < 300
                            })
        
        print(f"Found {len(signature_boxes)} signature text instances:")
        for i, box in enumerate(signature_boxes):
            print(f"  {i+1}. '{box['text']}' at {box['bbox']} ({box['position']} side)")
        
        # Get all drawings on the last page
        drawings = last_page.get_drawings()
        print(f"\nFound {len(drawings)} total drawings on last page")
        
        # Analyze drawings in signature areas
        left_signature_area = None
        right_signature_area = None
        
        # Define signature areas based on the signature text positions
        if signature_boxes:
            # Estimate signature box areas (expand around signature text)
            for box in signature_boxes:
                if box['position'] == 'left':
                    left_signature_area = (
                        box['bbox'][0] - 100,  # left
                        box['bbox'][1] - 50,   # top
                        box['bbox'][2] + 200,  # right
                        box['bbox'][3] + 150   # bottom
                    )
                else:
                    right_signature_area = (
                        box['bbox'][0] - 100,  # left
                        box['bbox'][1] - 50,   # top
                        box['bbox'][2] + 200,  # right
                        box['bbox'][3] + 150   # bottom
                    )
        
        print(f"\nSignature areas:")
        print(f"  Left area: {left_signature_area}")
        print(f"  Right area: {right_signature_area}")
        
        # Count lines in each signature area
        left_lines = 0
        right_lines = 0
        
        for i, drawing in enumerate(drawings):
            print(f"\nDrawing {i+1}: {drawing['type']}")
            
            if drawing['type'] == 's':  # stroke/line
                for item in drawing['items']:
                    if item[0] == 'l':  # line
                        start_point = item[1]
                        end_point = item[2]
                        line_center_x = (start_point.x + end_point.x) / 2
                        line_center_y = (start_point.y + end_point.y) / 2
                        
                        print(f"  Line from {start_point} to {end_point}, center: ({line_center_x:.1f}, {line_center_y:.1f})")
                        
                        # Check if line is in left signature area
                        if left_signature_area:
                            if (left_signature_area[0] <= line_center_x <= left_signature_area[2] and
                                left_signature_area[1] <= line_center_y <= left_signature_area[3]):
                                left_lines += 1
                                print(f"    *** In LEFT signature area ***")
                        
                        # Check if line is in right signature area
                        if right_signature_area:
                            if (right_signature_area[0] <= line_center_x <= right_signature_area[2] and
                                right_signature_area[1] <= line_center_y <= right_signature_area[3]):
                                right_lines += 1
                                print(f"    *** In RIGHT signature area ***")
            
            elif drawing['type'] == 'f':  # fill (might be part of stamp)
                rect = drawing.get('rect')
                if rect:
                    rect_center_x = (rect.x0 + rect.x1) / 2
                    rect_center_y = (rect.y0 + rect.y1) / 2
                    
                    print(f"  Fill rect: {rect}, center: ({rect_center_x:.1f}, {rect_center_y:.1f})")
                    
                    # Check if fill is in signature areas (might be stamp)
                    if left_signature_area:
                        if (left_signature_area[0] <= rect_center_x <= left_signature_area[2] and
                            left_signature_area[1] <= rect_center_y <= left_signature_area[3]):
                            print(f"    *** Fill in LEFT signature area (possible stamp) ***")
                    
                    if right_signature_area:
                        if (right_signature_area[0] <= rect_center_x <= right_signature_area[2] and
                            right_signature_area[1] <= rect_center_y <= right_signature_area[3]):
                            print(f"    *** Fill in RIGHT signature area ***")
        
        print(f"\n" + "="*50)
        print(f"SIGNATURE ANALYSIS RESULTS:")
        print(f"="*50)
        print(f"Left signature box: {left_lines} lines")
        print(f"Right signature box: {right_lines} lines")
        print(f"Total signature lines: {left_lines + right_lines}")
        
        pdf_document.close()
        
        return {
            'left_signature_lines': left_lines,
            'right_signature_lines': right_lines,
            'total_signature_lines': left_lines + right_lines
        }
        
    except Exception as e:
        print(f"Error analyzing signature boxes: {e}")
        import traceback
        traceback.print_exc()
        return None

# Analyze both PDFs
print("="*60)
print("ANALYZING CONTRACT WITH STAMP AND SIGNATURE")
print("="*60)
result1 = analyze_signature_boxes('Contract-with-stamp-and-signature.pdf')

print("\n" + "="*60)
print("ANALYZING EXTRACTED DOCUMENT (ORIGINAL)")
print("="*60)
result2 = analyze_signature_boxes('extracted_document.pdf')

print("\n" + "="*60)
print("COMPARISON RESULTS")
print("="*60)
if result1 and result2:
    print(f"Contract with stamp/signature: Left={result1['left_signature_lines']}, Right={result1['right_signature_lines']}")
    print(f"Original extracted document: Left={result2['left_signature_lines']}, Right={result2['right_signature_lines']}")
else:
    print("Error in analysis")