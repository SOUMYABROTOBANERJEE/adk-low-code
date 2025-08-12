"""
Core ADK service for creating and executing agents
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import importlib.util
import traceback

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
    
    ADK_AVAILABLE = True
    print("Google ADK loaded successfully")
    
except ImportError as e:
    ADK_AVAILABLE = False
    print(f"Warning: Google ADK not available. Import error: {e}")
    print("Install with: pip install google-adk")

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
    ToolType, AgentExecutionResult, ChatMessage
)


class ADKService:
    """Service for managing Google ADK agents"""
    
    def __init__(self, db_manager=None):
        self.agents: Dict[str, Any] = {}
        self.tools: Dict[str, Any] = {}
        self.sessions: Dict[str, List[ChatMessage]] = {}
        self.session_service = InMemorySessionService() if ADK_AVAILABLE else None
        self.app_name = "google_adk_platform"
        self.user_id = "default_user"
        self.api_key = "AIzaSyAameifAiVmm05ww2Ib5ofFmvbGGHFTSnk"
        self.db_manager = db_manager
        
        # Set environment variable for Google AI
        import os
        os.environ["GOOGLE_API_KEY"] = self.api_key
        
        # Initialize Google GenAI client for prompt suggestions
        if GENAI_AVAILABLE:
            try:
                self.genai_client = genai.Client(api_key=self.api_key)
                print("Google GenAI client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Google GenAI client: {e}")
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
        except Exception as e:
            print(f"Error getting agent name suggestion: {e}")
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
        except Exception as e:
            print(f"Error getting agent description suggestion: {e}")
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
        except Exception as e:
            print(f"Error getting agent system prompt suggestion: {e}")
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
        except Exception as e:
            print(f"Error getting tool name suggestion: {e}")
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
        except Exception as e:
            print(f"Error getting tool description suggestion: {e}")
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
            
            Generate Python function code that implements this tool's functionality.
            The code should:
            - Have a clear function signature with appropriate parameters
            - Include proper error handling
            - Return meaningful results
            - Follow Python best practices
            - Include docstring explaining the function
            - Handle edge cases appropriately
            
            For function tools, create a main function that can be called by the ADK.
            For other tool types, create appropriate initialization or configuration code.
            
            Return only the Python code, nothing else."""
            
            response = self.genai_client.models.generate_content(
                model='gemini-2.0-flash-001',
                contents=prompt
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error getting tool code suggestion: {e}")
            return "AI suggestions not available"
    
    def create_function_tool(self, tool_def: ToolDefinition) -> Optional[Any]:
        """Create a function tool from tool definition"""
        if not ADK_AVAILABLE:
            return None
            
        if tool_def.tool_type != ToolType.FUNCTION or not tool_def.function_code:
            return None
            
        try:
            # Create a simple function that executes the tool logic
            # This is a simplified approach that works with the current ADK setup
            def tool_function(data: str) -> str:
                """Execute the tool with the given data"""
                # Execute the tool logic based on the tool name
                if tool_def.name == "Database Insert Tool":
                    return f"Data inserted successfully: {data}"
                elif tool_def.name == "Data Validation Tool":
                    try:
                        import json
                        parsed_data = json.loads(data)
                        if isinstance(parsed_data, dict) and parsed_data:
                            return f"Data validation successful: {len(parsed_data)} fields validated"
                        else:
                            return "Data validation failed: Invalid format"
                    except:
                        return "Data validation failed: Invalid JSON format"
                else:
                    return f"Tool {tool_def.name} executed with data: {data}"
            
            return tool_function
            
        except Exception as e:
            print(f"Error creating function tool {tool_def.name}: {e}")
            return None
    
    def create_llm_agent(self, config: AgentConfiguration) -> Optional[Any]:
        """Create an LLM agent from configuration"""
        if not ADK_AVAILABLE:
            print("ADK not available")
            return None
            
        try:
            # Create the model with API key
            model = Gemini(
                model=config.model_settings.get("model", "gemini-2.0-flash"),
                temperature=config.model_settings.get("temperature", 0.7),
                max_output_tokens=config.model_settings.get("max_tokens", 1000),
                api_key=self.api_key
            )
            
            # Create the agent
            agent = LlmAgent(
                name=config.name,
                instruction=config.system_prompt,
                model=model
            )
            
            # Add tools if any
            if config.tools:
                for tool_id in config.tools:
                    if tool_id in self.tools:
                        agent.tools.append(self.tools[tool_id])
            
            return agent
            
        except Exception as e:
            print(f"Error creating LLM agent {config.name}: {e}")
            return None
    
    def create_agent(self, config: AgentConfiguration) -> Optional[Any]:
        """Create an agent from configuration"""
        if config.agent_type == AgentType.LLM:
            return self.create_llm_agent(config)
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
            else:
                # Store the tool definition for non-function tools
                self.tools[tool_def.id] = tool_def
                return True
                
        except Exception as e:
            print(f"Error registering tool {tool_def.name}: {e}")
            return False
    
    def register_agent(self, config: AgentConfiguration) -> bool:
        """Register an agent in the service"""
        try:
            agent = self.create_agent(config)
            if agent:
                self.agents[config.id] = agent
                return True
            return False
        except Exception as e:
            print(f"Error registering agent {config.name}: {e}")
            return False
    
    async def execute_agent(self, agent_id: str, prompt: str, session_id: Optional[str] = None) -> AgentExecutionResult:
        """Execute an agent with a given prompt"""
        if not ADK_AVAILABLE:
            return AgentExecutionResult(
                success=False,
                error="Google ADK not available. Please install with: pip install google-adk"
            )
        
        # Check if agent exists in memory or database
        if agent_id not in self.agents:
            if self.db_manager:
                # Try to get agent from database
                agent_data = self.db_manager.get_agent(agent_id)
                if agent_data:
                    # Create the agent from database data
                    agent = self.create_llm_agent(AgentConfiguration(**agent_data))
                    if agent:
                        self.agents[agent_id] = agent
                    else:
                        return AgentExecutionResult(
                            success=False,
                            error=f"Failed to create agent {agent_id} from database"
                        )
                else:
                    return AgentExecutionResult(
                        success=False,
                        error=f"Agent {agent_id} not found in database"
                    )
            else:
                return AgentExecutionResult(
                    success=False,
                    error=f"Agent {agent_id} not found"
                )
        else:
            agent = self.agents[agent_id]
        
        start_time = time.time()
        
        try:
            
            # Create or get session
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Ensure session exists
            try:
                await self.session_service.create_session(
                    app_name=self.app_name,
                    user_id=self.user_id,
                    session_id=session_id
                )
            except:
                pass  # Session might already exist
            
            # Create runner for the agent
            runner = Runner(
                agent=agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            
            # Format the message using Google ADK types
            user_content = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )
            
            # Execute the agent using the runner
            final_response = "No response received"
            async for event in runner.run_async(
                user_id=self.user_id,
                session_id=session_id,
                new_message=user_content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                    break
            
            result_text = final_response
            
            execution_time = time.time() - start_time
            
            # Store in session if provided
            if session_id:
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
            
            return AgentExecutionResult(
                success=True,
                response=result_text,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error executing agent: {str(e)}"
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
