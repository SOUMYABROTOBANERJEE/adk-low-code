#!/usr/bin/env python3
"""
Test script to verify sub-agent functionality
"""

import os
import sys
import asyncio
import logging
from typing import Dict, Any

# Add the src path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'google2', 'adk1', 'nocode'))

# Change to the nocode directory to avoid relative import issues
os.chdir(os.path.join(os.path.dirname(__file__), 'src', 'google2', 'adk1', 'nocode'))

from adk_service import ADKService
from firestore_manager import FirestoreManager
from models import AgentConfiguration, AgentType, SubAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_sub_agent_functionality():
    """Test that sub-agents are properly integrated and functional"""
    
    print("\n" + "=" * 60)
    print("🧪 TESTING SUB-AGENT FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Initialize services
        print("🔧 Initializing services...")
        db_manager = FirestoreManager()
        adk_service = ADKService(db_manager)
        
        print("✅ Services initialized")
        
        # Create a simple sub-agent first
        print("\n📝 Creating test sub-agent...")
        sub_agent_config = AgentConfiguration(
            id="test_sub_agent_001",
            name="Test Sub-Agent",
            description="A simple test sub-agent",
            agent_type=AgentType.LLM,
            system_prompt="You are a helpful assistant that specializes in math calculations.",
            instructions="Always show your work step by step.",
            tools=[],
            model_provider="google",
            model_settings={"model": "gemini-1.5-flash"}
        )
        
        # Save sub-agent to database
        sub_agent_data = sub_agent_config.model_dump()
        if db_manager.save_agent(sub_agent_data):
            print("✅ Sub-agent saved to database")
        else:
            print("❌ Failed to save sub-agent")
            return
        
        # Create a parent agent with the sub-agent
        print("\n📝 Creating parent agent with sub-agent...")
        parent_agent_config = AgentConfiguration(
            id="test_parent_agent_001",
            name="Test Parent Agent",
            description="A parent agent that uses sub-agents",
            agent_type=AgentType.LLM,
            system_prompt="You are a coordinator agent. When you need math help, delegate to your sub-agent.",
            instructions="Use your sub-agent for mathematical calculations.",
            tools=[],
            sub_agents=[
                SubAgent(
                    id="test_sub_agent_001",
                    name="Test Sub-Agent",
                    agent_type=AgentType.LLM,
                    system_prompt="You are a helpful assistant that specializes in math calculations.",
                    instructions="Always show your work step by step.",
                    tools=[],
                    model_settings={"model": "gemini-1.5-flash"}
                )
            ],
            model_provider="google",
            model_settings={"model": "gemini-1.5-flash"}
        )
        
        # Create the parent agent (this should now include sub-agent tools)
        print("🔧 Creating parent agent with sub-agent integration...")
        parent_agent = await adk_service.create_agent(parent_agent_config)
        
        if parent_agent:
            print("✅ Parent agent created successfully")
            
            # Check if sub-agent tools were added
            print(f"📊 Parent agent tools count: {len(parent_agent.tools) if hasattr(parent_agent, 'tools') else 'No tools attribute'}")
            
            if hasattr(parent_agent, 'tools') and parent_agent.tools:
                print("🔍 Available tools:")
                for i, tool in enumerate(parent_agent.tools):
                    tool_name = getattr(tool, 'name', f'Tool_{i}')
                    tool_desc = getattr(tool, 'description', 'No description')
                    print(f"  {i+1}. {tool_name}: {tool_desc}")
            
            # Test execution
            print("\n🚀 Testing agent execution...")
            test_prompt = "What is 15 + 27? Please use your sub-agent for the calculation."
            
            result = await adk_service.execute_agent(
                agent_id="test_parent_agent_001",
                prompt=test_prompt,
                session_id="test_session",
                user_id="test_user"
            )
            
            if result.success:
                print("✅ Agent execution successful!")
                print(f"📝 Response: {result.response}")
            else:
                print(f"❌ Agent execution failed: {result.error}")
        
        else:
            print("❌ Failed to create parent agent")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        db_manager.delete_agent("test_sub_agent_001")
        db_manager.delete_agent("test_parent_agent_001")
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 SUB-AGENT FUNCTIONALITY TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_sub_agent_functionality())
