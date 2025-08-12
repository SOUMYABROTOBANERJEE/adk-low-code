#!/usr/bin/env python3
"""
Startup script for the Google ADK No-Code Platform
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'jinja2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages, check=True)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please run: pip install -r requirements.txt")
            return False
    
    return True

def check_google_adk():
    """Check if Google ADK is available"""
    print("\n🔍 Checking Google ADK availability...")
    
    try:
        import google.adk
        print("✅ Google ADK is available")
        return True
    except ImportError:
        print("⚠️ Google ADK not available")
        print("📚 This is optional - the platform will work with limited functionality")
        print("🔧 To install: pip install google-adk")
        return False

def start_platform():
    """Start the platform"""
    print("\n🚀 Starting Google ADK No-Code Platform...")
    
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Check if we're in the right directory
    if not (script_dir / "src").exists():
        print("❌ Please run this script from the project root directory")
        return
    
    # Start the platform
    try:
        # Open browser after a short delay
        def open_browser():
            time.sleep(3)
            webbrowser.open("http://127.0.0.1:8080")
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Start the platform
        subprocess.run([sys.executable, "app.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Platform stopped by user")
    except Exception as e:
        print(f"❌ Error starting platform: {e}")

def main():
    """Main function"""
    print("🎯 Google ADK No-Code Platform")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check Google ADK
    check_google_adk()
    
    # Start the platform
    start_platform()

if __name__ == "__main__":
    main()
