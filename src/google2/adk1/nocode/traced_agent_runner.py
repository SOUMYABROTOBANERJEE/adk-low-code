"""
Custom Agent Runner with Cloud Trace Integration
Provides observability and user ID tracking for all agent executions
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

# OpenTelemetry imports for Cloud Trace
try:
    from opentelemetry import trace
    from opentelemetry.exporter.gcp_trace import CloudTraceSpanExporter
    from opentelemetry.sdk.trace import export
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    OPENTELEMETRY_AVAILABLE = True
    print("OpenTelemetry Cloud Trace loaded successfully")
except ImportError as e:
    OPENTELEMETRY_AVAILABLE = False
    print(f"Warning: OpenTelemetry not available. Import error: {e}")
    print("Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-cloud-trace")

# ADK imports
try:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.agents import Agent
    from google.genai.types import Content, Part
    ADK_AVAILABLE = True
    # Define SessionService as an alias for compatibility
    SessionService = InMemorySessionService
except ImportError as e:
    ADK_AVAILABLE = False
    print(f"Warning: Google ADK not available. Import error: {e}")
    # Define a dummy SessionService for type hints
    SessionService = None

logger = logging.getLogger(__name__)

class TracedAgentRunner:
    """
    Custom agent runner with Cloud Trace integration and user ID tracking
    """
    
    def __init__(self, 
                 project_id: str = "tsl-generative-ai",
                 app_name: str = "adk-platform",
                 session_service: Optional[SessionService] = None):
        """
        Initialize the traced agent runner
        
        Args:
            project_id: Google Cloud project ID
            app_name: Application name for tracing
            session_service: ADK session service
        """
        self.project_id = project_id
        self.app_name = app_name
        self.session_service = session_service
        self.tracer = None
        self.runners: Dict[str, Runner] = {}  # Cache runners by agent_id
        
        # Initialize Cloud Trace if available
        if OPENTELEMETRY_AVAILABLE:
            self._initialize_cloud_trace()
        else:
            logger.warning("Cloud Trace not available - running without tracing")
    
    def _initialize_cloud_trace(self):
        """Initialize Cloud Trace exporter and tracer"""
        try:
            # Set environment variable for service account
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "svcacct.json"
            
            # Create tracer provider
            provider = TracerProvider()
            
            # Create Cloud Trace exporter
            exporter = CloudTraceSpanExporter(project_id=self.project_id)
            
            # Create batch span processor
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            
            # Set the tracer provider
            trace.set_tracer_provider(provider)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            logger.info(f"Cloud Trace initialized for project: {self.project_id} with service account")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cloud Trace: {e}")
            self.tracer = None
    
    def _create_span_name(self, operation: str, agent_id: str, user_id: str) -> str:
        """Create a descriptive span name"""
        return f"{self.app_name}.{operation}.{agent_id}.{user_id}"
    
    def _add_user_context(self, span, user_id: str, agent_id: str, session_id: str):
        """Add user context to span"""
        if span:
            span.set_attribute("user.id", user_id)
            span.set_attribute("agent.id", agent_id)
            span.set_attribute("session.id", session_id)
            span.set_attribute("app.name", self.app_name)
            span.set_attribute("timestamp", datetime.now().isoformat())
    
    async def run_agent_with_trace(self,
                                  agent: Agent,
                                  user_id: str,
                                  session_id: str,
                                  user_message: str,
                                  agent_id: str,
                                  additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run an agent with Cloud Trace integration and user ID tracking
        
        Args:
            agent: ADK Agent instance
            user_id: User identifier for tracking
            session_id: Session identifier
            user_message: User's message
            agent_id: Agent identifier
            additional_context: Additional context for tracing
            
        Returns:
            Dict containing the response and trace information
        """
        if not ADK_AVAILABLE:
            logger.error("ADK not available - cannot run agent")
            return {"error": "ADK not available", "success": False}
        
        # Create span for the entire agent execution
        span_name = self._create_span_name("agent_execution", agent_id, user_id)
        span = self.tracer.start_span(span_name) if self.tracer else None
        
        try:
            # Add user context to span
            self._add_user_context(span, user_id, agent_id, session_id)
            
            # Add additional context if provided
            if span and additional_context:
                for key, value in additional_context.items():
                    span.set_attribute(f"context.{key}", str(value))
            
            # Get or create runner for this agent
            if agent_id not in self.runners:
                self.runners[agent_id] = Runner(
                    agent=agent, 
                    app_name=self.app_name, 
                    session_service=self.session_service
                )
            
            runner = self.runners[agent_id]
            
            # Get or create session
            session = await self.session_service.get_session(
                app_name=self.app_name, 
                user_id=user_id, 
                session_id=session_id
            )
            
            if session is None:
                session = await self.session_service.create_session(
                    app_name=self.app_name, 
                    user_id=user_id, 
                    session_id=session_id
                )
            
            # Create user content
            user_content = Content(
                role="user", 
                parts=[Part(text=user_message)]
            )
            
            # Track agent execution with nested spans
            final_response_content = "No response"
            tool_calls = []
            llm_calls = []
            
            # Create span for agent run
            agent_run_span = self.tracer.start_span(
                self._create_span_name("agent_run", agent_id, user_id)
            ) if self.tracer else None
            
            if agent_run_span:
                self._add_user_context(agent_run_span, user_id, agent_id, session_id)
                agent_run_span.set_attribute("user.message", user_message)
            
            try:
                # Run the agent and collect events
                async for event in runner.run_async(
                    user_id=user_id, 
                    session_id=session_id, 
                    new_message=user_content
                ):
                    # Track different types of events
                    if event.is_final_response() and event.content and event.content.parts:
                        final_response_content = event.content.parts[0].text
                        
                        if agent_run_span:
                            agent_run_span.set_attribute("response.length", len(final_response_content))
                            agent_run_span.set_attribute("response.preview", final_response_content[:100])
                    
                    # Track tool calls
                    if hasattr(event, 'tool_calls') and event.tool_calls:
                        for tool_call in event.tool_calls:
                            tool_calls.append({
                                "tool_name": getattr(tool_call, 'name', 'unknown'),
                                "timestamp": datetime.now().isoformat()
                            })
                    
                    # Track LLM calls
                    if hasattr(event, 'model') and event.model:
                        llm_calls.append({
                            "model": event.model,
                            "timestamp": datetime.now().isoformat()
                        })
                
                # Add tool and LLM call information to span
                if agent_run_span:
                    agent_run_span.set_attribute("tool_calls.count", len(tool_calls))
                    agent_run_span.set_attribute("llm_calls.count", len(llm_calls))
                    
                    if tool_calls:
                        agent_run_span.set_attribute("tool_calls.names", 
                                                  [tc["tool_name"] for tc in tool_calls])
                    
                    if llm_calls:
                        agent_run_span.set_attribute("llm_calls.models", 
                                                  [lc["model"] for lc in llm_calls])
                
                # Set span status to success
                if agent_run_span:
                    agent_run_span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Set span status to error
                if agent_run_span:
                    agent_run_span.set_status(Status(StatusCode.ERROR, str(e)))
                    agent_run_span.set_attribute("error.message", str(e))
                raise
            
            finally:
                # End agent run span
                if agent_run_span:
                    agent_run_span.end()
            
            # Prepare response
            response_data = {
                "success": True,
                "response": final_response_content,
                "user_id": user_id,
                "agent_id": agent_id,
                "session_id": session_id,
                "tool_calls": tool_calls,
                "llm_calls": llm_calls,
                "timestamp": datetime.now().isoformat(),
                "trace_enabled": self.tracer is not None
            }
            
            # Set main span status to success
            if span:
                span.set_status(Status(StatusCode.OK))
                span.set_attribute("response.length", len(final_response_content))
                span.set_attribute("tool_calls.count", len(tool_calls))
                span.set_attribute("llm_calls.count", len(llm_calls))
            
            return response_data
            
        except Exception as e:
            # Set span status to error
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("error.message", str(e))
                span.set_attribute("error.type", type(e).__name__)
            
            logger.error(f"Agent execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "agent_id": agent_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "trace_enabled": self.tracer is not None
            }
        
        finally:
            # End main span
            if span:
                span.end()
    
    def run_agent_sync(self,
                      agent: Agent,
                      user_id: str,
                      session_id: str,
                      user_message: str,
                      agent_id: str,
                      additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for run_agent_with_trace
        
        Args:
            agent: ADK Agent instance
            user_id: User identifier for tracking
            session_id: Session identifier
            user_message: User's message
            agent_id: Agent identifier
            additional_context: Additional context for tracing
            
        Returns:
            Dict containing the response and trace information
        """
        try:
            # Run the async function in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.run_agent_with_trace(
                        agent=agent,
                        user_id=user_id,
                        session_id=session_id,
                        user_message=user_message,
                        agent_id=agent_id,
                        additional_context=additional_context
                    )
                )
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Sync agent execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "agent_id": agent_id,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "trace_enabled": self.tracer is not None
            }
    
    def get_trace_info(self) -> Dict[str, Any]:
        """Get information about the tracing setup"""
        return {
            "tracing_enabled": self.tracer is not None,
            "project_id": self.project_id,
            "app_name": self.app_name,
            "opentelemetry_available": OPENTELEMETRY_AVAILABLE,
            "adk_available": ADK_AVAILABLE
        }
    
    def cleanup(self):
        """Cleanup resources"""
        # Clear runner cache
        self.runners.clear()
        
        # Note: OpenTelemetry handles its own cleanup
        logger.info("TracedAgentRunner cleanup completed")

# Global instance for the application
_traced_runner: Optional[TracedAgentRunner] = None

def get_traced_runner(project_id: str = "tsl-generative-ai", 
                     app_name: str = "adk-platform",
                     session_service: Optional[SessionService] = None) -> TracedAgentRunner:
    """Get or create the global traced runner instance"""
    global _traced_runner
    
    if _traced_runner is None:
        _traced_runner = TracedAgentRunner(
            project_id=project_id,
            app_name=app_name,
            session_service=session_service
        )
    
    return _traced_runner

def initialize_fastapi_tracing(app):
    """Initialize FastAPI tracing if OpenTelemetry is available"""
    if OPENTELEMETRY_AVAILABLE:
        try:
            # Only instrument if not already instrumented
            if not FastAPIInstrumentor.is_instrumented_by_opentelemetry:
                FastAPIInstrumentor.instrument_app(app)
                RequestsInstrumentor().instrument()
                logger.info("FastAPI tracing initialized")
            else:
                logger.info("FastAPI tracing already initialized")
        except Exception as e:
            logger.error(f"Failed to initialize FastAPI tracing: {e}")
    else:
        logger.warning("OpenTelemetry not available - FastAPI tracing not initialized")
