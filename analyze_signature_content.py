import fitz

def analyze_actual_signatures(pdf_path):
    """Look for actual signature/stamp content beyond table borders"""
    try:
        pdf_document = fitz.open(pdf_path)
        last_page_num = pdf_document.page_count - 1
        last_page = pdf_document[last_page_num]
        
        print(f"Analyzing {pdf_path}")
        
        # Define more precise signature box areas based on the analysis
        # These are the actual content areas inside the signature boxes
        left_content_area = (95, 420, 290, 540)   # Inside left signature box
        right_content_area = (305, 420, 500, 540)  # Inside right signature box
        
        print(f"Left content area: {left_content_area}")
        print(f"Right content area: {right_content_area}")
        
        # Get all drawings
        drawings = last_page.get_drawings()
        
        left_content_lines = 0
        right_content_lines = 0
        left_content_fills = 0
        right_content_fills = 0
        
        print(f"\nAnalyzing {len(drawings)} drawings for signature content:")
        
        for i, drawing in enumerate(drawings):
            if drawing['type'] == 's':  # stroke/line
                for item in drawing['items']:
                    if item[0] == 'l':  # line
                        start_point = item[1]
                        end_point = item[2]
                        line_center_x = (start_point.x + end_point.x) / 2
                        line_center_y = (start_point.y + end_point.y) / 2
                        
                        # Check if line is INSIDE the content areas (not table borders)
                        in_left_content = (left_content_area[0] < line_center_x < left_content_area[2] and
                                         left_content_area[1] < line_center_y < left_content_area[3])
                        in_right_content = (right_content_area[0] < line_center_x < right_content_area[2] and
                                          right_content_area[1] < line_center_y < right_content_area[3])
                        
                        if in_left_content:
                            left_content_lines += 1
                            print(f"  Drawing {i+1}: Line in LEFT content area at ({line_center_x:.1f}, {line_center_y:.1f})")
                        
                        if in_right_content:
                            right_content_lines += 1
                            print(f"  Drawing {i+1}: Line in RIGHT content area at ({line_center_x:.1f}, {line_center_y:.1f})")
            
            elif drawing['type'] == 'f':  # fill
                rect = drawing.get('rect')
                if rect:
                    rect_center_x = (rect.x0 + rect.x1) / 2
                    rect_center_y = (rect.y0 + rect.y1) / 2
                    
                    # Check if fill is INSIDE the content areas
                    in_left_content = (left_content_area[0] < rect_center_x < left_content_area[2] and
                                     left_content_area[1] < rect_center_y < left_content_area[3])
                    in_right_content = (right_content_area[0] < rect_center_x < right_content_area[2] and
                                      right_content_area[1] < rect_center_y < right_content_area[3])
                    
                    if in_left_content:
                        left_content_fills += 1
                        print(f"  Drawing {i+1}: Fill in LEFT content area at ({rect_center_x:.1f}, {rect_center_y:.1f})")
                    
                    if in_right_content:
                        right_content_fills += 1
                        print(f"  Drawing {i+1}: Fill in RIGHT content area at ({rect_center_x:.1f}, {rect_center_y:.1f})")
        
        print(f"\n" + "="*50)
        print(f"SIGNATURE CONTENT ANALYSIS:")
        print(f"="*50)
        print(f"Left signature content: {left_content_lines} lines, {left_content_fills} fills")
        print(f"Right signature content: {right_content_lines} lines, {right_content_fills} fills")
        print(f"Total content elements: {left_content_lines + right_content_lines + left_content_fills + right_content_fills}")
        
        pdf_document.close()
        
        return {
            'left_lines': left_content_lines,
            'left_fills': left_content_fills,
            'right_lines': right_content_lines,
            'right_fills': right_content_fills,
            'total_elements': left_content_lines + right_content_lines + left_content_fills + right_content_fills
        }
        
    except Exception as e:
        print(f"Error: {e}")
        return None

print("="*70)
print("ANALYZING ACTUAL SIGNATURE/STAMP CONTENT")
print("="*70)

result1 = analyze_actual_signatures('Contract-with-stamp-and-signature.pdf')
print()
result2 = analyze_actual_signatures('extracted_document.pdf')

print("\n" + "="*70)
print("COMPARISON:")
print("="*70)
if result1 and result2:
    print(f"With stamp/signature - Left: {result1['left_lines']}L+{result1['left_fills']}F, Right: {result1['right_lines']}L+{result1['right_fills']}F, Total: {result1['total_elements']}")
    print(f"Original document    - Left: {result2['left_lines']}L+{result2['left_fills']}F, Right: {result2['right_lines']}L+{result2['right_fills']}F, Total: {result2['total_elements']}")
    
    difference = result1['total_elements'] - result2['total_elements']
    print(f"Difference: {difference} elements")
    
    if difference > 0:
        print("✅ Contract with stamp/signature has MORE content elements (likely has actual signatures)")
    else:
        print("❌ No significant difference detected")