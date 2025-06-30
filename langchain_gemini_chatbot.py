import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

class LangChainGeminiChatbot:
    def __init__(self):
        """Initialize the LangChain Gemini chatbot"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize the Gemini model through LangChain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=self.api_key,
            temperature=0.7,
            max_output_tokens=2048
        )
        
        # Create conversation memory
        self.memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True
        )
        
        # Create conversation chain
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            verbose=False
        )
        
        # Custom prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["history", "input"],
            template="""You are a helpful and friendly AI assistant. You provide clear, accurate, and helpful responses.

Current conversation:
{history}
Human: {input}
AI Assistant:"""
        )
        
        # Create conversation chain with custom prompt
        self.conversation_with_prompt = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt_template,
            verbose=False
        )
    
    def chat(self, user_input: str) -> str:
        """Send a message to the chatbot and get response"""
        try:
            response = self.conversation_with_prompt.predict(input=user_input)
            return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def simple_chat(self, user_input: str) -> str:
        """Simple chat without conversation memory"""
        try:
            messages = [
                SystemMessage(content="You are a helpful and friendly AI assistant."),
                HumanMessage(content=user_input)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_history(self) -> str:
        """Get formatted conversation history"""
        try:
            messages = self.memory.chat_memory.messages
            if not messages:
                return "📝 No conversation history yet."
            
            history_text = "📝 Conversation History:\n" + "=" * 50 + "\n"
            
            for i, message in enumerate(messages, 1):
                if hasattr(message, 'type'):
                    if message.type == 'human':
                        history_text += f"👤 Human ({i}): {message.content}\n"
                    elif message.type == 'ai':
                        history_text += f"🤖 Assistant ({i}): {message.content}\n"
                    else:
                        history_text += f"💬 {message.type.title()} ({i}): {message.content}\n"
                else:
                    # Fallback for different message types
                    role = getattr(message, 'role', 'Unknown')
                    history_text += f"💬 {role.title()} ({i}): {message.content}\n"
                
                history_text += "-" * 30 + "\n"
            
            # Add summary
            total_messages = len(messages)
            history_text += f"\n📊 Total messages: {total_messages}"
            
            return history_text
            
        except Exception as e:
            return f"Error retrieving history: {str(e)}"
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()

def main():
    """Main function to run the chatbot"""
    print(" LangChain + Gemini Chatbot")
    print("=" * 40)
    print("Commands:")
    print("  'quit', 'exit', or 'q' - Exit the chatbot")
    print("  'clear' - Clear conversation memory")
    print("  'history' - Show all conversation history")
    print("  'simple' - Switch to simple mode (no memory)")
    print("=" * 40)
    
    try:
        chatbot = LangChainGeminiChatbot()
        print("✅ Chatbot initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        return
    
    simple_mode = False
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'clear':
                chatbot.clear_memory()
                print("🧹 Conversation memory cleared!")
                continue
            
            if user_input.lower() == 'history':
                history = chatbot.get_history()
                print(history)
                continue
            
            if user_input.lower() == 'simple':
                simple_mode = not simple_mode
                mode = "simple" if simple_mode else "conversation"
                print(f" Switched to {mode} mode")
                continue
            
            if not user_input:
                continue
            
            # Get response based on mode
            if simple_mode:
                response = chatbot.simple_chat(user_input)
            else:
                response = chatbot.chat(user_input)
            
            print(f"🤖 Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 