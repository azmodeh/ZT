#!/usr/bin/env python3
"""
Direct test of Gemini API connection
"""

import requests
import json

def test_gemini_connection():
    """Test Gemini API directly"""
    
    api_key = "AIzaSyDz3bfQ1iLNg_BvYgx5wzI9z6964_8v1Wo"
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    model = "gemini-2.0-flash"
    
    print("=== Testing Gemini Connection ===")
    print(f"API URL: {base_url}")
    print(f"Model: {model}")
    print(f"API Key: ***{api_key[-8:]}")
    
    # Test with OpenAI-compatible endpoint
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello! Please respond with 'Gemini connected successfully'"}
        ],
        "max_tokens": 50
    }
    
    try:
        print("\n🔗 Testing API connection...")
        response = requests.post(
            f"{base_url}chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ Gemini Response: {ai_response}")
            return True
        else:
            print(f"❌ Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

# Test with Google's native API format as backup
def test_gemini_native():
    """Test with native Google API format"""
    
    api_key = "AIzaSyDz3bfQ1iLNg_BvYgx5wzI9z6964_8v1Wo"
    
    print("\n=== Testing Native Gemini API ===")
    
    # Native Google API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": "Hello! Please respond with 'Native Gemini connected successfully'"
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            print(f"✅ Native Gemini Response: {text}")
            return True
        else:
            print(f"❌ Error Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    openai_compat = test_gemini_connection()
    native = test_gemini_native()
    
    print("\n=== Gemini Test Results ===")
    print(f"OpenAI Compatible: {'✅ Working' if openai_compat else '❌ Failed'}")
    print(f"Native API: {'✅ Working' if native else '❌ Failed'}")
    
    if openai_compat or native:
        print("🎉 Gemini connection successful!")
    else:
        print("⚠️ Gemini connection failed")
