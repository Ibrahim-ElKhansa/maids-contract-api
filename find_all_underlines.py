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

def find_all_underlined_words(page):
    """Find all words that have horizontal lines near them (potential underlines)"""
    text_dict = page.get_text("dict")
    drawings = page.get_drawings()
    
    # Find all horizontal lines
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
    
    underlined_words = []
    
    # Check all text against all horizontal lines
    for block in text_dict.get("blocks", []):
        if "lines" in block:
            for line in block["lines"]:
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    span_bbox = span.get('bbox')
                    
                    if text and span_bbox:
                        words = text.split()
                        if words:
                            # Calculate character width for word positioning
                            char_width = (span_bbox[2] - span_bbox[0]) / len(text) if len(text) > 0 else 0
                            current_char_pos = 0
                            
                            for word in words:
                                if word.strip():  # Skip empty words
                                    # Find exact character position of word in text
                                    word_start_in_text = text.find(word, current_char_pos)
                                    if word_start_in_text >= 0:
                                        word_end_in_text = word_start_in_text + len(word)
                                        
                                        # Calculate word bbox
                                        word_left = span_bbox[0] + (word_start_in_text * char_width)
                                        word_right = span_bbox[0] + (word_end_in_text * char_width)
                                        word_bbox = (word_left, span_bbox[1], word_right, span_bbox[3])
                                        
                                        # Check against all horizontal lines
                                        for line in horizontal_lines:
                                            text_bottom = word_bbox[3]
                                            text_top = word_bbox[1]
                                            
                                            # Check if line is near the text (within 5 points)
                                            distance_below = line['y'] - text_bottom
                                            distance_above = text_top - line['y']
                                            
                                            if (-5 <= distance_below <= 10) or (-5 <= distance_above <= 5):
                                                # Check horizontal overlap
                                                overlap_left = max(word_bbox[0], line['left'])
                                                overlap_right = min(word_bbox[2], line['right'])
                                                overlap = overlap_right - overlap_left
                                                
                                                if overlap > len(word) * char_width * 0.5:  # At least 50% overlap
                                                    underlined_words.append({
                                                        'word': word,
                                                        'word_bbox': word_bbox,
                                                        'line_y': line['y'],
                                                        'distance_below': distance_below,
                                                        'distance_above': distance_above,
                                                        'overlap': overlap,
                                                        'drawing_index': line['drawing_index'],
                                                        'full_text': text
                                                    })
                                        
                                        current_char_pos = word_end_in_text
                                    else:
                                        current_char_pos += len(word) + 1
    
    return underlined_words

try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    print("=== FINDING ALL UNDERLINED WORDS IN THE ENTIRE PDF ===")
    
    all_underlined_words = []
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        print(f"\n--- PAGE {page_num + 1} ---")
        
        underlined_words = find_all_underlined_words(page)
        
        if underlined_words:
            print(f"Found {len(underlined_words)} underlined words:")
            for word_info in underlined_words:
                print(f"  *** '{word_info['word']}' ***")
                print(f"    Full text: '{word_info['full_text']}'")
                print(f"    Position: {word_info['word_bbox']}")
                print(f"    Line Y: {word_info['line_y']}")
                print(f"    Distance below: {word_info['distance_below']:.2f}")
                print(f"    Overlap: {word_info['overlap']:.2f}")
                print()
                all_underlined_words.append(word_info['word'])
        else:
            print("No underlined words found")
    
    print(f"\n=== SUMMARY ===")
    if all_underlined_words:
        print(f"All underlined words in the PDF: {list(set(all_underlined_words))}")
    else:
        print("No underlined words found in the entire PDF")
        print("\nThis could mean:")
        print("1. The PDF doesn't contain any underlined text")
        print("2. The underlines are created using a different method (annotations, text formatting)")
        print("3. The underlines are very subtle and not detected by this method")
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()