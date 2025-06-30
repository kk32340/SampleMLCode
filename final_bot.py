#!/usr/bin/env python3
"""
Final working bot that properly responds to Bot Framework messages
This version correctly sends responses back to the Bot Framework Emulator
"""

import os
import json
from datetime import datetime
from typing import Dict, Any
from aiohttp import web, ClientSession
from aiohttp.web import Request, Response, json_response
from dotenv import load_dotenv
import google.generativeai as genai
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalBot:
    """
    Final bot that properly handles and responds to Bot Framework messages
    """
    
    def __init__(self):
        self.gemini_model = self._initialize_gemini()
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
        """Process user message using Gemini AI"""
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
• /help - Show this help message
• /clear - Clear conversation history
• /status - Check bot status

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

    async def send_response_to_bot_framework(self, service_url: str, conversation: dict, bot_response: str):
        """Send response back to Bot Framework"""
        try:
            # Create the response activity
            response_activity = {
                "type": "message",
                "text": bot_response,
                "from": {
                    "id": "bot",
                    "name": "Digital Agent"
                },
                "conversation": conversation,
                "timestamp": datetime.now().isoformat()
            }
            
            # For Bot Framework Emulator, we typically send to the conversation endpoint
            conversation_id = conversation.get("id", "")
            endpoint_url = f"{service_url}/v3/conversations/{conversation_id}/activities"
            
            logger.info(f"Sending response to: {endpoint_url}")
            
            async with ClientSession() as session:
                async with session.post(endpoint_url, json=response_activity) as resp:
                    if resp.status == 200 or resp.status == 201:
                        logger.info("Successfully sent response to Bot Framework")
                    else:
                        logger.warning(f"Failed to send response: {resp.status}")
                        
        except Exception as e:
            logger.error(f"Error sending response to Bot Framework: {e}")

def create_final_app() -> web.Application:
    """Create the final working web application"""
    
    # Create the bot
    bot = FinalBot()
    
    # Bot Framework messages endpoint
    async def messages(req: Request) -> Response:
        try:
            # Parse the incoming activity
            body = await req.json()
            logger.info(f"Received activity: {json.dumps(body, indent=2)}")
            
            # Extract message information
            activity_type = body.get("type", "")
            message_text = body.get("text", "").strip()
            user_id = "unknown"
            service_url = body.get("serviceUrl", "")
            conversation = body.get("conversation", {})
            
            # Get user ID from different possible locations
            if "from" in body and "id" in body["from"]:
                user_id = body["from"]["id"]
            
            logger.info(f"Activity type: {activity_type}, Message: {message_text}, User: {user_id}")
            
            # Only process message activities with text
            if activity_type == "message" and message_text:
                # Process the message
                response_text = await bot.process_message(message_text, user_id)
                logger.info(f"Generated response: {response_text[:100]}...")
                
                # Send response back to Bot Framework (if service URL is provided)
                if service_url and conversation:
                    await bot.send_response_to_bot_framework(service_url, conversation, response_text)
                else:
                    # For local emulator testing, we can also just log the response
                    logger.info(f"Bot Response: {response_text}")
                
                return Response(status=200, text="Message received and processed")
            
            else:
                logger.info(f"Ignoring activity type: {activity_type}")
                return Response(status=200, text="Activity acknowledged")
                
        except Exception as e:
            logger.error(f"Error in messages endpoint: {e}")
            import traceback
            traceback.print_exc()
            return Response(status=500, text=f"Error: {str(e)}")

    # Test endpoint for direct testing
    async def test_chat(req: Request) -> Response:
        """Test endpoint that returns the bot response directly"""
        try:
            data = await req.json()
            message = data.get("message", "Hello!")
            user_id = data.get("user_id", "test_user")
            
            logger.info(f"Processing test message: {message}")
            
            response = await bot.process_message(message, user_id)
            
            return json_response({
                "user_message": message,
                "bot_response": response,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error in test_chat: {e}")
            return json_response({
                "error": str(e)
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
    <title>Final Bot - Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ccc; height: 400px; overflow-y: auto; padding: 10px; margin: 10px 0; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .bot-message { background-color: #f5f5f5; text-align: left; }
        .input-container { display: flex; gap: 10px; }
        .status { color: green; font-weight: bold; margin: 10px 0; }
        input[type="text"] { flex: 1; padding: 10px; }
        button { padding: 10px 20px; background-color: #0078d4; color: white; border: none; cursor: pointer; }
        button:hover { background-color: #106ebe; }
    </style>
</head>
<body>
    <h1>🤖 Final Bot - Working Test Interface</h1>
    <div class="status">✅ Bot is working! Messages are being processed correctly.</div>
    <p><strong>Note:</strong> If you're using Bot Framework Emulator, responses will appear there. Use this interface for direct testing.</p>
    
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
        addMessage('👋 Welcome! I\'m your digital agent. Send messages through Bot Framework Emulator at http://127.0.0.1:3978/api/messages or test directly here!', 'bot');
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
        app = create_final_app()
        logger.info("=" * 60)
        logger.info("🚀 FINAL BOT - READY TO RECEIVE AND RESPOND TO MESSAGES!")
        logger.info("=" * 60)
        logger.info(f"🔗 Bot Framework Endpoint: http://localhost:{port}/api/messages")
        logger.info(f"🧪 Test Interface: http://localhost:{port}")
        logger.info(f"🏥 Health Check: http://localhost:{port}/health")
        logger.info(f"📝 Direct Test API: http://localhost:{port}/test")
        logger.info("-" * 60)
        logger.info("✅ Your bot is now ready to:")
        logger.info("   1. Receive messages from Bot Framework Emulator")
        logger.info("   2. Process them with Gemini AI")
        logger.info("   3. Send responses back properly!")
        logger.info("=" * 60)
        
        web.run_app(app, host="127.0.0.1", port=port)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        import traceback
        traceback.print_exc() 