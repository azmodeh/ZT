#!/usr/bin/env python3
"""
Test AI connection for ZT system
"""

import sys
import requests
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

def test_ai_connection():
    """Test AI connection using configured settings"""
    
    try:
        print("=== Testing AI Connection ===")
        
        # Load AI config from contract rules
        import importlib.util
        spec = importlib.util.spec_from_file_location("server", "contract-enforcer-mcp/server.py")
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        
        print("✅ Server module loaded")
        
        # Load contract rules to get AI config
        rules = server.load_contract_rules()
        ai_config = rules.get("ai_config", {})
        
        if not ai_config:
            print("❌ No AI configuration found")
            return False
            
        print("✅ AI configuration found:")
        print(f"   API URL: {ai_config.get('base_url', 'Not set')}")
        print(f"   Model: {ai_config.get('model', 'Not set')}")
        print(f"   API Key: {'***' + ai_config.get('api_key', '')[-8:] if ai_config.get('api_key') else 'Not set'}")
        
        # Test basic API connection
        api_key = ai_config.get("api_key")
        base_url = ai_config.get("base_url")
        model = ai_config.get("model")
        
        if not all([api_key, base_url, model]):
            print("❌ Incomplete AI configuration")
            return False
            
        # Test API with a simple request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Test connection - respond with 'OK'"}
            ],
            "max_tokens": 10
        }
        
        print("\n🔗 Testing API connection...")
        
        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"✅ AI Connection successful!")
                print(f"   Response: {ai_response.strip()}")
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
            
    except Exception as e:
        print(f"❌ General error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_integration():
    """Test AI integration with ZT utilities"""
    
    try:
        print("\n=== Testing AI Integration ===")
        
        # Import utilities
        from enforcement.utils import get_ai_config
        
        config = get_ai_config()
        print("✅ AI config loaded via utils:")
        print(f"   Model: {config.get('model', 'Not set')}")
        print(f"   Base URL: {config.get('base_url', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI integration error: {e}")
        return False

if __name__ == "__main__":
    connection_ok = test_ai_connection()
    integration_ok = test_ai_integration()
    
    print("\n=== AI Test Results ===")
    print(f"Connection: {'✅ Working' if connection_ok else '❌ Failed'}")
    print(f"Integration: {'✅ Working' if integration_ok else '❌ Failed'}")
    
    if connection_ok and integration_ok:
        print("🎉 AI system fully operational!")
    else:
        print("⚠️ AI system needs attention")
