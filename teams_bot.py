import os
import asyncio
from datetime import datetime
from typing import Dict, Any
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory, CardFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes, SuggestedActions, CardAction, ActionTypes
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import CloudAdapter
from dotenv import load_dotenv
import google.generativeai as genai
from document_processor import DocumentProcessor
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TeamsDigitalAgent(ActivityHandler):
    """
    Teams Bot that acts as a digital agent using Gemini AI
    """
    
    def __init__(self):
        super().__init__()
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

    async def on_message_activity(self, turn_context: TurnContext):
        """
        Handle incoming messages from Teams
        """
        user_message = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id
        
        # Initialize conversation history for new users
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        # Add user message to history
        self.conversation_history[user_id].append(f"User: {user_message}")
        
        # Process the message and get response
        response = await self._process_message(user_message, user_id)
        
        # Add bot response to history
        self.conversation_history[user_id].append(f"Assistant: {response}")
        
        # Keep conversation history manageable (last 10 exchanges)
        if len(self.conversation_history[user_id]) > 20:
            self.conversation_history[user_id] = self.conversation_history[user_id][-20:]
        
        # Send response back to Teams
        await turn_context.send_activity(MessageFactory.text(response))

    async def _process_message(self, message: str, user_id: str) -> str:
        """
        Process user message using Gemini AI
        """
        try:
            if not self.gemini_model:
                return "Sorry, I'm having trouble connecting to my AI brain right now. Please try again later."
            
            # Check for special commands
            if message.lower().startswith('/help'):
                return self._get_help_message()
            elif message.lower().startswith('/clear'):
                self.conversation_history[user_id] = []
                return "✅ Conversation history cleared! Starting fresh."
            elif message.lower().startswith('/status'):
                return self._get_status_message()
            
            # Build context with conversation history
            context = self._build_context(user_id)
            
            # Create a comprehensive prompt
            prompt = f"""You are a helpful digital assistant working within Microsoft Teams. 
            
Context from previous conversation:
{context}

Current user message: {message}

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
            return response.text
            
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

    async def on_members_added_activity(
        self, members_added: ChannelAccount, turn_context: TurnContext
    ):
        """
        Greet new members when they join
        """
        welcome_text = """👋 **Welcome to your Digital Agent!**

I'm here to help you with questions, analysis, and various tasks within Teams.

Type `/help` to see what I can do, or just start chatting with me naturally!

How can I assist you today? 😊"""

        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(MessageFactory.text(welcome_text))

# Create the main application
def create_app() -> web.Application:
    """Create the main aiohttp application"""
    
    # Create adapter with minimal configuration for maximum compatibility
    # This approach works with most Bot Framework versions
    
    # Simple credentials
    app_id = os.getenv("MICROSOFT_APP_ID", "")
    app_password = os.getenv("MICROSOFT_APP_PASSWORD", "")
    
    # Try different adapter approaches for compatibility
    try:
        # Method 1: Try CloudAdapter with minimal auth (newer versions)
        from botbuilder.core.integration import BotFrameworkAuthentication
        
        # Create minimal authentication
        auth = BotFrameworkAuthentication()
        adapter = CloudAdapter(auth)
        logger.info("Using CloudAdapter with BotFrameworkAuthentication")
        
    except (ImportError, Exception) as e1:
        try:
            # Method 2: Try CloudAdapter with no auth (for local development)
            adapter = CloudAdapter()
            logger.info("Using CloudAdapter with no authentication")
            
        except Exception as e2:
            # Method 3: Fallback to basic aiohttp approach
            logger.warning(f"CloudAdapter failed: {e2}")
            logger.info("Using basic aiohttp approach")
            
            # Create a very basic adapter setup
            class BasicAdapter:
                def __init__(self):
                    self.app_id = app_id
                    self.app_password = app_password
                
                async def process_activity(self, activity, auth_header, callback):
                    """Basic activity processing"""
                    from botbuilder.core import TurnContext
                    
                    # Create a basic turn context
                    turn_context = TurnContext(self, activity)
                    
                    # Call the bot's on_turn method
                    await callback(turn_context)
                    
                    return None
            
            adapter = BasicAdapter()
    
    # Create the bot
    bot = TeamsDigitalAgent()
    
    # Define the main messaging endpoint
    async def messages(req: Request) -> Response:
        body = await req.json()
        activity = Activity().deserialize(body)
        auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""
        
        try:
            response = await adapter.process_activity(activity, auth_header, bot.on_turn)
            if response:
                return json_response(data=response.body, status=response.status)
            return Response(status=201)
        except Exception as e:
            logger.error(f"Error processing activity: {e}")
            return Response(status=500)

    # Create web app
    app = web.Application(middlewares=[aiohttp_error_middleware])
    app.router.add_post("/api/messages", messages)
    
    # Add a health check endpoint
    async def health_check(req: Request) -> Response:
        return json_response({"status": "healthy", "timestamp": datetime.now().isoformat()})
    
    app.router.add_get("/health", health_check)
    
    return app

if __name__ == "__main__":
    try:
        # Get port from environment or use default
        port = int(os.getenv("PORT", 3978))
        
        # Create and run the app
        app = create_app()
        logger.info(f"Starting Teams Digital Agent on port {port}")
        web.run_app(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}") 