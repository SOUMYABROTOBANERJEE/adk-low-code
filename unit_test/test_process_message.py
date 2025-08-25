#!/usr/bin/env python3
"""
Test script for process_message method
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google2.adk1.nocode.adk_service import ADKService

async def test_process_message():
    """Test the process_message method"""
    
    print("🧪 Testing process_message method...")
    
    # Create ADK service instance
    adk_service = ADKService()
    
    # Test agent data
    test_agent = {
        'name': 'Test Agent',
        'agent_type': 'llm',
        'system_prompt': 'You are a helpful AI assistant.'
    }
    
    test_message = "Hello, how are you?"
    
    print(f"Agent: {test_agent}")
    print(f"Message: {test_message}")
    print(f"GenAI Available: {adk_service.is_genai_available()}")
    
    try:
        # Test the process_message method
        response = await adk_service.process_message(test_agent, test_message)
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_process_message())
