#!/usr/bin/env python3
"""
Test script to check if the backend is working after fixes
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8083"

def test_backend():
    """Test the backend endpoints"""
    print("🔍 Testing Backend After Fixes...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ADK Available: {data.get('adk_available', False)}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Available agents for sub-agents
    try:
        response = requests.get(f"{BASE_URL}/api/agents/available-for-sub", timeout=5)
        print(f"✅ Available agents endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Available agents: {len(data.get('available_agents', []))}")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"❌ Available agents endpoint failed: {e}")
    
    # Test 3: List all agents
    try:
        response = requests.get(f"{BASE_URL}/api/agents", timeout=5)
        print(f"✅ Agents list endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total agents: {len(data.get('agents', []))}")
        else:
            print(f"   Error response: {response.text}")
    except Exception as e:
        print(f"❌ Agents list endpoint failed: {e}")
    
    print("✅ Backend test completed")
    return True

if __name__ == "__main__":
    test_backend()

