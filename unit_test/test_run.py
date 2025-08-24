#!/usr/bin/env python3
"""
Run script for the Google ADK No-Code Platform
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import uvicorn
        import fastapi
        import pydantic
    except ImportError as e:
        print(f"Error: Missing required dependency: {e.name}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)

def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("Warning: .env file not found. Creating template...")
        create_env_template()
    
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed. Environment variables from .env file won't be loaded.")

def create_env_template():
    """Create a template .env file"""
    template = """# Google ADK No-Code Platform Environment Configuration

# Google API Key (required for Google ADK functionality)
GOOGLE_API_KEY=your_google_api_key_here

# Langfuse Configuration (optional - for observability)
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Database Configuration
DATABASE_PATH=adk_platform.db

# Server Configuration
HOST=0.0.0.0
PORT=8080
DEBUG=false

# Security (optional)
SECRET_KEY=your_secret_key_here
"""
    
    with open(".env", "w") as f:
        f.write(template)
    
    print("Created .env template file. Please edit it with your configuration.")

def main():
    """Main function to run the application"""
    print("🚀 Starting Google ADK No-Code Platform...")
    
    # Check system requirements
    check_python_version()
    check_dependencies()
    setup_environment()
    
    # Get configuration from environment or defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Run the application
    try:
        import uvicorn
        print(f"🌟 Server starting on http://{host}:{port}")
        print("📝 API documentation available at http://localhost:8080/docs")
        print("🔍 Alternative docs at http://localhost:8080/redoc")
        print("💾 Database will be created automatically as 'adk_platform.db'")
        print("\nPress Ctrl+C to stop the server")
        
        uvicorn.run(
            "src.google2.adk1.nocode.main:app",
            host=host,
            port=port,
            reload=debug,
            log_level="info" if not debug else "debug"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
