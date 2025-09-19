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

def find_word_bbox(page, target_word):
    """Find the exact bounding box of a specific word on a page"""
    text_dict = page.get_text("dict")
    word_positions = []
    
    for block in text_dict.get("blocks", []):
        if "lines" in block:
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    span_bbox = span.get('bbox')
                    
                    if target_word.lower() in text.lower() and span_bbox:
                        # Find the exact position of the word within the span
                        words = text.split()
                        current_pos = 0
                        
                        for word in words:
                            if target_word.lower() in word.lower():
                                # Calculate word position more precisely
                                char_width = (span_bbox[2] - span_bbox[0]) / len(text)
                                word_start = current_pos
                                word_end = current_pos + len(word)
                                
                                word_left = span_bbox[0] + (word_start * char_width)
                                word_right = span_bbox[0] + (word_end * char_width)
                                word_bbox = (word_left, span_bbox[1], word_right, span_bbox[3])
                                
                                word_positions.append({
                                    'word': word,
                                    'bbox': word_bbox,
                                    'full_text': text,
                                    'span_bbox': span_bbox
                                })
                            current_pos += len(word) + 1  # +1 for space
    
    return word_positions

def check_for_underline_near_word(page, word_bbox, threshold=5):
    """Check for horizontal lines near a specific word"""
    drawings = page.get_drawings()
    text_bottom = word_bbox[3]
    text_left = word_bbox[0]
    text_right = word_bbox[2]
    
    underlines_found = []
    
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
                        
                        # Check multiple positions: below, above, and through the text
                        distance_below = line_y - text_bottom
                        distance_above = word_bbox[1] - line_y
                        
                        if (-threshold <= distance_below <= threshold) or (-threshold <= distance_above <= threshold):
                            # Check horizontal overlap
                            overlap = min(text_right, line_right) - max(text_left, line_left)
                            if overlap > 0:
                                underlines_found.append({
                                    'drawing_index': i,
                                    'line_y': line_y,
                                    'distance_below': distance_below,
                                    'distance_above': distance_above,
                                    'overlap': overlap,
                                    'line_coords': (line_left, line_y, line_right, line_y)
                                })
    
    return underlines_found

try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    target_words = ["weekly", "monthly"]
    
    print("=== SEARCHING FOR SPECIFIC WORDS AND THEIR UNDERLINES ===")
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        print(f"\n--- PAGE {page_num + 1} ---")
        
        for target_word in target_words:
            word_positions = find_word_bbox(page, target_word)
            
            if word_positions:
                print(f"\nFound '{target_word}' on page {page_num + 1}:")
                
                for pos in word_positions:
                    print(f"  Word: '{pos['word']}'")
                    print(f"  Full text: '{pos['full_text']}'")
                    print(f"  Word bbox: {pos['bbox']}")
                    
                    # Check for underlines
                    underlines = check_for_underline_near_word(page, pos['bbox'])
                    
                    if underlines:
                        print(f"  *** UNDERLINES FOUND: ***")
                        for underline in underlines:
                            print(f"    Drawing {underline['drawing_index']}: line at y={underline['line_y']}")
                            print(f"    Distance below text: {underline['distance_below']}")
                            print(f"    Distance above text: {underline['distance_above']}")
                            print(f"    Overlap with word: {underline['overlap']}")
                    else:
                        print(f"  No underlines found near this word")
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()