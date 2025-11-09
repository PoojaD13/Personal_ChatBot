#final code working version =================================================
import requests
import json
import base64
from PIL import Image
import io
import time

class LLMManager:
    def __init__(self):
        self.ollama_base_url = "http://localhost:11434"
        self.text_model = "gemma2:2b"
        self.vision_model = "llava:7b"
        self.fallback_mode = False
        self.available_models = []
        
        print("🔄 Initializing LLM Manager...")
        self._initialize_ollama()
    
    def _initialize_ollama(self):
        """Initialize Ollama with retry logic"""
        max_retries = 5
        retry_delay = 3
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Connecting to Ollama... (Attempt {attempt + 1}/{max_retries})")
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    self.available_models = [model['name'] for model in data.get('models', [])]
                    
                    if self.available_models:
                        print(f"✅ Ollama connected! Available models: {self.available_models}")
                        
                        # Auto-select available models
                        self._select_available_models()
                        self.fallback_mode = False
                        return
                    else:
                        print("⚠️  Ollama connected but no models found.")
                        break
                else:
                    print(f"❌ Ollama responded with {response.status_code}: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print(f"❌ Cannot connect to Ollama (Attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    print(f"⏳ Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                break
        
        # If we get here, switch to fallback mode
        print("🚨 Switching to fallback mode (no Ollama)")
        self.fallback_mode = True
    
    # def _select_available_models(self):
    #     """Automatically select the best available models"""
    #     # Priority list for text models
    #     text_model_priority = ['llama2:7b', 'mistral:7b', 'llama2:3b', 'codellama:7b']
    #     vision_model_priority = ['llava:7b', 'bakllava:7b']
        
    #     # Select text model
    #     for model in text_model_priority:
    #         if model in self.available_models:
    #             self.text_model = model
    #             print(f"🤖 Selected text model: {self.text_model}")
    #             break
    #     else:
    #         # Fallback to first available model
    #         self.text_model = self.available_models[0]
    #         print(f"🤖 Fallback to text model: {self.text_model}")
        
    #     # Select vision model
    #     for model in vision_model_priority:
    #         if model in self.available_models:
    #             self.vision_model = model
    #             print(f"👁️ Selected vision model: {self.vision_model}")
    #             break
    #     else:
    #         print("⚠️  No vision model available")
    def _select_available_models(self):
        """Automatically select the best available models"""
        # Priority list for text models - PHI3:MINI FIRST!
        text_model_priority = ['gemma2:2b','llama3.2:1b','llama3.2:3b','phi3:mini', 'llama2:7b', 'mistral:7b', 'llama2:3b', 'codellama:7b']
        vision_model_priority = ['llava:7b', 'bakllava:7b']
    
        # Select text model
        for model in text_model_priority:
            if model in self.available_models:
                self.text_model = model
                print(f"🤖 Selected text model: {self.text_model}")
                break
        else:
            # Fallback to first available model
            if self.available_models:
                self.text_model = self.available_models[0]
                print(f"🤖 Fallback to text model: {self.text_model}")
            else:
                print("⚠️  No text models available")
    
        # Select vision model
        for model in vision_model_priority:
            if model in self.available_models:
                self.vision_model = model
                print(f"👁️ Selected vision model: {self.vision_model}")
                break
        else:
            print("⚠️  No vision model available")
    
    # def generate_response(self, user_question: str, context: str = "", images: list = None):
    #     """Generate response with enhanced error handling"""
        
    #     print(f"\n🎯 User question: {user_question}")
    #     print(f"📄 Context length: {len(context) if context else 0}")
    #     print(f"🖼️  Images provided: {len(images) if images else 0}")
    #     print(f"🤖 Ollama status: {'Connected' if not self.fallback_mode else 'Fallback Mode'}")
        
    #     # Use fallback if no context or Ollama unavailable
    #     if self.fallback_mode or not context or context == "No relevant documents found.":
    #         print("🔄 Using content extraction (fallback)")
    #         return self._extract_from_context(user_question, context)
        
    #     # Use vision model if images provided
    #     if images:
    #         return self._process_with_vision(user_question, images, context)
        
    #     # Use text model
    #     return self._process_text_only(user_question, context)
    def generate_response(self, user_question: str, context: str = "", images: list = None):
        """Generate response with image question handling"""
    
        print(f"\n🎯 User question: {user_question}")
        print(f"📄 Context length: {len(context) if context else 0}")
    
        # Check if this is an image-related question
        image_keywords = [
            'image', 'picture', 'photo', 'screenshot', 'chart', 'graph',
            'what is this', 'what does this show', 'describe this',
            'what contain', 'what about', 'what text', 'what written'
        ]
        is_image_question = any(keyword in user_question.lower() for keyword in image_keywords)
    
        # Use fallback if no context
        if self.fallback_mode or not context or context == "No relevant documents found.":
            return self._extract_from_context(user_question, context)
    
        # SPECIAL: For image questions, return full extracted text directly
        if is_image_question:
            print("🖼️ Image question detected - returning full extracted text")
            return self._handle_image_question(context)
    
         # Normal processing for other questions
        if images:
            return self._process_with_vision(user_question, images, context)
    
        return self._process_text_only(user_question, context)

    def _handle_image_question(self, context: str):
        """Return full extracted text from images"""
        # Extract just the OCR text part
        if "Extracted text from image:" in context:
            # Get everything after "Extracted text from image:"
            parts = context.split("Extracted text from image:")
            if len(parts) > 1:
                ocr_text = parts[1].split("---")[0].strip()  # Get text before separator
                if ocr_text:
                    return f"The image contains the following text:\n\n{ocr_text}"
    
        # Fallback: return the original context
        return context
    
    # def _process_text_only(self, user_question: str, context: str):
    #     """Process text queries with better error handling"""
    #     try:
    #         url = f"{self.ollama_base_url}/api/generate"
    #         prompt = self._format_text_prompt(user_question, context)
            
    #         # DEBUG: Show the prompt being sent
    #         print(f"📝 PROMPT SENT TO OLLAMA:")
    #         print(f"--- PROMPT START ---")
    #         print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    #         print(f"--- PROMPT END ---")
            
    #         payload = {
    #             "model": self.text_model,
    #             "prompt": prompt,
    #             "stream": False,
    #             "options": {
    #                 "temperature": 0.1,  # Lower temperature for more factual responses
    #                 "top_p": 0.8,
    #                 "num_ctx": 2048
    #             }
    #         }
            
    #         print(f"🔄 Calling Ollama with {self.text_model}...")
    #         start_time = time.time()
            
    #         response = requests.post(url, json=payload, timeout=120)
            
    #         elapsed_time = time.time() - start_time
    #         print(f"⏱️  Ollama response time: {elapsed_time:.2f}s")
            
    #         if response.status_code == 200:
    #             result = response.json()
    #             response_text = result.get("response", "").strip()
                
    #             if response_text and len(response_text) > 10:
    #                 print("✅ Ollama response successful!")
    #                 return response_text
    #             else:
    #                 print("⚠️  Ollama returned empty or short response")
    #                 raise ValueError("Empty response from Ollama")
                    
    #         else:
    #             error_msg = f"Ollama API returned {response.status_code}: {response.text}"
    #             print(f"❌ {error_msg}")
    #             raise Exception(error_msg)
                
    #     except Exception as e:
    #         print(f"🔄 Ollama failed: {e}")
    #         print("🔄 Switching to content extraction...")
    #         return self._extract_from_context(user_question, context)
    def _process_text_only(self, user_question: str, context: str):
        try:
            url = f"{self.ollama_base_url}/api/generate"
            prompt = self._format_text_prompt(user_question, context)
        
            # DEBUG: Show the prompt being sent
            print(f"📝 PROMPT SENT TO OLLAMA:")
            print(f"--- PROMPT START ---")
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            print(f"--- PROMPT END ---")
        
            # NEW PAYLOAD WITH CPU-ONLY SETTINGS
            payload = {
                "model": self.text_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_gpu": 0,           # ← FORCE CPU ONLY
                    "num_ctx": 1024,        # ← REDUCE CONTEXT SIZE
                    "num_thread": 2         # ← LIMIT THREADS
                }
            }
        
            print(f"🔄 Calling Ollama with {self.text_model}...")
            start_time = time.time()
        
            response = requests.post(url, json=payload, timeout=120)
        
            elapsed_time = time.time() - start_time
            print(f"⏱️  Ollama response time: {elapsed_time:.2f}s")
        
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "").strip()
            
                if response_text and len(response_text) > 10:
                    print("✅ Ollama response successful!")
                    return response_text
                else:
                    print("⚠️  Ollama returned empty or short response")
                    raise ValueError("Empty response from Ollama")
                
            else:
                error_msg = f"Ollama API returned {response.status_code}: {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
        except Exception as e:
            print(f"🔄 Ollama failed: {e}")
            print("🔄 Switching to content extraction...")
            return self._extract_from_context(user_question, context)
    
    def _process_with_vision(self, user_question: str, images: list, context: str = ""):
        """Process vision queries with better error handling"""
        try:
            if self.vision_model not in self.available_models:
                raise Exception(f"Vision model {self.vision_model} not available")
            
            url = f"{self.ollama_base_url}/api/generate"
            full_prompt = self._format_vision_prompt(user_question, context)
            
            payload = {
                "model": self.vision_model,
                "prompt": full_prompt,
                "stream": False,
                "images": images
            }
            
            print(f"👁️  Calling vision model {self.vision_model}...")
            response = requests.post(url, json=payload, timeout=180)
            
            if response.status_code == 200:
                result = response.json()
                vision_response = result.get("response", "").strip()
                
                if vision_response:
                    print("✅ Vision analysis successful!")
                    return vision_response
                else:
                    raise ValueError("Empty response from vision model")
                    
            else:
                raise Exception(f"Vision API error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Vision processing failed: {e}")
            # Fallback to text analysis with image descriptions
            return self._extract_from_context(user_question, context)
    
    def _format_text_prompt(self, user_question: str, context: str):
        """STRICT prompt for concise, direct answers"""
        if context and context != "No relevant documents found.":
            return f"""You are an AI assistant that provides direct, factual answers based ONLY on the given context.

CONTEXT INFORMATION:
{context}

USER QUESTION: {user_question}

INSTRUCTIONS:
- Provide a direct, concise answer to the question
- Use ONLY information from the context provided
- Do not add any extra information, explanations, or examples
- If the answer requires specific numbers or facts, include them precisely
- Maximum 2-3 sentences
- Do not reference the context itself in your answer
- Do not say "based on the context" or similar phrases

If the context doesn't contain the answer, respond with: "The available documents don't contain information about this specific question."

ANSWER:"""
        else:
            return f"""USER QUESTION: {user_question}

Please provide a helpful and accurate answer:"""
    
    def _format_vision_prompt(self, user_question: str, context: str):
        """Format prompt for vision models"""
        base_prompt = f"""Please analyze the provided image(s) and answer the user's question.

QUESTION: {user_question}"""
        
        if context and context != "No relevant documents found.":
            base_prompt += f"""

ADDITIONAL CONTEXT:
{context}"""
        
        base_prompt += """

Please provide a clear analysis of what you see in the images:"""
        
        return base_prompt
    
    def _extract_from_context(self, user_question: str, context: str):
        """Improved fallback content extraction"""
        if not context or context == "No relevant documents found.":
            return "I don't have enough information in the uploaded documents to answer this question. Please upload relevant documents or ask about the content that has been uploaded."
        
        # Simple keyword-based extraction
        question_lower = user_question.lower()
        relevant_info = []
        
        # Look for lines that might be relevant
        for line in context.split('\n'):
            line = line.strip()
            if len(line) > 20:  # Only substantial lines
                line_lower = line.lower()
                # Check for keyword matches
                question_words = [word for word in question_lower.split() if len(word) > 3]
                matches = sum(1 for word in question_words if word in line_lower)
                
                if matches > 0:
                    relevant_info.append(line)
        
        if relevant_info:
            response = "Based on the available documents, here's relevant information:" + "\n".join(relevant_info[:3])
            return response[:800]  # Limit response length
        else:
            return "I found documents, but they don't contain specific information about your question. The documents might cover different topics."
    
    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """Convert image file to base64 string for Ollama"""
        try:
            with Image.open(image_path) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                max_size = (1024, 1024)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                return img_str
                
        except Exception as e:
            print(f"❌ Error converting image: {e}")
            return None