"""
Core ADK service for creating and executing agents
"""

import asyncio
import time
import uuid
import os
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import importlib.util
import traceback

# Import our models
from .models import ToolDefinition, ToolType, AgentConfiguration

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import Google ADK modules
try:
    # Import ADK modules from the correct submodules
    from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
    from google.adk.tools import FunctionTool
    from google.adk.tools import google_search
    from google.adk.models import Gemini
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    # MCP imports
    from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
    
    ADK_AVAILABLE = True
    print("Google ADK loaded successfully")
    
except ImportError as e:
    ADK_AVAILABLE = False
    print(f"Warning: Google ADK not available. Import error: {e}")
    print("Install with: pip install google-adk")

# LiteLLM imports for multi-model support
try:
    import litellm
    from litellm import completion
    LITELLM_AVAILABLE = True
    print("LiteLLM loaded successfully")
except ImportError as e:
    LITELLM_AVAILABLE = False
    print(f"Warning: LiteLLM not available. Import error: {e}")
    print("Install with: pip install litellm")

# Import Google GenAI for prompt suggestions
try:
    from google import genai
    from google.genai import types as genai_types
    GENAI_AVAILABLE = True
    print("Google GenAI loaded successfully")
except ImportError as e:
    GENAI_AVAILABLE = False
    print(f"Warning: Google GenAI not available. Import error: {e}")
    print("Install with: pip install google-genai")

from .models import (
    AgentConfiguration, ToolDefinition, SubAgent, AgentType, 
    ToolType, AgentExecutionResult, ChatMessage, ModelProvider
)
from .traced_agent_runner import get_traced_runner
from .model_service import ModelService


class ADKService:
    """Service for managing Google ADK agents"""
    
    def __init__(self, db_manager=None):
        # Load environment variables first
        from dotenv import load_dotenv
        load_dotenv('.env')
        
        self.agents: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        self.sessions: Dict[str, List[ChatMessage]] = {}
        self.session_service = InMemorySessionService() if ADK_AVAILABLE else None
        self.app_name = "google_adk_platform"
        self.user_id = "default_user"
        self.db_manager = db_manager
        self.model_service = ModelService()
        
        # Set up service account authentication for all Google services
        if os.path.exists("svcacct.json"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "svcacct.json"
            print("Service account authentication configured")
        else:
            print("Warning: No service account file found. Some features may not work.")
        
        # Initialize traced runner for Cloud Trace integration
        self.traced_runner = None
        if ADK_AVAILABLE:
            try:
                self.traced_runner = get_traced_runner(
                    project_id="tsl-generative-ai",
                    app_name=self.app_name,
                    session_service=self.session_service
                )
                print("Traced agent runner initialized successfully")
            except Exception as e:
                print(f"Failed to initialize traced runner: {e}")
                self.traced_runner = None
        
        # Initialize Google GenAI client for prompt suggestions
        if GENAI_AVAILABLE:
            try:
                # Only use service account authentication
                if os.path.exists("svcacct.json"):
                    # Initialize without API key to use service account
                    self.genai_client = genai.Client()
                    print("Google GenAI client initialized with service account authentication")
                else:
                    print("No service account file found. Google GenAI client not initialized.")
                    self.genai_client = None
            except Exception as exc:
                print(f"Failed to initialize Google GenAI client: {exc}")
                self.genai_client = None
        else:
            self.genai_client = None
        
    def is_available(self) -> bool:
        """Check if Google ADK is available"""
        return ADK_AVAILABLE
    
    def is_genai_available(self) -> bool:
        """Check if Google GenAI is available"""
        return GENAI_AVAILABLE and self.genai_client is not None
    
    def get_builtin_tools(self) -> List[Dict[str, Any]]:
        """Get list of available built-in tools"""
        if not ADK_AVAILABLE:
            return []
        
        builtin_tools = [
            {
                "id": "google_search",
                "name": "Google Search",
                "description": "Search the web using Google Search. Only compatible with Gemini 2 models.",
                "tool_type": "builtin",
                "builtin_name": "google_search",
                "is_enabled": True
            }
        ]
        
        return builtin_tools
    
    async def get_agent_name_suggestion(self, description: str) -> str:
        """Get AI-powered suggestion for agent name based on description"""
        if not self.is_genai_available():
            return "AI suggestions not available"
        
        try:
            prompt = f"""Given this agent description: "{description}"
            
            Generate a concise, professional agent name (2-4 words max) that clearly represents the agent's purpose.
            The name should be:
            - Descriptive and professional
            - Easy to understand
            - Follow naming conventions (e.g., "Data_Processor", "Search_Assistant")
            
            Return only the suggested name, nothing else."""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt
            )
            
            return response.text.strip()
        except Exception as exc:
            print(f"Error getting agent name suggestion: {exc}")
            return "AI suggestions not available"
    
    async def get_agent_description_suggestion(self, name: str, agent_type: str) -> str:
        """Get AI-powered suggestion for agent description based on name and type"""
        if not self.is_genai_available():
            return "AI suggestions not available"
        
        try:
            prompt = f"""Given this agent name: "{name}" and type: "{agent_type}"
            
            Generate a clear, professional description (1-2 sentences) that explains what this agent does.
            The description should be:
            - Clear and concise
            - Professional in tone
            - Explain the agent's main purpose and capabilities
            
            Return only the suggested description, nothing else."""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt
            )
            
            return response.text.strip()
        except Exception as exc:
            print(f"Error getting agent description suggestion: {exc}")
            return "AI suggestions not available"
    
    async def get_agent_system_prompt_suggestion(self, name: str, description: str, agent_type: str) -> str:
        """Get AI-powered suggestion for agent system prompt based on name, description and type"""
        if not self.is_genai_available():
            return "AI suggestions not available"
        
        try:
            prompt = f"""Given this agent:
            Name: "{name}"
            Description: "{description}"
            Type: "{agent_type}"
            
            Generate a professional system prompt that defines the agent's role and behavior.
            The system prompt should:
            - Be clear and professional
            - Define the agent's primary purpose
            - Include appropriate tone and style
            - Be 1-2 sentences long
            
            Return only the suggested system prompt, nothing else."""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt
            )
            
            return response.text.strip()
        except Exception as exc:
            print(f"Error getting agent system prompt suggestion: {exc}")
            return "AI suggestions not available"
    
    async def get_tool_name_suggestion(self, description: str, tool_type: str) -> str:
        """Get AI-powered suggestion for tool name based on description and type"""
        if not self.is_genai_available():
            return "AI suggestions not available"
        
        try:
            prompt = f"""Given this tool:
            Description: "{description}"
            Type: "{tool_type}"
            
            Generate a concise, descriptive tool name (2-4 words max) that clearly represents the tool's function.
            The name should be:
            - Descriptive and professional
            - Easy to understand
            - Follow naming conventions (e.g., "Database_Insert", "Data_Validator")
            
            Return only the suggested name, nothing else."""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt
            )
            
            return response.text.strip()
        except Exception as exc:
            print(f"Error getting tool name suggestion: {exc}")
            return "AI suggestions not available"
    
    async def get_tool_description_suggestion(self, name: str, tool_type: str) -> str:
        """Get AI-powered suggestion for tool description based on name and type"""
        if not self.is_genai_available():
            return "AI suggestions not available"
        
        try:
            prompt = f"""Given this tool:
            Name: "{name}"
            Type: "{tool_type}"
            
            Generate a clear, professional description (1-2 sentences) that explains what this tool does.
            The description should be:
            - Clear and concise
            - Professional in tone
            - Explain the tool's main function and purpose
            
            Return only the suggested description, nothing else."""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt
            )
            
            return response.text.strip()
        except Exception as exc:
            print(f"Error getting tool description suggestion: {exc}")
            return "AI suggestions not available"
    
    async def get_tool_code_suggestion(self, name: str, description: str, tool_type: str) -> str:
        """Get AI-powered suggestion for tool function code based on name, description and type"""
        if not self.is_genai_available():
            return "AI suggestions not available"
        
        try:
            prompt = f"""Given this tool:
            Name: "{name}"
            Description: "{description}"
            Type: "{tool_type}"
            
            Generate Python function code that implements this tool's functionality following Google ADK patterns.
            The code should:
            - Have a clear function signature with appropriate parameters
            - Include proper error handling and validation
            - Return meaningful results
            - Follow Python best practices
            - Include comprehensive docstring explaining the function
            - Handle edge cases appropriately
            - Be compatible with Google ADK function tool requirements
            - Always include tool_context as the last parameter
            
            For function tools, create an 'execute' function that follows this pattern:
            def execute(input_data: str, tool_context) -> str:
                \"\"\"
                [Tool description]
                
                Args:
                    input_data (str): The input data for the tool
                    tool_context: The tool execution context
                    
                Returns:
                    str: The result of the tool execution
                \"\"\"
                try:
                    # Your tool logic here
                    # Process input_data and return result
                    return "Result: [your processed data]"
                except Exception as exc:
                    return f"Error: {{str(exc)}}"
            
            Return only the Python code without any markdown formatting or backticks. Do not include ```python or ``` in your response."""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt
            )
            
            # Clean up the response by removing any markdown backticks
            result = response.text.strip()
            
            # Remove ```python from the beginning
            if result.startswith('```python'):
                result = result[9:].strip()
            elif result.startswith('```'):
                result = result[3:].strip()
                
            # Remove ``` from the end
            if result.endswith('```'):
                result = result[:-3].strip()
                
            return result
        except Exception as exc:
            print(f"Error getting tool code suggestion: {exc}")
            return "AI suggestions not available"
    
    def create_function_tool(self, tool_def: ToolDefinition) -> Optional[Any]:
        """Create a function tool from tool definition following ADK patterns"""
        logger.info(f"🔧 Creating function tool: {tool_def.name} (ID: {tool_def.id})")
        
        if not ADK_AVAILABLE:
            logger.error("❌ ADK not available for tool creation")
            return None
            
        if tool_def.tool_type != ToolType.FUNCTION or not tool_def.function_code:
            logger.error(f"❌ Invalid tool definition: type={tool_def.tool_type}, has_code={bool(tool_def.function_code)}")
            return None
            
        logger.debug(f"📝 Tool function code length: {len(tool_def.function_code)} characters")
        logger.debug(f"📋 Tool function code preview: {tool_def.function_code[:200]}...")
            
        try:
            # Create a proper ADK function tool
            # The function should follow ADK patterns: clear signature, proper typing, docstrings
            def tool_function(input_data: str) -> str:
                """
                Execute the tool with the given input data.
                
                Args:
                    input_data (str): The input data for the tool
                    
                Returns:
                    str: The result of the tool execution
                """
                logger.info(f"🛠️ Executing tool '{tool_def.name}' with input: '{input_data[:100]}...'")
                try:
                    # Parse and handle import statements properly
                    logger.info(f"📝 Parsing imports from tool code for '{tool_def.name}'...")
                    imports_dict = self._extract_imports_from_code(tool_def.function_code)
                    logger.info(f"📦 Found imports: {list(imports_dict.keys())}")
                    
                    # Create a safe execution context with imports
                    safe_globals = {
                        '__builtins__': {
                            '__import__': __import__,  # Essential for import statements
                            'print': print,
                            'len': len,
                            'str': str,
                            'int': int,
                            'float': float,
                            'bool': bool,
                            'list': list,
                            'dict': dict,
                            'tuple': tuple,
                            'set': set,
                            'range': range,
                            'enumerate': enumerate,
                            'zip': zip,
                            'min': min,
                            'max': max,
                            'sum': sum,
                            'abs': abs,
                            'round': round,
                            'sorted': sorted,
                            'reversed': reversed,
                            'any': any,
                            'all': all,
                            'isinstance': isinstance,
                            'hasattr': hasattr,
                            'getattr': getattr,
                            'setattr': setattr,
                            'type': type,
                            'open': open,
                            # Exception classes
                            'Exception': Exception,
                            'ValueError': ValueError,
                            'TypeError': TypeError,
                            'AttributeError': AttributeError,
                            'KeyError': KeyError,
                            'IndexError': IndexError,
                            'ImportError': ImportError,
                            'RuntimeError': RuntimeError,
                            'OSError': OSError,
                            'IOError': IOError,
                        },
                        **imports_dict  # Add all the imported modules
                    }
                    
                    local_vars = {
                        'input_data': input_data,
                    }
                    
                    logger.info(f"📝 Executing function code for tool '{tool_def.name}'...")
                    
                    # Execute the function code with proper globals
                    # This will execute any top-level imports and function definitions
                    exec(tool_def.function_code, safe_globals, local_vars)
                    logger.info(f"✅ Function code executed successfully. Available functions: {list(local_vars.keys())}")
                    
                    # Look for an execute function or main function
                    if 'execute' in local_vars:
                        execute_func = local_vars['execute']
                        logger.info(f"🎯 Found execute function: {execute_func}")
                        # Always try with tool_context parameter first
                        try:
                            logger.info(f"🔄 Trying execute function with tool_context parameter...")
                            result = str(execute_func(input_data, None))
                            logger.info(f"✅ Execute function succeeded with tool_context: {len(result)} characters")
                            return result
                        except TypeError as e:
                            logger.info(f"⚠️ Execute function failed with tool_context, trying without: {e}")
                            # If that fails, try without tool_context
                            result = str(execute_func(input_data))
                            logger.info(f"✅ Execute function succeeded without tool_context: {len(result)} characters")
                            return result
                    elif 'main' in local_vars:
                        logger.info(f"🎯 Found main function: {local_vars['main']}")
                        result = str(local_vars['main'](input_data))
                        logger.info(f"✅ Main function succeeded: {len(result)} characters")
                        return result
                    else:
                        # If no execute function found, return a default response
                        logger.warning(f"⚠️ No execute or main function found in tool '{tool_def.name}'")
                        return f"Tool {tool_def.name} executed successfully with input: {input_data}"
                        
                except Exception as exc:
                    logger.error(f"❌ Error executing tool '{tool_def.name}': {exc}")
                    logger.error(f"📋 Tool execution error details: {traceback.format_exc()}")
                    return f"Error executing tool {tool_def.name}: {str(exc)}"
            
            # Set the function name and docstring for better identification
            tool_function.__name__ = tool_def.name.replace(' ', '_').lower()
            tool_function.__doc__ = tool_def.description
            
            # Create a proper ADK FunctionTool
            logger.info(f"🔧 Creating ADK FunctionTool for '{tool_def.name}'...")
            try:
                from google.adk.tools import FunctionTool
                logger.info(f"✅ FunctionTool imported successfully")
                # Check the correct constructor parameters for FunctionTool
                try:
                    adk_tool = FunctionTool(tool_function)
                    logger.info(f"✅ ADK FunctionTool created successfully: {type(adk_tool)}")
                    # Wrap the FunctionTool to make it callable
                    def wrapped_tool(input_data: str) -> str:
                        logger.info(f"🔄 Wrapped tool called for '{tool_def.name}' with input: '{input_data[:50]}...'")
                        try:
                            # Use the FunctionTool's run method if available
                            if hasattr(adk_tool, 'run'):
                                logger.info(f"🎯 Using adk_tool.run() method")
                                result = str(adk_tool.run(input_data))
                                logger.info(f"✅ adk_tool.run() succeeded: {len(result)} characters")
                                return result
                            elif hasattr(adk_tool, '__call__'):
                                logger.info(f"🎯 Using adk_tool.__call__() method")
                                result = str(adk_tool(input_data))
                                logger.info(f"✅ adk_tool.__call__() succeeded: {len(result)} characters")
                                return result
                            else:
                                logger.info(f"🎯 Using fallback to original function")
                                # Fallback to the original function with proper parameters
                                import inspect
                                sig = inspect.signature(tool_function)
                                logger.info(f"📋 Function signature: {sig}")
                                if len(sig.parameters) >= 2:
                                    logger.info(f"🔄 Calling with tool_context parameter")
                                    result = str(tool_function(input_data, None))
                                else:
                                    logger.info(f"🔄 Calling without tool_context parameter")
                                    result = str(tool_function(input_data))
                                logger.info(f"✅ Fallback function succeeded: {len(result)} characters")
                                return result
                        except Exception as exc:
                            logger.error(f"❌ Wrapped tool execution failed: {exc}")
                            logger.error(f"📋 Wrapped tool error details: {traceback.format_exc()}")
                            return f"Error executing tool {tool_def.name}: {str(exc)}"
                    
                    wrapped_tool.__name__ = tool_def.name.replace(' ', '_').lower()
                    wrapped_tool.__doc__ = tool_def.description
                    return wrapped_tool
                except TypeError as e:
                    logger.warning(f"⚠️ FunctionTool creation failed with TypeError: {e}")
                    # If that fails, try with just the function
                    try:
                        logger.info(f"🔄 Trying FunctionTool with just function parameter...")
                        adk_tool = FunctionTool(tool_function)
                        logger.info(f"✅ FunctionTool created with function only: {type(adk_tool)}")
                        # Same wrapping logic
                        def wrapped_tool(input_data: str) -> str:
                            try:
                                if hasattr(adk_tool, 'run'):
                                    return str(adk_tool.run(input_data))
                                elif hasattr(adk_tool, '__call__'):
                                    return str(adk_tool(input_data))
                                else:
                                    # Fallback to the original function with proper parameters
                                    import inspect
                                    sig = inspect.signature(tool_function)
                                    if len(sig.parameters) >= 2:
                                        return str(tool_function(input_data, None))
                                    else:
                                        return str(tool_function(input_data))
                            except Exception as execution_error:
                                return f"Error executing tool {tool_def.name}: {str(execution_error)}"
                        
                        wrapped_tool.__name__ = tool_def.name.replace(' ', '_').lower()
                        wrapped_tool.__doc__ = tool_def.description
                        return wrapped_tool
                    except Exception as e2:
                        logger.error(f"❌ FunctionTool creation failed completely: {e2}")
                        # Fallback to the function if FunctionTool fails
                        logger.info(f"🔄 Falling back to original function")
                        return tool_function
            except ImportError as e:
                logger.error(f"❌ FunctionTool import failed: {e}")
                # Fallback to the function if FunctionTool is not available
                logger.info(f"🔄 Falling back to original function")
                return tool_function
            
        except Exception as exc:
            logger.error(f"❌ Error creating function tool '{tool_def.name}': {exc}")
            logger.error(f"📋 Tool creation error details: {traceback.format_exc()}")
            print(f"Error creating function tool {tool_def.name}: {exc}")
            return None
    
    async def create_mcp_tool(self, tool_def: ToolDefinition) -> Optional[Any]:
        """Create an MCP tool from configuration"""
        logger.info(f"🔧 Creating MCP tool: {tool_def.name} (ID: {tool_def.id})")
        
        if not ADK_AVAILABLE:
            logger.error("❌ ADK not available for MCP tool creation")
            return None
            
        # Check for MCP config in various field names (due to storage issues)
        mcp_config = tool_def.mcp_config or tool_def.mcp_server_config or tool_def.mcp_configuration
        
        if not mcp_config:
            logger.error(f"❌ MCP config missing for tool '{tool_def.name}'")
            logger.error(f"🔧 Available fields: mcp_config={tool_def.mcp_config}, mcp_server_config={tool_def.mcp_server_config}, mcp_configuration={tool_def.mcp_configuration}")
            return None
            
        try:
            # Extract MCP configuration (already retrieved above)
            command = mcp_config.get("command", "npx")
            args = mcp_config.get("args", [])
            env = mcp_config.get("env", {})
            timeout = mcp_config.get("timeout", 300)
            
            logger.info(f"📋 MCP Config: command={command}, args={args}, env_keys={list(env.keys())}")
            
            # Create server parameters (using StdioConnectionParams as recommended)
            from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams
            server_params = StdioConnectionParams(
                server_params={
                    "command": command,
                    "args": args,
                    "env": env
                }
            )
            
            # Create MCP toolset
            logger.info(f"🔗 Connecting to MCP server...")
            mcp_toolset = MCPToolset(
                connection_params=server_params
            )
            
            logger.info(f"✅ MCP toolset created successfully for '{tool_def.name}'")
            return mcp_toolset
            
        except Exception as exc:
            logger.error(f"❌ Error creating MCP tool '{tool_def.name}': {exc}")
            logger.error(f"📋 MCP tool creation error details: {traceback.format_exc()}")
            return None
    
    async def _convert_mcp_tools_for_agent(self, agent):
        """Convert MCP ToolDefinition objects to MCPToolset objects for agent execution"""
        if not hasattr(agent, 'tools'):
            return
            
        converted_tools = []
        for tool in agent.tools:
            if isinstance(tool, ToolDefinition) and tool.tool_type == ToolType.MCP:
                logger.info(f"🔧 Converting MCP ToolDefinition to MCPToolset: {tool.name}")
                try:
                    mcp_toolset = await self.create_mcp_tool(tool)
                    if mcp_toolset:
                        converted_tools.append(mcp_toolset)
                        logger.info(f"✅ MCP toolset converted: {tool.name}")
                    else:
                        logger.error(f"❌ Failed to convert MCP tool: {tool.name}")
                except Exception as e:
                    logger.error(f"❌ Error converting MCP tool {tool.name}: {e}")
            else:
                converted_tools.append(tool)
        
        # Update agent tools with converted tools
        agent.tools = converted_tools
        logger.info(f"🔧 Agent tools converted: {len(converted_tools)} tools")
    
    def _create_model_for_provider(self, config: AgentConfiguration) -> Any:
        """Create model instance based on provider"""
        provider = getattr(config, 'model_provider', ModelProvider.GOOGLE)
        model_name = config.model_settings.get("model", "gemini-2.0-flash")
        temperature = config.model_settings.get("temperature", 0.7)
        max_tokens = config.model_settings.get("max_tokens", 1000)
        
        logger.info(f"🔧 Creating model: provider={provider}, model={model_name}")
        
        if provider == ModelProvider.GOOGLE:
            # Use Google Gemini with service account
            return Gemini(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        else:
            # For non-Google providers, we'll use LiteLLM
            if not LITELLM_AVAILABLE:
                logger.warning(f"⚠️ LiteLLM not available, falling back to Google Gemini")
                return Gemini(
                    model="gemini-2.0-flash",
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            
            # Validate provider configuration
            if not self.model_service.validate_provider_config(provider):
                logger.warning(f"⚠️ Provider {provider} not configured, falling back to Google Gemini")
                return Gemini(
                    model="gemini-2.0-flash",
                    temperature=temperature,
                    max_output_tokens=max_tokens
                )
            
            # Create LiteLLM model
            litellm_model_name = self.model_service.get_litellm_model_name(provider, model_name)
            logger.info(f"🔧 Using LiteLLM model: {litellm_model_name}")
            
            # For now, we'll create a custom model wrapper that uses LiteLLM
            # This is a simplified approach - in production, you'd want a more robust integration
            class LiteLLMModel:
                def __init__(self, model_name, temperature, max_tokens):
                    self.model_name = model_name
                    self.temperature = temperature
                    self.max_tokens = max_tokens
                
                def generate_content(self, prompt, **kwargs):
                    """Generate content using LiteLLM"""
                    try:
                        response = litellm.completion(
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=self.temperature,
                            max_tokens=self.max_tokens,
                            **kwargs
                        )
                        return response.choices[0].message.content
                    except Exception as e:
                        logger.error(f"❌ LiteLLM generation failed: {e}")
                        return f"Error generating content: {str(e)}"
            
            return LiteLLMModel(litellm_model_name, temperature, max_tokens)
    
    def _extract_imports_from_code(self, code: str) -> Dict[str, Any]:
        """
        Extract import statements from Python code and return a dictionary of imported modules.
        Automatically installs missing packages using pip.
        
        Args:
            code: Python code string
            
        Returns:
            Dictionary mapping import names to imported modules
        """
        import ast
        import importlib
        import subprocess
        import sys
        
        imports_dict = {}
        missing_packages = set()
        
        try:
            # Parse the code into an AST
            tree = ast.parse(code)
            
            # Walk through the AST to find import statements
            # This will find imports at any level (module level or inside functions)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Handle: import module
                    for alias in node.names:
                        module_name = alias.name
                        import_name = alias.asname if alias.asname else module_name.split('.')[0]
                        
                        try:
                            logger.info(f"📦 Importing module: {module_name} as {import_name}")
                            module = importlib.import_module(module_name)
                            imports_dict[import_name] = module
                            logger.info(f"✅ Successfully imported {module_name} as {import_name}")
                            
                            # Also add the full module path for nested access
                            if '.' in module_name:
                                parts = module_name.split('.')
                                for i in range(1, len(parts) + 1):
                                    partial_name = '.'.join(parts[:i])
                                    try:
                                        partial_module = importlib.import_module(partial_name)
                                        imports_dict[partial_name] = partial_module
                                    except ImportError:
                                        pass
                                        
                        except ImportError as e:
                            logger.warning(f"⚠️ Failed to import {module_name}: {e}")
                            # Add to missing packages for auto-installation
                            package_name = module_name.split('.')[0]
                            missing_packages.add(package_name)
                            
                            # Try to import parent modules if this fails
                            if '.' in module_name:
                                parent_module = module_name.rsplit('.', 1)[0]
                                try:
                                    logger.info(f"📦 Trying parent module: {parent_module}")
                                    parent = importlib.import_module(parent_module)
                                    imports_dict[parent_module] = parent
                                except ImportError:
                                    pass
                            
                elif isinstance(node, ast.ImportFrom):
                    # Handle: from module import name
                    module_name = node.module
                    if module_name:
                        try:
                            logger.info(f"📦 Importing from module: {module_name}")
                            module = importlib.import_module(module_name)
                            
                            for alias in node.names:
                                import_name = alias.asname if alias.asname else alias.name
                                
                                if alias.name == '*':
                                    # Handle: from module import *
                                    logger.info(f"📦 Importing all from {module_name}")
                                    if hasattr(module, '__all__'):
                                        for name in module.__all__:
                                            if hasattr(module, name):
                                                imports_dict[name] = getattr(module, name)
                                                logger.info(f"✅ Imported {name} from {module_name}")
                                    else:
                                        # Import all non-private attributes
                                        for name in dir(module):
                                            if not name.startswith('_'):
                                                imports_dict[name] = getattr(module, name)
                                                logger.info(f"✅ Imported {name} from {module_name}")
                                else:
                                    # Handle: from module import specific_name
                                    if hasattr(module, alias.name):
                                        imports_dict[import_name] = getattr(module, alias.name)
                                        logger.info(f"✅ Imported {alias.name} as {import_name} from {module_name}")
                                    else:
                                        logger.warning(f"⚠️ {alias.name} not found in {module_name}")
                                        # Try to find it in submodules
                                        for attr_name in dir(module):
                                            if not attr_name.startswith('_'):
                                                try:
                                                    attr = getattr(module, attr_name)
                                                    if hasattr(attr, alias.name):
                                                        imports_dict[import_name] = getattr(attr, alias.name)
                                                        logger.info(f"✅ Found {alias.name} in submodule {attr_name}")
                                                        break
                                                except:
                                                    pass
                                        
                        except ImportError as e:
                            logger.warning(f"⚠️ Failed to import from {module_name}: {e}")
                            # Add to missing packages for auto-installation
                            package_name = module_name.split('.')[0]
                            missing_packages.add(package_name)
                            
                            # Try to import parent modules if this fails
                            if '.' in module_name:
                                parent_module = module_name.rsplit('.', 1)[0]
                                try:
                                    logger.info(f"📦 Trying parent module: {parent_module}")
                                    parent = importlib.import_module(parent_module)
                                    imports_dict[parent_module] = parent
                                except ImportError:
                                    pass
            
            # Auto-install missing packages
            if missing_packages:
                logger.info(f"🔧 Auto-installing missing packages: {list(missing_packages)}")
                for package in missing_packages:
                    try:
                        logger.info(f"📦 Installing package: {package}")
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install", package, "--quiet"
                        ])
                        logger.info(f"✅ Successfully installed {package}")
                        
                        # Try to import the package again
                        try:
                            module = importlib.import_module(package)
                            imports_dict[package] = module
                            logger.info(f"✅ Successfully imported {package} after installation")
                        except ImportError as e:
                            logger.warning(f"⚠️ Still failed to import {package} after installation: {e}")
                            
                    except subprocess.CalledProcessError as e:
                        logger.error(f"❌ Failed to install package {package}: {e}")
                    except Exception as e:
                        logger.error(f"❌ Unexpected error installing {package}: {e}")
                            
        except SyntaxError as e:
            logger.warning(f"⚠️ Syntax error in code: {e}")
            # Don't fallback to hardcoded imports - let it fail cleanly
            logger.info("📝 Code has syntax errors, no imports will be available")
                
        return imports_dict
    
    async def create_llm_agent(self, config: AgentConfiguration) -> Optional[Any]:
        """Create an LLM agent from configuration"""
        logger.info(f"🤖 Creating LLM agent: {config.name} (ID: {config.id})")
        logger.info(f"📋 Agent config: type={config.agent_type}, model={config.model_settings.get('model', 'default')}, tools_count={len(config.tools) if config.tools else 0}")
        
        if not ADK_AVAILABLE:
            logger.error("❌ ADK not available for agent creation")
            print("ADK not available")
            return None
            
        try:
            print(f"Creating LLM agent: {config.name}")
            print(f"Available tools: {list(self.tools.keys())}")
            print(f"Requested tools: {config.tools}")
            
            # Create the model based on provider
            model = self._create_model_for_provider(config)
            
            # Create the agent
            agent = LlmAgent(
                name=config.name,
                instruction=config.system_prompt,
                model=model
            )
            
            # Add tools if any
            if config.tools:
                print(f"Adding tools to agent: {config.tools}")
                for tool_id in config.tools:
                    if tool_id in self.tools:
                        tool = self.tools[tool_id]
                        
                        # Handle MCP tools - they need async creation
                        if isinstance(tool, ToolDefinition) and tool.tool_type == ToolType.MCP:
                            print(f"Creating MCP tool {tool_id} for agent")
                            try:
                                # Create MCP tool asynchronously
                                import asyncio
                                try:
                                    # Try to get existing event loop
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        # If loop is running, we need to use a different approach
                                        print(f"⚠️ Event loop is running, deferring MCP tool creation for {tool_id}")
                                        # Store the tool definition for later async creation
                                        agent.tools.append(tool)
                                    else:
                                        mcp_tool = loop.run_until_complete(self.create_mcp_tool(tool))
                                        if mcp_tool:
                                            agent.tools.append(mcp_tool)
                                            print(f"✅ MCP tool {tool_id} added to agent")
                                        else:
                                            print(f"❌ Failed to create MCP tool {tool_id}")
                                except RuntimeError:
                                    # No event loop, create one
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    mcp_tool = loop.run_until_complete(self.create_mcp_tool(tool))
                                    loop.close()
                                    
                                    if mcp_tool:
                                        agent.tools.append(mcp_tool)
                                        print(f"✅ MCP tool {tool_id} added to agent")
                                    else:
                                        print(f"❌ Failed to create MCP tool {tool_id}")
                            except Exception as e:
                                print(f"❌ Error creating MCP tool {tool_id}: {e}")
                                # Add the tool definition anyway for later processing
                                agent.tools.append(tool)
                        else:
                            print(f"Adding tool {tool_id} to agent")
                            agent.tools.append(tool)
                    else:
                        print(f"Warning: Tool {tool_id} not found in registered tools")
            
            print(f"Successfully created agent: {config.name}")
            # Store agent in memory for execution
            # Handle sub-agents if any
            if config.sub_agents:
                logger.info(f"🔗 Processing {len(config.sub_agents)} sub-agents for agent {config.name}")
                await self._add_sub_agents_to_agent(agent, config.sub_agents)
            
            # Store the agent
            self.agents[config.id] = agent
            
            # Store the original config for MCP tool conversion later
            agent._original_config = config
            
            return agent
            
        except Exception as exc:
            print(f"Error creating LLM agent {config.name}: {exc}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _add_sub_agents_to_agent(self, parent_agent: Any, sub_agents: List[Any]) -> None:
        """Add sub-agents to a parent agent by creating tools that delegate to sub-agents"""
        logger.info(f"🔗 Adding {len(sub_agents)} sub-agents to parent agent")
        
        for sub_agent_config in sub_agents:
            try:
                logger.info(f"🔧 Creating sub-agent tool for: {sub_agent_config.name} (ID: {sub_agent_config.id})")
                
                # Create a tool that delegates to the sub-agent
                sub_agent_tool = self._create_sub_agent_tool(sub_agent_config)
                if sub_agent_tool:
                    parent_agent.tools.append(sub_agent_tool)
                    logger.info(f"✅ Added sub-agent tool: {sub_agent_config.name}")
                else:
                    logger.error(f"❌ Failed to create sub-agent tool: {sub_agent_config.name}")
                    
            except Exception as e:
                logger.error(f"❌ Error creating sub-agent tool for {sub_agent_config.name}: {e}")
                logger.error(f"📋 Sub-agent tool creation error details: {traceback.format_exc()}")
    
    def _create_sub_agent_tool(self, sub_agent_config: Any) -> Optional[Any]:
        """Create a tool that delegates execution to a sub-agent"""
        try:
            # Create a synchronous function that will execute the sub-agent
            def sub_agent_executor(input_data: str, tool_context: Optional[Any] = None) -> str:
                """Execute a sub-agent with the given input"""
                try:
                    logger.info(f"🎯 Executing sub-agent: {sub_agent_config.name}")
                    
                    # Get the sub-agent from the database
                    if self.db_manager:
                        sub_agent_data = self.db_manager.get_agent(sub_agent_config.id)
                        if sub_agent_data:
                            # Create a temporary agent configuration
                            from .models import AgentConfiguration, AgentType
                            sub_config = AgentConfiguration(**sub_agent_data)
                            
                            # Create and execute the sub-agent synchronously
                            import asyncio
                            import concurrent.futures
                            try:
                                # Use ThreadPoolExecutor to run async code in a separate thread
                                logger.info(f"🔄 Executing sub-agent {sub_agent_config.name} in separate thread")
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        lambda: asyncio.run(self._execute_sub_agent_sync(sub_config, input_data))
                                    )
                                    result = future.result(timeout=30)
                                    return result
                            except Exception as loop_error:
                                logger.error(f"❌ Event loop error: {loop_error}")
                                return f"Sub-agent execution failed: {str(loop_error)}"
                        else:
                            return f"Sub-agent {sub_agent_config.name} not found in database"
                    else:
                        return f"No database manager available for sub-agent {sub_agent_config.name}"
                        
                except Exception as e:
                    logger.error(f"❌ Error executing sub-agent {sub_agent_config.name}: {e}")
                    return f"Error executing sub-agent {sub_agent_config.name}: {str(e)}"
            
            # Create the ADK function tool
            from google.adk.tools.function_tool import FunctionTool
            adk_tool = FunctionTool(sub_agent_executor)
            
            # Set the tool name to match what the LLM will call
            adk_tool.name = "sub_agent_executor"
            adk_tool.description = f"Use this tool to delegate tasks to your sub-agent '{sub_agent_config.name}'. Call this function when you need help from your sub-agent. Input: the question or task for the sub-agent."
            
            return adk_tool
            
        except Exception as e:
            logger.error(f"❌ Error creating sub-agent tool: {e}")
            return None
    
    async def _execute_sub_agent_sync(self, sub_config: Any, input_data: str) -> str:
        """Execute a sub-agent synchronously"""
        try:
            logger.info(f"🔧 Creating sub-agent: {sub_config.name}")
            # Create the sub-agent
            sub_agent = await self.create_llm_agent(sub_config)
            if not sub_agent:
                logger.error(f"❌ Failed to create sub-agent: {sub_config.name}")
                return f"Failed to create sub-agent: {sub_config.name}"
            
            logger.info(f"✅ Sub-agent created successfully: {sub_config.name}")
            logger.info(f"🎯 Executing sub-agent with prompt: {input_data}")
            
            # Execute the sub-agent
            result = await self.traced_runner.run(
                agent=sub_agent,
                prompt=input_data,
                session_id=f"sub_agent_{sub_config.id}",
                user_id="sub_agent_execution"
            )
            
            logger.info(f"📊 Sub-agent execution result: success={result.success}")
            if result.success:
                logger.info(f"✅ Sub-agent response: {result.response[:100]}...")
                return result.response
            else:
                logger.error(f"❌ Sub-agent execution failed: {result.error}")
                return f"Sub-agent execution failed: {result.error}"
                
        except Exception as e:
            logger.error(f"❌ Error in sub-agent execution: {e}")
            logger.error(f"📋 Sub-agent execution error details: {traceback.format_exc()}")
            return f"Sub-agent execution error: {str(e)}"
    
    async def create_agent(self, config: AgentConfiguration) -> Optional[Any]:
        """Create an agent from configuration"""
        if config.agent_type == AgentType.LLM:
            return await self.create_llm_agent(config)
        else:
            print(f"Unsupported agent type: {config.agent_type}")
            return None
    
    def register_tool(self, tool_def: ToolDefinition) -> bool:
        """Register a tool in the service"""
        try:
            if tool_def.tool_type == ToolType.FUNCTION and tool_def.function_code:
                # Create a proper ADK function tool
                tool = self.create_function_tool(tool_def)
                if tool:
                    self.tools[tool_def.id] = tool
                    return True
                else:
                    print(f"Failed to create function tool for: {tool_def.name}")
                    return False
            elif tool_def.tool_type == ToolType.BUILTIN:
                # Handle built-in tools
                if tool_def.builtin_name == "google_search":
                    adk_tool = google_search
                else:
                    print(f"Unknown built-in tool: {tool_def.builtin_name}")
                    return False
                
                self.tools[tool_def.id] = adk_tool
                return True
            elif tool_def.tool_type == ToolType.MCP:
                # Handle MCP tools - store the tool definition for async creation
                self.tools[tool_def.id] = tool_def
                logger.info(f"📋 MCP tool '{tool_def.name}' registered for async creation")
                return True
            else:
                # Store the tool definition for non-function tools
                self.tools[tool_def.id] = tool_def
                return True
                
        except Exception as exc:
            print(f"Error registering tool {tool_def.name}: {exc}")
            return False
    
    def register_agent(self, config: AgentConfiguration) -> bool:
        """Register an agent in the service"""
        try:
            print(f"Registering agent: {config.name} (ID: {config.id})")
            print(f"ADK available: {ADK_AVAILABLE}")
            print(f"Agent type: {config.agent_type}")
            
            agent = self.create_agent(config)
            if agent:
                self.agents[config.id] = agent
                print(f"Successfully registered agent: {config.name}")
                return True
            else:
                print(f"Failed to create agent: {config.name}")
                return False
        except Exception as exc:
            print(f"Error registering agent {config.name}: {exc}")
            import traceback
            traceback.print_exc()
            return False
    
    async def execute_agent(self, agent_id: str, prompt: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> AgentExecutionResult:
        """Execute an agent with a given prompt"""
        logger.info(f"🚀 Starting agent execution - Agent ID: {agent_id}, Prompt: '{prompt[:100]}...', Session: {session_id}, User: {user_id}")
        
        if not ADK_AVAILABLE:
            logger.error("❌ Google ADK not available")
            return AgentExecutionResult(
                success=False,
                error="Google ADK not available. Please install with: pip install google-adk"
            )
        
        # Check if agent exists in memory or database
        logger.info(f"🔍 Checking for agent {agent_id} in memory...")
        logger.info(f"📊 Available agents in memory: {list(self.agents.keys())}")
        
        # Force reload agent from database to get latest code changes
        if agent_id in self.agents:
            logger.info(f"🔄 Force reloading agent {agent_id} from database to get latest changes...")
            del self.agents[agent_id]
        
        if agent_id not in self.agents:
            logger.info(f"⚠️ Agent {agent_id} not found in memory, checking database...")
            if self.db_manager:
                # Try to get agent from database
                agent_data = self.db_manager.get_agent(agent_id)
                logger.info(f"📋 Agent data from database: {json.dumps(agent_data, indent=2) if agent_data else 'None'}")
                
                if agent_data:
                    # Create the agent from database data
                    logger.info(f"🔧 Creating agent from database data...")
                    agent = await self.create_llm_agent(AgentConfiguration(**agent_data))
                    if agent:
                        self.agents[agent_id] = agent
                        logger.info(f"✅ Successfully created and cached agent {agent_id}")
                    else:
                        logger.error(f"❌ Failed to create agent {agent_id} from database")
                        return AgentExecutionResult(
                            success=False,
                            error=f"Failed to create agent {agent_id} from database"
                        )
                else:
                    logger.error(f"❌ Agent {agent_id} not found in database")
                    return AgentExecutionResult(
                        success=False,
                        error=f"Agent {agent_id} not found in database"
                    )
            else:
                logger.error(f"❌ Agent {agent_id} not found and no database manager")
                return AgentExecutionResult(
                    success=False,
                    error=f"Agent {agent_id} not found"
                )
        else:
            agent = self.agents[agent_id]
            logger.info(f"✅ Found agent {agent_id} in memory")
        
        start_time = time.time()
        
        # Use provided user_id or default
        effective_user_id = user_id or self.user_id
        logger.info(f"👤 Using user ID: {effective_user_id}")
        
        try:
            # Create or get session
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.info(f"🆔 Generated new session ID: {session_id}")
            else:
                logger.info(f"🆔 Using provided session ID: {session_id}")
            
            # Log agent details
            logger.info(f"🤖 Agent details: {type(agent).__name__}")
            logger.info(f"🔧 Agent tools: {getattr(agent, 'tools', 'No tools')}")
            
            # Convert MCP tools before execution
            await self._convert_mcp_tools_for_agent(agent)
            
            # Use traced runner if available, otherwise fall back to regular runner
            if self.traced_runner:
                logger.info(f"📊 Using traced runner for execution...")
                # Execute with Cloud Trace integration
                logger.info(f"📊 Executing with traced runner...")
                logger.info(f"📝 Additional context: prompt_length={len(prompt)}, agent_type={getattr(agent, 'agent_type', 'unknown')}, model={getattr(agent, 'model', getattr(agent, 'model_name', 'unknown'))}")
                
                trace_result = await self.traced_runner.run_agent_with_trace(
                    agent=agent,
                    user_id=effective_user_id,
                    session_id=session_id,
                    user_message=prompt,
                    agent_id=agent_id,
                    additional_context={
                        "prompt_length": len(prompt),
                        "agent_type": getattr(agent, 'agent_type', 'unknown'),
                        "model": getattr(agent, 'model', getattr(agent, 'model_name', 'unknown'))
                    }
                )
                
                logger.info(f"📊 Trace result: {json.dumps(trace_result, indent=2)}")
                
                if trace_result.get("success"):
                    final_response = trace_result.get("response", "No response received")
                    logger.info(f"✅ Traced execution successful, response length: {len(final_response)}")
                else:
                    logger.error(f"❌ Traced execution failed: {trace_result.get('error', 'Unknown error')}")
                    return AgentExecutionResult(
                        success=False,
                        error=trace_result.get("error", "Unknown error"),
                        execution_time=time.time() - start_time
                    )
            else:
                logger.info(f"🔄 Using fallback execution without tracing...")
                # Fallback to regular execution without tracing
                # Ensure session exists
                try:
                    logger.info(f"📝 Creating session: app_name={self.app_name}, user_id={effective_user_id}, session_id={session_id}")
                    await self.session_service.create_session(
                        app_name=self.app_name,
                        user_id=effective_user_id,
                        session_id=session_id
                    )
                    logger.info(f"✅ Session created successfully")
                except Exception as e:
                    logger.info(f"⚠️ Session creation failed (might already exist): {e}")
                    pass  # Session might already exist
                
                # Create runner for the agent
                logger.info(f"🏃 Creating runner for agent...")
                runner = Runner(
                    agent=agent,
                    app_name=self.app_name,
                    session_service=self.session_service
                )
                logger.info(f"✅ Runner created successfully")
                
                # Format the message using Google ADK types
                user_content = types.Content(
                    role='user',
                    parts=[types.Part(text=prompt)]
                )
                logger.info(f"📝 Formatted user content: role=user, text_length={len(prompt)}")
                
                # Execute the agent using the runner
                final_response = "No response received"
                event_count = 0
                logger.info(f"🚀 Starting agent execution with runner...")
                
                async for event in runner.run_async(
                    user_id=effective_user_id,
                    session_id=session_id,
                    new_message=user_content
                ):
                    event_count += 1
                    logger.info(f"📨 Event #{event_count}: {type(event).__name__}")
                    
                    if event.is_final_response() and event.content and event.content.parts:
                        final_response = event.content.parts[0].text
                        logger.info(f"✅ Final response received: {len(final_response)} characters")
                        break
                    else:
                        logger.info(f"📝 Intermediate event: {event}")
                
                logger.info(f"🏁 Execution completed after {event_count} events")
            
            result_text = final_response
            execution_time = time.time() - start_time
            
            logger.info(f"⏱️ Execution completed in {execution_time:.2f} seconds")
            logger.info(f"📄 Final response: {result_text[:200]}..." if len(result_text) > 200 else f"📄 Final response: {result_text}")
            
            # Store in session if provided
            if session_id:
                logger.info(f"💾 Storing conversation in session {session_id}")
                if session_id not in self.sessions:
                    self.sessions[session_id] = []
                
                # Add user message
                user_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    role="user",
                    content=prompt,
                    timestamp=str(time.time())
                )
                self.sessions[session_id].append(user_message)
                
                # Add assistant message
                assistant_message = ChatMessage(
                    id=str(uuid.uuid4()),
                    role="assistant",
                    content=result_text,
                    timestamp=str(time.time())
                )
                self.sessions[session_id].append(assistant_message)
                
                # Store in database if available
                if self.db_manager:
                    try:
                        # Get existing session or create new one
                        existing_session = self.db_manager.get_chat_session(session_id)
                        if existing_session:
                            # Update existing session
                            messages = existing_session.get('messages', [])
                            messages.extend([user_message.dict(), assistant_message.dict()])
                            self.db_manager.save_chat_session({
                                'id': session_id,
                                'agent_id': agent_id,
                                'messages': messages
                            })
                        else:
                            # Create new session
                            self.db_manager.save_chat_session({
                                'id': session_id,
                                'agent_id': agent_id,
                                'messages': [user_message.dict(), assistant_message.dict()]
                            })
                    except Exception as e:
                        print(f"Failed to save session to database: {e}")
            
            return AgentExecutionResult(
                success=True,
                response=result_text,
                execution_time=execution_time
            )
            
        except Exception as exc:
            execution_time = time.time() - start_time
            error_msg = f"Error executing agent: {str(exc)}"
            logger.error(f"❌ Error executing agent {agent_id}: {exc}")
            logger.error(f"📊 Execution time before error: {execution_time:.2f} seconds")
            logger.error(f"🔍 Error type: {type(exc).__name__}")
            logger.error(f"📋 Error details: {traceback.format_exc()}")
            
            print(error_msg)
            
            return AgentExecutionResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
    
    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get a registered agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all registered agent IDs"""
        return list(self.agents.keys())
    
    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """Get messages for a chat session"""
        return self.sessions.get(session_id, [])
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a chat session"""

        

        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def process_message(self, agent: Dict[str, Any], message: str) -> str:
        """Process a message through an agent for embedded chat"""
        try:
            # Create a simple agent instance for processing
            if agent.get('agent_type') == 'llm':
                # For LLM agents, use the system prompt
                system_prompt = agent.get('system_prompt', 'You are a helpful AI assistant.')
                
                # Use GenAI for simple text generation if available
                if self.genai_client:
                    try:
                        # Use the correct GenAI API method
                        response = self.genai_client.models.generate_content(
                            model='gemini-2.0-flash-001',
                            contents=f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
                        )
                        return response.text
                    except Exception as genai_error:
                        print(f"GenAI error: {genai_error}")
                        # Fallback response
                        return f"I understand you said: '{message}'. I'm configured as {agent.get('name', 'an AI assistant')}."
                else:
                    # Fallback response
                    return f"I understand you said: '{message}'. I'm configured as {agent.get('name', 'an AI assistant')}."
            
            elif agent.get('agent_type') == 'workflow':
                # For workflow agents, provide a structured response
                return f"As a workflow agent ({agent.get('name', 'AI Assistant')}), I can help you with: {agent.get('description', 'various tasks')}. Your message: '{message}'"
            
            else:
                # Generic response for other agent types
                return f"Hello! I'm {agent.get('name', 'an AI agent')}. I received your message: '{message}'. How can I assist you?"
                
        except Exception as e:
            print(f"Error processing message: {e}")
            return "I'm sorry, I encountered an error processing your message. Please try again."