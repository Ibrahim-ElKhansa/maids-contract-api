import fitz  # PyMuPDF
import os

def analyze_signature_boxes(pdf_path, pdf_name):
    """Analyze what's actually in the signature boxes"""
    print(f"\n{'='*80}")
    print(f"ANALYZING SIGNATURE BOXES: {pdf_name}")
    print(f"{'='*80}")
    
    # Open the PDF
    pdf_document = fitz.open(pdf_path)
    
    # Get the last page
    last_page_num = pdf_document.page_count - 1
    last_page = pdf_document[last_page_num]
    
    print(f"Last page number: {last_page_num + 1}")
    
    # Define signature areas based on the actual table structure
    left_content_area = (90, 410, 297, 544)   # Left signature box content area
    right_content_area = (297, 410, 505, 544)  # Right signature box content area
    
    print(f"Left signature box: {left_content_area}")
    print(f"Right signature box: {right_content_area}")
    
    # Check drawings
    print(f"\n--- DRAWINGS ANALYSIS ---")
    drawings = last_page.get_drawings()
    print(f"Total drawings on last page: {len(drawings)}")
    
    left_drawings = 0
    right_drawings = 0
    
    for i, drawing in enumerate(drawings):
        # Get the bounding box of the drawing
        if 'rect' in drawing and drawing['rect']:
            rect = drawing['rect']
            center_x = (rect.x0 + rect.x1) / 2
            center_y = (rect.y0 + rect.y1) / 2
        else:
            # For line drawings, use the first point
            if drawing['type'] == 's' and drawing['items']:
                item = drawing['items'][0]
                if item[0] == 'l':  # line
                    center_x = item[1][0]  # start point x
                    center_y = item[1][1]  # start point y
                else:
                    continue
            else:
                continue
        
        # Check if drawing is in signature areas
        in_left = (left_content_area[0] <= center_x <= left_content_area[2] and
                   left_content_area[1] <= center_y <= left_content_area[3])
        in_right = (right_content_area[0] <= center_x <= right_content_area[2] and
                    right_content_area[1] <= center_y <= right_content_area[3])
        
        if in_left or in_right:
            area = "LEFT" if in_left else "RIGHT"
            print(f"  Drawing {i+1} in {area} box: Type={drawing['type']}, Center=({center_x:.1f}, {center_y:.1f})")
            if in_left:
                left_drawings += 1
            if in_right:
                right_drawings += 1
    
    # Check images
    print(f"\n--- IMAGES ANALYSIS ---")
    image_list = last_page.get_images()
    print(f"Total images on last page: {len(image_list)}")
    
    left_images = 0
    right_images = 0
    
    for img_index, img in enumerate(image_list):
        # Get image bounding box
        try:
            img_rect = last_page.get_image_bbox(img[7])  # img[7] is the image xref
            center_x = (img_rect.x0 + img_rect.x1) / 2
            center_y = (img_rect.y0 + img_rect.y1) / 2
            
            # Check if image is in signature areas
            in_left = (left_content_area[0] <= center_x <= left_content_area[2] and
                       left_content_area[1] <= center_y <= left_content_area[3])
            in_right = (right_content_area[0] <= center_x <= right_content_area[2] and
                        right_content_area[1] <= center_y <= right_content_area[3])
            
            if in_left or in_right:
                area = "LEFT" if in_left else "RIGHT"
                print(f"  Image {img_index+1} in {area} box: Center=({center_x:.1f}, {center_y:.1f}), Size={img_rect.width:.1f}x{img_rect.height:.1f}")
                if in_left:
                    left_images += 1
                if in_right:
                    right_images += 1
        except Exception as e:
            print(f"  Error analyzing image {img_index+1}: {e}")
    
    # Check text blocks
    print(f"\n--- TEXT ANALYSIS ---")
    text_dict = last_page.get_text("dict")
    
    left_text_blocks = 0
    right_text_blocks = 0
    
    for block in text_dict["blocks"]:
        if "bbox" in block:
            bbox = block["bbox"]
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            
            # Check if text is in signature areas
            in_left = (left_content_area[0] <= center_x <= left_content_area[2] and
                       left_content_area[1] <= center_y <= left_content_area[3])
            in_right = (right_content_area[0] <= center_x <= right_content_area[2] and
                        right_content_area[1] <= center_y <= right_content_area[3])
            
            if in_left or in_right:
                area = "LEFT" if in_left else "RIGHT"
                # Get text content
                text_content = ""
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_content += span["text"]
                
                if text_content.strip():
                    print(f"  Text in {area} box: '{text_content.strip()}' at ({center_x:.1f}, {center_y:.1f})")
                    if in_left:
                        left_text_blocks += 1
                    if in_right:
                        right_text_blocks += 1
    
    # Summary
    print(f"\n--- SUMMARY ---")
    print(f"Left signature box content:")
    print(f"  - Drawings: {left_drawings}")
    print(f"  - Images: {left_images}")
    print(f"  - Text blocks: {left_text_blocks}")
    print(f"  - Total: {left_drawings + left_images + left_text_blocks}")
    
    print(f"Right signature box content:")
    print(f"  - Drawings: {right_drawings}")
    print(f"  - Images: {right_images}")
    print(f"  - Text blocks: {right_text_blocks}")
    print(f"  - Total: {right_drawings + right_images + right_text_blocks}")
    
    pdf_document.close()

if __name__ == "__main__":
    # Analyze both PDFs
    if os.path.exists("Contract-with-stamp-and-signature.pdf"):
        analyze_signature_boxes("Contract-with-stamp-and-signature.pdf", "Contract with stamp and signature")
    
    if os.path.exists("extracted_document.pdf"):
        analyze_signature_boxes("extracted_document.pdf", "Original extracted document")