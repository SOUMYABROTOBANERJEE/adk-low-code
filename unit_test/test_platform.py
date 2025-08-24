#!/usr/bin/env python3
"""
Test script for ADK Low-Code Platform - Projects & Sub-Agents
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8083"

def test_endpoint(endpoint, method="GET", data=None):
    """Test a single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        print(f"🔍 Testing {method} {endpoint}")
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Success: {json.dumps(result, indent=2)[:200]}...")
                return result
            except Exception as e:
                print(f"   ⚠️  Response parsing error: {e}")
                print(f"   Raw response: {response.text[:200]}...")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ Timeout")
    except requests.exceptions.ConnectionError:
        print(f"   🔌 Connection failed")
    except Exception as e:
        print(f"   💥 Error: {e}")
    
    return None

def test_projects():
    """Test projects functionality"""
    print("\n🏗️  TESTING PROJECTS FUNCTIONALITY")
    print("=" * 50)
    
    # Test projects endpoint
    projects = test_endpoint("/api/projects")
    
    # Test project creation (if endpoint exists)
    test_endpoint("/api/projects", "POST", {
        "name": "test_project",
        "description": "Test project for sub-agents"
    })

def test_sub_agents():
    """Test sub-agents functionality"""
    print("\n🤖 TESTING SUB-AGENTS FUNCTIONALITY")
    print("=" * 50)
    
    # Test creating a multi-agent system
    multi_agent_config = {
        "name": "test_multi_agent",
        "model": "gemini-2.0-pro-001",
        "provider": "google",
        "instruction": "You are a coordinator for multiple specialized agents.",
        "description": "A test multi-agent system",
        "flow": "sequential",
        "generate_api": True,
        "sub_agents": [
            {
                "name": "researcher",
                "model": "gemini-2.0-flash-001",
                "instruction": "You are a research agent. Find information using search tools.",
                "description": "Researches information",
                "tools": ["google_search", "load_web_page"]
            },
            {
                "name": "coder",
                "model": "gemini-2.0-pro-001",
                "instruction": "You are a coding agent. Write and execute code to solve problems.",
                "description": "Writes and executes code",
                "tools": ["built_in_code_execution"]
            }
        ]
    }
    
    print("🔧 Creating multi-agent system...")
    result = test_endpoint("/api/agents", "POST", multi_agent_config)
    
    if result:
        print("✅ Multi-agent created successfully!")
        
        # Test the created agent
        agent_id = multi_agent_config["name"]
        test_endpoint(f"/api/agents/{agent_id}")
        test_endpoint(f"/api/agents/{agent_id}/status")
        
        # Test chat with the multi-agent
        test_endpoint(f"/api/chat/{agent_id}", "POST", {
            "message": "Hello! Can you help me research Python and then write some code?",
            "agent_id": agent_id
        })
    else:
        print("❌ Failed to create multi-agent")

def test_core_functionality():
    """Test core platform functionality"""
    print("\n🔧 TESTING CORE FUNCTIONALITY")
    print("=" * 50)
    
    # Test health
    test_endpoint("/api/health")
    
    # Test agents
    test_endpoint("/api/agents")
    
    # Test tools
    test_endpoint("/api/tools")
    
    # Test templates
    test_endpoint("/api/templates")
    
    # Test models
    test_endpoint("/api/models")
    
    # Test config
    test_endpoint("/api/config")

def main():
    """Main test function"""
    print("🚀 ADK LOW-CODE PLATFORM - COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Test core functionality first
    test_core_functionality()
    
    # Test projects
    test_projects()
    
    # Test sub-agents
    test_sub_agents()
    
    print("\n🎯 TESTING COMPLETE!")
    print("Check the results above to see what's working and what needs fixing.")

if __name__ == "__main__":
    main()
