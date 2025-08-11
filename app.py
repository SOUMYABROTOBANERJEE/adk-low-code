#!/usr/bin/env python
"""
Development server for Google ADK No-Code Platform.
This script allows running the ADK platform directly from the source code.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.google2.adk1.nocode.main import app
from dotenv import load_dotenv

load_dotenv('config.env')

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Google ADK No-Code Platform...")
    print("📱 Access the platform at: http://127.0.0.1:8080")
    print("🔧 API documentation at: http://127.0.0.1:8080/docs")
    print("📖 Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(app, host="127.0.0.1", port=8080, reload=False)
