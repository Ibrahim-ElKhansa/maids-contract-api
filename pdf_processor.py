import base64
import io
import fitz  # PyMuPDF
import re
from typing import List, Set
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Class to handle PDF processing and underline extraction."""
    
    def __init__(self):
        self.underlined_words = set()
    
    def decode_base64_pdf(self, base64_string: str) -> bytes:
        """
        Decode base64 string to PDF bytes.
        
        Args:
            base64_string: Base64 encoded PDF content
            
        Returns:
            bytes: PDF content as bytes
            
        Raises:
            ValueError: If base64 string is invalid
        """
        try:
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            pdf_bytes = base64.b64decode(base64_string)
            return pdf_bytes
        except Exception as e:
            logger.error(f"Error decoding base64 PDF: {str(e)}")
            raise ValueError(f"Invalid base64 PDF data: {str(e)}")
    
    def extract_underlined_words(self, pdf_bytes: bytes) -> dict:
        """
        Extract underlined word counts from page 2, signature analysis from last page, and AED 3500 count.
        
        Args:
            pdf_bytes: PDF content as bytes
            
        Returns:
            dict: Dictionary with status, underline counts, AED count, and signature counts
            
        Raises:
            ValueError: If PDF cannot be processed
        """
        try:
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            logger.info(f"Processing PDF with {pdf_document.page_count} pages")
            
            # Get underlined word counts from page 2 only
            word_counts = self._get_page2_underlined_counts(pdf_document)
            
            # Get signature analysis from last page
            signature_counts = self._analyze_last_page_signatures(pdf_document)
            
            # Count AED 3500 occurrences throughout the PDF
            aed_count = self._count_aed_occurrences(pdf_document)
            
            pdf_document.close()
            
            # Format as requested new structure
            result = {
                "status": "success",
                "hour": word_counts['hour'],
                "day": word_counts['day'],
                "week": word_counts['week'],
                "month": word_counts['month'],
                "aed_3500_count": aed_count,
                "left_stamp": signature_counts['left_elements'],
                "right_signature": signature_counts['right_elements']
            }
            
            logger.info(f"Analysis results: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return {
                "status": "error",
                "hour": 0,
                "day": 0,
                "week": 0,
                "month": 0,
                "aed_3500_count": 0,
                "left_stamp": 0,
                "right_signature": 0,
                "error_message": str(e)
            }
    
    def _get_page2_underlined_counts(self, pdf_document):
        """Get underlined word counts for hour/day/week/month from page 2 only"""
        target_words = ["hour", "day", "week", "month"]
        word_counts = {word: 0 for word in target_words}
        
        # Return zeros if there's no page 2
        if pdf_document.page_count < 2:
            logger.info("PDF has less than 2 pages, returning zero counts")
            return word_counts
        
        # Process page 2 (index 1)
        page = pdf_document[1]
        logger.info("Processing page 2 for underlined target words")
        
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
        
        logger.info(f"Page 2: Found {len(horizontal_lines)} horizontal lines")
        
        # Get text and find target words
        text_dict = page.get_text("dict")
        
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
                                    
                                    # Calculate character width for positioning
                                    char_width = (span_bbox[2] - span_bbox[0]) / len(text) if len(text) > 0 else 0
                                    
                                    # Calculate word bbox
                                    word_left = span_bbox[0] + (pos * char_width)
                                    word_right = span_bbox[0] + ((pos + len(target)) * char_width)
                                    word_bbox = (word_left, span_bbox[1], word_right, span_bbox[3])
                                    
                                    # Check for underlines
                                    is_underlined = False
                                    for h_line in horizontal_lines:
                                        text_bottom = word_bbox[3]
                                        text_top = word_bbox[1]
                                        
                                        # Check distances (more lenient for detection)
                                        distance_below = h_line['y'] - text_bottom
                                        distance_above = text_top - h_line['y']
                                        
                                        if (-10 <= distance_below <= 15) or (-10 <= distance_above <= 10):
                                            # Check horizontal overlap
                                            overlap_left = max(word_bbox[0], h_line['left'])
                                            overlap_right = min(word_bbox[2], h_line['right'])
                                            overlap = overlap_right - overlap_left
                                            
                                            if overlap > 0:  # Any overlap
                                                word_width = word_bbox[2] - word_bbox[0]
                                                overlap_percentage = (overlap / word_width) * 100 if word_width > 0 else 0
                                                
                                                if overlap_percentage > 25:  # At least 25% overlap
                                                    is_underlined = True
                                                    break
                                    
                                    if is_underlined:
                                        word_counts[target] += 1
                                        logger.info(f"Found underlined '{target}' in text: '{text}'")
                                    
                                    start_pos = pos + 1
        
        logger.info(f"Page 2 underlined counts: {word_counts}")
        return word_counts

    def _analyze_last_page_signatures(self, pdf_document):
        """Analyze signature boxes on the last page for ANY content (drawings, images, text)
        
        Determines signature box layout by searching for company strings on the LAST PAGE:
        - If "Maids CC Domestic Workers" found: Uses high boxes (Y: 425-537)
        - If "Al Mustaqeem Domestic Workers" found: Uses low boxes (Y: 508-608)
        
        Then counts ANY content found inside the determined signature boxes.
        """
        signature_counts = {
            'left_elements': 0,
            'right_elements': 0
        }
        
        # Return zeros if there are no pages
        if pdf_document.page_count == 0:
            logger.info("PDF has no pages, returning zero signature counts")
            return signature_counts
        
        # Process last page
        last_page_num = pdf_document.page_count - 1
        last_page = pdf_document[last_page_num]
        logger.info(f"Analyzing signatures on last page (page {last_page_num + 1})")
        
        # Search the last page for company strings to determine layout
        signature_layout = None  # Will be "high" or "low"
        
        logger.info("Searching last page for company identification strings...")
        
        text_dict = last_page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "").strip()
                        
                        # Check for Maids CC company string
                        if "Maids CC Domestic Workers" in text:
                            signature_layout = "high"
                            logger.info(f"Found 'Maids CC Domestic Workers' on last page - Using HIGH layout")
                            break
                        
                        # Check for Al Mustaqeem company string  
                        elif "Al Mustaqeem Domestic Workers" in text:
                            signature_layout = "low"
                            logger.info(f"Found 'Al Mustaqeem Domestic Workers' on last page - Using LOW layout")
                            break
                    
                    if signature_layout:
                        break
                if signature_layout:
                    break
        
        # Default to high layout if no company string found
        if not signature_layout:
            signature_layout = "high"
            logger.warning("No company identification string found on last page, defaulting to HIGH layout")
        
        # Define signature content areas based on detected company type
        if signature_layout == "high":
            # Maids CC layout coordinates (high boxes)
            left_content_area = (95, 425, 290, 537)   # Left signature box
            right_content_area = (300, 425, 500, 537)  # Right signature box
            logger.info("Using MAIDS CC layout coordinates: Left(95,425,290,537) Right(300,425,500,537)")
        else:  # low layout
            # Al Mustaqeem layout coordinates (low boxes)
            left_content_area = (95, 508, 290, 608)   # Left signature box
            right_content_area = (300, 508, 500, 608)  # Right signature box
            logger.info("Using AL MUSTAQEEM layout coordinates: Left(95,508,290,608) Right(300,508,500,608)")
        
        # Count different types of content
        left_count = 0
        right_count = 0
        
        # 1. Count drawings (any drawing content inside the boxes)
        drawings = last_page.get_drawings()
        logger.info(f"Found {len(drawings)} drawings on last page")
        
        for drawing in drawings:
            # Get drawing center point or any point within the drawing
            center_x, center_y = None, None
            
            if 'rect' in drawing and drawing['rect']:
                rect = drawing['rect']
                center_x = (rect.x0 + rect.x1) / 2
                center_y = (rect.y0 + rect.y1) / 2
            elif drawing['type'] == 's' and drawing['items']:
                # For line drawings, use the first point
                item = drawing['items'][0]
                if item[0] == 'l':  # line
                    center_x = item[1][0]  # start point x
                    center_y = item[1][1]  # start point y
            
            if center_x is not None and center_y is not None:
                # Check if drawing point is inside signature areas (inclusive boundaries)
                in_left = (left_content_area[0] <= center_x <= left_content_area[2] and
                          left_content_area[1] <= center_y <= left_content_area[3])
                in_right = (right_content_area[0] <= center_x <= right_content_area[2] and
                           right_content_area[1] <= center_y <= right_content_area[3])
                
                if in_left:
                    left_count += 1
                    logger.info(f"Drawing in left signature area: type={drawing['type']}, center=({center_x:.1f}, {center_y:.1f})")
                elif in_right:
                    right_count += 1
                    logger.info(f"Drawing in right signature area: type={drawing['type']}, center=({center_x:.1f}, {center_y:.1f})")
        
        # 2. Count images
        image_list = last_page.get_images()
        logger.info(f"Found {len(image_list)} images on last page")
        
        for img_index, img in enumerate(image_list):
            try:
                img_rect = last_page.get_image_bbox(img[7])  # img[7] is the image xref
                center_x = (img_rect.x0 + img_rect.x1) / 2
                center_y = (img_rect.y0 + img_rect.y1) / 2
                
                # Check if image is in signature areas
                in_left = (left_content_area[0] <= center_x <= left_content_area[2] and
                          left_content_area[1] <= center_y <= left_content_area[3])
                in_right = (right_content_area[0] <= center_x <= right_content_area[2] and
                           right_content_area[1] <= center_y <= right_content_area[3])
                
                if in_left:
                    left_count += 1
                    logger.info(f"Image in left signature area: center=({center_x:.1f}, {center_y:.1f}), size={img_rect.width:.1f}x{img_rect.height:.1f}")
                elif in_right:
                    right_count += 1
                    logger.info(f"Image in right signature area: center=({center_x:.1f}, {center_y:.1f}), size={img_rect.width:.1f}x{img_rect.height:.1f}")
            except Exception as e:
                logger.warning(f"Error analyzing image {img_index}: {e}")
        
        # 3. Count all text content inside signature boxes (excluding layout detection labels)
        for block in text_dict["blocks"]:
            if "bbox" in block:
                bbox = block["bbox"]
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                
                # Check if text is inside signature areas (inclusive boundaries)
                in_left = (left_content_area[0] <= center_x <= left_content_area[2] and
                          left_content_area[1] <= center_y <= left_content_area[3])
                in_right = (right_content_area[0] <= center_x <= right_content_area[2] and
                           right_content_area[1] <= center_y <= right_content_area[3])
                
                if in_left or in_right:
                    # Get text content
                    text_content = ""
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text_content += span["text"]
                    
                    # Count ALL text content inside the boxes
                    if text_content.strip():
                        area = "left" if in_left else "right"
                        if in_left:
                            left_count += 1
                        else:
                            right_count += 1
                        logger.info(f"Text in {area} signature area: '{text_content.strip()}'")
        
        signature_counts['left_elements'] = left_count
        signature_counts['right_elements'] = right_count
        
        logger.info(f"Final signature analysis: left={left_count}, right={right_count}")
        
        return signature_counts

    def _count_aed_occurrences(self, pdf_document):
        """Count occurrences of 'AED 3500' string throughout the entire PDF"""
        aed_count = 0
        search_string = "AED 3500"
        
        logger.info(f"Searching for '{search_string}' throughout the PDF")
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span.get("text", "").strip()
                            # Count occurrences in this text span
                            count_in_span = text.count(search_string)
                            if count_in_span > 0:
                                aed_count += count_in_span
                                logger.info(f"Found {count_in_span} occurrence(s) of '{search_string}' on page {page_num + 1}: '{text}'")
        
        logger.info(f"Total '{search_string}' occurrences: {aed_count}")
        return aed_count

    def _extract_underlined_from_drawings(self, pdf_document):
        """Extract underlined words by detecting horizontal lines near text, focusing on target words"""
        target_words = ["hour", "day", "week", "month"]
        underlined_words = []
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            logger.info(f"Processing page {page_num + 1}")
            
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
            
            logger.info(f"Page {page_num + 1}: Found {len(horizontal_lines)} horizontal lines")
            
            # Get text and check for target words only
            text_dict = page.get_text("dict")
            page_underlined_words = []
            
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
                                        if word.strip():
                                            # Check if this word contains any of our target words
                                            word_clean = word.strip().lower().rstrip('.,!?()[]{}/:;')
                                            target_found = None
                                            for target in target_words:
                                                if target in word_clean:
                                                    target_found = target
                                                    break
                                            
                                            if target_found:
                                                # Find exact character position of word in text
                                                word_start_in_text = text.find(word, current_char_pos)
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
                                                    
                                                    if is_underlined:
                                                        page_underlined_words.append(target_found)
                                                        logger.info(f"Found underlined target word: '{target_found}' in '{word}' on page {page_num + 1}")
                                                
                                                current_char_pos = word_end_in_text
                                            else:
                                                current_char_pos += len(word) + 1
            
            logger.info(f"Page {page_num + 1}: Found {len(page_underlined_words)} underlined target words: {page_underlined_words}")
            underlined_words.extend(page_underlined_words)
        
        return underlined_words
    
    def _extract_underlined_from_html(self, html_content: str) -> Set[str]:
        """
        Extract underlined words from HTML content.
        
        Args:
            html_content: HTML content from PDF page
            
        Returns:
            Set[str]: Set of underlined words
        """
        underlined_words = set()
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Method 1: Look for <u> tags (underline tags)
            underline_tags = soup.find_all('u')
            for tag in underline_tags:
                text = tag.get_text()
                words = self._extract_words_from_text(text)
                if words:
                    underlined_words.update(words)
                    logger.info(f"Found underlined text in <u> tag: '{text}' -> {words}")
            
            # Method 2: Look for style attributes with text-decoration: underline
            elements_with_style = soup.find_all(attrs={"style": True})
            for element in elements_with_style:
                style = element.get('style', '').lower()
                if 'text-decoration' in style and 'underline' in style:
                    text = element.get_text()
                    words = self._extract_words_from_text(text)
                    if words:
                        underlined_words.update(words)
                        logger.info(f"Found underlined text in style attribute: '{text}' -> {words}")
            
            # Method 3: Look for CSS classes that might indicate underlining
            elements_with_class = soup.find_all(attrs={"class": True})
            for element in elements_with_class:
                classes = element.get('class', [])
                class_str = ' '.join(classes).lower()
                if 'underline' in class_str or 'underlin' in class_str:
                    text = element.get_text()
                    words = self._extract_words_from_text(text)
                    if words:
                        underlined_words.update(words)
                        logger.info(f"Found underlined text in CSS class: '{text}' -> {words}")
            
            # Method 4: Look for span elements with specific styling
            spans = soup.find_all('span')
            for span in spans:
                style = span.get('style', '').lower()
                if any(keyword in style for keyword in ['underline', 'border-bottom', 'text-decoration']):
                    text = span.get_text()
                    words = self._extract_words_from_text(text)
                    if words:
                        underlined_words.update(words)
                        logger.info(f"Found underlined text in span styling: '{text}' -> {words}")
            
            # Method 5: Log all HTML content for debugging (first 1000 chars)
            logger.info(f"HTML content sample: {html_content[:1000]}...")
            
        except Exception as e:
            logger.warning(f"Error extracting from HTML: {str(e)}")
        
        return underlined_words
    
    def _extract_from_annotations(self, page) -> Set[str]:
        """Extract underlined words from PDF annotations."""
        underlined_words = set()
        
        try:
            # Get all annotations on the page
            annotations = page.annots()
            
            for annot in annotations:
                # Check if annotation is an underline
                if annot.type[1] == 'Underline':
                    # Get the rectangle area of the annotation
                    rect = annot.rect
                    
                    # Extract text from the annotation area
                    text_instances = page.get_textbox(rect)
                    if text_instances:
                        words = self._extract_words_from_text(text_instances)
                        underlined_words.update(words)
                        
        except Exception as e:
            logger.warning(f"Error extracting from annotations: {str(e)}")
        
        return underlined_words
    
    def _extract_from_text_formatting(self, text_dict: dict) -> Set[str]:
        """Extract underlined words from text formatting information."""
        underlined_words = set()
        
        try:
            # Parse text dictionary for formatting information
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            # Check span flags for underline formatting
                            flags = span.get("flags", 0)
                            
                            # Flag 4 typically indicates underline in PyMuPDF
                            if flags & 4:  # Underline flag
                                text = span.get("text", "")
                                words = self._extract_words_from_text(text)
                                underlined_words.update(words)
                                logger.info(f"Found underlined text via flags: '{text}' -> {words}")
                            
                            # Also check for explicit underline in font name or style
                            font = span.get("font", "").lower()
                            if "underline" in font:
                                text = span.get("text", "")
                                words = self._extract_words_from_text(text)
                                underlined_words.update(words)
                                logger.info(f"Found underlined text via font: '{text}' -> {words}")
                                
        except Exception as e:
            logger.warning(f"Error extracting from text formatting: {str(e)}")
        
        return underlined_words
    
    def _extract_from_drawings(self, page) -> Set[str]:
        """Extract underlined words by analyzing page drawings and shapes."""
        underlined_words = set()
        
        try:
            # Get page drawings
            drawings = page.get_drawings()
            text_blocks = page.get_text("dict")
            
            # Look for horizontal lines that might be underlines
            horizontal_lines = []
            for drawing in drawings:
                for path in drawing.get("items", []):
                    if path[0] == "l":  # Line
                        x1, y1, x2, y2 = path[1:5]
                        # Check if it's a mostly horizontal line
                        if abs(y2 - y1) < 5 and abs(x2 - x1) > 10:
                            horizontal_lines.append({
                                'y': (y1 + y2) / 2,
                                'x1': min(x1, x2),
                                'x2': max(x1, x2)
                            })
            
            # For each horizontal line, find text above it that might be underlined
            for line in horizontal_lines:
                for block in text_blocks.get("blocks", []):
                    if "lines" in block:
                        for text_line in block["lines"]:
                            # Check if text is close above the line
                            bbox = text_line.get("bbox", [])
                            if bbox and len(bbox) >= 4:
                                text_bottom = bbox[3]
                                if abs(text_bottom - line['y']) < 10:  # Text close to line
                                    # Extract text from this line
                                    for span in text_line.get("spans", []):
                                        text = span.get("text", "")
                                        words = self._extract_words_from_text(text)
                                        if words:
                                            underlined_words.update(words)
                                            logger.info(f"Found underlined text via drawings: '{text}' -> {words}")
                                
        except Exception as e:
            logger.warning(f"Error extracting from drawings: {str(e)}")
        
        return underlined_words
    
    def _extract_from_font_styles(self, text_dict: dict) -> Set[str]:
        """Extract words that might be underlined based on font style analysis."""
        underlined_words = set()
        
        try:
            # Look for fonts with specific characteristics that might indicate underlining
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            font = span.get("font", "").lower()
                            flags = span.get("flags", 0)
                            
                            # Check for various indicators
                            underline_indicators = [
                                "underline" in font,
                                "underlin" in font,
                                flags & 4,  # Underline flag
                                flags & 16,  # Sometimes underline is flag 16
                            ]
                            
                            if any(underline_indicators):
                                text = span.get("text", "")
                                words = self._extract_words_from_text(text)
                                if words:
                                    underlined_words.update(words)
                                    logger.info(f"Found underlined text via font style: '{text}' -> {words}")
                                
        except Exception as e:
            logger.warning(f"Error extracting from font styles: {str(e)}")
        
        return underlined_words
    
    def _extract_words_from_text(self, text: str) -> Set[str]:
        """
        Extract individual words from text string.
        
        Args:
            text: Text string to extract words from
            
        Returns:
            Set[str]: Set of individual words
        """
        if not text:
            return set()
        
        # Use regex to extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', text)
        return set(word.strip() for word in words if word.strip())

# Create a global instance
pdf_processor = PDFProcessor()

def process_pdf_base64(base64_string: str) -> dict:
    """
    Main function to process base64 PDF and extract all analysis data.
    
    Args:
        base64_string: Base64 encoded PDF content
        
    Returns:
        dict: Dictionary with status and all analysis results
        
    Raises:
        ValueError: If processing fails
    """
    pdf_bytes = pdf_processor.decode_base64_pdf(base64_string)
    result = pdf_processor.extract_underlined_words(pdf_bytes)
    return result