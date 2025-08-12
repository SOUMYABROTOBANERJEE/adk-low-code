"""
Google ADK Integration Module

This module provides proper integration with Google ADK for creating and running
agents with tools using the LlmAgent and Runner classes.
"""

import os
import sys
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Try to import Google ADK components
try:
    from google.adk.agents import LlmAgent
    from google.adk.runner import Runner
    from google.adk.tools import FunctionTool
    from google.adk.session import InMemorySessionService
    from google.adk.types import Content, Part
    from google.genai.types import GenerateContentConfig
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    # Create placeholder classes for when ADK is not available
    LlmAgent = None
    Runner = None
    FunctionTool = None
    InMemorySessionService = None
    Content = None
    Part = None
    GenerateContentConfig = None
    logging.warning("Google ADK not available. Install with: pip install google-adk")

# Try to import Google GenAI for content generation
try:
    from google.genai import types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    logging.warning("Google GenAI not available. Install with: pip install google-genai")

logger = logging.getLogger(__name__)

class GoogleADKAgentConfig:
    """Configuration for Google ADK agents."""
    
    def __init__(
        self,
        name: str,
        model: str,
        instruction: str,
        description: Optional[str] = None,
        tools: Optional[List[str]] = None,
        temperature: Optional[float] = 0.2,
        api_key: Optional[str] = None
    ):
        self.name = name
        self.model = model
        self.instruction = instruction
        self.description = description or ""
        self.tools = tools or []
        self.temperature = temperature
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')

class GoogleADKIntegration:
    """Main integration class for Google ADK."""
    
    def __init__(self):
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError("Google ADK is not available. Please install it first.")
        
        self.session_service = InMemorySessionService()
        self.agents: Dict[str, LlmAgent] = {}
        self.runners: Dict[str, Runner] = {}
        
    def create_agent(self, config: GoogleADKAgentConfig) -> LlmAgent:
        """Create a Google ADK agent with the specified configuration."""
        try:
            # Create tools list
            tools = []
            if config.tools:
                for tool_id in config.tools:
                    tool = self._create_tool(tool_id)
                    if tool:
                        tools.append(tool)
            
            # Create generate content config
            generate_config = None
            if config.temperature is not None and GOOGLE_GENAI_AVAILABLE:
                generate_config = types.GenerateContentConfig(
                    temperature=config.temperature
                )
            
            # Create the agent
            agent = LlmAgent(
                model=config.model,
                name=config.name,
                description=config.description,
                instruction=config.instruction,
                tools=tools,
                generate_content_config=generate_config
            )
            
            # Store the agent
            self.agents[config.name] = agent
            
            # Create a runner for this agent
            runner = Runner(
                agent=agent,
                app_name="adk-nocode",
                user_id="default_user",
                session_service=self.session_service
            )
            self.runners[config.name] = runner
            
            logger.info(f"Created Google ADK agent: {config.name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {config.name}: {e}")
            raise
    
    def _create_tool(self, tool_id: str) -> Optional[Any]:
        """Create a tool based on the tool ID."""
        if not GOOGLE_ADK_AVAILABLE or FunctionTool is None:
            logger.warning(f"Cannot create tool {tool_id}: Google ADK not available")
            return None
            
        try:
            if tool_id == "google_search":
                return self._create_google_search_tool()
            elif tool_id == "load_web_page":
                return self._create_web_page_tool()
            elif tool_id == "built_in_code_execution":
                return self._create_code_execution_tool()
            elif tool_id == "get_user_choice":
                return self._create_user_choice_tool()
            elif tool_id == "calculator":
                return self._create_calculator_tool()
            elif tool_id == "text_processor":
                return self._create_text_processor_tool()
            else:
                # Try to load custom tool
                return self._load_custom_tool(tool_id)
        except Exception as e:
            logger.error(f"Failed to create tool {tool_id}: {e}")
            return None
    
    def _create_google_search_tool(self) -> Optional[Any]:
        """Create a Google Search tool."""
        def google_search(query: str) -> Dict[str, str]:
            """Search the web using Google Search.
            
            Args:
                query: The search query
                
            Returns:
                Search results as a dictionary
            """
            # This is a placeholder - in a real implementation, you'd use
            # Google Custom Search API or similar
            return {
                "query": query,
                "results": [
                    f"Search result for: {query}",
                    "This is a placeholder result. Configure Google Search API for real results."
                ],
                "source": "google_search_tool"
            }
        
        if FunctionTool is not None:
            return FunctionTool.create(google_search)
        else:
            logger.warning("FunctionTool not available")
            return None
    
    def _create_web_page_tool(self) -> Optional[Any]:
        """Create a web page loading tool."""
        def load_web_page(url: str) -> Dict[str, str]:
            """Load and extract content from a web page.
            
            Args:
                url: The URL to load
                
            Returns:
                Page content as a dictionary
            """
            try:
                import requests
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # Extract text content (basic implementation)
                content = response.text[:1000] + "..." if len(response.text) > 1000 else response.text
                
                return {
                    "url": url,
                    "status": response.status_code,
                    "content": content,
                    "source": "web_page_tool"
                }
            except Exception as e:
                return {
                    "url": url,
                    "error": str(e),
                    "source": "web_page_tool"
                }
        
        if FunctionTool is not None:
            return FunctionTool.create(load_web_page)
        else:
            logger.warning("FunctionTool not available")
            return None
    
    def _create_code_execution_tool(self) -> Optional[Any]:
        """Create a code execution tool."""
        def execute_code(code: str, language: str = "python") -> Dict[str, str]:
            """Execute code in the specified language.
            
            Args:
                code: The code to execute
                language: The programming language (default: python)
                
            Returns:
                Execution result as a dictionary
            """
            if language.lower() != "python":
                return {
                    "error": f"Language {language} not supported yet",
                    "source": "code_execution_tool"
                }
            
            try:
                # Create a safe execution environment
                local_vars = {}
                exec(code, {"__builtins__": {}}, local_vars)
                
                return {
                    "code": code,
                    "language": language,
                    "result": str(local_vars.get('result', 'Code executed successfully')),
                    "source": "code_execution_tool"
                }
            except Exception as e:
                return {
                    "code": code,
                    "language": language,
                    "error": str(e),
                    "source": "code_execution_tool"
                }
        
        if FunctionTool is not None:
            return FunctionTool.create(execute_code)
        else:
            logger.warning("FunctionTool not available")
            return None
    
    def _create_user_choice_tool(self) -> Optional[Any]:
        """Create a user choice tool."""
        def get_user_choice(question: str, options: List[str]) -> Dict[str, str]:
            """Ask the user to make a choice.
            
            Args:
                question: The question to ask
                options: List of available options
                
            Returns:
                User's choice as a dictionary
            """
            # In a real implementation, this would interact with the UI
            # For now, return a placeholder
            return {
                "question": question,
                "options": options,
                "user_choice": "User choice placeholder - implement UI interaction",
                "source": "user_choice_tool"
            }
        
        if FunctionTool is not None:
            return FunctionTool.create(get_user_choice)
        else:
            logger.warning("FunctionTool not available")
            return None
    
    def _create_calculator_tool(self) -> Optional[Any]:
        """Create a calculator tool."""
        def calculator(operation: str, a: float, b: float) -> Dict[str, Any]:
            """Perform basic arithmetic operations.
            
            Args:
                operation: The operation to perform ('add', 'subtract', 'multiply', 'divide')
                a: First number
                b: Second number
                
            Returns:
                Calculation result as a dictionary
            """
            try:
                if operation == 'add':
                    result = a + b
                elif operation == 'subtract':
                    result = a - b
                elif operation == 'multiply':
                    result = a * b
                elif operation == 'divide':
                    if b == 0:
                        raise ValueError("Cannot divide by zero")
                    result = a / b
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                return {
                    "operation": operation,
                    "a": a,
                    "b": b,
                    "result": result,
                    "source": "calculator_tool"
                }
            except Exception as e:
                return {
                    "operation": operation,
                    "a": a,
                    "b": b,
                    "error": str(e),
                    "source": "calculator_tool"
                }
        
        if FunctionTool is not None:
            return FunctionTool.create(calculator)
        else:
            logger.warning("FunctionTool not available")
            return None
    
    def _create_text_processor_tool(self) -> Optional[Any]:
        """Create a text processing tool."""
        def text_processor(text: str, operation: str) -> Dict[str, str]:
            """Process text using various operations.
            
            Args:
                text: Input text to process
                operation: The operation to perform ('uppercase', 'lowercase', 'count_words', 'reverse')
                
            Returns:
                Processed text or analysis result as a dictionary
            """
            try:
                if operation == 'uppercase':
                    result = text.upper()
                elif operation == 'lowercase':
                    result = text.lower()
                elif operation == 'count_words':
                    result = str(len(text.split()))
                elif operation == 'reverse':
                    result = text[::-1]
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                return {
                    "text": text,
                    "operation": operation,
                    "result": result,
                    "source": "text_processor_tool"
                }
            except Exception as e:
                return {
                    "text": text,
                    "operation": operation,
                    "error": str(e),
                    "source": "text_processor_tool"
                }
        
        if FunctionTool is not None:
            return FunctionTool.create(text_processor)
        else:
            logger.warning("FunctionTool not available")
            return None
    
    def _load_custom_tool(self, tool_id: str) -> Optional[Any]:
        """Load a custom tool from the custom_tools directory."""
        try:
            # Add custom_tools to Python path
            custom_tools_dir = Path(__file__).parent / "custom_tools"
            if custom_tools_dir.exists():
                sys.path.insert(0, str(custom_tools_dir))
                
                # Try to import the tool module
                tool_module = __import__(tool_id)
                if hasattr(tool_module, tool_id):
                    tool_function = getattr(tool_module, tool_id)
                    if FunctionTool is not None:
                        return FunctionTool.create(tool_function)
                    else:
                        logger.warning("FunctionTool not available")
                        return None
                else:
                    logger.warning(f"Tool function {tool_id} not found in module {tool_id}")
                    return None
            else:
                logger.warning(f"Custom tools directory not found: {custom_tools_dir}")
                return None
        except Exception as e:
            logger.error(f"Failed to load custom tool {tool_id}: {e}")
            return None
    
    async def run_agent(self, agent_name: str, user_input: str, session_id: str = None) -> str:
        """Run an agent with user input and return the response."""
        try:
            if agent_name not in self.runners:
                raise ValueError(f"Agent '{agent_name}' not found")
            
            runner = self.runners[agent_name]
            
            # Create or get session
            if not session_id:
                session_id = f"session_{agent_name}_{hash(user_input) % 10000}"
            
            # Create content from user input
            content = Content.from_parts(Part.from_text(user_input))
            
            # Run the agent
            events = runner.run_async("default_user", session_id, content)
            
            # Collect the response
            response_text = ""
            async for event in events:
                if hasattr(event, 'final_response') and event.final_response:
                    if hasattr(event, 'content') and event.content:
                        for part in event.content.parts:
                            if hasattr(part, 'text'):
                                response_text += part.text
            
            return response_text if response_text else "No response generated"
            
        except Exception as e:
            logger.error(f"Failed to run agent {agent_name}: {e}")
            return f"Error running agent: {str(e)}"
    
    def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get the status of an agent."""
        if agent_name not in self.agents:
            return {"status": "not_found"}
        
        agent = self.agents[agent_name]
        return {
            "status": "ready",
            "name": agent.name,
            "model": agent.model,
            "description": agent.description,
            "tools_count": len(agent.tools) if hasattr(agent, 'tools') else 0
        }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents."""
        return [
            {
                "name": name,
                "status": self.get_agent_status(name)
            }
            for name in self.agents.keys()
        ]

# Global instance
google_adk_integration = None

def get_google_adk_integration() -> GoogleADKIntegration:
    """Get or create the global Google ADK integration instance."""
    global google_adk_integration
    if google_adk_integration is None:
        if GOOGLE_ADK_AVAILABLE:
            google_adk_integration = GoogleADKIntegration()
        else:
            raise ImportError("Google ADK is not available")
    return google_adk_integration

def is_google_adk_available() -> bool:
    """Check if Google ADK is available."""
    return GOOGLE_ADK_AVAILABLE
