"""Ollama integration for the No-Code ADK Interface."""

import os
import json
import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class OllamaAgentConfig(BaseModel):
    """Configuration for an Ollama agent."""
    
    name: str
    model: str
    base_url: str = "http://localhost:11434"
    instruction: str
    description: Optional[str] = None
    tools: Optional[List[str]] = None
    temperature: Optional[float] = 0.2

def generate_ollama_agent_code(agent_config: OllamaAgentConfig) -> str:
    """Generate agent.py code for an Ollama agent."""
    imports = [
        "import os",
        "import requests",
        "from google.adk.agents import Agent",
        "from google.adk.agents.agent_utils import AgentResponse",
        "from typing import Dict, List, Any, Optional",
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
    
    # Generate agent code
    code = "\n".join(imports) + "\n\n"
    
    # Add custom Ollama agent class
    code += f"""
# Custom Ollama Agent implementation
class OllamaAgent(Agent):
    def __init__(self, model, name, description, instruction, tools=None, sub_agents=None, flow="auto", temperature=0.2):
        self.model = model
        self.name = name
        self.description = description
        self.instruction = instruction
        self.tools = tools or []
        self.sub_agents = sub_agents or []
        self.flow = flow
        self.temperature = temperature
        self.ollama_base_url = "{agent_config.base_url}"
        
    async def generate_content(self, prompt, **kwargs):
        \"\"\"Generate content using Ollama API.\"\"\"
        url = f"{{self.ollama_base_url}}/api/generate"
        
        payload = {{
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False
        }}
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return AgentResponse(text=result.get("response", ""))

# Create the agent instance
root_agent = OllamaAgent(
    model="{agent_config.model}",
    name="{agent_config.name}",
    description="{agent_config.description or ''}",
    instruction=\"\"\"
{agent_config.instruction}
\"\"\",
"""
    
    # Add tools
    if agent_config.tools:
        code += "    tools=[\n"
        for tool_id in agent_config.tools:
            code += f"        {tool_id},\n"
        code += "    ],\n"
    
    # Add temperature
    if agent_config.temperature is not None:
        code += f"    temperature={agent_config.temperature},\n"
    
    # Close the agent instantiation
    code += ")\n"
    
    return code

def check_ollama_availability(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is available at the given URL."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def list_ollama_models(base_url: str = "http://localhost:11434") -> List[Dict[str, str]]:
    """List available Ollama models."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append({
                    "id": model["name"],
                    "name": model["name"],
                    "provider": "ollama"
                })
            return models
        return []
    except:
        return []
