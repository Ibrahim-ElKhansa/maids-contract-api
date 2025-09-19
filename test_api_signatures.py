import requests
import base64
import json

def test_signature_detection():
    # Read the PDF file with stamp and signature
    with open("Contract-with-stamp-and-signature.pdf", "rb") as f:
        pdf_content = f.read()
    
    # Convert to base64
    pdf_base64 = base64.b64encode(pdf_content).decode()
    
    # Call the API
    url = "https://maids-contract-1aoqzovt0-ibrahim-el-khansas-projects.vercel.app/extract-underlines"
    
    payload = {
        "pdf_base64": pdf_base64
    }
    
    print("Testing API with contract that has stamp and signature...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ API Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")

def test_original_document():
    # Read the original PDF file
    with open("extracted_document.pdf", "rb") as f:
        pdf_content = f.read()
    
    # Convert to base64
    pdf_base64 = base64.b64encode(pdf_content).decode()
    
    # Call the API
    url = "https://maids-contract-1aoqzovt0-ibrahim-el-khansas-projects.vercel.app/extract-underlines"
    
    payload = {
        "pdf_base64": pdf_base64
    }
    
    print("\nTesting API with original document (no signature)...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ API Response: {json.dumps(result, indent=2)}")
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_signature_detection()
    test_original_document()