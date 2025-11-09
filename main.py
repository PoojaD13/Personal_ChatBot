from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from typing import List
from fastapi import Form
import base64
# Import your modules
from file_processor import FileProcessor
from vector_db import VectorDBManager
from llm_manager import LLMManager

app = FastAPI(title="JARVIS Enhanced Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
try:
    vector_db = VectorDBManager()
    llm_manager = LLMManager()
    file_processor = FileProcessor()
    print("✅ Enhanced JARVIS initialized successfully")
except Exception as e:
    print(f"❌ Initialization error: {e}")

# Store conversation history
conversation_history = {}

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    session_id: str

#debugging router remove it 
# Add these imports at the top of main.py
import glob
from datetime import datetime

# Add this global variable to track processing status
file_processing_logs = []

@app.get("/debug-upload-logs")
async def debug_upload_logs():
    """Get recent file processing logs"""
    return {
        "total_logs": len(file_processing_logs),
        "recent_logs": file_processing_logs[-10:] if file_processing_logs else []  # Last 10 logs
    }

@app.get("/debug-processing-status")
async def debug_processing_status():
    """Comprehensive processing status check"""
    try:
        # Check for any temp files that might be stuck
        temp_files = glob.glob("temp_*")
        current_temp_files = []
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                file_size = os.path.getsize(temp_file)
                current_temp_files.append({
                    'filename': temp_file,
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2)
                })
        
        return {
            "current_temp_files": current_temp_files,
            "total_temp_files": len(current_temp_files),
            "processing_logs_count": len(file_processing_logs),
            "vector_db_document_count": vector_db.search("test", top_k=1)['matches']  # Quick count
        }
    except Exception as e:
        return {"error": str(e)}

#Upto here 
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint"""
    try:
        session_id = message.session_id
        
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Search vector DB for relevant content
        search_results = vector_db.search(message.message, top_k=5)
        
        # Extract context from search results
        context_chunks = []
        sources = []
        for match in search_results['matches']:
            context_chunks.append(match['metadata']['text'])
            source_info = f"{match['metadata']['filename']}"
            if match['metadata'].get('file_type'):
                source_info += f" ({match['metadata']['file_type']})"
            sources.append(source_info)
        
        context = "\n---\n".join(context_chunks) if context_chunks else "No relevant documents found."
        
        print(f"🎯 User question: {message.message}")
        print(f"📄 Context found: {len(context)} characters")
        
        # FIXED: Pass user question and context separately
        response = llm_manager.generate_response(
            user_question=message.message,
            context=context
        )
        
        # Update conversation history
        conversation_history[session_id].append({
            "user": message.message,
            "assistant": response
        })
        
        return ChatResponse(
            response=response,
            sources=sources,
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and process ALL file types"""
    try:
        # Validate file type
        allowed_extensions = ['pdf', 'docx', 'doc', 'txt', 'xlsx', 'xls', 'csv', 
                            'pptx', 'ppt', 'png', 'jpg', 'jpeg', 'bmp', 'tiff']
        file_ext = file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported")
        
        # Create temp file
        file_path = f"temp_{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process in background
        background_tasks.add_task(process_and_ingest_file, file_path, file.filename)
        
        return {
            "status": "processing", 
            "filename": file.filename, 
            "file_type": file_ext,
            "message": f"File is being processed and analyzed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
def process_and_ingest_file(file_path: str, filename: str):
    """Background task to process and ingest ALL file types - INSTRUMENTED VERSION"""
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "file_path": file_path,
        "steps": []
    }
    
    def log_step(step, status, details=""):
        """Helper to log each step"""
        step_log = {
            "step": step,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        log_entry["steps"].append(step_log)
        print(f"🔧 {step}: {status} - {details}")
    
    try:
        log_step("START", "processing", f"Starting processing of {filename}")
        
        # Step 1: Check if file exists and is readable
        if not os.path.exists(file_path):
            log_step("FILE_CHECK", "failed", f"File not found: {file_path}")
            return False
        
        file_size = os.path.getsize(file_path)
        log_step("FILE_CHECK", "success", f"File exists, size: {file_size} bytes")
        
        # Step 2: Extract text from file
        log_step("TEXT_EXTRACTION", "started", "Calling file_processor.process_file()")
        text = file_processor.process_file(file_path, filename)
        
        if not text:
            log_step("TEXT_EXTRACTION", "failed", "No text returned from processor")
            # Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
            file_processing_logs.append(log_entry)
            return False
        
        text_length = len(text)
        log_step("TEXT_EXTRACTION", "success", f"Extracted {text_length} characters")
        log_step("TEXT_PREVIEW", "info", f"First 200 chars: {text[:200]}...")
        
        if text_length < 10:
            log_step("TEXT_EXTRACTION", "failed", f"Text too short: {text_length} chars")
            if os.path.exists(file_path):
                os.remove(file_path)
            file_processing_logs.append(log_entry)
            return False
        
        # Step 3: Split into chunks
        log_step("CHUNKING", "started", "Splitting text into chunks")
        text_chunks = file_processor.split_text(text)
        
        if not text_chunks:
            log_step("CHUNKING", "failed", "No chunks created")
            if os.path.exists(file_path):
                os.remove(file_path)
            file_processing_logs.append(log_entry)
            return False
        
        log_step("CHUNKING", "success", f"Created {len(text_chunks)} chunks")
        
        # Log first chunk preview
        if text_chunks:
            log_step("CHUNK_PREVIEW", "info", f"First chunk: {text_chunks[0][:100]}...")
        
        # Step 4: Prepare chunks for vector DB
        log_step("PREPARE_METADATA", "started", "Preparing chunks with metadata")
        chunks_with_metadata = []
        for i, chunk_text in enumerate(text_chunks):
            chunks_with_metadata.append({
                'text': chunk_text,
                'filename': filename,
                'file_type': filename.split('.')[-1].lower()
            })
        
        log_step("PREPARE_METADATA", "success", f"Prepared {len(chunks_with_metadata)} chunks")
        
        # Step 5: Ingest to vector DB
        doc_id = f"{filename}_{uuid.uuid4()}"
        log_step("VECTOR_DB_INGEST", "started", f"Ingesting {len(chunks_with_metadata)} chunks to Vector DB")
        
        success = vector_db.ingest_documents(chunks_with_metadata, doc_id)
        
        if success:
            log_step("VECTOR_DB_INGEST", "success", f"Successfully ingested document {doc_id}")
        else:
            log_step("VECTOR_DB_INGEST", "failed", "Vector DB ingestion returned False")
        
        # Step 6: Cleanup
        log_step("CLEANUP", "started", "Removing temporary file")
        if os.path.exists(file_path):
            os.remove(file_path)
            log_step("CLEANUP", "success", "Temporary file removed")
        else:
            log_step("CLEANUP", "warning", "Temporary file already removed")
        
        # Step 7: Final result
        if success:
            log_step("FINAL", "success", f"Completed processing {filename}")
        else:
            log_step("FINAL", "failed", f"Processing failed for {filename}")
        
        # Store the log
        file_processing_logs.append(log_entry)
        return success
        
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        log_step("ERROR", "failed", error_msg)
        
        import traceback
        error_details = traceback.format_exc()
        log_step("STACK_TRACE", "error", error_details)
        
        # Cleanup on error
        if os.path.exists(file_path):
            os.remove(file_path)
            log_step("CLEANUP_ERROR", "info", "Removed temporary file after error")
        
        # Store the log
        file_processing_logs.append(log_entry)
        return False
    
@app.get("/")
async def root():
    return {
        "message": "Enhanced JARVIS Agent API is running", 
        "status": "healthy",
        "features": [
            "Multi-format file support (PDF, Word, Excel, PPT, Images)",
            "OCR for images and scanned documents", 
            "Semantic search across all documents",
            "Visual content analysis"
        ]
    }

@app.get("/supported-formats")
async def supported_formats():
    return {
        "document_formats": ["pdf", "docx", "doc", "txt"],
        "spreadsheet_formats": ["xlsx", "xls", "csv"],
        "presentation_formats": ["pptx", "ppt"],
        "image_formats": ["png", "jpg", "jpeg", "bmp", "tiff"]
    }
# main.py (add these imports and endpoints)


# Update your existing imports and keep the existing initialization

class MultimodalQuery(BaseModel):
    message: str
    session_id: str = "default"
    image_data: List[str] = None  # Base64 encoded images

@app.post("/multimodal-chat", response_model=ChatResponse)
async def multimodal_chat(query: MultimodalQuery):
    """Enhanced chat endpoint that supports text + images"""
    try:
        session_id = query.session_id
        
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Search vector DB for relevant content
        search_results = vector_db.search(query.message, top_k=5)
        
        # Extract context from search results
        context_chunks = []
        sources = []
        for match in search_results['matches']:
            context_chunks.append(match['metadata']['text'])
            source_info = f"{match['metadata']['filename']}"
            if match['metadata'].get('file_type'):
                source_info += f" ({match['metadata']['file_type']})"
            sources.append(source_info)
        
        context = "\n---\n".join(context_chunks) if context_chunks else "No relevant documents found."
        
        print(f"🎯 User question: {query.message}")
        print(f"📄 Context found: {len(context)} characters")
        print(f"🖼️  Images provided: {len(query.image_data) if query.image_data else 0}")
        
        # Process with LLM manager (now supports images)
        response = llm_manager.generate_response(
            user_question=query.message,
            context=context,
            images=query.image_data  # Pass base64 images
        )
        
        # Update conversation history
        conversation_history[session_id].append({
            "user": query.message,
            "assistant": response,
            "has_images": bool(query.image_data)
        })
        
        return ChatResponse(
            response=response,
            sources=sources,
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-image")
async def analyze_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    question: str = Form("What can you see in this image?")
):
    """Direct image analysis endpoint"""
    try:
        # Validate image file
        allowed_extensions = ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp']
        file_ext = file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Image format {file_ext} not supported")
        
        # Save temp file
        file_path = f"temp_image_{uuid.uuid4()}.{file_ext}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process in background
        background_tasks.add_task(process_image_analysis, file_path, question)
        
        return {
            "status": "processing", 
            "filename": file.filename,
            "question": question,
            "message": "Image is being analyzed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_image_analysis(image_path: str, question: str):
    """Background task for image analysis"""
    try:
        # Convert image to base64 for Ollama
        image_base64 = LLMManager.image_to_base64(image_path)
        
        if image_base64:
            # Use vision model directly
            response = llm_manager.generate_response(
                user_question=question,
                images=[image_base64]
            )
            
            print(f"✅ Image analysis complete: {response[:100]}...")
        else:
            print("❌ Failed to process image")
        
        # Cleanup
        os.remove(image_path)
        
    except Exception as e:
        print(f"❌ Error in image analysis: {str(e)}")
        if os.path.exists(image_path):
            os.remove(image_path)
# Add these debug endpoints to your main.py

@app.get("/debug-status")
async def debug_status():
    """Comprehensive debug endpoint"""
    try:
        # Test vector DB search
        search_results = vector_db.search("test", top_k=10)
        
        # Check temp files
        import glob
        temp_files = glob.glob("temp_*")
        
        return {
            "vector_db_status": "connected",
            "vector_db_documents": len(search_results['matches']),
            "vector_db_sample": [
                {
                    'filename': match['metadata']['filename'],
                    'file_type': match['metadata'].get('file_type', 'unknown'),
                    'text_preview': match['metadata']['text'][:100] + "..." if len(match['metadata']['text']) > 100 else match['metadata']['text']
                }
                for match in search_results['matches'][:3]
            ],
            "temp_files_count": len(temp_files),
            "temp_files": temp_files[:5],
            "llm_manager_status": "fallback" if llm_manager.fallback_mode else "connected",
            "file_processor_status": "active"
        }
    except Exception as e:
        return {"error": str(e)}
# just added 
@app.get("/debug-search/{query}")
async def debug_search(query: str, top_k: int = 5):
    """Debug search functionality"""
    try:
        results = vector_db.search(query, top_k=top_k)
        return {
            "query": query,
            "total_matches": len(results['matches']),
            "matches": [
                {
                    'filename': match['metadata']['filename'],
                    'file_type': match['metadata'].get('file_type', 'unknown'),
                    'score': match.get('score', 0),
                    'text': match['metadata']['text'],
                    'text_length': len(match['metadata']['text'])
                }
                for match in results['matches']
            ]
        }
    except Exception as e:
        return {"error": str(e)}
# to debug the imge pipeline remove once its working 
@app.get("/test-background-task")
async def test_background_task(background_tasks: BackgroundTasks):
    """Test if background tasks are working"""
    
    def test_task(filename: str):
        print(f"🎯 BACKGROUND TASK EXECUTED: {filename}")
        print(f"✅ Background tasks are working!")
    
    background_tasks.add_task(test_task, "test_file.txt")
    
    return {"status": "background_task_started", "message": "Check console for output"}

@app.get("/test-file-processor")
async def test_file_processor():
    """Test the file processor directly"""
    try:
        # Create a test image
        from PIL import Image, ImageDraw
        img = Image.new('RGB', (400, 200), color='white')
        d = ImageDraw.Draw(img)
        d.text((50, 50), "TEST OCR PROCESSING", fill='black')
        d.text((50, 100), "HELLO JARVIS SYSTEM", fill='black')
        
        test_path = "direct_test.png"
        img.save(test_path)
        
        # Test processing directly
        print("🧪 Testing file processor directly...")
        text = file_processor.process_file(test_path, "direct_test.png")
        print(f"📄 Processor result: {text}")
        
        # Cleanup
        import os
        if os.path.exists(test_path):
            os.remove(test_path)
            
        return {"processor_test": "completed", "text_length": len(text), "text_preview": text[:100]}
        
    except Exception as e:
        return {"error": str(e)}
# up to here 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)