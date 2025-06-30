import os
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import json

# Load environment variables
load_dotenv()

# Define the state structure
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_input: str
    current_step: str
    context: dict
    final_answer: str

class LangGraphGeminiWorkflow:
    def __init__(self):
        """Initialize the LangGraph workflow with Gemini"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=self.api_key,
            temperature=0.7,
            max_output_tokens=2048
        )
        
        # Create the workflow graph
        self.workflow = self.create_workflow()
        
        # Initialize memory saver for conversation persistence
        self.memory = MemorySaver()
    
    def create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes to the graph
        workflow.add_node("analyze_input", self.analyze_input)
        workflow.add_node("research_topic", self.research_topic)
        workflow.add_node("generate_response", self.generate_response)
        workflow.add_node("validate_response", self.validate_response)
        workflow.add_node("format_output", self.format_output)
        
        # Define the workflow edges
        workflow.set_entry_point("analyze_input")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "analyze_input",
            self.should_research,
            {
                "research": "research_topic",
                "direct": "generate_response"
            }
        )
        
        workflow.add_conditional_edges(
            "research_topic",
            self.should_validate,
            {
                "validate": "validate_response",
                "format": "format_output"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_response",
            self.should_validate,
            {
                "validate": "validate_response",
                "format": "format_output"
            }
        )
        
        workflow.add_edge("validate_response", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile()
    
    def analyze_input(self, state: AgentState) -> AgentState:
        """Analyze user input to determine next steps"""
        user_input = state["user_input"]
        
        # Create analysis prompt
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an input analyzer. Analyze the user's input and determine:
1. What type of question/request this is
2. Whether it requires research or can be answered directly
3. The complexity level (simple, medium, complex)

Respond in JSON format:
{{
    "type": "question|request|conversation",
    "requires_research": true/false,
    "complexity": "simple|medium|complex",
    "key_topics": ["topic1", "topic2"],
    "analysis": "brief analysis"
}}
"""),
            ("human", f"Analyze this input: {user_input}")
        ])
        
        # Get analysis
        chain = analysis_prompt | self.llm
        result = chain.invoke({})
        
        try:
            analysis = json.loads(result.content)
        except:
            analysis = {
                "type": "question",
                "requires_research": False,
                "complexity": "simple",
                "key_topics": [],
                "analysis": "Could not parse analysis"
            }
        
        # Update state
        state["context"]["analysis"] = analysis
        state["current_step"] = "analyzed"
        
        return state
    
    def research_topic(self, state: AgentState) -> AgentState:
        """Research the topic if needed"""
        user_input = state["user_input"]
        analysis = state["context"]["analysis"]
        
        # Create research prompt
        research_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research assistant. Research the given topic and provide:
1. Key facts and information
2. Relevant context
3. Sources or references (if applicable)

Be thorough but concise."""),
            ("human", f"Research this topic: {user_input}\nKey topics: {analysis.get('key_topics', [])}")
        ])
        
        # Get research
        chain = research_prompt | self.llm
        research_result = chain.invoke({})
        
        # Update state
        state["context"]["research"] = research_result.content
        state["current_step"] = "researched"
        
        return state
    
    def generate_response(self, state: AgentState) -> AgentState:
        """Generate initial response"""
        user_input = state["user_input"]
        analysis = state["context"]["analysis"]
        research = state["context"].get("research", "")
        
        # Create response generation prompt
        response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant. Generate a comprehensive response to the user's input.
If research was provided, incorporate it into your response.
Be clear, accurate, and helpful."""),
            ("human", f"""User input: {user_input}
Analysis: {analysis}
Research: {research}

Generate a helpful response:""")
        ])
        
        # Generate response
        chain = response_prompt | self.llm
        response_result = chain.invoke({})
        
        # Update state
        state["context"]["initial_response"] = response_result.content
        state["current_step"] = "generated"
        
        return state
    
    def validate_response(self, state: AgentState) -> AgentState:
        """Validate and improve the response"""
        user_input = state["user_input"]
        initial_response = state["context"]["initial_response"]
        analysis = state["context"]["analysis"]
        
        # Create validation prompt
        validation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a response validator. Review the generated response and:
1. Check for accuracy and completeness
2. Ensure it addresses the user's question
3. Improve clarity and structure if needed
4. Add any missing important information

Provide the improved response."""),
            ("human", f"""Original question: {user_input}
Generated response: {initial_response}
Analysis: {analysis}

Validate and improve the response:""")
        ])
        
        # Validate and improve
        chain = validation_prompt | self.llm
        validation_result = chain.invoke({})
        
        # Update state
        state["context"]["validated_response"] = validation_result.content
        state["current_step"] = "validated"
        
        return state
    
    def format_output(self, state: AgentState) -> AgentState:
        """Format the final output"""
        user_input = state["user_input"]
        analysis = state["context"]["analysis"]
        
        # Get the best response available
        if "validated_response" in state["context"]:
            response = state["context"]["validated_response"]
        elif "initial_response" in state["context"]:
            response = state["context"]["initial_response"]
        else:
            response = "I apologize, but I couldn't generate a proper response."
        
        # Create formatted output
        formatted_response = f"""**Response to your query:**

{response}

---
**Analysis Summary:**
- Type: {analysis.get('type', 'unknown')}
- Complexity: {analysis.get('complexity', 'unknown')}
- Research Required: {analysis.get('requires_research', False)}
- Key Topics: {', '.join(analysis.get('key_topics', []))}
"""
        
        # Update state
        state["final_answer"] = formatted_response
        state["current_step"] = "completed"
        
        return state
    
    def should_research(self, state: AgentState) -> str:
        """Determine if research is needed"""
        analysis = state["context"].get("analysis", {})
        requires_research = analysis.get("requires_research", False)
        complexity = analysis.get("complexity", "simple")
        
        # Research for complex questions or when explicitly required
        if requires_research or complexity in ["medium", "complex"]:
            return "research"
        return "direct"
    
    def should_validate(self, state: AgentState) -> str:
        """Determine if validation is needed"""
        analysis = state["context"].get("analysis", {})
        complexity = analysis.get("complexity", "simple")
        
        # Validate complex responses
        if complexity in ["medium", "complex"]:
            return "validate"
        return "format"
    
    def process_query(self, user_input: str, session_id: str = "default") -> str:
        """Process a user query through the workflow"""
        try:
            # Initialize state
            initial_state = {
                "messages": [],
                "user_input": user_input,
                "current_step": "started",
                "context": {},
                "final_answer": ""
            }
            
            # Run the workflow
            config = {"configurable": {"thread_id": session_id}}
            result = self.workflow.invoke(initial_state, config)
            
            return result["final_answer"]
            
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"
    
    def get_workflow_status(self, session_id: str = "default") -> dict:
        """Get the current status of the workflow"""
        try:
            # This would typically query the memory store
            # For simplicity, we'll return a basic status
            return {
                "session_id": session_id,
                "status": "active",
                "memory_available": True
            }
        except Exception as e:
            return {"error": str(e)}

def main():
    """Main function to demonstrate LangGraph workflow"""
    print(" LangGraph + Gemini Workflow Demo")
    print("=" * 50)
    print("This demo shows a multi-step workflow:")
    print("1. Analyze input")
    print("2. Research (if needed)")
    print("3. Generate response")
    print("4. Validate (if complex)")
    print("5. Format output")
    print("=" * 50)
    
    try:
        workflow = LangGraphGeminiWorkflow()
        print("✅ Workflow initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing workflow: {e}")
        return
    
    session_id = "demo_session"
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'status':
                status = workflow.get_workflow_status(session_id)
                print(f"📊 Status: {status}")
                continue
            
            if not user_input:
                continue
            
            print("\n Processing through workflow...")
            result = workflow.process_query(user_input, session_id)
            print(f"\n{result}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 