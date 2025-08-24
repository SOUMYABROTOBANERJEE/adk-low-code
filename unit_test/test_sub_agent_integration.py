#!/usr/bin/env python3
"""
Test script for sub-agent integration in agent creation
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_sub_agent_integration():
    """Test the complete sub-agent integration flow"""
    
    print("🧪 Testing Sub-Agent Integration in Agent Creation")
    print("=" * 60)
    
    # Test 1: Create a simple agent first (to use as sub-agent)
    print("\n1. Creating a base agent to use as sub-agent...")
    
    base_agent_data = {
        "name": "Test Base Agent",
        "description": "A test agent to be used as sub-agent",
        "agent_type": "llm",
        "system_prompt": "You are a helpful test agent.",
        "instructions": "Provide helpful responses",
        "tools": [],
        "model_settings": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "sub_agents": {"existing": [], "new": []}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents", json=base_agent_data)
        if response.status_code == 200:
            base_agent = response.json()
            base_agent_id = base_agent['agent']['id']
            print(f"✅ Base agent created with ID: {base_agent_id}")
        else:
            print(f"❌ Failed to create base agent: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating base agent: {e}")
        return
    
    # Test 2: Create an agent with existing sub-agent
    print("\n2. Creating an agent with existing sub-agent...")
    
    agent_with_existing_sub = {
        "name": "Main Agent with Existing Sub",
        "description": "An agent that uses an existing agent as sub-agent",
        "agent_type": "llm",
        "system_prompt": "You are a main agent that coordinates with sub-agents.",
        "instructions": "Coordinate tasks with your sub-agents",
        "tools": [],
        "model_settings": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "sub_agents": {
            "existing": [base_agent_id],
            "new": []
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_with_existing_sub)
        if response.status_code == 200:
            main_agent = response.json()
            main_agent_id = main_agent['agent']['id']
            print(f"✅ Main agent created with existing sub-agent: {main_agent_id}")
            print(f"   Sub-agents: {len(main_agent['agent']['sub_agents'])}")
        else:
            print(f"❌ Failed to create main agent: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating main agent: {e}")
        return
    
    # Test 3: Create an agent with new sub-agent
    print("\n3. Creating an agent with new sub-agent...")
    
    agent_with_new_sub = {
        "name": "Main Agent with New Sub",
        "description": "An agent that creates a new sub-agent during creation",
        "agent_type": "llm",
        "system_prompt": "You are a main agent that creates new sub-agents.",
        "instructions": "Create and manage new sub-agents",
        "tools": [],
        "model_settings": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "sub_agents": {
            "existing": [],
            "new": [
                {
                    "name": "New Sub Agent",
                    "type": "llm",
                    "description": "A newly created sub-agent",
                    "system_prompt": "You are a specialized sub-agent."
                }
            ]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_with_new_sub)
        if response.status_code == 200:
            new_sub_agent = response.json()
            new_sub_agent_id = new_sub_agent['agent']['id']
            print(f"✅ Main agent created with new sub-agent: {new_sub_agent_id}")
            print(f"   Sub-agents: {len(new_sub_agent['agent']['sub_agents'])}")
        else:
            print(f"❌ Failed to create agent with new sub-agent: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating agent with new sub-agent: {e}")
        return
    
    # Test 4: Create an agent with both existing and new sub-agents
    print("\n4. Creating an agent with both existing and new sub-agents...")
    
    agent_with_both = {
        "name": "Main Agent with Both Types",
        "description": "An agent that combines existing and new sub-agents",
        "agent_type": "llm",
        "system_prompt": "You are a main agent that manages multiple types of sub-agents.",
        "instructions": "Coordinate between existing and new sub-agents",
        "tools": [],
        "model_settings": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "sub_agents": {
            "existing": [base_agent_id],
            "new": [
                {
                    "name": "Another New Sub",
                    "type": "sequential",
                    "description": "A sequential sub-agent",
                    "system_prompt": "You are a sequential processing sub-agent."
                }
            ]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_with_both)
        if response.status_code == 200:
            both_agent = response.json()
            both_agent_id = both_agent['agent']['id']
            print(f"✅ Main agent created with both types: {both_agent_id}")
            print(f"   Sub-agents: {len(both_agent['agent']['sub_agents'])}")
        else:
            print(f"❌ Failed to create agent with both types: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating agent with both types: {e}")
        return
    
    # Test 5: Verify all agents were created
    print("\n5. Verifying all agents were created...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Total agents in system: {len(agents['agents'])}")
            
            # Find our test agents
            test_agents = [a for a in agents['agents'] if 'Test' in a.get('name', '') or 'Main Agent' in a.get('name', '')]
            print(f"   Test agents found: {len(test_agents)}")
            
            for agent in test_agents:
                sub_count = len(agent.get('sub_agents', []))
                print(f"   - {agent['name']}: {sub_count} sub-agents")
                
        else:
            print(f"❌ Failed to list agents: {response.status_code}")
    except Exception as e:
        print(f"❌ Error listing agents: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Sub-Agent Integration Test Completed!")
    print("\nNext steps:")
    print("1. Open the UI at http://localhost:8000")
    print("2. Go to Agents section")
    print("3. Click 'Create Agent'")
    print("4. Fill in agent details")
    print("5. Use the Sub-Agents section to:")
    print("   - Add existing agents as sub-agents")
    print("   - Create new sub-agents")
    print("6. Submit the form to test the integration")

if __name__ == "__main__":
    try:
        test_sub_agent_integration()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")

