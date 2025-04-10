#!/usr/bin/env python
"""
Development server for No-Code ADK.
This script allows running the No-Code ADK interface directly from the source code.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from google.adk.nocode.app import create_app, run_server

if __name__ == "__main__":
    app = create_app()
    run_server(app, host="127.0.0.1", port=8080)
