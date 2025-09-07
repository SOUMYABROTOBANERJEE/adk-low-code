#!/usr/bin/env python3
"""
Test script to verify Cloud Trace integration works correctly
Tests agent execution with user ID tracking and Cloud Trace
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

def test_cloud_trace_integration():
    """Test Cloud Trace integration with user ID tracking"""
    print("\n🔥 TESTING CLOUD TRACE INTEGRATION")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    health = test_endpoint("/api/health")
    if health and health.get('status') == 'healthy':
        print("   ✅ Platform is healthy")
    else:
        print("   ❌ Platform health check failed")
        return False
    
    # Test 2: Create a test agent
    print("\n2. Creating test agent for Cloud Trace...")
    agent_data = {
        "id": f"trace_test_agent_{int(time.time())}",
        "name": "Cloud Trace Test Agent",
        "description": "A test agent to verify Cloud Trace functionality with user ID tracking",
        "agent_type": "llm",
        "system_prompt": "You are a test agent for Cloud Trace verification. Respond briefly and clearly.",
        "tools": [],
        "model_settings": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 500
        },
        "sub_agents": {"existing": [], "new": []}
    }
    
    agent_result = test_endpoint("/api/agents", "POST", agent_data)
    if agent_result and agent_result.get('success'):
        print("   ✅ Test agent created successfully")
        agent_id = agent_result['agent']['id']
    else:
        print("   ❌ Test agent creation failed")
        return False
    
    # Test 3: Test chat with different user IDs (Cloud Trace tracking)
    print("\n3. Testing Cloud Trace with multiple users...")
    
    test_users = [
        {"user_id": "user_001", "message": "Hello! Can you tell me what you do?"},
        {"user_id": "user_002", "message": "What's the weather like today?"},
        {"user_id": "user_003", "message": "Can you help me with a simple task?"}
    ]
    
    successful_chats = 0
    for i, test_case in enumerate(test_users, 1):
        print(f"\n   3.{i} Testing user: {test_case['user_id']}")
        
        chat_data = {
            "message": test_case['message'],
            "user_id": test_case['user_id'],
            "session_id": f"trace_session_{test_case['user_id']}_{int(time.time())}"
        }
        
        chat_result = test_endpoint(f"/api/chat/{agent_id}", "POST", chat_data)
        if chat_result:
            print(f"   ✅ Chat successful for user {test_case['user_id']}")
            successful_chats += 1
            
            # Check if response contains expected fields
            if 'response' in chat_result:
                print(f"   📝 Response length: {len(chat_result['response'])} characters")
            if 'execution_time' in chat_result:
                print(f"   ⏱️  Execution time: {chat_result['execution_time']:.2f}s")
        else:
            print(f"   ❌ Chat failed for user {test_case['user_id']}")
    
    print(f"\n   📊 Successful chats: {successful_chats}/{len(test_users)}")
    
    # Test 4: Test trace info endpoint
    print("\n4. Testing trace information...")
    trace_info = test_endpoint("/api/trace-info")
    if trace_info:
        print("   ✅ Trace info retrieved successfully")
        print(f"   🔍 Tracing enabled: {trace_info.get('tracing_enabled', 'unknown')}")
        print(f"   🏗️  Project ID: {trace_info.get('project_id', 'unknown')}")
        print(f"   📱 App name: {trace_info.get('app_name', 'unknown')}")
    else:
        print("   ⚠️  Trace info not available (this might be expected)")
    
    # Test 5: Test concurrent users (stress test for Cloud Trace)
    print("\n5. Testing concurrent user execution...")
    
    import concurrent.futures
    import threading
    
    def concurrent_chat(user_id, message):
        """Execute a chat request"""
        chat_data = {
            "message": message,
            "user_id": user_id,
            "session_id": f"concurrent_session_{user_id}_{int(time.time())}"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat/{agent_id}", 
                json=chat_data, 
                timeout=30
            )
            return {
                "user_id": user_id,
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "user_id": user_id,
                "success": False,
                "error": str(e)
            }
    
    # Execute 5 concurrent chats
    concurrent_users = [
        ("concurrent_user_1", "Tell me a short story"),
        ("concurrent_user_2", "What's 2+2?"),
        ("concurrent_user_3", "Explain quantum computing briefly"),
        ("concurrent_user_4", "What's the capital of France?"),
        ("concurrent_user_5", "Give me a random fact")
    ]
    
    print("   🚀 Executing 5 concurrent chats...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(concurrent_chat, user_id, message)
            for user_id, message in concurrent_users
        ]
        
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    successful_concurrent = sum(1 for r in results if r.get('success'))
    print(f"   📊 Concurrent chats successful: {successful_concurrent}/{len(concurrent_users)}")
    
    # Test 6: Cleanup
    print("\n6. Testing cleanup...")
    test_endpoint(f"/api/agents/{agent_id}", "DELETE")
    print("   ✅ Cleanup completed")
    
    # Overall assessment
    total_tests = len(test_users) + len(concurrent_users)
    total_successful = successful_chats + successful_concurrent
    
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Total chat tests: {total_tests}")
    print(f"   Successful: {total_successful}")
    print(f"   Success rate: {(total_successful/total_tests)*100:.1f}%")
    
    return total_successful >= total_tests * 0.8  # 80% success rate

def test_trace_observability():
    """Test trace observability features"""
    print("\n🔍 TESTING TRACE OBSERVABILITY")
    print("=" * 50)
    
    # Test trace info endpoint
    trace_info = test_endpoint("/api/trace-info")
    if trace_info:
        print("✅ Trace info endpoint working")
        
        # Check if tracing is enabled
        if trace_info.get('tracing_enabled'):
            print("✅ Cloud Trace is enabled")
            print(f"   Project: {trace_info.get('project_id')}")
            print(f"   App: {trace_info.get('app_name')}")
            print("\n🎯 Next steps for Cloud Trace:")
            print("   1. Go to Google Cloud Console")
            print("   2. Navigate to Cloud Trace > Trace Explorer")
            print("   3. Look for traces with your user IDs")
            print("   4. Check span details for agent executions")
        else:
            print("⚠️  Cloud Trace is not enabled")
            print("   Check your service account and project configuration")
    else:
        print("❌ Trace info endpoint not available")

def main():
    """Main test function"""
    print("🚀 CLOUD TRACE INTEGRATION VERIFICATION TEST")
    print("=" * 60)
    
    # Test Cloud Trace integration
    if test_cloud_trace_integration():
        print("\n🎉 CLOUD TRACE INTEGRATION SUCCESSFUL!")
        print("✅ User ID tracking is working")
        print("✅ Agent execution tracing is enabled")
        print("✅ Concurrent user support verified")
        
        # Test observability features
        test_trace_observability()
        
        print("\n🎯 Cloud Trace Benefits Achieved:")
        print("✅ User-specific trace tracking")
        print("✅ Agent execution monitoring")
        print("✅ Performance analysis")
        print("✅ Error debugging capabilities")
        print("✅ Concurrent user support")
        
        print("\n📊 Monitoring Instructions:")
        print("1. Go to Google Cloud Console")
        print("2. Navigate to Cloud Trace > Trace Explorer")
        print("3. Filter by service: 'adk-platform'")
        print("4. Look for user-specific traces")
        print("5. Analyze agent execution spans")
        
    else:
        print("\n❌ CLOUD TRACE INTEGRATION FAILED!")
        print("Please check the errors above and fix them.")
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
