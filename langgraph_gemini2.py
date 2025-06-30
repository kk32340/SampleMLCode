"""
Interactive LangGraph Workflow with User Input
==============================================

This example shows how to:
1. Pause workflow execution for user input
2. Process user responses
3. Continue workflow based on user choices
4. Handle multi-step interactive processes

Perfect for guided report migration!
"""

import os
from typing import TypedDict, List, Optional, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
import google.generativeai as genai
import json

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# State definition for interactive workflow
class InteractiveState(TypedDict):
    # User interaction
    current_step: str
    user_input: str
    waiting_for_user: bool
    user_responses: dict
    
    # Process data
    process_type: str
    collected_info: dict
    validation_results: dict
    
    # Messages and responses
    bot_message: str
    step_history: List[str]
    final_result: str
    
    # Error handling
    retry_count: int
    max_retries: int

# ==================== INTERACTIVE NODES ====================

def start_process(state: InteractiveState) -> InteractiveState:
    """Initialize the interactive process"""
    
    bot_message = """
🚀 Welcome to the Interactive Report Migration Assistant!

I'll guide you through the migration process step by step.

What would you like to do today?
1. Convert a single report
2. Batch convert multiple reports  
3. Check report compatibility
4. Get migration advice

Please reply with the number (1-4) or describe what you need.
    """.strip()
    
    return {
        **state,
        "current_step": "get_process_type",
        "waiting_for_user": True,
        "bot_message": bot_message,
        "step_history": ["Started interactive process"],
        "retry_count": 0,
        "max_retries": 3
    }

def process_type_selection(state: InteractiveState) -> InteractiveState:
    """Process user's choice of what they want to do"""
    
    user_input = state["user_input"].strip().lower()
    step_history = state["step_history"]
    
    # Parse user choice
    if "1" in user_input or "single" in user_input or "convert" in user_input:
        process_type = "single_conversion"
        next_message = """
📄 Single Report Conversion Selected

I'll help you convert one report. Please provide:

1. **Source file path** (e.g., /path/to/report.rdl)
2. **Source format** (SSRS, Power BI, Tableau, Crystal Reports)
3. **Target format** (what you want to convert TO)

You can provide all info at once or I'll ask for each piece.

Example: "Convert /reports/sales.rdl from SSRS to Power BI"
        """.strip()
        next_step = "collect_file_info"
        
    elif "2" in user_input or "batch" in user_input or "multiple" in user_input:
        process_type = "batch_conversion"
        next_message = """
📁 Batch Conversion Selected

I'll help you convert multiple reports. Please tell me:

1. **Folder path** containing your reports
2. **Source format** of all reports
3. **Target format** you want
4. **Any filters** (file patterns, date ranges, etc.)

Example: "Convert all SSRS reports in /reports/quarterly/ to Power BI"
        """.strip()
        next_step = "collect_batch_info"
        
    elif "3" in user_input or "compatibility" in user_input or "check" in user_input:
        process_type = "compatibility_check"
        next_message = """
🔍 Compatibility Check Selected

I'll analyze your report for migration compatibility.

Please provide:
1. **File path** to your report
2. **Source format** 
3. **Intended target format**

Example: "Check if /reports/complex_dashboard.rdl can convert from SSRS to Power BI"
        """.strip()
        next_step = "collect_compatibility_info"
        
    elif "4" in user_input or "advice" in user_input or "help" in user_input:
        process_type = "migration_advice"
        next_message = """
💡 Migration Advice Selected

I'll provide guidance on your migration project.

Tell me about your situation:
- What reports do you have?
- What formats are you working with?
- What challenges are you facing?
- What's your timeline?

Be as detailed as you'd like!
        """.strip()
        next_step = "collect_advice_info"
        
    else:
        # Invalid choice - retry
        retry_count = state.get("retry_count", 0) + 1
        if retry_count >= state.get("max_retries", 3):
            next_message = "I'm sorry, I couldn't understand your choice. Let's start over."
            next_step = "get_process_type"
            retry_count = 0
        else:
            next_message = f"""
I didn't understand that choice. Please select:

1. Convert a single report
2. Batch convert multiple reports
3. Check report compatibility  
4. Get migration advice

Try again ({retry_count}/{state.get('max_retries', 3)}):
            """.strip()
            next_step = "get_process_type"
        
        return {
            **state,
            "current_step": next_step,
            "waiting_for_user": True,
            "bot_message": next_message,
            "retry_count": retry_count,
            "step_history": step_history + [f"Invalid choice attempt {retry_count}"]
        }
    
    step_history.append(f"Selected process type: {process_type}")
    
    return {
        **state,
        "process_type": process_type,
        "current_step": next_step,
        "waiting_for_user": True,
        "bot_message": next_message,
        "step_history": step_history,
        "retry_count": 0
    }

def collect_file_info(state: InteractiveState) -> InteractiveState:
    """Collect single file conversion information"""
    
    user_input = state["user_input"]
    step_history = state["step_history"]
    collected_info = state.get("collected_info", {})
    
    # Try to extract file info using simple parsing
    # In real implementation, you'd use NLP/regex for better extraction
    
    formats = ["ssrs", "power bi", "powerbi", "tableau", "crystal reports"]
    found_formats = [f for f in formats if f in user_input.lower()]
    
    # Extract file path (simple pattern matching)
    import re
    file_pattern = r'[/\\][\w\\/.-]+'
    file_matches = re.findall(file_pattern, user_input)
    
    # Update collected info
    if file_matches:
        collected_info["file_path"] = file_matches[0]
    if "from" in user_input.lower() and "to" in user_input.lower():
        parts = user_input.lower().split("from")[1].split("to")
        if len(parts) == 2:
            for fmt in formats:
                if fmt in parts[0]:
                    collected_info["source_format"] = fmt
                if fmt in parts[1]:
                    collected_info["target_format"] = fmt
    
    # Check what we still need
    missing = []
    if not collected_info.get("file_path"):
        missing.append("file path")
    if not collected_info.get("source_format"):
        missing.append("source format")
    if not collected_info.get("target_format"):
        missing.append("target format")
    
    if missing:
        # Still need more info
        next_message = f"""
Thanks! I got some information, but I still need:
{chr(10).join(f"• {item}" for item in missing)}

Currently collected:
• File path: {collected_info.get('file_path', 'Not provided')}
• Source format: {collected_info.get('source_format', 'Not provided')}
• Target format: {collected_info.get('target_format', 'Not provided')}

Please provide the missing information:
        """.strip()
        
        step_history.append(f"Partial info collected: {len(collected_info)} items")
        
        return {
            **state,
            "collected_info": collected_info,
            "current_step": "collect_file_info",
            "waiting_for_user": True,
            "bot_message": next_message,
            "step_history": step_history
        }
    else:
        # We have everything we need
        next_message = f"""
✅ Perfect! I have all the information:

• **File**: {collected_info['file_path']}
• **From**: {collected_info['source_format']}  
• **To**: {collected_info['target_format']}

Would you like me to:
1. Proceed with the conversion
2. Check compatibility first
3. Modify the settings

Reply with 1, 2, or 3:
        """.strip()
        
        step_history.append("Complete file info collected")
        
        return {
            **state,
            "collected_info": collected_info,
            "current_step": "confirm_conversion",
            "waiting_for_user": True,
            "bot_message": next_message,
            "step_history": step_history
        }

def confirm_conversion(state: InteractiveState) -> InteractiveState:
    """Get user confirmation before proceeding"""
    
    user_input = state["user_input"].strip().lower()
    collected_info = state["collected_info"]
    step_history = state["step_history"]
    
    if "1" in user_input or "proceed" in user_input or "yes" in user_input:
        # User wants to proceed
        step_history.append("User confirmed conversion")
        return {
            **state,
            "current_step": "execute_conversion",
            "waiting_for_user": False,  # No user input needed for execution
            "step_history": step_history
        }
        
    elif "2" in user_input or "compatibility" in user_input or "check" in user_input:
        # User wants compatibility check first
        step_history.append("User requested compatibility check")
        return {
            **state,
            "current_step": "check_compatibility", 
            "waiting_for_user": False,
            "step_history": step_history
        }
        
    elif "3" in user_input or "modify" in user_input or "change" in user_input:
        # User wants to modify settings
        next_message = f"""
🔧 Let's modify the settings. Current configuration:

• **File**: {collected_info['file_path']}
• **From**: {collected_info['source_format']}
• **To**: {collected_info['target_format']}

What would you like to change?
1. File path
2. Source format  
3. Target format
4. Start over

Reply with the number or describe the change:
        """.strip()
        
        step_history.append("User wants to modify settings")
        
        return {
            **state,
            "current_step": "modify_settings",
            "waiting_for_user": True,
            "bot_message": next_message,
            "step_history": step_history
        }
    else:
        # Invalid choice
        next_message = """
Please choose:
1. Proceed with conversion
2. Check compatibility first  
3. Modify settings

Reply with 1, 2, or 3:
        """.strip()
        
        return {
            **state,
            "current_step": "confirm_conversion",
            "waiting_for_user": True,
            "bot_message": next_message,
            "step_history": step_history
        }

def execute_conversion(state: InteractiveState) -> InteractiveState:
    """Execute the actual conversion (no user input needed)"""
    
    collected_info = state["collected_info"] 
    step_history = state["step_history"]
    
    # Simulate conversion process
    # In real implementation, this would call your migration tool
    
    try:
        # Mock conversion result
        conversion_result = {
            "status": "success",
            "input_file": collected_info["file_path"],
            "output_file": f"/output/{collected_info['file_path'].split('/')[-1]}.converted",
            "source_format": collected_info["source_format"],
            "target_format": collected_info["target_format"],
            "conversion_time": "3.2 seconds",
            "warnings": ["Some custom fonts may not transfer exactly"],
            "elements_converted": 12,
            "elements_total": 12
        }
        
        final_result = f"""
✅ **Conversion Completed Successfully!**

📊 **Results:**
• Input: {conversion_result['input_file']}
• Output: {conversion_result['output_file']}
• Format: {conversion_result['source_format']} → {conversion_result['target_format']}
• Time: {conversion_result['conversion_time']}
• Elements: {conversion_result['elements_converted']}/{conversion_result['elements_total']} converted

⚠️ **Warnings:**
{chr(10).join(f"• {w}" for w in conversion_result['warnings'])}

🎉 Your report is ready! Check the output file for the converted report.

Would you like to convert another report? (yes/no)
        """.strip()
        
        step_history.append("Conversion completed successfully")
        
        return {
            **state,
            "final_result": final_result,
            "current_step": "ask_continue",
            "waiting_for_user": True,
            "bot_message": final_result,
            "step_history": step_history
        }
        
    except Exception as e:
        error_message = f"""
❌ **Conversion Failed**

Error: {str(e)}

Would you like to:
1. Try again with different settings
2. Check compatibility first
3. Get help with this error

Reply with 1, 2, or 3:
        """.strip()
        
        step_history.append(f"Conversion failed: {str(e)}")
        
        return {
            **state,
            "current_step": "handle_error",
            "waiting_for_user": True,
            "bot_message": error_message,
            "step_history": step_history
        }

def ask_continue(state: InteractiveState) -> InteractiveState:
    """Ask if user wants to continue with more conversions"""
    
    user_input = state["user_input"].strip().lower()
    
    if "yes" in user_input or "y" in user_input or "sure" in user_input:
        # Start over
        return {
            **state,
            "current_step": "get_process_type",
            "waiting_for_user": True,
            "bot_message": "Great! What would you like to do next?\n\n1. Convert a single report\n2. Batch convert multiple reports\n3. Check report compatibility\n4. Get migration advice",
            "collected_info": {},  # Reset collected info
            "step_history": state["step_history"] + ["User wants to continue"]
        }
    else:
        # End conversation
        return {
            **state,
            "current_step": "end",
            "waiting_for_user": False,
            "final_result": "👋 Thanks for using the Interactive Report Migration Assistant! Have a great day!",
            "step_history": state["step_history"] + ["User ended conversation"]
        }

# =================== ROUTING LOGIC ===================

def route_next_step(state: InteractiveState) -> str:
    """Route to next step based on current state"""
    
    current_step = state["current_step"]
    
    # Direct routing based on current step
    if current_step == "get_process_type":
        return "process_type_selection"
    elif current_step == "collect_file_info":
        return "collect_file_info"
    elif current_step == "confirm_conversion":
        return "confirm_conversion"
    elif current_step == "execute_conversion":
        return "execute_conversion"
    elif current_step == "ask_continue":
        return "ask_continue"
    elif current_step == "end":
        return END
    else:
        return "start_process"  # Default fallback

# =================== GRAPH CREATION ===================

def create_interactive_workflow():
    """Create the interactive workflow graph"""
    
    # Use memory for persistence across interactions
    memory = MemorySaver()
    
    workflow = StateGraph(InteractiveState)
    
    # Add all nodes
    workflow.add_node("start_process", start_process)
    workflow.add_node("process_type_selection", process_type_selection)
    workflow.add_node("collect_file_info", collect_file_info)
    workflow.add_node("confirm_conversion", confirm_conversion)
    workflow.add_node("execute_conversion", execute_conversion)
    workflow.add_node("ask_continue", ask_continue)
    
    # Set entry point
    workflow.set_entry_point("start_process")
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "start_process",
        route_next_step,
        {
            "process_type_selection": "process_type_selection",
            "start_process": "start_process"
        }
    )
    
    workflow.add_conditional_edges(
        "process_type_selection", 
        route_next_step,
        {
            "collect_file_info": "collect_file_info",
            "get_process_type": "process_type_selection"
        }
    )
    
    workflow.add_conditional_edges(
        "collect_file_info",
        route_next_step,
        {
            "collect_file_info": "collect_file_info",
            "confirm_conversion": "confirm_conversion"
        }
    )
    
    workflow.add_conditional_edges(
        "confirm_conversion",
        route_next_step,
        {
            "execute_conversion": "execute_conversion",
            "confirm_conversion": "confirm_conversion"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_conversion",
        route_next_step,
        {
            "ask_continue": "ask_continue"
        }
    )
    
    workflow.add_conditional_edges(
        "ask_continue",
        route_next_step,  
        {
            "process_type_selection": "process_type_selection",
            END: END
        }
    )
    
    return workflow.compile(checkpointer=memory)

# =================== INTERACTIVE DEMO ===================

def interactive_demo():
    """Run the interactive demo"""
    
    app = create_interactive_workflow()
    
    print("🤖 Interactive Report Migration Assistant")
    print("=" * 50)
    print("This demo shows a multi-step interactive workflow.")
    print("The bot will guide you through the process step by step.")
    print("Type 'quit' at any time to exit.")
    print("=" * 50)
    
    # Use a thread ID for conversation persistence
    config = {"configurable": {"thread_id": "demo_user"}}
    
    # Initialize the conversation
    initial_state = {
        "current_step": "",
        "user_input": "",
        "waiting_for_user": False,
        "user_responses": {},
        "process_type": "",
        "collected_info": {},
        "validation_results": {},
        "bot_message": "",
        "step_history": [],
        "final_result": "",
        "retry_count": 0,
        "max_retries": 3
    }
    
    # Start the conversation
    result = app.invoke(initial_state, config)
    print(f"\n🤖 Assistant:\n{result['bot_message']}")
    
    # Interactive loop
    while result.get("waiting_for_user", False):
        user_input = input("\n💬 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("👋 Goodbye!")
            break
            
        if not user_input:
            print("Please provide a response.")
            continue
        
        # Update state with user input and continue
        result["user_input"] = user_input
        
        try:
            result = app.invoke(result, config)
            print(f"\n🤖 Assistant:\n{result['bot_message']}")
            
            # Check if we've reached the end
            if not result.get("waiting_for_user", False):
                if result.get("final_result"):
                    print(f"\n✅ Final Result:\n{result['final_result']}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            break

if __name__ == "__main__":
    interactive_demo()