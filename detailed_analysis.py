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

def detailed_word_analysis(pdf_document, target_words):
    """Find ALL instances of target words and analyze their underline status with detailed debugging"""
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        print(f"\n{'='*60}")
        print(f"PAGE {page_num + 1} ANALYSIS")
        print(f"{'='*60}")
        
        # Get all horizontal lines from drawings
        drawings = page.get_drawings()
        horizontal_lines = []
        for i, drawing in enumerate(drawings):
            if drawing['type'] == 's':  # stroke/line
                for item in drawing['items']:
                    if item[0] == 'l':  # line
                        start_point = item[1]
                        end_point = item[2]
                        
                        # Check if it's a horizontal line
                        if abs(start_point.y - end_point.y) < 1:
                            line_y = start_point.y
                            line_left = min(start_point.x, end_point.x)
                            line_right = max(start_point.x, end_point.x)
                            horizontal_lines.append({
                                'y': line_y,
                                'left': line_left,
                                'right': line_right,
                                'drawing_index': i
                            })
        
        print(f"Found {len(horizontal_lines)} horizontal lines on this page")
        
        # Get text and find ALL instances of target words
        text_dict = page.get_text("dict")
        word_instances = []
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        span_bbox = span.get('bbox')
                        
                        if text and span_bbox:
                            # Look for target words in the text (case insensitive)
                            text_lower = text.lower()
                            for target in target_words:
                                target_lower = target.lower()
                                start_pos = 0
                                while True:
                                    pos = text_lower.find(target_lower, start_pos)
                                    if pos == -1:
                                        break
                                    
                                    # Extract the actual word from original text
                                    actual_word = text[pos:pos+len(target)]
                                    
                                    # Calculate character width for positioning
                                    char_width = (span_bbox[2] - span_bbox[0]) / len(text) if len(text) > 0 else 0
                                    
                                    # Calculate word bbox
                                    word_left = span_bbox[0] + (pos * char_width)
                                    word_right = span_bbox[0] + ((pos + len(target)) * char_width)
                                    word_bbox = (word_left, span_bbox[1], word_right, span_bbox[3])
                                    
                                    word_instances.append({
                                        'target': target_lower,
                                        'actual_word': actual_word,
                                        'full_text': text,
                                        'bbox': word_bbox,
                                        'char_pos': pos
                                    })
                                    
                                    start_pos = pos + 1
        
        print(f"\nFound {len(word_instances)} instances of target words:")
        
        # Check underline status for each instance
        underlined_count = {word: 0 for word in target_words}
        total_count = {word: 0 for word in target_words}
        
        for i, instance in enumerate(word_instances):
            target = instance['target']
            total_count[target] += 1
            
            print(f"\n{i+1}. Target: '{target}' -> Actual: '{instance['actual_word']}'")
            print(f"   Context: '{instance['full_text']}'")
            print(f"   Bbox: {instance['bbox']}")
            
            # Check for underlines with more detailed analysis
            is_underlined = False
            closest_line_distance = float('inf')
            best_overlap = 0
            
            for j, h_line in enumerate(horizontal_lines):
                text_bottom = instance['bbox'][3]
                text_top = instance['bbox'][1]
                
                # Check distances
                distance_below = h_line['y'] - text_bottom
                distance_above = text_top - h_line['y']
                
                # Check horizontal overlap
                overlap_left = max(instance['bbox'][0], h_line['left'])
                overlap_right = min(instance['bbox'][2], h_line['right'])
                overlap = overlap_right - overlap_left
                
                # More lenient threshold for detection
                if (-10 <= distance_below <= 15) or (-10 <= distance_above <= 10):
                    if overlap > 0:  # Any overlap
                        word_width = instance['bbox'][2] - instance['bbox'][0]
                        overlap_percentage = (overlap / word_width) * 100 if word_width > 0 else 0
                        
                        print(f"     Line {j}: y={h_line['y']:.1f}, dist_below={distance_below:.1f}, dist_above={distance_above:.1f}")
                        print(f"              overlap={overlap:.1f} ({overlap_percentage:.1f}% of word width)")
                        
                        if overlap_percentage > 25:  # Lower threshold
                            is_underlined = True
                            if abs(distance_below) < abs(closest_line_distance):
                                closest_line_distance = distance_below
                                best_overlap = overlap_percentage
            
            if is_underlined:
                underlined_count[target] += 1
                print(f"   *** UNDERLINED *** (best: {best_overlap:.1f}% overlap, {closest_line_distance:.1f}px below)")
            else:
                print(f"   not underlined")
        
        print(f"\nPage {page_num + 1} Summary:")
        for target in target_words:
            print(f"  {target.upper()}: {underlined_count[target]} underlined / {total_count[target]} total")

try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    target_words = ["hour", "day", "week", "month"]
    
    print("=== DETAILED ANALYSIS OF ALL TARGET WORD INSTANCES ===")
    
    detailed_word_analysis(pdf_document, target_words)
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()