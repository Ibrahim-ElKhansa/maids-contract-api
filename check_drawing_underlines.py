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

def check_underline_proximity(text_bbox, drawings, threshold=5):
    """Check if any horizontal line is close enough below the text to be an underline"""
    text_bottom = text_bbox[3]  # Bottom Y coordinate of text
    text_left = text_bbox[0]    # Left X coordinate
    text_right = text_bbox[2]   # Right X coordinate
    
    for i, drawing in enumerate(drawings):
        if drawing['type'] == 's':  # stroke/line
            for item in drawing['items']:
                if item[0] == 'l':  # line
                    start_point = item[1]
                    end_point = item[2]
                    
                    # Check if it's a horizontal line
                    if abs(start_point.y - end_point.y) < 1:  # Horizontal line
                        line_y = start_point.y
                        line_left = min(start_point.x, end_point.x)
                        line_right = max(start_point.x, end_point.x)
                        
                        # Check if line is below text within threshold
                        if text_bottom <= line_y <= text_bottom + threshold:
                            # Check if line overlaps horizontally with text
                            if (line_left <= text_right and line_right >= text_left):
                                return True, i, {
                                    'line_y': line_y,
                                    'text_bottom': text_bottom,
                                    'distance': line_y - text_bottom,
                                    'line_range': (line_left, line_right),
                                    'text_range': (text_left, text_right)
                                }
    return False, None, None

try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    print("=== CHECKING FOR UNDERLINES BASED ON DRAWING PROXIMITY ===")
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        print(f"\n--- PAGE {page_num + 1} ---")
        
        # Get all drawings
        drawings = page.get_drawings()
        
        # Get text with detailed formatting
        text_dict = page.get_text("dict")
        
        words_with_underlines = []
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            # Split into words and check each
                            words = text.split()
                            span_bbox = span.get('bbox')
                            
                            if span_bbox and words:
                                # Estimate word positions within the span
                                span_width = span_bbox[2] - span_bbox[0]
                                word_width = span_width / len(words)
                                
                                for word_idx, word in enumerate(words):
                                    # Estimate word bbox
                                    word_left = span_bbox[0] + (word_idx * word_width)
                                    word_right = word_left + word_width
                                    word_bbox = (word_left, span_bbox[1], word_right, span_bbox[3])
                                    
                                    # Check if this word has an underline
                                    has_underline, drawing_idx, details = check_underline_proximity(word_bbox, drawings)
                                    
                                    if has_underline:
                                        print(f"*** UNDERLINED WORD FOUND: '{word}' ***")
                                        print(f"  Word bbox: {word_bbox}")
                                        print(f"  Drawing index: {drawing_idx}")
                                        print(f"  Details: {details}")
                                        words_with_underlines.append(word)
        
        if words_with_underlines:
            print(f"Underlined words on page {page_num + 1}: {words_with_underlines}")
        else:
            print(f"No underlined words found on page {page_num + 1}")
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()