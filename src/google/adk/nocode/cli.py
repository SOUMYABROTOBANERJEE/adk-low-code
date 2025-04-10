"""Command-line interface for the No-Code ADK."""

import os
import sys
import logging
import argparse
import uvicorn
from pathlib import Path

from .app import create_app

logger = logging.getLogger(__name__)

def main():
    """No-Code Agent Development Kit CLI tools."""
    parser = argparse.ArgumentParser(description="No-Code ADK Interface")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the No-Code ADK interface")
    start_parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    start_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to run the server on")
    start_parser.add_argument("--agents-dir", type=str, help="Directory to store agents")
    start_parser.add_argument("--log-level", type=str, default="INFO", help="Log level")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_server(args)
    else:
        parser.print_help()

def start_server(args):
    """Start the No-Code ADK interface server."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create agents directory if specified
    if args.agents_dir:
        agents_path = Path(args.agents_dir)
        agents_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using agents directory: {agents_path.absolute()}")
    
    # Create the app
    app = create_app()
    
    # Print banner
    print(f"""
+-----------------------------------------------------------------------------+
| No-Code ADK Interface                                                       |
+-----------------------------------------------------------------------------+
| Server running at: http://{args.host}:{args.port}                            
| Documentation available at: http://{args.host}:{args.port}/docs               
+-----------------------------------------------------------------------------+
""")
    
    # Run the server
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
