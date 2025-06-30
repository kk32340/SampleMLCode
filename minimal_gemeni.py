import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def list_available_models():
    """
    List all available Gemini models
    """
    try:
        models = genai.list_models()
        print("📋 Available Gemini Models:")
        print("-" * 40)
        
        for model in models:
            # Only show models that support generateContent
            if 'generateContent' in model.supported_generation_methods:
                print(f"✅ {model.name}")
        
        return [model.name for model in models if 'generateContent' in model.supported_generation_methods]
    
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []

def connect_to_gemini(model_name=None):
    """
    Simple function to connect to Gemini LLM and send a prompt
    """
    # Get API key from environment variable
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Check if API key exists
    if not api_key:
        print("Error: GEMINI_API_KEY not found!")
        print("Please set your API key in environment variables or .env file")
        return None
    
    try:
        # Configure the API key
        genai.configure(api_key=api_key)
        
        # If no model specified, use the latest flash model
        if not model_name:
            model_name = 'gemini-1.5-flash-latest'
        
        # Initialize the model
        model = genai.GenerativeModel(model_name)
        
        print(f"✅ Successfully connected to {model_name}!")
        return model
        
    except Exception as e:
        print(f"❌ Error connecting to Gemini: {e}")
        
        # Try to list available models for troubleshooting
        print("\nLet's check available models:")
        list_available_models()
        return None

def ask_gemini(model, prompt):
    """
    Send a prompt to Gemini and get response
    """
    try:
        # Generate response
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"Error generating response: {e}"

def main():
    """
    Main function to demonstrate Gemini connection
    """
    print("🚀 Connecting to Gemini LLM...")
    
    # First, let's see what models are available
    print("\nChecking available models...")
    available_models = list_available_models()
    
    # Try different model names in order of preference
    model_names_to_try = [
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro-latest', 
        'gemini-1.0-pro'
    ]
    
    model = None
    for model_name in model_names_to_try:
        print(f"\n🔄 Trying to connect with {model_name}...")
        model = connect_to_gemini(model_name)
        if model:
            break
    
    if model:
        # Example prompts
        prompts = [
            "Hello! What is artificial intelligence?",
            "Write a short poem about Python programming",
            "Explain machine learning in simple terms"
        ]
        
        print("\n" + "="*50)
        print("GEMINI LLM DEMO")
        print("="*50)
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\n📝 Prompt {i}: {prompt}")
            print("-" * 40)
            
            # Get response from Gemini
            response = ask_gemini(model, prompt)
            print(f"🤖 Gemini: {response}")
            print("-" * 40)
        
        # Interactive mode
        print("\n💬 Interactive mode (type 'quit' to exit):")
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if user_input:
                response = ask_gemini(model, user_input)
                print(f"🤖 Gemini: {response}")
    else:
        print("❌ Could not connect to any Gemini model. Please check your API key and try again.")

if __name__ == "__main__":
    main()