import requests
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

print(f"Testing with PDF data length: {len(pdf_base64)} characters")

# First, let's manually convert PDF to HTML to see what we get
try:
    pdf_bytes = base64.b64decode(pdf_base64)
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    print(f"\nPDF has {pdf_document.page_count} pages")
    
    # Convert each page to HTML and save for inspection
    for page_num in range(min(pdf_document.page_count, 2)):  # Only first 2 pages
        page = pdf_document[page_num]
        html_content = page.get_text("html")
        
        # Save HTML to file
        with open(f'page_{page_num + 1}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Page {page_num + 1} HTML saved to page_{page_num + 1}.html")
        print(f"Page {page_num + 1} HTML length: {len(html_content)} characters")
        
        # Look for underline indicators in the HTML
        html_lower = html_content.lower()
        underline_indicators = [
            '<u>', '</u>',
            'text-decoration', 'underline',
            'border-bottom',
            'style=', 'class='
        ]
        
        found_indicators = []
        for indicator in underline_indicators:
            if indicator in html_lower:
                found_indicators.append(indicator)
                
        print(f"Page {page_num + 1} found HTML indicators: {found_indicators}")
        
        # Show a sample of the HTML
        print(f"Page {page_num + 1} HTML sample (first 500 chars):")
        print(html_content[:500])
        print("=" * 50)
    
    pdf_document.close()
    
except Exception as e:
    print(f"Error processing PDF manually: {e}")

# Now test the API
url = "http://127.0.0.1:8000/extract-underlines"
payload = {
    "pdf_base64": pdf_base64
}

try:
    print("\nMaking request to API...")
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"Underlined words found: {result['underlined_words']}")
        print(f"Total count: {result['total_count']}")
        print(f"Message: {result['message']}")
    else:
        print("❌ Error occurred:")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")