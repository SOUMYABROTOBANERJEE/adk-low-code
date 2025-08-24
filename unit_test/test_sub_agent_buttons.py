#!/usr/bin/env python3
"""
Test script to verify sub-agent button functionality and backend endpoints
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8083"

def test_backend_endpoints():
    """Test the backend endpoints for sub-agent functionality"""
    print("🔍 Testing Backend Endpoints...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Check available agents for sub-agents
    try:
        response = requests.get(f"{BASE_URL}/api/agents/available-for-sub", timeout=5)
        print(f"✅ Available agents endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Available agents: {len(data.get('available_agents', []))}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Available agents endpoint failed: {e}")
    
    # Test 3: Check if there are any agents
    try:
        response = requests.get(f"{BASE_URL}/api/agents", timeout=5)
        print(f"✅ Agents list endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total agents: {len(data.get('agents', []))}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Agents list endpoint failed: {e}")
    
    return True

def test_frontend_integration():
    """Test the frontend integration by checking if buttons exist"""
    print("\n🔍 Testing Frontend Integration...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        print("🌐 Starting browser...")
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Navigate to the page
            driver.get(f"{BASE_URL}")
            print(f"✅ Page loaded: {driver.title}")
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if the page has loaded
            if "Agent Genie" in driver.title or "ADK" in driver.title:
                print("✅ Page title indicates correct application")
            else:
                print(f"⚠️  Unexpected page title: {driver.title}")
            
            # Try to find the create agent button
            try:
                create_agent_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "createAgentBtn"))
                )
                print("✅ Create Agent button found")
                
                # Click it to open the modal
                create_agent_btn.click()
                print("✅ Create Agent button clicked")
                
                # Wait for modal to appear
                time.sleep(2)
                
                # Check if modal is visible
                modal = driver.find_element(By.ID, "agentModal")
                if "hidden" not in modal.get_attribute("class"):
                    print("✅ Agent modal is visible")
                else:
                    print("❌ Agent modal is hidden")
                
                # Look for sub-agent buttons
                try:
                    add_existing_btn = driver.find_element(By.ID, "addExistingAsSubInAgentBtn")
                    print("✅ Add Existing Sub-Agent button found")
                    print(f"   Button text: {add_existing_btn.text}")
                    print(f"   Button visible: {add_existing_btn.is_displayed()}")
                except Exception as e:
                    print(f"❌ Add Existing Sub-Agent button not found: {e}")
                
                try:
                    add_new_btn = driver.find_element(By.ID, "addNewSubAgentInAgentBtn")
                    print("✅ Add New Sub-Agent button found")
                    print(f"   Button text: {add_new_btn.text}")
                    print(f"   Button visible: {add_new_btn.is_displayed()}")
                except Exception as e:
                    print(f"❌ Add New Sub-Agent button not found: {e}")
                
                # Check for sub-agent containers
                try:
                    existing_container = driver.find_element(By.ID, "existingSubAgentsSelection")
                    print("✅ Existing Sub-Agents container found")
                except Exception as e:
                    print(f"❌ Existing Sub-Agents container not found: {e}")
                
                try:
                    new_container = driver.find_element(By.ID, "newSubAgentsContainer")
                    print("✅ New Sub-Agents container found")
                except Exception as e:
                    print(f"❌ New Sub-Agents container not found: {e}")
                
            except Exception as e:
                print(f"❌ Could not interact with Create Agent button: {e}")
            
        finally:
            driver.quit()
            print("🌐 Browser closed")
            
    except ImportError:
        print("⚠️  Selenium not available, skipping frontend tests")
        print("   Install with: pip install selenium")
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")

def main():
    """Main test function"""
    print("🚀 Testing Sub-Agent Button Functionality")
    print("=" * 50)
    
    # Test backend first
    if test_backend_endpoints():
        # Test frontend if backend is working
        test_frontend_integration()
    
    print("\n" + "=" * 50)
    print("🏁 Testing Complete!")

if __name__ == "__main__":
    main()

