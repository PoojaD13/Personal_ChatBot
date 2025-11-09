
import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class VectorDBManager:
    def __init__(self):
        # Initialize Pinecone with new API
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        
        self.index_name = "jarvis-docs"
        self.embedder = SentenceTransformer(os.getenv('EMBEDDING_MODEL'))
        
        # Check if index exists, create if not
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=384,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
        self.index = self.pc.Index(self.index_name)
        print("✅ Vector DB initialized")

    def ingest_documents(self, chunks: list, doc_id: str):
        """Store document chunks in vector database"""
        if not chunks:
            return False
            
        try:
            texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.encode(texts)
            
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{doc_id}_chunk_{i}"
                vectors.append({
                    'id': vector_id,
                    'values': embedding.tolist(),
                    'metadata': {
                        'text': chunk['text'],
                        'filename': chunk['filename'],
                        'file_type': chunk['file_type'],
                        'chunk_id': i,
                        'doc_id': doc_id
                    }
                })
            
            self.index.upsert(vectors=vectors)
            print(f"✅ Ingested {len(vectors)} chunks from {chunks[0]['filename']}")
            return True
            
        except Exception as e:
            print(f"❌ Error ingesting documents: {str(e)}")
            return False

    # def search(self, query: str, top_k: int = 5):
    #     """Semantic search in vector database with relaxed filtering"""
    #     try:
    #         query_embedding = self.embedder.encode([query]).tolist()
    #         results = self.index.query(
    #             vector=query_embedding,
    #             top_k=top_k,
    #             include_metadata=True
    #         )
        
    #         # More relaxed filtering - crucial fixes!
    #         filtered_matches = []
    #         seen_texts = set()
        
    #         for match in results.get('matches', []):
    #             text = match['metadata'].get('text', '')
    #             score = match.get('score', 0)
            
    #             # RELAXED FILTERS:
    #             if (score > 0.3 and  # Lowered from 0.5 to 0.3
    #                 text not in seen_texts and 
    #                 len(text) > 5 and len(text) < 1000):  # Increased max length from 500 to 1000
    #                 filtered_matches.append(match)
    #                 seen_texts.add(text)
        
    #         return {'matches': filtered_matches}  # Return ALL filtered results, not just top 2
        
    #     except Exception as e:
    #         print(f"❌ Search error: {str(e)}")
    #         return {'matches': []}
        # Update the search function to be more lenient for image queries
    def search(self, query: str, top_k: int = 5):
        """Semantic search - IMAGE FRIENDLY VERSION"""
        try:
            query_embedding = self.embedder.encode([query]).tolist()
            results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
            )
        
            # SPECIAL HANDLING FOR IMAGE QUERIES
            filtered_matches = []
            seen_texts = set()
        
            image_keywords = ['image', 'picture', 'photo', 'screenshot', 'chart', 'graph', 'what contain', 'what about', 'describe']
            is_image_query = any(keyword in query.lower() for keyword in image_keywords)
        
            for match in results.get('matches', []):
                text = match['metadata'].get('text', '')
                score = match.get('score', 0)
                file_type = match['metadata'].get('file_type', '')
                is_image_file = file_type in ['png', 'jpg', 'jpeg', 'bmp', 'tiff']
            
                if is_image_query and is_image_file:
                    # VERY LENIENT for image queries - return ALL image content
                    filtered_matches.append(match)
                if (score > 0.1 and  # Very low threshold
                    text not in seen_texts and 
                    len(text) > 10):
                    filtered_matches.append(match)
                    seen_texts.add(text)
                else:
                    # Normal filtering for other content
                    if (score > 0.3 and 
                        text not in seen_texts and 
                        len(text) > 5 and len(text) < 1000):
                        filtered_matches.append(match)
                        seen_texts.add(text)
        
            return {'matches': filtered_matches}
        
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return {'matches': []}