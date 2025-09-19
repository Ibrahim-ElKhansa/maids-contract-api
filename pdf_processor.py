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
    
    def extract_underlined_words(self, pdf_bytes: bytes) -> List[str]:
        """
        Extract underlined word counts from page 2 only, focusing on hour/day/week/month.
        
        Args:
            pdf_bytes: PDF content as bytes
            
        Returns:
            List[str]: List with counts in format ["hour:X", "day:X", "week:X", "month:X"]
            
        Raises:
            ValueError: If PDF cannot be processed
        """
        try:
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            logger.info(f"Processing PDF with {pdf_document.page_count} pages")
            
            # Get underlined word counts from page 2 only
            word_counts = self._get_page2_underlined_counts(pdf_document)
            
            pdf_document.close()
            
            # Format as requested: ["hour:X", "day:X", "week:X", "month:X"]
            result = [
                f"hour:{word_counts['hour']}",
                f"day:{word_counts['day']}",
                f"week:{word_counts['week']}",
                f"month:{word_counts['month']}"
            ]
            
            logger.info(f"Page 2 underlined word counts: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise ValueError(f"Error processing PDF: {str(e)}")
    
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

def process_pdf_base64(base64_string: str) -> List[str]:
    """
    Main function to process base64 PDF and extract underlined words.
    
    Args:
        base64_string: Base64 encoded PDF content
        
    Returns:
        List[str]: List of underlined words
        
    Raises:
        ValueError: If processing fails
    """
    pdf_bytes = pdf_processor.decode_base64_pdf(base64_string)
    underlined_words = pdf_processor.extract_underlined_words(pdf_bytes)
    return underlined_words