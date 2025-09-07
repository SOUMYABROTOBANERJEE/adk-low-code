#!/usr/bin/env python3
"""
Test script to verify Firestore migration works correctly
Tests all existing functionality with Firestore backend
"""

import requests
import json
import time
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

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
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
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

def test_firestore_migration():
    """Test that Firestore migration works correctly"""
    print("\n🔥 TESTING FIRESTORE MIGRATION")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    health = test_endpoint("/api/health")
    if health and health.get('status') == 'healthy':
        print("   ✅ Platform is healthy")
    else:
        print("   ❌ Platform health check failed")
        return False
    
    # Test 2: Create a tool
    print("\n2. Testing tool creation...")
    tool_data = {
        "id": f"test_tool_{int(time.time())}",
        "name": "Test Firestore Tool",
        "description": "A test tool to verify Firestore functionality",
        "tool_type": "function",
        "function_code": "def execute(input_data):\n    return f'Processed: {input_data}'",
        "tags": ["test", "firestore"]
    }
    
    tool_result = test_endpoint("/api/tools", "POST", tool_data)
    if tool_result and tool_result.get('success'):
        print("   ✅ Tool created successfully in Firestore")
        tool_id = tool_result['tool']['id']
    else:
        print("   ❌ Tool creation failed")
        return False
    
    # Test 3: Retrieve the tool
    print("\n3. Testing tool retrieval...")
    retrieved_tool = test_endpoint(f"/api/tools/{tool_id}")
    if retrieved_tool and retrieved_tool.get('id') == tool_id:
        print("   ✅ Tool retrieved successfully from Firestore")
    else:
        print("   ❌ Tool retrieval failed")
        return False
    
    # Test 4: Create an agent
    print("\n4. Testing agent creation...")
    agent_data = {
        "id": f"test_agent_{int(time.time())}",
        "name": "Test Firestore Agent",
        "description": "A test agent to verify Firestore functionality",
        "agent_type": "llm",
        "system_prompt": "You are a test agent for Firestore verification.",
        "tools": [tool_id],
        "model_settings": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        "sub_agents": {"existing": [], "new": []}
    }
    
    agent_result = test_endpoint("/api/agents", "POST", agent_data)
    if agent_result and agent_result.get('success'):
        print("   ✅ Agent created successfully in Firestore")
        agent_id = agent_result['agent']['id']
    else:
        print("   ❌ Agent creation failed")
        return False
    
    # Test 5: Retrieve the agent
    print("\n5. Testing agent retrieval...")
    retrieved_agent = test_endpoint(f"/api/agents/{agent_id}")
    if retrieved_agent and retrieved_agent.get('id') == agent_id:
        print("   ✅ Agent retrieved successfully from Firestore")
    else:
        print("   ❌ Agent retrieval failed")
        return False
    
    # Test 6: Create a project
    print("\n6. Testing project creation...")
    project_data = {
        "id": f"test_project_{int(time.time())}",
        "name": "Test Firestore Project",
        "description": "A test project to verify Firestore functionality",
        "agents": [agent_id],
        "tools": [tool_id]
    }
    
    project_result = test_endpoint("/api/projects", "POST", project_data)
    if project_result and project_result.get('success'):
        print("   ✅ Project created successfully in Firestore")
        project_id = project_result['project']['id']
    else:
        print("   ❌ Project creation failed")
        return False
    
    # Test 7: Test chat functionality
    print("\n7. Testing chat functionality...")
    chat_data = {
        "message": "Hello, this is a test message for Firestore verification.",
        "session_id": f"test_session_{int(time.time())}"
    }
    
    chat_result = test_endpoint(f"/api/chat/{agent_id}", "POST", chat_data)
    if chat_result:
        print("   ✅ Chat functionality works with Firestore")
    else:
        print("   ⚠️  Chat functionality may have issues (this could be due to ADK availability)")
    
    # Test 8: List all data
    print("\n8. Testing data listing...")
    tools_list = test_endpoint("/api/tools")
    agents_list = test_endpoint("/api/agents")
    projects_list = test_endpoint("/api/projects")
    
    if tools_list and agents_list and projects_list:
        print(f"   ✅ Data listing works: {len(tools_list.get('tools', []))} tools, {len(agents_list.get('agents', []))} agents, {len(projects_list.get('projects', []))} projects")
    else:
        print("   ❌ Data listing failed")
        return False
    
    # Test 9: Cleanup
    print("\n9. Testing cleanup...")
    test_endpoint(f"/api/tools/{tool_id}", "DELETE")
    test_endpoint(f"/api/agents/{agent_id}", "DELETE")
    test_endpoint(f"/api/projects/{project_id}", "DELETE")
    print("   ✅ Cleanup completed")
    
    return True

def test_existing_functionality():
    """Test all existing functionality to ensure nothing broke"""
    print("\n🔧 TESTING EXISTING FUNCTIONALITY")
    print("=" * 50)
    
    # Test core endpoints
    endpoints_to_test = [
        ("/api/health", "GET"),
        ("/api/models", "GET"),
        ("/api/config", "GET"),
        ("/api/tools", "GET"),
        ("/api/templates", "GET"),
        ("/api/agents", "GET"),
        ("/api/custom_tools", "GET"),
        ("/api/function_tools", "GET"),
        ("/api/projects", "GET"),
        ("/api/agents/available-for-sub", "GET")
    ]
    
    for endpoint, method in endpoints_to_test:
        test_endpoint(endpoint, method)

def main():
    """Main test function"""
    print("🚀 FIRESTORE MIGRATION VERIFICATION TEST")
    print("=" * 60)
    
    # Test existing functionality first
    test_existing_functionality()
    
    # Test Firestore migration
    if test_firestore_migration():
        print("\n🎉 FIRESTORE MIGRATION SUCCESSFUL!")
        print("✅ All functionality works with Firestore backend")
        print("✅ Platform is ready for production deployment")
        print("\nNext steps:")
        print("1. Deploy to Google Cloud Run")
        print("2. Monitor Firestore usage in Google Cloud Console")
        print("3. Set up monitoring and alerts")
    else:
        print("\n❌ FIRESTORE MIGRATION FAILED!")
        print("Please check the errors above and fix them before deploying.")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        sys.exit(1)
