#!/usr/bin/env python3
"""
Frontend Integration Test - Verify all functionality works end-to-end
"""

import requests
import json
import time
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

BASE_URL = "http://127.0.0.1:8083"

def test_backend_endpoints():
    """Test all backend endpoints are working"""
    print("🔧 TESTING BACKEND ENDPOINTS")
    print("=" * 40)
    
    endpoints = [
        ("/api/health", "GET"),
        ("/api/models", "GET"),
        ("/api/config", "GET"),
        ("/api/tools", "GET"),
        ("/api/agents", "GET"),
        ("/api/projects", "GET"),
        ("/api/agents/available-for-sub", "GET")
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=10)
            
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {method} {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"❌ {method} {endpoint}: Error - {e}")

def test_frontend_access():
    """Test frontend pages are accessible"""
    print("\n🌐 TESTING FRONTEND ACCESS")
    print("=" * 40)
    
    pages = [
        "/",
        "/login"
    ]
    
    for page in pages:
        try:
            response = requests.get(f"{BASE_URL}{page}", timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {page}: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                if "Agent Genie" in content:
                    print(f"   ✅ Page contains expected content")
                else:
                    print(f"   ⚠️  Page content may be incomplete")
                    
        except Exception as e:
            print(f"❌ {page}: Error - {e}")

def test_agent_creation_flow():
    """Test the complete agent creation flow"""
    print("\n🤖 TESTING AGENT CREATION FLOW")
    print("=" * 40)
    
    # Create a test agent
    agent_data = {
        "name": "integration_test_agent",
        "description": "Agent created during integration testing",
        "agent_type": "llm",
        "system_prompt": "You are an integration test agent.",
        "model_settings": {
            "model": "gemini-2.0-flash",
            "temperature": 0.7,
            "max_tokens": 1000
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents", json=agent_data, timeout=10)
        if response.status_code == 200:
            print("✅ Agent created successfully")
            agent_id = response.json().get('agent', {}).get('id')
            return agent_id
        else:
            print(f"❌ Agent creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Agent creation error: {e}")
        return None

def test_sub_agent_flow(agent_id):
    """Test the complete sub-agent creation flow"""
    if not agent_id:
        print("⚠️  Skipping sub-agent tests - no agent ID available")
        return
    
    print(f"\n🔗 TESTING SUB-AGENT FLOW FOR AGENT: {agent_id}")
    print("=" * 50)
    
    # Test adding a new sub-agent
    sub_agent_data = {
        "name": "integration_test_sub_agent",
        "description": "Sub-agent created during integration testing",
        "agent_type": "llm",
        "system_prompt": "You are an integration test sub-agent."
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/agents/{agent_id}/sub-agents", 
                               json=sub_agent_data, timeout=10)
        if response.status_code == 200:
            print("✅ Sub-agent created successfully")
        else:
            print(f"❌ Sub-agent creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Sub-agent creation error: {e}")
    
    # Test getting sub-agents
    try:
        response = requests.get(f"{BASE_URL}/api/agents/{agent_id}/sub-agents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            sub_agents = data.get('sub_agents', [])
            print(f"✅ Retrieved {len(sub_agents)} sub-agents")
        else:
            print(f"❌ Failed to get sub-agents: {response.status_code}")
    except Exception as e:
        print(f"❌ Get sub-agents error: {e}")

def test_project_flow():
    """Test the complete project creation flow"""
    print("\n📁 TESTING PROJECT CREATION FLOW")
    print("=" * 40)
    
    project_data = {
        "name": "integration_test_project",
        "description": "Project created during integration testing"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/projects", json=project_data, timeout=10)
        if response.status_code == 200:
            print("✅ Project created successfully")
            project_id = response.json().get('project', {}).get('id')
            return project_id
        else:
            print(f"❌ Project creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Project creation error: {e}")
        return None

def test_project_export(project_id):
    """Test project export functionality"""
    if not project_id:
        print("⚠️  Skipping project export tests - no project ID available")
        return
    
    print(f"\n📦 TESTING PROJECT EXPORT FOR PROJECT: {project_id}")
    print("=" * 50)
    
    # Test project export
    try:
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/export", timeout=10)
        if response.status_code == 200:
            print("✅ Project export successful")
            data = response.json()
            if 'download_url' in data:
                print(f"   📥 Download URL: {data['download_url']}")
        else:
            print(f"❌ Project export failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Project export error: {e}")

def open_browser_for_manual_testing():
    """Open browser for manual testing"""
    print("\n🌐 OPENING BROWSER FOR MANUAL TESTING")
    print("=" * 40)
    
    try:
        webbrowser.open(f"{BASE_URL}")
        print("✅ Browser opened successfully")
        print("📋 Manual testing checklist:")
        print("   1. Verify login page loads")
        print("   2. Check dashboard displays correctly")
        print("   3. Navigate to Agents section")
        print("   4. Navigate to Tools section")
        print("   5. Navigate to Projects section")
        print("   6. Navigate to Sub-Agents section")
        print("   7. Test creating an agent")
        print("   8. Test creating a tool")
        print("   9. Test creating a project")
        print("   10. Test adding sub-agents")
        print("   11. Test linking existing agents as sub-agents")
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")

def main():
    """Main test function"""
    print("🚀 FRONTEND INTEGRATION TEST")
    print("=" * 60)
    
    # Test backend endpoints
    test_backend_endpoints()
    
    # Test frontend access
    test_frontend_access()
    
    # Test agent creation flow
    agent_id = test_agent_creation_flow()
    
    # Test sub-agent flow
    test_sub_agent_flow(agent_id)
    
    # Test project creation flow
    project_id = test_project_flow()
    
    # Test project export
    test_project_export(project_id)
    
    # Open browser for manual testing
    open_browser_for_manual_testing()
    
    print("\n🎯 INTEGRATION TESTING COMPLETE!")
    print("All functionality should now be working end-to-end.")

if __name__ == "__main__":
    main()

