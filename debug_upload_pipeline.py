# debug_upload_pipeline.py
import requests
import time
import os
from PIL import Image, ImageDraw
import json

def test_upload_with_monitoring():
    """Test upload while monitoring processing logs"""
    
    print("🚀 Starting Upload Pipeline Debug...\n")
    
    # Step 1: Check initial status
    print("📊 Step 1: Checking initial system status...")
    response = requests.get("http://localhost:8000/debug-status")
    initial_status = response.json()
    print(f"   - Vector DB documents: {initial_status['vector_db_documents']}")
    print(f"   - LLM Status: {initial_status['llm_manager_status']}")
    
    # Step 2: Check processing logs
    print("\n📝 Step 2: Checking processing logs...")
    response = requests.get("http://localhost:8000/debug-upload-logs")
    logs = response.json()
    print(f"   - Total logs in system: {logs['total_logs']}")
    
    # Step 3: Create a test image with VERY clear text
    print("\n🎨 Step 3: Creating test image...")
    img = Image.new('RGB', (1000, 600), color='white')
    d = ImageDraw.Draw(img)
    
    # Large, clear text that's easy for OCR
    text_content = [
        "JARVIS AI SYSTEM TEST 2024",
        "DOCUMENT PROCESSING PIPELINE",
        "ARTIFICIAL INTELLIGENCE PLATFORM",
        "VECTOR DATABASE STORAGE SYSTEM",
        "OPTICAL CHARACTER RECOGNITION",
        "TEST CONTENT FOR DEBUGGING",
        "HELLO WORLD FROM JARVIS AI"
    ]
    
    y_position = 80
    for line in text_content:
        d.text((100, y_position), line, fill='black')
        y_position += 70
    
    test_image_path = "debug_test_image.png"
    img.save(test_image_path, quality=100)
    print(f"   - Created: {test_image_path}")
    print(f"   - File size: {os.path.getsize(test_image_path)} bytes")
    
    # Step 4: Upload the image
    print("\n📤 Step 4: Uploading test image...")
    with open(test_image_path, 'rb') as file:
        files = {'file': (test_image_path, file, 'image/png')}
        response = requests.post("http://localhost:8000/upload", files=files)
    
    if response.status_code == 200:
        upload_result = response.json()
        print(f"   ✅ Upload accepted: {upload_result['filename']}")
        print(f"   📋 Response: {upload_result}")
    else:
        print(f"   ❌ Upload failed: {response.status_code} - {response.text}")
        return
    
    # Step 5: Monitor processing in real-time
    print("\n🔍 Step 5: Monitoring processing (30 seconds)...")
    for i in range(10):
        time.sleep(3)
        print(f"   Check {i+1}/10:")
        
        # Check processing logs
        logs_response = requests.get("http://localhost:8000/debug-upload-logs")
        logs_data = logs_response.json()
        
        if logs_data['recent_logs']:
            latest_log = logs_data['recent_logs'][-1]
            print(f"     Latest log: {latest_log['filename']}")
            if latest_log['steps']:
                latest_step = latest_log['steps'][-1]
                print(f"     Latest step: {latest_step['step']} - {latest_step['status']}")
        
        # Check temp files
        status_response = requests.get("http://localhost:8000/debug-processing-status")
        status_data = status_response.json()
        print(f"     Temp files: {status_data['total_temp_files']}")
        
        # Test search
        search_response = requests.get("http://localhost:8000/debug-search/JARVIS AI SYSTEM")
        search_data = search_response.json()
        print(f"     Search matches: {search_data['total_matches']}")
        
        if search_data['total_matches'] > 0:
            print(f"     🎉 SUCCESS! Document found in Vector DB!")
            break
    
    # Step 6: Final status check
    print("\n📊 Step 6: Final system status...")
    response = requests.get("http://localhost:8000/debug-status")
    final_status = response.json()
    print(f"   - Vector DB documents: {final_status['vector_db_documents']}")
    
    # Step 7: Cleanup
    print("\n🧹 Step 7: Cleanup...")
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"   - Removed test file: {test_image_path}")
    
    print("\n🎉 Debug completed!")

if __name__ == "__main__":
    test_upload_with_monitoring()