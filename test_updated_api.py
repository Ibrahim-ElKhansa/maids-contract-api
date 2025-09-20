#!/usr/bin/env python3
import requests
import json

def test_updated_api():
    # Read the base64 content
    with open("arabic-pdf-base64.txt", "r", encoding="utf-8") as f:
        base64_content = f.read().strip()

    print(f"Base64 content length: {len(base64_content)}")

    # Test the updated API
    api_url = "https://maids-contract-api.vercel.app/extract_underlined_words"

    payload = {
        "pdf_data": base64_content
    }

    try:
        print("Testing updated API...")
        response = requests.post(api_url, json=payload, timeout=30)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\nAPI Response - Arabic count:")
            arabic_count = result.get('arabic_contract_count', 'NOT FOUND')
            print(f"Arabic contract count: {arabic_count}")
            
            if arabic_count > 0:
                print("🎉 SUCCESS! Arabic text detection is working via API!")
            else:
                print("❌ Still getting 0 count from API")
                
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_updated_api()