#!/usr/bin/env python3
import base64
import fitz  # PyMuPDF

def analyze_arabic_text_order():
    # Read the base64 content
    with open("arabic-pdf-base64.txt", "r", encoding="utf-8") as f:
        base64_content = f.read().strip()
    
    # Decode the base64 to get PDF bytes
    pdf_bytes = base64.b64decode(base64_content)
    
    # Open the PDF
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Extract text from all pages and look for Arabic content
    all_text = ""
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text = page.get_text()
        all_text += text + "\n"
    
    pdf_document.close()
    
    print("=== ANALYZING ARABIC TEXT PATTERNS ===")
    
    # Find lines containing Arabic characters
    lines = all_text.split('\n')
    arabic_lines = []
    
    for i, line in enumerate(lines):
        if any(ord(c) >= 1536 and ord(c) <= 1791 for c in line):
            if len(line.strip()) > 5:  # Only meaningful lines
                arabic_lines.append((i, line.strip()))
    
    print(f"Found {len(arabic_lines)} lines with Arabic text")
    
    # Look for lines that might contain our target word
    target_variations = [
        "ﺍﻟﻤﻮﺿﻮﻉ",    # Original search term
        "الموضوع",        # Standard Arabic
        "موضوع",         # Without article
        "ﻤﻮﺿﻮﻉ",        # Possible variation
        "ﻮﺿﻮﻉ",         # Partial
    ]
    
    print("\n=== SEARCHING FOR PATTERN VARIATIONS ===")
    for variation in target_variations:
        count = all_text.count(variation)
        if count > 0:
            print(f"'{variation}' found {count} times")
            # Show the bytes representation
            print(f"  Bytes: {variation.encode('utf-8').hex()}")
            print(f"  Unicode points: {[ord(c) for c in variation]}")
    
    # Find the actual words that contain "موضوع" in any form
    print("\n=== EXTRACTING ACTUAL WORDS FROM TEXT ===")
    import re
    
    # Extract all Arabic words and look for ones containing our target characters
    arabic_word_pattern = r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+'
    arabic_words = re.findall(arabic_word_pattern, all_text)
    
    # Look for words that might be "موضوع" in different forms
    potential_matches = []
    target_chars = ['م', 'و', 'ض', 'و', 'ع']  # Basic Arabic letters
    
    for word in arabic_words:
        # Check if word contains the basic letters we're looking for
        if 'ض' in word and 'ع' in word:  # Key identifying characters
            potential_matches.append(word)
            print(f"Potential match: '{word}'")
            print(f"  Bytes: {word.encode('utf-8').hex()}")
            print(f"  Unicode points: {[ord(c) for c in word]}")
            print(f"  Length: {len(word)}")
    
    print(f"\nFound {len(potential_matches)} potential variations")
    
    # Test counting each variation
    print("\n=== TESTING COUNT FOR EACH VARIATION ===")
    for word in set(potential_matches):
        count = all_text.count(word)
        print(f"'{word}' appears {count} times")

if __name__ == "__main__":
    analyze_arabic_text_order()