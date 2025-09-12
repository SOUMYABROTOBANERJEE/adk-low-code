#!/usr/bin/env python3
"""
Google ADK No-Code Platform
Main entry point for running the platform
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.google2.adk1.nocode.main import app

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Google ADK No-Code Platform...")
    print("📱 Access the platform at: http://127.0.0.1:8083")
    print("🔧 API documentation at: http://127.0.0.1:8083/docs")
    print("📖 Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,  # Changed from 8082 to 8083
        log_level="debug",
        reload=False  # Set to True for development
    )
