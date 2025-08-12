#!/usr/bin/env python3
"""
Test script for the Google ADK No-Code Platform
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.google.adk1.nocode.models import (
    AgentConfiguration, ToolDefinition, AgentType, ToolType
)
from src.google.adk1.nocode.adk_service import ADKService


async def test_platform():
    """Test the basic functionality of the platform"""
    print("🧪 Testing Google ADK No-Code Platform...")
    
    # Initialize the ADK service
    adk_service = ADKService()
    
    print(f"✅ ADK Service initialized")
    print(f"📊 ADK Available: {adk_service.is_available()}")
    
    # Create a sample tool
    sample_tool = ToolDefinition(
        id="test_calculator",
        name="Test Calculator",
        description="A simple calculator for testing",
        tool_type=ToolType.FUNCTION,
        function_code="""
def execute(expression: str) -> str:
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
""",
        tags=["test", "calculator"]
    )
    
    print(f"🔧 Created sample tool: {sample_tool.name}")
    
    # Register the tool
    if adk_service.register_tool(sample_tool):
        print("✅ Tool registered successfully")
    else:
        print("❌ Failed to register tool")
        return
    
    # Create a sample agent
    sample_agent = AgentConfiguration(
        id="test_agent",
        name="Test Math Agent",
        description="A test agent for mathematical operations",
        agent_type=AgentType.LLM,
        system_prompt="You are a helpful math assistant. Use the calculator tool to perform calculations.",
        tools=["test_calculator"],
        tags=["test", "math"]
    )
    
    print(f"🤖 Created sample agent: {sample_agent.name}")
    
    # Register the agent
    if adk_service.register_agent(sample_agent):
        print("✅ Agent registered successfully")
    else:
        print("❌ Failed to register agent")
        return
    
    # Test agent execution
    print("🧮 Testing agent execution...")
    result = await adk_service.execute_agent("test_agent", "What is 2 + 2?")
    
    if result.success:
        print(f"✅ Agent executed successfully")
        print(f"📝 Response: {result.response}")
        print(f"⏱️ Execution time: {result.execution_time:.2f}s")
    else:
        print(f"❌ Agent execution failed: {result.error}")
    
    # Test code generation
    print("📝 Testing code generation...")
    try:
        from src.google.adk1.nocode.main import generate_agent_code
        # This would test the code generation endpoint
        print("✅ Code generation endpoint available")
    except ImportError:
        print("⚠️ Code generation not available in test mode")
    
    print("\n🎉 Platform test completed!")
    print("🚀 You can now run the platform with: python app.py")


if __name__ == "__main__":
    asyncio.run(test_platform())
