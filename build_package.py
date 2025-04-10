#!/usr/bin/env python
"""Build script for the No-Code ADK package."""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Build the package."""
    # Get the current directory
    current_dir = Path(__file__).parent.absolute()
    
    # Clean up previous builds
    build_dir = current_dir / "build"
    dist_dir = current_dir / "dist"
    egg_dir = current_dir / "src" / "google_adk_nocode.egg-info"
    
    for dir_path in [build_dir, dist_dir, egg_dir]:
        if dir_path.exists():
            print(f"Removing {dir_path}")
            shutil.rmtree(dir_path)
    
    # Build the package
    print("Building package...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "build"], check=True)
    subprocess.run([sys.executable, "-m", "build"], cwd=current_dir, check=True)
    
    # Install the package locally for testing
    print("Installing package locally...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--editable", "."], cwd=current_dir, check=True)
    
    print("\nBuild completed successfully!")
    print("\nTo publish to PyPI:")
    print("1. Install twine: pip install --upgrade twine")
    print("2. Upload to PyPI: python -m twine upload dist/*")
    print("\nTo install the package:")
    print("pip install google-adk-nocode")

if __name__ == "__main__":
    main()
