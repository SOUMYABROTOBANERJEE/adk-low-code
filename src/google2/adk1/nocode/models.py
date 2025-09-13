"""
Data models for the Google ADK No-Code Platform
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime


class ToolType(str, Enum):
    """Types of tools available in the platform"""
    FUNCTION = "function"
    BUILTIN = "builtin"
    GOOGLE_CLOUD = "google_cloud"
    MCP = "mcp"
    OPENAPI = "openapi"
    CUSTOM = "custom"


class User(BaseModel):
    """User model for authentication and tracking"""
    id: str = Field(..., description="Unique identifier for the user")
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name")
    password_hash: str = Field(..., description="Hashed password for authentication")
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When the user was created")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional user metadata")

class UserSession(BaseModel):
    """User session for tracking and authentication"""
    id: str = Field(..., description="Unique session identifier")
    user_id: str = Field(..., description="Associated user ID")
    session_token: str = Field(..., description="Session authentication token")
    expires_at: str = Field(..., description="When the session expires")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Session creation time")
    last_activity: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Last activity timestamp")
    user_agent: Optional[str] = Field(None, description="User agent string")
    ip_address: Optional[str] = Field(None, description="IP address of the session")


class ModelProvider(str, Enum):
    """Supported model providers"""
    GOOGLE = "google"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    MISTRAL = "mistral"
    OLLAMA = "ollama"

class AgentType(str, Enum):
    """Types of agents available in the platform"""
    LLM = "llm"
    WORKFLOW = "workflow"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    LOOP = "loop"
    CUSTOM = "custom"


class ToolDefinition(BaseModel):
    """Definition of a tool that can be used by agents"""
    id: str = Field(..., description="Unique identifier for the tool")
    name: str = Field(..., description="Display name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    tool_type: ToolType = Field(..., description="Type of the tool")
    
    class Config:
        # Include all fields in model_dump, even if they are None
        exclude_none = False
        # Use dict instead of exclude_none for older Pydantic versions
        use_enum_values = True
    
    # For function tools
    function_code: Optional[str] = Field(None, description="Python code for custom function tools")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters for the tool")
    
    # For builtin tools
    builtin_name: Optional[str] = Field(None, description="Name of builtin tool if applicable")
    
    # For external tools
    external_config: Optional[Dict[str, Any]] = Field(None, description="Configuration for external tools")
    
    # For MCP tools
    mcp_config: Optional[Dict[str, Any]] = Field(None, description="Configuration for MCP server connection")
    mcp_server_config: Optional[Dict[str, Any]] = Field(None, description="Alternative MCP server configuration")
    test_field: Optional[str] = Field(None, description="Test field")
    mcp_configuration: Optional[Dict[str, Any]] = Field(None, description="MCP configuration alternative")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    is_enabled: bool = Field(default=True, description="Whether the tool is enabled")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    
    @validator('function_code')
    def validate_function_code(cls, v, values):
        # If this is a function tool, function_code is required
        if values.get('tool_type') == ToolType.FUNCTION and not v:
            raise ValueError("function_code is required for function tools")
        
        if v is not None:
            # Basic validation that it's valid Python code
            try:
                compile(v, '<string>', 'exec')
            except SyntaxError as e:
                raise ValueError(f"Invalid Python code: {e}")
        return v
    
    @validator('mcp_config')
    def validate_mcp_config(cls, v, values):
        # If this is an MCP tool, mcp_config is required
        if values.get('tool_type') == ToolType.MCP and not v:
            raise ValueError("mcp_config is required for MCP tools")
        return v


class SubAgent(BaseModel):
    """Definition of a sub-agent within a multi-agent system"""
    id: str = Field(..., description="Unique identifier for the sub-agent")
    name: str = Field(..., description="Display name of the sub-agent")
    agent_type: AgentType = Field(..., description="Type of the sub-agent")
    
    # Configuration
    system_prompt: str = Field(..., description="System prompt for the sub-agent")
    instructions: Optional[str] = Field(None, description="Additional instructions")
    
    # Tools and capabilities
    tools: List[str] = Field(default_factory=list, description="List of tool IDs this agent can use")
    
    # Model configuration
    model_settings: Optional[Dict[str, Any]] = Field(None, description="Model-specific configuration")
    
    # Position in the workflow (for workflow agents)
    position: Optional[Dict[str, int]] = Field(None, description="Position coordinates for UI")
    
    # Metadata
    is_enabled: bool = Field(default=True, description="Whether the sub-agent is enabled")


class AgentCreateRequest(BaseModel):
    """Request model for creating agents with sub-agent support"""
    id: Optional[str] = Field(None, description="Unique identifier for the agent")
    name: str = Field(..., description="Display name of the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    agent_type: AgentType = Field(..., description="Type of the agent")
    
    # Core configuration
    system_prompt: str = Field(..., description="Main system prompt for the agent")
    instructions: Optional[str] = Field(None, description="Additional instructions")
    
    # Sub-agents structure for creation
    sub_agents: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {"existing": [], "new": []},
        description="Sub-agents structure with existing IDs and new configurations"
    )
    
    # Tools
    tools: List[str] = Field(default_factory=list, description="List of tool IDs this agent can use")
    
    # Model configuration
    model_provider: ModelProvider = Field(default=ModelProvider.GOOGLE, description="Model provider to use")
    model_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        description="Configuration for the underlying model"
    )
    
    # Workflow configuration (for workflow agents)
    workflow_config: Optional[Dict[str, Any]] = Field(None, description="Workflow-specific configuration")
    
    # UI configuration
    ui_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "position": {"x": 100, "y": 100},
            "size": {"width": 300, "height": 200},
            "color": "#4A90E2"
        },
        description="UI display configuration"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    version: str = Field(default="1.0.0", description="Version of the agent configuration")
    is_enabled: bool = Field(default=True, description="Whether the agent is enabled")


class AgentConfiguration(BaseModel):
    """Complete configuration for an agent"""
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Display name of the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    agent_type: AgentType = Field(..., description="Type of the agent")
    
    # Core configuration
    system_prompt: str = Field(..., description="Main system prompt for the agent")
    instructions: Optional[str] = Field(None, description="Additional instructions")
    
    # Sub-agents (for multi-agent systems)
    sub_agents: List[SubAgent] = Field(default_factory=list, description="List of sub-agents")
    
    # Tools
    tools: List[str] = Field(default_factory=list, description="List of tool IDs this agent can use")
    
    # Model configuration
    model_provider: ModelProvider = Field(default=ModelProvider.GOOGLE, description="Model provider to use")
    model_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        description="Configuration for the underlying model"
    )
    
    # Workflow configuration (for workflow agents)
    workflow_config: Optional[Dict[str, Any]] = Field(None, description="Workflow-specific configuration")
    
    # UI configuration
    ui_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "position": {"x": 100, "y": 100},
            "size": {"width": 300, "height": 200},
            "color": "#4A90E2"
        },
        description="UI display configuration"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    version: str = Field(default="1.0.0", description="Version of the agent configuration")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    is_enabled: bool = Field(default=True, description="Whether the agent is enabled")


class ChatMessage(BaseModel):
    """A message in the chat interface"""
    id: str = Field(..., description="Unique identifier for the message")
    role: str = Field(..., description="Role of the message sender (user/assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: str = Field(..., description="Timestamp of the message")
    user_id: Optional[str] = Field(None, description="User ID who sent the message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ChatSession(BaseModel):
    """A chat session with an agent"""
    id: str = Field(..., description="Unique identifier for the session")
    agent_id: str = Field(..., description="ID of the agent being used")
    messages: List[ChatMessage] = Field(default_factory=list, description="List of messages in the session")
    created_at: str = Field(..., description="Session creation timestamp")
    updated_at: str = Field(..., description="Last activity timestamp")


class AgentExecutionResult(BaseModel):
    """Result of executing an agent"""
    success: bool = Field(..., description="Whether the execution was successful")
    response: Optional[str] = Field(None, description="Response from the agent")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional execution metadata")


class ProjectConfiguration(BaseModel):
    """Configuration for a complete project"""
    id: str = Field(..., description="Unique identifier for the project")
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Description of the project")
    
    # Agents in the project
    agents: List[AgentConfiguration] = Field(default_factory=list, description="List of agents in the project")
    
    # Tools available in the project
    tools: List[ToolDefinition] = Field(default_factory=list, description="List of tools available in the project")
    
    # Project settings
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "default_model": "gemini-1.5-pro",
            "auto_save": True,
            "version_control": True
        },
        description="Project-level settings"
    )
    
    # Configuration (for backward compatibility with database)
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration data")
    
    # Metadata
    version: str = Field(default="1.0.0", description="Version of the project")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class LoginRequest(BaseModel):
    """Request model for user login"""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class RegisterRequest(BaseModel):
    """Request model for user registration"""
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's display name")
    password: str = Field(..., description="User's password")

class AuthResponse(BaseModel):
    """Response model for authentication"""
    success: bool = Field(..., description="Whether authentication was successful")
    user: Optional[User] = Field(None, description="User information if successful")
    session_token: Optional[str] = Field(None, description="Session token if successful")
    message: str = Field(..., description="Response message")

class AgentUpdateRequest(BaseModel):
    """Request model for updating an agent (ID not required)"""
    name: str = Field(..., description="Display name of the agent")
    description: str = Field(..., description="Description of the agent's purpose")
    agent_type: AgentType = Field(..., description="Type of the agent")
    
    # Core configuration
    system_prompt: str = Field(..., description="Main system prompt for the agent")
    instructions: Optional[str] = Field(None, description="Additional instructions")
    
    # Sub-agents (for multi-agent systems)
    sub_agents: List[SubAgent] = Field(default_factory=list, description="List of sub-agents")
    
    # Tools
    tools: List[str] = Field(default_factory=list, description="List of tool IDs this agent can use")
    
    # Model configuration
    model_provider: ModelProvider = Field(default=ModelProvider.GOOGLE, description="Model provider to use")
    model_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model": "gemini-1.5-pro",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        description="Configuration for the underlying model"
    )
    
    # Workflow configuration (for workflow agents)
    workflow_config: Optional[Dict[str, Any]] = Field(None, description="Workflow-specific configuration")
    
    # UI configuration
    ui_config: Dict[str, Any] = Field(
        default_factory=lambda: {
            "position": {"x": 100, "y": 100},
            "size": {"width": 300, "height": 200},
            "color": "#4A90E2"
        },
        description="UI display configuration"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    version: str = Field(default="1.0.0", description="Version of the agent configuration")
    is_enabled: bool = Field(default=True, description="Whether the agent is enabled")
