#!/usr/bin/env python3
"""
Debug script to identify issues with the Teams bot
"""

import os
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai

async def test_gemini_connection():
    """Test Gemini connection step by step"""
    print("🔍 Testing Gemini AI Connection...")
    print("-" * 40)
    
    # Load environment
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"1. API Key found: {bool(api_key and api_key != 'your_gemini_api_key_here')}")
    
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ PROBLEM: Gemini API key not set!")
        print("SOLUTION: Create a .env file with your real Gemini API key:")
        print("GEMINI_API_KEY=your_actual_api_key_here")
        return False
    
    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        print("2. ✅ Gemini configured successfully")
    except Exception as e:
        print(f"2. ❌ Gemini configuration failed: {e}")
        return False
    
    # Test model creation
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("3. ✅ Model created successfully")
    except Exception as e:
        print(f"3. ❌ Model creation failed: {e}")
        return False
    
    # Test simple generation
    try:
        response = model.generate_content("Say hello")
        print("4. ✅ Test generation successful")
        print(f"   Response: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"4. ❌ Test generation failed: {e}")
        print(f"   Error details: {str(e)}")
        return False

async def test_bot_creation():
    """Test if the bot can be created"""
    print("\n🤖 Testing Bot Creation...")
    print("-" * 40)
    
    try:
        from simple_teams_bot import SimpleTeamsBot
        bot = SimpleTeamsBot()
        print("1. ✅ Bot created successfully")
        
        # Test message processing
        response = await bot.process_message("Hello", "test_user")
        print("2. ✅ Message processing works")
        print(f"   Response: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Bot creation/testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_web_endpoints():
    """Test if web endpoints work"""
    print("\n🌐 Testing Web Endpoints...")
    print("-" * 40)
    
    try:
        import aiohttp
        
        # Test if we can make a simple request
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:3978/health') as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print("1. ✅ Health endpoint works")
                        print(f"   Status: {data.get('status')}")
                        print(f"   Gemini: {data.get('gemini_ai')}")
                        return True
                    else:
                        print(f"1. ❌ Health endpoint returned status {resp.status}")
                        return False
            except aiohttp.ClientConnectorError:
                print("1. ❌ Cannot connect to bot - is it running?")
                print("   Start the bot with: python simple_teams_bot.py")
                return False
                
    except Exception as e:
        print(f"❌ Web endpoint test failed: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("🔧 Checking Environment...")
    print("-" * 40)
    
    load_dotenv()
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("1. ✅ .env file found")
    else:
        print("1. ⚠️ .env file not found")
        print("   Create .env file with: GEMINI_API_KEY=your_key_here")
    
    # Check environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        print("2. ✅ GEMINI_API_KEY is set")
    else:
        print("2. ❌ GEMINI_API_KEY not properly set")
    
    # Check Python packages
    try:
        import aiohttp
        print("3. ✅ aiohttp available")
    except ImportError:
        print("3. ❌ aiohttp not installed")
        print("   Install with: pip install aiohttp")
    
    try:
        import google.generativeai
        print("4. ✅ google-generativeai available")
    except ImportError:
        print("4. ❌ google-generativeai not installed")
        print("   Install with: pip install google-generativeai")

async def main():
    """Run all debug tests"""
    print("🚀 Teams Bot Debug Tool")
    print("=" * 50)
    
    # Check environment first
    check_environment()
    
    # Test Gemini connection
    gemini_works = await test_gemini_connection()
    
    if gemini_works:
        # Test bot creation
        bot_works = await test_bot_creation()
        
        if bot_works:
            # Test web endpoints (only if bot is running)
            await test_web_endpoints()
    
    print("\n" + "=" * 50)
    print("🎯 SUMMARY:")
    
    if not gemini_works:
        print("❌ Main issue: Gemini AI connection failed")
        print("🔧 Fix: Check your GEMINI_API_KEY in .env file")
    else:
        print("✅ Gemini AI is working")
        print("🎉 Your bot should work! Try: python simple_teams_bot.py")
    
    print("\n📝 Quick Start:")
    print("1. Create .env file with your Gemini API key")
    print("2. Run: python simple_teams_bot.py")
    print("3. Open: http://localhost:3978")
    print("4. Check browser console (F12) for JavaScript errors")

if __name__ == "__main__":
    asyncio.run(main()) 