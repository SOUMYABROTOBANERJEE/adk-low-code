import os
import json
import uvicorn
import requests
import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Load environment variables from config file
def load_env_config():
    """Load environment variables from config.env file."""
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), '.env')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load configuration
load_env_config()

# Import Ollama integration
try:
    from .ollama_integration import generate_ollama_agent_code, check_ollama_availability, list_ollama_models
    OLLAMA_AVAILABLE = check_ollama_availability()
except ImportError:
    OLLAMA_AVAILABLE = False

# Import Google ADK integration
try:
    from .google_adk_integration import get_google_adk_integration, GoogleADKAgentConfig, is_google_adk_available
    GOOGLE_ADK_AVAILABLE = is_google_adk_available()
except ImportError:
    GOOGLE_ADK_AVAILABLE = False

# Google Gemini API Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyAameifAiVmm05ww2Ib5ofFmvbGGHFTSnk')
GOOGLE_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

def check_google_api_key():
    """Check if Google API key is valid by making a test request."""
    if not GOOGLE_API_KEY:
        return False
    
    try:
        # Test the API key with a simple request
        test_url = f"{GOOGLE_API_BASE_URL}/gemini-1.5-flash"
        headers = {"Authorization": f"Bearer {GOOGLE_API_KEY}"}
        response = requests.get(test_url, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking Google API key: {e}")
        return False

# Define model classes
class SubAgentConfig(BaseModel):
    name: str
    model: str
    instruction: str
    description: Optional[str] = None
    tools: Optional[List[str]] = None

class AgentConfig(BaseModel):
    name: str
    model: str
    provider: str = "google"  # Default to Google, can be "ollama"
    ollama_base_url: Optional[str] = "http://localhost:11434"  # For Ollama models
    instruction: str
    description: Optional[str] = None
    tools: Optional[List[str]] = None
    sub_agents: Optional[List[SubAgentConfig]] = None
    flow: Optional[str] = "auto"
    temperature: Optional[float] = 0.2
    # Multi-tech stack support
    generate_api: Optional[bool] = False
    api_port: Optional[int] = 8000

def create_app():
    """Create the FastAPI application."""
    # Create FastAPI app
    app = FastAPI(title="No-Code ADK Interface")

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, "templates")
    static_dir = os.path.join(current_dir, "static")

    # Create agents directory
    agents_dir = os.path.join(current_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)

    # Set up templates
    templates = Jinja2Templates(directory=templates_dir)

    # Mount static files
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Create custom tools directory and file
    custom_tools_dir = os.path.join(current_dir, "custom_tools")
    custom_tools_file = os.path.join(custom_tools_dir, "tools.json")
    os.makedirs(custom_tools_dir, exist_ok=True)
    if not os.path.exists(os.path.join(custom_tools_dir, "__init__.py")):
        open(os.path.join(custom_tools_dir, "__init__.py"), "a").close()
    if not os.path.exists(custom_tools_file):
        with open(custom_tools_file, "w") as f:
            json.dump([], f)

    def _load_custom_tools():
        try:
            if os.path.exists(custom_tools_file):
                with open(custom_tools_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading custom tools: {e}")
            return []

    def _save_custom_tools(tools: list):
        with open(custom_tools_file, "w") as f:
            json.dump(tools, f, indent=2)

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the main page."""
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/api/models")
    async def get_models():
        """Get available LLM models."""
        models = []
        
        # Check Google API key and add Gemini models if available
        google_api_available = check_google_api_key()
        if google_api_available:
            models.extend([
                {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google", "status": "available"},
                {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google", "status": "available"},
                {"id": "gemini-2.0-flash-001", "name": "Gemini 2.0 Flash", "provider": "google", "status": "available"},
                {"id": "gemini-2.0-pro-001", "name": "Gemini 2.0 Pro", "provider": "google", "status": "available"},
            ])
        else:
            # Add models but mark as unavailable
            models.extend([
                {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google", "status": "unavailable", "reason": "API key not configured or invalid"},
                {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google", "status": "unavailable", "reason": "API key not configured or invalid"},
                {"id": "gemini-2.0-flash-001", "name": "Gemini 2.0 Flash", "provider": "google", "status": "unavailable", "reason": "API key not configured or invalid"},
                {"id": "gemini-2.0-pro-001", "name": "Gemini 2.0 Pro", "provider": "google", "status": "unavailable", "reason": "API key not configured or invalid"},
            ])
        
        # Add Ollama models if available
        if OLLAMA_AVAILABLE:
            try:
                ollama_models = list_ollama_models()
                if ollama_models:
                    models.extend(ollama_models)
                else:
                    # Fallback to default Ollama models
                    models.extend([
                        {"id": "llama3:8b", "name": "Llama 3 (8B)", "provider": "ollama", "status": "available"},
                        {"id": "llama3:70b", "name": "Llama 3 (70B)", "provider": "ollama", "status": "available"},
                        {"id": "mistral", "name": "Mistral", "provider": "ollama", "status": "available"},
                        {"id": "mixtral", "name": "Mixtral", "provider": "ollama", "status": "available"},
                        {"id": "phi3", "name": "Phi-3", "provider": "ollama", "status": "available"},
                        {"id": "gemma:7b", "name": "Gemma (7B)", "provider": "ollama", "status": "available"},
                        {"id": "gemma:2b", "name": "Gemma (2B)", "provider": "ollama", "status": "available"},
                        {"id": "codellama", "name": "Code Llama", "provider": "ollama", "status": "available"},
                    ])
            except Exception as e:
                print(f"Error fetching Ollama models: {e}")
        
        return {"models": models, "google_api_available": google_api_available}

    @app.get("/api/config")
    async def get_config():
        """Get application configuration and API key status."""
        return {
            "google_api_key_configured": bool(GOOGLE_API_KEY),
            "google_api_available": check_google_api_key(),
            "ollama_available": OLLAMA_AVAILABLE,
            "api_base_urls": {
                "google": GOOGLE_API_BASE_URL,
                "ollama": "http://localhost:11434" if OLLAMA_AVAILABLE else None
            }
        }

    @app.get("/api/tools")
    async def get_tools():
        """Get built-in and custom tools."""
        built_in = [
            {"id": "google_search", "name": "Google Search", "description": "Search the web using Google"},
            {"id": "load_web_page", "name": "Load Web Page", "description": "Load and extract content from a web page"},
            {"id": "built_in_code_execution", "name": "Code Execution", "description": "Execute Python code"},
            {"id": "get_user_choice", "name": "User Choice", "description": "Ask the user to make a choice"},
        ]
        try:
            custom_tools = _load_custom_tools()
            return {"tools": built_in + custom_tools}
        except Exception as e:
            print(f"Error in get_tools: {e}")
            return {"tools": built_in}

    @app.get("/api/templates")
    async def get_templates():
        """Get agent templates."""
        return {
            "templates": [
                {
                    "id": "search_assistant",
                    "name": "Search Assistant",
                    "description": "An assistant that can search the web",
                    "config": {
                        "name": "search_assistant",
                        "model": "gemini-2.0-flash-001",
                        "provider": "google",
                        "instruction": "You are a helpful assistant. Answer user questions using Google Search when needed.",
                        "description": "An assistant that can search the web.",
                        "tools": ["google_search"],
                        "generate_api": True
                    }
                },
                {
                    "id": "code_assistant",
                    "name": "Code Assistant",
                    "description": "An assistant that can write and execute code",
                    "config": {
                        "name": "code_assistant",
                        "model": "gemini-2.0-pro-001",
                        "provider": "google",
                        "instruction": "You are a helpful coding assistant. Help users write and execute Python code.",
                        "description": "An assistant that can write and execute code.",
                        "tools": ["built_in_code_execution"],
                        "generate_api": True
                    }
                },
                {
                    "id": "multi_agent",
                    "name": "Multi-Agent System",
                    "description": "A system with multiple specialized agents",
                    "config": {
                        "name": "multi_agent_system",
                        "model": "gemini-2.0-pro-001",
                        "provider": "google",
                        "instruction": "You are a coordinator for multiple specialized agents. Delegate tasks to the appropriate agent.",
                        "description": "A multi-agent system with specialized agents.",
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
                },
                {
                    "id": "ollama_assistant",
                    "name": "Ollama Local Assistant",
                    "description": "An assistant that runs locally using Ollama",
                    "config": {
                        "name": "ollama_assistant",
                        "model": "llama3:8b",
                        "provider": "ollama",
                        "ollama_base_url": "http://localhost:11434",
                        "instruction": "You are a helpful assistant running locally on the user's machine using Ollama.",
                        "description": "A local assistant powered by Ollama.",
                        "tools": [],
                        "generate_api": True
                    }
                }
            ]
        }

    @app.get("/api/agents")
    async def list_agents():
        """List all created agents."""
        if not os.path.exists(agents_dir):
            return {"agents": []}
        
        agents = []
        for agent_dir in os.listdir(agents_dir):
            agent_path = os.path.join(agents_dir, agent_dir)
            if os.path.isdir(agent_path) and os.path.exists(os.path.join(agent_path, "agent.py")):
                agents.append({
                    "id": agent_dir,
                    "name": agent_dir,
                    "path": agent_path
                })
        
        return {"agents": agents}

    @app.get("/api/agents/{agent_id}")
    async def get_agent(agent_id: str):
        """Get agent details."""
        agent_path = os.path.join(agents_dir, agent_id)
        
        if not os.path.exists(agent_path) or not os.path.exists(os.path.join(agent_path, "agent.py")):
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        # Read agent.py to extract configuration
        try:
            with open(os.path.join(agent_path, "agent.py"), "r") as f:
                agent_code = f.read()
            
            # Read config.json if it exists
            config_path = os.path.join(agent_path, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                config = {
                    "name": agent_id,
                    "model": "unknown",
                    "instruction": "Unknown instruction",
                    "description": "",
                    "tools": []
                }
            
            # Check if API is available
            api_available = os.path.exists(os.path.join(agent_path, "api.py"))
            
            # Get Google ADK status if available
            adk_status = None
            if GOOGLE_ADK_AVAILABLE and config.get('provider') == 'google':
                try:
                    google_adk = get_google_adk_integration()
                    adk_status = google_adk.get_agent_status(agent_id)
                except Exception as e:
                    adk_status = {"status": "error", "error": str(e)}
            
            return {
                "id": agent_id,
                "name": agent_id,
                "path": agent_path,
                "code": agent_code,
                "config": config,
                "api_available": api_available,
                "adk_status": adk_status
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read agent: {str(e)}")
    
    @app.get("/api/agents/{agent_id}/status")
    async def get_agent_status(agent_id: str):
        """Get agent status and tools information."""
        try:
            # Check if agent exists
            agent_path = os.path.join(agents_dir, agent_id)
            if not os.path.exists(agent_path):
                raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
            
            # Load agent configuration
            config_path = os.path.join(agent_path, "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
            else:
                raise HTTPException(status_code=404, detail=f"Agent configuration not found")
            
            # Get Google ADK status if available
            adk_status = None
            tools_info = []
            
            if GOOGLE_ADK_AVAILABLE and config.get('provider') == 'google':
                try:
                    google_adk = get_google_adk_integration()
                    adk_status = google_adk.get_agent_status(agent_id)
                    
                    # Get tools information
                    if config.get('tools'):
                        for tool_id in config['tools']:
                            tool_info = {
                                "id": tool_id,
                                "name": tool_id.replace('_', ' ').title(),
                                "description": f"Tool: {tool_id}",
                                "status": "available"
                            }
                            tools_info.append(tool_info)
                except Exception as e:
                    adk_status = {"status": "error", "error": str(e)}
            
            return {
                "agent_id": agent_id,
                "name": config.get('name', agent_id),
                "provider": config.get('provider', 'unknown'),
                "model": config.get('model', 'unknown'),
                "adk_status": adk_status,
                "tools": tools_info,
                "tools_count": len(tools_info)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")

    @app.post("/api/agents")
    async def create_agent(agent_config: AgentConfig):
        """Create a new agent from configuration."""
        agent_path = os.path.join(agents_dir, agent_config.name)
        
        if os.path.exists(agent_path):
            raise HTTPException(status_code=400, detail=f"Agent '{agent_config.name}' already exists")
        
        try:
            # Create agent directory
            os.makedirs(agent_path)
            
            # Generate __init__.py
            with open(os.path.join(agent_path, "__init__.py"), "w") as f:
                f.write(f"# {agent_config.name}\nfrom . import agent\n")
            
            # Generate agent.py
            with open(os.path.join(agent_path, "agent.py"), "w") as f:
                if agent_config.provider == "ollama" and OLLAMA_AVAILABLE:
                    # Use Ollama-specific code generator
                    from .ollama_integration import OllamaAgentConfig
                    ollama_config = OllamaAgentConfig(
                        name=agent_config.name,
                        model=agent_config.model,
                        base_url=agent_config.ollama_base_url,
                        instruction=agent_config.instruction,
                        description=agent_config.description,
                        tools=agent_config.tools,
                        temperature=agent_config.temperature
                    )
                    f.write(generate_ollama_agent_code(ollama_config))
                else:
                    # Use standard code generator
                    f.write(generate_agent_code(agent_config))
            
            # Generate API wrapper if requested
            if agent_config.generate_api:
                with open(os.path.join(agent_path, "api.py"), "w") as f:
                    f.write(generate_api_code(agent_config))
                
                # Generate TypeScript client
                ts_dir = os.path.join(agent_path, "clients", "typescript")
                os.makedirs(ts_dir, exist_ok=True)
                with open(os.path.join(ts_dir, "agent-client.ts"), "w") as f:
                    f.write(generate_typescript_client(agent_config))
                
                # Generate JavaScript client
                js_dir = os.path.join(agent_path, "clients", "javascript")
                os.makedirs(js_dir, exist_ok=True)
                with open(os.path.join(js_dir, "agent-client.js"), "w") as f:
                    f.write(generate_javascript_client(agent_config))
                
                # Generate README with usage instructions
                with open(os.path.join(agent_path, "README.md"), "w") as f:
                    f.write(generate_readme(agent_config))
            
            # Save config.json
            with open(os.path.join(agent_path, "config.json"), "w") as f:
                f.write(agent_config.model_dump_json(indent=2))
            
            # Create Google ADK agent if provider is Google and ADK is available
            if agent_config.provider == "google" and GOOGLE_ADK_AVAILABLE:
                try:
                    google_adk = get_google_adk_integration()
                    google_adk_config = GoogleADKAgentConfig(
                        name=agent_config.name,
                        model=agent_config.model,
                        instruction=agent_config.instruction,
                        description=agent_config.description,
                        tools=agent_config.tools,
                        temperature=agent_config.temperature
                    )
                    google_adk.create_agent(google_adk_config)
                    print(f"Created Google ADK agent: {agent_config.name}")
                except Exception as e:
                    print(f"Warning: Failed to create Google ADK agent: {e}")
            
            return {"message": f"Agent '{agent_config.name}' created successfully", "path": agent_path}
        except Exception as e:
            # Clean up if there was an error
            if os.path.exists(agent_path):
                import shutil
                shutil.rmtree(agent_path)
            raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

    @app.delete("/api/agents/{agent_id}")
    async def delete_agent(agent_id: str):
        """Delete an agent."""
        agent_path = os.path.join(agents_dir, agent_id)
        
        if not os.path.exists(agent_path):
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        try:
            # Delete agent directory
            import shutil
            shutil.rmtree(agent_path)
            
            return {"message": f"Agent '{agent_id}' deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

    @app.post("/api/run/{agent_id}")
    async def run_agent(agent_id: str):
        """Run an agent using the ADK CLI."""
        agent_path = os.path.join(agents_dir, agent_id)
        
        if not os.path.exists(agent_path) or not os.path.exists(os.path.join(agent_path, "agent.py")):
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        try:
            # Check if API is available
            api_available = os.path.exists(os.path.join(agent_path, "api.py"))
            
            if api_available:
                return {
                    "message": f"Agent '{agent_id}' launched",
                    "command": f"python {os.path.join(agent_path, 'api.py')}",
                    "url": f"http://localhost:8000/docs"
                }
            else:
                # This would launch the ADK web UI for the agent
                return {
                    "message": f"Agent '{agent_id}' launched",
                    "command": f"adk web {os.path.dirname(agent_path)}",
                    "url": f"http://localhost:8000/dev-ui"
                }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to run agent: {str(e)}")

    # Chat functionality
    class ChatMessage(BaseModel):
        message: str
        agent_id: str

    @app.post("/api/chat/{agent_id}")
    async def chat_with_agent(agent_id: str, chat_message: ChatMessage):
        """Chat with a specific agent."""
        agent_path = os.path.join(agents_dir, agent_id)
        
        if not os.path.exists(agent_path) or not os.path.exists(os.path.join(agent_path, "agent.py")):
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        try:
            # Load agent configuration
            agent_config_file = os.path.join(agent_path, "config.json")
            if os.path.exists(agent_config_file):
                with open(agent_config_file, 'r') as f:
                    agent_config = json.load(f)
            else:
                # Fallback to basic agent info
                agent_config = {"name": agent_id, "model": "unknown", "provider": "unknown"}
            
            # Try to use Google ADK first if available and provider is Google
            if agent_config.get('provider') == 'google' and GOOGLE_ADK_AVAILABLE:
                try:
                    google_adk = get_google_adk_integration()
                    response = await google_adk.run_agent(agent_id, chat_message.message)
                    print(f"Google ADK agent response: {response}")
                except Exception as adk_error:
                    print(f"Google ADK execution failed: {adk_error}")
                    # Fall back to file-based execution
                    response = None
            else:
                response = None
            
            # Fall back to file-based execution if Google ADK failed or not available
            if response is None:
                try:
                    # Add the agent directory to Python path
                    sys.path.insert(0, agent_path)
                    
                    # Import the agent module
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("agent", os.path.join(agent_path, "agent.py"))
                    agent_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(agent_module)
                    
                    # Get the root agent
                    if hasattr(agent_module, 'root_agent'):
                        agent = agent_module.root_agent
                    else:
                        raise Exception("No root_agent found in agent module")
                    
                    # Run the agent with the user's message
                    if hasattr(agent, 'generate_content'):
                        # Use the generate_content method (primary method)
                        result = await agent.generate_content(chat_message.message)
                        response = result.text if hasattr(result, 'text') else str(result)
                    elif hasattr(agent, 'chat'):
                        # Use the chat method if available
                        result = await agent.chat(chat_message.message)
                        response = str(result)
                    elif hasattr(agent, 'run'):
                        # Use the run method if available
                        result = await agent.run(chat_message.message)
                        response = str(result)
                    else:
                        raise Exception("Agent has no generate_content, chat, or run method")
                    
                except Exception as agent_error:
                    # If agent execution fails, provide a helpful error message
                    response = f"I'm {agent_config.get('name', agent_id)}, but I encountered an error while processing your message: '{chat_message.message}'. Error: {str(agent_error)}. Please check my configuration and try again."
                    print(f"Agent execution error: {agent_error}")
            
            return {
                "response": response,
                "agent_id": agent_id,
                "agent_name": agent_config.get('name', agent_id),
                "timestamp": str(datetime.datetime.now())
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to chat with agent: {str(e)}")

    
    # Custom Tools Support
    class CustomTool(BaseModel):
        id: str
        name: str
        description: str
        code: str | None = None
        parameters: dict | None = None
        return_type: str | None = None
        examples: list | None = None

    @app.get("/api/custom_tools")
    async def list_custom_tools():
        """List user-defined custom tools."""
        return {"tools": _load_custom_tools()}

    @app.post("/api/custom_tools")
    async def create_custom_tool(tool: CustomTool):
        """Create a new custom tool."""
        tools = _load_custom_tools()
        if any(t["id"] == tool.id for t in tools):
            raise HTTPException(status_code=400, detail=f"Tool '{tool.id}' already exists")
        tools.append(tool.model_dump())
        _save_custom_tools(tools)
        if tool.code:
            mod_path = os.path.join(custom_tools_dir, f"{tool.id}.py")
            with open(mod_path, "w") as f:
                f.write(tool.code)
        return {"message": f"Tool '{tool.id}' created"}

    @app.get("/api/function_tools")
    async def get_function_tools():
        """Get function tool templates and examples."""
        return {
            "templates": [
                {
                    "id": "calculator",
                    "name": "Calculator Tool",
                    "description": "A simple calculator that can perform basic arithmetic operations",
                    "code": """def calculator(operation: str, a: float, b: float) -> float:
    \"\"\"Perform basic arithmetic operations.
    
    Args:
        operation: The operation to perform ('add', 'subtract', 'multiply', 'divide')
        a: First number
        b: Second number
    
    Returns:
        The result of the operation
    \"\"\"
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    elif operation == 'multiply':
        return a * b
    elif operation == 'divide':
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")""",
                    "parameters": {
                        "operation": {"type": "string", "description": "Arithmetic operation", "enum": ["add", "subtract", "multiply", "divide"]},
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "return_type": "number",
                    "examples": [
                        {"input": {"operation": "add", "a": 5, "b": 3}, "output": 8},
                        {"input": {"operation": "multiply", "a": 4, "b": 7}, "output": 28}
                    ]
                },
                {
                    "id": "text_processor",
                    "name": "Text Processor Tool",
                    "description": "Process and analyze text content",
                    "code": """def text_processor(text: str, operation: str) -> str:
    \"\"\"Process text using various operations.
    
    Args:
        text: Input text to process
        operation: The operation to perform ('uppercase', 'lowercase', 'count_words', 'reverse')
    
    Returns:
        Processed text or analysis result
    \"\"\"
    if operation == 'uppercase':
        return text.upper()
    elif operation == 'lowercase':
        return text.lower()
    elif operation == 'count_words':
        return str(len(text.split()))
    elif operation == 'reverse':
        return text[::-1]
    else:
        raise ValueError(f"Unknown operation: {operation}")""",
                    "parameters": {
                        "text": {"type": "string", "description": "Input text to process"},
                        "operation": {"type": "string", "description": "Text processing operation", "enum": ["uppercase", "lowercase", "count_words", "reverse"]}
                    },
                    "return_type": "string",
                    "examples": [
                        {"input": {"text": "Hello World", "operation": "uppercase"}, "output": "HELLO WORLD"},
                        {"input": {"text": "Python Programming", "operation": "count_words"}, "output": "2"}
                    ]
                }
            ]
        }
    
    @app.post("/api/test_tool")
    async def test_tool(request: Request):
        """Test a specific tool with parameters."""
        try:
            data = await request.json()
            tool_id = data.get('tool_id')
            parameters = data.get('parameters', {})
            
            if not tool_id:
                raise HTTPException(status_code=400, detail="tool_id is required")
            
            # Test the tool using Google ADK if available
            if GOOGLE_ADK_AVAILABLE:
                try:
                    google_adk = get_google_adk_integration()
                    tool = google_adk._create_tool(tool_id)
                    
                    if tool:
                        # Execute the tool with parameters
                        if hasattr(tool, 'function'):
                            result = tool.function(**parameters)
                            return {
                                "tool_id": tool_id,
                                "parameters": parameters,
                                "result": result,
                                "status": "success"
                            }
                        else:
                            raise HTTPException(status_code=500, detail="Tool function not accessible")
                    else:
                        raise HTTPException(status_code=404, detail=f"Tool {tool_id} not found")
                        
                except Exception as e:
                    return {
                        "tool_id": tool_id,
                        "parameters": parameters,
                        "error": str(e),
                        "status": "error"
                    }
            else:
                raise HTTPException(status_code=503, detail="Google ADK not available")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to test tool: {str(e)}")
    
    return app

def generate_agent_code(agent_config: AgentConfig) -> str:
    """Generate agent.py code from configuration."""
    imports = [
        "import sys, pathlib, os",
        "sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent / 'custom_tools'))",
        "from google.adk.agents import Agent",
        "from google.genai import types",
        "import asyncio",
    ]
    
    # Add tool imports
    if agent_config.tools:
        tool_imports = set()
        for tool_id in agent_config.tools:
            if tool_id == "google_search":
                tool_imports.add("from google.adk.tools import google_search")
            elif tool_id == "load_web_page":
                tool_imports.add("from google.adk.tools import load_web_page")
            elif tool_id == "built_in_code_execution":
                tool_imports.add("from google.adk.tools import built_in_code_execution")
            elif tool_id == "get_user_choice":
                tool_imports.add("from google.adk.tools import get_user_choice")
            else:
                tool_imports.add(f"from custom_tools.{tool_id} import {tool_id}")  # Custom tool fallback import
        
        imports.extend(sorted(tool_imports))
    
    # Generate sub-agent code
    sub_agent_code = ""
    sub_agent_names = []
    
    if agent_config.sub_agents:
        for sub_agent in agent_config.sub_agents:
            sub_agent_names.append(sub_agent.name)
            sub_agent_code += f"""
{sub_agent.name} = Agent(
    model="{sub_agent.model}",
    name="{sub_agent.name}",
    description="{sub_agent.description or ''}",
    instruction=\"\"\"
{sub_agent.instruction}
\"\"\",
"""
            
            if sub_agent.tools:
                sub_agent_code += "    tools=[\n"
                for tool_id in sub_agent.tools:
                    sub_agent_code += f"        {tool_id},\n"
                sub_agent_code += "    ],\n"
            
            sub_agent_code += ")\n\n"
    
    # Generate root agent code
    root_agent_code = f"""
root_agent = Agent(
    model="{agent_config.model}",
    name="{agent_config.name}",
    description="{agent_config.description or ''}",
    instruction=\"\"\"
{agent_config.instruction}
\"\"\",
"""
    
    if agent_config.tools:
        root_agent_code += "    tools=[\n"
        for tool_id in agent_config.tools:
            root_agent_code += f"        {tool_id},\n"
        root_agent_code += "    ],\n"
    
    if sub_agent_names:
        root_agent_code += "    sub_agents=[\n"
        for name in sub_agent_names:
            root_agent_code += f"        {name},\n"
        root_agent_code += "    ],\n"
    
    if agent_config.flow:
        root_agent_code += f'    flow="{agent_config.flow}",\n'
    
    if agent_config.temperature is not None:
        root_agent_code += f"""    generate_content_config=types.GenerateContentConfig(
        temperature={agent_config.temperature},
    ),\n"""
    
    root_agent_code += ")\n"
    
    # Combine all code
    code = "\n".join(imports) + "\n\n" + sub_agent_code + root_agent_code
    
    # Add main execution block for testing
    code += f"""

# Main execution block for testing
if __name__ == "__main__":
    async def main():
        # Test the agent
        try:
            result = await root_agent.generate_content("Hello, how are you?")
            print(f"Agent response: {{result.text if hasattr(result, 'text') else result}}")
        except Exception as e:
            print(f"Error running agent: {{e}}")
    
    # Run the async main function
    asyncio.run(main())
"""
    
    return code

def generate_api_code(agent_config: AgentConfig) -> str:
    """Generate API wrapper code for the agent."""
    port = agent_config.api_port or 8000
    
    code = f"""import os
import sys
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Import the agent
from . import agent

class GenerateRequest(BaseModel):
    prompt: str
    temperature: Optional[float] = None

class GenerateResponse(BaseModel):
    text: str

app = FastAPI(title="{agent_config.name} API", description="{agent_config.description or 'Agent API'}")

@app.get("/")
async def root():
    return {{"message": "Welcome to the {agent_config.name} API"}}

@app.post("/api/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    try:
        response = await agent.root_agent.generate_content(request.prompt)
        return {{"text": response.text}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print(f"Starting {agent_config.name} API on http://localhost:{port}")
    print(f"API documentation available at http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port={port})
"""
    return code

def generate_typescript_client(agent_config: AgentConfig) -> str:
    """Generate TypeScript client for the agent API."""
    port = agent_config.api_port or 8000
    
    code = f"""/**
 * TypeScript client for {agent_config.name} API
 */

export interface GenerateRequest {{
  prompt: string;
  temperature?: number;
}}

export interface GenerateResponse {{
  text: string;
}}

export class AgentClient {{
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:{port}') {{
    this.baseUrl = baseUrl;
  }}

  /**
   * Generate content using the agent
   * @param prompt The prompt to send to the agent
   * @param temperature Optional temperature parameter
   * @returns The generated text
   */
  async generateContent(prompt: string, temperature?: number): Promise<GenerateResponse> {{
    const request: GenerateRequest = {{
      prompt,
      ...(temperature !== undefined && {{ temperature }})
    }};

    const response = await fetch(`${{this.baseUrl}}/api/generate`, {{
      method: 'POST',
      headers: {{
        'Content-Type': 'application/json',
      }},
      body: JSON.stringify(request),
    }});

    if (!response.ok) {{
      const error = await response.json();
      throw new Error(`API error: ${{error.detail || response.statusText}}`);
    }}

    return await response.json();
  }}
}}
"""
    return code

def generate_javascript_client(agent_config: AgentConfig) -> str:
    """Generate JavaScript client for the agent API."""
    port = agent_config.api_port or 8000
    
    code = f"""/**
 * JavaScript client for {agent_config.name} API
 */

class AgentClient {{
  /**
   * Create a new AgentClient
   * @param {{string}} baseUrl - The base URL of the agent API
   */
  constructor(baseUrl = 'http://localhost:{port}') {{
    this.baseUrl = baseUrl;
  }}

  /**
   * Generate content using the agent
   * @param {{string}} prompt - The prompt to send to the agent
   * @param {{number|undefined}} temperature - Optional temperature parameter
   * @returns {{Promise<{{text: string}}>}} The generated text
   */
  async generateContent(prompt, temperature) {{
    const request = {{
      prompt,
      ...(temperature !== undefined && {{ temperature }})
    }};

    const response = await fetch(`${{this.baseUrl}}/api/generate`, {{
      method: 'POST',
      headers: {{
        'Content-Type': 'application/json',
      }},
      body: JSON.stringify(request),
    }});

    if (!response.ok) {{
      const error = await response.json();
      throw new Error(`API error: ${{error.detail || response.statusText}}`);
    }}

    return await response.json();
  }}
}}

// For CommonJS environments
if (typeof module !== 'undefined' && module.exports) {{
  module.exports = {{ AgentClient }};
}}
"""
    return code

def generate_readme(agent_config: AgentConfig) -> str:
    """Generate README with usage instructions."""
    port = agent_config.api_port or 8000
    
    readme = f"""# {agent_config.name}

{agent_config.description or 'An AI agent created with the No-Code ADK.'}

## Running the Agent

### As a Python Module

```python
from {agent_config.name} import root_agent

async def main():
    response = await root_agent.generate_content("Hello, agent!")
    print(response.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### As an API

Start the API server:

```bash
python {agent_config.name}/api.py
```

The API will be available at http://localhost:{port} with documentation at http://localhost:{port}/docs.

## Using in Different Tech Stacks

### Python

```python
import requests

response = requests.post(
    "http://localhost:{port}/api/generate",
    json={{"prompt": "Hello, agent!"}}
)
print(response.json()["text"])
```

### Node.js/TypeScript

```typescript
// TypeScript
import {{ AgentClient }} from './{agent_config.name}/clients/typescript/agent-client';

async function main() {{
  const agent = new AgentClient('http://localhost:{port}');
  const response = await agent.generateContent('Hello, agent!');
  console.log(response.text);
}}

main().catch(console.error);
```

### JavaScript

```javascript
// JavaScript
const {{ AgentClient }} = require('./{agent_config.name}/clients/javascript/agent-client');

async function main() {{
  const agent = new AgentClient('http://localhost:{port}');
  const response = await agent.generateContent('Hello, agent!');
  console.log(response.text);
}}

main().catch(console.error);
```

### Other Languages

You can use the REST API directly from any language that can make HTTP requests:

```
POST http://localhost:{port}/api/generate
Content-Type: application/json

{{
  "prompt": "Hello, agent!"
}}
```
"""
    return readme
