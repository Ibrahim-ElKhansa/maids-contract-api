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

def find_underlined_target_words(pdf_document, target_words):
    """Find and count underlined instances of specific target words"""
    word_counts = {word.lower(): 0 for word in target_words}
    word_details = {word.lower(): [] for word in target_words}
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        
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
        
        # Get text and check for target words
        text_dict = page.get_text("dict")
        
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
                                    word_clean = word.strip().lower().rstrip('.,!?()[]{}/:;')
                                    
                                    # Check if this word is one of our targets
                                    if word_clean in word_counts:
                                        # Find exact character position of word in text
                                        word_start_in_text = text.lower().find(word.lower(), current_char_pos)
                                        if word_start_in_text >= 0:
                                            word_end_in_text = word_start_in_text + len(word)
                                            
                                            # Calculate word bbox
                                            word_left = span_bbox[0] + (word_start_in_text * char_width)
                                            word_right = span_bbox[0] + (word_end_in_text * char_width)
                                            word_bbox = (word_left, span_bbox[1], word_right, span_bbox[3])
                                            
                                            # Check against all horizontal lines
                                            is_underlined = False
                                            for h_line in horizontal_lines:
                                                text_bottom = word_bbox[3]
                                                text_top = word_bbox[1]
                                                
                                                # Check if line is near the text (within threshold)
                                                distance_below = h_line['y'] - text_bottom
                                                distance_above = text_top - h_line['y']
                                                
                                                if (-5 <= distance_below <= 10) or (-5 <= distance_above <= 5):
                                                    # Check horizontal overlap
                                                    overlap_left = max(word_bbox[0], h_line['left'])
                                                    overlap_right = min(word_bbox[2], h_line['right'])
                                                    overlap = overlap_right - overlap_left
                                                    
                                                    if overlap > len(word) * char_width * 0.5:  # At least 50% overlap
                                                        is_underlined = True
                                                        break
                                            
                                            # Record the result
                                            status = "UNDERLINED" if is_underlined else "not underlined"
                                            word_details[word_clean].append({
                                                'page': page_num + 1,
                                                'word': word,
                                                'full_text': text,
                                                'bbox': word_bbox,
                                                'underlined': is_underlined
                                            })
                                            
                                            if is_underlined:
                                                word_counts[word_clean] += 1
                                            
                                            print(f"Page {page_num + 1}: '{word}' ({word_clean}) - {status}")
                                            print(f"  Context: '{text}'")
                                            
                                            current_char_pos = word_end_in_text
                                    else:
                                        current_char_pos += len(word) + 1
    
    return word_counts, word_details

try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    target_words = ["hour", "day", "week", "month"]
    
    print("=== CHECKING FOR UNDERLINED TARGET WORDS ===")
    print(f"Looking for: {target_words}")
    print()
    
    word_counts, word_details = find_underlined_target_words(pdf_document, target_words)
    
    print("\n" + "="*50)
    print("FINAL RESULTS:")
    print("="*50)
    
    total_underlined = 0
    for word in target_words:
        count = word_counts[word.lower()]
        total_underlined += count
        print(f"{word.upper()}: {count} underlined instances")
        
        if count > 0:
            print(f"  Details for '{word}':")
            for detail in word_details[word.lower()]:
                if detail['underlined']:
                    print(f"    Page {detail['page']}: '{detail['word']}' in context '{detail['full_text']}'")
        print()
    
    print(f"TOTAL UNDERLINED TARGET WORDS: {total_underlined}")
    
    if total_underlined == 0:
        print("\n⚠️  No target words are underlined in this PDF")
        print("This means either:")
        print("1. None of hour/day/week/month are actually underlined")
        print("2. The underlining method is different than expected")
        print("3. The words might be part of compound words or have different formatting")
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()