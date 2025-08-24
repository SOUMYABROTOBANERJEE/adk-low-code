#!/usr/bin/env python3
"""
Simple test script to check if sub-agent buttons are working
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8083"

def test_backend():
    """Test the backend endpoints"""
    print("🔍 Testing Backend Endpoints...")
    
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
            print(f"   Response: {response.text}")
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
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Agents list endpoint failed: {e}")
    
    return True

def test_frontend_buttons():
    """Test if the frontend buttons exist and are accessible"""
    print("\n🔍 Testing Frontend Button Accessibility...")
    
    try:
        # Test if the main page loads
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"✅ Main page: {response.status_code}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check if the buttons exist in the HTML
            if 'addExistingAsSubInAgentBtn' in html_content:
                print("✅ Add Existing button found in HTML")
            else:
                print("❌ Add Existing button NOT found in HTML")
            
            if 'addNewSubAgentInAgentBtn' in html_content:
                print("✅ Add New button found in HTML")
            else:
                print("❌ Add New button NOT found in HTML")
            
            if 'selectExistingAgentModal' in html_content:
                print("✅ Select Existing Modal found in HTML")
            else:
                print("❌ Select Existing Modal NOT found in HTML")
            
            if 'existingSubAgentsSelection' in html_content:
                print("✅ Existing Sub-Agents container found in HTML")
            else:
                print("❌ Existing Sub-Agents container NOT found in HTML")
            
            if 'newSubAgentsContainer' in html_content:
                print("✅ New Sub-Agents container found in HTML")
            else:
                print("❌ New Sub-Agents container NOT found in HTML")
            
        else:
            print(f"❌ Main page failed to load: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")

def main():
    """Main test function"""
    print("🚀 Testing Sub-Agent Button Functionality")
    print("=" * 50)
    
    # Test backend first
    if test_backend():
        # Test frontend
        test_frontend_buttons()
    
    print("\n" + "=" * 50)
    print("🏁 Testing Complete!")
    print("\n💡 If buttons are not working, check:")
    print("   1. Browser console for JavaScript errors")
    print("   2. Network tab for failed API calls")
    print("   3. Elements tab to see if buttons exist in DOM")

if __name__ == "__main__":
    main()

