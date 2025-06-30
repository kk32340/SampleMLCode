import os
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()

# Define conversation state
class ConversationState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_input: str
    conversation_type: str
    response: str

class LangGraphConversationFlow:
    def __init__(self):
        """Initialize LangGraph conversation flow"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=self.api_key,
            temperature=0.7
        )
        
        # Create conversation flow
        self.conversation_flow = self.create_conversation_flow()
        
        # Memory for conversation persistence
        self.memory = MemorySaver()
    
    def create_conversation_flow(self) -> StateGraph:
        """Create conversation flow with different response types"""
        
        # Define the graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("classify_input", self.classify_input)
        workflow.add_node("casual_response", self.casual_response)
        workflow.add_node("formal_response", self.formal_response)
        workflow.add_node("technical_response", self.technical_response)
        workflow.add_node("creative_response", self.creative_response)
        
        # Set entry point
        workflow.set_entry_point("classify_input")
        
        # Add conditional edges based on classification
        workflow.add_conditional_edges(
            "classify_input",
            self.route_conversation,
            {
                "casual": "casual_response",
                "formal": "formal_response",
                "technical": "technical_response",
                "creative": "creative_response"
            }
        )
        
        # All response nodes go to END
        workflow.add_edge("casual_response", END)
        workflow.add_edge("formal_response", END)
        workflow.add_edge("technical_response", END)
        workflow.add_edge("creative_response", END)
        
        return workflow.compile()
    
    def classify_input(self, state: ConversationState) -> ConversationState:
        """Classify the type of conversation"""
        user_input = state["user_input"]
        
        classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """Classify the user's input into one of these categories:
- casual: Informal, friendly, everyday conversation
- formal: Professional, business-like, serious topics
- technical: Technical questions, programming, complex topics
- creative: Creative writing, brainstorming, artistic topics

Respond with just the category name."""),
            ("human", f"Classify: {user_input}")
        ])
        
        chain = classification_prompt | self.llm
        result = chain.invoke({})
        
        conversation_type = result.content.strip().lower()
        if conversation_type not in ["casual", "formal", "technical", "creative"]:
            conversation_type = "casual"  # Default
        
        state["conversation_type"] = conversation_type
        return state
    
    def casual_response(self, state: ConversationState) -> ConversationState:
        """Generate casual, friendly response"""
        user_input = state["user_input"]
        
        casual_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly, casual AI assistant. Respond in a warm, 
conversational tone. Use emojis occasionally and keep it light and engaging."""),
            ("human", f"User says: {user_input}")
        ])
        
        chain = casual_prompt | self.llm
        result = chain.invoke({})
        
        state["response"] = f"�� {result.content}"
        return state
    
    def formal_response(self, state: ConversationState) -> ConversationState:
        """Generate formal, professional response"""
        user_input = state["user_input"]
        
        formal_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional AI assistant. Provide clear, 
well-structured responses with proper formatting. Be thorough and authoritative."""),
            ("human", f"User query: {user_input}")
        ])
        
        chain = formal_prompt | self.llm
        result = chain.invoke({})
        
        state["response"] = f"📋 **Professional Response:**\n\n{result.content}"
        return state
    
    def technical_response(self, state: ConversationState) -> ConversationState:
        """Generate technical, detailed response"""
        user_input = state["user_input"]
        
        technical_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a technical expert. Provide detailed, accurate 
technical information. Use code examples when appropriate and explain complex concepts clearly."""),
            ("human", f"Technical question: {user_input}")
        ])
        
        chain = technical_prompt | self.llm
        result = chain.invoke({})
        
        state["response"] = f"⚙️ **Technical Analysis:**\n\n{result.content}"
        return state
    
    def creative_response(self, state: ConversationState) -> ConversationState:
        """Generate creative, imaginative response"""
        user_input = state["user_input"]
        
        creative_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a creative AI assistant. Think outside the box, 
be imaginative, and provide unique perspectives. Use creative language and metaphors."""),
            ("human", f"Creative prompt: {user_input}")
        ])
        
        chain = creative_prompt | self.llm
        result = chain.invoke({})
        
        state["response"] = f"🎨 **Creative Response:**\n\n{result.content}"
        return state
    
    def route_conversation(self, state: ConversationState) -> str:
        """Route to appropriate response type"""
        return state["conversation_type"]
    
    def chat(self, user_input: str, session_id: str = "default") -> str:
        """Process a chat message through the workflow"""
        try:
            # Initialize state
            initial_state = {
                "messages": [],
                "user_input": user_input,
                "conversation_type": "",
                "response": ""
            }
            
            # Run the workflow
            config = {"configurable": {"thread_id": session_id}}
            result = self.conversation_flow.invoke(initial_state, config)
            
            return result["response"]
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

def main():
    """Demo the conversation flow"""
    print("🔄 LangGraph Conversation Flow Demo")
    print("=" * 40)
    print("Try different types of inputs:")
    print("- Casual: 'Hey, how are you?'")
    print("- Formal: 'Please provide a business analysis'")
    print("- Technical: 'Explain how neural networks work'")
    print("- Creative: 'Write a story about a robot'")
    print("=" * 40)
    
    try:
        flow = LangGraphConversationFlow()
        print("✅ Conversation flow initialized!")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            response = flow.chat(user_input)
            print(f"\n🤖 {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 