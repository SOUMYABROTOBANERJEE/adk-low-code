#!/usr/bin/env python3
"""
Test script for agent embed functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:8083"
TEST_AGENT_NAME = "Test_Embed_Agent"
TEST_AGENT_DESCRIPTION = "A test agent for embedding functionality"

def test_embed_functionality():
    """Test the complete embed functionality"""
    print("🧪 Testing Agent Embed Functionality")
    print("=" * 50)
    
    # Step 1: Create a test agent
    print("\n1️⃣ Creating test agent...")
    agent_data = {
        "name": TEST_AGENT_NAME,
        "description": TEST_AGENT_DESCRIPTION,
        "agent_type": "llm",
        "system_prompt": "You are a helpful test agent that can be embedded on websites.",
        "instructions": "Provide helpful responses to user queries.",
        "model_settings": {
            "model": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_data)
        if response.status_code == 200:
            agent = response.json()
            agent_id = agent['id']
            print(f"✅ Agent created successfully: {agent['name']} (ID: {agent_id})")
        else:
            print(f"❌ Failed to create agent: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return
    
    # Step 2: Create an embed for the agent
    print("\n2️⃣ Creating agent embed...")
    try:
        response = requests.post(f"{BASE_URL}/api/agents/{agent_id}/embed")
        if response.status_code == 200:
            embed_data = response.json()
            embed_id = embed_data['embed_id']
            print(f"✅ Embed created successfully: {embed_id}")
            print(f"   Embed URL: {embed_data['embed_url']}")
        else:
            print(f"❌ Failed to create embed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating embed: {e}")
        return
    
    # Step 3: Test the embedded agent interface
    print("\n3️⃣ Testing embedded agent interface...")
    try:
        response = requests.get(f"{BASE_URL}/api/embed/{embed_id}")
        if response.status_code == 200:
            print("✅ Embedded agent interface loaded successfully")
            print(f"   Content length: {len(response.text)} characters")
        else:
            print(f"❌ Failed to load embedded agent: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error loading embedded agent: {e}")
        return
    
    # Step 4: Test chat functionality
    print("\n4️⃣ Testing embedded agent chat...")
    try:
        chat_data = {"message": "Hello! Can you introduce yourself?"}
        response = requests.post(f"{BASE_URL}/api/embed/{embed_id}/chat", json=chat_data)
        if response.status_code == 200:
            chat_response = response.json()
            print("✅ Chat functionality working")
            print(f"   Response: {chat_response.get('response', 'No response')}")
        else:
            print(f"❌ Failed to chat with embedded agent: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        return
    
    # Step 5: List agent embeds
    print("\n5️⃣ Listing agent embeds...")
    try:
        response = requests.get(f"{BASE_URL}/api/agents/{agent_id}/embeds")
        if response.status_code == 200:
            embeds_data = response.json()
            print(f"✅ Found {len(embeds_data['embeds'])} embeds for agent")
            for embed in embeds_data['embeds']:
                print(f"   - {embed['embed_id']} (Views: {embed['access_count']})")
        else:
            print(f"❌ Failed to list embeds: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error listing embeds: {e}")
        return
    
    # Step 6: Test embed code generation
    print("\n6️⃣ Testing embed code generation...")
    try:
        response = requests.post(f"{BASE_URL}/api/agents/{agent_id}/embed")
        if response.status_code == 200:
            embed_data = response.json()
            embed_code = embed_data['embed_code']
            print("✅ Embed code generated successfully")
            print(f"   Code length: {len(embed_code)} characters")
            print(f"   Contains iframe: {'iframe' in embed_code}")
            print(f"   Contains script: {'script' in embed_code}")
        else:
            print(f"❌ Failed to generate embed code: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error generating embed code: {e}")
        return
    
    # Step 7: Clean up - Delete test embeds
    print("\n7️⃣ Cleaning up test embeds...")
    try:
        response = requests.get(f"{BASE_URL}/api/agents/{agent_id}/embeds")
        if response.status_code == 200:
            embeds_data = response.json()
            for embed in embeds_data['embeds']:
                delete_response = requests.delete(f"{BASE_URL}/api/embed/{embed['embed_id']}")
                if delete_response.status_code == 200:
                    print(f"✅ Deleted embed: {embed['embed_id']}")
                else:
                    print(f"❌ Failed to delete embed {embed['embed_id']}: {delete_response.status_code}")
        else:
            print(f"❌ Failed to get embeds for cleanup: {response.status_code}")
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
    
    print("\n🎉 Embed functionality test completed successfully!")
    print(f"📝 Test agent '{TEST_AGENT_NAME}' remains in the system")
    print(f"🔗 You can now use the embed functionality in the web interface")

if __name__ == "__main__":
    try:
        test_embed_functionality()
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
