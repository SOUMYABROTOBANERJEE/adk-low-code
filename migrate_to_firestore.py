#!/usr/bin/env python3
"""
Firestore Migration Script
Initializes the agent-genie collection structure in Firestore
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from src.google2.adk1.nocode.firestore_manager import FirestoreManager

def main():
    """Initialize Firestore collections"""
    print("🚀 Initializing Firestore Collections for Agent Genie")
    print("=" * 60)
    
    try:
        # Initialize Firestore manager
        print("📡 Connecting to Firestore...")
        firestore_manager = FirestoreManager()
        
        print("🏗️  Initializing collection structure...")
        firestore_manager.initialize_collections()
        
        print("✅ Firestore collections initialized successfully!")
        print("\nCollection structure created:")
        print("  📁 agent-genie/")
        print("    ├── 📁 tools/items/")
        print("    ├── 📁 agents/items/")
        print("    ├── 📁 projects/items/")
        print("    ├── 📁 chat_sessions/items/")
        print("    ├── 📁 users/items/")
        print("    └── 📁 user_sessions/items/")
        
        print("\n🎯 Ready for production deployment!")
        print("All existing functionality will work with Firestore backend.")
        
    except Exception as e:
        print(f"❌ Error initializing Firestore: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure svcacct.json is in the project root")
        print("2. Check that the service account has Firestore permissions")
        print("3. Verify the project ID is correct")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
