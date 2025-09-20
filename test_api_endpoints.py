#!/usr/bin/env python3
import requests
import json

def test_api_endpoints():
    # Read the base64 content
    with open("arabic-pdf-base64.txt", "r", encoding="utf-8") as f:
        base64_content = f.read().strip()

    print(f"Base64 content length: {len(base64_content)}")

    # Test different possible endpoints
    endpoints = [
        "https://maids-contract-api.vercel.app/analyze",
        "https://maids-contract-api.vercel.app/extract_underlined_words",
        "https://maids-contract-api.vercel.app/",
    ]

    payload = {
        "pdf_data": base64_content
    }

    for endpoint in endpoints:
        print(f"\n=== Testing endpoint: {endpoint} ===")
        try:
            response = requests.post(endpoint, json=payload, timeout=30)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("SUCCESS! API Response:")
                arabic_count = result.get('arabic_contract_count', 'NOT FOUND')
                print(f"Arabic contract count: {arabic_count}")
                
                # Show some other relevant fields
                print(f"Status: {result.get('status', 'N/A')}")
                print(f"Article count: {result.get('article_count', 'N/A')}")
                break
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    # Also test the root endpoint to see what's available
    print(f"\n=== Testing info endpoint ===")
    try:
        response = requests.get("https://maids-contract-api.vercel.app/info")
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("Info response:", response.json())
    except Exception as e:
        print(f"Error getting info: {e}")

if __name__ == "__main__":
    test_api_endpoints()