#!/usr/bin/env python3
"""
Test script to verify all existing functionality still works
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8083"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"🔍 Testing {method} {endpoint}")
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == expected_status:
            try:
                result = response.json()
                print(f"   ✅ Success: {json.dumps(result, indent=2)[:200]}...")
                return result
            except Exception as e:
                print(f"   ⚠️  Response parsing error: {e}")
                print(f"   Raw response: {response.text[:200]}...")
                return response.text
        else:
            print(f"   ❌ Error: {response.text[:200]}...")
            return None
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout")
        return None
    except requests.exceptions.ConnectionError:
        print(f"   🔌 Connection failed")
        return None
    except Exception as e:
        print(f"   💥 Error: {e}")
        return None

def test_existing_functionality():
    """Test all existing functionality to ensure nothing broke"""
    print("\n🔧 TESTING EXISTING FUNCTIONALITY")
    print("=" * 50)
    
    # Test health endpoint
    test_endpoint("/api/health")
    
    # Test models endpoint
    test_endpoint("/api/models")
    
    # Test config endpoint
    test_endpoint("/api/config")
    
    # Test tools endpoint
    test_endpoint("/api/tools")
    
    # Test templates endpoint
    test_endpoint("/api/templates")
    
    # Test agents endpoint
    test_endpoint("/api/agents")
    
    # Test custom tools endpoint
    test_endpoint("/api/custom_tools")
    
    # Test function tools endpoint
    test_endpoint("/api/function_tools")

def test_new_functionality():
    """Test the new functionality I added"""
    print("\n🆕 TESTING NEW FUNCTIONALITY")
    print("=" * 50)
    
    # Test projects endpoint
    test_endpoint("/api/projects")
    
    # Test sub-agents endpoints
    test_endpoint("/api/agents/available-for-sub")
    
    # Test creating a simple project
    project_data = {
        "name": "test_project",
        "description": "Test project for functionality verification"
    }
    test_endpoint("/api/projects", "POST", project_data)
    
    # Test creating a simple agent
    agent_data = {
        "name": "test_agent",
        "description": "Test agent for functionality verification",
        "agent_type": "llm",
        "system_prompt": "You are a test agent."
    }
    test_endpoint("/api/agents", "POST", agent_data)
    
    # Test sub-agent functionality
    print("\n🔗 TESTING SUB-AGENT FUNCTIONALITY")
    print("-" * 40)
    
    # Get the created agent ID for testing sub-agents
    agents_response = test_endpoint("/api/agents")
    if agents_response and 'agents' in agents_response and len(agents_response['agents']) > 0:
        test_agent_id = agents_response['agents'][0]['id']
        
        # Test getting sub-agents for an agent
        test_endpoint(f"/api/agents/{test_agent_id}/sub-agents")
        
        # Test adding a sub-agent
        sub_agent_data = {
            "name": "test_sub_agent",
            "description": "Test sub-agent for functionality verification",
            "agent_type": "llm",
            "system_prompt": "You are a test sub-agent."
        }
        test_endpoint(f"/api/agents/{test_agent_id}/sub-agents", "POST", sub_agent_data)
        
        # Test linking an existing agent as sub-agent
        link_data = {"source_agent_id": test_agent_id}
        test_endpoint(f"/api/agents/{test_agent_id}/sub-agents/from-existing", "POST", link_data)
    else:
        print("   ⚠️  Skipping sub-agent tests - no agents available")

def main():
    """Main test function"""
    print("🚀 FUNCTIONALITY VERIFICATION TEST")
    print("=" * 60)
    
    # Test existing functionality first
    test_existing_functionality()
    
    # Test new functionality
    test_new_functionality()
    
    print("\n🎯 TESTING COMPLETE!")
    print("All existing functionality should still work as expected.")

if __name__ == "__main__":
    main()
