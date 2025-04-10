import os
import json
import uvicorn
import requests
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import Ollama integration
try:
    from .ollama_integration import generate_ollama_agent_code, check_ollama_availability, list_ollama_models
    OLLAMA_AVAILABLE = check_ollama_availability()
except ImportError:
    OLLAMA_AVAILABLE = False

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

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        """Serve the main page."""
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/api/models")
    async def get_models():
        """Get available LLM models."""
        models = [
            # Google Gemini models
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google"},
            {"id": "gemini-2.0-flash-001", "name": "Gemini 2.0 Flash", "provider": "google"},
            {"id": "gemini-2.0-pro-001", "name": "Gemini 2.0 Pro", "provider": "google"},
        ]
        
        # Add Ollama models if available
        if OLLAMA_AVAILABLE:
            try:
                ollama_models = list_ollama_models()
                if ollama_models:
                    models.extend(ollama_models)
                else:
                    # Fallback to default Ollama models
                    models.extend([
                        {"id": "llama3:8b", "name": "Llama 3 (8B)", "provider": "ollama"},
                        {"id": "llama3:70b", "name": "Llama 3 (70B)", "provider": "ollama"},
                        {"id": "mistral", "name": "Mistral", "provider": "ollama"},
                        {"id": "mixtral", "name": "Mixtral", "provider": "ollama"},
                        {"id": "phi3", "name": "Phi-3", "provider": "ollama"},
                        {"id": "gemma:7b", "name": "Gemma (7B)", "provider": "ollama"},
                        {"id": "gemma:2b", "name": "Gemma (2B)", "provider": "ollama"},
                        {"id": "codellama", "name": "Code Llama", "provider": "ollama"},
                    ])
            except Exception as e:
                print(f"Error fetching Ollama models: {e}")
        
        return {"models": models}

    @app.get("/api/tools")
    async def get_tools():
        """Get available tools."""
        return {
            "tools": [
                {"id": "google_search", "name": "Google Search", "description": "Search the web using Google"},
                {"id": "load_web_page", "name": "Load Web Page", "description": "Load and extract content from a web page"},
                {"id": "built_in_code_execution", "name": "Code Execution", "description": "Execute Python code"},
                {"id": "get_user_choice", "name": "User Choice", "description": "Ask the user to make a choice"},
            ]
        }

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
            
            return {
                "id": agent_id,
                "name": agent_id,
                "path": agent_path,
                "code": agent_code,
                "config": config,
                "api_available": api_available
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read agent: {str(e)}")

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
                f.write(agent_config.json(indent=2))
            
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

    return app

def generate_agent_code(agent_config: AgentConfig) -> str:
    """Generate agent.py code from configuration."""
    imports = [
        "from google.adk.agents import Agent",
        "from google.genai import types",
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
