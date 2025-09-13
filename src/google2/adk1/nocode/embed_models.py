
"""
Embed-specific models for the Google ADK No-Code Platform
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AgentEmbed(BaseModel):
    """Agent embed configuration"""
    id: str = Field(..., description="Unique identifier for the embed")
    agent_id: str = Field(..., description="ID of the agent being embedded")
    embed_url: str = Field(..., description="URL for the embed")
    embed_code: str = Field(..., description="HTML embed code")
    is_active: bool = Field(default=True, description="Whether the embed is active")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When the embed was created")
    access_count: int = Field(default=0, description="Number of times the embed has been accessed")
    last_access: Optional[str] = Field(None, description="Last access timestamp")
    
    # Embed configuration
    purpose: str = Field(..., description="Purpose of the embed")
    custom_purpose: Optional[str] = Field(None, description="Custom purpose description")
    environment: str = Field(..., description="Environment (development/staging/production)")
    requests_per_hour: str = Field(..., description="Estimated requests per hour")
    payload_size: str = Field(..., description="Estimated payload size")
    system_url: str = Field(..., description="Primary whitelisted URL")
    additional_urls: List[str] = Field(default_factory=list, description="Additional whitelisted URLs")
    strict_whitelist: bool = Field(default=False, description="Whether to use strict URL whitelisting")


class EmbedRequest(BaseModel):
    """Request to create an embed"""
    purpose: str = Field(..., description="Purpose of the embed")
    custom_purpose: Optional[str] = Field(None, description="Custom purpose description")
    environment: str = Field(..., description="Environment (development/staging/production)")
    requests_per_hour: str = Field(..., description="Estimated requests per hour")
    payload_size: str = Field(..., description="Estimated payload size")
    system_url: str = Field(..., description="Primary whitelisted URL")
    additional_urls: List[str] = Field(default_factory=list, description="Additional whitelisted URLs")
    strict_whitelist: bool = Field(default=False, description="Whether to use strict URL whitelisting")
    
    # Optional fields that might be sent but aren't required for validation
    agent_name: Optional[str] = Field(None, description="Agent name (optional, derived from agent_id)")
