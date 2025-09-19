import json
import base64

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

try:
    # Decode the base64 data
    pdf_bytes = base64.b64decode(pdf_base64)
    
    # Write to a PDF file
    output_filename = 'extracted_document.pdf'
    with open(output_filename, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"✅ PDF successfully created: {output_filename}")
    print(f"PDF file size: {len(pdf_bytes)} bytes")
    print(f"You can now open {output_filename} to visually inspect the underlined words")
    
except Exception as e:
    print(f"❌ Error creating PDF: {e}")
    import traceback
    traceback.print_exc()