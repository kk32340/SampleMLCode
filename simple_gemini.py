 

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
model_name="gemini-2.0-flash"

genai.configure(api_key=api_key)

model = genai.GenerativeModel(model_name)

def ask_gemini(prompt):
    """
    Send a prompt to Gemini and get response
    """
    try:
        # Generate response
        response = model.generate_content(prompt)
        return response.text
    
    except Exception as e:
        return f"Error generating response: {e}"
    

while True:
    user_input = input("\nYou: ").strip()
    
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("👋 Goodbye!")
        break
    
    if user_input:
        response = ask_gemini(user_input)
        print(f"🤖 Gemini: {response}")