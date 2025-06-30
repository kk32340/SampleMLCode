#!/usr/bin/env python3
"""
Simple test script to verify Teams bot setup
"""

import os
import sys
from dotenv import load_dotenv

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import aiohttp
        print("✅ aiohttp imported successfully")
    except ImportError as e:
        print(f"❌ aiohttp import failed: {e}")
        return False
    
    try:
        from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
        print("✅ Bot Framework core imported successfully")
    except ImportError as e:
        print(f"❌ Bot Framework core import failed: {e}")
        return False
    
    try:
        from botbuilder.integration.aiohttp import CloudAdapter
        print("✅ Bot Framework aiohttp integration imported successfully")
    except ImportError as e:
        print(f"❌ Bot Framework aiohttp integration import failed: {e}")
        return False
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment variables"""
    print("\n🔍 Testing environment variables...")
    
    load_dotenv()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        print("✅ GEMINI_API_KEY is set")
    else:
        print("⚠️ GEMINI_API_KEY is not set or using placeholder value")
        print("   Please update your .env file with a real Gemini API key")
    
    app_id = os.getenv("MICROSOFT_APP_ID")
    if app_id and app_id != "your_microsoft_app_id_here":
        print("✅ MICROSOFT_APP_ID is set")
    else:
        print("ℹ️ MICROSOFT_APP_ID not set (OK for local testing)")
    
    app_password = os.getenv("MICROSOFT_APP_PASSWORD")
    if app_password and app_password != "your_microsoft_app_password_here":
        print("✅ MICROSOFT_APP_PASSWORD is set")
    else:
        print("ℹ️ MICROSOFT_APP_PASSWORD not set (OK for local testing)")

def test_gemini_connection():
    """Test Gemini AI connection"""
    print("\n🔍 Testing Gemini AI connection...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            print("⚠️ Cannot test Gemini connection - API key not set")
            return False
        
        genai.configure(api_key=api_key)
        
        # Try to list models to verify connection
        try:
            models = list(genai.list_models())
            if models:
                print("✅ Gemini AI connection successful")
                print(f"   Found {len(models)} available models")
                return True
            else:
                print("⚠️ Gemini connection works but no models found")
                return False
        except Exception as e:
            print(f"❌ Gemini connection failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gemini connection: {e}")
        return False

def test_bot_creation():
    """Test if the bot can be created"""
    print("\n🔍 Testing bot creation...")
    
    try:
        from teams_bot import TeamsDigitalAgent
        bot = TeamsDigitalAgent()
        print("✅ Bot created successfully")
        return True
    except Exception as e:
        print(f"❌ Bot creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 Teams Digital Agent - Setup Test")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    all_passed = True
    
    all_passed &= test_imports()
    test_environment()  # This doesn't affect all_passed
    all_passed &= test_gemini_connection()
    all_passed &= test_bot_creation()
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Your bot setup looks good.")
        print("\nNext steps:")
        print("1. Make sure you have a valid GEMINI_API_KEY in your .env file")
        print("2. Run: python teams_bot.py")
        print("3. Test with Bot Framework Emulator at: http://localhost:3978/api/messages")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up your .env file with proper API keys")
        print("3. Check your Python version (3.9+ recommended)")

if __name__ == "__main__":
    main() 