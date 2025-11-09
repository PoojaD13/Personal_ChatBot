# test_fixed_system.py
import requests
import time
import os
from PIL import Image, ImageDraw
import json

def test_debug_endpoints():
    """Test the new debug endpoints"""
    print("🔧 Testing debug endpoints...")
    
    # Test debug status
    response = requests.get("http://localhost:8000/debug-status")
    if response.status_code == 200:
        status = response.json()
        print(f"✅ System Status:")
        print(f"   - Vector DB documents: {status['vector_db_documents']}")
        print(f"   - LLM Manager: {status['llm_manager_status']}")
        print(f"   - Temp files: {status['temp_files_count']}")
        
        if status['vector_db_documents'] > 0:
            print(f"   - Sample documents:")
            for doc in status['vector_db_sample']:
                print(f"     * {doc['filename']} ({doc['file_type']})")
    else:
        print(f"❌ Debug status failed: {response.status_code}")

def test_search_functionality():
    """Test search with various terms"""
    print("\n🔍 Testing search functionality...")
    
    test_queries = ["test", "document", "file", "data", "hello"]
    
    for query in test_queries:
        response = requests.get(f"http://localhost:8000/debug-search/{query}")
        if response.status_code == 200:
            result = response.json()
            print(f"   '{query}': {result['total_matches']} matches")
        else:
            print(f"   '{query}': ERROR {response.status_code}")

def upload_test_image():
    """Upload a test image and monitor processing"""
    print("\n📤 Uploading test image...")
    
    # Create a simple test image
    img = Image.new('RGB', (800, 400), color='white')
    d = ImageDraw.Draw(img)
    
    # Add clear, searchable text
    text_lines = [
        "JARVIS TEST DOCUMENT 2024",
        "ARTIFICIAL INTELLIGENCE SYSTEM",
        "TEST CONTENT FOR VECTOR DATABASE",
        "QUARTERLY SALES: $1,000,000",
        "PERFORMANCE METRICS: EXCELLENT"
    ]
    
    y_pos = 50
    for line in text_lines:
        d.text((50, y_pos), line, fill='black')
        y_pos += 60
    
    test_path = "jarvis_test_image.png"
    img.save(test_path)
    print(f"✅ Created test image: {test_path}")
    
    # Upload the image
    with open(test_path, 'rb') as f:
        files = {'file': (test_path, f, 'image/png')}
        response = requests.post("http://localhost:8000/upload", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload accepted: {result['filename']}")
        print(f"⏳ Waiting for processing...")
        
        # Monitor for 30 seconds
        for i in range(6):
            time.sleep(5)
            print(f"   Check {i+1}/6: Waiting 5 seconds...")
            
            # Test search for the uploaded content
            response = requests.get("http://localhost:8000/debug-search/JARVIS TEST DOCUMENT")
            if response.status_code == 200:
                search_result = response.json()
                if search_result['total_matches'] > 0:
                    print(f"🎉 SUCCESS! Document found in Vector DB!")
                    print(f"   Matches: {search_result['total_matches']}")
                    break
        else:
            print("❌ Document not found after 30 seconds")
    
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
    
    # Cleanup
    if os.path.exists(test_path):
        os.remove(test_path)

if __name__ == "__main__":
    print("🚀 Testing Fixed JARVIS System...\n")
    
    # Test 1: Check current system status
    test_debug_endpoints()
    
    # Test 2: Test search before upload
    test_search_functionality()
    
    # Test 3: Upload and test processing
    upload_test_image()
    
    # Test 4: Check status after upload
    print("\n📊 Final system status:")
    test_debug_endpoints()
    
    print("\n🎉 Test completed!")