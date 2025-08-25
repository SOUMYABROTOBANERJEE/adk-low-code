#!/usr/bin/env python3
"""
Debug script for embedded chat functionality
"""

import requests
import json
import sys

def test_embed_functionality():
    """Test the embedded chat functionality step by step"""
    
    base_url = "http://localhost:8083"
    
    print("🔍 Testing Embedded Chat Functionality")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   ADK Available: {response.json().get('adk_available')}")
            print(f"   Langfuse Available: {response.json().get('langfuse_available')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: List agents
    print("\n2. Testing agent listing...")
    try:
        response = requests.get(f"{base_url}/api/agents")
        if response.status_code == 200:
            agents = response.json().get('agents', [])
            print(f"✅ Found {len(agents)} agents")
            if agents:
                print(f"   First agent: {agents[0].get('name', 'Unknown')} (ID: {agents[0].get('id', 'Unknown')})")
                test_agent_id = agents[0]['id']
            else:
                print("   No agents found - creating a test agent...")
                test_agent_id = create_test_agent(base_url)
                if not test_agent_id:
                    return False
        else:
            print(f"❌ Agent listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Agent listing error: {e}")
        return False
    
    # Test 3: Create embed for the agent
    print(f"\n3. Creating embed for agent {test_agent_id}...")
    try:
        embed_data = {
            "name": "Test Embed",
            "description": "Debug test embed",
            "is_active": True
        }
        response = requests.post(f"{base_url}/api/agents/{test_agent_id}/embed", json=embed_data)
        if response.status_code == 200:
            embed_info = response.json()
            embed_id = embed_info.get('embed_id')
            print(f"✅ Embed created successfully")
            print(f"   Embed ID: {embed_id}")
            print(f"   Embed URL: {base_url}/api/embed/{embed_id}")
        else:
            print(f"❌ Embed creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Embed creation error: {e}")
        return False
    
    # Test 4: Test the embed endpoint
    print(f"\n4. Testing embed endpoint...")
    try:
        response = requests.get(f"{base_url}/api/embed/{embed_id}")
        if response.status_code == 200:
            print("✅ Embed endpoint working")
            print(f"   Content length: {len(response.text)} characters")
            if "sendMessage" in response.text:
                print("   ✅ JavaScript function 'sendMessage' found in HTML")
            else:
                print("   ❌ JavaScript function 'sendMessage' NOT found in HTML")
            if "chat-input" in response.text:
                print("   ✅ Chat input field found in HTML")
            else:
                print("   ❌ Chat input field NOT found in HTML")
        else:
            print(f"❌ Embed endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Embed endpoint error: {e}")
        return False
    
    # Test 5: Test the chat endpoint
    print(f"\n5. Testing chat endpoint...")
    try:
        chat_data = {"message": "Hello, this is a test message"}
        response = requests.post(f"{base_url}/api/embed/{embed_id}/chat", json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Chat endpoint working")
            print(f"   Success: {chat_response.get('success')}")
            print(f"   Response: {chat_response.get('response', 'No response')}")
            print(f"   Agent: {chat_response.get('agent_name', 'Unknown')}")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False
    
    # Test 6: Test CORS
    print(f"\n6. Testing CORS...")
    try:
        headers = {
            'Origin': 'http://example.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        response = requests.options(f"{base_url}/api/embed/{embed_id}/chat", headers=headers)
        print(f"✅ CORS preflight response: {response.status_code}")
        if 'access-control-allow-origin' in response.headers:
            print(f"   CORS headers present: {response.headers.get('access-control-allow-origin')}")
        else:
            print("   ⚠️ CORS headers not found")
    except Exception as e:
        print(f"❌ CORS test error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Summary:")
    print(f"   Embed URL: {base_url}/api/embed/{embed_id}")
    print(f"   Chat Endpoint: {base_url}/api/embed/{embed_id}/chat")
    print("\n📝 Next Steps:")
    print("   1. Open the embed URL in your browser")
    print("   2. Check browser console for JavaScript errors")
    print("   3. Try typing a message and clicking send")
    print("   4. Check network tab for failed requests")
    
    return True

def create_test_agent(base_url):
    """Create a test agent if none exist"""
    try:
        agent_data = {
            "name": "Debug Test Agent",
            "description": "A test agent for debugging embedded chat",
            "agent_type": "llm",
            "system_prompt": "You are a helpful test agent. Respond to user messages in a friendly way.",
            "is_enabled": True
        }
        response = requests.post(f"{base_url}/api/agents", json=agent_data)
        if response.status_code == 200:
            agent_info = response.json()
            print(f"   ✅ Test agent created: {agent_info.get('name')}")
            return agent_info.get('id')
        else:
            print(f"   ❌ Test agent creation failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Test agent creation error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting Embedded Chat Debug Test")
    print("Make sure your ADK platform is running on http://localhost:8083")
    print()
    
    success = test_embed_functionality()
    
    if success:
        print("\n✅ Debug test completed successfully!")
    else:
        print("\n❌ Debug test failed!")
        sys.exit(1)
