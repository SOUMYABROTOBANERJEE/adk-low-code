"""
Langfuse observability service for the Google ADK No-Code Platform
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from langfuse import Langfuse
from langfuse import Langfuse


class LangfuseService:
    """Service for integrating Langfuse observability into the platform"""
    
    def __init__(self):
        # Initialize Langfuse client with environment variables
        self.langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", "sk-lf-e25e825c-e8f8-43ee-be43-23d359e87815"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "pk-lf-46b372c7-51ae-4a32-9187-ed8930153e0b"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Langfuse is available and accessible"""
        try:
            # Try to make a simple API call to check connectivity
            self.langfuse.auth_check()
            print("✅ Langfuse connected successfully")
            return True
        except Exception as e:
            print(f"⚠️ Langfuse not available: {e}")
            return False
    
    def is_langfuse_available(self) -> bool:
        """Check if Langfuse service is available"""
        return self.is_available
    
    def create_trace(self, 
                    name: str, 
                    user_id: str, 
                    session_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new trace for tracking user interactions"""
        if not self.is_available:
            return None
        
        try:
            trace_id = str(uuid.uuid4())
            
            # Use the new Langfuse API
            trace = self.langfuse.trace(
                id=trace_id,
                name=name,
                user_id=user_id,
                session_id=session_id,
                metadata=metadata or {}
            )
            return trace_id
            
        except Exception as e:
            print(f"Error creating Langfuse trace: {e}")
            return None
    
    def create_span(self, 
                   trace_id: str, 
                   name: str, 
                   input: Optional[Dict[str, Any]] = None,
                   output: Optional[Dict[str, Any]] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a span within a trace for tracking specific operations"""
        if not self.is_available:
            return None
        
        try:
            span_id = str(uuid.uuid4())
            
            # Use the new Langfuse API
            span = self.langfuse.span(
                id=span_id,
                trace_id=trace_id,
                name=name,
                input=input,
                output=output,
                metadata=metadata or {}
            )
            return span_id
            
        except Exception as e:
            print(f"Error creating Langfuse span: {e}")
            return None
    
    def create_generation(self, 
                         trace_id: str, 
                         name: str, 
                         model: str,
                         input_text: str,
                         output_text: str,
                         metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a generation record for LLM interactions.

        Note: Newer Langfuse SDKs expect `input`/`output` instead of `prompt`/`completion`.
        """
        if not self.is_available:
            return None
        
        try:
            generation_id = str(uuid.uuid4())
            
            # Use the new Langfuse API
            generation = self.langfuse.generation(
                id=generation_id,
                trace_id=trace_id,
                name=name,
                model=model,
                input=input_text,
                output=output_text,
                metadata=metadata or {}
            )
            return generation_id
            
        except Exception as e:
            print(f"Error creating Langfuse generation: {e}")
            return None
    
    def create_score(self, 
                    trace_id: str, 
                    name: str, 
                    value: float,
                    comment: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a score for evaluating trace quality"""
        if not self.is_available:
            return None
        
        try:
            score_id = str(uuid.uuid4())
            
            # Use the new Langfuse API
            score = self.langfuse.score(
                id=score_id,
                trace_id=trace_id,
                name=name,
                value=value,
                comment=comment,
                metadata=metadata or {}
            )
            return score_id
            
        except Exception as e:
            print(f"Error creating Langfuse score: {e}")
            return None
    
    def trace_agent_execution(self, 
                             user_id: str, 
                             agent_id: str, 
                             agent_name: str,
                             user_prompt: str,
                             agent_response: str,
                             execution_time: float,
                             success: bool,
                             metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a comprehensive trace for agent execution"""
        if not self.is_available:
            return None
        
        try:
            # Create main trace
            trace_id = self.create_trace(
                name=f"Agent Execution: {agent_name}",
                user_id=user_id,
                metadata={
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "execution_time": execution_time,
                    "success": success,
                    **(metadata or {})
                }
            )
            
            if not trace_id:
                return None
            
            # Create span for the execution
            self.create_span(
                trace_id=trace_id,
                name="Agent Execution",
                input={"user_prompt": user_prompt},
                output={"agent_response": agent_response},
                metadata={
                    "execution_time": execution_time,
                    "success": success
                }
            )
            
            # Create generation record for the LLM interaction
            self.create_generation(
                trace_id=trace_id,
                name=f"{agent_name} Response",
                model="gemini-2.0-flash",  # Default model
                input_text=user_prompt,
                output_text=agent_response,
                metadata={
                    "agent_id": agent_id,
                    "execution_time": execution_time
                }
            )
            
            # Create success score
            score_value = 1.0 if success else 0.0
            self.create_score(
                trace_id=trace_id,
                name="execution_success",
                value=score_value,
                comment="Agent execution success indicator"
            )
            
            return trace_id
            
        except Exception as e:
            print(f"Error tracing agent execution: {e}")
            return None
    
    def trace_tool_usage(self, 
                         trace_id: str, 
                         tool_name: str, 
                         tool_input: Any,
                         tool_output: Any,
                         execution_time: float,
                         success: bool) -> Optional[str]:
        """Create a span for tool usage within a trace"""
        if not self.is_available:
            return None
        
        try:
            return self.create_span(
                trace_id=trace_id,
                name=f"Tool Usage: {tool_name}",
                input={"tool_input": tool_input},
                output={"tool_output": tool_output},
                metadata={
                    "tool_name": tool_name,
                    "execution_time": execution_time,
                    "success": success
                }
            )
        except Exception as e:
            print(f"Error tracing tool usage: {e}")
            return None
    
    def trace_user_action(self, 
                         user_id: str, 
                         action: str, 
                         details: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a trace for user actions (login, logout, etc.)"""
        if not self.is_available:
            return None
        
        try:
            return self.create_trace(
                name=f"User Action: {action}",
                user_id=user_id,
                metadata={
                    "action": action,
                    "timestamp": datetime.now().isoformat(),
                    **(details or {})
                }
            )
        except Exception as e:
            print(f"Error tracing user action: {e}")
            return None
    
    def get_trace_url(self, trace_id: str) -> Optional[str]:
        """Get the URL for viewing a trace in Langfuse UI"""
        if not self.is_available:
            return None
        
        try:
            base_url = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            return f"{base_url}/traces/{trace_id}"
        except Exception as e:
            print(f"Error generating trace URL: {e}")
            return None
    
    def close(self):
        """Close Langfuse client connections"""
        if self.is_available:
            try:
                self.langfuse.flush()
            except Exception as e:
                print(f"Error flushing Langfuse: {e}")
