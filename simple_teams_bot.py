import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from dotenv import load_dotenv
import google.generativeai as genai
from document_processor import DocumentProcessor
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleTeamsBot:
    """
    Simplified Teams Bot that works without complex Bot Framework setup
    Perfect for local development and testing
    """
    
    def __init__(self):
        self.gemini_model = self._initialize_gemini()
        self.document_processor = DocumentProcessor()
        self.conversation_history: Dict[str, list] = {}
        
    def _initialize_gemini(self):
        """Initialize Gemini AI model"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment variables")
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            logger.info("Successfully initialized Gemini AI model")
            return model
        except Exception as e:
            logger.error(f"Error initializing Gemini: {e}")
            return None

    async def process_message(self, message_text: str, user_id: str = "default_user") -> str:
        """
        Process user message using Gemini AI
        """
        try:
            if not self.gemini_model:
                return "Sorry, I'm having trouble connecting to my AI brain right now. Please try again later."
            
            # Initialize conversation history for new users
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Add user message to history
            self.conversation_history[user_id].append(f"User: {message_text}")
            
            # Check for special commands
            if message_text.lower().startswith('/help'):
                return self._get_help_message()
            elif message_text.lower().startswith('/clear'):
                self.conversation_history[user_id] = []
                return "✅ Conversation history cleared! Starting fresh."
            elif message_text.lower().startswith('/status'):
                return self._get_status_message()
            
            # Build context with conversation history
            context = self._build_context(user_id)
            
            # Create a comprehensive prompt
            prompt = f"""You are a helpful digital assistant working within Microsoft Teams. 
            
Context from previous conversation:
{context}

Current user message: {message_text}

Please provide a helpful, professional response. Keep responses concise but informative.
If the user asks about your capabilities, mention that you can:
- Answer questions and provide information
- Help with analysis and problem-solving
- Process documents (if they share files)
- Maintain conversation context
- Provide various types of assistance within Teams

Respond naturally and professionally."""

            # Get response from Gemini
            response = self.gemini_model.generate_content(prompt)
            bot_response = response.text
            
            # Add bot response to history
            self.conversation_history[user_id].append(f"Assistant: {bot_response}")
            
            # Keep conversation history manageable (last 10 exchanges)
            if len(self.conversation_history[user_id]) > 20:
                self.conversation_history[user_id] = self.conversation_history[user_id][-20:]
            
            return bot_response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I encountered an error while processing your message. Please try again. Error: {str(e)}"

    def _build_context(self, user_id: str) -> str:
        """Build conversation context from history"""
        if user_id not in self.conversation_history or not self.conversation_history[user_id]:
            return "No previous conversation."
        
        # Get last 6 exchanges (12 messages)
        recent_history = self.conversation_history[user_id][-12:]
        return "\n".join(recent_history)

    def _get_help_message(self) -> str:
        """Get help message"""
        return """🤖 **Digital Agent Help**

**Available Commands:**
• `/help` - Show this help message
• `/clear` - Clear conversation history
• `/status` - Check bot status

**What I can do:**
✅ Answer questions and provide information
✅ Help with analysis and problem-solving  
✅ Maintain conversation context
✅ Process and analyze shared documents
✅ Provide assistance across various topics

**Tips:**
• I remember our conversation context
• Feel free to ask follow-up questions
• Share documents for analysis
• Use natural language - no special formatting needed

Just ask me anything! 😊"""

    def _get_status_message(self) -> str:
        """Get status message"""
        gemini_status = "✅ Connected" if self.gemini_model else "❌ Disconnected"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""🔍 **Digital Agent Status**

**AI Model:** {gemini_status}
**Document Processor:** ✅ Ready
**Timestamp:** {timestamp}

**System:** All systems operational and ready to assist! 🚀"""

def create_simple_app() -> web.Application:
    """Create a simple web application for testing"""
    
    # Create the bot
    bot = SimpleTeamsBot()
    
    # Simple message endpoint for testing
    async def messages(req: Request) -> Response:
        try:
            # Handle both Bot Framework format and simple JSON
            body = await req.json()
            logger.info(f"Received message: {body}")
            
            # Extract message text from different possible formats
            message_text = ""
            user_id = "test_user"
            conversation_id = "default_conversation"
            activity_id = None
            
            if "text" in body:
                # Bot Framework format
                message_text = body["text"]
                if "from" in body and "id" in body["from"]:
                    user_id = body["from"]["id"]
                if "conversation" in body and "id" in body["conversation"]:
                    conversation_id = body["conversation"]["id"]
                if "id" in body:
                    activity_id = body["id"]
            elif "message" in body:
                # Simple format for testing
                message_text = body["message"]
                user_id = body.get("user_id", "test_user")
            else:
                return json_response({"error": "No message text found"}, status=400)
            
            # Process the message
            response_text = await bot.process_message(message_text, user_id)
            
            # Return response in PROPER Bot Framework format
            response_data = {
                "type": "message", 
                "text": response_text,
                "from": {
                    "id": "bot",
                    "name": "Digital Agent"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Copy conversation info from incoming message if available
            if "conversation" in body:
                response_data["conversation"] = body["conversation"]
            if "serviceUrl" in body:
                response_data["serviceUrl"] = body["serviceUrl"]
            
            # Add replyToId if this is a reply to a specific message
            if activity_id:
                response_data["replyToId"] = activity_id
            
            logger.info(f"Sending response: {response_data}")
            return json_response(response_data)
            
        except Exception as e:
            logger.error(f"Error in messages endpoint: {e}")
            import traceback
            traceback.print_exc()
            return json_response({"error": str(e)}, status=500)

    # Test endpoint for simple interaction
    async def test_chat(req: Request) -> Response:
        """Simple test endpoint"""
        try:
            data = await req.json()
            message = data.get("message", "Hello!")
            user_id = data.get("user_id", "test_user")
            
            logger.info(f"Processing message: {message}")
            
            response = await bot.process_message(message, user_id)
            
            logger.info(f"Response generated successfully")
            
            return json_response({
                "user_message": message,
                "bot_response": response,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in test_chat: {e}")
            import traceback
            traceback.print_exc()
            return json_response({
                "error": str(e),
                "details": "Check server logs for more information"
            }, status=500)

    # Health check endpoint
    async def health_check(req: Request) -> Response:
        gemini_status = "connected" if bot.gemini_model else "disconnected"
        return json_response({
            "status": "healthy", 
            "gemini_ai": gemini_status,
            "timestamp": datetime.now().isoformat()
        })
    
    # Simple web UI for testing
    async def web_ui(req: Request) -> Response:
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Teams Digital Agent - Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .bot-message { background-color: #f5f5f5; text-align: left; }
        .input-container { display: flex; gap: 10px; }
        input[type="text"] { flex: 1; padding: 10px; }
        button { padding: 10px 20px; background-color: #0078d4; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #106ebe; }
    </style>
</head>
<body>
    <h1>🤖 Teams Digital Agent - Test Interface</h1>
    <div id="chat" class="chat-container"></div>
    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Type your message here..." onkeypress="handleKeyPress(event)">
        <button onclick="sendMessage()">Send</button>
        <button onclick="clearChat()">Clear</button>
    </div>
    
    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                // Add bot response to chat
                addMessage(data.bot_response, 'bot');
                
            } catch (error) {
                addMessage('Error: ' + error.message, 'bot');
            }
        }
        
        function addMessage(text, type) {
            const chat = document.getElementById('chat');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.textContent = text;
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }
        
        function clearChat() {
            document.getElementById('chat').innerHTML = '';
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        // Add welcome message
        addMessage('👋 Welcome! I\'m your digital agent. Type "/help" to see what I can do!', 'bot');
    </script>
</body>
</html>
        """
        return web.Response(text=html, content_type='text/html')

    # Create web app
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    app.router.add_post("/test", test_chat)
    app.router.add_get("/health", health_check)
    app.router.add_get("/", web_ui)
    
    return app

if __name__ == "__main__":
    try:
        # Get port from environment or use default
        port = int(os.getenv("PORT", 3978))
        
        # Create and run the app
        app = create_simple_app()
        logger.info(f"Starting Simple Teams Digital Agent on port {port}")
        logger.info(f"Web UI available at: http://localhost:{port}")
        logger.info(f"API endpoint: http://localhost:{port}/api/messages")
        logger.info(f"Test endpoint: http://localhost:{port}/test")
        web.run_app(app, host="127.0.0.1", port=port)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}") 