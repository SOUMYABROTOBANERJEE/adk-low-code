"""
Main FastAPI application for the Google ADK No-Code Platform
"""

import uuid
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .models import (
    AgentConfiguration, AgentCreateRequest, AgentUpdateRequest, ToolDefinition, SubAgent, AgentType, ToolType,
    ChatMessage, ChatSession, AgentExecutionResult, ProjectConfiguration,
    LoginRequest, RegisterRequest, AuthResponse
)
from .adk_service import ADKService
from .database import DatabaseManager
from .auth_service import AuthService
from .langfuse_service import LangfuseService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
db_manager = DatabaseManager()
adk_service = ADKService(db_manager)
auth_service = AuthService(db_manager)
langfuse_service = LangfuseService()

# Get the directory of this file
current_dir = Path(__file__).parent

# Lifespan context manager for startup/shutdown events
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
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
                tags=["math", "calculator"],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
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
                sub_agents=[],
                tools=["sample_tool"],
                tags=["math", "assistant"],
                model_settings={
                    "model": "gemini-2.0-flash",
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                workflow_config=None,
                ui_config={
                    "position": {"x": 100, "y": 100},
                    "size": {"width": 300, "height": 200},
                    "color": "#4A90E2"
                },
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
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
    
    yield
    
    # Shutdown
    print("Shutting down...")

# Update FastAPI app initialization with lifespan
app = FastAPI(
    title="Google ADK No-Code Platform",
    description="A visual platform for building and testing Google ADK agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        # Try to register tool in ADK service (optional for function tools)
        adk_registration_success = adk_service.register_tool(tool)
        
        # Save to database (required)
        tool_data = tool.model_dump()
        if db_manager.save_tool(tool_data):
            # Return success even if ADK registration failed
            if not adk_registration_success:
                print(f"Warning: Tool {tool.name} saved to database but ADK registration failed")
            return {"success": True, "tool": tool_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to save tool to database")
            
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
        
        # Try to re-register tool in ADK service (optional for function tools)
        adk_registration_success = adk_service.register_tool(tool)
        
        # Update in database (required)
        tool_data = tool.model_dump()
        if db_manager.save_tool(tool_data):
            # Return success even if ADK registration failed
            if not adk_registration_success:
                print(f"Warning: Tool {tool.name} updated in database but ADK registration failed")
            return {"success": True, "tool": tool_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to update tool in database")
            
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
async def create_agent(agent_request: AgentCreateRequest):
    """Create a new agent with sub-agent support"""
    try:
        agent_id = agent_request.id or str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        updated_at = datetime.now().isoformat()
        
        # Process sub-agents
        sub_agents = []
        
        # Handle existing agents as sub-agents
        if agent_request.sub_agents and agent_request.sub_agents.get('existing'):
            for existing_agent_id in agent_request.sub_agents['existing']:
                existing_agent = db_manager.get_agent(existing_agent_id)
                if existing_agent:
                    sub_agent = SubAgent(
                        id=existing_agent_id,
                        name=existing_agent['name'],
                        agent_type=existing_agent['agent_type'],
                        system_prompt=existing_agent.get('system_prompt', ''),
                        instructions=existing_agent.get('instructions', ''),
                        tools=existing_agent.get('tools', []),
                        model_settings=existing_agent.get('model_settings', {}),
                        is_enabled=True
                    )
                    sub_agents.append(sub_agent)
        
        # Handle new sub-agents
        if agent_request.sub_agents and agent_request.sub_agents.get('new'):
            for new_sub_agent_data in agent_request.sub_agents['new']:
                sub_agent_id = str(uuid.uuid4())
                sub_agent = SubAgent(
                    id=sub_agent_id,
                    name=new_sub_agent_data['name'],
                    agent_type=new_sub_agent_data['type'],
                    system_prompt=new_sub_agent_data.get('system_prompt', ''),
                    instructions=new_sub_agent_data.get('description', ''),
                    tools=[],
                    model_settings={},
                    is_enabled=True
                )
                sub_agents.append(sub_agent)
        
        # Create the main agent configuration
        agent = AgentConfiguration(
            id=agent_id,
            name=agent_request.name,
            description=agent_request.description,
            agent_type=agent_request.agent_type,
            system_prompt=agent_request.system_prompt,
            instructions=agent_request.instructions,
            sub_agents=sub_agents,
            tools=agent_request.tools,
            model_settings=agent_request.model_settings,
            workflow_config=agent_request.workflow_config,
            ui_config=agent_request.ui_config,
            tags=agent_request.tags,
            version=agent_request.version,
            created_at=created_at,
            updated_at=updated_at,
            is_enabled=agent_request.is_enabled
        )
        
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
        print(f"API /api/agents called, returning {len(agents)} agents")
        print(f"Agents: {agents}")
        return {"agents": agents}
    except Exception as e:
        print(f"Error in /api/agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/available-for-sub")
async def get_agents_for_sub_agents():
    """Get all agents that can be used as sub-agents"""
    try:
        agents = db_manager.get_all_agents()
        # Filter out agents that are already sub-agents of other agents
        available_agents = []
        for agent in agents:
            # Check if this agent is already a sub-agent somewhere
            is_sub_agent = False
            for other_agent in agents:
                if other_agent.get('sub_agents'):
                    for sub_agent in other_agent['sub_agents']:
                        if sub_agent.get('id') == agent['id']:
                            is_sub_agent = True
                            break
                    if is_sub_agent:
                        break
            
            if not is_sub_agent:
                available_agents.append(agent)
        
        return {"agents": available_agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent"""
    try:
        # Validate agent_id format
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
    except HTTPException:
        raise
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
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        # Validate request payload
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request body must be a JSON object")
        
        # Check if agent exists in database
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Validate and extract message
        prompt = request.get("message", "")
        if not prompt or not prompt.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        session_id = request.get("session_id")
        user_id = request.get("user_id", "anonymous")
        
        # Validate user_id if provided
        if user_id and not isinstance(user_id, str):
            raise HTTPException(status_code=400, detail="user_id must be a string")
        
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
    try:
        # Check if project exists
        existing_project = db_manager.get_project(project_id)
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project.id = project_id
        project.updated_at = datetime.now().isoformat()
        
        # Save to database
        project_data = project.model_dump()
        if db_manager.save_project(project_data):
            return {"success": True, "project": project_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to update project in database")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        # Check if project exists
        existing_project = db_manager.get_project(project_id)
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Actually delete the project from the database
        if db_manager.delete_project(project_id):
            return {"success": True, "message": "Project deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete project")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/export")
async def export_project(project_id: str):
    """Export project as a complete package"""
    try:
        project = db_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create export package
        export_data = {
            "project": project,
            "agents": [],
            "tools": []
        }
        
        # Add agents
        if project.get('agents'):
            for agent_id in project['agents']:
                agent = db_manager.get_agent(agent_id)
                if agent:
                    export_data["agents"].append(agent)
        
        # Add tools
        if project.get('tools'):
            for tool_id in project['tools']:
                tool = db_manager.get_tool(tool_id)
                if tool:
                    export_data["tools"].append(tool)
        
        return {
            "success": True,
            "message": f"Project '{project['name']}' exported successfully",
            "export_data": export_data,
            "download_url": f"/api/projects/{project_id}/download"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export project: {str(e)}")


@app.get("/api/projects/{project_id}/download")
async def download_project(project_id: str):
    """Download project as a ZIP file"""
    try:
        project = db_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        import zipfile
        import tempfile
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add project metadata
                project_meta = {
                    "name": project['name'],
                    "description": project['description'],
                    "version": project.get('version', '1.0.0'),
                    "created_at": project.get('created_at'),
                    "agents_count": len(project.get('agents', [])),
                    "tools_count": len(project.get('tools', []))
                }
                
                # Create project.json
                import json
                project_json = json.dumps(project_meta, indent=2)
                zipf.writestr("project.json", project_json)
                
                # Add agents
                if project.get('agents'):
                    for agent_id in project['agents']:
                        agent = db_manager.get_agent(agent_id)
                        if agent:
                            agent_dir = f"agents/{agent_id}"
                            zipf.writestr(f"{agent_dir}/config.json", json.dumps(agent, indent=2))
                            
                            # Generate agent code
                            if agent.get('system_prompt'):
                                agent_code = f'''#!/usr/bin/env python3
"""
Generated agent: {agent['name']}
Description: {agent['description']}
"""

import asyncio
from google.adk import LlmAgent
from google.adk.models import GeminiModel

async def main():
    # Create model for {agent['name']}
    model = GeminiModel(
        model_name='{agent.get('model_settings', {}).get('model', 'gemini-1.5-pro')}',
        temperature={agent.get('model_settings', {}).get('temperature', 0.7)},
        max_output_tokens={agent.get('model_settings', {}).get('max_tokens', 1000)}
    )
    
    # Create agent: {agent['name']}
    agent = LlmAgent(
        name='{agent['name']}',
        system_prompt='{agent['system_prompt']}',
        model=model
    )
    
    # Execute agent
    response = await agent.generate_content("Hello, agent!")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
'''
                                zipf.writestr(f"{agent_dir}/agent.py", agent_code)
                
                # Add tools
                if project.get('tools'):
                    for tool_id in project['tools']:
                        tool = db_manager.get_tool(tool_id)
                        if tool:
                            tool_dir = f"tools/{tool_id}"
                            zipf.writestr(f"{tool_dir}/config.json", json.dumps(tool, indent=2))
                            
                            # Add tool code if available
                            if tool.get('function_code'):
                                zipf.writestr(f"{tool_dir}/tool.py", tool['function_code'])
                
                # Create requirements.txt
                requirements = '''google-adk>=0.2.0
google-genai>=0.3.0
google-cloud-aiplatform>=1.38.0
fastapi>=0.100.0
uvicorn>=0.20.0
'''
                zipf.writestr("requirements.txt", requirements)
                
                # Create README
                readme = f'''# {project['name']}

{project['description']}

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
                
                if project.get('agents'):
                    for agent_id in project['agents']:
                        agent = db_manager.get_agent(agent_id)
                        if agent:
                            readme += f'''### {agent['name']}
{agent['description']}

'''
                
                readme += '''
## Project Structure

- `agents/` - Contains all agent configurations and code
- `tools/` - Contains all tool definitions and implementations
- `project.json` - Project metadata and configuration
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Development

This project was generated using the Google ADK No-Code Platform.
'''
                
                zipf.writestr("README.md", readme)
            
            # Read the ZIP file and return it
            with open(tmp_file.name, 'rb') as f:
                zip_content = f.read()
            
            # Clean up temporary file
            import os
            os.unlink(tmp_file.name)
            
            return JSONResponse(
                content=zip_content,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={project['name']}.zip"}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download project: {str(e)}")


# Enhanced Sub-Agents Management
@app.get("/api/agents/{agent_id}/sub-agents")
async def get_agent_sub_agents(agent_id: str):
    """Get sub-agents for a specific agent"""
    try:
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        sub_agents = agent.get('sub_agents', [])
        return {"sub_agents": sub_agents}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/{agent_id}/sub-agents")
async def add_sub_agent_to_agent(agent_id: str, sub_agent: SubAgent):
    """Add a sub-agent to an existing agent"""
    try:
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Generate ID for sub-agent if not provided
        if not sub_agent.id:
            sub_agent.id = str(uuid.uuid4())
        
        # Add sub-agent to the agent's sub_agents list
        if 'sub_agents' not in agent:
            agent['sub_agents'] = []
        
        # Check if sub-agent with same name already exists
        existing_names = [sa.get('name') for sa in agent['sub_agents']]
        if sub_agent.name in existing_names:
            raise HTTPException(status_code=400, detail=f"Sub-agent with name '{sub_agent.name}' already exists")
        
        # Add the new sub-agent
        agent['sub_agents'].append(sub_agent.model_dump())
        agent['updated_at'] = datetime.now().isoformat()
        
        # Save updated agent
        if db_manager.save_agent(agent):
            return {"success": True, "message": f"Sub-agent '{sub_agent.name}' added successfully", "sub_agent": sub_agent.model_dump()}
        else:
            raise HTTPException(status_code=500, detail="Failed to save agent with new sub-agent")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/available-for-sub")
async def get_agents_available_for_sub():
    """Get all agents that can be used as sub-agents"""
    try:
        # Try to get agents with basic error handling
        try:
            agents = db_manager.get_all_agents()
            logger.info(f"Retrieved {len(agents) if agents else 0} agents from database")
        except Exception as db_error:
            logger.error(f"Database error in get_all_agents: {db_error}")
            return {"available_agents": [], "error": "Database error"}
        
        if not agents:
            logger.info("No agents found in database")
            return {"available_agents": []}
        
        # Simple approach - just return all agents without complex filtering for now
        available_agents = []
        for agent in agents:
            try:
                # Basic agent info extraction with error handling
                agent_info = {
                    "id": agent.get('id', 'unknown'),
                    "name": agent.get('name', 'Unknown'),
                    "description": agent.get('description', ''),
                    "agent_type": agent.get('agent_type', 'basic'),
                    "tools": agent.get('tools', []) if isinstance(agent.get('tools'), list) else []
                }
                available_agents.append(agent_info)
            except Exception as agent_error:
                logger.warning(f"Failed to process agent: {agent_error}")
                continue
        
        logger.info(f"Returning {len(available_agents)} available agents")
        return {"available_agents": available_agents}
        
    except Exception as e:
        logger.error(f"Unexpected error in get_agents_available_for_sub: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Return a basic error response instead of raising HTTPException
        return {"available_agents": [], "error": str(e)}


@app.post("/api/agents/{agent_id}/sub-agents/from-existing")
async def add_existing_agent_as_sub(agent_id: str, request: dict):
    """Add an existing agent as a sub-agent to another agent"""
    try:
        source_agent_id = request.get('source_agent_id')
        if not source_agent_id:
            raise HTTPException(status_code=400, detail="source_agent_id is required")
        
        # Get the target agent (the one that will receive the sub-agent)
        target_agent = db_manager.get_agent(agent_id)
        if not target_agent:
            raise HTTPException(status_code=404, detail="Target agent not found")
        
        # Get the source agent (the one that will become a sub-agent)
        source_agent = db_manager.get_agent(source_agent_id)
        if not source_agent:
            raise HTTPException(status_code=404, detail="Source agent not found")
        
        # Check if source agent is already a sub-agent of target agent
        if 'sub_agents' in target_agent:
            for sub_agent in target_agent['sub_agents']:
                if sub_agent.get('id') == source_agent_id:
                    raise HTTPException(status_code=400, detail=f"Agent '{source_agent['name']}' is already a sub-agent")
        
        # Create sub-agent configuration from source agent
        sub_agent = SubAgent(
            id=source_agent_id,
            name=source_agent['name'],
            agent_type=source_agent['agent_type'],
            system_prompt=source_agent.get('system_prompt', ''),
            instructions=source_agent.get('instructions'),
            tools=source_agent.get('tools', []),
            model_settings=source_agent.get('model_settings', {}),
            is_enabled=source_agent.get('is_enabled', True)
        )
        
        # Add sub-agent to target agent
        if 'sub_agents' not in target_agent:
            target_agent['sub_agents'] = []
        
        target_agent['sub_agents'].append(sub_agent.model_dump())
        target_agent['updated_at'] = datetime.now().isoformat()
        
        # Save updated target agent
        if db_manager.save_agent(target_agent):
            return {
                "success": True, 
                "message": f"Agent '{source_agent['name']}' added as sub-agent to '{target_agent['name']}'",
                "sub_agent": sub_agent.model_dump()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save agent with new sub-agent")
            
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/agents/{agent_id}/sub-agents/{sub_agent_id}")
async def remove_sub_agent(agent_id: str, sub_agent_id: str):
    """Remove a sub-agent from an agent"""
    try:
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if 'sub_agents' not in agent:
            raise HTTPException(status_code=404, detail="Agent has no sub-agents")
        
        # Find and remove the sub-agent
        sub_agents = agent['sub_agents']
        sub_agent_found = False
        
        for i, sub_agent in enumerate(sub_agents):
            if sub_agent.get('id') == sub_agent_id:
                removed_sub_agent = sub_agents.pop(i)
                sub_agent_found = True
                break
        
        if not sub_agent_found:
            raise HTTPException(status_code=404, detail="Sub-agent not found")
        
        # Update agent
        agent['updated_at'] = datetime.now().isoformat()
        
        # Save updated agent
        if db_manager.save_agent(agent):
            return {
                "success": True, 
                "message": f"Sub-agent '{removed_sub_agent.get('name')}' removed successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save agent after removing sub-agent")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Code Generation Endpoints
@app.post("/api/generate/{agent_id}")
async def generate_agent_code(agent_id: str):
    """Generate Python code for an agent"""
    try:
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Generate Python code
        code = f'''#!/usr/bin/env python3
"""
Generated agent: {agent['name']}
Description: {agent['description']}
"""

import asyncio
from google.adk import LlmAgent
from google.adk.models import GeminiModel

async def main():
    # Create model for {agent['name']}
    model = GeminiModel(
        model_name='{agent.get('model_settings', {}).get('model', 'gemini-1.5-pro')}',
        temperature={agent.get('model_settings', {}).get('temperature', 0.7)},
        max_output_tokens={agent.get('model_settings', {}).get('max_tokens', 1000)}
    )
    
    # Create agent: {agent['name']}
    agent = LlmAgent(
        name='{agent['name']}',
        system_prompt='{agent.get('system_prompt', '')}',
        model=model
    )
    
    # Execute agent
    response = await agent.generate_content("Hello, agent!")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        return {"code": code, "filename": f"{agent['name'].lower().replace(' ', '_')}.py"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate agent code: {str(e)}")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
