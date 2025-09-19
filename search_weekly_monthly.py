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

try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    print(f"PDF has {pdf_document.page_count} pages")
    
    # Convert all pages to HTML and search for weekly/monthly
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        html_content = page.get_text("html")
        
        # Save HTML to file
        with open(f'page_{page_num + 1}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nPage {page_num + 1}:")
        print(f"HTML length: {len(html_content)} characters")
        
        # Search for weekly or monthly (case insensitive)
        html_lower = html_content.lower()
        
        if 'weekly' in html_lower:
            print(f"  ✓ Found 'weekly' on page {page_num + 1}")
            # Find the context around "weekly"
            weekly_pos = html_lower.find('weekly')
            context_start = max(0, weekly_pos - 200)
            context_end = min(len(html_content), weekly_pos + 200)
            context = html_content[context_start:context_end]
            print(f"  Context: {context}")
            
        if 'monthly' in html_lower:
            print(f"  ✓ Found 'monthly' on page {page_num + 1}")
            # Find the context around "monthly"  
            monthly_pos = html_lower.find('monthly')
            context_start = max(0, monthly_pos - 200)
            context_end = min(len(html_content), monthly_pos + 200)
            context = html_content[context_start:context_end]
            print(f"  Context: {context}")
        
        # Also get plain text to see all content
        plain_text = page.get_text()
        if 'weekly' in plain_text.lower() or 'monthly' in plain_text.lower():
            print(f"  Plain text contains weekly/monthly")
            lines = plain_text.split('\n')
            for i, line in enumerate(lines):
                if 'weekly' in line.lower() or 'monthly' in line.lower():
                    print(f"    Line {i}: {line.strip()}")
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error: {e}")