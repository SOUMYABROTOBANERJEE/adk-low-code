#!/usr/bin/env python3
"""
Command Line Interface for Google ADK No-Code Platform
"""

import click
import uvicorn
import webbrowser
import time
from pathlib import Path
import sys

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_dir))

from src.google.adk1.nocode.main import app


@click.group()
def cli():
    """Google ADK No-Code Platform CLI"""
    pass


@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8080, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--open-browser', is_flag=True, help='Open browser automatically')
def start(host, port, reload, open_browser):
    """Start the ADK Platform server"""
    click.echo("🚀 Starting Google ADK No-Code Platform...")
    click.echo(f"📱 Platform will be available at: http://{host}:{port}")
    click.echo(f"🔧 API documentation at: http://{host}:{port}/docs")
    click.echo("📖 Press Ctrl+C to stop the server")
    click.echo()
    
    if open_browser:
        def open_browser_delayed():
            time.sleep(2)  # Wait for server to start
            webbrowser.open(f"http://{host}:{port}")
        
        import threading
        threading.Thread(target=open_browser_delayed, daemon=True).start()
    
    uvicorn.run(app, host=host, port=port, reload=reload)


@cli.command()
def status():
    """Check the status of the ADK Platform"""
    click.echo("🔍 Checking ADK Platform status...")
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:8080/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            click.echo("✅ Platform is running")
            click.echo(f"📊 ADK Available: {'✅ Yes' if data.get('adk_available') else '❌ No'}")
            click.echo(f"🕐 Last Check: {data.get('timestamp', 'Unknown')}")
        else:
            click.echo("❌ Platform is running but returned an error")
    except requests.exceptions.ConnectionError:
        click.echo("❌ Platform is not running")
    except Exception as e:
        click.echo(f"❌ Error checking status: {e}")


@cli.command()
def install():
    """Install required dependencies"""
    click.echo("📦 Installing required dependencies...")
    
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        click.echo("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Error installing dependencies: {e}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.command()
def test():
    """Run tests for the platform"""
    click.echo("🧪 Running tests...")
    
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "pytest", "test_google_adk.py"], check=True)
        click.echo("✅ Tests completed successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Tests failed: {e}")
    except Exception as e:
        click.echo(f"❌ Error running tests: {e}")


@cli.command()
def docs():
    """Open the platform documentation"""
    click.echo("📚 Opening documentation...")
    
    try:
        webbrowser.open("https://google.github.io/adk-docs/")
        click.echo("✅ Documentation opened in browser")
    except Exception as e:
        click.echo(f"❌ Error opening documentation: {e}")


if __name__ == "__main__":
    cli()
