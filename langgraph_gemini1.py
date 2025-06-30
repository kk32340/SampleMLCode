"""
Simple LangGraph Example with Gemini API
========================================

This example creates a basic graph that:
1. Takes user input
2. Calls Gemini API for processing
3. Formats the response
4. Returns the result

Requirements:
pip install langgraph google-generativeai
"""

import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
import google.generativeai as genai

# Configure Gemini API
# Set your API key: export GEMINI_API_KEY="your-api-key-here"
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Define the state structure
class ConversationState(TypedDict):
    user_input: str
    gemini_response: str
    final_response: str
    step_log: List[str]

# Node 1: Process user input
def process_input(state: ConversationState) -> ConversationState:
    """Clean and prepare user input"""
    user_input = state.get("user_input", "").strip()
    
    # Add to log
    step_log = state.get("step_log", [])
    step_log.append(f"✓ Processed input: '{user_input[:50]}...'")
    
    return {
        **state,
        "user_input": user_input,
        "step_log": step_log
    }

# Node 2: Call Gemini API
def call_gemini(state: ConversationState) -> ConversationState:
    """Make API call to Gemini"""
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create a more interesting prompt
        prompt = f"""
        You are a helpful AI assistant. Please respond to this user input thoughtfully:
        
        User: {state['user_input']}
        
        Provide a clear, helpful response.
        """
        
        # Generate response
        response = model.generate_content(prompt)
        gemini_response = response.text
        
        # Add to log
        step_log = state["step_log"]
        step_log.append("✓ Called Gemini API successfully")
        
    except Exception as e:
        gemini_response = f"Error calling Gemini API: {str(e)}"
        step_log = state["step_log"]
        step_log.append(f"✗ Gemini API error: {str(e)}")
    
    return {
        **state,
        "gemini_response": gemini_response,
        "step_log": step_log
    }

# Node 3: Format final response
def format_response(state: ConversationState) -> ConversationState:
    """Format the final response for the user"""
    
    final_response = f"""
🤖 AI Assistant Response:
{state['gemini_response']}

📋 Process Log:
{chr(10).join(state['step_log'])}
    """.strip()
    
    step_log = state["step_log"]
    step_log.append("✓ Formatted final response")
    
    return {
        **state,
        "final_response": final_response,
        "step_log": step_log
    }

# Create the graph
def create_simple_gemini_graph():
    """Create and compile the LangGraph workflow"""
    
    # Initialize the graph
    workflow = StateGraph(ConversationState)
    
    # Add nodes
    workflow.add_node("process_input", process_input)
    workflow.add_node("call_gemini", call_gemini)
    workflow.add_node("format_response", format_response)
    
    # Define the flow
    workflow.set_entry_point("process_input")
    workflow.add_edge("process_input", "call_gemini")
    workflow.add_edge("call_gemini", "format_response")
    workflow.add_edge("format_response", END)
    
    # Compile the graph
    return workflow.compile()

# Example usage
def main():
    """Example of how to use the graph"""
    
    # Create the compiled graph
    app = create_simple_gemini_graph()
    
    # Example inputs to test
    test_inputs = [
        "What is machine learning?",
        "Explain Python decorators in simple terms",
        "How do I build a REST API?"
    ]
    
    print("🚀 Simple LangGraph + Gemini Example")
    print("=" * 40)
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n📝 Test {i}: {user_input}")
        print("-" * 30)
        
        # Initial state
        initial_state = {
            "user_input": user_input,
            "gemini_response": "",
            "final_response": "",
            "step_log": []
        }
        
        try:
            # Run the graph
            result = app.invoke(initial_state)
            print(result["final_response"])
            
        except Exception as e:
            print(f"❌ Error: {e}")

# Interactive version
def interactive_chat():
    """Interactive chat using the graph"""
    
    app = create_simple_gemini_graph()
    
    print("🤖 Interactive Chat with Gemini (type 'quit' to exit)")
    print("=" * 50)
    
    while True:
        user_input = input("\n💬 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
            
        if not user_input:
            continue
            
        initial_state = {
            "user_input": user_input,
            "gemini_response": "",
            "final_response": "",
            "step_log": []
        }
        
        try:
            result = app.invoke(initial_state)
            print(f"\n{result['final_response']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

# Advanced example with conditional logic
def create_conditional_gemini_graph():
    """Example with conditional edges based on input type"""
    
    def route_by_input_type(state: ConversationState) -> str:
        """Route based on input type"""
        user_input = state["user_input"].lower()
        
        if "code" in user_input or "python" in user_input or "programming" in user_input:
            return "technical_response"
        elif "?" in user_input:
            return "question_response"
        else:
            return "general_response"
    
    def technical_response(state: ConversationState) -> ConversationState:
        """Specialized technical response"""
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        You are a senior software engineer. Provide a technical, detailed response:
        
        {state['user_input']}
        
        Include code examples if relevant.
        """
        
        response = model.generate_content(prompt)
        
        step_log = state["step_log"]
        step_log.append("✓ Used technical response path")
        
        return {
            **state,
            "gemini_response": response.text,
            "step_log": step_log
        }
    
    def question_response(state: ConversationState) -> ConversationState:
        """Specialized Q&A response"""
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Answer this question clearly and concisely:
        
        {state['user_input']}
        
        Provide a structured answer with examples.
        """
        
        response = model.generate_content(prompt)
        
        step_log = state["step_log"]
        step_log.append("✓ Used Q&A response path")
        
        return {
            **state,
            "gemini_response": response.text,
            "step_log": step_log
        }
    
    def general_response(state: ConversationState) -> ConversationState:
        """General conversational response"""
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Have a friendly, helpful conversation:
        
        {state['user_input']}
        """
        
        response = model.generate_content(prompt)
        
        step_log = state["step_log"]
        step_log.append("✓ Used general response path")
        
        return {
            **state,
            "gemini_response": response.text,
            "step_log": step_log
        }
    
    # Build the conditional graph
    workflow = StateGraph(ConversationState)
    
    # Add all nodes
    workflow.add_node("process_input", process_input)
    workflow.add_node("technical_response", technical_response)
    workflow.add_node("question_response", question_response)
    workflow.add_node("general_response", general_response)
    workflow.add_node("format_response", format_response)
    
    # Set entry point
    workflow.set_entry_point("process_input")
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "process_input",
        route_by_input_type,
        {
            "technical_response": "technical_response",
            "question_response": "question_response", 
            "general_response": "general_response"
        }
    )
    
    # All paths lead to formatting
    workflow.add_edge("technical_response", "format_response")
    workflow.add_edge("question_response", "format_response")
    workflow.add_edge("general_response", "format_response")
    workflow.add_edge("format_response", END)
    
    return workflow.compile()

if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv('GEMINI_API_KEY'):
        print("⚠️  Please set GEMINI_API_KEY environment variable")
        print("   export GEMINI_API_KEY='your-api-key-here'")
    else:
        # Run examples
        print("Choose an option:")
        print("1. Run test examples")
        print("2. Interactive chat")
        print("3. Conditional graph demo")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            main()
        elif choice == "2":
            interactive_chat()
        elif choice == "3":
            print("🔀 Conditional Graph Demo")
            app = create_conditional_gemini_graph()
            
            test_inputs = [
                "How do I write Python code for loops?",  # Technical
                "What is the capital of France?",          # Question
                "Hello there!"                             # General
            ]
            
            for user_input in test_inputs:
                initial_state = {
                    "user_input": user_input,
                    "gemini_response": "",
                    "final_response": "",
                    "step_log": []
                }
                
                result = app.invoke(initial_state)
                print(f"\n📝 Input: {user_input}")
                print(result["final_response"])
        else:
            print("Invalid choice")