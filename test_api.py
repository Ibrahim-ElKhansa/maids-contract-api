"""
Example script to test the PDF Underline Extractor API.
This script demonstrates how to use the API to extract underlined words from a PDF.
"""

import base64
import requests
import json

def test_api():
    """Test the API with a sample request."""
    
    # API endpoint
    url = "http://localhost:8000/extract-underlines"
    
    # For testing purposes, you would need a real PDF file
    # Here's how you would encode a PDF file:
    """
    with open("sample.pdf", "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
    """
    
    # Example payload (you would replace this with real base64 PDF data)
    payload = {
        "pdf_base64": "your_base64_pdf_content_here"
    }
    
    try:
        # Make the API request
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print("Success!")
            print(f"Underlined words: {result['underlined_words']}")
            print(f"Total count: {result['total_count']}")
            print(f"Message: {result['message']}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Details: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"Error: {str(e)}")

def encode_pdf_file(file_path: str) -> str:
    """
    Helper function to encode a PDF file to base64.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Base64 encoded PDF content
    """
    try:
        with open(file_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            return pdf_base64
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return ""
    except Exception as e:
        print(f"Error encoding PDF: {str(e)}")
        return ""

if __name__ == "__main__":
    print("PDF Underline Extractor API Test")
    print("=" * 40)
    
    # Test health endpoint
    try:
        health_response = requests.get("http://localhost:8000/health")
        if health_response.status_code == 200:
            print("✓ API is healthy")
        else:
            print("✗ API health check failed")
    except:
        print("✗ Cannot connect to API")
    
    print("\nTo test with a real PDF file:")
    print("1. Place your PDF file in the same directory as this script")
    print("2. Update the file_path in the code below")
    print("3. Uncomment and run the test")
    
    # Uncomment the lines below to test with a real PDF file
    # file_path = "your_sample.pdf"
    # pdf_base64 = encode_pdf_file(file_path)
    # if pdf_base64:
    #     payload = {"pdf_base64": pdf_base64}
    #     # Make API request here...