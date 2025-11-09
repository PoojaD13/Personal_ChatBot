const API_BASE_URL = 'http://localhost:8000';

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkBackendStatus();
    loadSystemInfo();
});

// Check if backend is running
async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        if (response.ok) {
            document.getElementById('status').innerHTML = '🟢 Backend Connected';
            document.getElementById('status').style.background = 'rgba(76, 175, 80, 0.3)';
        } else {
            throw new Error('Backend not responding');
        }
    } catch (error) {
        document.getElementById('status').innerHTML = '🔴 Backend Offline';
        document.getElementById('status').style.background = 'rgba(244, 67, 54, 0.3)';
        console.error('Backend connection failed:', error);
    }
}

// Load system information
async function loadSystemInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/debug-status`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('systemInfo').innerHTML = `
                <div>📊 Documents: ${data.vector_db_documents}</div>
                <div>🤖 AI Status: ${data.llm_manager_status}</div>
                <div>💾 Temp Files: ${data.temp_files_count}</div>
            `;
        }
    } catch (error) {
        document.getElementById('systemInfo').innerHTML = 'Unable to load system info';
    }
}

// Upload file function
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file first');
        return;
    }

    const uploadStatus = document.getElementById('uploadStatus');
    uploadStatus.innerHTML = '⏳ Uploading...';
    uploadStatus.style.background = 'rgba(255, 193, 7, 0.3)';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            uploadStatus.innerHTML = `✅ ${result.message}`;
            uploadStatus.style.background = 'rgba(76, 175, 80, 0.3)';
            
            // Clear file input
            fileInput.value = '';
            
            // Reload system info to show updated document count
            loadSystemInfo();
        } else {
            throw new Error('Upload failed');
        }
    } catch (error) {
        uploadStatus.innerHTML = '❌ Upload failed. Check backend.';
        uploadStatus.style.background = 'rgba(244, 67, 54, 0.3)';
        console.error('Upload error:', error);
    }
}

// Send chat message
async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    if (!message) {
        alert('Please enter a message');
        return;
    }

    // Add user message to chat
    addMessage('user', message, []);
    userInput.value = '';

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: 'web-ui'
            })
        });

        if (response.ok) {
            const data = await response.json();
            addMessage('assistant', data.response, data.sources || []);
        } else {
            throw new Error('Chat failed');
        }
    } catch (error) {
        addMessage('assistant', 'Sorry, I encountered an error. Please check if the backend is running.', []);
        console.error('Chat error:', error);
    }
}

// Ask predefined question
function askQuestion(question) {
    document.getElementById('userInput').value = question;
    sendMessage();
}

// Add message to chat
function addMessage(role, text, sources) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let messageHTML = `<strong>${role === 'user' ? 'You' : 'JARVIS'}:</strong> ${text}`;
    
    if (sources && sources.length > 0) {
        messageHTML += `<div class="sources">📁 Sources: ${sources.join(', ')}</div>`;
    }
    
    messageDiv.innerHTML = messageHTML;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Clear chat
function clearChat() {
    document.getElementById('chatMessages').innerHTML = `
        <div class="message assistant">
            <strong>JARVIS:</strong> Hello! I'm JARVIS. Upload documents or ask me questions about your content.
        </div>
    `;
}

// Handle Enter key in textarea
document.getElementById('userInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Voice recognition and synthesis variables
let recognition = null;
let synthesis = null;
let isListening = false;
let isSpeaking = false;

// Initialize voice features when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkBackendStatus();
    loadSystemInfo();
    initializeVoiceFeatures();
});

// Initialize voice recognition and synthesis
function initializeVoiceFeatures() {
    // Check browser support
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onstart = function() {
            isListening = true;
            document.getElementById('voiceInputBtn').classList.add('recording');
            document.getElementById('stopVoiceBtn').style.display = 'inline-block';
            document.getElementById('voiceInputBtn').style.display = 'none';
            showVoiceStatus('🎤 Listening... Speak now', 'listening');
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('userInput').value = transcript;
            showVoiceStatus('✅ Speech recognized! Click Send or speak again.', 'listening');
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            showVoiceStatus('❌ Error: ' + event.error, 'listening');
            stopVoiceInput();
        };
        
        recognition.onend = function() {
            stopVoiceInput();
        };
    } else {
        console.warn('Speech recognition not supported');
        document.getElementById('voiceInputBtn').style.display = 'none';
    }
    
    // Check speech synthesis support
    if ('speechSynthesis' in window) {
        synthesis = window.speechSynthesis;
    } else {
        console.warn('Speech synthesis not supported');
        document.getElementById('speakBtn').style.display = 'none';
    }
}

// Start voice input
function startVoiceInput() {
    if (recognition && !isListening) {
        try {
            recognition.start();
        } catch (error) {
            console.error('Error starting voice recognition:', error);
            showVoiceStatus('❌ Cannot start voice input', 'listening');
        }
    }
}

// Stop voice input
function stopVoiceInput() {
    if (recognition && isListening) {
        recognition.stop();
        isListening = false;
        document.getElementById('voiceInputBtn').classList.remove('recording');
        document.getElementById('stopVoiceBtn').style.display = 'none';
        document.getElementById('voiceInputBtn').style.display = 'inline-block';
        hideVoiceStatus();
    }
}

// Speak the last assistant response
function speakLastResponse() {
    if (!synthesis) {
        alert('Text-to-speech not supported in your browser');
        return;
    }
    
    if (isSpeaking) {
        synthesis.cancel();
        isSpeaking = false;
        document.getElementById('speakBtn').innerHTML = '🔊 Speak Response';
        hideVoiceStatus();
        return;
    }
    
    const chatMessages = document.getElementById('chatMessages');
    const messages = chatMessages.getElementsByClassName('message assistant');
    
    if (messages.length > 0) {
        const lastMessage = messages[messages.length - 1];
        // Extract text content without HTML tags
        const text = lastMessage.textContent.replace('JARVIS:', '').trim();
        
        if (text) {
            speakText(text);
        } else {
            alert('No response to speak');
        }
    } else {
        alert('No responses available to speak');
    }
}

// Speak text using Web Speech API
function speakText(text) {
    if (!synthesis) return;
    
    // Cancel any ongoing speech
    synthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configure voice
    utterance.rate = 1.0;    // Speaking rate (0.1 to 10)
    utterance.pitch = 1.0;   // Pitch (0 to 2)
    utterance.volume = 1.0;  // Volume (0 to 1)
    
    // Try to use a nice voice
    const voices = synthesis.getVoices();
    const englishVoice = voices.find(voice => 
        voice.lang.startsWith('en-') && 
        voice.name.includes('Female')
    ) || voices.find(voice => voice.lang.startsWith('en-'));
    
    if (englishVoice) {
        utterance.voice = englishVoice;
    }
    
    utterance.onstart = function() {
        isSpeaking = true;
        document.getElementById('speakBtn').innerHTML = '⏹️ Stop Speaking';
        showVoiceStatus('🔊 Speaking response...', 'speaking');
    };
    
    utterance.onend = function() {
        isSpeaking = false;
        document.getElementById('speakBtn').innerHTML = '🔊 Speak Response';
        hideVoiceStatus();
    };
    
    utterance.onerror = function(event) {
        console.error('Speech synthesis error:', event);
        isSpeaking = false;
        document.getElementById('speakBtn').innerHTML = '🔊 Speak Response';
        hideVoiceStatus();
        alert('Error speaking text');
    };
    
    synthesis.speak(utterance);
}

// Auto-speak new responses
function addMessage(role, text, sources) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let messageHTML = `<strong>${role === 'user' ? 'You' : 'JARVIS'}:</strong> ${text}`;
    
    if (sources && sources.length > 0) {
        messageHTML += `<div class="sources">📁 Sources: ${sources.join(', ')}</div>`;
    }
    
    messageDiv.innerHTML = messageHTML;
    chatMessages.appendChild(messageDiv);
    
    // // Auto-speak assistant responses
    // if (role === 'assistant' && synthesis && !isSpeaking) {
    //     // Small delay to let user read first
    //     setTimeout(() => {
    //         if (confirm('Would you like me to speak the response?')) {
    //             speakText(text);
    //         }
    //     }, 500);
    // }
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show voice status message
function showVoiceStatus(message, type) {
    let statusDiv = document.getElementById('voiceStatus');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.id = 'voiceStatus';
        statusDiv.className = `voice-status ${type}`;
        document.querySelector('.chat-input').parentNode.insertBefore(statusDiv, document.querySelector('.chat-input'));
    }
    statusDiv.textContent = message;
    statusDiv.className = `voice-status ${type}`;
    statusDiv.style.display = 'block';
}

// Hide voice status
function hideVoiceStatus() {
    const statusDiv = document.getElementById('voiceStatus');
    if (statusDiv) {
        statusDiv.style.display = 'none';
    }
}

// Voice command shortcuts
function setupVoiceCommands() {
    document.addEventListener('keydown', function(e) {
        // Ctrl + Space to start voice input
        if (e.ctrlKey && e.code === 'Space') {
            e.preventDefault();
            startVoiceInput();
        }
        
        // Escape to stop voice input/speech
        if (e.code === 'Escape') {
            stopVoiceInput();
            if (synthesis && isSpeaking) {
                synthesis.cancel();
                isSpeaking = false;
                document.getElementById('speakBtn').innerHTML = '🔊 Speak Response';
                hideVoiceStatus();
            }
        }
    });
}

// Add this function for conversational responses
function getConversationalResponse(message) {
    const lowerMessage = message.toLowerCase().trim();
    
    const conversationalResponses = {
        // Greetings
        'hi': 'Hello! How can I help you today?',
        'hello': 'Hi there! Ready to explore your documents?',
        'hey': 'Hey! What can I do for you?',
        
        // Thanks
        'thanks': 'You\'re welcome! Happy to help.',
        'thank you': 'You\'re welcome! Is there anything else you need?',
        'thank': 'You\'re welcome!',
        
        // How are you
        'how are you': 'I\'m functioning optimally, thank you! Ready to assist with your documents.',
        'how are you doing': 'I\'m doing great! Ready to help you analyze your content.',
        
        // Who are you
        'who are you': 'I\'m JARVIS, your AI assistant! I help you analyze and understand your documents.',
        'what are you': 'I\'m JARVIS - an AI assistant that can read and analyze your uploaded documents.',
        
        // Capabilities
        'what can you do': 'I can read your documents (PDF, Word, images), answer questions about them, and help you find specific information. Try uploading a file!',
        'help': 'I can: • Read your documents • Answer questions • Find specific information • Analyze content. Just upload files and ask away!',
        
        // Goodbyes
        'bye': 'Goodbye! Feel free to come back with more questions.',
        'goodbye': 'See you later! Don\'t hesitate to ask if you need more help.',
        'see you': 'See you! I\'ll be here when you need me.',
        
        // Polite
        'please': 'Of course! How can I assist you?',
        'sorry': 'No need to apologize! How can I help?',
        
        // Fun
        'joke': 'Why did the AI cross the road? To get to the other side of the data set! 😄',
        'tell me a joke': 'Why do programmers prefer dark mode? Because light attracts bugs! 🐛',
        
        // Time
        'what time is it': `It's currently ${new Date().toLocaleTimeString()}.`,
        'what day is it': `Today is ${new Date().toLocaleDateString()}.`,
        
        // Status
        'are you there': 'Yes, I\'m here and ready to help!',
        'are you awake': 'Always awake and ready to assist you!'
    };
    
    // Check for exact matches first
    if (conversationalResponses[lowerMessage]) {
        return conversationalResponses[lowerMessage];
    }
    
    // Check for partial matches
    for (const [key, response] of Object.entries(conversationalResponses)) {
        if (lowerMessage.includes(key) && key.length > 3) {
            return response;
        }
    }
    
    return null; // No conversational response found
}

// Update the sendMessage function to use conversational responses
async function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    if (!message) {
        alert('Please enter a message');
        return;
    }

    // Add user message to chat
    addMessage('user', message, []);
    userInput.value = '';

    // Check for conversational response first
    const conversationalResponse = getConversationalResponse(message);
    if (conversationalResponse) {
        // Small delay to make it feel natural
        setTimeout(() => {
            addMessage('assistant', conversationalResponse, []);
        }, 500);
        return;
    }

    // If no conversational response, call the API
    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: 'web-ui'
            })
        });

        if (response.ok) {
            const data = await response.json();
            addMessage('assistant', data.response, data.sources || []);
        } else {
            throw new Error('Chat failed');
        }
    } catch (error) {
        addMessage('assistant', 'Sorry, I encountered an error. Please check if the backend is running.', []);
        console.error('Chat error:', error);
    }
}

// Initialize voice commands
setupVoiceCommands();