import fitz

def debug_all_drawings(pdf_path):
    """Debug all drawings to find the actual signature content"""
    try:
        pdf_document = fitz.open(pdf_path)
        last_page = pdf_document[pdf_document.page_count - 1]
        
        print(f"Debugging all drawings in {pdf_path}")
        
        drawings = last_page.get_drawings()
        
        for i, drawing in enumerate(drawings):
            print(f"\nDrawing {i+1}:")
            print(f"  Type: {drawing['type']}")
            print(f"  Items: {len(drawing.get('items', []))}")
            
            if drawing['type'] == 's':  # stroke
                for j, item in enumerate(drawing['items']):
                    if item[0] == 'l':  # line
                        start = item[1]
                        end = item[2]
                        print(f"    Line {j+1}: ({start.x:.1f}, {start.y:.1f}) to ({end.x:.1f}, {end.y:.1f})")
                        
                        # Check if this could be signature content (not table borders)
                        # Table borders are usually at specific y coordinates
                        if start.y > 430 and start.y < 530:  # In signature area
                            print(f"      *** POTENTIAL SIGNATURE LINE ***")
            
            elif drawing['type'] == 'f':  # fill
                rect = drawing.get('rect')
                if rect:
                    print(f"    Fill: ({rect.x0:.1f}, {rect.y0:.1f}) to ({rect.x1:.1f}, {rect.y1:.1f})")
                    if rect.y0 > 430 and rect.y0 < 530:  # In signature area
                        print(f"      *** POTENTIAL STAMP FILL ***")
            
            # Print all other properties
            for key, value in drawing.items():
                if key not in ['type', 'items', 'rect']:
                    print(f"    {key}: {value}")
        
        pdf_document.close()
        
    except Exception as e:
        print(f"Error: {e}")

print("="*80)
print("DEBUGGING CONTRACT WITH STAMP AND SIGNATURE")
print("="*80)
debug_all_drawings('Contract-with-stamp-and-signature.pdf')

print("\n" + "="*80)
print("DEBUGGING ORIGINAL EXTRACTED DOCUMENT") 
print("="*80)
debug_all_drawings('extracted_document.pdf')