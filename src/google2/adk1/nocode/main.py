"""
Main FastAPI application for the Google ADK No-Code Platform
"""

import uuid
import json
import logging
import os
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
from .embed_models import EmbedRequest, AgentEmbed
from .adk_service import ADKService
from .database import DatabaseManager
from .firestore_manager import FirestoreManager
from .auth_service import AuthService
from .langfuse_service import LangfuseService
from .traced_agent_runner import initialize_fastapi_tracing

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
def get_database_manager():
    """Get database manager - Firestore for production, SQLite for development"""
    try:
        # Check if we're in production mode (service account file exists)
        if os.path.exists("svcacct.json"):
            print("🔥 Using Firestore database (Production mode)")
            return FirestoreManager()
        else:
            print("💾 Using SQLite database (Development mode)")
            return DatabaseManager()
    except Exception as e:
        print(f"⚠️  Failed to initialize Firestore, falling back to SQLite: {e}")
        return DatabaseManager()

db_manager = get_database_manager()
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
        # Database is already initialized
        print("Database initialized successfully!")
        
        # Initialize Firestore collections if using Firestore
        if isinstance(db_manager, FirestoreManager):
            try:
                print("Initializing Firestore collections...")
                db_manager.initialize_collections()
                print("✅ Firestore collections initialized")
            except Exception as e:
                print(f"⚠️  Firestore collection initialization failed: {e}")
        
        # Check if we have any existing data
        existing_tools = db_manager.get_all_tools()
        existing_agents = db_manager.get_all_agents()
        
        print(f"Found {len(existing_tools)} existing tools in database")
        print(f"Found {len(existing_agents)} existing agents in database")
        
        # Initialize FastAPI tracing for Cloud Trace
        print("Initializing FastAPI tracing for Cloud Trace...")
        initialize_fastapi_tracing(app)
        print("✅ FastAPI tracing initialized")
        
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
        
        # Register existing tools from database with ADK service
        if adk_service.is_available() and existing_tools:
            print("Registering existing tools from database...")
            for tool_data in existing_tools:
                try:
                    tool = ToolDefinition(**tool_data)
                    if adk_service.register_tool(tool):
                        print(f"Registered tool: {tool.name}")
                    else:
                        print(f"Failed to register tool: {tool.name}")
                except Exception as e:
                    print(f"Error creating tool {tool_data.get('name', 'unknown')}: {e}")
                    print(f"Tool data: {tool_data}")
        
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

# URL Whitelisting middleware for embed security
@app.middleware("http")
async def url_whitelist_middleware(request: Request, call_next):
    """Middleware to enforce URL whitelisting for embed endpoints"""
    # Only apply whitelisting to embed endpoints
    if request.url.path.startswith("/embed/"):
        # Extract embed ID from path
        embed_id = request.url.path.split("/embed/")[1].split("/")[0]
        
        # Get whitelisted URLs from database
        try:
            embed_config = await db_manager.get_embed_config(embed_id)
            if embed_config:
                # Get the origin of the request
                origin = request.headers.get("origin") or request.headers.get("referer")
                if origin:
                    # Parse origin to get the base URL
                    from urllib.parse import urlparse
                    parsed_origin = urlparse(origin)
                    origin_base = f"{parsed_origin.scheme}://{parsed_origin.netloc}"
                    
                    # Check if origin is whitelisted
                    whitelisted_urls = [embed_config["system_url"]] + embed_config.get("additional_urls", [])
                    
                    is_allowed = False
                    for whitelisted_url in whitelisted_urls:
                        if embed_config.get("strict_whitelist", False):
                            # Strict matching - exact URL match
                            if origin_base == whitelisted_url.rstrip("/"):
                                is_allowed = True
                                break
                        else:
                            # Flexible matching - allow subdomains and paths
                            if origin_base.startswith(whitelisted_url.rstrip("/")) or whitelisted_url.rstrip("/").startswith(origin_base):
                                is_allowed = True
                                break
                    
                    if not is_allowed:
                        return JSONResponse(
                            status_code=403,
                            content={
                                "error": "Access denied",
                                "message": f"Origin '{origin_base}' is not whitelisted for this embed",
                                "whitelisted_urls": whitelisted_urls
                            }
                        )
                else:
                    # No origin header - might be a direct request
                    # Allow for now but log the event
                    print(f"⚠️ Embed request without origin header: {request.url.path}")
        except Exception as e:
            print(f"⚠️ Error checking embed whitelist: {e}")
            # Allow request to proceed if there's an error checking whitelist
    
    response = await call_next(request)
    return response

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

@app.get("/api/trace-info")
async def get_trace_info():
    """Get information about Cloud Trace setup"""
    try:
        if hasattr(adk_service, 'traced_runner') and adk_service.traced_runner:
            trace_info = adk_service.traced_runner.get_trace_info()
            return {
                "success": True,
                "tracing_enabled": trace_info.get("tracing_enabled", False),
                "project_id": trace_info.get("project_id", "unknown"),
                "app_name": trace_info.get("app_name", "unknown"),
                "opentelemetry_available": trace_info.get("opentelemetry_available", False),
                "adk_available": trace_info.get("adk_available", False),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "tracing_enabled": False,
                "error": "Traced runner not available",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "success": False,
            "tracing_enabled": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Authentication Endpoints
@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(request: RegisterRequest, req: Request):
    """Register a new user"""
    try:
        # Validate request
        if not request.email or not request.email.strip():
            raise HTTPException(status_code=400, detail="Email is required")
        
        if not request.password or len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Validate email format (basic)
        if '@' not in request.email or '.' not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        # Get client IP and user agent
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # Register user
        response = auth_service.register_user(request)
        
        # Trace user registration
        if response.success and response.user:
            # Create user profile in Langfuse
            langfuse_service.create_user_profile(
                user_id=request.email.strip(),
                user_data={
                    "email": request.email.strip(),
                    "internal_id": response.user.id,
                    "registration_date": datetime.now().isoformat(),
                    "ip_address": client_ip,
                    "user_agent": user_agent
                }
            )
            
            # Trace user registration action
            langfuse_service.trace_user_action(
                user_id=request.email.strip(),  # Use email as user_id for Langfuse
                action="user_registration",
                details={
                    "email": request.email.strip(),
                    "ip_address": client_ip,
                    "user_agent": user_agent,
                    "user_id": response.user.id  # Store internal user ID in details
                }
            )
        
        logger.info(f"User registration: {request.email.strip()}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user registration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(request: LoginRequest, req: Request):
    """Authenticate user and create session"""
    try:
        # Validate request
        if not request.email or not request.email.strip():
            raise HTTPException(status_code=400, detail="Email is required")
        
        if not request.password:
            raise HTTPException(status_code=400, detail="Password is required")
        
        # Get client IP and user agent
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        
        # Login user
        response = auth_service.login_user(request, user_agent, client_ip)
        
        # Trace user login
        if response.success and response.user:
            # Create user session in Langfuse
            session_id = str(uuid.uuid4())
            langfuse_service.create_user_session(
                user_id=request.email.strip(),
                session_id=session_id,
                user_metadata={
                    "email": request.email.strip(),
                    "internal_id": response.user.id,
                    "login_time": datetime.now().isoformat(),
                    "ip_address": client_ip,
                    "user_agent": user_agent
                }
            )
            
            # Trace user login action
            langfuse_service.trace_user_action(
                user_id=request.email.strip(),  # Use email as user_id for Langfuse
                action="user_login",
                details={
                    "email": request.email.strip(),
                    "ip_address": client_ip,
                    "user_agent": user_agent,
                    "user_id": response.user.id,  # Store internal user ID in details
                    "session_id": session_id
                }
            )
        
        logger.info(f"User login: {request.email.strip()}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/logout")
async def logout_user(session_token: str):
    """Logout user by invalidating session"""
    try:
        # Validate session token
        if not session_token or not session_token.strip():
            raise HTTPException(status_code=400, detail="Session token is required")
        
        # Get user info before logout for tracking
        user = auth_service.get_user_by_session(session_token.strip())
        
        success = auth_service.logout_user(session_token.strip())
        if success:
            # Trace user logout if we have user info
            if user:
                langfuse_service.trace_user_action(
                    user_id=user.email,  # Use email as user_id for Langfuse
                    action="user_logout",
                    details={
                        "email": user.email,
                        "user_id": user.id,
                        "logout_time": datetime.now().isoformat()
                    }
                )
            
            logger.info(f"User logged out successfully")
            return {"success": True, "message": "Logged out successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid session token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in user logout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_current_user(session_token: str):
    """Get current user information from session"""
    try:
        # Validate session token
        if not session_token or not session_token.strip():
            raise HTTPException(status_code=400, detail="Session token is required")
        
        user = auth_service.get_user_by_session(session_token.strip())
        if user:
            return {"success": True, "user": user.model_dump()}
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Tool Management Endpoints
@app.post("/api/tools")
async def create_tool(tool: ToolDefinition):
    """Create a new tool"""
    try:
        logger.info(f"🔧 Received tool data: {tool}")
        logger.info(f"🔧 Tool mcp_config: {tool.mcp_config}")
        logger.info(f"🔧 Tool type: {tool.tool_type}")
        logger.info(f"🔧 Tool dict: {tool.__dict__}")
        
        # Validate required fields
        if not tool.name or not tool.name.strip():
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        if not tool.description or not tool.description.strip():
            raise HTTPException(status_code=400, detail="Tool description is required")
        
        # Check if tool with same name already exists
        existing_tools = db_manager.get_all_tools()
        for existing_tool in existing_tools:
            if existing_tool.get('name', '').lower() == tool.name.lower():
                raise HTTPException(status_code=400, detail=f"Tool with name '{tool.name}' already exists")
        
        tool.id = tool.id or str(uuid.uuid4())
        
        # Try to register tool in ADK service (optional for function tools)
        adk_registration_success = adk_service.register_tool(tool)
        
        # Save to database (required)
        tool_data = tool.model_dump(exclude_none=False)
        logger.info(f"🔧 Tool data being saved: {tool_data}")
        logger.info(f"🔧 Tool mcp_config from model: {tool.mcp_config}")
        logger.info(f"🔧 Tool mcp_config from dump: {tool_data.get('mcp_config')}")
        if db_manager.save_tool(tool_data):
            # Return success even if ADK registration failed
            if not adk_registration_success:
                logger.warning(f"Tool {tool.name} saved to database but ADK registration failed")
            else:
                logger.info(f"Created tool: {tool.name} (ID: {tool.id})")
            return {"success": True, "tool": tool_data, "debug_mcp_config": tool.mcp_config}
        else:
            raise HTTPException(status_code=500, detail="Failed to save tool to database")
            
    except ValidationError as e:
        logger.error(f"Validation error creating tool: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating tool: {e}")
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
        # Validate tool_id
        if not tool_id or not tool_id.strip():
            raise HTTPException(status_code=400, detail="Tool ID cannot be empty")
        
        tool = db_manager.get_tool(tool_id.strip())
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/tools/{tool_id}")
async def update_tool(tool_id: str, tool: ToolDefinition):
    """Update an existing tool"""
    try:
        # Validate tool_id
        if not tool_id or not tool_id.strip():
            raise HTTPException(status_code=400, detail="Tool ID cannot be empty")
        
        # Check if tool exists
        existing_tool = db_manager.get_tool(tool_id.strip())
        if not existing_tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Validate required fields
        if not tool.name or not tool.name.strip():
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        if not tool.description or not tool.description.strip():
            raise HTTPException(status_code=400, detail="Tool description is required")
        
        # Check if another tool with same name already exists (excluding current tool)
        existing_tools = db_manager.get_all_tools()
        for existing in existing_tools:
            if (existing.get('id') != tool_id and 
                existing.get('name', '').lower() == tool.name.lower()):
                raise HTTPException(status_code=400, detail=f"Tool with name '{tool.name}' already exists")
        
        tool.id = tool_id.strip()
        tool.updated_at = datetime.now().isoformat()
        
        # Try to re-register tool in ADK service (optional for function tools)
        adk_registration_success = adk_service.register_tool(tool)
        
        # Update in database (required)
        tool_data = tool.model_dump()
        if db_manager.save_tool(tool_data):
            # Return success even if ADK registration failed
            if not adk_registration_success:
                logger.warning(f"Tool {tool.name} updated in database but ADK registration failed")
            else:
                logger.info(f"Updated tool: {tool.name} (ID: {tool_id})")
            return {"success": True, "tool": tool_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to update tool in database")
            
    except ValidationError as e:
        logger.error(f"Validation error updating tool: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tools/{tool_id}")
async def delete_tool(tool_id: str):
    """Delete a tool"""
    try:
        # Validate tool_id
        if not tool_id or not tool_id.strip():
            raise HTTPException(status_code=400, detail="Tool ID cannot be empty")
        
        # Check if tool exists before deleting
        existing_tool = db_manager.get_tool(tool_id.strip())
        if not existing_tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        if db_manager.delete_tool(tool_id.strip()):
            logger.info(f"Deleted tool: {existing_tool.get('name', 'Unknown')} (ID: {tool_id})")
            return {"success": True, "message": "Tool deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete tool")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting tool {tool_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent Management Endpoints
@app.post("/api/agents")
async def create_agent(agent_request: AgentCreateRequest):
    """Create a new agent with sub-agent support"""
    try:
        # Validate required fields
        if not agent_request.name or not agent_request.name.strip():
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        if not agent_request.description or not agent_request.description.strip():
            raise HTTPException(status_code=400, detail="Agent description is required")
        
        # Check if agent with same name already exists
        existing_agents = db_manager.get_all_agents()
        for existing_agent in existing_agents:
            if existing_agent.get('name', '').lower() == agent_request.name.lower():
                raise HTTPException(status_code=400, detail=f"Agent with name '{agent_request.name}' already exists")
        
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
        
        # Convert agent name to valid identifier for ADK
        # ADK requires agent names to be valid identifiers (no spaces, special chars)
        valid_agent_name = agent_request.name.strip().replace(' ', '_').replace('-', '_')
        # Remove any other special characters and ensure it starts with letter/underscore
        import re
        valid_agent_name = re.sub(r'[^a-zA-Z0-9_]', '_', valid_agent_name)
        if valid_agent_name and not valid_agent_name[0].isalpha() and valid_agent_name[0] != '_':
            valid_agent_name = 'agent_' + valid_agent_name
        
        # Create the main agent configuration
        agent = AgentConfiguration(
            id=agent_id,
            name=valid_agent_name,  # Use valid identifier for ADK
            description=agent_request.description.strip(),
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
                logger.info(f"Created agent: {agent_request.name} (ID: {agent_id})")
                return {"success": True, "agent": agent_data}
            else:
                raise HTTPException(status_code=500, detail="Failed to save agent to database")
        else:
            raise HTTPException(status_code=400, detail="Failed to register agent in ADK service")
            
    except ValidationError as e:
        logger.error(f"Validation error creating agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
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
        logger.error(f"Error getting agents for sub-agents: {e}")
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
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        # Check if agent exists
        existing_agent = db_manager.get_agent(agent_id.strip())
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Validate required fields
        if not agent_update.name or not agent_update.name.strip():
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        if not agent_update.description or not agent_update.description.strip():
            raise HTTPException(status_code=400, detail="Agent description is required")
        
        # Check if another agent with same name already exists (excluding current agent)
        existing_agents = db_manager.get_all_agents()
        for existing in existing_agents:
            if (existing.get('id') != agent_id and 
                existing.get('name', '').lower() == agent_update.name.lower()):
                raise HTTPException(status_code=400, detail=f"Agent with name '{agent_update.name}' already exists")
        
        # Update fields from the request
        updated_agent = AgentConfiguration(
            id=agent_id.strip(),
            name=agent_update.name.strip(),
            description=agent_update.description.strip(),
            agent_type=agent_update.agent_type,
            system_prompt=agent_update.system_prompt,
            instructions=agent_update.instructions,
            sub_agents=agent_update.sub_agents,
            tools=agent_update.tools,
            model_provider=agent_update.model_provider,
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
                    logger.info(f"Updated agent: {agent_update.name} (ID: {agent_id})")
                    return {"success": True, "agent": agent_data}
                else:
                    raise HTTPException(status_code=500, detail="Failed to update agent in database")
            else:
                raise HTTPException(status_code=400, detail="Failed to register updated agent")
        else:
            # If ADK is not available, just update the database
            agent_data = updated_agent.model_dump()
            if db_manager.save_agent(agent_data):
                logger.info(f"Updated agent: {agent_update.name} (ID: {agent_id}) - ADK not available")
                return {"success": True, "agent": agent_data, "warning": "ADK not available, agent updated in database only"}
            else:
                raise HTTPException(status_code=500, detail="Failed to update agent in database")
                
    except ValidationError as e:
        logger.error(f"Validation error updating agent: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating agent: {str(e)}")


@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        # Check if agent exists before deleting
        existing_agent = db_manager.get_agent(agent_id.strip())
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if db_manager.delete_agent(agent_id.strip()):
            logger.info(f"Deleted agent: {existing_agent.get('name', 'Unknown')} (ID: {agent_id})")
            return {"success": True, "message": "Agent deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete agent")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
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
        
        # Check if agent is enabled
        if not agent.get('is_enabled', True):
            raise HTTPException(status_code=400, detail="Agent is disabled")
        
        # Validate and extract message
        prompt = request.get("message", "")
        if not prompt or not prompt.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Limit message length
        if len(prompt) > 2000:
            raise HTTPException(status_code=400, detail="Message too long (max 2000 characters)")
        
        session_id = request.get("session_id")
        user_email = request.get("user_email", "anonymous")  # Changed from user_id to user_email
        
        # Validate user_email if provided
        if user_email and not isinstance(user_email, str):
            raise HTTPException(status_code=400, detail="user_email must be a string")
        
        if not session_id:
            session_id = str(uuid.uuid4())
        user_id = user_email
        # Execute agent with user_id for Cloud Trace tracking
        result = await adk_service.execute_agent(agent_id, prompt, session_id, user_id)
        
        # Trace agent execution with Langfuse using email as user_id
        if langfuse_service.is_langfuse_available():
            trace_id = langfuse_service.trace_agent_execution(
                user_id=user_email,  # Use email as user_id for Langfuse
                agent_id=agent_id,
                agent_name=agent.get("name", "Unknown Agent"),
                user_prompt=prompt,
                agent_response=result.response if result.success else result.error,
                execution_time=result.execution_time or 0.0,
                success=result.success,
                metadata={
                    "agent_type": agent.get("agent_type", "unknown"),
                    "model": agent.get("model_settings", {}).get("model") if agent.get("model_settings") else "unknown",
                    "session_id": session_id,
                    "user_email": user_email  # Add email to metadata for additional context
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
            "user_id": user_email,  # Use email as user_id
            "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": result.response}]
        }
        db_manager.save_chat_session(session_data)
        
        logger.info(f"Chat with agent {agent_id}: {len(prompt)} chars, success: {result.success}, user: {user_email}")
        
        return {
            "success": result.success,
            "response": result.response,
            "error": result.error,
            "session_id": session_id,
            "execution_time": result.execution_time,
            "metadata": result.metadata
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat with agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session messages"""
    try:
        # Validate session_id
        if not session_id or not session_id.strip():
            raise HTTPException(status_code=400, detail="Session ID cannot be empty")
        
        messages = adk_service.get_session_messages(session_id.strip())
        return {"session_id": session_id.strip(), "messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/chat/sessions/{session_id}")
async def clear_chat_session(session_id: str):
    """Clear a chat session"""
    try:
        # Validate session_id
        if not session_id or not session_id.strip():
            raise HTTPException(status_code=400, detail="Session ID cannot be empty")
        
        success = adk_service.clear_session(session_id.strip())
        if success:
            logger.info(f"Cleared chat session: {session_id}")
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Project Management Endpoints
@app.post("/api/projects")
async def create_project(project_data: dict):
    """Create a new project"""
    try:
        # Validate required fields
        if not project_data.get('name') or not project_data['name'].strip():
            raise HTTPException(status_code=400, detail="Project name is required")
        
        if not project_data.get('description') or not project_data['description'].strip():
            raise HTTPException(status_code=400, detail="Project description is required")
        
        # Check if project with same name already exists
        existing_projects = db_manager.get_all_projects()
        for existing_project in existing_projects:
            if existing_project.get('name', '').lower() == project_data['name'].lower():
                raise HTTPException(status_code=400, detail=f"Project with name '{project_data['name']}' already exists")
        
        # Create project configuration
        project = ProjectConfiguration(
            id=str(uuid.uuid4()),
            name=project_data['name'].strip(),
            description=project_data['description'].strip(),
            agents=project_data.get('agents', []),
            tools=project_data.get('tools', []),
            settings=project_data.get('settings', {}),
            version=project_data.get('version', '1.0.0'),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Save to database
        project_data_to_save = project.model_dump()
        if db_manager.save_project(project_data_to_save):
            logger.info(f"Created project: {project.name} (ID: {project.id})")
            return {"success": True, "project": project_data_to_save}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project to database")
        
    except ValidationError as e:
        logger.error(f"Validation error creating project: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/agents")
async def add_agent_to_project(project_id: str, request: dict):
    """Add an agent to a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        agent_id = request.get('agent_id')
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID is required")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if agent exists
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Initialize agents list if it doesn't exist
        if 'agents' not in project:
            project['agents'] = []
        
        # Check if agent is already in the project
        if agent_id.strip() in project['agents']:
            raise HTTPException(status_code=400, detail="Agent is already in this project")
        
        # Add agent to project
        project['agents'].append(agent_id.strip())
        project['updated_at'] = datetime.now().isoformat()
        
        # Save updated project
        if db_manager.save_project(project):
            logger.info(f"Added agent {agent_id} to project {project_id}")
            return {"success": True, "message": f"Agent '{agent['name']}' added to project"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding agent to project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/tools")
async def add_tool_to_project(project_id: str, request: dict):
    """Add a tool to a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        tool_id = request.get('tool_id')
        if not tool_id or not tool_id.strip():
            raise HTTPException(status_code=400, detail="Tool ID is required")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if tool exists
        tool = db_manager.get_tool(tool_id.strip())
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        
        # Initialize tools list if it doesn't exist
        if 'tools' not in project:
            project['tools'] = []
        
        # Check if tool is already in the project
        if tool_id.strip() in project['tools']:
            raise HTTPException(status_code=400, detail="Tool is already in this project")
        
        # Add tool to project
        project['tools'].append(tool_id.strip())
        project['updated_at'] = datetime.now().isoformat()
        
        # Save updated project
        if db_manager.save_project(project):
            logger.info(f"Added tool {tool_id} to project {project_id}")
            return {"success": True, "message": f"Tool '{tool['name']}' added to project"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding tool to project: {e}")
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
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, project: ProjectConfiguration):
    """Update a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        existing_project = db_manager.get_project(project_id.strip())
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate required fields
        if not project.name or not project.name.strip():
            raise HTTPException(status_code=400, detail="Project name is required")
        
        if not project.description or not project.description.strip():
            raise HTTPException(status_code=400, detail="Project description is required")
        
        # Check if another project with same name already exists (excluding current project)
        existing_projects = db_manager.get_all_projects()
        for existing in existing_projects:
            if (existing.get('id') != project_id and 
                existing.get('name', '').lower() == project.name.lower()):
                raise HTTPException(status_code=400, detail=f"Project with name '{project.name}' already exists")
        
        project.id = project_id.strip()
        project.updated_at = datetime.now().isoformat()
        
        # Save to database
        project_data = project.model_dump()
        if db_manager.save_project(project_data):
            logger.info(f"Updated project: {project.name} (ID: {project_id})")
            return {"success": True, "project": project_data}
        else:
            raise HTTPException(status_code=500, detail="Failed to update project in database")
            
    except ValidationError as e:
        logger.error(f"Validation error updating project: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/projects/{project_id}")
async def partial_update_project(project_id: str, updates: dict):
    """Partially update a project (for editing specific fields)"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        existing_project = db_manager.get_project(project_id.strip())
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate request
        if not isinstance(updates, dict):
            raise HTTPException(status_code=400, detail="Updates must be a JSON object")
        
        # Only allow specific fields to be updated
        allowed_fields = {'name', 'description', 'version', 'settings'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(status_code=400, detail=f"Cannot update fields: {', '.join(invalid_fields)}")
        
        # Apply updates
        updated_project = existing_project.copy()
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'name' and value and not value.strip():
                    raise HTTPException(status_code=400, detail="Project name cannot be empty")
                if field == 'description' and value and not value.strip():
                    raise HTTPException(status_code=400, detail="Project description cannot be empty")
                
                updated_project[field] = value.strip() if isinstance(value, str) else value
        
        # Update timestamp
        updated_project['updated_at'] = datetime.now().isoformat()
        
        # Check for name conflicts if name is being updated
        if 'name' in updates and updates['name']:
            existing_projects = db_manager.get_all_projects()
            for existing in existing_projects:
                if (existing.get('id') != project_id and 
                    existing.get('name', '').lower() == updates['name'].lower()):
                    raise HTTPException(status_code=400, detail=f"Project with name '{updates['name']}' already exists")
        
        # Save updated project
        if db_manager.save_project(updated_project):
            logger.info(f"Partially updated project: {updated_project.get('name', 'Unknown')} (ID: {project_id})")
            return {"success": True, "project": updated_project}
        else:
            raise HTTPException(status_code=500, detail="Failed to save updated project")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error partially updating project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")


@app.post("/api/projects/{project_id}/edit")
async def edit_project(project_id: str, updates: dict):
    """Edit a project with simplified interface"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        existing_project = db_manager.get_project(project_id.strip())
        if not existing_project:
            raise HTTPException(status_code=400, detail="Project not found")
        
        # Validate request
        if not isinstance(updates, dict):
            raise HTTPException(status_code=400, detail="Updates must be a JSON object")
        
        # Only allow specific fields to be updated
        allowed_fields = {'name', 'description', 'version', 'settings'}
        invalid_fields = set(updates.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(status_code=400, detail=f"Cannot update fields: {', '.join(invalid_fields)}")
        
        # Apply updates
        updated_project = existing_project.copy()
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'name' and value and not value.strip():
                    raise HTTPException(status_code=400, detail="Project name cannot be empty")
                if field == 'description' and value and not value.strip():
                    raise HTTPException(status_code=400, detail="Project description cannot be empty")
                
                updated_project[field] = value.strip() if isinstance(value, str) else value
        
        # Update timestamp
        updated_project['updated_at'] = datetime.now().isoformat()
        
        # Check for name conflicts if name is being updated
        if 'name' in updates and updates['name']:
            existing_projects = db_manager.get_all_projects()
            for existing in existing_projects:
                if (existing.get('id') != project_id and 
                    existing.get('name', '').lower() == updates['name'].lower()):
                    raise HTTPException(status_code=400, detail=f"Project with name '{updates['name']}' already exists")
        
        # Save updated project
        if db_manager.save_project(updated_project):
            logger.info(f"Edited project: {updated_project.get('name', 'Unknown')} (ID: {project_id})")
            return {"success": True, "project": updated_project, "message": "Project updated successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save updated project")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to edit project: {str(e)}")


@app.post("/api/projects/{project_id}/agents/add")
async def add_agent_to_project(project_id: str, agent_data: dict):
    """Add an agent to a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        
        # Validate agent data
        if not isinstance(agent_data, dict):
            raise HTTPException(status_code=400, detail="Agent data must be a JSON object")
        
        agent_id = agent_data.get('agent_id')
        if not agent_id:
            raise HTTPException(status_code=400, detail="Agent ID is required")
        
        # Check if agent exists
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=400, detail="Agent not found")
        
        # Check if agent is already in project
        if 'agents' not in project:
            project['agents'] = []
        
        if agent_id in [a.get('id') for a in project['agents']]:
            raise HTTPException(status_code=400, detail="Agent is already in this project")
        
        # Add agent to project
        project['agents'].append({
            'id': agent_id,
            'name': agent.get('name', 'Unknown Agent'),
            'added_at': datetime.now().isoformat()
        })
        
        # Update project timestamp
        project['updated_at'] = datetime.now().isoformat()
        
        # Save updated project
        if db_manager.save_project(project):
            logger.info(f"Added agent {agent_id} to project {project_id}")
            return {"success": True, "message": "Agent added to project successfully", "project": project}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding agent to project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add agent to project: {str(e)}")


@app.delete("/api/projects/{project_id}/agents/{agent_id}")
async def remove_agent_from_project(project_id: str, agent_id: str):
    """Remove an agent from a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        
        # Check if agent is in project
        if 'agents' not in project or not project['agents']:
            raise HTTPException(status_code=400, detail="No agents in this project")
        
        # Find and remove agent
        original_count = len(project['agents'])
        project['agents'] = [a for a in project['agents'] if a.get('id') != agent_id]
        
        if len(project['agents']) == original_count:
            raise HTTPException(status_code=400, detail="Agent not found in this project")
        
        # Update project timestamp
        project['updated_at'] = datetime.now().isoformat()
        
        # Save updated project
        if db_manager.save_project(project):
            logger.info(f"Removed agent {agent_id} from project {project_id}")
            return {"success": True, "message": "Agent removed from project successfully", "project": project}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing agent from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove agent from project: {str(e)}")


@app.post("/api/projects/{project_id}/tools/add")
async def add_tool_to_project(project_id: str, tool_data: dict):
    """Add a tool to a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        
        # Validate tool data
        if not isinstance(tool_data, dict):
            raise HTTPException(status_code=400, detail="Tool data must be a JSON object")
        
        tool_id = tool_data.get('tool_id')
        if not tool_id:
            raise HTTPException(status_code=400, detail="Tool ID is required")
        
        # Check if tool exists
        tool = db_manager.get_tool(tool_id)
        if not tool:
            raise HTTPException(status_code=400, detail="Tool not found")
        
        # Check if tool is already in project
        if 'tools' not in project:
            project['tools'] = []
        
        if tool_id in [t.get('id') for t in project['tools']]:
            raise HTTPException(status_code=400, detail="Tool is already in this project")
        
        # Add tool to project
        project['tools'].append({
            'id': tool_id,
            'name': tool.get('name', 'Unknown Tool'),
            'added_at': datetime.now().isoformat()
        })
        
        # Update project timestamp
        project['updated_at'] = datetime.now().isoformat()
        
        # Save updated project
        if db_manager.save_project(project):
            logger.info(f"Added tool {tool_id} to project {project_id}")
            return {"success": True, "message": "Tool added to project successfully", "project": project}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding tool to project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add tool to project: {str(e)}")


@app.delete("/api/projects/{project_id}/tools/{tool_id}")
async def remove_tool_from_project(project_id: str, tool_id: str):
    """Remove a tool from a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        
        # Check if tool is in project
        if 'tools' not in project or not project['tools']:
            raise HTTPException(status_code=400, detail="No tools in this project")
        
        # Find and remove tool
        original_count = len(project['tools'])
        project['tools'] = [t for t in project['tools'] if t.get('id') != tool_id]
        
        if len(project['tools']) == original_count:
            raise HTTPException(status_code=400, detail="Tool not found in this project")
        
        # Update project timestamp
        project['updated_at'] = datetime.now().isoformat()
        
        # Save updated project
        if db_manager.save_project(project):
            logger.info(f"Removed tool {tool_id} from project {project_id}")
            return {"success": True, "message": "Tool removed from project successfully", "project": project}
        else:
            raise HTTPException(status_code=500, detail="Failed to save project")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing tool from project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove tool from project: {str(e)}")


@app.get("/api/projects/{project_id}/agents")
async def get_project_agents(project_id: str):
    """Get all agents in a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        
        # Get agent details
        project_agents = []
        if 'agents' in project and project['agents']:
            for agent_ref in project['agents']:
                agent = db_manager.get_agent(agent_ref.get('id'))
                if agent:
                    project_agents.append(agent)
        
        return {"success": True, "agents": project_agents}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project agents {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project agents: {str(e)}")


@app.get("/api/projects/{project_id}/tools")
async def get_project_tools(project_id: str):
    """Get all tools in a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        project = db_manager.get_project(project_id.strip())
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        
        # Get tool details
        project_tools = []
        if 'tools' in project and project['tools']:
            for tool_ref in project['tools']:
                tool = db_manager.get_tool(tool_ref.get('id'))
                if tool:
                    project_tools.append(tool)
        
        return {"success": True, "tools": project_tools}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project tools {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project tools: {str(e)}")


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        # Check if project exists
        existing_project = db_manager.get_project(project_id.strip())
        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Actually delete the project from the database
        if db_manager.delete_project(project_id.strip()):
            logger.info(f"Deleted project: {existing_project.get('name', 'Unknown')} (ID: {project_id})")
            return {"success": True, "message": "Project deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete project")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/export")
async def export_project(project_id: str):
    """Export project as a complete package"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        project = db_manager.get_project(project_id.strip())
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
        
        logger.info(f"Exported project: {project.get('name', 'Unknown')} (ID: {project_id})")
        
        return {
            "success": True,
            "message": f"Project '{project['name']}' exported successfully",
            "export_data": export_data,
            "download_url": f"/api/projects/{project_id}/download"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export project: {str(e)}")


@app.get("/api/projects/{project_id}/download")
async def download_project(project_id: str):
    """Download project as a ZIP file"""
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            raise HTTPException(status_code=400, detail="Project ID cannot be empty")
        
        project = db_manager.get_project(project_id.strip())
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
            
            logger.info(f"Downloaded project: {project.get('name', 'Unknown')} (ID: {project_id})")
            
            return JSONResponse(
                content=zip_content,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={project['name']}.zip"}
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download project: {str(e)}")


# Enhanced Sub-Agents Management
@app.get("/api/agents/{agent_id}/sub-agents")
async def get_agent_sub_agents(agent_id: str):
    """Get sub-agents for a specific agent"""
    try:
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        sub_agents = agent.get('sub_agents', [])
        return {"sub_agents": sub_agents}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sub-agents for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/{agent_id}/sub-agents")
async def add_sub_agent_to_agent(agent_id: str, sub_agent: SubAgent):
    """Add a sub-agent to an existing agent"""
    try:
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        # Validate sub-agent
        if not sub_agent.name or not sub_agent.name.strip():
            raise HTTPException(status_code=400, detail="Sub-agent name is required")
        
        agent = db_manager.get_agent(agent_id.strip())
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
        if sub_agent.name.strip() in existing_names:
            raise HTTPException(status_code=400, detail=f"Sub-agent with name '{sub_agent.name}' already exists")
        
        # Add the new sub-agent
        agent['sub_agents'].append(sub_agent.model_dump())
        agent['updated_at'] = datetime.now().isoformat()
        
        # Save updated agent
        if db_manager.save_agent(agent):
            logger.info(f"Added sub-agent '{sub_agent.name}' to agent {agent_id}")
            return {"success": True, "message": f"Sub-agent '{sub_agent.name}' added successfully", "sub_agent": sub_agent.model_dump()}
        else:
            raise HTTPException(status_code=500, detail="Failed to save agent with new sub-agent")
            
    except ValidationError as e:
        logger.error(f"Validation error adding sub-agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding sub-agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))





@app.post("/api/agents/{agent_id}/sub-agents/from-existing")
async def add_existing_agent_as_sub(agent_id: str, request: dict):
    """Add an existing agent as a sub-agent to another agent"""
    try:
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        source_agent_id = request.get('source_agent_id')
        if not source_agent_id or not source_agent_id.strip():
            raise HTTPException(status_code=400, detail="source_agent_id is required")
        
        # Prevent self-referencing
        if agent_id.strip() == source_agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent cannot be its own sub-agent")
        
        # Get the target agent (the one that will receive the sub-agent)
        target_agent = db_manager.get_agent(agent_id.strip())
        if not target_agent:
            raise HTTPException(status_code=404, detail="Target agent not found")
        
        # Get the source agent (the one that will become a sub-agent)
        source_agent = db_manager.get_agent(source_agent_id.strip())
        if not source_agent:
            raise HTTPException(status_code=404, detail="Source agent not found")
        
        # Check if source agent is already a sub-agent of target agent
        if 'sub_agents' in target_agent:
            for sub_agent in target_agent['sub_agents']:
                if sub_agent.get('id') == source_agent_id:
                    raise HTTPException(status_code=400, detail=f"Agent '{source_agent['name']}' is already a sub-agent")
        
        # Create sub-agent configuration from source agent
        sub_agent = SubAgent(
            id=source_agent_id.strip(),
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
            logger.info(f"Added existing agent '{source_agent['name']}' as sub-agent to '{target_agent['name']}'")
            return {
                "success": True, 
                "message": f"Agent '{source_agent['name']}' added as sub-agent to '{target_agent['name']}'",
                "sub_agent": sub_agent.model_dump()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save agent with new sub-agent")
            
    except ValidationError as e:
        logger.error(f"Validation error adding existing agent as sub-agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding existing agent as sub-agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/agents/{agent_id}/sub-agents/{sub_agent_id}")
async def remove_sub_agent(agent_id: str, sub_agent_id: str):
    """Remove a sub-agent from an agent"""
    try:
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        # Validate sub_agent_id
        if not sub_agent_id or not sub_agent_id.strip():
            raise HTTPException(status_code=400, detail="Sub-agent ID cannot be empty")
        
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if 'sub_agents' not in agent:
            raise HTTPException(status_code=404, detail="Agent has no sub-agents")
        
        # Find and remove the sub-agent
        sub_agents = agent['sub_agents']
        sub_agent_found = False
        removed_sub_agent = None
        
        for i, sub_agent in enumerate(sub_agents):
            if sub_agent.get('id') == sub_agent_id.strip():
                removed_sub_agent = sub_agents.pop(i)
                sub_agent_found = True
                break
        
        if not sub_agent_found:
            raise HTTPException(status_code=404, detail="Sub-agent not found")
        
        # Update agent
        agent['updated_at'] = datetime.now().isoformat()
        
        # Save updated agent
        if db_manager.save_agent(agent):
            logger.info(f"Removed sub-agent '{removed_sub_agent.get('name')}' from agent {agent_id}")
            return {
                "success": True, 
                "message": f"Sub-agent '{removed_sub_agent.get('name')}' removed successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save agent after removing sub-agent")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing sub-agent {sub_agent_id} from agent {agent_id}: {e}")
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
        logger.error(f"Error generating agent code: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate agent code: {str(e)}")


# Agent Embedding Endpoints
@app.post("/api/agents/{agent_id}/embed/debug")
async def debug_embed_request(agent_id: str, request: Request):
    """Debug endpoint to see raw request data"""
    try:
        body = await request.body()
        logger.info(f"Raw request body for agent {agent_id}: {body}")
        
        try:
            json_data = await request.json()
            logger.info(f"Parsed JSON data: {json_data}")
            return {"debug": "ok", "data": json_data}
        except Exception as e:
            logger.error(f"JSON parsing error: {e}")
            return {"debug": "json_error", "error": str(e)}
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return {"debug": "error", "error": str(e)}

@app.post("/api/agents/{agent_id}/embed")
async def create_agent_embed(agent_id: str, request: Request, embed_request: EmbedRequest):
    """Create an embeddable version of an agent with configuration"""
    try:
        logger.info(f"Creating embed for agent {agent_id}")
        logger.info(f"Embed request data: {embed_request.model_dump()}")
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent is enabled
        if not agent.get('is_enabled', True):
            raise HTTPException(status_code=400, detail="Cannot embed disabled agent")
        
        # Generate unique embed ID
        embed_id = f"embed_{agent_id}_{uuid.uuid4().hex[:8]}"
        
        # Create embed configuration with all the form data
        embed_config = {
            "embed_id": embed_id,
            "agent_id": agent_id,
            "agent_name": agent['name'],
            "created_at": datetime.now().isoformat(),
            "is_active": True,
            "access_count": 0,
            "last_accessed": None,
            # Embed configuration from form
            "purpose": embed_request.purpose,
            "custom_purpose": embed_request.custom_purpose or "",
            "environment": embed_request.environment,
            "requests_per_hour": embed_request.requests_per_hour,
            "payload_size": embed_request.payload_size,
            "system_url": embed_request.system_url,
            "additional_urls": embed_request.additional_urls,
            "strict_whitelist": embed_request.strict_whitelist
        }
        
        # Save embed configuration to database
        if not db_manager.save_agent_embed(embed_config):
            raise HTTPException(status_code=500, detail="Failed to save embed configuration")
        
        # Generate embed code
        embed_code = generate_embed_html(agent, embed_id)
        
        logger.info(f"Created embed for agent {agent_id}: {embed_id}")
        
        return {
            "success": True,
            "embed_id": embed_id,
            "embed_code": embed_code,
            "embed_url": f"/api/embed/{embed_id}",
            "message": "Agent embed created successfully"
        }
        
    except ValidationError as e:
        logger.error(f"Validation error creating agent embed: {e}")
        raise HTTPException(status_code=422, detail=f"Invalid embed request: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent embed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create agent embed: {str(e)}")


@app.get("/embed/{embed_id}")
async def serve_embed_page(embed_id: str):
    """Serve the embed page for an agent"""
    try:
        # Validate embed_id
        if not embed_id or not embed_id.strip():
            raise HTTPException(status_code=400, detail="Embed ID cannot be empty")
        
        embed_config = db_manager.get_agent_embed(embed_id.strip())
        if not embed_config:
            raise HTTPException(status_code=404, detail="Embed not found")
        
        if not embed_config.get('is_active', False):
            raise HTTPException(status_code=410, detail="Embed is no longer active")
        
        agent = db_manager.get_agent(embed_config['agent_id'])
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent is enabled
        if not agent.get('is_enabled', True):
            raise HTTPException(status_code=400, detail="Agent is disabled")
        
        # Update access count
        db_manager.update_embed_access(embed_id, {
            "access_count": embed_config.get('access_count', 0) + 1,
            "last_accessed": datetime.now().isoformat()
        })
        
        # Generate embed HTML page
        embed_html = generate_embed_page_html(agent, embed_config)
        
        return HTMLResponse(content=embed_html)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving embed page: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to serve embed page: {str(e)}")


@app.get("/api/embed/{embed_id}")
async def get_embedded_agent(embed_id: str):
    """Get embedded agent interface"""
    try:
        # Validate embed_id
        if not embed_id or not embed_id.strip():
            raise HTTPException(status_code=400, detail="Embed ID cannot be empty")
        
        embed_config = db_manager.get_agent_embed(embed_id.strip())
        if not embed_config:
            raise HTTPException(status_code=404, detail="Embed not found")
        
        if not embed_config.get('is_active', False):
            raise HTTPException(status_code=410, detail="Embed is no longer active")
        
        agent = db_manager.get_agent(embed_config['agent_id'])
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent is enabled
        if not agent.get('is_enabled', True):
            raise HTTPException(status_code=410, detail="Agent is disabled")
        
        # Update access statistics
        db_manager.update_embed_access(embed_id.strip())
        
        # Return embedded agent HTML
        return HTMLResponse(content=generate_embedded_agent_html(agent, embed_id.strip()))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading embedded agent {embed_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load embedded agent: {str(e)}")


@app.post("/api/embed/{embed_id}/chat")
async def embedded_agent_chat(embed_id: str, request: dict):
    """Handle chat requests from embedded agents"""
    try:
        # Validate embed_id
        if not embed_id or not embed_id.strip():
            raise HTTPException(status_code=400, detail="Embed ID cannot be empty")
        
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        embed_config = db_manager.get_agent_embed(embed_id.strip())
        if not embed_config:
            raise HTTPException(status_code=404, detail="Embed not found")
        
        if not embed_config.get('is_active', False):
            raise HTTPException(status_code=410, detail="Embed is no longer active")
        
        agent = db_manager.get_agent(embed_config['agent_id'])
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if agent is enabled
        if not agent.get('is_enabled', True):
            raise HTTPException(status_code=400, detail="Agent is disabled")
        
        message = request.get("message", "")
        if not message or not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Limit message length
        if len(message) > 1000:
            raise HTTPException(status_code=400, detail="Message too long (max 1000 characters)")
        
        # Process message through agent
        response = await adk_service.process_message(agent, message.strip())
        
        # Update access statistics
        db_manager.update_embed_access(embed_id)
        
        logger.info(f"Processed chat for embed {embed_id}: {len(message)} chars")
        
        return {
            "success": True,
            "response": response,
            "agent_name": agent['name'],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing embedded chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")


@app.get("/api/agents/{agent_id}/embeds")
async def list_agent_embeds(agent_id: str):
    """List all embeds for an agent"""
    try:
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            raise HTTPException(status_code=400, detail="Agent ID cannot be empty")
        
        # Check if agent exists
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        embeds = db_manager.get_agent_embeds(agent_id.strip())
        return {"embeds": embeds}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing embeds for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list embeds: {str(e)}")


@app.get("/api/embeds")
async def list_all_embeds():
    """List all embeds across all agents"""
    try:
        embeds = db_manager.get_all_embeds()
        return {"embeds": embeds, "count": len(embeds)}
    except Exception as e:
        logger.error(f"Error listing all embeds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list embeds: {str(e)}")


@app.delete("/api/embed/{embed_id}")
async def delete_agent_embed(embed_id: str):
    """Delete an agent embed"""
    try:
        # Validate embed_id
        if not embed_id or not embed_id.strip():
            raise HTTPException(status_code=400, detail="Embed ID cannot be empty")
        
        # Check if embed exists before deleting
        embed_config = db_manager.get_agent_embed(embed_id.strip())
        if not embed_config:
            raise HTTPException(status_code=404, detail="Embed not found")
        
        # Delete the embed
        success = db_manager.delete_agent_embed(embed_id.strip())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete embed from database")
        
        logger.info(f"Deleted embed: {embed_id}")
        
        return {
            "success": True,
            "message": "Embed deleted successfully",
            "deleted_embed_id": embed_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting embed {embed_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete embed: {str(e)}")


# Helper functions for agent embedding
def generate_embed_html(agent: dict, embed_id: str) -> str:
    """Generate HTML embed code for an agent"""
    embed_url = f"/api/embed/{embed_id}"
    
    return f'''<!-- {agent['name']} Agent Embed Code -->
 <!-- Copy this code to embed the agent on any website -->
 <!-- IMPORTANT: Replace YOUR_DOMAIN with your actual ADK platform domain (e.g., https://yourdomain.com) -->
 <div id="adk-agent-{embed_id}" style="width: 100%; max-width: 600px; margin: 0 auto;">
     <iframe 
         src="https://YOUR_DOMAIN{embed_url}" 
         width="100%" 
         height="600" 
         frameborder="0" 
         scrolling="no"
         style="border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
     </iframe>
 </div>
 
 <!-- Alternative: Direct JavaScript integration with automatic domain detection -->
 <script>
 (function() {{
     const container = document.getElementById('adk-agent-{embed_id}');
     if (!container) return;
     
     // Configuration - Update this with your ADK platform domain
     const ADK_DOMAIN = 'https://YOUR_DOMAIN'; // Replace with your actual domain
     
     // Create chat interface
     const chatDiv = document.createElement('div');
     chatDiv.innerHTML = `
         <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; background: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
             <h3 style="margin: 0 0 15px 0; color: #374151; font-size: 18px;">{agent['name']}</h3>
             <div id="chat-messages-{embed_id}" style="height: 300px; overflow-y: auto; margin-bottom: 15px; padding: 10px; background: #f9fafb; border-radius: 4px;"></div>
             <div style="display: flex; gap: 10px;">
                 <input type="text" id="chat-input-{embed_id}" placeholder="Type your message..." 
                        style="flex: 1; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 14px;">
                 <button onclick="sendMessage_{embed_id}()" 
                         style="padding: 8px 16px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                     Send
                 </button>
             </div>
         </div>
     `;
     
     container.appendChild(chatDiv);
     
     // Add message handling
     window.sendMessage_{embed_id} = async function() {{
         const input = document.getElementById('chat-input-{embed_id}');
         const messagesDiv = document.getElementById('chat-messages-{embed_id}');
         const message = input.value.trim();
         
         if (!message) return;
         
         // Add user message
         messagesDiv.innerHTML += `<div style="margin-bottom: 10px; text-align: right;"><span style="background: #3b82f6; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;">${{message}}</span></div>`;
         input.value = '';
         
         try {{
             // Use the configured ADK domain
             const response = await fetch(`${{ADK_DOMAIN}}{embed_url}/chat`, {{
                 method: 'POST',
                 headers: {{ 'Content-Type': 'application/json' }},
                 body: JSON.stringify({{ message: message }})
             }});
             
             const data = await response.json();
             
             if (data.success) {{
                 messagesDiv.innerHTML += `<div style="margin-bottom: 10px;"><span style="background: #f3f4f6; color: #374151; padding: 5px 10px; border-radius: 15px; font-size: 12px;">${{data.response}}</span></div>`;
             }} else {{
                 messagesDiv.innerHTML += `<div style="margin-bottom: 10px;"><span style="background: #fef2f2; color: #dc2626; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Error: ${{data.detail || 'Failed to get response'}}</span></div>`;
             }}
         }} catch (error) {{
             messagesDiv.innerHTML += `<div style="margin-bottom: 10px;"><span style="background: #fef2f2; color: #dc2626; padding: 5px 10px; border-radius: 15px; font-size: 12px;">Error: ${{error.message}}</span></div>`;
         }}
         
         messagesDiv.scrollTop = messagesDiv.scrollHeight;
     }};
     
     // Enter key support
     document.getElementById('chat-input-{embed_id}').addEventListener('keypress', function(e) {{
         if (e.key === 'Enter') {{
             sendMessage_{embed_id}();
         }}
     }});
 }})();
 </script>'''




def generate_embed_page_html(agent: dict, embed_config: dict) -> str:
    """Generate HTML page for embedded agent"""
    embed_id = embed_config['embed_id']
    agent_name = agent['name']
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agent_name} - AI Agent</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .embed-container {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            width: 100%;
            max-width: 500px;
            height: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .embed-header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        
        .embed-header h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .embed-header p {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .chat-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
        }}
        
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            padding: 10px;
            background: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        
        .message {{
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
            word-wrap: break-word;
        }}
        
        .message.user {{
            background: #3b82f6;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }}
        
        .message.assistant {{
            background: #e2e8f0;
            color: #1e293b;
            border-bottom-left-radius: 4px;
        }}
        
        .message.system {{
            background: #fef3c7;
            color: #92400e;
            text-align: center;
            margin: 0 auto;
            font-size: 14px;
        }}
        
        .input-container {{
            display: flex;
            gap: 10px;
        }}
        
        .chat-input {{
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        
        .chat-input:focus {{
            border-color: #3b82f6;
        }}
        
        .send-button {{
            padding: 12px 20px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background-color 0.2s;
        }}
        
        .send-button:hover {{
            background: #2563eb;
        }}
        
        .send-button:disabled {{
            background: #9ca3af;
            cursor: not-allowed;
        }}
        
        .typing-indicator {{
            display: none;
            padding: 12px 16px;
            color: #6b7280;
            font-style: italic;
        }}
        
        .typing-indicator.show {{
            display: block;
        }}
        
        .error-message {{
            background: #fef2f2;
            color: #dc2626;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 1px solid #fecaca;
        }}
        
        @media (max-width: 480px) {{
            .embed-container {{
                height: 100vh;
                border-radius: 0;
            }}
            
            .embed-header {{
                padding: 15px;
            }}
            
            .embed-header h1 {{
                font-size: 20px;
            }}
            
            .chat-container {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="embed-container">
        <div class="embed-header">
            <h1>{agent_name}</h1>
            <p>AI Assistant</p>
        </div>
        
        <div class="chat-container">
            <div class="chat-messages" id="chatMessages">
                <div class="message system">
                    👋 Hello! I'm {agent_name}, your AI assistant. How can I help you today?
                </div>
            </div>
            
            <div class="typing-indicator" id="typingIndicator">
                {agent_name} is typing...
            </div>
            
            <div class="input-container">
                <input type="text" id="chatInput" class="chat-input" placeholder="Type your message..." autocomplete="off">
                <button id="sendButton" class="send-button">Send</button>
            </div>
        </div>
    </div>

    <script>
        const embedId = '{embed_id}';
        const agentName = '{agent_name}';
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        
        let isTyping = false;
        
        // Add message to chat
        function addMessage(content, type) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{type}}`;
            messageDiv.textContent = content;
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}
        
        // Show typing indicator
        function showTyping() {{
            if (!isTyping) {{
                isTyping = true;
                typingIndicator.classList.add('show');
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }}
        }}
        
        // Hide typing indicator
        function hideTyping() {{
            isTyping = false;
            typingIndicator.classList.remove('show');
        }}
        
        // Send message
        async function sendMessage() {{
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            chatInput.value = '';
            
            // Disable input
            chatInput.disabled = true;
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';
            
            // Show typing indicator
            showTyping();
            
            try {{
                const response = await fetch(`/api/embed/${{embedId}}/chat`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        message: message,
                        embed_id: embedId
                    }})
                }});
                
                const data = await response.json();
                
                hideTyping();
                
                if (response.ok) {{
                    addMessage(data.response, 'assistant');
                }} else {{
                    addMessage(`Error: ${{data.detail || 'Something went wrong'}}`, 'system');
                }}
            }} catch (error) {{
                hideTyping();
                addMessage(`Error: ${{error.message}}`, 'system');
            }} finally {{
                // Re-enable input
                chatInput.disabled = false;
                sendButton.disabled = false;
                sendButton.textContent = 'Send';
                chatInput.focus();
            }}
        }}
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', function(e) {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                sendMessage();
            }}
        }});
        
        // Focus input on load
        chatInput.focus();
    </script>
</body>
</html>'''
    
    return html_content


def generate_embedded_agent_html(agent: dict, embed_id: str) -> str:
    """Generate HTML for embedded agent interface"""
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{agent["name"]} - AI Agent</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f9fafb;
        }}
        .chat-container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .chat-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .chat-header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .chat-header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .chat-messages {{
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: #f8fafc;
        }}
        .message {{
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }}
        .message.user {{
            flex-direction: row-reverse;
        }}
        .message-avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
            color: white;
        }}
        .message.user .message-avatar {{
            background: #3b82f6;
        }}
        .message.agent .message-avatar {{
            background: #10b981;
        }}
        .message-content {{
            background: white;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 70%;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        .message.user .message-content {{
            background: #3b82f6;
            color: white;
        }}
        .message.agent .message-content {{
            background: white;
            color: #374151;
        }}
        .chat-input-container {{
            padding: 20px;
            background: white;
            border-top: 1px solid #e5e7eb;
        }}
        .chat-input-wrapper {{
            display: flex;
            gap: 10px;
        }}
        .chat-input {{
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e5e7eb;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }}
        .chat-input:focus {{
            border-color: #3b82f6;
        }}
        .send-button {{
            padding: 12px 24px;
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
        }}
        .send-button:hover {{
            background: #2563eb;
        }}
        .send-button:disabled {{
            background: #9ca3af;
            cursor: not-allowed;
        }}
        .welcome-message {{
            text-align: center;
            color: #6b7280;
            font-style: italic;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>{agent["name"]}</h1>
            <p>{agent.get("description", "AI Assistant")}</p>
        </div>
        
        <div class="chat-messages" id="chat-messages">
            <div class="welcome-message">
                👋 Hi! I'm {agent["name"]}. How can I help you today?
            </div>
        </div>
        
        <div class="chat-input-container">
            <div class="chat-input-wrapper">
                <input type="text" class="chat-input" id="chat-input" placeholder="Type your message..." />
                <button class="send-button" onclick="sendMessage()" id="send-button">Send</button>
            </div>
        </div>
    </div>

    <script>
        const embedId = '{embed_id}';
        const agentName = '{agent["name"]}';
        
        async function sendMessage() {{
            const input = document.getElementById('chat-input');
            const button = document.getElementById('send-button');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Disable input and button
            input.disabled = true;
            button.disabled = true;
            button.textContent = 'Sending...';
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            try {{
                // Get the current origin to construct the full API URL
                const currentOrigin = window.location.origin;
                const apiUrl = currentOrigin + '/api/embed/' + embedId + '/chat';
                
                const response = await fetch(apiUrl, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ message: message }})
                }});
                
                const data = await response.json();
                
                if (data.success) {{
                    addMessage(data.response, 'agent');
                }} else {{
                    addMessage('Sorry, I encountered an error. Please try again.', 'agent');
                }}
            }} catch (error) {{
                addMessage('Sorry, I\\'m having trouble connecting right now. Please try again later.', 'agent');
            }}
            
            // Re-enable input and button
            input.disabled = false;
            button.disabled = false;
            button.textContent = 'Send';
            input.focus();
        }}
        
        function addMessage(content, type) {{
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type;
            
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = type === 'user' ? 'U' : 'A';
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = content;
            
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
            messagesDiv.appendChild(messageDiv);
            
            // Scroll to bottom
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }}
        
        // Enter key support
        document.getElementById('chat-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});
    </script>
</body>
</html>'''
    
    return html_content


# AI Suggestion Endpoints
@app.post("/api/suggestions/agent/name")
async def suggest_agent_name(request: dict):
    """Get AI-powered suggestion for agent name"""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        description = request.get("description", "")
        if not description or not description.strip():
            raise HTTPException(status_code=400, detail="Description is required")
        
        # Limit description length
        if len(description) > 500:
            raise HTTPException(status_code=400, detail="Description too long (max 500 characters)")
        
        suggestion = await adk_service.get_agent_name_suggestion(description.strip())
        return {"success": True, "suggestion": suggestion}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent name suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/agent/description")
async def suggest_agent_description(request: dict):
    """Get AI-powered suggestion for agent description"""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        name = request.get("name", "")
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        agent_type = request.get("agent_type", "")
        if not agent_type or not agent_type.strip():
            raise HTTPException(status_code=400, detail="Agent type is required")
        
        # Limit input lengths
        if len(name) > 100:
            raise HTTPException(status_code=400, detail="Agent name too long (max 100 characters)")
        
        suggestion = await adk_service.get_agent_description_suggestion(name.strip(), agent_type.strip())
        return {"success": True, "suggestion": suggestion}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent description suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/agent/system_prompt")
async def suggest_agent_system_prompt(request: dict):
    """Get AI-powered suggestion for agent system prompt"""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        name = request.get("name", "")
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        description = request.get("description", "")
        if not description or not description.strip():
            raise HTTPException(status_code=400, detail="Agent description is required")
        
        agent_type = request.get("agent_type", "")
        if not agent_type or not agent_type.strip():
            raise HTTPException(status_code=400, detail="Agent type is required")
        
        # Limit input lengths
        if len(name) > 100:
            raise HTTPException(status_code=400, detail="Agent name too long (max 100 characters)")
        
        if len(description) > 500:
            raise HTTPException(status_code=400, detail="Agent description too long (max 500 characters)")
        
        suggestion = await adk_service.get_agent_system_prompt_suggestion(name.strip(), description.strip(), agent_type.strip())
        return {"success": True, "suggestion": suggestion}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent system prompt suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/tool/name")
async def suggest_tool_name(request: dict):
    """Get AI-powered suggestion for tool name"""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        description = request.get("description", "")
        if not description or not description.strip():
            raise HTTPException(status_code=400, detail="Tool description is required")
        
        tool_type = request.get("tool_type", "")
        if not tool_type or not tool_type.strip():
            raise HTTPException(status_code=400, detail="Tool type is required")
        
        # Limit input lengths
        if len(description) > 500:
            raise HTTPException(status_code=400, detail="Tool description too long (max 500 characters)")
        
        suggestion = await adk_service.get_tool_name_suggestion(description.strip(), tool_type.strip())
        return {"success": True, "suggestion": suggestion}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool name suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/tool/description")
async def suggest_tool_description(request: dict):
    """Get AI-powered suggestion for tool description"""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        name = request.get("name", "")
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        tool_type = request.get("tool_type", "")
        if not tool_type or not tool_type.strip():
            raise HTTPException(status_code=400, detail="Tool type is required")
        
        # Limit input lengths
        if len(name) > 100:
            raise HTTPException(status_code=400, detail="Tool name too long (max 100 characters)")
        
        suggestion = await adk_service.get_tool_description_suggestion(name.strip(), tool_type.strip())
        return {"success": True, "suggestion": suggestion}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool description suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/suggestions/tool/code")
async def suggest_tool_code(request: dict):
    """Get AI-powered suggestion for tool function code"""
    try:
        # Validate request
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="Request must be a JSON object")
        
        name = request.get("name", "")
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Tool name is required")
        
        description = request.get("description", "")
        if not description or not description.strip():
            raise HTTPException(status_code=400, detail="Tool description is required")
        
        tool_type = request.get("tool_type", "")
        if not tool_type or not tool_type.strip():
            raise HTTPException(status_code=400, detail="Tool type is required")
        
        # Limit input lengths
        if len(name) > 100:
            raise HTTPException(status_code=400, detail="Tool name too long (max 100 characters)")
        
        if len(description) > 500:
            raise HTTPException(status_code=400, detail="Tool description too long (max 500 characters)")
        
        suggestion = await adk_service.get_tool_code_suggestion(name.strip(), description.strip(), tool_type.strip())
        return {"success": True, "suggestion": suggestion}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool code suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for real-time chat
@app.websocket("/ws/chat/{agent_id}")
async def websocket_chat(websocket: WebSocket, agent_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        # Validate agent_id
        if not agent_id or not agent_id.strip():
            await websocket.send_text(json.dumps({
                "error": "Invalid agent ID"
            }))
            await websocket.close()
            return
        
        # Check if agent exists in database
        agent = db_manager.get_agent(agent_id.strip())
        if not agent:
            await websocket.send_text(json.dumps({
                "error": "Agent not found"
            }))
            await websocket.close()
            return
        
        # Check if agent is enabled
        if not agent.get('is_enabled', True):
            await websocket.send_text(json.dumps({
                "error": "Agent is disabled"
            }))
            await websocket.close()
            return
        
        logger.info(f"WebSocket chat started for agent {agent_id}")
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                prompt = message_data.get("message", "")
                session_id = message_data.get("session_id", str(uuid.uuid4()))
                
                # Validate message
                if not prompt or not prompt.strip():
                    await websocket.send_text(json.dumps({
                        "error": "Message cannot be empty"
                    }))
                    continue
                
                # Limit message length
                if len(prompt) > 2000:
                    await websocket.send_text(json.dumps({
                        "error": "Message too long (max 2000 characters)"
                    }))
                    continue
                
                # Execute agent
                result = await adk_service.execute_agent(agent_id.strip(), prompt.strip(), session_id)
                
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
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format"
                }))
            except Exception as msg_error:
                logger.error(f"Error processing WebSocket message: {msg_error}")
                await websocket.send_text(json.dumps({
                    "error": "Internal server error"
                }))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for agent {agent_id}")
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "error": "Internal server error"
            }))
        except:
            pass
        await websocket.close()


# Usage Statistics and Analytics Endpoints
@app.get("/api/usage/statistics")
async def get_usage_statistics():
    """Get comprehensive usage statistics from Firestore"""
    try:
        # Get basic counts
        agents = db_manager.get_all_agents()
        tools = db_manager.get_all_tools()
        projects = db_manager.get_all_projects()
        
        # Get chat sessions count
        chat_sessions = db_manager.get_all_chat_sessions()
        
        # Calculate token consumption by agent
        agent_token_usage = {}
        total_tokens = 0
        
        for session in chat_sessions:
            agent_id = session.get('agent_id')
            if agent_id:
                # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
                message_count = len(session.get('messages', []))
                estimated_tokens = message_count * 50  # Average 50 tokens per message
                
                if agent_id not in agent_token_usage:
                    agent_token_usage[agent_id] = {
                        'agent_id': agent_id,
                        'agent_name': 'Unknown Agent',
                        'total_tokens': 0,
                        'chat_sessions': 0,
                        'last_used': None
                    }
                
                agent_token_usage[agent_id]['total_tokens'] += estimated_tokens
                agent_token_usage[agent_id]['chat_sessions'] += 1
                agent_token_usage[agent_id]['last_used'] = session.get('created_at')
                total_tokens += estimated_tokens
        
        # Update agent names
        for agent in agents:
            agent_id = agent.get('id')
            if agent_id in agent_token_usage:
                agent_token_usage[agent_id]['agent_name'] = agent.get('name', 'Unknown Agent')
        
        # Sort agents by token usage
        sorted_agents = sorted(agent_token_usage.values(), key=lambda x: x['total_tokens'], reverse=True)
        
        return {
            "success": True,
            "statistics": {
                "total_agents": len(agents),
                "total_tools": len(tools),
                "total_projects": len(projects),
                "total_chat_sessions": len(chat_sessions),
                "total_tokens": total_tokens,
                "agent_token_usage": sorted_agents[:10],  # Top 10 agents
                "recent_agents": [
                    {
                        "id": agent.get('id'),
                        "name": agent.get('name'),
                        "created_at": agent.get('created_at'),
                        "is_enabled": agent.get('is_enabled', True)
                    }
                    for agent in sorted(agents, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting usage statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage statistics: {str(e)}")


@app.get("/api/usage/agent/{agent_id}/tokens")
async def get_agent_token_usage(agent_id: str):
    """Get detailed token usage for a specific agent"""
    try:
        # Get agent info
        agent = db_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get chat sessions for this agent
        chat_sessions = db_manager.get_all_chat_sessions()
        agent_sessions = [s for s in chat_sessions if s.get('agent_id') == agent_id]
        
        # Calculate detailed token usage
        total_tokens = 0
        total_messages = 0
        daily_usage = {}
        
        for session in agent_sessions:
            messages = session.get('messages', [])
            total_messages += len(messages)
            
            # Estimate tokens per message
            session_tokens = len(messages) * 50  # Average 50 tokens per message
            total_tokens += session_tokens
            
            # Group by date
            created_at = session.get('created_at', '')
            if created_at:
                date = created_at.split('T')[0]  # Extract date part
                daily_usage[date] = daily_usage.get(date, 0) + session_tokens
        
        # Sort daily usage
        sorted_daily_usage = sorted(daily_usage.items(), key=lambda x: x[0], reverse=True)
        
        return {
            "success": True,
            "agent": {
                "id": agent_id,
                "name": agent.get('name'),
                "total_tokens": total_tokens,
                "total_sessions": len(agent_sessions),
                "total_messages": total_messages,
                "average_tokens_per_session": total_tokens / len(agent_sessions) if agent_sessions else 0,
                "daily_usage": sorted_daily_usage[:30]  # Last 30 days
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent token usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent token usage: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
