import requests
import json

# Read the PDF base64 data
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

# Prepare the request
url = "http://127.0.0.1:8001/extract-underlines"
payload = {
    "pdf_base64": pdf_base64
}

try:
    print("Making request to API...")
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Success!")
        print(f"Underlined words found: {result['underlined_words']}")
        print(f"Total count: {result['count']}")
        print(f"Message: {result['message']}")
    else:
        print(f"❌ Error response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")