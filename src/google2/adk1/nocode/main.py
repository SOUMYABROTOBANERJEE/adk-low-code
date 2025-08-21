"""
Main FastAPI application for the Google ADK No-Code Platform
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from pydantic import ValidationError

from .models import (
    AgentConfiguration, AgentUpdateRequest, ToolDefinition, SubAgent, AgentType, ToolType,
    ChatMessage, ChatSession, AgentExecutionResult, ProjectConfiguration,
    LoginRequest, RegisterRequest, AuthResponse
)
from .adk_service import ADKService
from .database import DatabaseManager
from .auth_service import AuthService
from .langfuse_service import LangfuseService

# Initialize FastAPI app
app = FastAPI(
    title="Google ADK No-Code Platform",
    description="A visual platform for building and testing Google ADK agents",
    version="1.0.0"
)

# Initialize services
db_manager = DatabaseManager()
adk_service = ADKService(db_manager)
auth_service = AuthService(db_manager)
langfuse_service = LangfuseService()

# Get the directory of this file
current_dir = Path(__file__).parent

# Mount static files
app.mount("/static", StaticFiles(directory=str(current_dir / "static")), name="static")

# Templates
templates = Jinja2Templates(directory=str(current_dir / "templates"))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "adk_available": adk_service.is_available(),
        "langfuse_available": langfuse_service.is_langfuse_available(),
        "timestamp": datetime.now().isoformat()
    }


# Authentication Endpoints
@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(request: RegisterRequest, req: Request):
    """Register a new user"""
    try:
        # Get client IP and user agent
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # Register user
        response = auth_service.register_user(request)
        
        # Trace user registration
        if response.success and response.user:
            langfuse_service.trace_user_action(
                user_id=response.user.id,
                action="user_registration",
                details={
                    "email": request.email,
                    "ip_address": client_ip,
                    "user_agent": user_agent
                }
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(request: LoginRequest, req: Request):
    """Authenticate user and create session"""
    try:
        # Get client IP and user agent
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # Login user
        response = auth_service.login_user(request, user_agent, client_ip)
        
        # Trace user login
        if response.success and response.user:
            langfuse_service.trace_user_action(
                user_id=response.user.id,
                action="user_login",
                details={
                    "email": request.email,
                    "ip_address": client_ip,
                    "user_agent": user_agent
                }
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
async def logout_user(session_token: str):
    """Logout user by invalidating session"""
    try:
        success = auth_service.logout_user(session_token)
        if success:
            return {"success": True, "message": "Logged out successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid session token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_current_user(session_token: str):
    """Get current user information from session"""
    try:
        user = auth_service.get_user_by_session(session_token)
        if user:
            return {"success": True, "user": user.model_dump()}
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Tool Management Endpoints
@app.post("/api/tools")
async def create_tool(tool: ToolDefinition):
    """Create a new tool"""
    try:
        tool.id = tool.id or str(uuid.uuid4())
        
        # Register tool in ADK service
        if adk_service.register_tool(tool):
            # Save to database
            tool_data = tool.model_dump()
            if db_manager.save_tool(tool_data):
                return {"success": True, "tool": tool_data}
            else:
                raise HTTPException(status_code=500, detail="Failed to save tool to database")
        else:
            raise HTTPException(status_code=400, detail="Failed to register tool in ADK service")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools")
async def list_tools():
    """List all tools"""
    try:
        # Get custom tools from database
        custom_tools = db_manager.get_all_tools()
        
        # Get built-in tools from ADK service
        builtin_tools = adk_service.get_builtin_tools() if adk_service.is_available() else []
        
        # Combine both types of tools
        all_tools = custom_tools + builtin_tools
        
        return {"tools": all_tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tools/{tool_id}")
async def get_tool(tool_id: str):
    """Get a specific tool"""
    try:
        tool = db_manager.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/tools/{tool_id}")
async def update_tool(tool_id: str, tool: ToolDefinition):
    """Update an existing tool"""
    try:
        # Check if tool exists
        existing_tool = db_manager.get_tool(tool_id)
        if not existing_tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        tool.id = tool_id
        
        # Re-register tool in ADK service
        if adk_service.register_tool(tool):
            # Update in database
            tool_data = tool.model_dump()
            if db_manager.save_tool(tool_data):
                return {"success": True, "tool": tool_data}
            else:
                raise HTTPException(status_code=500, detail="Failed to update tool in database")
        else:
            raise HTTPException(status_code=400, detail="Failed to register updated tool")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a tool"""
    try:
        if db_manager.delete_tool(tool_id):
            return {"success": True, "message": "Tool deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete tool")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Agent Management Endpoints
@app.post("/api/agents")
async def create_agent(agent: AgentConfiguration):
    """Create a new agent"""
    try:
        agent.id = agent.id or str(uuid.uuid4())
        agent.created_at = datetime.now().isoformat()
        agent.updated_at = datetime.now().isoformat()
        
        # Register agent in ADK service
        if adk_service.register_agent(agent):
            # Save to database
            agent_data = agent.model_dump()
            if db_manager.save_agent(agent_data):
                return {"success": True, "agent": agent_data}
            else:
                raise HTTPException(status_code=500, detail="Failed to save agent to database")
        else:
            raise HTTPException(status_code=400, detail="Failed to register agent in ADK service")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents")
async def list_agents():
    """List all agents"""
    try:
        agents = db_manager.get_all_agents()
        return {"agents": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent"""
    try:
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/agents/{agent_id}")
async def update_agent(agent_id: str, agent_update: AgentUpdateRequest):
    """Update an agent"""
    try:
        # Check if agent exists
        existing_agent = db_manager.get_agent(agent_id)
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update fields from the request
        updated_agent = AgentConfiguration(
            id=agent_id,
            name=agent_update.name,
            description=agent_update.description,
            agent_type=agent_update.agent_type,
            system_prompt=agent_update.system_prompt,
            instructions=agent_update.instructions,
            sub_agents=agent_update.sub_agents,
            tools=agent_update.tools,
            model_settings=agent_update.model_settings,
            workflow_config=agent_update.workflow_config,
            ui_config=agent_update.ui_config,
            tags=agent_update.tags,
            version=agent_update.version,
            created_at=existing_agent['created_at'],
            updated_at=datetime.now().isoformat(),
            is_enabled=agent_update.is_enabled
        )
        
        # Re-register agent in ADK service (only if ADK is available)
        if adk_service.is_available():
            if adk_service.register_agent(updated_agent):
                # Update in database
                agent_data = updated_agent.model_dump()
                if db_manager.save_agent(agent_data):
                    return {"success": True, "agent": agent_data}
                else:
                    raise HTTPException(status_code=500, detail="Failed to update agent in database")
            else:
                raise HTTPException(status_code=400, detail="Failed to register updated agent")
        else:
            # If ADK is not available, just update the database
            agent_data = updated_agent.model_dump()
            if db_manager.save_agent(agent_data):
                return {"success": True, "agent": agent_data, "warning": "ADK not available, agent updated in database only"}
            else:
                raise HTTPException(status_code=500, detail="Failed to update agent in database")
                
    except ValidationError as e:
        print(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        if db_manager.delete_agent(agent_id):
            return {"success": True, "message": "Agent deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete agent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chat and Execution Endpoints
@app.post("/api/chat/{agent_id}")
async def chat_with_agent(agent_id: str, request: Dict[str, Any], req: Request):
    """Chat with an agent"""
    try:
        # Check if agent exists in database
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        prompt = request.get("message", "")
        session_id = request.get("session_id")
        user_id = request.get("user_id", "anonymous")
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Execute agent
        result = await adk_service.execute_agent(agent_id, prompt, session_id)
        
        # Trace agent execution with Langfuse
        if langfuse_service.is_langfuse_available():
            trace_id = langfuse_service.trace_agent_execution(
                user_id=user_id,
                agent_id=agent_id,
                agent_name=agent.get("name", "Unknown Agent"),
                user_prompt=prompt,
                agent_response=result.response if result.success else result.error,
                execution_time=result.execution_time or 0.0,
                success=result.success,
                metadata={
                    "agent_type": agent.get("agent_type", "unknown"),
                    "model": agent.get("model_settings", {}).get("model") if agent.get("model_settings") else "unknown",
                    "session_id": session_id
                }
            )
            
            # Add trace ID to response if available
            if trace_id:
                result.metadata = result.metadata or {}
                result.metadata["trace_id"] = trace_id
                result.metadata["trace_url"] = langfuse_service.get_trace_url(trace_id)
        
        # Save chat session to database
        session_data = {
            "id": session_id,
            "agent_id": agent_id,
            "user_id": user_id,
            "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": result.response}]
        }
        db_manager.save_chat_session(session_data)
        
        return {
            "success": result.success,
            "response": result.response,
            "error": result.error,
            "session_id": session_id,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session messages"""
    messages = adk_service.get_session_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@app.delete("/api/chat/sessions/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session"""
    success = adk_service.clear_session(session_id)
    return {"success": success}


# Project Management Endpoints
@app.post("/api/projects")
async def create_project(project: ProjectConfiguration):
    """Create a new project"""
    try:
        project.id = project.id or str(uuid.uuid4())
        project.created_at = datetime.now().isoformat()
        project.updated_at = datetime.now().isoformat()
        
        # Save to database
        project_data = project.model_dump()
        if db_manager.save_project(project_data):
            return {"success": True, "project": project_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project to database")
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects")
async def list_projects():
    """List all projects"""
    try:
        projects = db_manager.get_all_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project"""
    try:
        project = db_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, project: ProjectConfiguration):
    """Update a project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.id = project_id
    project.updated_at = datetime.now().isoformat()
    projects[project_id] = project
    
    return {"success": True, "project": project.model_dump()}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    del projects[project_id]
    return {"success": True}


# Code Generation Endpoints
@app.post("/api/generate/{agent_id}")
async def generate_agent_code(agent_id: str):
    """Generate Python code for an agent"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = agents[agent_id]
    
    # Generate Python code
    code = f'''#!/usr/bin/env python3
"""
Generated agent: {agent.name}
Description: {agent.description}
"""

import asyncio
from google.adk import LlmAgent
from google.adk.models import GeminiModel

async def main():
    # Create model for {agent.name}
    model = GeminiModel(
        model_name='{agent.model_settings.get("model", "gemini-1.5-pro")}',
        temperature={agent.model_settings.get("temperature", 0.7)},
        max_output_tokens={agent.model_settings.get("max_tokens", 1000)}
    )
    
    # Create agent: {agent.name}
    agent = LlmAgent(
        name='{agent.name}',
        system_prompt='{agent.system_prompt}',
        model=model
    )
    
    # Execute agent
    response = await agent.generate_content("Hello, agent!")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    return {"code": code, "filename": f"{agent.name.lower().replace(' ', '_')}.py"}


@app.post("/api/export/project/{project_id}")
async def export_project(project_id: str):
    """Export a project as Python files"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects[project_id]
    
    # Generate main project file
    main_code = f'''#!/usr/bin/env python3
"""
Generated project: {project.name}
Description: {project.description}
"""

import asyncio
from pathlib import Path
import sys

# Add project modules to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    print("ADK Project loaded successfully!")
    print("Available agents:")
'''
    
    for agent in project.agents:
        main_code += f'    print("  - {agent.name}")\n'
    
    main_code += '''
    # Example usage
    # from agents import get_agent
    # agent = get_agent("agent_name")
    # response = await agent.generate_content("Hello!")
    # print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Generate agents module
    agents_code = '''#!/usr/bin/env python3
"""Generated agents module"""

from google.adk import LlmAgent
from google.adk.models import GeminiModel

def get_agent(agent_name: str):
    """Get an agent by name"""
    agents = {
'''
    
    for agent in project.agents:
        agents_code += f'        "{agent.name}": create_{agent.id}_agent(),\n'
    
    agents_code += '''    }
    return agents.get(agent_name)

'''
    
    # Generate individual agent functions
    for agent in project.agents:
        agents_code += f'''
def create_{agent.id}_agent():
    """Create {agent.name} agent"""
    model = Gemini(
        model_name='{agent.model_settings.get("model", "gemini-2.0-flash")}',
        temperature='{agent.model_settings.get("temperature", 0.7)}',
        max_output_tokens='{agent.model_settings.get("max_tokens", 1000)}'
    )
    
    agent = LlmAgent(
        name='{agent.name}',
        system_prompt='{agent.system_prompt}',
        model=model
    )
    
    return agent
'''
    
    # Generate requirements
    requirements = '''google-adk>=0.2.0
google-genai>=0.3.0
google-cloud-aiplatform>=1.38.0
'''
    
    # Generate README
    readme = f'''# {project.name}

{project.description}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

## Available Agents

'''
    
    for agent in project.agents:
        readme += f'''### {agent.name}
{agent.description}

'''
    
    return {
        "files": {
            "main.py": main_code,
            "agents.py": agents_code,
            "requirements.txt": requirements,
            "README.md": readme
        }
    }


# AI Suggestion Endpoints
@app.post("/api/suggestions/agent/name")
async def suggest_agent_name(request: dict):
    """Get AI-powered suggestion for agent name"""
    try:
        description = request.get("description", "")
        suggestion = await adk_service.get_agent_name_suggestion(description)
        return {"success": True, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/agent/description")
async def suggest_agent_description(request: dict):
    """Get AI-powered suggestion for agent description"""
    try:
        name = request.get("name", "")
        agent_type = request.get("agent_type", "")
        suggestion = await adk_service.get_agent_description_suggestion(name, agent_type)
        return {"success": True, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/agent/system_prompt")
async def suggest_agent_system_prompt(request: dict):
    """Get AI-powered suggestion for agent system prompt"""
    try:
        name = request.get("name", "")
        description = request.get("description", "")
        agent_type = request.get("agent_type", "")
        suggestion = await adk_service.get_agent_system_prompt_suggestion(name, description, agent_type)
        return {"success": True, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/tool/name")
async def suggest_tool_name(request: dict):
    """Get AI-powered suggestion for tool name"""
    try:
        description = request.get("description", "")
        tool_type = request.get("tool_type", "")
        suggestion = await adk_service.get_tool_name_suggestion(description, tool_type)
        return {"success": True, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/tool/description")
async def suggest_tool_description(request: dict):
    """Get AI-powered suggestion for tool description"""
    try:
        name = request.get("name", "")
        tool_type = request.get("tool_type", "")
        suggestion = await adk_service.get_tool_description_suggestion(name, tool_type)
        return {"success": True, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/tool/code")
async def suggest_tool_code(request: dict):
    """Get AI-powered suggestion for tool function code"""
    try:
        name = request.get("name", "")
        description = request.get("description", "")
        tool_type = request.get("tool_type", "")
        suggestion = await adk_service.get_tool_code_suggestion(name, description, tool_type)
        return {"success": True, "suggestion": suggestion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for real-time chat
@app.websocket("/ws/chat/{agent_id}")
async def websocket_chat(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        # Check if agent exists in database
        agent = db_manager.get_agent(agent_id)
        if not agent:
            await websocket.send_text(json.dumps({
                "error": "Agent not found"
            }))
            await websocket.close()
            return
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            prompt = message_data.get("message", "")
            session_id = message_data.get("session_id", str(uuid.uuid4()))
            
            # Execute agent
            result = await adk_service.execute_agent(agent_id, prompt, session_id)
            
            # Save chat session to database
            session_data = {
                "id": session_id,
                "agent_id": agent_id,
                "user_id": message_data.get("user_id"),
                "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": result.response}]
            }
            db_manager.save_chat_session(session_data)
            
            # Send response back to client
            await websocket.send_text(json.dumps({
                "success": result.success,
                "response": result.response,
                "error": result.error,
                "session_id": session_id,
                "execution_time": result.execution_time
            }))
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        await websocket.send_text(json.dumps({
            "error": str(e)
        }))
        await websocket.close()


# Initialize with sample data
@app.on_event("startup")
async def startup_event():
    """Initialize database and load existing data on startup"""
    try:
        # Database is already initialized in DatabaseManager constructor
        print("Database initialized successfully!")
        
        # Check if we have any existing data
        existing_tools = db_manager.get_all_tools()
        existing_agents = db_manager.get_all_agents()
        
        print(f"Found {len(existing_tools)} existing tools in database")
        print(f"Found {len(existing_agents)} existing agents in database")
        
        if not existing_tools:
            # Create sample tools if none exist
            sample_tool = ToolDefinition(
                id="sample_tool",
                name="Sample Calculator",
                description="A simple calculator tool that can perform basic arithmetic",
                tool_type=ToolType.FUNCTION,
                function_code="""
def execute(expression: str) -> str:
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"
""",
                tags=["math", "calculator"]
            )
            
            if adk_service.register_tool(sample_tool):
                db_manager.save_tool(sample_tool.model_dump())
                print(f"Sample tool '{sample_tool.name}' created and saved to database")
        
        # Register built-in tools with ADK service
        if adk_service.is_available():
            print("Registering built-in tools...")
            builtin_tools = adk_service.get_builtin_tools()
            for tool_data in builtin_tools:
                tool = ToolDefinition(**tool_data)
                if adk_service.register_tool(tool):
                    print(f"Registered built-in tool: {tool.name}")
                else:
                    print(f"Failed to register built-in tool: {tool.name}")
        
        if not existing_agents:
            # Create sample agent if none exist
            sample_agent = AgentConfiguration(
                id="sample_agent",
                name="Math_Assistant",
                description="An AI assistant that helps with mathematical calculations",
                agent_type=AgentType.LLM,
                system_prompt="You are a helpful math assistant. You can perform calculations and explain mathematical concepts.",
                tools=["sample_tool"],
                tags=["math", "assistant"],
                model_settings={
                    "model": "gemini-2.0-flash",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                is_enabled=True
            )
            
            if adk_service.register_agent(sample_agent):
                db_manager.save_agent(sample_agent.model_dump())
                print(f"Sample agent '{sample_agent.name}' created and saved to database")
            else:
                print("Failed to register sample agent in ADK service")
        else:
            print(f"Found {len(existing_agents)} existing agents in database")
        
        print(f"Startup complete! Loaded {len(existing_tools)} tools and {len(existing_agents)} agents from database")
        
    except Exception as e:
        print(f"Error during startup: {e}")
        print("Continuing without sample data...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
