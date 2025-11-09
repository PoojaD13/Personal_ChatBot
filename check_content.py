# check_pinecone_content.py
import requests
import json

def check_all_content():
    """Check what content is actually in the vector database"""
    
    # Test various search terms to see what exists
    test_queries = [
        "screenshot",
        "image",
        "png",
        "2025-09-03",
        "224226",
        "software",
        "interface",
        "text",
        "chart",
        "data"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        payload = {
            "message": query,
            "session_id": "diagnostic"
        }
        
        response = requests.post("http://localhost:8000/chat", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Context length: {len(result['response'])}")
            if result['sources']:
                print(f"Sources found: {result['sources']}")
            else:
                print("No sources found")
        else:
            print(f"Error: {response.status_code}")

def test_direct_search():
    """Test if vector DB has any content at all"""
    print("\n🧪 Testing vector database content...")
    
    # Test very broad searches
    broad_queries = ["the", "and", "data", "file", "document"]
    
    for query in broad_queries:
        payload = {
            "message": query,
            "session_id": "diagnostic"
        }
        
        response = requests.post("http://localhost:8000/chat", json=payload)
        result = response.json()
        
        print(f"Query: '{query}' -> Response length: {len(result['response'])}")

if __name__ == "__main__":
    print("🔍 Diagnosing Pinecone Content...")
    check_all_content()
    test_direct_search()