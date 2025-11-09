# # test_ocr_fixed.py
# import requests
# from file_processor import FileProcessor
# import os

# def test_fixed_ocr():
#     print("🔍 Testing Fixed OCR Processing...")
    
#     # Create a clear test image
#     from PIL import Image, ImageDraw, ImageFont
    
#     img = Image.new('RGB', (800, 400), color='white')
#     d = ImageDraw.Draw(img)
    
#     # Use larger, clearer text
#     text_content = [
#         "JARVIS AI SYSTEM TEST",
#         "OPTICAL CHARACTER RECOGNITION",
#         "ARTIFICIAL INTELLIGENCE PLATFORM", 
#         "TEST SUCCESSFUL 2024"
#     ]
    
#     y_pos = 60
#     for line in text_content:
#         d.text((80, y_pos), line, fill='black')
#         y_pos += 80
    
#     test_path = "fixed_test.png"
#     img.save(test_path, quality=100)
#     print(f"✅ Created test image: {test_path}")
    
#     # Test the fixed processor
#     processor = FileProcessor()
#     print("\n🔄 Processing image with fixed OCR...")
#     result = processor.process_file(test_path, "fixed_test.png")
    
#     print(f"\n📄 OCR Result:")
#     print(f"Length: {len(result)} characters")
#     print(f"Preview: {result[:200]}...")
    
#     # Check if key terms are found
#     key_terms = ["JARVIS", "OPTICAL", "CHARACTER", "RECOGNITION", "ARTIFICIAL", "INTELLIGENCE"]
#     found_terms = [term for term in key_terms if term in result]
    
#     print(f"\n🔍 Key terms found: {found_terms}")
#     print(f"📊 Success rate: {len(found_terms)}/{len(key_terms)}")
    
#     # Cleanup
#     if os.path.exists(test_path):
#         os.remove(test_path)
    
#     return result, len(found_terms) >= 3  # At least 3 terms should be found

# if __name__ == "__main__":
#     result, success = test_fixed_ocr()
#     if success:
#         print("\n🎉 OCR is now working! Images should be processed successfully.")
#     else:
#         print("\n❌ OCR still not working properly. Check dependencies.")
#         print("Required installations:")
#         print("  pip install pytesseract opencv-python pillow")
#         print("  Download Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki")

# test_ocr_working.py
import requests

def test_upload_and_search():
    """Test that uploaded images can be found"""
    
    # Upload a simple image
    from PIL import Image, ImageDraw
    
    img = Image.new('RGB', (600, 300), color='white')
    d = ImageDraw.Draw(img)
    d.text((100, 100), "JARVIS TEST DOCUMENT", fill='black')
    d.text((100, 150), "ARTIFICIAL INTELLIGENCE", fill='black')
    
    test_path = "search_test.png"
    img.save(test_path)
    
    print("📤 Uploading test image...")
    with open(test_path, 'rb') as f:
        files = {'file': (test_path, f, 'image/png')}
        response = requests.post("http://localhost:8000/upload", files=files)
        print(f"Upload response: {response.json()}")
    
    # Wait for processing
    import time
    time.sleep(10)
    
    # Test search
    print("\n🔍 Testing search...")
    search_response = requests.get("http://localhost:8000/debug-search/JARVIS")
    search_data = search_response.json()
    print(f"Search results: {search_data['total_matches']} matches")
    
    for match in search_data['matches']:
        print(f"  - {match['filename']} (score: {match['score']:.3f})")
        print(f"    Text: {match['text'][:100]}...")
    
    # Cleanup
    import os
    if os.path.exists(test_path):
        os.remove(test_path)

if __name__ == "__main__":
    test_upload_and_search()