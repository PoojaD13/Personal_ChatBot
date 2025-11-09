# investigate_pinecone.py
import requests
import json

def investigate_search_results():
    """Investigate what's actually in Pinecone"""
    
    print("🔍 Investigating Pinecone Content...\n")
    
    # Test searches with different terms
    search_terms = [
        "TEST DOCUMENT",
        "JARVIS", 
        "ARTIFICIAL INTELLIGENCE",
        "SYSTEM",
        "HELLO",
        "debug_test_image.png"  # The actual filename
    ]
    
    for term in search_terms:
        print(f"\nSearching for: '{term}'")
        response = requests.get(f"http://localhost:8000/debug-search/{term}?top_k=10")
        
        if response.status_code == 200:
            results = response.json()
            print(f"  Total matches: {results['total_matches']}")
            
            for match in results['matches']:
                print(f"  📄 {match['filename']} (score: {match['score']:.3f})")
                print(f"     Type: {match['file_type']}")
                print(f"     Text: {match['text'][:100]}...")
                print(f"     Length: {match['text_length']} chars")
        else:
            print(f"  ❌ Search failed: {response.status_code}")

def test_chat_with_documents():
    """Test if we can actually retrieve the content via chat"""
    print("\n💬 Testing chat with uploaded documents...")
    
    test_questions = [
        "What test documents do you have?",
        "Tell me about the JARVIS system",
        "What artificial intelligence content do you have?",
        "Do you have any images or screenshots?",
        "What is in debug_test_image.png?"
    ]
    
    for question in test_questions:
        print(f"\nQ: {question}")
        
        payload = {
            "message": question,
            "session_id": "investigation"
        }
        
        response = requests.post("http://localhost:8000/chat", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"A: {result['response'][:150]}...")
            if result['sources']:
                print(f"   Sources: {result['sources']}")
            else:
                print("   No sources cited")
        else:
            print(f"❌ Chat failed: {response.status_code}")

if __name__ == "__main__":
    investigate_search_results()
    test_chat_with_documents()